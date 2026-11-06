import re

def _words(text: str) -> list[str]: return re.findall(r"\S+", text.lower())
def _distance(left: list[str], right: list[str]) -> int:
    row = list(range(len(right) + 1))
    for index, value in enumerate(left, 1):
        current = [index]
        for other, target in enumerate(right, 1):
            current.append(min(current[-1] + 1, row[other] + 1, row[other - 1] + (value != target)))
        row = current
    return row[-1]
def cer(reference: str, hypothesis: str) -> float:
    left, right = list(reference), list(hypothesis)
    return _distance(left, right) / max(1, len(left))
def wer(reference: str, hypothesis: str) -> float:
    left, right = _words(reference), _words(hypothesis)
    return _distance(left, right) / max(1, len(left))
