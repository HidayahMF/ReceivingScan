# Test Plan

- M1: frontend TypeScript/build and backend health/schema tests.
- M2: eight manually labelled samples; measure field accuracy, line exactness, hallucination rate, latency, and peak RAM. No scores before execution.
- M2.5: verify PaddlePaddle runtime plus PaddleOCR inference on approved samples, verify Ollama model metadata and image inference, validate output JSON, and record failures separately from manual fallback. Unit tests must not be counted as real-AI validation.
- Universal OCR Phase 1: evaluate full text independently of document type using CER/WER, coverage, reading order, bounding-box alignment, duration, and memory against manually transcribed ground truth. Structured receiving extraction is not part of this gate.
- M3: read-only MySQL integration tests against a controlled account; SQL Server migration review before any apply.
- M4: upload failure, retry/idempotency, review correction, physical quantity, duplicate finalization, and audit tests.
- M5: HTTPS phone camera, RBAC, backup/restore, authorization, rate limit, and security tests.

Async readiness: `backend/app/workers/tasks.py` now provides the Celery processing boundary. It must not be treated as production-ready until job status, idempotency, retries, and result metadata are persisted in approved SQL Server tables.

Migration plan:

1. Create an approved SQL Server `processing_jobs` record before enqueueing, with an idempotency key and immutable original path.
2. Enqueue `process_document_task` through Redis/Celery and return `202 Accepted` plus job ID from the upload endpoint.
3. Worker claims the job with a lease/version check, writes OCR/VLM artifacts, and transitions status transactionally.
4. Frontend polls the job endpoint or uses an authenticated event channel; it must render `PROCESSING_FAILED` with manual entry.
5. Add retry limits, dead-letter handling, duplicate-finalization tests, and recovery tests before replacing the current synchronous development path.
