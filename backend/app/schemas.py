from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field

class OCRResult(BaseModel):
    text: str = ""
    boxes: list[list[list[float]]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float = 0
    engine: str = "none"

class Evidence(BaseModel):
    text: str
    box: list[list[float]]
    confidence: float | None = None
    source: str

class FieldExtraction(BaseModel):
    value: str | None = None
    status: str = "missing"
    evidence: list[Evidence] = Field(default_factory=list)
    rejected: list[dict] = Field(default_factory=list)

class LayoutExtraction(BaseModel):
    lines: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

class StructuredExtraction(BaseModel):
    document_number: FieldExtraction
    document_date: FieldExtraction
    po_number: FieldExtraction
    partner_name: FieldExtraction
    items: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    rejected_candidates: list[dict] = Field(default_factory=list)
    regions: list[dict] = Field(default_factory=list)

class VisionResult(BaseModel):
    result: "ExtractionResult | None" = None
    warnings: list[str] = Field(default_factory=list)
    duration_ms: float = 0
    model: str | None = None

class ReceivingItem(BaseModel):
    line_number: int | None = None
    supplier_item_code: str | None = None
    internal_item_code: str | None = None
    description: str | None = None
    document_qty: Decimal | None = None
    document_unit: str | None = None
    actual_qty: Decimal | None = None
    actual_unit: str | None = None
    needs_review: bool = True

class ExtractionResult(BaseModel):
    document_number: str | None = None
    document_date: date | None = None
    po_number: str | None = None
    partner_name: str | None = None
    vehicle_number: str | None = None
    driver_name: str | None = None
    items: list[ReceivingItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=lambda: ["Requires operator verification"])
    extraction_method: str = "manual"

class ProcessingResponse(BaseModel):
    job_id: str
    status: str
    original_path: str
    processed_path: str | None = None
    ocr: OCRResult
    vision: VisionResult
    extraction: ExtractionResult

class HealthResponse(BaseModel):
    status: str
    service: str

class UniversalWord(BaseModel):
    text: str
    confidence: float | None = None
    bbox: list[list[float]]
    page_number: int
    line_number: int | None = None
    reading_order: int
    needs_review: bool = False

class UniversalPage(BaseModel):
    page_number: int
    text: str
    lines: list[dict] = Field(default_factory=list)
    words: list[UniversalWord] = Field(default_factory=list)

class UniversalOCRResult(BaseModel):
    status: str
    full_text: str
    pages: list[UniversalPage] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    processing_metadata: dict = Field(default_factory=dict)
