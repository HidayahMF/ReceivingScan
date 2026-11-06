import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.layout_extraction import extract_structured, reconstruct_layout

parser = argparse.ArgumentParser(description="Reconstruct OCR layout from an existing quality JSON artifact")
parser.add_argument("artifact", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
payload = json.loads(args.artifact.read_text(encoding="utf-8"))
best = payload.get("best")
if not best:
    raise SystemExit("Artifact has no best candidate; do not infer from raw quality failures")
layout = reconstruct_layout(best.get("lines", []))
structured = extract_structured(layout)
result = {"source_artifact": str(args.artifact), "sample": payload.get("file"), "selected_candidate": {key: best.get(key) for key in ("rotation", "preprocessing", "psm", "quality_score")}, "layout": layout.model_dump(mode="json"), "structured": structured.model_dump(mode="json"), "ground_truth_status": "not_provided", "accuracy_status": "not_calculated"}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"output": str(args.output), "lines": len(layout.lines), "items": len(structured.items)}, ensure_ascii=False))
