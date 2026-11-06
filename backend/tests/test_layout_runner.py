import json
from pathlib import Path

from scripts.layout_runner import main

def test_layout_runner_reads_artifact_and_writes_structured_json(tmp_path: Path, monkeypatch):
    artifact = tmp_path / "quality.json"
    artifact.write_text(json.dumps({"file": "sample.jpg", "box_coordinate_system": "original_and_upright", "best": {"rotation": 270, "preprocessing": "contrast", "psm": 3, "quality_score": 0.8, "lines": [{"text": "Item Code Qty Unit", "confidence": 0.8, "box": [[10, 10], [150, 10], [150, 30], [10, 30]], "upright_box": [[10, 10], [150, 10], [150, 30], [10, 30]]}, {"text": "A100 45 Pcs", "confidence": 0.8, "box": [[10, 35], [110, 35], [110, 55], [10, 55]], "upright_box": [[10, 35], [110, 35], [110, 55], [10, 55]], "tokens": [{"text": "A100", "confidence": 0.8, "box": [[10, 35], [45, 35], [45, 55], [10, 55]], "upright_box": [[10, 35], [45, 35], [45, 55], [10, 55]]}, {"text": "45", "confidence": 0.8, "box": [[50, 35], [70, 35], [70, 55], [50, 55]], "upright_box": [[50, 35], [70, 35], [70, 55], [50, 55]]}, {"text": "Pcs", "confidence": 0.8, "box": [[75, 35], [100, 35], [100, 55], [75, 55]], "upright_box": [[75, 35], [100, 35], [100, 55], [75, 55]]}]}]}}), encoding="utf-8")
    output = tmp_path / "result.json"
    monkeypatch.setattr("sys.argv", ["layout_runner", str(artifact), "--output", str(output)])
    assert main() == 0
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["selected_candidate"]["rotation"] == 270
    assert result["structured"]["items"][0]["document_qty"] == "45"
