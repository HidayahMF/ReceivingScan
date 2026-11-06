import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

from PIL import Image, ImageEnhance, ImageOps

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.geometry import transform_box

def run(args):
    with Image.open(args.image) as raw:
        source = ImageOps.exif_transpose(raw).convert("RGB")
        original_size = list(source.size)
        upright = source.rotate(270, expand=True)
        upright_size = list(upright.size)
        processed = ImageEnhance.Contrast(ImageOps.grayscale(upright)).enhance(1.6)
        with tempfile.TemporaryDirectory(prefix="tesseract-targeted-") as work:
            image = Path(work) / "upright-contrast.png"
            processed.save(image)
            completed = subprocess.run(["tesseract", str(image), "stdout", "--psm", "3", "-l", args.language, "tsv"], check=True, capture_output=True, text=True, timeout=120)
    words = []
    for row in csv.DictReader(io.StringIO(completed.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row["conf"])
            box = [[float(row["left"]), float(row["top"])], [float(row["left"]) + float(row["width"]), float(row["top"])], [float(row["left"]) + float(row["width"]), float(row["top"]) + float(row["height"])], [float(row["left"]), float(row["top"]) + float(row["height"])]]
        except (KeyError, ValueError):
            continue
        if not text or confidence < 0: continue
        words.append({"text": text, "confidence": round(confidence / 100, 4), "upright_box": box, "original_box": transform_box(box, original_size[0], original_size[1], 270, "to_original"), "page": int(row.get("page_num") or 0), "block": int(row.get("block_num") or 0), "paragraph": int(row.get("par_num") or 0), "line": int(row.get("line_num") or 0), "word": int(row.get("word_num") or 0)})
    words.sort(key=lambda word: (word["upright_box"][0][1], word["upright_box"][0][0]))
    rows = _rows(words)
    table = _table(rows)
    payload = {"candidate": "tesseract-targeted-rotation270-contrast-psm3", "file": args.image.name, "sha256": hashlib.sha256(args.image.read_bytes()).hexdigest(), "runtime": {"python": platform.python_version(), "platform": platform.platform()}, "original_size": original_size, "upright_size": upright_size, "rotation": 270, "preprocessing": "contrast", "psm": 3, "box_coordinate_system": "original_and_upright", "words": words, "rows": rows, "table": table, "structured": _structured(table), "warnings": ["All values require operator verification"], "duration_ms": None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "words": len(words), "rows": len(rows), "table_status": table["status"]}, ensure_ascii=False))

def _rows(words):
    rows = []
    for word in words:
        center = (word["upright_box"][0][1] + word["upright_box"][2][1]) / 2
        target = next((row for row in rows if abs(row["center_y"] - center) <= max(8, (word["upright_box"][2][1] - word["upright_box"][0][1]) * 0.6)), None)
        if target is None: rows.append({"center_y": center, "words": [word]})
        else: target["words"].append(word); target["center_y"] = sum((w["upright_box"][0][1] + w["upright_box"][2][1]) / 2 for w in target["words"]) / len(target["words"])
    result = []
    for index, row in enumerate(sorted(rows, key=lambda item: item["center_y"]), 1):
        ordered = sorted(row["words"], key=lambda word: word["upright_box"][0][0])
        result.append({"row": index, "text": " ".join(word["text"] for word in ordered), "words": ordered, "box": _union([word["upright_box"] for word in ordered])})
    return result

def _table(rows):
    headers = [row for row in rows if sum(marker in row["text"].lower() for marker in ("nama", "barang", "bt", "jumlah", "pcs", "tonase", "kg")) >= 2]
    body = [row for row in rows if any(token["text"].upper() in {"PCS", "BOX", "KG", "SET"} for token in row["words"]) and any(token["text"].isdigit() for token in row["words"])]
    if not headers or not body: return {"status": "missing", "header_rows": [row["row"] for row in headers], "candidate_rows": [row["row"] for row in body], "rejected": [{"reason": "table header or supported body row missing"}]}
    return {"status": "candidate", "header_rows": [row["row"] for row in headers], "candidate_rows": [row["row"] for row in body], "rejected": [{"reason": "candidate rows require manual item/code verification"}]}

def _structured(table):
    return {"document_number": None, "document_date": None, "partner_name": None, "po_number": None, "items": [], "table_status": table["status"], "status": "manual_review"}
def _union(boxes):
    points = [point for box in boxes for point in box]; left, top = min(p[0] for p in points), min(p[1] for p in points); right, bottom = max(p[0] for p in points), max(p[1] for p in points); return [[left, top], [right, top], [right, bottom], [left, bottom]]

parser = argparse.ArgumentParser()
parser.add_argument("image", type=Path)
parser.add_argument("--output", type=Path, required=True)
parser.add_argument("--language", default="eng")
args = parser.parse_args()
started = time.perf_counter()
run(args)
