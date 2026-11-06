import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

parser = argparse.ArgumentParser(description="Validate OCR artifact coordinate metadata without rerunning OCR")
parser.add_argument("artifact", type=Path)
args = parser.parse_args()
payload = json.loads(args.artifact.read_text(encoding="utf-8"))
best = payload.get("best") or {}
lines = best.get("lines", [])
tokens = [token for line in lines for token in line.get("tokens", [])]
has_upright = bool(tokens) and all("upright_box" in token for token in tokens)
original_size = payload.get("original_size") or [None, None]
rotation = best.get("rotation")
upright_size = [original_size[1], original_size[0]] if rotation in (90, 270) and all(isinstance(value, (int, float)) for value in original_size) else original_size
boxes = [point for line in lines for point in (line.get("box") or [])]
extents = {"min_x": min((point[0] for point in boxes), default=None), "min_y": min((point[1] for point in boxes), default=None), "max_x": max((point[0] for point in boxes), default=None), "max_y": max((point[1] for point in boxes), default=None)}
report = {"artifact": str(args.artifact), "sample": payload.get("file"), "rotation": rotation, "original_size": original_size, "upright_size": upright_size, "box_extents": extents, "box_coordinate_system": payload.get("box_coordinate_system", "missing"), "line_count": len(lines), "token_count": len(tokens), "has_upright_box": has_upright, "geometry_status": "usable" if has_upright and payload.get("box_coordinate_system") == "original_and_upright" else "unsafe_to_migrate", "warnings": []}
if payload.get("geometry_migration", {}).get("status") == "verified_from_legacy_runner_code": report["geometry_status"] = "usable_migrated_legacy"
if not has_upright: report["warnings"].append("Artifact lacks upright_box per token; do not join tokens from original box alone")
if payload.get("box_coordinate_system") != "original_and_upright": report["warnings"].append("Artifact lacks explicit coordinate-system metadata")
if not original_size or not rotation: report["warnings"].append("Original dimensions or selected rotation are missing")
print(json.dumps(report, ensure_ascii=False, indent=2))
