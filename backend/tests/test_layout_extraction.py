from app.layout_extraction import extract_structured, reconstruct_layout

def test_layout_groups_tokens_and_keeps_item_evidence():
    layout = reconstruct_layout([
        {"text": "Item Code Qty Unit", "confidence": 0.9, "box": [[10, 80], [160, 80], [160, 100], [10, 100]]},
        {"text": "A100 45 Pcs", "confidence": 0.9, "box": [[10, 100], [160, 100], [160, 120], [10, 120]], "tokens": [{"text": "A100", "confidence": 0.9, "box": [[10, 100], [50, 100], [50, 120], [10, 120]]}, {"text": "45", "confidence": 0.8, "box": [[60, 100], [80, 100], [80, 120], [60, 120]]}, {"text": "Pcs", "confidence": 0.95, "box": [[90, 100], [120, 100], [120, 120], [90, 120]]}]},
    ])
    result = extract_structured(layout)
    assert len(layout.lines) == 2
    assert result.items[0]["document_qty"] == "45"
    assert result.items[0]["document_unit"] == "PCS"
    assert result.items[0]["status"] == "uncertain"
    assert result.items[0]["evidence"]

def test_missing_fields_are_not_guessed():
    result = extract_structured(reconstruct_layout([]))
    assert result.po_number.value is None
    assert result.po_number.status == "missing"

def test_address_number_is_rejected_without_table_region():
    layout = reconstruct_layout([{"text": "barang Company BOX 17132", "confidence": 0.92, "box": [[10, 100], [200, 100], [200, 120], [10, 120]], "tokens": [{"text": "barang", "confidence": 0.9, "box": [[10,100],[50,100],[50,120],[10,120]]}, {"text": "Company", "confidence": 0.9, "box": [[55,100],[110,100],[110,120],[55,120]]}, {"text": "BOX", "confidence": 0.92, "box": [[115,100],[145,100],[145,120],[115,120]]}, {"text": "17132", "confidence": 0.92, "box": [[150,100],[200,100],[200,120],[150,120]]}]}])
    result = extract_structured(layout)
    assert result.items == []
    assert any("table" in candidate["reason"] for candidate in result.rejected_candidates)

def test_invalid_document_number_is_rejected():
    layout = reconstruct_layout([{"text": "Surat Jalan 4 PT Maret Form-Disp-Rf", "confidence": 0.9, "box": [[10,10],[250,10],[250,30],[10,30]]}])
    result = extract_structured(layout)
    assert result.document_number.value is None
    assert result.document_number.status == "missing"
    assert any(candidate["field"] == "document_number" for candidate in result.rejected_candidates)
