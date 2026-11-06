import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Evaluate structured extraction only against manually verified ground truth")
parser.add_argument("ground_truth", type=Path)
parser.add_argument("structured_dir", type=Path)
args = parser.parse_args()
truth = json.loads(args.ground_truth.read_text(encoding="utf-8"))
if truth.get("status") != "manually_verified":
    raise SystemExit("Ground truth status is not manually_verified; accuracy will not be calculated")
results = []
for document in truth.get("documents", []):
    structured_path = args.structured_dir / f"{Path(document['file']).stem}.structured-extraction.json"
    if not structured_path.exists():
        results.append({"file": document["file"], "status": "missing_extraction"})
        continue
    predicted = json.loads(structured_path.read_text(encoding="utf-8"))["structured"]
    fields = {}
    for field in ("document_number", "document_date", "partner_name", "po_number"):
        expected = document["fields"].get(field)
        actual = (predicted.get(field) or {}).get("value")
        fields[field] = {"expected": expected, "actual": actual, "correct": expected is not None and expected == actual}
    results.append({"file": document["file"], "fields": fields})
print(json.dumps({"status": "evaluated", "documents": results}, ensure_ascii=False, indent=2))
