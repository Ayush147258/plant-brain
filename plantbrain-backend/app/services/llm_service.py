"""Gemini-backed LLM service for PlantBrain question answering and analysis."""

import json
import logging
import re
import time
from typing import Any

from google import genai
from google.genai import types
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import settings


logger = logging.getLogger(__name__)


class LLMService:
    """Wrap Gemini API calls for RAG answers, compliance checks, and pattern summaries."""

    def __init__(self) -> None:
        """Initialize the Gemini client and model configuration."""

        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model
        self.max_tokens = 1500

    def build_system_prompt(self, language: str = "en") -> str:
        """Return the PlantBrain assistant system prompt."""

        base = """
   You are PlantBrain, an AI assistant for industrial plant operations. You have deep knowledge about plant equipment, safety procedures, maintenance records, and compliance regulations.

   Your job is to answer questions from plant engineers and technicians accurately and safely.

   Rules:
   - Always cite the source document name and page/section when you use information from it.
   - Express your confidence level at the end: [Confidence: High/Medium/Low]
   - If the context does not contain enough information to answer, say so clearly — do not guess.
   - For safety-critical questions, always add a caution note.
   - Answer in the same language the question was asked (English or Hindi).
   - Keep answers concise but complete. Use bullet points for lists.
   - Never fabricate equipment tags, specifications, or regulation codes.
   """
        if language == "hi":
            base += "\nIMPORTANT: The user is asking in Hindi. Reply ENTIRELY in Hindi (Devanagari script). Use Hindi terminology for industrial/engineering terms."
        return base

    def build_rag_prompt(
        self,
        question: str,
        retrieved_chunks: list[dict],
        graph_context: list[dict] | None = None,
    ) -> str:
        """Build the retrieval-augmented user prompt for Gemini."""

        context_parts = []
        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {}) or {}
            filename = metadata.get("filename", "Unknown")
            chunk_index = int(metadata.get("chunk_index", 0)) + 1
            text = chunk.get("text", "")
            context_parts.append(
                f"Source: {filename} | Section: chunk {chunk_index}\n{text}\n---"
            )

        graph_parts = []
        for item in graph_context or []:
            tag = item.get("tag", "Unknown")
            relationship = item.get("relationship", "connected_to")
            depth = item.get("depth", 0)
            attributes = item.get("attributes", {}) or {}
            name = attributes.get("name") or attributes.get("equipment_type") or ""
            suffix = f" ({name})" if name else ""
            graph_parts.append(f"- {tag}{suffix}: relationship={relationship}, depth={depth}")

        document_context = "\n".join(context_parts) if context_parts else "No retrieved document context."
        equipment_context = "\n".join(graph_parts) if graph_parts else "No equipment graph context provided."

        return f"""
RETRIEVED DOCUMENT CONTEXT:
{document_context}

EQUIPMENT GRAPH CONTEXT:
{equipment_context}

QUESTION: {question}

Answer based on the above context. If information is not in the context, say "This information is not available in the uploaded documents."
""".strip()

    async def answer_question(
        self,
        question: str,
        retrieved_chunks: list[dict],
        graph_context: list[dict] | None = None,
        session_id: str | None = None,
        language: str = "en",
    ) -> dict:
        """Answer a user question using retrieved document and equipment graph context."""

        start_time = time.time()
        try:
            user_prompt = self.build_rag_prompt(question, retrieved_chunks, graph_context)
            logger.info("Generating Gemini answer for session_id=%s", session_id)
            response = await self._resilient_generate_content(
                model=self.model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.build_system_prompt(language),
                    max_output_tokens=self.max_tokens,
                ),
            )
            self._log_usage(response)

            answer_text = self._extract_response_text(response)
            confidence_match = re.search(r"\[Confidence:\s*(High|Medium|Low)\]", answer_text, re.IGNORECASE)
            confidence = confidence_match.group(1).title() if confidence_match else "Medium"
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.info("Generated Gemini answer in %s ms", response_time_ms)

            return {
                "answer": answer_text,
                "confidence": confidence,
                "sources": self._extract_sources(retrieved_chunks),
                "response_time_ms": response_time_ms,
                "model": self.model,
            }
        except Exception as exc:
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.exception("Error generating Gemini answer after %s ms", response_time_ms)
            return {
                "answer": "Error generating answer",
                "confidence": "Low",
                "sources": [],
                "error": str(exc),
                "response_time_ms": response_time_ms,
                "model": self.model,
            }

    async def check_compliance(self, procedure_text: str, rule_text: str, rule_code: str) -> dict:
        """Check a plant procedure against a compliance rule using Gemini."""

        start_time = time.time()
        prompt = f"""You are a compliance auditor for industrial plants in India.
Rule {rule_code}: {rule_text}
Procedure to check: {procedure_text}
Is the procedure compliant with this rule? Answer with:
STATUS: [COMPLIANT / NON_COMPLIANT / PARTIAL / INSUFFICIENT_INFORMATION]
FINDINGS: [explain what matches and what is missing]
RECOMMENDATION: [what needs to change if not fully compliant]"""

        try:
            logger.info("Running Gemini compliance check for rule %s", rule_code)
            response = await self._resilient_generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=self.max_tokens),
            )
            self._log_usage(response)

            text = self._extract_response_text(response)
            response_time_ms = int((time.time() - start_time) * 1000)
            logger.info("Completed compliance check for %s in %s ms", rule_code, response_time_ms)
            return {
                "status": self._extract_field(text, "STATUS", "INSUFFICIENT_INFORMATION"),
                "findings": self._extract_field(text, "FINDINGS", ""),
                "recommendation": self._extract_field(text, "RECOMMENDATION", ""),
                "rule_code": rule_code,
            }
        except Exception:
            logger.exception("Error checking compliance for rule %s", rule_code)
            return {
                "status": "INSUFFICIENT_INFORMATION",
                "findings": "Error checking compliance",
                "recommendation": "Retry the compliance check after resolving the service error.",
                "rule_code": rule_code,
            }

    async def summarize_pattern(self, failure_records: list[dict]) -> str:
        """Summarize failure records into a concise engineering pattern analysis."""

        start_time = time.time()
        prompt = """Summarize the following failure pattern for a plant engineer. What is the root cause hypothesis? What preventive action is recommended? Keep it under 150 words.

Failure records JSON:
""" + json.dumps(failure_records, ensure_ascii=False, indent=2)

        try:
            logger.info("Summarizing %s failure records with Gemini", len(failure_records))
            response = await self._resilient_generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(max_output_tokens=self.max_tokens),
            )
            self._log_usage(response)
            summary = self._extract_response_text(response)
            elapsed_ms = int((time.time() - start_time) * 1000)
            logger.info("Summarized failure pattern in %s ms", elapsed_ms)
            return summary
        except Exception:
            logger.exception("Error summarizing failure pattern")
            return "Error summarizing failure pattern"
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception(lambda exc: LLMService._is_retryable_error(exc)),
        reraise=True,
    )
    async def _resilient_generate_content(self, **kwargs):
        """Call Gemini generate_content with tenacity retries for transient API errors."""

        return await self.client.aio.models.generate_content(**kwargs)

    @staticmethod
    def _extract_response_text(response: Any) -> str:
        """Extract text from a Gemini response object."""

        text = getattr(response, "text", None)
        if text:
            return text

        candidates = getattr(response, "candidates", None) or []
        if candidates:
            content = getattr(candidates[0], "content", None)
            parts = getattr(content, "parts", None) or []
            part_text = [getattr(part, "text", "") for part in parts]
            return "".join(part_text).strip()

        return ""

    @staticmethod
    def _extract_sources(retrieved_chunks: list[dict]) -> list[dict]:
        """Extract source metadata from retrieved chunks."""

        sources = []
        for chunk in retrieved_chunks:
            metadata = chunk.get("metadata", {}) or {}
            sources.append(
                {
                    "filename": metadata.get("filename"),
                    "chunk_index": metadata.get("chunk_index"),
                }
            )
        return sources

    @staticmethod
    def _extract_field(text: str, field_name: str, default: str) -> str:
        """Extract a labeled field from model output."""

        pattern = rf"{field_name}:\s*(.*?)(?=\n[A-Z_]+:|\Z)"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if not match:
            return default
        return match.group(1).strip().strip("[]") or default

    @staticmethod
    def _log_usage(response: Any) -> None:
        """Log token usage metadata when Gemini returns it."""

        usage = getattr(response, "usage_metadata", None)
        if usage is None:
            logger.info("Gemini token usage metadata unavailable")
            return

        prompt_tokens = getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_token_count", None)
        logger.info(
            "Gemini token usage: prompt=%s output=%s total=%s",
            prompt_tokens,
            output_tokens,
            total_tokens,
        )


llm_service = LLMService()



__all__ = ["LLMService", "llm_service"]
