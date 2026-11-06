import argparse
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

parser = argparse.ArgumentParser(description="Render original/upright OCR geometry overlays")
parser.add_argument("artifact", type=Path)
parser.add_argument("image", type=Path)
parser.add_argument("output_dir", type=Path)
args = parser.parse_args()
payload = json.loads(args.artifact.read_text(encoding="utf-8"))
best = payload.get("best") or {}
args.output_dir.mkdir(parents=True, exist_ok=True)
with Image.open(args.image) as source:
    original = source.convert("RGB")
    rotation = best.get("rotation", 0)
    upright = original.rotate(rotation, expand=True) if rotation else original.copy()
    overlays = {"original": original.copy(), "upright": upright, "rows": upright.copy()}
    draws = {name: ImageDraw.Draw(image) for name, image in overlays.items()}
    for index, line in enumerate(best.get("lines", []), 1):
        for name, key, color in (("original", "box", "red"), ("upright", "upright_box", "blue"), ("rows", "upright_box", "green")):
            box = line.get(key)
            if not box: continue
            points = [(int(p[0]), int(p[1])) for p in box]
            draws[name].line(points + [points[0]], fill=color, width=2)
            draws[name].text(points[0], f"L{index} {line.get('text','')[:24]}", fill=color)
    for name, image in overlays.items(): image.save(args.output_dir / f"{name}.png")
print(json.dumps({"output_dir": str(args.output_dir), "has_upright": all("upright_box" in line for line in best.get("lines", [])), "rotation": rotation, "status": "usable" if all("upright_box" in line for line in best.get("lines", [])) else "legacy_original_only"}))
