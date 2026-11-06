import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time
import sys
import platform

import psutil

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings
from app.processing import process_document

parser = argparse.ArgumentParser(description="Benchmark only approved local samples; no uploads")
parser.add_argument("--samples", type=Path, default=Path("samples"))
parser.add_argument("--output", type=Path, default=Path("docs/benchmark-results.json"))
args = parser.parse_args()

files = sorted(path for path in args.samples.iterdir() if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}) if args.samples.is_dir() else []
records = []
process = psutil.Process()
runtime = {"python": platform.python_version(), "platform": platform.platform()}
try:
    import paddle
    import paddleocr
    runtime.update({"paddle": paddle.__version__, "paddleocr": getattr(paddleocr, "__version__", "unknown")})
except ImportError as error:
    runtime["import_error"] = f"{type(error).__name__}: {error}"
with tempfile.TemporaryDirectory(prefix="receiving-benchmark-") as staging:
    staging_path = Path(staging)
    for path in files:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        staged = staging_path / path.name
        shutil.copy2(path, staged)
        started = time.perf_counter()
        memory_before_mb = round(process.memory_info().rss / 1024 / 1024, 2)
        try:
            result = process_document(staged, Settings(storage_path=str(staging_path / "storage"), enable_local_vlm=False))
            memory_after_mb = round(process.memory_info().rss / 1024 / 1024, 2)
            records.append({"file": path.name, "sha256": digest, "bytes": path.stat().st_size, "memory_before_mb": memory_before_mb, "memory_after_mb": memory_after_mb, "total_duration_ms": round((time.perf_counter() - started) * 1000, 2), "ocr": result.ocr.model_dump(mode="json"), "vision": result.vision.model_dump(mode="json"), "extraction": result.extraction.model_dump(mode="json"), "status": result.status})
        except Exception as error:
            memory_after_mb = round(process.memory_info().rss / 1024 / 1024, 2)
            records.append({"file": path.name, "sha256": digest, "bytes": path.stat().st_size, "memory_before_mb": memory_before_mb, "memory_after_mb": memory_after_mb, "total_duration_ms": round((time.perf_counter() - started) * 1000, 2), "status": "BENCHMARK_ERROR", "error": f"{type(error).__name__}: {error}"})

args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps({"sample_count": len(records), "runtime": runtime, "records": records}, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"sample_count": len(records), "output": str(args.output)}, ensure_ascii=False))
