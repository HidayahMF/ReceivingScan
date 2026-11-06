from app.ocr_metrics import cer, wer

def test_metrics_zero_for_identical_text():
    assert cer("Alpha 123", "Alpha 123") == 0
    assert wer("Alpha 123", "Alpha 123") == 0
