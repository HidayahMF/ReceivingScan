from pathlib import Path
from .schemas import ExtractionResult

def normalize_upload_name(filename: str) -> str:
    return Path(filename).name

def manual_fallback() -> ExtractionResult:
    return ExtractionResult(warnings=["OCR/AI belum dijalankan; masukkan data secara manual"], extraction_method="manual")
