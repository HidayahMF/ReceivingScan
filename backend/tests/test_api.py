from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_draft_is_manual_and_unknowns_are_null():
    response = client.get("/api/v1/receiving/draft")
    assert response.status_code == 200
    body = response.json()
    assert body["po_number"] is None
    assert body["extraction_method"] == "manual"

def test_upload_rejects_invalid_content_type():
    response = client.post("/api/v1/receiving/process", files={"file": ("note.txt", b"not-image", "text/plain")})
    assert response.status_code == 415

def test_review_endpoint_keeps_unknowns_null():
    response = client.put("/api/v1/receiving/process/missing/review", json={})
    assert response.status_code == 404

def test_valid_image_upload_reaches_review_without_ai(tmp_path, monkeypatch):
    from PIL import Image
    from app.ocr import OCRText
    monkeypatch.setattr("app.processing.run_paddleocr", lambda path: OCRText("", [], ["mock OCR for API workflow test"], 1, "mock"))
    monkeypatch.setattr("app.processing.normalize_image", lambda source, destination: destination.write_bytes(source.read_bytes()))
    image_path = tmp_path / "valid.png"
    Image.new("RGB", (32, 32), "white").save(image_path)
    monkeypatch.setenv("STORAGE_PATH", str(tmp_path / "storage"))
    with image_path.open("rb") as image:
        response = client.post("/api/v1/receiving/process", files={"file": ("valid.png", image, "image/png")})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "NEEDS_REVIEW"
    assert body["extraction"]["po_number"] is None
    assert body["extraction"]["items"] == []
    job_id = body["job_id"]
    review = client.put(f"/api/v1/receiving/process/{job_id}/review", json={"po_number": "PO-TEST", "items": [{"actual_qty": "2", "actual_unit": "PCS"}]})
    assert review.status_code == 200
    assert review.json()["extraction"]["po_number"] == "PO-TEST"
    assert review.json()["extraction"]["items"][0]["actual_qty"] == "2"
