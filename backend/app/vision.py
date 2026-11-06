import base64
import json
import logging
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .config import Settings
from .schemas import ExtractionResult, VisionResult

logger = logging.getLogger(__name__)
VISION_PROMPT = """Extract only values visibly supported by this delivery document. Return JSON matching the supplied schema. Use null for unknown fields, never guess PO, supplier, item code, or quantity. Set needs_review true for ambiguous fields. Document quantity and actual_qty are different; actual_qty must remain null because it requires operator counting."""

class OllamaVisionAdapter:
    def __init__(self, settings: Settings):
        if not settings.enable_local_vlm or not settings.ollama_model:
            raise ValueError("Local VLM is disabled or no model is configured")
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout_seconds = settings.ollama_timeout_seconds
        self.max_retries = settings.ollama_max_retries

    def extract(self, image_path: Path, prompt: str = VISION_PROMPT) -> VisionResult:
        started = time.perf_counter()
        image_base64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = json.dumps({"model": self.model, "prompt": prompt, "images": [image_base64], "stream": False, "format": "json"}).encode("utf-8")
        request = Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with urlopen(request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read())
                extraction = ExtractionResult.model_validate_json(body["response"])
                return VisionResult(result=extraction, duration_ms=round((time.perf_counter() - started) * 1000, 2), model=self.model)
            except (HTTPError, URLError, TimeoutError, OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                last_error = error
                logger.warning("Ollama attempt %s/%s failed: %s", attempt + 1, self.max_retries + 1, type(error).__name__)
        return VisionResult(warnings=[f"Vision AI lokal tidak tersedia: {type(last_error).__name__ if last_error else 'unknown error'}"], duration_ms=round((time.perf_counter() - started) * 1000, 2), model=self.model)
