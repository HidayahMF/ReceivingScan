import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.geometry import original_to_upright, upright_to_original

parser = argparse.ArgumentParser(description="Audit PIL rotation and legacy OCR coordinate mapping")
parser.add_argument("artifact", type=Path)
args = parser.parse_args()
payload = json.loads(args.artifact.read_text(encoding="utf-8"))
best = payload.get("best") or {}
width, height = payload.get("original_size", [None, None])
rotation = best.get("rotation")
corners = [[0, 0], [width, 0], [width, height], [0, height]] if width and height else []
rows = []
for point in corners:
    upright = original_to_upright(point, width, height, rotation or 0)
    recovered = upright_to_original(upright, width, height, rotation or 0)
    legacy = [height - upright[1], upright[0]] if rotation == 270 else None
    recovered_from_legacy = [height - legacy[0], height - legacy[1]] if legacy else None
    rows.append({"original": point, "upright": upright, "round_trip_original": recovered, "legacy_box": legacy, "legacy_recovered_original": recovered_from_legacy})
report = {"artifact": str(args.artifact), "original_size": [width, height], "upright_size": [height, width] if rotation in (90, 270) else [width, height], "rotation": rotation, "box_coordinate_system": payload.get("box_coordinate_system", "missing"), "legacy_line_count": len(best.get("lines", [])), "legacy_has_tokens": any(line.get("tokens") for line in best.get("lines", [])), "corners": rows, "warnings": []}
if payload.get("box_coordinate_system") != "original_and_upright": report["warnings"].append("Artifact metadata is legacy or missing; visual overlay is required before spatial joins")
print(json.dumps(report, ensure_ascii=False, indent=2))
