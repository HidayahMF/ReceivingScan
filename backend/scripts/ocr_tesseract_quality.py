import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import time
import sys

import psutil
from PIL import Image, ImageEnhance, ImageOps
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.geometry import transform_box

parser = argparse.ArgumentParser(description="Tesseract quality matrix: rotation, preprocessing, and PSM")
parser.add_argument("image", type=Path)
parser.add_argument("--output", type=Path, default=None)
parser.add_argument("--language", default="eng")
args = parser.parse_args()

PSMS = (3, 4, 6, 11)
ROTATIONS = (0, 90, 180, 270)

def preprocess(image: Image.Image, name: str) -> Image.Image:
    if name == "original":
        return image.copy()
    gray = ImageOps.grayscale(image)
    if name == "grayscale":
        return gray
    if name == "threshold":
        return gray.point(lambda pixel: 255 if pixel > 170 else 0)
    if name == "contrast":
        return ImageEnhance.Contrast(gray).enhance(1.6)
    raise ValueError(name)

def tsv_result(path: Path, psm: int, language: str, width: int, height: int, angle: int) -> dict:
    command = ["tesseract", str(path), "stdout", "--psm", str(psm), "-l", language, "tsv"]
    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    lines: list[dict] = []
    for row in csv.DictReader(io.StringIO(completed.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
            left, top = float(row["left"]), float(row["top"])
            box = [[left, top], [left + float(row["width"]), top], [left + float(row["width"]), top + float(row["height"])], [left, top + float(row["height"])]]
        except (KeyError, TypeError, ValueError):
            continue
        if text and confidence >= 0:
            lines.append({"text": text, "confidence": round(confidence / 100, 4), "box": transform_box(box, width, height, angle, "to_original"), "upright_box": box})
    lines.sort(key=lambda line: (min(point[1] for point in line["box"]), min(point[0] for point in line["box"])))
    text = "\n".join(line["text"] for line in lines)
    avg_confidence = sum(line["confidence"] for line in lines) / len(lines) if lines else 0
    alnum_ratio = sum(character.isalnum() for character in text) / max(1, len(text))
    quality = round(avg_confidence * (0.5 + 0.5 * alnum_ratio) * (1 + min(len(lines), 40) / 100), 6)
    return {"text": text, "lines": lines, "average_confidence": round(avg_confidence, 4), "alnum_ratio": round(alnum_ratio, 4), "quality_score": quality}

def main() -> int:
    with Image.open(args.image) as source:
        source = ImageOps.exif_transpose(source).convert("RGB")
        original_width, original_height = source.size
        exif_orientation = source.getexif().get(274)
        records = []
        process = psutil.Process()
        started_all = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="tesseract-quality-") as directory:
            workdir = Path(directory)
            for angle in ROTATIONS:
                rotated = source.rotate(angle, expand=True) if angle else source.copy()
                for preprocessing in ("original", "grayscale", "threshold", "contrast"):
                    variant = preprocess(rotated, preprocessing)
                    variant_path = workdir / f"r{angle}-{preprocessing}.png"
                    variant.save(variant_path)
                    for psm in PSMS:
                        started = time.perf_counter()
                        try:
                            result = tsv_result(variant_path, psm, args.language, original_width, original_height, angle)
                            status = "SUCCESS" if result["text"] else "NO_TEXT"
                            error = None
                        except Exception as caught:
                            result = {"text": "", "lines": [], "average_confidence": 0, "alnum_ratio": 0, "quality_score": 0}
                            status = "RUNTIME_FAILURE"
                            error = f"{type(caught).__name__}: {caught}"
                        records.append({"rotation": angle, "preprocessing": preprocessing, "psm": psm, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "status": status, "error": error, **result})
        successes = [record for record in records if record["status"] == "SUCCESS"]
        best = max(successes, key=lambda record: record["quality_score"], default=None)
        payload = {"candidate": "tesseract-quality-matrix", "file": args.image.name, "sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(), "bytes": args.image.stat().st_size, "runtime": {"python": platform.python_version(), "platform": platform.platform()}, "exif_orientation": exif_orientation, "original_size": [original_width, original_height], "box_coordinate_system": "original_and_upright", "total_duration_ms": round((time.perf_counter() - started_all) * 1000, 2), "memory_after_mb": round(process.memory_info().rss / 1024 / 1024, 2), "language": args.language, "best": best, "records": records}
    output = args.output or args.image.with_suffix(".tesseract-quality.json")
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "sample": args.image.name, "combinations": len(records), "successful_combinations": len(successes), "best": {key: best[key] for key in ("rotation", "preprocessing", "psm", "quality_score")} if best else None}, ensure_ascii=False, indent=2))
    return 0 if best else 1

raise SystemExit(main())
