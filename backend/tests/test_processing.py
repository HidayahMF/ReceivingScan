from pathlib import Path
import pytest

from app.config import Settings
from app.processing import process_document

def test_processing_rejects_invalid_image_content(tmp_path: Path):
    source = tmp_path / "bad.png"
    source.write_bytes(b"not-an-image")
    with pytest.raises(ValueError):
        process_document(source, Settings(storage_path=str(tmp_path)))

def test_ocr_engine_failure_is_not_reported_as_review(monkeypatch, tmp_path: Path):
    from PIL import Image
    from app.ocr import OCRText
    source = tmp_path / "valid.png"
    Image.new("RGB", (16, 16), "white").save(source)
    monkeypatch.setattr("app.processing.run_paddleocr", lambda path: OCRText("", [], ["PaddleOCR gagal"], 1, "paddleocr"))
    monkeypatch.setattr("app.processing.normalize_image", lambda source, destination: destination.write_bytes(source.read_bytes()))
    result = process_document(source, Settings(storage_path=str(tmp_path)))
    assert result.status == "PROCESSING_FAILED"
    assert result.extraction.extraction_method == "manual"
