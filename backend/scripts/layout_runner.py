import argparse
import importlib
import json
from pathlib import Path
import sys

def check_dependencies() -> None:
    for module_name in ("pydantic", "app.layout_extraction"):
        importlib.import_module(module_name)

def main() -> int:
    parser = argparse.ArgumentParser(description="Run layout reconstruction in an isolated container")
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    check_dependencies()
    if not args.artifact.is_file():
        raise SystemExit(f"Artifact not found: {args.artifact}")
    from app.layout_extraction import extract_structured, reconstruct_layout
    payload = json.loads(args.artifact.read_text(encoding="utf-8"))
    best = payload.get("best")
    if not best or not isinstance(best.get("lines"), list):
        raise SystemExit("Artifact has no usable best.lines; do not infer from raw quality failures")
    if payload.get("box_coordinate_system") != "original_and_upright" or not any("upright_box" in token for line in best["lines"] for token in line.get("tokens", [])):
        raise SystemExit("Artifact geometry is unsafe_to_migrate: upright_box and explicit coordinate metadata are required")
    lines = [{**line, "box": line.get("upright_box", line.get("box")), "original_box": line.get("box")} for line in best["lines"]]
    layout = reconstruct_layout(lines, rotation=0, original_size=None)
    structured = extract_structured(layout)
    result = {"source_artifact": str(args.artifact), "sample": payload.get("file"), "selected_candidate": {key: best.get(key) for key in ("rotation", "preprocessing", "psm", "quality_score")}, "layout": layout.model_dump(mode="json"), "structured": structured.model_dump(mode="json"), "ground_truth_status": "not_provided", "accuracy_status": "not_calculated"}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"dependency_check": "passed", "output": str(args.output), "lines": len(layout.lines), "items": len(structured.items)}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
