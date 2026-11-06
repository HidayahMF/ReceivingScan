from pathlib import Path

from PIL import Image

from app import tesseract_ocr

def test_quality_runner_defines_expected_matrix():
    script = (Path(__file__).parents[1] / "scripts" / "ocr_tesseract_quality.py").read_text(encoding="utf-8")
    assert "ROTATIONS = (0, 90, 180, 270)" in script
    assert "PSMS = (3, 4, 6, 11)" in script
    assert "threshold" in script
    assert "quality_score" in script

def test_tesseract_image_validation_accepts_png(tmp_path: Path):
    image = tmp_path / "sample.png"
    Image.new("RGB", (8, 8), "white").save(image)
    tesseract_ocr.validate_tesseract_image(image, 1024 * 1024)
