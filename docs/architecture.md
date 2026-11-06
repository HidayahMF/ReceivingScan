# Architecture

Nginx serves the React static build and proxies only approved application routes in the eventual secure reverse-proxy setup. FastAPI owns authentication, validation, upload metadata, and SQL Server transactions. Redis/Celery provide asynchronous processing. Original files live on persistent host storage; SQL Server stores metadata and audit records. MySQL is an external, read-only PO source. Ollama is optional, private to the Compose network, and never receives documents through a cloud endpoint.

The OCR baseline is lazy-loaded by `backend/app/ocr.py`: OpenCV creates a processing derivative while preserving the original, and PaddleOCR remains optional until Python/runtime compatibility and host resources are verified. OCR failure returns warnings rather than blocking manual entry.
