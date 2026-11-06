# BMC Receiving AI — Project Specification

Version: 1.0 | Status: Implementation blueprint | Language: Indonesian for operator UI

## 1. Purpose and scope
Build an internal, self-hosted web application to assist BMC goods receiving. Operators use a phone browser to photograph delivery notes (surat jalan). Local OCR and vision-language processing attempt to extract structured fields; deterministic validation looks up legacy purchase orders in an existing MySQL database; humans review physical quantities and document fields; finalized receiving records and audit trails are stored in the company's **existing Microsoft SQL Server**.

This is an **AI-assisted** workflow, not automatic acceptance of goods. It must remain usable when OCR or local AI fails. The goal is zero cloud AI API keys and zero per-document cloud AI charges, not zero total operating cost. Do not transmit documents or extracted contents to cloud AI, telemetry, or external endpoints.

## 2. Non-negotiable decisions
- Deployment: Docker Compose stack through **existing Portainer on Ubuntu/Debian Linux**.
- Primary application database: **existing company SQL Server**, not a new SQL Server container.
- Legacy PO source: **existing MySQL**, accessed initially **read-only**. Do not modify schema, records, permissions, or stored procedures.
- Frontend: React + TypeScript + Tailwind CSS, built into static assets served by Nginx.
- Backend: Python + FastAPI + Pydantic + SQLAlchemy; Microsoft ODBC Driver for SQL Server / pyodbc as appropriate.
- Image processing: OpenCV/Pillow. OCR baseline: PaddleOCR running locally.
- Optional local vision-language model: self-hosted inference (Ollama plus a compatible vision model, e.g. a suitable Qwen-VL variant), chosen **only after** inspecting CPU/RAM/GPU and testing on sample documents.
- Background processing: Redis + Celery worker, or an equivalently reliable queue if justified.
- Proxy: Nginx or existing secure company reverse proxy; HTTPS for phone camera browser features.
- File storage: persistent bind mount/volume on the Linux host; SQL Server stores metadata/path, not image BLOBs.
- No React Native, Android APK, cloud vision service, cloud AI key, or model training in MVP.
- Never hardcode passwords, connection strings, API keys, production IPs, or sample personal data.

## 3. Reference documents
User-supplied Google Drive folder (reference samples only):
https://drive.google.com/drive/folders/1StnO7-HjIWaumMCWlQNcYUd37KZc7cXi?hl=ID

Eight sample images include Shinko Kogyo Indonesia, Bina Usaha Mandiri Misuzawa, Bakrie Autoparts, Spring San Cahaya, and other photo variants. Formats differ: printed tables, rotated photos, multi-unit quantities (PCS/BOX/KG), stamps, faint handwriting, and ambiguous PO labels. **Do not claim tested OCR accuracy before actually benchmarking.** If the agent cannot access Drive, request that samples be copied to a local, gitignored `samples/` folder; never pretend to have analyzed bytes it cannot access.

## 4. Functional end-to-end flow
1. Operator authenticates and starts a new receiving draft.
2. Browser captures/uploads one or more document images; preview, retake, and manual entry are supported.
3. Backend stores original immutable image, creates a processing job, returns job ID promptly.
4. Worker validates file type/size, normalizes orientation, optionally crops/enhances image, preserves original.
5. PaddleOCR extracts text and bounding boxes; optional local VLM interprets layout and handwriting, with OCR text as supplementary evidence.
6. Normalize into a typed schema. Unknown values must be `null`; never hallucinate missing PO or product IDs. Record source evidence, extraction method, and `needs_review`; avoid presenting invented calibrated confidence percentages.
7. Deterministic validation checks required fields, quantities, units, duplicates, and supplier/product mapping.
8. Backend looks up PO in MySQL using a read-only connector. Verify PO number, supplier, item code, unit, ordered amount, and any available historical receipts. Treat cross-database receiving totals carefully; do not assume MySQL reflects new SQL Server receipts.
9. Operator reviews original image alongside editable extracted fields and line items; enters **physically counted quantity** separately from **document quantity**.
10. On verify/finalize, revalidate on server, enforce duplicate/idempotency and quantity policies, and persist a consistent receiving transaction and audit trail in SQL Server.
11. Dashboard and reports query SQL Server; PO reference can be refreshed from MySQL as needed.

