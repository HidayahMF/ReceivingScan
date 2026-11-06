from pathlib import Path
import json

from app.config import Settings
from app.vision import OllamaVisionAdapter

class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = json.dumps(payload).encode()
    def __enter__(self): return self
    def __exit__(self, *_): return None
    def read(self): return self.payload

def test_ollama_structured_response_is_validated(monkeypatch, tmp_path: Path):
    image = tmp_path / "image.png"
    image.write_bytes(b"local-test-image")
    payload = {"response": json.dumps({"po_number": None, "items": [{"document_qty": None, "actual_qty": None}]})}
    monkeypatch.setattr("app.vision.urlopen", lambda *args, **kwargs: FakeResponse(payload))
    result = OllamaVisionAdapter(Settings(enable_local_vlm=True, ollama_model="local-test")).extract(image)
    assert result.result is not None
    assert result.result.po_number is None
    assert result.result.items[0].document_qty is None

def test_ollama_failure_returns_warning(monkeypatch, tmp_path: Path):
    image = tmp_path / "image.png"
    image.write_bytes(b"local-test-image")
    def fail(*args, **kwargs): raise TimeoutError("test timeout")
    monkeypatch.setattr("app.vision.urlopen", fail)
    result = OllamaVisionAdapter(Settings(enable_local_vlm=True, ollama_model="local-test", ollama_max_retries=1)).extract(image)
    assert result.result is None
    assert result.warnings
