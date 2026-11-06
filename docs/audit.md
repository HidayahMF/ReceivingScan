# M0 Audit

## Confirmed locally

- Workspace is not a Git repository; project files and confidential samples are protected by `.gitignore` rules, but repository-level Git status cannot be verified here.
- Host is Windows 11 Pro, not the target Ubuntu/Debian Portainer host.
- Node `v22.18.0`, npm `10.9.3`, Git `2.50.1`, Python launcher `3.14.6`, and pip `26.1.2` are available.
- Docker CLI/daemon and Docker Compose are not available in this environment.
- No SQL Server, MySQL, Portainer, or Linux host access was verified. Eight local sample images are present.
- Backend API tests pass in the Python 3.12 environment. Native OCR dependencies were not usable on Python 3.14; the local virtualenv and Linux Docker image target Python 3.12.
- Python 3.12.10 is installed side-by-side and `backend/.venv312` was created. The base backend dependency set, including OpenCV/Pillow/PyODBC, PaddlePaddle `3.3.1`, and PaddleOCR `3.3.0`, installed successfully there.
- M2.5 runtime audit: PaddlePaddle `3.3.1` and PaddleOCR `3.3.0` import successfully. Eight valid image samples were found, SHA-256 recorded, and real inference attempted. Ollama CLI is unavailable and localhost port `11434` is unreachable.
- M2.5 execution audit: 8 real samples were validated and staged by copy. All 8 real PaddleOCR calls loaded cached models but failed during inference with the same Paddle oneDNN/PIR `NotImplementedError`; no text or bounding boxes were produced. Ollama remains unavailable. The sample originals were not modified.
- Linux staging audit: Docker CLI/daemon is unavailable on this Windows host; WSL is not enabled. Total physical memory is approximately 12 GB with approximately 1.4 GB free at audit time. A Python 3.12 CPU OCR image, persistent Paddle model volume, and read-only sample smoke-test profile were prepared but not built or executed locally.
- Linux smoke-test attempt reached the container but failed before OCR because PaddleX attempted to create `/.paddlex` under non-root UID `10001`. The staging operator then ran `docker system prune -a`, which removed unused images, networks, and build cache including the temporary OCR image and several unused networks; `docker volume prune` was interrupted before confirmation. Do not run global prune again on this shared host.
- Linux smoke-test retry passed image preprocessing, writable cache, model-cache lookup, and model initialization. Real `predict()` still failed with `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]` using Python `3.12.15`, PaddlePaddle `3.3.1`, PaddleOCR `3.3.0`, and cached PP-OCRv5 models. No text or boxes were produced.
- Mobile compatibility candidate was executed on Linux with Python `3.12.15`, PaddlePaddle `3.3.1`, PaddleOCR `3.3.0`, PP-OCRv5 mobile det/rec, and all optional orientation modules disabled. It downloaded both mobile models but failed with the identical PIR/oneDNN error before output. RSS was `36.5 MB` to `526.55 MB`, duration `16263.09 ms`.
- Runtime defects corrected: uploaded files are now content-verified with Pillow, PaddleOCR polygon output is normalized from NumPy/list forms, and processing failure no longer invokes OCR a second time.
- API workflow tests cover valid upload, manual fallback, operator review, and separate `actual_qty`; the OCR engine is mocked in that test so the suite does not download or initialize a model.
- Backend test result: `12 passed` in the Python 3.12 environment. Frontend production build and Compose safety checks passed. These are component/workflow results, not real document accuracy results.

## Blockers and questions

- Obtain read-only Linux host output for `uname -a`, `lscpu`, `free -h`, `df -h`, `docker version`, `docker compose version`, `docker info`, and optional `nvidia-smi`.
- Obtain approved network endpoints and credentials through a secure channel; do not put them in Git.
- DBA must identify target SQL Server database/schema and approve migrations.
- Legacy MySQL schema/table relationships must be inspected using metadata-only queries before adapter implementation.
- Confirm HTTPS origin, roles, retention, backups, and no-PO policy.
- Linux staging must build and run the real OCR smoke test against the existing gitignored `samples/` before any accuracy claim.

## Safety

No production connection, DDL, data write, firewall change, deployment, or cloud AI call was performed. A real Windows OCR benchmark was performed and recorded as 8/8 runtime failures; no accuracy claim was made.
