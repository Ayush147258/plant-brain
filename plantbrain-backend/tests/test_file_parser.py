"""File parser format coverage and failure-shape tests."""

from __future__ import annotations

import sys
import types
from email.message import EmailMessage

import fitz
import pytest
from PIL import Image, ImageDraw

from app.config import settings
from app.utils.file_parser import FileParser
from app.utils.text_chunker import TextChunker


def _assert_failure_shape(result: dict, expected_format: str) -> None:
    assert result["success"] is False
    assert result["format"] == expected_format
    assert result["reason"]
    assert result["error"]


def test_pymupdf_preserves_page_boundaries(tmp_path, monkeypatch) -> None:
    """Fallback parsing exposes clean per-page text for page-aware chunking."""

    pdf_path = tmp_path / "pages.pdf"
    document = fitz.open()
    first = document.new_page()
    first.insert_text((72, 72), "Pump P-202 inspection finding on page one.")
    second = document.new_page()
    second.insert_text((72, 72), "Valve V-101 maintenance action on page two.")
    document.save(pdf_path)
    document.close()
    monkeypatch.setattr(settings, "document_parser", "pymupdf")

    result = FileParser.parse_pdf(str(pdf_path))

    assert result["success"] is True
    assert result["metadata"]["parser"] == "pymupdf"
    assert [page["page_number"] for page in result["page_texts"]] == [1, 2]
    assert "P-202" in result["page_texts"][0]["text"]
    assert "V-101" in result["page_texts"][1]["text"]


def test_detect_format_prefers_pdf_magic_over_mislabeled_extension(tmp_path, monkeypatch, caplog) -> None:
    """A PDF named .txt is parsed as PDF and emits a mismatch warning."""

    mislabeled = tmp_path / "actually_pdf.txt"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Mislabeled PDF content P-301.")
    document.save(mislabeled)
    document.close()
    monkeypatch.setattr(settings, "document_parser", "pymupdf")

    assert FileParser.detect_format(str(mislabeled)) == "pdf"
    result = FileParser.parse_file_sync(str(mislabeled), "txt")

    assert result["success"] is True
    assert result["format"] == "pdf"
    assert "P-301" in result["text"]
    assert "extension" in caplog.text.lower()


def test_parse_xlsx_extracts_sheet_cells(tmp_path) -> None:
    """XLSX parsing uses openpyxl and extracts cell text."""

    openpyxl = pytest.importorskip("openpyxl")
    path = tmp_path / "maintenance.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Log"
    sheet.append(["Asset", "Failure"])
    sheet.append(["P-202", "Seal leak"])
    workbook.save(path)

    result = FileParser.parse_file_sync(str(path), "xlsx")

    assert result["success"] is True
    assert result["format"] == "xlsx"
    assert "P-202" in result["text"]
    assert result["metadata"]["parser"] == "openpyxl"


def test_parse_xls_uses_xlrd_adapter(monkeypatch, tmp_path) -> None:
    """Legacy XLS parser reads rows through xlrd without changing result shape."""

    class FakeSheet:
        name = "Legacy"
        nrows = 2
        ncols = 2

        def cell_value(self, row: int, col: int):
            return [["Asset", "Failure"], ["P-303", "Bearing wear"]][row][col]

    class FakeWorkbook:
        nsheets = 1

        def sheets(self):
            return [FakeSheet()]

    fake_xlrd = types.SimpleNamespace(open_workbook=lambda _: FakeWorkbook())
    monkeypatch.setitem(sys.modules, "xlrd", fake_xlrd)
    path = tmp_path / "legacy.xls"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1fake")

    result = FileParser.parse_file_sync(str(path), "xls")

    assert result["success"] is True
    assert result["format"] == "xls"
    assert "P-303" in result["text"]


