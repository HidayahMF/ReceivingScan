from pathlib import Path
import pytest

from app.ocr import run_paddleocr, validate_image_file

def test_ocr_missing_dependency_falls_back(monkeypatch, tmp_path: Path):
    # This test does not download a model or require sample documents.
    monkeypatch.setitem(__import__('sys').modules, 'paddleocr', None)
    result = run_paddleocr(tmp_path / "not-used.png")
    assert result.text == ""
    assert result.warnings

def test_upload_validation_rejects_unknown_extension(tmp_path: Path):
    source = tmp_path / "document.txt"
    source.write_text("not an image")
    with pytest.raises(ValueError):
        validate_image_file(source, 1024)

def test_upload_validation_rejects_fake_image_content(tmp_path: Path):
    source = tmp_path / "document.png"
    source.write_text("not an image")
    with pytest.raises(ValueError):
        validate_image_file(source, 1024)
