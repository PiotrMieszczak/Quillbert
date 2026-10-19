FROM python:3.11-slim-bookworm

WORKDIR /app

# Tesseract for scanned pages (ADR-0002 IMP-005), with English and Polish data.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        tesseract-ocr tesseract-ocr-eng tesseract-ocr-pol \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md alembic.ini ./
COPY app ./app

RUN pip install --no-cache-dir .

EXPOSE 8000

# Migrations run as a dedicated CI step (.github/workflows/migrate.yml), not on boot.
# The app container only serves; the schema is already at head before it starts.
CMD ["uvicorn", "app.composition:build_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
