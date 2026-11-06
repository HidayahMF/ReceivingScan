# Deployment Checklist

Run on the target Linux host, after review, without changing production databases:

```sh
uname -a
lscpu
free -h
docker compose version
nvidia-smi # optional
docker compose -f infra/docker-compose.yml config
```

Create `.env`/Portainer environment values from `.env.example` using secure storage. Start only the scaffold stack after approval with `docker compose -f infra/docker-compose.yml up -d --build`. Verify `/health` through the internal backend route and the frontend port. Do not enable the `local-vlm` profile until resources, model license, and a local benchmark are approved.

The backend image targets Python 3.12 and installs only `requirements-base.txt`. The Celery worker and `ocr-smoke` profile use `backend/Dockerfile.ocr`, which adds PaddlePaddle/PaddleOCR and persists model cache in the `paddle_models` volume. PaddleOCR and its Paddle runtime are platform-specific; verify the approved Linux CPU package combination before using this image beyond staging.

Linux staging smoke test, after Docker is available and the samples have been copied to the staging host:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-smoke build ocr-smoke
docker compose -f infra/docker-compose.yml --profile ocr-smoke run --rm ocr-smoke
```

The command must return JSON with non-empty `ocr.text` and exit code 0 to count as a real OCR success. Exit code 1 means a runtime/inference failure; exit code 2 means the image was valid but no text was produced. The source sample mount is read-only. The Ollama volume is persistent, but Ollama remains internal-only and model selection is supplied through `OLLAMA_MODEL`.

The OCR image runs as UID `10001`. `HOME`, `TMPDIR`, and PaddleX cache variables are explicitly mapped to writable paths and the `/models` volume. This avoids PaddleX attempting to create `/.paddlex` on a non-writable root.

If the Linux CPU smoke test reproduces a Paddle PIR/oneDNN failure, do not claim OCR success. Capture the full traceback, Python/Paddle/PaddleOCR versions, CPU/RAM, and model cache state. Evaluate an officially supported Linux Paddle runtime combination before changing model versions; do not keep adding Windows environment flags as a workaround.
