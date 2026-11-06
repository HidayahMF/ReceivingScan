FROM python:3.12-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ unixodbc-dev tesseract-ocr tesseract-ocr-eng tesseract-ocr-ind libtesseract5 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt
COPY requirements-universal-ocr.txt .
RUN pip install --no-cache-dir -r requirements-universal-ocr.txt
COPY app ./app
RUN mkdir -p /var/lib/receiving-ai && chown -R 10001:10001 /var/lib/receiving-ai /app
USER 10001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
