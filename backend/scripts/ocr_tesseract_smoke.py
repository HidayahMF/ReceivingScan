import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tesseract_ocr import run_tesseract, validate_tesseract_image

parser = argparse.ArgumentParser(description="Real local Tesseract OCR smoke test")
parser.add_argument("image", type=Path)
parser.add_argument("--language", default="eng")
args = parser.parse_args()
validate_tesseract_image(args.image, 10 * 1024 * 1024)
started = time.perf_counter()
process = psutil.Process()
before = process.memory_info().rss / 1024 / 1024
result = run_tesseract(args.image, args.language)
after = process.memory_info().rss / 1024 / 1024
payload = {"candidate": "tesseract-local", "file": args.image.name, "sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(), "bytes": args.image.stat().st_size, "runtime": {"python": platform.python_version(), "platform": platform.platform()}, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "memory_before_mb": round(before, 2), "memory_after_mb": round(after, 2), "ocr": result.model_dump(mode="json"), "status": "SUCCESS" if result.text else "NO_TEXT"}
print(json.dumps(payload, ensure_ascii=False, indent=2))
sys.exit(0 if result.text else 2)
