from pathlib import Path
import csv
import io
import subprocess
import time
from .universal_ocr import _tesseract_executable
from typing import Any

from .ocr import ALLOWED_EXTENSIONS
from .schemas import OCRResult

def validate_tesseract_image(path: Path, max_bytes: int) -> None:
    if not path.is_file() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("File gambar tidak ditemukan atau format tidak didukung")
    if path.stat().st_size == 0 or path.stat().st_size > max_bytes:
        raise ValueError("Ukuran gambar kosong atau melebihi batas upload")
    try:
        from PIL import Image
        with Image.open(path) as image:
            image.verify()
    except Exception as error:
        raise ValueError("Isi file bukan gambar valid") from error

def run_tesseract(image_path: Path, language: str = "eng") -> OCRResult:
    started = time.perf_counter()
    executable = _tesseract_executable()
    if executable is None:
        return OCRResult(warnings=["Tesseract tidak terpasang. Install Tesseract OCR dan tambahkan ke PATH, atau set TESSERACT_CMD"], duration_ms=_duration(started), engine="tesseract")
    command = [executable, str(image_path), "stdout", "--psm", "6", "-l", language, "tsv"]
    try:
        completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
    except FileNotFoundError as error:
        return OCRResult(warnings=["Tesseract binary tidak tersedia"], duration_ms=_duration(started), engine="tesseract")
    except subprocess.TimeoutExpired:
        return OCRResult(warnings=["Tesseract timeout"], duration_ms=_duration(started), engine="tesseract")
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()[:500]
        return OCRResult(warnings=[f"Tesseract gagal: {detail or 'process error'}"], duration_ms=_duration(started), engine="tesseract")

    texts: list[str] = []
    boxes: list[list[list[float]]] = []
    scores: list[float] = []
    for row in csv.DictReader(io.StringIO(completed.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
            left, top = float(row["left"]), float(row["top"])
            width, height = float(row["width"]), float(row["height"])
        except (KeyError, TypeError, ValueError):
            continue
        if text and confidence >= 0:
            texts.append(text)
            scores.append(confidence / 100)
            boxes.append([[left, top], [left + width, top], [left + width, top + height], [left, top + height]])
    warnings = [] if texts else ["Tesseract tidak menghasilkan teks"]
    return OCRResult(text="\n".join(texts), boxes=boxes, warnings=warnings, duration_ms=_duration(started), engine="tesseract")

def _duration(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 2)
