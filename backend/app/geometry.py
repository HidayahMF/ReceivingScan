def original_to_upright(point: list[float], width: float, height: float, rotation: int) -> list[float]:
    x, y = point
    if rotation == 90:
        return [y, width - x]
    if rotation == 180:
        return [width - x, height - y]
    if rotation == 270:
        return [height - y, x]
    return [x, y]

def upright_to_original(point: list[float], width: float, height: float, rotation: int) -> list[float]:
    x, y = point
    if rotation == 90:
        return [width - y, x]
    if rotation == 180:
        return [width - x, height - y]
    if rotation == 270:
        return [y, height - x]
    return [x, y]

def transform_box(box: list[list[float]], width: float, height: float, rotation: int, direction: str) -> list[list[float]]:
    transform = original_to_upright if direction == "to_upright" else upright_to_original
    return [transform(point, width, height, rotation) for point in box]
