"""Utilities for extracting clean text from uploaded PlantBrain files."""

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import fitz
import pytesseract
from docx import Document
from PIL import Image


logger = logging.getLogger(__name__)


class FileParser:
    """Parser helpers for extracting text and metadata from supported file types."""

    @staticmethod
    def parse_file_sync(file_path: str, file_type: str) -> dict[str, Any]:
        """Synchronously route a file to the correct parser based on its type."""

        logger.info("Parsing file %s as %s", file_path, file_type)
        normalized_type = file_type.lower().strip()
        parsers = {
            "pdf": FileParser.parse_pdf,
            "docx": FileParser.parse_docx,
            "doc": FileParser.parse_docx,
            "txt": FileParser.parse_txt,
            "image": FileParser.parse_image,
        }
        parser = parsers.get(normalized_type)
        if parser is None:
            error = f"Unsupported file type: {file_type}"
            logger.warning(error)
            return {
                "text": "",
                "metadata": {},
                "pages": 0,
                "success": False,
                "error": error,
            }
        return parser(file_path)
    @staticmethod
    async def parse_file(file_path: str, file_type: str) -> dict[str, Any]:
        """Route a file to the correct parser based on its type."""

        return FileParser.parse_file_sync(file_path, file_type)

    @staticmethod
    def parse_pdf(file_path: str) -> dict[str, Any]:
        """Extract text from a PDF, using OCR for sparse pages."""

        logger.info("Extracting PDF text from %s", file_path)
        try:
            page_texts: list[str] = []
            with fitz.open(file_path) as doc:
                page_count = doc.page_count
                metadata = {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "pages": page_count,
                }

                for page_index, page in enumerate(doc, start=1):
                    logger.debug("Extracting text from PDF page %s", page_index)
                    text = page.get_text("text") or ""

                    if len(text.strip()) < 50:
                        logger.info("Page %s has sparse text; attempting OCR", page_index)
                        ocr_text = FileParser._ocr_pdf_page(page)
                        if ocr_text:
                            text = f"{text}\n{ocr_text}" if text.strip() else ocr_text

                    page_texts.append(text)

            combined_text = FileParser.clean_text("\n\n".join(page_texts))
            logger.info("Successfully parsed PDF %s with %s pages", file_path, page_count)
            return {
                "text": combined_text,
                "metadata": metadata,
                "pages": page_count,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Failed to parse PDF %s", file_path)
            return FileParser._error_result(str(exc))

    @staticmethod
    def parse_docx(file_path: str) -> dict[str, Any]:
        """Extract paragraph and table text from a Word document."""

        logger.info("Extracting DOCX text from %s", file_path)
        try:
            doc = Document(file_path)
            text_parts: list[str] = []

            paragraphs = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            text_parts.extend(paragraphs)

            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        text_parts.append(row_text)

            combined_text = FileParser.clean_text("\n".join(text_parts))
            metadata = {"paragraphs": len(paragraphs), "tables": len(doc.tables)}
            logger.info(
                "Successfully parsed DOCX %s with %s paragraphs and %s tables",
                file_path,
                len(paragraphs),
                len(doc.tables),
            )
            return {
                "text": combined_text,
                "metadata": metadata,
                "pages": 0,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Failed to parse DOCX %s", file_path)
            return FileParser._error_result(str(exc))

    @staticmethod
    def parse_txt(file_path: str) -> dict[str, Any]:
        """Read text from a plain text file with UTF-8 and Latin-1 fallback."""

        logger.info("Extracting TXT text from %s", file_path)
        try:
            detected_encoding = "utf-8"
            try:
                with open(file_path, encoding="utf-8") as file:
                    text = file.read()
            except UnicodeDecodeError:
                logger.info("UTF-8 decode failed for %s; falling back to latin-1", file_path)
                detected_encoding = "latin-1"
                with open(file_path, encoding="latin-1") as file:
                    text = file.read()

            cleaned_text = FileParser.clean_text(text)
            logger.info("Successfully parsed TXT %s using %s", file_path, detected_encoding)
            return {
                "text": cleaned_text,
                "metadata": {"encoding": detected_encoding},
                "pages": 1,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Failed to parse TXT %s", file_path)
            return FileParser._error_result(str(exc))

    @staticmethod
    def parse_image(file_path: str) -> dict[str, Any]:
        """Extract text from an image using OCR with English and Hindi language support."""

        logger.info("Extracting image text from %s", file_path)
        try:
            with Image.open(file_path) as image:
                metadata = {
                    "width": image.width,
                    "height": image.height,
                    "mode": image.mode,
                }
                text = pytesseract.image_to_string(image, lang="eng+hin")

            cleaned_text = FileParser.clean_text(text)
            logger.info("Successfully parsed image %s", file_path)
            return {
                "text": cleaned_text,
                "metadata": metadata,
                "pages": 1,
                "success": True,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Failed to parse image %s", file_path)
            return FileParser._error_result(str(exc))

    @staticmethod
    def clean_text(text: str) -> str:
        """Normalize extracted text by removing null bytes and excessive whitespace."""

        if not text:
            return ""

        cleaned = text.replace("\x00", "")
        cleaned = "\n".join(line.strip() for line in cleaned.splitlines())
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def detect_file_type(filename: str) -> str:
        """Detect the supported parser type from a filename extension."""

        extension = Path(filename).suffix.lower()
        extension_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
            ".txt": "txt",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".tiff": "image",
            ".bmp": "image",
        }
        file_type = extension_map.get(extension, "unknown")
        logger.debug("Detected file type %s for filename %s", file_type, filename)
        return file_type

    @staticmethod
    def _ocr_pdf_page(page: fitz.Page) -> str:
        """Render a PDF page to a temporary image and OCR it."""

        temp_path = ""
        try:
            pix = page.get_pixmap(dpi=200)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                temp_path = temp_file.name
                pix.save(temp_path)

            with Image.open(temp_path) as image:
                return pytesseract.image_to_string(image, lang="eng+hin")
        except Exception:
            logger.exception("Failed to OCR sparse PDF page")
            return ""
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    @staticmethod
    def _error_result(error: str) -> dict[str, Any]:
        """Build a standard parser failure response."""

        return {
            "text": "",
            "metadata": {},
            "pages": 0,
            "success": False,
            "error": error,
        }

