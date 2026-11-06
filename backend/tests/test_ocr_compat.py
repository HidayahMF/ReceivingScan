from pathlib import Path

def test_compatibility_runner_contains_isolated_candidate():
    script = Path(__file__).parents[1] / "scripts" / "ocr_compat.py"
    content = script.read_text(encoding="utf-8")
    assert "PP-OCRv5_mobile_det" in content
    assert "use_doc_orientation_classify=False" in content
    assert "RUNTIME_FAILURE" in content
