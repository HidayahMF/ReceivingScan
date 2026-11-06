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

parser = argparse.ArgumentParser(description="Isolated real PaddleOCR compatibility candidate")
parser.add_argument("image", type=Path)
parser.add_argument("--workdir", type=Path, default=Path("/tmp/ocr-compat"))
parser.add_argument("--det-model", default="PP-OCRv5_mobile_det")
parser.add_argument("--rec-model", default="PP-OCRv5_mobile_rec")
args = parser.parse_args()

validate_image_file(args.image, 10 * 1024 * 1024)
args.workdir.mkdir(parents=True, exist_ok=True)
processed = args.workdir / f"{args.image.stem}.processed.png"
started = time.perf_counter()
process = psutil.Process()
memory_before = process.memory_info().rss / 1024 / 1024
payload = {
    "candidate": "paddleocr-3.3.0-paddlepaddle-3.3.1-mobile-no-orientation",
    "file": args.image.name,
    "sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(),
    "bytes": args.image.stat().st_size,
    "runtime": {"python": platform.python_version(), "platform": platform.platform()},
    "configuration": {"det_model": args.det_model, "rec_model": args.rec_model, "use_doc_orientation_classify": False, "use_doc_unwarping": False, "use_textline_orientation": False},
}
try:
    normalize_image(args.image, processed)
    from paddleocr import PaddleOCR
    import paddle
    import paddleocr
    payload["runtime"].update({"paddle": paddle.__version__, "paddleocr": getattr(paddleocr, "__version__", "unknown")})
    engine = PaddleOCR(
        text_detection_model_name=args.det_model,
        text_recognition_model_name=args.rec_model,
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )
    pages = list(engine.predict(str(processed)))
    texts = []
    boxes = []
    scores = []
    for page in pages:
        get = page.get if hasattr(page, "get") else lambda key, default=None: getattr(page, key, default)
        texts.extend(str(value) for value in (get("rec_texts", []) or []))
        raw_boxes = get("rec_polys", []) or []
        if hasattr(raw_boxes, "tolist"):
            raw_boxes = raw_boxes.tolist()
        boxes.extend(raw_boxes)
        raw_scores = get("rec_scores", []) or []
        if hasattr(raw_scores, "tolist"):
            raw_scores = raw_scores.tolist()
        scores.extend(float(value) for value in raw_scores)
    payload["ocr"] = {"text": "\n".join(texts), "boxes": boxes, "scores": scores, "pages": len(pages)}
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
