# BMC Receiving AI

Fondasi aplikasi receiving internal dengan React/TypeScript/Tailwind, FastAPI, Redis/Celery, PaddleOCR/OpenCV, dan koneksi ke database existing.

## Status

M0 audit dan M1 scaffold sedang dibangun. Belum ada deployment production, migrasi SQL Server, koneksi database nyata, atau benchmark OCR. `PROJECT_SPEC.md` adalah sumber kebenaran.

## Pengembangan lokal

1. Salin `.env.example` menjadi `.env` dan isi hanya konfigurasi non-production yang memang tersedia.
2. Frontend: `cd frontend`, `npm install`, `npm run dev`.
3. Backend Windows: `py -3.12 -m venv backend/.venv312`, lalu `backend\.venv312\Scripts\python.exe -m pip install -r backend\requirements.txt` dan `backend\.venv312\Scripts\python.exe -m uvicorn app.main:app --reload --app-dir backend`.
4. Jalankan test backend: `backend\.venv312\Scripts\python.exe -m pytest backend\tests -q`.

Tanpa database, backend memakai adapter mock. Koneksi nyata tidak pernah diuji atau diaktifkan tanpa konfigurasi eksplisit.

## M2.5 real-AI validation

Tempatkan hanya dokumen yang telah disetujui di `samples/` (folder di-ignore Git), lalu jalankan benchmark dengan Python 3.12. Hasil harus memiliki ground truth manual terpisah sebelum metrik akurasi dihitung. Import package tidak dianggap sebagai inference nyata. Ollama harus berjalan lokal dan model vision harus dikonfigurasi melalui `OLLAMA_MODEL`; jangan mengisi nama model tanpa verifikasi `/api/tags` dan dukungan image.

Status real validation saat ini: OCR runtime blocked. `paddlepaddle==3.3.1` dan `paddleocr==3.3.0` berhasil di-import pada Python 3.12 dan sudah dicoba pada 8 dokumen nyata, tetapi semua gagal saat model `predict()` dengan error PIR/oneDNN Windows. Ollama tidak tersedia pada mesin development. `backend/app/workers/tasks.py` adalah boundary awal Celery; migrasi penuh dari in-memory jobs menunggu schema SQL Server yang disetujui.

Linux OCR staging image tersedia melalui `backend/Dockerfile.ocr` dan profile `ocr-smoke`. Image tersebut memisahkan dependency OCR dari API dasar dan menyimpan cache model pada volume `paddle_models`. Build dan smoke test belum dijalankan karena Docker daemon tidak tersedia pada development host.

## Portainer/Linux

Gunakan `infra/docker-compose.yml` sebagai Stack. Sediakan environment melalui Portainer secrets/environment settings. Compose ini tidak membuat container SQL Server atau MySQL; keduanya harus berupa service existing yang dapat dijangkau dari network host. Jangan expose Redis atau Ollama ke host.

Perintah verifikasi read-only dan checklist ada di `docs/deployment.md` dan `docs/audit.md`.
