"""Local Whisper voice transcription service for PlantBrain."""

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.inspection import Inspection


logger = logging.getLogger(__name__)


class VoiceService:
    """Transcribe audio with local Whisper; the model loads ~500MB on first call."""

    KEYWORDS = [
        "inspection",
        "leak",
        "vibration",
        "temperature",
        "pressure",
        "noise",
        "repair",
        "replace",
        "corrode",
        "fail",
    ]
    HINDI_KEYWORDS = ["निरीक्षण", "रिसाव", "कंपन", "तापमान", "दबाव", "मरम्मत"]
    CRITICAL_TERMS = ["critical", "emergency", "urgent", "immediately"]
    MINOR_TERMS = ["concern", "check", "monitor"]
    ACTION_TERMS = ["need to", "should", "must", "replace", "repair", "call"]
    EQUIPMENT_TAG_PATTERN = re.compile(r"\b([A-Z]{1,3}-\d{3,4})\b")

    def __init__(self) -> None:
        """Create a lazy Whisper transcription service."""

        self._model = None
        self._model_name = settings.whisper_model
        self._supported_formats = {".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".webm", ".flac"}

    def get_model(self):
        """Load and cache the local Whisper model; first load downloads/loads ~500MB."""

        if self._model is None:
            try:
                import whisper

                logger.info("Loading Whisper model %s...", self._model_name)
                self._model = whisper.load_model(self._model_name)
                logger.info("Whisper model %s loaded", self._model_name)
            except Exception:
                logger.exception("Failed to load Whisper model %s", self._model_name)
                raise
        return self._model

    def transcribe_file(self, file_path: str, language: str | None = None) -> dict:
        """Transcribe an audio file locally with Whisper using CPU-safe fp16=False."""

        try:
            logger.info("Transcribing audio file %s", file_path)
            model = self.get_model()
            whisper_language = self._normalize_language_hint(language)
            result = model.transcribe(file_path, language=whisper_language, fp16=False)
            segments = [
                {
                    "start": segment["start"],
                    "end": segment["end"],
                    "text": segment["text"],
                }
                for segment in result.get("segments", [])
            ]
            duration_seconds = segments[-1]["end"] if segments else 0
            logger.info("Transcribed %s seconds from %s", duration_seconds, file_path)
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", "unknown"),
                "segments": segments,
                "duration_seconds": duration_seconds,
            }
        except Exception as exc:
            logger.exception("Failed to transcribe audio file %s", file_path)
            return {"text": "", "error": str(exc)}

    async def transcribe_async(self, file_path: str, language: str | None = None) -> dict:
        """Run blocking Whisper transcription in a thread pool."""

        return await asyncio.get_event_loop().run_in_executor(None, self.transcribe_file, file_path, language)

    def extract_knowledge(self, transcription_text: str) -> dict:
        """Extract simple equipment, keyword, severity, and action hints from transcription text."""

        text = transcription_text or ""
        lowered_text = text.lower()
        equipment_tags = self._dedupe_preserve_order(self.EQUIPMENT_TAG_PATTERN.findall(text.upper()))
        all_keywords = self.KEYWORDS + self.HINDI_KEYWORDS
        keywords = [keyword for keyword in all_keywords if keyword in lowered_text or keyword in text]

        if any(term in lowered_text for term in self.CRITICAL_TERMS):
            severity_hint = "critical"
        elif any(term in lowered_text for term in self.MINOR_TERMS):
            severity_hint = "minor"
        else:
            severity_hint = "routine"

        has_action_item = any(term in lowered_text for term in self.ACTION_TERMS)
        return {
            "equipment_tags": equipment_tags,
            "keywords": keywords,
            "severity_hint": severity_hint,
            "has_action_item": has_action_item,
        }

    def validate_audio_file(self, filename: str, file_size_bytes: int) -> tuple[bool, str]:
        """Validate audio extension and 25 MB local Whisper upload limit."""

        extension = Path(filename).suffix.lower()
        if extension not in self._supported_formats:
            return False, f"Unsupported audio format: {extension or 'unknown'}"

        max_size_bytes = 25 * 1024 * 1024
        if file_size_bytes > max_size_bytes:
            return False, "Audio file exceeds maximum size of 25 MB"

        return True, ""

    async def process_voice_note(
        self,
        file_path: str,
        filename: str,
        document_id: str,
        language: str | None = None,
    ) -> dict:
        """Transcribe and extract knowledge from a voice note; Whisper loads ~500MB on first call."""

        logger.info("Processing voice note %s for document %s", filename, document_id)
        transcription = await self.transcribe_async(file_path, language)
        text = transcription.get("text", "")
        knowledge = self.extract_knowledge(text)
        equipment_tags = knowledge["equipment_tags"]
        inspection_created = False

        if equipment_tags:
            try:
                from app.services.graph_service import graph_service

                graph_service.extract_and_add_from_text(text, document_id)
            except Exception:
                logger.exception("Failed to update graph from voice note %s", filename)

        if knowledge["severity_hint"] != "routine" and equipment_tags:
            inspection_created = await self._create_inspection_from_voice(
                equipment_tags[0],
                text,
                knowledge["severity_hint"],
                document_id,
            )

        return {
            "transcription": text,
            "language_detected": transcription.get("language", language or "unknown"),
            "knowledge_extracted": knowledge,
            "equipment_tags_found": equipment_tags,
            "inspection_created": inspection_created,
            "duration_seconds": transcription.get("duration_seconds", 0),
        }

    @staticmethod
    def _normalize_language_hint(language: str | None) -> str | None:
        """Normalize user language hints for Whisper transcription."""

        if not language:
            return None

        normalized = language.strip().lower()
        if normalized in {"", "auto"}:
            return None
        if normalized in {"hi", "hindi"}:
            return "hi"
        return normalized

    async def _create_inspection_from_voice(
        self,
        equipment_tag: str,
        findings: str,
        severity: str,
        document_id: str,
    ) -> bool:
        """Create an inspection record from extracted voice-note knowledge."""

        try:
            async with AsyncSessionLocal() as session:
                session.add(
                    Inspection(
                        equipment_tag=equipment_tag,
                        inspection_date=datetime.utcnow(),
                        inspector_name="voice_note",
                        inspection_type="voice_auto_extracted",
                        findings=findings,
                        severity=severity,
                        source_document_id=document_id,
                    )
                )
                await session.commit()
            logger.info("Created voice-derived inspection for %s", equipment_tag)
            return True
        except Exception:
            logger.exception("Failed to create voice-derived inspection for %s", equipment_tag)
            return False

    @staticmethod
    def _dedupe_preserve_order(values: list[str]) -> list[str]:
        """Remove duplicate strings while preserving first-seen order."""

        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                deduped.append(value)
        return deduped


voice_service = VoiceService()

__all__ = ["VoiceService", "voice_service"]