def test_parse_multipage_tiff_iterates_all_pages(tmp_path, monkeypatch) -> None:
    """Multi-page TIFF OCR visits every frame instead of only the first."""

    import pytesseract

    path = tmp_path / "scan.tiff"
    images = []
    for label in ["page one", "page two"]:
        image = Image.new("RGB", (120, 60), "white")
        ImageDraw.Draw(image).text((10, 20), label, fill="black")
        images.append(image)
    images[0].save(path, save_all=True, append_images=images[1:])
    calls: list[int] = []

    def fake_ocr(image, lang="", output_type=None):
        calls.append(1)
        return {"text": ["OCR", "page", str(len(calls))], "conf": ["95", "94", "93"]}

    monkeypatch.setattr(pytesseract, "image_to_data", fake_ocr)

    result = FileParser.parse_file_sync(str(path), "image")

    assert result["success"] is True
    assert result["format"] == "tiff"
    assert result["pages"] == 2
    assert calls == [1, 1]
    assert "OCR page 2" in result["text"]


def test_parse_eml_extracts_headers_and_body(tmp_path) -> None:
    """EML parser uses the stdlib email package for RFC 822 messages."""

    path = tmp_path / "maintenance.eml"
    message = EmailMessage()
    message["From"] = "tech@example.com"
    message["To"] = "ops@example.com"
    message["Subject"] = "Pump P-404 failure"
    message.set_content("Observed cavitation on P-404 during inspection.")
    path.write_bytes(message.as_bytes())

    result = FileParser.parse_file_sync(str(path), "eml")

    assert result["success"] is True
    assert result["format"] == "eml"
    assert "Pump P-404 failure" in result["text"]
    assert "Observed cavitation" in result["text"]


def test_parse_msg_uses_extract_msg_adapter(monkeypatch, tmp_path) -> None:
    """MSG parser integrates with extract-msg and returns normalized text."""

    class FakeMessage:
        sender = "tech@example.com"
        to = "ops@example.com"
        subject = "Valve V-12"
        date = "2026-07-07"
        body = "Valve V-12 sticking during startup."

        def close(self):
            return None

    fake_module = types.SimpleNamespace(Message=lambda _: FakeMessage())
    monkeypatch.setitem(sys.modules, "extract_msg", fake_module)
    path = tmp_path / "mail.msg"
    path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1fake")

    result = FileParser.parse_file_sync(str(path), "msg")

    assert result["success"] is True
    assert result["format"] == "msg"
    assert "Valve V-12" in result["text"]


def test_parse_dxf_extracts_text_entities(tmp_path) -> None:
    """DXF parsing uses ezdxf for text entities."""

    ezdxf = pytest.importorskip("ezdxf")
    path = tmp_path / "layout.dxf"
    document = ezdxf.new()
    document.modelspace().add_text("P-505")
    document.saveas(path)

    result = FileParser.parse_file_sync(str(path), "dxf")

    assert result["success"] is True
    assert result["format"] == "dxf"
    assert "P-505" in result["text"]


def test_parse_dwg_returns_clean_unsupported_result(tmp_path) -> None:
    """DWG binary detection returns a useful unsupported result instead of crashing."""

    path = tmp_path / "drawing.dwg"
    path.write_bytes(b"AC1032\x00binary dwg sample")

    result = FileParser.parse_file_sync(str(path), "dwg")

    _assert_failure_shape(result, "dwg")
    assert result["reason"] == "unsupported_dwg"


def test_corrupted_pdf_returns_consistent_failure_shape(tmp_path, monkeypatch) -> None:
    """Corrupted files do not raise out of the parser."""

    path = tmp_path / "corrupt.pdf"
    path.write_bytes(b"%PDF-1.7\nnot a valid pdf")
    monkeypatch.setattr(settings, "document_parser", "pymupdf")

    result = FileParser.parse_file_sync(str(path), "pdf")

    _assert_failure_shape(result, "pdf")
    assert result["reason"] == "parse_error"


