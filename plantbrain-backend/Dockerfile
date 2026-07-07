FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PORT=7860 \
    ENVIRONMENT=production \
    LIGHTWEIGHT_EMBEDDINGS=true \
    DOCUMENT_PARSER=pymupdf \
    DATABASE_URL=sqlite+aiosqlite:////data/plantbrain.db \
    REQUIRE_NEO4J_IN_PRODUCTION=false \
    CHROMA_PERSIST_DIR=/data/chroma_db \
    UPLOAD_DIR=/data/uploads

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        tesseract-ocr \
        poppler-utils \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements-hf.txt ./requirements-hf.txt
RUN pip install --no-cache-dir -r requirements-hf.txt

COPY . .
RUN mkdir -p /data/chroma_db /data/uploads /data/graph

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --workers 1"]
