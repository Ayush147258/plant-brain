"""Gemini multimodal structured extraction for diagrams and maintenance logs."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Literal

from google import genai
from google.genai import types

from app.config import settings


logger = logging.getLogger(__name__)
ExtractionKind = Literal["auto", "pid", "maintenance_log", "none"]

PID_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "zone": {"type": "string", "nullable": True},
        "equipment": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "nullable": True},
                    "type": {"type": "string", "nullable": True},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["id", "type", "confidence"],
            },
        },
        "valves": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "valve_id": {"type": "string", "nullable": True},
                    "valve_type": {"type": "string", "nullable": True},
                    "connects_from": {"type": "string", "nullable": True},
                    "connects_to": {"type": "string", "nullable": True},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["valve_id", "valve_type", "connects_from", "connects_to", "confidence"],
            },
        },
        "instruments": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "tag": {"type": "string", "nullable": True},
                    "attached_to_line_between": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["tag", "attached_to_line_between", "confidence"],
            },
        },
        "confidence_flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["zone", "equipment", "valves", "instruments", "confidence_flags"],
}

LOG_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "entries": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Asset_ID": {"type": "string", "nullable": True},
                    "Failure_Mode": {"type": "string", "nullable": True},
                    "Date": {"type": "string", "nullable": True},
                    "Technician_Notes": {"type": "string", "nullable": True},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["Asset_ID", "Failure_Mode", "Date", "Technician_Notes", "confidence"],
            },
        },
        "confidence_flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["entries", "confidence_flags"],
}

PID_PROMPT = """You are a process engineering assistant analyzing a Piping and Instrumentation Diagram (P&ID).

TASK:
Examine the attached image/PDF page carefully, including line weights, tag labels near symbols, and connecting lines between equipment.

Extract only the requested zone/area when one is provided:
1. Every equipment ID (tanks, pumps, heat exchangers, compressors, reactors, vessels, etc.)
2. Every valve ID and its type (gate, check, control, relief, etc.) if legible
3. The connectivity: which equipment IDs each valve connects (upstream/downstream)
4. Any instrument tags (for example PT-101, FT-204) attached to a line

RULES:
- If a tag is partially obscured or illegible, return it as null and add a note in confidence_flags. Do not guess.
- Do not infer connections that are not shown by an actual drawn line.
- Distinguish process lines from instrument signal lines when visible.
- Use null rather than fabricating IDs, dates, tags, or connection endpoints.
- Return confidence high/medium/low per extracted object
- If symbol interpretation depends on an inferred P&ID standard or legend (for example ISA-5.1 versus a legacy/company-specific legend) and confidence is not high, add that inferred standard and uncertainty to confidence_flags rather than silently guessing.

Return ONLY valid JSON matching the schema provided. No prose, no markdown fences.
"""

LOG_PROMPT = """You are extracting structured maintenance records from a scanned industrial log page. Handwriting, stamps, or smudging may make some fields ambiguous.

For each distinct log entry, extract:
- Asset_ID
- Failure_Mode (a short standardized phrase, not verbatim handwriting)
- Date (ISO 8601 format YYYY-MM-DD; if only partial date is legible, use null instead of guessing)
- Technician_Notes (verbatim if legible, else null)
- confidence (high/medium/low) reflecting your certainty about this row as a whole

Rules:
- If a field cannot be determined with reasonable confidence, return null. Never fabricate a plausible-looking value.
- Do not merge two separate entries even if they are visually close together on the page.
- Preserve the original order of entries as they appear top-to-bottom.

Return ONLY valid JSON matching the schema provided. No prose, no markdown fences.
"""


class MultimodalExtractionService:
    """Use Gemini response_schema to turn visual plant documents into validated JSON."""

    VISUAL_FILE_TYPES = {"pdf", "png", "jpg", "jpeg", "tiff", "bmp"}
    PID_HINTS = ("p&id", "pid", "piping", "instrumentation", "blueprint", "drawing", "valve", "zone")
    LOG_HINTS = ("maintenance", "failure", "technician", "inspection", "repair", "work order", "log")

    def __init__(self) -> None:
        self.model = settings.gemini_extraction_model

    def configured(self) -> bool:
        key = settings.gemini_api_key.strip()
        return settings.multimodal_extraction_enabled and bool(key) and key not in {"test-key", "your_key_here"}

    def classify(self, filename: str, file_type: str, text: str, requested_kind: ExtractionKind = "auto") -> ExtractionKind:
        if requested_kind in {"pid", "maintenance_log", "none"}:
            return requested_kind
        if file_type.lower() not in self.VISUAL_FILE_TYPES:
            return "none"

        haystack = f"{filename}\n{text[:4000]}".lower()
        pid_score = sum(1 for hint in self.PID_HINTS if hint in haystack)
        log_score = sum(1 for hint in self.LOG_HINTS if hint in haystack)
        if pid_score == 0 and log_score == 0:
            return "none"
        return "pid" if pid_score >= log_score else "maintenance_log"

    def extract(self, file_path: str, kind: ExtractionKind, zone: str = "") -> dict[str, Any]:
        if kind == "pid":
            prompt = f"{PID_PROMPT}\nZone of interest: {zone or 'entire drawing'}"
            return self._generate_json(file_path, prompt, PID_SCHEMA)
        if kind == "maintenance_log":
            return self._generate_json(file_path, LOG_PROMPT, LOG_SCHEMA)
        return {}

    def _generate_json(self, file_path: str, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        path = Path(file_path)
        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(data=path.read_bytes(), mime_type=self._mime_type(path)),
                prompt,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0,
            ),
        )
        parsed = json.loads(response.text or "{}")
        logger.info("Gemini structured extraction completed for %s using %s", path.name, self.model)
        return parsed

    @staticmethod
    def _mime_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            return "application/pdf"
        if suffix in {".jpg", ".jpeg"}:
            return "image/jpeg"
        if suffix in {".tif", ".tiff"}:
            return "image/tiff"
        if suffix == ".bmp":
            return "image/bmp"
        return "image/png"


multimodal_extraction_service = MultimodalExtractionService()

__all__ = ["MultimodalExtractionService", "multimodal_extraction_service"]
