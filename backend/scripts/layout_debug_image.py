import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

parser = argparse.ArgumentParser(description="Render OCR/layout debug overlay without rerunning OCR")
parser.add_argument("artifact", type=Path)
parser.add_argument("image", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
payload = json.loads(args.artifact.read_text(encoding="utf-8"))
best = payload["best"]
with Image.open(args.image) as source:
    image = source.convert("RGB")
    draw = ImageDraw.Draw(image)
    for index, line in enumerate(best.get("lines", []), start=1):
        box = line.get("box") or line.get("upright_box")
        if not box: continue
        points = [(int(point[0]), int(point[1])) for point in box]
        draw.line(points + [points[0]], fill=(255, 40, 40), width=2)
        draw.text(points[0], f"L{index}: {line.get('text', '')[:40]}", fill=(255, 0, 0))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(args.output)
print(json.dumps({"output": str(args.output), "lines": len(best.get("lines", []))}))