def test_password_protected_pdf_returns_clean_failure(tmp_path, monkeypatch) -> None:
    """Password-protected PDFs return a short reason code, not an exception."""

    path = tmp_path / "locked.pdf"
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "Locked text")
    document.save(path, encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret")
    document.close()
    monkeypatch.setattr(settings, "document_parser", "pymupdf")

    result = FileParser.parse_file_sync(str(path), "pdf")

    _assert_failure_shape(result, "pdf")
    assert result["reason"] == "password_protected"


def test_document_context_uses_query_filename_contract() -> None:
    """Chroma metadata uses the filename key consumed by citation responses."""

    chunks = TextChunker.smart_chunk("Pump P-202 requires inspection and seal maintenance.", metadata={"page_number": 4})
    contextual = TextChunker.add_document_context(chunks, "manual.pdf", "doc-1")

    assert contextual[0]["metadata"]["filename"] == "manual.pdf"
    assert contextual[0]["metadata"]["document_id"] == "doc-1"
    assert contextual[0]["metadata"]["page_number"] == 4


def test_preprocess_image_for_ocr_returns_thresholded_image() -> None:
    """OCR preprocessing is testable apart from the OCR call."""

    pytest.importorskip("cv2")
    image = Image.new("RGB", (220, 80), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 25), "Pump P-202", fill="black")

    processed = FileParser.preprocess_image_for_ocr(image)

    assert processed.mode == "L"
    assert processed.size == image.size


def test_image_ocr_uses_word_confidence_scores(tmp_path, monkeypatch) -> None:
    """Image parsing uses pytesseract.image_to_data and exposes average OCR confidence."""

    pytest.importorskip("cv2")
    import pytesseract

    path = tmp_path / "scan.png"
    image = Image.new("RGB", (220, 80), "white")
    ImageDraw.Draw(image).text((20, 25), "Pump P-202", fill="black")
    image.save(path)

    def fake_image_to_data(*args, **kwargs):
        return {"text": ["Pump", "P-202", ""], "conf": ["80", "40", "-1"]}

    monkeypatch.setattr(pytesseract, "image_to_data", fake_image_to_data)
    monkeypatch.setattr(settings, "ocr_confidence_threshold", 70.0)

    result = FileParser.parse_image(str(path))

    assert result["success"] is True
    assert result["text"] == "Pump P-202"
    assert result["ocr_average_confidence"] == 60.0
    assert result["low_confidence"] is True
    assert result["page_texts"][0]["ocr_confidence"] == 60.0


def test_degraded_synthetic_images_return_parse_result(tmp_path, monkeypatch) -> None:
    """Degraded scans are parsed or flagged low-confidence instead of crashing."""

    pytest.importorskip("cv2")
    import pytesseract
    from PIL import ImageFilter

    confidences = iter([85, 55, 25])

    def fake_image_to_data(*args, **kwargs):
        confidence = next(confidences)
        return {"text": ["Asset", "P-707"], "conf": [str(confidence), str(confidence)]}

    monkeypatch.setattr(pytesseract, "image_to_data", fake_image_to_data)
    monkeypatch.setattr(settings, "ocr_confidence_threshold", 60.0)

    clean = Image.new("RGB", (260, 100), "white")
    ImageDraw.Draw(clean).text((20, 35), "Asset P-707 seal leak", fill="black")
    severities = [1, 2, 3]
    results = []
    for severity in severities:
        degraded = clean.rotate(severity * 2, expand=False, fillcolor="white")
        degraded = degraded.filter(ImageFilter.GaussianBlur(radius=severity * 0.7))
        path = tmp_path / f"degraded_{severity}.jpg"
        degraded.save(path, format="JPEG", quality=max(20, 85 - severity * 20))
        results.append(FileParser.parse_image(str(path)))

    assert [result["success"] for result in results] == [True, True, True]
    assert [result["low_confidence"] for result in results] == [False, True, True]
    assert all("P-707" in result["text"] for result in results)
