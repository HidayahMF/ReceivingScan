from app.geometry import original_to_upright, upright_to_original

def test_rotation_round_trip():
    for rotation in (0, 90, 180, 270):
        point = [30, 40]
        assert upright_to_original(original_to_upright(point, 200, 100, rotation), 200, 100, rotation) == point
