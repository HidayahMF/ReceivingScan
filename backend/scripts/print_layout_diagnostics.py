import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description="Print existing OCR artifact in upright reading order")
parser.add_argument("artifact", type=Path)
args = parser.parse_args()
print(f"sample={payload.get('file')} rotation={best.get('rotation')} preprocessing={best.get('preprocessing')} psm={best.get('psm')}")
for index, line in enumerate(best.get("lines", []), start=1):
    print(f"L{index:02d} text={line.get('text')!r} box={line.get('upright_box', line.get('box'))} confidence={line.get('confidence')}")
    for token in line.get("tokens", []):
        print(f"  token={token.get('text')!r} box={token.get('upright_box', token.get('box'))} confidence={token.get('confidence')}")
