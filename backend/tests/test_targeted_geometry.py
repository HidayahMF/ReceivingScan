from pathlib import Path
from app.geometry import original_to_upright, upright_to_original

def test_targeted_rotation_inverse_corners():
    for point in ([0, 0], [1200, 0], [0, 1600], [1200, 1600]):
        assert upright_to_original(original_to_upright(list(point), 1200, 1600, 270), 1200, 1600, 270) == list(point)
