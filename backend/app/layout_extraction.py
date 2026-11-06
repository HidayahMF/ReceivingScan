from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import re
from typing import Any

from .schemas import Evidence, FieldExtraction, LayoutExtraction, StructuredExtraction
from .geometry import transform_box

ALLOWED_UNITS = {"PCS", "PC", "BOX", "KG", "SET", "UNIT", "LOT"}
TABLE_HEADERS = ("item", "kode", "code", "description", "qty", "quantity", "jumlah", "unit")
FOOTER_MARKERS = ("terima", "received", "signature", "tanda tangan", "hormat")

@dataclass(frozen=True)
class OCRToken:
    text: str
    confidence: float
    box: list[list[float]]
    @property
    def left(self): return min(p[0] for p in self.box)
    @property
    def top(self): return min(p[1] for p in self.box)
    @property
    def right(self): return max(p[0] for p in self.box)
    @property
    def bottom(self): return max(p[1] for p in self.box)
    @property
    def center_y(self): return (self.top + self.bottom) / 2

@dataclass
class Candidate:
    field: FieldExtraction
    rejected: list[dict]

def reconstruct_layout(lines: list[dict[str, Any]], y_tolerance: float | None = None, rotation: int = 0, original_size: list[float] | None = None) -> LayoutExtraction:
    width, height = original_size or [0, 0]
    tokens = []
    for line in lines:
        for source in line.get("tokens") or [line]:
            if not source.get("text") or not source.get("box"): continue
            box = transform_box(source["box"], width, height, rotation, "to_upright") if original_size else source["box"]
            tokens.append(OCRToken(str(source["text"]), float(source.get("confidence", line.get("confidence", 0))), box))
    if not tokens: return LayoutExtraction(lines=[], warnings=["Tidak ada OCR line dengan evidence koordinat"])
    median_height = sorted(t.bottom - t.top for t in tokens)[len(tokens) // 2]
    tolerance = y_tolerance or max(6.0, median_height * 0.45)
    rows: list[list[OCRToken]] = []
    for token in sorted(tokens, key=lambda t: (t.center_y, t.left)):
        matches = [row for row in rows if abs(token.center_y - _row_center(row)) <= tolerance]
        if matches:
            min(matches, key=lambda row: abs(token.center_y - _row_center(row))).append(token)
        else:
            rows.append([token])
    output = []
    for number, row in enumerate(sorted(rows, key=_row_center), 1):
        ordered = sorted(row, key=lambda t: t.left)
        output.append({"line_number": number, "text": " ".join(t.text for t in ordered), "confidence": round(sum(t.confidence for t in ordered) / len(ordered), 4), "box": _union([t.box for t in ordered]), "tokens": [{"text": t.text, "confidence": t.confidence, "box": t.box} for t in ordered]})
    return LayoutExtraction(lines=output, warnings=[])

def extract_structured(layout: LayoutExtraction) -> StructuredExtraction:
    document_number = _document_number(layout.lines)
    document_date = _date_field(layout.lines)
    po_number = _po_field(layout.lines)
    partner = _partner_field(layout.lines)
    table_start, table_end, table_reason, table_diagnostics = _table_region(layout.lines)
    rejected = document_number.rejected + document_date.rejected + po_number.rejected + partner.rejected
    if table_start is None:
        rejected.append({"field": "items", "text": None, "reason": f"item table not identified: {table_reason}", "table_diagnostics": table_diagnostics})
        items = []
    else:
        items, item_rejected = _extract_items(layout.lines[table_start:table_end])
        rejected.extend(item_rejected)
    regions = [{"name": "item_table", "start_line": table_start, "end_line": table_end, "status": "identified" if table_start is not None else "missing", "reason": table_reason, "diagnostics": table_diagnostics}]
    return StructuredExtraction(document_number=document_number.field, document_date=document_date.field, po_number=po_number.field, partner_name=partner.field, items=items, rejected_candidates=rejected, regions=regions, warnings=["Field dan item hanya kandidat; verifikasi operator wajib"])

def _document_number(lines):
    rejected = []
    labels = ("surat jalan", "delivery note", "no surat jalan", "nomor surat jalan", "document no")
    for line in lines:
        if any(label in line["text"].lower() for label in labels):
            value = _after(line["text"], labels)
            if value and _plausible_identifier(value): return Candidate(FieldExtraction(value=value, status="uncertain", evidence=[_evidence(line)]), rejected)
            rejected.append({"field": "document_number", "text": value or line["text"], "reason": "explicit document label but identifier is not plausible"})
    return Candidate(FieldExtraction(status="missing"), rejected)

def _date_field(lines):
    rejected = []
    for line in lines:
        if re.search(r"\b(tanggal|date)\b", line["text"], re.I):
            value = _after(line["text"], ("tanggal", "date"))
            if _parse_date(value): return Candidate(FieldExtraction(value=value, status="uncertain", evidence=[_evidence(line)]), rejected)
            rejected.append({"field": "document_date", "text": value or line["text"], "reason": "does not parse as date"})
    return Candidate(FieldExtraction(status="missing"), rejected)

def _po_field(lines):
    rejected = []
    for line in lines:
        if re.search(r"\b(P\.O\.?|PO|purchase order)\b", line["text"], re.I):
            value = _after(line["text"], ("P.O.", "P.O", "PO", "purchase order"))
            if value and _plausible_identifier(value): return Candidate(FieldExtraction(value=value, status="uncertain", evidence=[_evidence(line)]), rejected)
            rejected.append({"field": "po_number", "text": value or line["text"], "reason": "explicit PO label without plausible identifier"})
    return Candidate(FieldExtraction(status="missing"), rejected)

def _partner_field(lines):
    for line in lines:
        if re.search(r"\b(supplier|vendor|dari|from|kepada|to)\b", line["text"], re.I):
            value = _after(line["text"], ("supplier", "vendor", "dari", "from", "kepada", "to"))
            if value and len(value) >= 3: return Candidate(FieldExtraction(value=value, status="uncertain", evidence=[_evidence(line)]), [])
    return Candidate(FieldExtraction(status="missing"), [])

def _table_region(lines):
    diagnostics = []
    header_scores = []
    for index, line in enumerate(lines):
        score = sum(marker in line["text"].lower() for marker in TABLE_HEADERS)
        if score: header_scores.append((index, score))
    for index, score in header_scores:
        diagnostics.append({"type": "header_signal", "start_line": index, "score": score, "text": lines[index]["text"]})
    # Support fragmented headers over adjacent OCR lines.
    for index in range(len(lines) - 1):
        combined = f"{lines[index]['text']} {lines[index + 1]['text']}".lower()
        score = sum(marker in combined for marker in TABLE_HEADERS)
        if score >= 2:
            return _region_from_header(lines, index + 1, "fragmented header markers", diagnostics, score)
    if header_scores:
        best_index, best_score = max(header_scores, key=lambda value: value[1])
        if best_score >= 2:
            return _region_from_header(lines, best_index + 1, "header markers identified", diagnostics, best_score)
    # Headerless fallback requires repeated rows with code, quantity, and unit signals.
    candidates = []
    for index, line in enumerate(lines):
        if _row_signal(line): candidates.append(index)
    diagnostics.append({"type": "headerless_row_signals", "lines": candidates})
    if len(candidates) >= 2 and _aligned_rows(lines, candidates):
        return candidates[0], min(len(lines), candidates[-1] + 1), "headerless repeated aligned rows", diagnostics
    return None, None, "no sufficiently independent table signals", diagnostics

def _region_from_header(lines, start, reason, diagnostics, score):
    body = [index for index in range(start, len(lines)) if _row_signal(lines[index])]
    end = next((index for index in range(start, len(lines)) if any(marker in lines[index]["text"].lower() for marker in FOOTER_MARKERS)), len(lines))
    diagnostics.append({"type": "accepted_header_region", "header_line": start - 1, "header_score": score, "body_lines": body, "end_line": end})
    if body: return start, end, reason, diagnostics
    return None, None, "header found but no plausible body rows", diagnostics

def _row_signal(line):
    tokens = line.get("tokens", [])
    has_unit = any(token["text"].upper() in ALLOWED_UNITS for token in tokens)
    has_quantity = any(re.fullmatch(r"\d+(?:[.,]\d+)?", token["text"]) for token in tokens)
    has_code = any(_plausible_code(token["text"]) for token in tokens)
    return has_unit and has_quantity and has_code

def _aligned_rows(lines, indices):
    if len(indices) < 2: return False
    anchors = []
    for index in indices:
        tokens = lines[index].get("tokens", [])
        numeric = next((token for token in tokens if re.fullmatch(r"\d+(?:[.,]\d+)?", token["text"])), None)
        unit = next((token for token in tokens if token["text"].upper() in ALLOWED_UNITS), None)
        if not numeric or not unit: return False
        anchors.append((numeric["box"][0][0], unit["box"][0][0]))
    return max(value[0] for value in anchors) - min(value[0] for value in anchors) < 80 and max(value[1] for value in anchors) - min(value[1] for value in anchors) < 80

def _extract_items(lines):
    items, rejected = [], []
    for line in lines:
        tokens = line.get("tokens", [])
        quantity = next((t for t in tokens if re.fullmatch(r"\d+(?:[.,]\d+)?", t["text"])), None)
        unit = next((t for t in tokens if t["text"].upper() in ALLOWED_UNITS), None)
        code = next((t for t in tokens if _plausible_code(t["text"])), None)
        if not quantity or not unit or not code:
            if quantity or unit or code: rejected.append({"field": "items", "text": line["text"], "reason": "row lacks item code, numeric quantity, or allowed unit"})
            continue
        try: value = Decimal(quantity["text"].replace(",", "."))
        except InvalidOperation: continue
        if code["text"].upper() in ALLOWED_UNITS:
            rejected.append({"field": "items", "text": line["text"], "reason": "item code is an allowed unit"}); continue
        items.append({"line_number": len(items) + 1, "item_code": code["text"], "description": " ".join(t["text"] for t in tokens if t not in (quantity, unit, code)) or None, "document_qty": str(value), "document_unit": unit["text"].upper(), "status": "uncertain", "evidence": [_evidence(line)]})
    return items, rejected

def _plausible_identifier(value): return bool(re.fullmatch(r"(?=.*[A-Z0-9])[A-Z0-9][A-Z0-9./_-]{2,}", value.strip(), re.I)) and len(value.strip()) <= 40
def _plausible_code(value): return bool(re.fullmatch(r"[A-Z0-9]{2,}[./_-]?[A-Z0-9-]*", value, re.I)) and value.upper() not in ALLOWED_UNITS
def _parse_date(value):
    if not value: return None
    match = re.search(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b", value)
    if not match: return None
    day, month, year = map(int, match.groups()); year += 2000 if year < 100 else 0
    try: return date(year, month, day)
    except ValueError: return None
def _after(text, labels):
    match = re.search(r"(?:" + "|".join(re.escape(x) for x in labels) + r")\s*[:#-]?\s*(.*)$", text, re.I)
    return match.group(1).strip(" :-") if match and match.group(1).strip(" :-") else None
def _row_center(row): return sum(t.center_y for t in row) / len(row)
def _union(boxes):
    points = [p for box in boxes for p in box]; l, t = min(p[0] for p in points), min(p[1] for p in points); r, b = max(p[0] for p in points), max(p[1] for p in points); return [[l,t],[r,t],[r,b],[l,b]]
def _evidence(line): return Evidence(text=line["text"], box=line["box"], confidence=line["confidence"], source="tesseract_tsv")
