import json
from pathlib import Path

from scripts.migrate_legacy_geometry import migrate_box

def test_legacy_rotation_270_formula_recovers_spaces():
    # Legacy coordinates are the old runner's reflected original-space box.
    original, upright = migrate_box([[1500, 1500], [1490, 1500], [1490, 1490], [1500, 1490]])
    assert upright[0] == [1500, 100]
    assert original[0] == [100, 100]
