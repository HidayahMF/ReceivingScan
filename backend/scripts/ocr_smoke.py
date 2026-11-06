import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import psutil

# The script is executed as /app/scripts/ocr_smoke.py inside the image.
# Add the application root so the local `app` package is importable.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ocr import normalize_image, run_paddleocr, to_schema, validate_image_file

parser = argparse.ArgumentParser(description="Real local PaddleOCR smoke test; does not modify the source image")
parser.add_argument("image", type=Path)
parser.add_argument("--workdir", type=Path, default=Path("/tmp/receiving-ocr-smoke"))
args = parser.parse_args()

validate_image_file(args.image, 10 * 1024 * 1024)
args.workdir.mkdir(parents=True, exist_ok=True)
source_hash = hashlib.sha256(args.image.read_bytes()).hexdigest()
processed = args.workdir / f"{args.image.stem}.processed.png"
started = time.perf_counter()
memory_before = psutil.Process().memory_info().rss / 1024 / 1024
error: str | None = None
try:
    normalize_image(args.image, processed)
    result = to_schema(run_paddleocr(processed))
except Exception as caught:
    error = f"{type(caught).__name__}: {caught}"
    result = None
memory_after = psutil.Process().memory_info().rss / 1024 / 1024
payload = {"file": args.image.name, "sha256": source_hash, "bytes": args.image.stat().st_size, "runtime": {"python": platform.python_version(), "platform": platform.platform()}, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "memory_before_mb": round(memory_before, 2), "memory_after_mb": round(memory_after, 2), "ocr": result.model_dump(mode="json") if result is not None else None}
if error:
    payload["error"] = error
if result is None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(1)
print(json.dumps(payload, ensure_ascii=False, indent=2))
if any(warning.startswith("PaddleOCR gagal:") for warning in result.warnings):
    sys.exit(1)
sys.exit(0 if result.text else 2)