## 5. Status models
Document: `DRAFT`, `PROCESSING`, `AI_COMPLETED`, `NEEDS_REVIEW`, `VERIFIED`, `RECEIVED`, `REJECTED`, `CANCELLED`, `PROCESSING_FAILED`.
PO match: `NOT_APPLICABLE`, `NO_PO`, `FOUND`, `NOT_FOUND`, `REVIEW`.
Ownership: `PO`, `CUSTOMER_OWNED`, `UNKNOWN`.

**Important:** Missing PO on a document does **not** automatically prove customer ownership. Require explicit operator confirmation and an allowed business reason for no-PO/customer-owned workflows. Ambiguous PO must be `REVIEW`.

## 6. Data extraction contract
Header: delivery note number/date, PO number, partner/supplier/customer, address if present, vehicle plate, driver, optional remarks.
Lines: line number, supplier item code, internal item code if mapped, description, document quantity, document unit, packaging quantity/unit, weight/unit if shown, notes.
Audit metadata: original file path, processed file path, raw OCR text, VLM JSON, model name/version, inference duration, warnings, field-level evidence, operator corrections, timestamps.

Use Pydantic schemas; dates in ISO format; decimal quantities (not floats for accounting); normalized units with original raw units retained. Explicitly distinguish quantities in PCS, BOX, and KG; do not combine different units.

Example response shape (illustrative only):
```json
{
  "document_number": null,
  "document_date": null,
  "po_number": null,
  "partner_name": null,
  "vehicle_number": null,
  "driver_name": null,
  "items": [{"line_number": 1, "item_code": null, "description": null, "document_qty": null, "unit": null, "pack_qty": null, "pack_unit": null, "weight": null, "weight_unit": null, "needs_review": true}],
  "warnings": ["Requires operator verification"]
}
```

## 7. SQL Server design (proposed, subject to DBA approval)
Create a dedicated schema such as `receiving_ai` within an approved database. **Do not execute DDL on production without authorization.** Design migrations for:
- `users`, `roles` (or integration with existing identity if required)
- `partners`, `products` (local mappings/cache as needed)
- `receiving_documents`, `receiving_items`
- `document_files`, `extraction_runs`, `field_corrections`
- `po_lookup_snapshots`, `audit_events`, `processing_jobs`
- optional `unit_mappings`, `supplier_item_mappings`

Keep PO source ID and number, source-system identifier, and snapshot of PO comparison. Include optimistic concurrency/version and unique idempotency keys to prevent double receiving. Use transactions and appropriate locking. Never overwrite AI raw output when an operator edits values.

## 8. MySQL integration
- First inspect actual legacy PO table names, column types, relationships, units, and status logic using metadata-only/read-only queries.
- Build an adapter/repository that maps legacy schema into an internal PO domain model.
- Use parameterized queries, least-privilege credentials, timeouts, retries with bounds, and secure network access.
- Define how cumulative receipts are computed across legacy MySQL and new SQL Server; warn if totals are incomplete.
- Do not migrate or alter legacy PO data unless separately authorized.
- If MySQL unavailable, allow drafts/manual review but do not falsely mark PO as validated.

## 9. Local AI architecture
- Start with OCR-only baseline. Evaluate whether a local VLM materially improves handwriting and table extraction.
- The local model endpoint must be private inside Docker network; do not expose Ollama publicly.
- Choose model based on measured RAM/VRAM, throughput, and document accuracy; avoid fixed model-size promises.
- Model downloads may require internet **during provisioning**; production inference must remain local.
- Pin model and container versions; verify model license and commercial-use terms.
- AI results are untrusted suggestions. Deterministic validation and operator approval are mandatory.
- On timeout, out-of-memory, or malformed JSON, mark processing failure/review and allow manual entry.
- Benchmark field accuracy, line-item accuracy, PO detection, hallucinations, latency, and memory use on the eight real samples. Maintain manually verified ground truth, do not invent benchmark scores.

