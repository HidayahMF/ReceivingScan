import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser(description="Run each OCR candidate once and persist outcomes")
parser.add_argument("--image", type=Path, default=Path("samples/PT Bakrie Autoparts.jpg"))
parser.add_argument("--state", type=Path, default=Path("docs/ocr-compatibility-state.json"))
args = parser.parse_args()
fingerprints = {
    "paddle-server-3.3.1-3.3.0": "paddle:3.3.1|ocr:3.3.0|models:server|orientation:on",
    "paddle-mobile-3.3.1-3.3.0": "paddle:3.3.1|ocr:3.3.0|models:mobile|orientation:off",
    "paddle-legacy-2.6.2-2.7.3": "paddle:2.6.2|ocr:2.7.3|models:ppocrv3|mkldnn:off",
    "tesseract-local": "tesseract:system|tsv:1|psm:6|lang:eng",
}
state = json.loads(args.state.read_text()) if args.state.exists() else {"samples": {}}
sample_key = hashlib.sha256(args.image.read_bytes()).hexdigest()
sample_state = state.setdefault("samples", {}).setdefault(sample_key, {})
commands = {
    "paddle-server-3.3.1-3.3.0": ["docker", "compose", "-f", "infra/docker-compose.yml", "--profile", "ocr-smoke", "run", "--rm", "ocr-smoke"],
    "paddle-mobile-3.3.1-3.3.0": ["docker", "compose", "-f", "infra/docker-compose.yml", "--profile", "ocr-compat", "run", "--rm", "ocr-compat-mobile"],
    "paddle-legacy-2.6.2-2.7.3": ["docker", "compose", "-f", "infra/docker-compose.yml", "--profile", "ocr-compat-legacy", "run", "--rm", "ocr-compat-legacy"],
    "tesseract-local": ["docker", "compose", "-f", "infra/docker-compose.yml", "--profile", "ocr-tesseract", "run", "--rm", "ocr-tesseract"],
}
for name, fingerprint in fingerprints.items():
    if sample_state.get(name, {}).get("fingerprint") == fingerprint:
        print(f"SKIP {name}: recorded fingerprint already tested")
        continue
    started = time.perf_counter()
    completed = subprocess.run(commands[name], capture_output=True, text=True)
    sample_state[name] = {"fingerprint": fingerprint, "status": "SUCCESS" if completed.returncode == 0 else "FAILED", "exit_code": completed.returncode, "duration_ms": round((time.perf_counter() - started) * 1000, 2), "output": completed.stdout[-10000:], "error": completed.stderr[-10000:]}
    args.state.parent.mkdir(parents=True, exist_ok=True)
    args.state.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{name}: {sample_state[name]['status']} exit={completed.returncode}")
    if completed.returncode == 0:
        print("Baseline OCR found; stopping matrix.")
        break
