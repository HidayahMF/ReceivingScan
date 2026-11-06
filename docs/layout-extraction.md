# Layout Reconstruction and Structured Extraction

`backend/scripts/reconstruct_layout.py` consumes an existing Tesseract quality artifact. It does not rerun the 64 quality combinations. It groups upright TSV evidence by vertical proximity, orders tokens left-to-right, preserves both original and upright evidence boxes, and extracts only conservative candidates. New quality artifacts include `box_coordinate_system: original_and_upright` and `upright_box`; the runner avoids transforming those boxes twice.

For Linux hosts without the backend Python environment, use the isolated `layout-reconstruction` Compose profile. It performs an import/dependency check inside the container before reading the artifact.

Field status:

- `missing`: no matching OCR evidence.
- `uncertain`: a spatial/text candidate exists, but OCR confidence is not proof of correctness.
- `verified`: reserved for a later operator/manual or trusted source confirmation. The extractor never emits `verified` by itself.

Run after copying the existing quality artifact from Linux:

```sh
python3 backend/scripts/reconstruct_layout.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json \
  --output docs/PT-Bakrie-Autoparts.structured-extraction.json
```

Container command, with the artifact already copied into `docs/`:

```sh
docker compose -f infra/docker-compose.yml --profile layout build layout-reconstruction
docker compose -f infra/docker-compose.yml --profile layout run --name bmc-layout-reconstruction layout-reconstruction
docker cp bmc-layout-reconstruction:/output/PT-Bakrie-Autoparts.structured-extraction.json ./docs/
docker rm bmc-layout-reconstruction
```

The command is intentionally not run until `docs/PT-Bakrie-Autoparts.tesseract-quality.json` exists. If that file is absent, the runner exits before extraction; it does not rerun OCR or create synthetic input.

Print the actual artifact evidence without rerunning OCR:

```sh
python3 backend/scripts/print_layout_diagnostics.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json
```

The output is the required source for investigating fragmented/headerless tables: each line and token is shown in upright reading order with its box and confidence.

Audit the actual PIL/legacy transform with image corner points:

```sh
python3 backend/scripts/geometry_audit.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json
```

The audit prints original corners, rotated/upright corners, inverse round trips, and the legacy rotation-270 mapping. It does not infer row membership.

Validate an existing artifact before spatial joins:

```sh
python3 backend/scripts/geometry_diagnose.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json
```

Render diagnostic overlays without rerunning OCR:

```sh
python3 backend/scripts/geometry_overlay.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json \
  samples/PT\ Bakrie\ Autoparts.jpg \
  docs/geometry-debug
```

If the report says `insufficient_for_reliable_spatial_join`, do not combine BT.1005 with 45 Pcs. Regenerate only the selected quality candidate with the corrected `upright_box` metadata; do not rerun the full 64-combination matrix unless explicitly required.

Legacy artifact handling:

```sh
python3 backend/scripts/legacy_geometry_report.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json \
  --output docs/PT-Bakrie-Autoparts.legacy-geometry.json
```

The legacy report is intentionally `unsafe_to_migrate`. It does not convert boxes or perform item joins when coordinate semantics cannot be proven.

Targeted recovery (no 64-combination rerun) uses direct TSV coordinates from the upright image:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-targeted build ocr-tesseract-targeted
docker compose -f infra/docker-compose.yml --profile ocr-targeted run --rm ocr-tesseract-targeted
```

The output contains `upright_box` directly from Tesseract, `original_box` from the tested inverse PIL rotation, TSV page/block/paragraph/line/word IDs, physical rows, table diagnostics, and conservative structured output. It does not overwrite the legacy artifact.

For the specific legacy artifact described in the runtime audit (`original_size=[1200,1600]`, `rotation=270`, 105 word-level entries), the old runner implementation is now understood and can be migrated without OCR rerun:

```sh
python3 backend/scripts/migrate_legacy_geometry.py \
  docs/PT-Bakrie-Autoparts.tesseract-quality.json \
  --output docs/PT-Bakrie-Autoparts.tesseract-quality.migrated.json
```

The migration preserves the legacy artifact, marks the source as verified from runner code, and creates one token per legacy word. It must still be visually checked before joining item rows.

The artifact mount is read-only at `/input`. Output is written by UID `10001` to the named `layout_results` volume, so no host checkout permission change or system Python installation is required.

Create a blank manual ground-truth template for the eight samples:

```sh
python3 backend/scripts/create_ground_truth_template.py
```

The template intentionally contains null fields. Do not fill it from OCR automatically. Accuracy evaluation is blocked until an operator verifies the original images.

After a human has filled every approved field and changed the template status to `manually_verified`, evaluate:

```sh
python3 backend/scripts/evaluate_extraction.py \
  docs/ground-truth.json docs
```

The evaluator refuses to calculate results while the template is not manually verified.
