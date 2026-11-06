from app.layout_extraction import extract_structured, reconstruct_layout

def _line(text, tokens, y):
    adjusted = []
    for token in tokens:
        adjusted.append({**token, "box": [[point[0], point[1] + y] for point in token["box"]]})
    return {"text": text, "confidence": 0.9, "box": [[0,y],[200,y],[200,y+20],[0,y+20]], "tokens": adjusted}

def _token(text, x):
    return {"text": text, "confidence": 0.9, "box": [[x,0],[x+20,0],[x+20,20],[x,20]]}

def test_fragmented_header_allows_table():
    lines = [_line("Item Code", [_token("Item", 0), _token("Code", 40)], 10), _line("Qty Unit", [_token("Qty", 0), _token("Unit", 40)], 35), _line("A100 45 PCS", [_token("A100", 0), _token("45", 50), _token("PCS", 100)], 60), _line("B200 2 BOX", [_token("B200", 0), _token("2", 50), _token("BOX", 100)], 85)]
    result = extract_structured(reconstruct_layout(lines))
    assert len(result.items) == 2

def test_headerless_aligned_rows_are_conservative():
    lines = [_line("A100 45 PCS", [_token("A100", 0), _token("45", 50), _token("PCS", 100)], 10), _line("B200 2 BOX", [_token("B200", 0), _token("2", 50), _token("BOX", 100)], 35)]
    result = extract_structured(reconstruct_layout(lines))
    assert len(result.items) == 2
