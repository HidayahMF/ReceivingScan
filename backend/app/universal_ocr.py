from pathlib import Path
import csv
import io
import subprocess
import tempfile
import time
import os
import shutil

from .schemas import UniversalOCRResult, UniversalPage, UniversalWord

def render_pages(path: Path, workdir: Path) -> list[Path]:
    if path.suffix.lower() != ".pdf": return [path]
    try:
        import fitz
    except ImportError as error:
        raise RuntimeError("PDF OCR membutuhkan PyMuPDF") from error
    pages = []
    with fitz.open(path) as document:
        for index, page in enumerate(document):
            output = workdir / f"page-{index + 1}.png"
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pixmap.save(output)
            pages.append(output)
    return pages

def scan_document(path: Path, language: str = "eng") -> UniversalOCRResult:
    started = time.perf_counter()
    warnings: list[str] = []
    with tempfile.TemporaryDirectory(prefix="universal-ocr-") as directory:
        pages = render_pages(path, Path(directory))
        output_pages = [_scan_page(page, index, language, warnings) for index, page in enumerate(pages, 1)]
    full_text = "\n\n".join(page.text for page in output_pages)
    status = "completed" if full_text or not warnings else "failed"
    return UniversalOCRResult(status=status, full_text=full_text, pages=output_pages, warnings=warnings, processing_metadata={"engine": "tesseract", "language": language, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "page_count": len(output_pages)})

def _scan_page(path: Path, page_number: int, language: str, warnings: list[str]) -> UniversalPage:
    executable = _tesseract_executable()
    if executable is None:
        warnings.append("Tesseract tidak terpasang. Install Tesseract OCR dan tambahkan ke PATH, atau set TESSERACT_CMD.")
        return UniversalPage(page_number=page_number, text="", lines=[], words=[])
    try:
        completed = subprocess.run([executable, str(path), "stdout", "--psm", "3", "-l", language, "tsv"], check=True, capture_output=True, text=True, timeout=180)
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        warnings.append(f"page {page_number}: Tesseract failure {type(error).__name__}")
        return UniversalPage(page_number=page_number, text="", lines=[], words=[])
    words: list[UniversalWord] = []
    for row in csv.DictReader(io.StringIO(completed.stdout), delimiter="\t"):
        text = (row.get("text") or "").strip()
        try:
            confidence = float(row.get("conf", "-1"))
            box = [[float(row["left"]), float(row["top"])], [float(row["left"]) + float(row["width"]), float(row["top"])], [float(row["left"]) + float(row["width"]), float(row["top"]) + float(row["height"])], [float(row["left"]), float(row["top"]) + float(row["height"])]]
        except (KeyError, ValueError): continue
        if not text or confidence < 0: continue
        words.append(UniversalWord(text=text, confidence=round(confidence / 100, 4), bbox=box, page_number=page_number, line_number=int(row.get("line_num") or 0), reading_order=len(words), needs_review=confidence < 70))
    lines: dict[int, list[UniversalWord]] = {}
    for word in words: lines.setdefault(word.line_number, []).append(word)
    output_lines = [{"line_number": number, "text": " ".join(word.text for word in sorted(items, key=lambda item: item.bbox[0][0])), "word_count": len(items)} for number, items in sorted(lines.items())]
    return UniversalPage(page_number=page_number, text="\n".join(line["text"] for line in output_lines), lines=output_lines, words=words)

def _tesseract_executable() -> str | None:
    configured = os.getenv("TESSERACT_CMD")
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (Path("C:/Program Files/Tesseract-OCR/tesseract.exe"), Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe")):
        if candidate.is_file():
            return str(candidate)
    return None
