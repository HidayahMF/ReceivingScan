import argparse
import json
from pathlib import Path

legacy_width, legacy_height = 1600, 1200
original_width, original_height = 1200, 1600

def migrate_point(point):
    legacy_x, legacy_y = point
    # Legacy runner stored [H-y_rotated, x_rotated]. Recover both spaces.
    upright = [legacy_y, original_height - legacy_x]
    original = [original_height - legacy_x, original_height - legacy_y]
    return original, upright

def migrate_box(box):
    original, upright = zip(*(migrate_point(point) for point in box))
    return list(original), list(upright)

def migrate_payload(payload):
    best = payload.get("best") or {}
    if best.get("rotation") != 270 or payload.get("original_size") != [1200, 1600]:
        raise ValueError("This migration is only for the verified legacy 1200x1600 rotation=270 artifact")
    new_lines = []
    for line in best.get("lines", []):
        original_box, upright_box = migrate_box(line["box"])
        new_lines.append({**line, "box": original_box, "upright_box": upright_box, "tokens": [{"text": line["text"], "confidence": line.get("confidence", 0), "box": original_box, "upright_box": upright_box}]})
    return {**payload, "box_coordinate_system": "migrated_legacy_original_and_upright", "geometry_migration": {"status": "verified_from_legacy_runner_code", "source_coordinate_system": "legacy_rotation_270_[H-y_rotated,x_rotated]", "input_size": [legacy_width, legacy_height], "original_size": [original_width, original_height], "formula": "original=[H-legacy_x,H-legacy_y]; upright=[legacy_y,H-legacy_x]", "word_level": True}, "best": {**best, "lines": new_lines}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate the known legacy rotation-270 box transform without rerunning OCR")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    migrated = migrate_payload(json.loads(args.artifact.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(migrated, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "migrated", "output": str(args.output), "words": len(migrated["best"]["lines"]), "source_unchanged": True}, ensure_ascii=False))
