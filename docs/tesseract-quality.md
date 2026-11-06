# Tesseract Quality Tuning

The quality runner is local-only and does not use PaddlePaddle, Ollama, or cloud services. It evaluates 64 combinations per sample:

- Rotations: 0, 90, 180, 270 degrees.
- Preprocessing: original, grayscale, light threshold, light contrast.
- Tesseract PSM: 3, 4, 6, 11.

It records EXIF orientation, raw text, TSV confidence, bounding boxes, duration, and a technical ranking score. The ranking score is not field accuracy. It favors confidence, readable alphanumeric ratio, and a reasonable number of lines. Operator ground truth is still required for accuracy.

Run on Linux staging:

```sh
docker compose -f infra/docker-compose.yml --profile ocr-tesseract-quality build ocr-tesseract-quality
docker compose -f infra/docker-compose.yml --profile ocr-tesseract-quality run --name bmc-tesseract-quality ocr-tesseract-quality
docker cp bmc-tesseract-quality:/results/PT-Bakrie-Autoparts.tesseract-quality.json ./docs/
docker rm bmc-tesseract-quality
```

The result is written to the named `tesseract_quality_results` volume to avoid checkout permission issues. Copy it out with `docker cp` as shown above. Original samples are read-only. Bounding boxes are mapped back to the EXIF-normalized original coordinate system.
