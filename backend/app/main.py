from pathlib import Path
from uuid import uuid4
from fastapi import FastAPI, File, HTTPException, UploadFile
from .config import get_settings
from .processing import process_document
from .schemas import ExtractionResult, HealthResponse, ProcessingResponse
from .services import manual_fallback
from .schemas import UniversalOCRResult
from .universal_ocr import scan_document

settings = get_settings()
app = FastAPI(title="BMC Receiving AI API", version="0.1.0")
jobs: dict[str, ProcessingResponse] = {}

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="backend")

@app.get("/ready", response_model=HealthResponse)
def ready() -> HealthResponse:
    return HealthResponse(status="ready", service="backend")

@app.get("/api/v1/receiving/draft", response_model=ExtractionResult)
def new_draft() -> ExtractionResult:
    return manual_fallback()

@app.post("/api/v1/ocr/scan", response_model=UniversalOCRResult)
async def universal_ocr_scan(file: UploadFile = File(...)) -> UniversalOCRResult:
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}
    if extension not in allowed_extensions:
        raise HTTPException(status_code=415, detail="Format harus JPG, PNG, WebP, atau PDF")
    target_dir = Path(settings.storage_path) / "ocr-originals"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{extension}"
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Ukuran dokumen melebihi batas")
    target.write_bytes(data)
    try:
        return scan_document(target)
    except (OSError, RuntimeError, ValueError) as error:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"OCR gagal: {error}") from error

@app.post("/api/v1/receiving/process", response_model=ProcessingResponse)
async def process_upload(file: UploadFile = File(...)) -> ProcessingResponse:
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    allowed = {value.strip() for value in settings.allowed_image_types.split(",")}
    if file.content_type not in allowed or extension not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=415, detail="Unggah file JPG, PNG, atau WebP")
    target_dir = Path(settings.storage_path) / "originals"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid4().hex}{extension}"
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="Ukuran gambar melebihi batas")
    target.write_bytes(data)
    try:
        response = process_document(target, settings)
    except ValueError as error:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(error)) from error
    jobs[response.job_id] = response
    return response

@app.get("/api/v1/receiving/process/{job_id}", response_model=ProcessingResponse)
def get_processing(job_id: str) -> ProcessingResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    return jobs[job_id]

@app.put("/api/v1/receiving/process/{job_id}/review", response_model=ProcessingResponse)
def update_review(job_id: str, extraction: ExtractionResult) -> ProcessingResponse:
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job tidak ditemukan")
    current = jobs[job_id]
    extraction.extraction_method = "operator_review"
    extraction.warnings = list(dict.fromkeys(extraction.warnings + ["Hasil sudah diedit operator; belum disimpan ke SQL Server"]))
    updated = current.model_copy(update={"extraction": extraction, "status": "NEEDS_REVIEW"})
    jobs[job_id] = updated
    return updated
