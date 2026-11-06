import argparse
import json
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ocr import normalize_image, run_paddleocr

parser = argparse.ArgumentParser(description="Run local OCR on one sample; never uploads data")
parser.add_argument("image", type=Path)
args = parser.parse_args()

if not args.image.is_file():
    raise SystemExit(f"Not a file: {args.image}")

with tempfile.TemporaryDirectory(prefix="receiving-ocr-") as workdir:
    normalized = Path(workdir) / "normalized.png"
    normalize_image(args.image, normalized)
    result = run_paddleocr(normalized)
    print(json.dumps({"text": result.text, "boxes": result.boxes, "warnings": result.warnings, "duration_ms": result.duration_ms, "engine": result.engine}, ensure_ascii=False))
