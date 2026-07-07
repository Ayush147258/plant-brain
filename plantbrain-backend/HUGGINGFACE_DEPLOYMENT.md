# Hugging Face Spaces Deployment

PlantBrain's backend is memory-heavy because it parses PDFs, OCRs scanned pages, chunks documents, builds embeddings, and routes Gemini multimodal extraction. Do not position a tiny 512 MB free web-service container as the main demo backend for this workload.

Recommended free backend target: Hugging Face Spaces with Docker.

## Why Hugging Face Spaces

- More practical free CPU/RAM envelope for document processing demos.
- Docker support lets us install OCR/PDF system packages such as Tesseract and Poppler.
- Persistent storage can keep uploads and Chroma data across restarts when configured.
- The public Space URL can be wired directly into the Vercel frontend.

## Space Setup

1. Create a new Hugging Face Space.
2. Choose Docker as the SDK.
3. Set the Space root to `plantbrain-backend` or copy this backend folder into the Space repo root.
4. Add these secrets in Space settings:

```env
GEMINI_API_KEY=your_gemini_key
DATABASE_URL=postgresql+psycopg://user:password@host:5432/plantbrain
NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
WORKER_QUEUE_URL=redis://user:password@host:6379/0
ADMIN_API_KEY=choose_a_real_admin_key
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

5. Hugging Face exposes the app on port `7860`; the included `Dockerfile` is already configured for that.
6. Set Vercel frontend env:

```env
NEXT_PUBLIC_PLANTBRAIN_API_URL=https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space
```

## Colab Backup Demo

For a temporary live demo, Colab can run the backend and expose it with ngrok/localtunnel. This is not production infrastructure, but it is useful when you need a GPU-backed demo session quickly.

```bash
pip install -r requirements.txt pyngrok
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Then expose port `8000` with ngrok and put the ngrok URL into `NEXT_PUBLIC_PLANTBRAIN_API_URL`.

## Production Path

For industry-grade pilots, keep the same app shape but use:

- Hugging Face Spaces or paid container hosting for the API.
- Managed Postgres for SQL metadata.
- Neo4j Aura as the source-of-truth graph database.
- Redis/Celery or a managed queue for ingestion jobs.
- Persistent object storage for uploaded PDFs and scans.
