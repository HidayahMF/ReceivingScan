from pathlib import Path

from app.tesseract_ocr import run_tesseract

def test_tesseract_missing_binary_falls_back(monkeypatch, tmp_path: Path):
    image = tmp_path / "sample.png"
    image.write_bytes(b"not-used")
    monkeypatch.setattr("app.tesseract_ocr.subprocess.run", lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()))
    result = run_tesseract(image)
    assert result.text == ""
    assert result.engine == "tesseract"
    assert result.warnings
