import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Report legacy artifact geometry without unsafe migration")
parser.add_argument("artifact", type=Path)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
result = {"status": "unsafe_to_migrate", "reason": "Legacy artifact lacks explicit upright coordinates/tokens; no spatial join performed", "artifact": str(args.artifact), "rotation": best.get("rotation"), "original_size": payload.get("original_size"), "line_count": len(best.get("lines", [])), "recommendation": "Regenerate only rotation=270, preprocessing=contrast, PSM=3 with original_box/upright_box/token metadata"}
args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