## 10. UI screens
- Login, dashboard, receiving list/detail, new receiving/camera capture, photo preview, processing progress, side-by-side review, PO comparison, final confirmation, master-data mappings, audit history, reports/export, admin settings.
- Mobile-first camera workflow; accessible validation indicators; responsive desktop review table.
- Separate document quantity from actual counted quantity.
- Role-based access: ADMIN, OPERATOR, SUPERVISOR. Final approval rules configurable and explicit.

## 11. Security and operations
- TLS/HTTPS, LAN/VPN-only access, CORS allowlist, authenticated routes, role authorization, CSRF/session protections as applicable, rate limits, safe file upload checks, file size/type limits, malware scanning if available.
- Secrets injected via secure deployment settings; no credentials in Git or logs.
- Secure file access; no public document URLs; access logs, operator audit trails, backup/restore tests, retention policy.
- Persistent storage and backup for images, SQL Server, and worker job metadata.
- Health checks, resource limits, restart policies, structured logs, graceful shutdown, job retries/idempotency.
- SQL Server ODBC connectivity and TLS certificate validation must be configured securely; do not disable certificate verification as a default workaround.
- Avoid sending confidential documents to external observability or AI services.

## 12. Suggested repository layout
```text
receiving-ai/
  frontend/              # React + TS + Tailwind
  backend/
    app/api/
    app/core/
    app/models/
    app/schemas/
    app/repositories/
    app/services/
    app/workers/
    migrations/
    tests/
  infra/
    docker-compose.yml
    nginx/
    env.example
  docs/
    architecture.md
    data-mapping.md
    deployment.md
    test-plan.md
  samples/               # gitignored confidential test images
  README.md
  PROJECT_SPEC.md
  AGENTS.md
```

## 13. Milestones and gates
**M0 Audit:** repo, Docker/Portainer environment, host resources, network, SQL Server connectivity, MySQL read-only metadata, HTTPS, storage. Produce report; do not mutate production.
**M1 Scaffold:** frontend/backend, lint/tests, Dockerfiles, compose, `.env.example`, health endpoints, mock database adapters. Verify build and startup.
**M2 AI PoC:** real sample benchmark with OCR baseline and optional VLM; measure performance; decide model and fallback.
**M3 Data integration:** SQL Server migrations after explicit approval; MySQL PO read-only adapter and unit mappings; integration tests.
**M4 Receiving workflow:** capture/upload, async jobs, review/edit, actual counts, PO validation, save draft/finalize, audit.
**M5 Operations:** RBAC, dashboard, reports, TLS, monitoring, backup, security tests, staged rollout.

Each milestone must document commands, changed files, tests, expected results, known risks, and next step. Never claim successful deployment or OCR accuracy without observed results.

## 14. Acceptance criteria
- Stack builds and starts via Portainer without deploying a new SQL Server.
- Existing MySQL PO data is read-only; existing SQL Server is used for application data.
- No cloud AI API keys, cloud inference calls, or external document uploads.
- All eight reference samples can be uploaded; extraction failures do not block manual entry.
- Operator can review/correct fields and separately enter actual received quantities.
- PO match checks code/unit/remaining quantity, with explicit warning/exception policy.
- Unknown fields remain null; source image and audit trail are retained.
- No double-finalization; consistent SQL Server transactions.
- HTTPS browser camera flow is tested on actual phones.
- Backup/restore, security, and error-path tests are documented.

## 15. Open questions to discover, not assume
- Linux host CPU/RAM/GPU/disk, resource contention, Portainer stack deployment workflow.
- SQL Server version/edition, target database/schema, service account and migration permissions.
- MySQL PO table schema, data quality, whether receipts are tracked there, network connectivity.
- Actual operator roles, approval rules, no-PO/customer-owned policy, unit conversions.
- Concurrency, daily document volume, retention, backup target, and required SLA.
- Whether commercial-use licenses for chosen models/components meet company policy.

Proceed with reasonable local scaffolding defaults, but stop before production DB changes, credential creation, firewall exposure, or rollout until authorized.
