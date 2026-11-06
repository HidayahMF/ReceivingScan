import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.ocr import normalize_image, validate_image_file

parser = argparse.ArgumentParser(description="Isolated PaddleOCR 2.x compatibility candidate")
parser.add_argument("image", type=Path)
parser.add_argument("--workdir", type=Path, default=Path("/tmp/ocr-compat-legacy"))
args = parser.parse_args()

validate_image_file(args.image, 10 * 1024 * 1024)
args.workdir.mkdir(parents=True, exist_ok=True)
processed = args.workdir / f"{args.image.stem}.processed.png"
started = time.perf_counter()
process = psutil.Process()
memory_before = process.memory_info().rss / 1024 / 1024
payload = {"candidate": "paddleocr-2.7.3-paddlepaddle-2.6.2-ppocrv3-mobile", "file": args.image.name, "sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(), "bytes": args.image.stat().st_size, "runtime": {"python": platform.python_version(), "platform": platform.platform()}, "configuration": {"use_angle_cls": False, "use_mkldnn": False}}
try:
    normalize_image(args.image, processed)
    import paddle
    import paddleocr
    from paddleocr import PaddleOCR
    payload["runtime"].update({"paddle": paddle.__version__, "paddleocr": getattr(paddleocr, "__version__", "unknown")})
    engine = PaddleOCR(use_angle_cls=False, lang="en", use_gpu=False, use_mkldnn=False, show_log=False)
    pages = engine.ocr(str(processed), cls=False)
    lines = pages[0] if pages and pages[0] else []
    texts = [str(line[1][0]) for line in lines]
    scores = [float(line[1][1]) for line in lines]
    boxes = [line[0] for line in lines]
    payload["ocr"] = {"text": "\n".join(texts), "boxes": boxes, "scores": scores, "lines": len(lines)}
    payload["status"] = "SUCCESS" if texts else "NO_TEXT"
except Exception as error:
    payload["status"] = "RUNTIME_FAILURE"
    payload["error"] = f"{type(error).__name__}: {error}"
    payload["ocr"] = {"text": "", "boxes": [], "scores": []}
finally:
    payload["duration_ms"] = round((time.perf_counter() - started) * 1000, 2)
    payload["memory_before_mb"] = round(memory_before, 2)
    payload["memory_after_mb"] = round(process.memory_info().rss / 1024 / 1024, 2)

print(json.dumps(payload, ensure_ascii=False, indent=2))
sys.exit({"SUCCESS": 0, "NO_TEXT": 2, "RUNTIME_FAILURE": 1}[payload["status"]])
