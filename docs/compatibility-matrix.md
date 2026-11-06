# OCR Compatibility Matrix

This matrix is for isolated staging experiments. It does not replace the existing `ocr-smoke` image and does not touch databases or production containers.

| Candidate | Runtime | Models | Config | Status |
|---|---|---|---|---|
| Existing baseline | Python 3.12.15 / PaddlePaddle 3.3.1 / PaddleOCR 3.3.0 | PP-OCRv5 server det/rec | Orientation and unwarping enabled | FAILED on Linux PIR/oneDNN before output |
| Mobile candidate 1 | Python 3.12 / PaddlePaddle 3.3.1 / PaddleOCR 3.3.0 | PP-OCRv5 mobile det/rec | Orientation, unwarping, and textline orientation disabled | NOT RUN: image prepared, Docker execution must be run on Linux staging |
| Older compatible pair | Python 3.10 / PaddlePaddle 2.6.2 / PaddleOCR 2.7.3 | PP-OCRv3 mobile defaults via legacy API | `use_angle_cls=False`, `use_mkldnn=False`, CPU | NOT RUN: isolated image prepared, Docker execution pending |
| Local fallback | TBD | Tesseract/RapidOCR | TBD | NOT RUN; runtime/license/resource review required |
| Tesseract local | System Tesseract + TSV | `tesseract-ocr-eng`, PSM 6 | Local binary, no Paddle dependency | NOT RUN: isolated image prepared |

## Operator command

Run from the Linux staging repository:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-compat build ocr-compat-mobile
docker compose -f infra/docker-compose.yml --profile ocr-compat run --rm ocr-compat-mobile
echo "exit_code=${PIPESTATUS[0]}"
```

Exit codes: `0` means non-empty OCR text, `1` runtime failure, `2` valid image with no text. The candidate uses a separate `paddle_models_compat` volume and a read-only sample mount. Do not remove the existing `infra_paddle_models` volume.

Legacy candidate command:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-compat-legacy build ocr-compat-legacy
docker compose -f infra/docker-compose.yml --profile ocr-compat-legacy run --rm ocr-compat-legacy
echo "exit_code=${PIPESTATUS[0]}"
```

It uses a separate `paddle_models_legacy` volume and does not replace the baseline or mobile candidate.

Tesseract candidate:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-tesseract build ocr-tesseract
docker compose -f infra/docker-compose.yml --profile ocr-tesseract run --rm ocr-tesseract
echo "exit_code=${PIPESTATUS[0]}"
```

The Tesseract image does not install or import PaddlePaddle/PaddleOCR. It emits TSV-derived bounding boxes and confidence scores through the existing `OCRResult` shape.
