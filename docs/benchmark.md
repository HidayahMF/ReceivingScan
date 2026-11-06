# OCR/VLM Benchmark Template

Run from the repository root after approved files are placed in the gitignored `samples/` folder:

```powershell
backend\.venv312\Scripts\python.exe backend\scripts\benchmark_samples.py --samples samples --output docs/benchmark-results.json
```

The runner writes `docs/benchmark-results.json`, which is gitignored because it can contain extracted document contents. It stages copies in a temporary directory, so original samples are not modified. It records SHA-256, byte size, runtime versions, RSS memory before/after, actual timings, engine status, warnings, and JSON output. It does not calculate accuracy without a manually verified ground-truth file.

The workspace contains 8 image samples. Real OCR execution was run from the Python 3.12 environment; the result file is the source of truth for observed output.

M2.5 OCR gate result: **failed runtime inference**. All 8 samples reached the cached PaddleOCR models but `predict()` failed with `NotImplementedError: ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]` from Paddle oneDNN on Windows. A minimal OCR configuration without orientation/unwarping also failed identically; disabling oneDNN environment flags did not resolve it. The result is a runtime compatibility failure, not an OCR accuracy score. Ollama is not installed and `http://localhost:11434/api/tags` is unreachable, so the Vision AI gate is blocked.

All records are marked `PROCESSING_FAILED`; empty text and empty boxes are not treated as successful OCR.

Linux smoke result: the container reached PaddleOCR model inference with Python `3.12.15` on Linux kernel `6.8.0-147-generic`, but failed with the same PIR/oneDNN `NotImplementedError`. The observed process RSS grew from `36.32 MB` to `972.41 MB`; inference duration was `16031.79 ms`. This is a runtime failure, not a zero-text OCR result.

Observed real-run summary from `docs/benchmark-results.json`:

- Samples: 8
- Valid image headers: 8/8
- OCR successes: 0/8
- Processing failures: 8/8
- OCR duration: approximately 13,331.63 to 17,704.48 ms per document
- RSS observed before/after: approximately 267.74 to 864.12 MB
- OCR text and bounding boxes: none produced because inference failed before prediction output
- Confidence values: unavailable because no prediction output was returned
- Ground truth and accuracy: not calculated

Structured extraction quality is not yet reported. The layout extractor and manual ground-truth template are available in `docs/layout-extraction.md`; the current workspace does not contain the Linux quality artifact, so no PT Bakrie field result or eight-document extraction benchmark is claimed here.

The current generated benchmark artifact contains:

```json
{"sample_count": 0, "records": []}
```

This is an observed empty-sample result, not a benchmark score.

| Sample | Field accuracy | Line exactness | PO detection | Hallucinations | Inference time | Peak RAM | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| pending | pending | pending | pending | pending | pending | pending | Samples not available |
