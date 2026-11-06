import json
from pathlib import Path

samples = sorted(path for path in Path("samples").iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
output = Path("docs/ground-truth.json")
payload = {"status": "manual_entry_required", "documents": [{"file": path.name, "sha256": None, "verified_by": None, "fields": {"document_number": None, "document_date": None, "partner_name": None, "po_number": None, "items": []}} for path in samples]}
output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Created blank ground-truth template for {len(samples)} samples: {output}")
