from dataclasses import dataclass
from pathlib import Path
import logging
import time
from typing import Any

from .schemas import OCRResult

logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

@dataclass(frozen=True)
class OCRText:
    text: str
    boxes: list[list[list[float]]]
    warnings: list[str]
    duration_ms: float
    engine: str

def validate_image_file(path: Path, max_bytes: int) -> None:
    if not path.is_file():
        raise ValueError("File gambar tidak ditemukan")
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Format gambar harus JPG, PNG, atau WebP")
    if path.stat().st_size == 0 or path.stat().st_size > max_bytes:
        raise ValueError("Ukuran gambar kosong atau melebihi batas upload")
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
    except Exception as error:
        raise ValueError("Isi file bukan gambar yang valid") from error

def normalize_image(source: Path, destination: Path) -> None:
    """Create a derivative; source remains immutable."""
    try:
        import cv2
        from PIL import Image, ImageOps
    except ImportError as error:
        raise RuntimeError("OpenCV/Pillow atau library sistem image processing belum tersedia; OCR processing tidak tersedia") from error
    try:
        with Image.open(source) as original:
            oriented = ImageOps.exif_transpose(original).convert("RGB")
            oriented.save(destination, format="PNG")
        image = cv2.imread(str(destination), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("File gambar tidak dapat dibaca")
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        # Estimate small document skew from foreground lines; leave ambiguous images unchanged.
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLinesP(edges, 1, 3.14159 / 180, 80, minLineLength=max(50, image.shape[1] // 5), maxLineGap=10)
        angles = [] if lines is None else [__import__('math').degrees(__import__('math').atan2(y2 - y1, x2 - x1)) for [[x1, y1, x2, y2]] in lines]
        angles = [angle for angle in angles if abs(angle) <= 15]
        if angles:
            angle = sum(angles) / len(angles)
            height, width = gray.shape[:2]
            matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1)
            gray = cv2.warpAffine(gray, matrix, (width, height), borderMode=cv2.BORDER_REPLICATE)
        if not cv2.imwrite(str(destination), gray):
            raise OSError("Gagal menyimpan gambar hasil normalisasi")
    except Exception:
        logger.exception("Image normalization failed for %s", source)
        raise

def run_paddleocr(image_path: Path) -> OCRText:
    started = time.perf_counter()
    try:
        from paddleocr import PaddleOCR
    except ImportError:
        return OCRText("", [], ["PaddleOCR belum terpasang; gunakan input manual"], (time.perf_counter() - started) * 1000, "none")
    try:
        engine: Any = PaddleOCR(use_doc_orientation_classify=True, use_doc_unwarping=True, use_textline_orientation=True)
        result = engine.predict(str(image_path))
        texts: list[str] = []
        boxes: list[list[list[float]]] = []
        for page in result:
            page_texts = page.get("rec_texts", []) if hasattr(page, "get") else getattr(page, "rec_texts", [])
            page_boxes = page.get("rec_polys", []) if hasattr(page, "get") else getattr(page, "rec_polys", [])
            texts.extend(str(value) for value in page_texts)
            boxes.extend(_to_nested_lists(page_boxes))
        return OCRText("\n".join(texts), boxes, [], (time.perf_counter() - started) * 1000, "paddleocr")
    except Exception as error:
        logger.exception("PaddleOCR failed")
        return OCRText("", [], [f"PaddleOCR gagal: {type(error).__name__}; gunakan input manual"], (time.perf_counter() - started) * 1000, "paddleocr")

def to_schema(result: OCRText) -> OCRResult:
    return OCRResult(text=result.text, boxes=result.boxes, warnings=result.warnings, duration_ms=round(result.duration_ms, 2), engine=result.engine)

def _to_nested_lists(value: Any) -> list[list[list[float]]]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [[[float(point[0]), float(point[1])] for point in polygon] for polygon in value]
