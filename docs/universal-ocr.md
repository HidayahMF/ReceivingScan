# Universal OCR Phase 1

Universal OCR is separate from receiving extraction. It preserves all Tesseract words, including low-confidence words marked `needs_review`, and returns page/line/word geometry. It accepts JPG, JPEG, PNG, WebP, and PDF when PyMuPDF is installed.

API:

```text
POST /api/v1/ocr/scan
```

The response contains `status`, `full_text`, `pages`, `warnings`, and `processing_metadata`. Structured receiving fields never control which OCR words are retained.

Docker build for local OCR smoke infrastructure:

```sh
docker compose -f infra/docker-compose.yml --profile universal-ocr build universal-ocr
```

Accuracy evaluation requires manually transcribed ground truth. Use `backend/app/ocr_metrics.py` for CER/WER; do not interpret Tesseract confidence as accuracy.
