from pathlib import Path
import json
import uuid

from .config import Settings
from .ocr import OCRText, normalize_image, run_paddleocr, to_schema, validate_image_file
from .schemas import ExtractionResult, ProcessingResponse, VisionResult
from .vision import OllamaVisionAdapter

def process_document(source: Path, settings: Settings) -> ProcessingResponse:
    validate_image_file(source, settings.max_upload_bytes)
    job_id = uuid.uuid4().hex
    processed = source.parent / f"{job_id}.processed.png"
    warnings: list[str] = []
    try:
        normalize_image(source, processed)
        ocr = to_schema(run_paddleocr(processed))
        extraction = ExtractionResult(warnings=list(ocr.warnings) or ["Hasil AI wajib diperiksa operator"], extraction_method=ocr.engine if ocr.engine != "none" and ocr.text else "manual")
        vision = VisionResult()
        if settings.enable_local_vlm and settings.ollama_model:
            vision = OllamaVisionAdapter(settings).extract(processed)
            if vision.result is not None:
                extraction = vision.result
                extraction.extraction_method = "ollama_vision"
                extraction.warnings = list(dict.fromkeys(extraction.warnings + ocr.warnings + ["Hasil AI wajib diperiksa operator"]))
            warnings.extend(vision.warnings)
        else:
            warnings.append("Vision AI lokal dinonaktifkan; gunakan OCR/manual review")
        extraction.warnings = list(dict.fromkeys(extraction.warnings + warnings))
        artifact = source.parent / f"{job_id}.ocr.json"
        artifact.write_text(json.dumps({"job_id": job_id, "ocr": ocr.model_dump(mode="json"), "vision": vision.model_dump(mode="json"), "extraction": extraction.model_dump(mode="json")}, ensure_ascii=False, indent=2), encoding="utf-8")
        status = "PROCESSING_FAILED" if ocr.engine == "paddleocr" and not ocr.text else "NEEDS_REVIEW"
        return ProcessingResponse(job_id=job_id, status=status, original_path=str(source), processed_path=str(processed), ocr=ocr, vision=vision, extraction=extraction)
    except Exception as error:
        warnings.append(f"Pemrosesan gagal: {type(error).__name__}; gunakan input manual")
        return ProcessingResponse(job_id=job_id, status="PROCESSING_FAILED", original_path=str(source), processed_path=str(processed) if processed.exists() else None, ocr=to_schema(OCRText("", [], warnings, 0, "none")), vision=VisionResult(warnings=warnings), extraction=ExtractionResult(warnings=warnings, extraction_method="manual"))
