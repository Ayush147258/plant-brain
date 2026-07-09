---
title: PlantBrain Backend
emoji: 🏭
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---
# PlantBrain Backend - Industrial Graph-RAG API

PlantBrain is a FastAPI backend for industrial knowledge intelligence. It ingests P&IDs, scanned maintenance logs, manuals, work orders, and OISD/PESO compliance documents, then turns them into queryable Graph-RAG context backed by Neo4j, vector retrieval, and Gemini multimodal structured extraction.

## Live Demo Targets

- Frontend: `https://plantbrain.vercel.app`
- Backend API: `https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space`
- API docs: `https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space/docs`

For heavy PDF/OCR demos, do not use a tiny free web-service container as the primary backend. The recommended free demo target is Hugging Face Spaces with Docker because it has a more realistic CPU/RAM envelope for PDF parsing, OCR, embeddings, and Gemini routing.

## What This Backend Proves

| Capability | Implementation |
| --- | --- |
| Multimodal extraction | Gemini `response_schema` for P&IDs and scanned logs |
| Graph-RAG | Neo4j stores equipment, valves, instruments, zones, events, compliance links |
| Safe ingestion | Pipeline stages expose upload, parse, schema extraction, validation, confidence scoring, Neo4j MERGE, vector update, review queue, query readiness |
| Production graph writes | Cypher `MERGE` avoids duplicate nodes and relationships on repeated runs |
| Human review | Low-confidence or unclear fields are preserved instead of guessed |
| Retrieval | Chroma vector store plus Neo4j graph context for grounded answers |
| Failure intelligence | Lessons-learned warnings from incidents, near-misses, audit findings, QMS gaps, and graph context |
| Deployment | Docker backend for Hugging Face Spaces or paid container hosting, Vercel frontend, Neo4j Aura, managed Postgres |

## Architecture

```text
Web dashboard / API / WhatsApp
    |
    v
FastAPI backend
    |
    |-- Ingestion pipeline
    |   |-- PDF/DOCX/TXT/image parser with OCR fallback
    |   |-- Gemini multimodal schema extraction for P&IDs/logs
    |   |-- JSON validation and confidence flags
    |   |-- Neo4j MERGE for graph entities and relationships
    |   `-- Vector index update
    |
    |-- Graph-RAG query path
    |   |-- Vector retrieval over document chunks
    |   |-- Neo4j path, event, compliance, and asset context
    |   `-- Gemini answer generation with citations
    |
    |-- Compliance intelligence
    |   |-- OISD/PESO/Factory Act rule nodes
    |   `-- Compliance checks linked to equipment/assets
    |
    `-- Operations evidence
        |-- Pipeline dashboard API
        |-- Failure intelligence warnings and QMS signals
        |-- Deep health checks
        `-- Graph export for frontend visualization
```

## Tech Stack

| Layer | Technology |
| --- | --- |
| API | FastAPI, Uvicorn |
| Database | Postgres via SQLAlchemy async; SQLite only for local fallback |
| Graph DB | Neo4j Aura/live Neo4j primary; NetworkX only as local fallback |
| Vector DB | ChromaDB persistent client; production should use persistent volume or managed vector-ready storage |
| Multimodal AI | Gemini via `google-genai` structured outputs |
| Embeddings | sentence-transformers multilingual model |
| Parsing | Docling structured Markdown, PyMuPDF/Tesseract fallback |
| Queue | Celery/RQ-compatible Redis URL with local async fallback |
| Deployment | Hugging Face Spaces Docker for demo; paid container/worker tier for production |

## Repository Layout

```text
plantbrain-backend/
  app/
    main.py
    config.py
    database.py
    startup_checks.py
    routers/
    services/
      ingestion_service.py
      multimodal_extraction_service.py
      neo4j_service.py
      task_queue.py
    utils/
  data/
    uploads/
    chroma_db/
  tests/
  Dockerfile
  HUGGINGFACE_DEPLOYMENT.md
  verify_deployment.py
  seed_demo_data.py
  requirements.txt
```

## Local Setup

```bash
cd plantbrain-backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Deep health: `http://localhost:8000/api/v1/health/deep`

## Frontend Setup

```bash
cd ../frontend
npm install
npm run dev
```

Set the backend URL in `frontend/.env.local`:

```env
NEXT_PUBLIC_PLANTBRAIN_API_URL=http://localhost:8000
```

The industrial demo dashboard is available at:

```text
/demo
```

## Required Environment Variables

```env
GEMINI_API_KEY=your_real_key
DATABASE_URL=postgresql+psycopg://user:pass@host:5432/plantbrain
NEO4J_URI=neo4j+s://your-db.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
ADMIN_API_KEY=generate_a_strong_random_value
ENVIRONMENT=production
CORS_ORIGINS=https://plantbrain.vercel.app
```

Useful optional variables:

```env
GEMINI_MODEL=gemini-3.5-flash
GEMINI_EXTRACTION_MODEL=gemini-3.5-flash
MULTIMODAL_EXTRACTION_ENABLED=true
GRAPH_BACKEND=neo4j
REQUIRE_NEO4J_IN_PRODUCTION=true
WORKER_QUEUE_URL=redis://user:pass@host:6379/0
CHROMA_PERSIST_DIR=/data/chroma_db
UPLOAD_DIR=/data/uploads
MAX_UPLOAD_SIZE_MB=50
```

## Security Hardening

PlantBrain now enforces these production guardrails:

- `ADMIN_API_KEY` must be set to a non-default value in production. The backend refuses production startup when it is missing or still `changeme`.
- `CORS_ORIGINS` must be restricted in production. Wildcard `*` is for local development only and fails production startup.
- Admin endpoints require `X-Admin-Key`, including document deletion, processing cancellation, vector reset, graph reset, database export, pending-review promotion, and outbound WhatsApp alerts.
- The Twilio inbound webhook validates `X-Twilio-Signature` whenever `TWILIO_AUTH_TOKEN` is configured. Use the exact public HTTPS webhook URL in Twilio: `/api/v1/whatsapp/webhook`.
- Real `.env` files, uploads, Chroma data, graph pickles, SQLite databases, logs, videos, and bundled demo documents are ignored by git. Keep secrets in deployment secret stores.
## Hugging Face Spaces Backend Deployment

The recommended free/demo backend target is **Hugging Face Spaces with Docker**. PlantBrain needs Docker because the backend depends on native PDF/OCR tooling such as Tesseract, Poppler, OpenCV libraries, and FFmpeg.

### 1. Create the Space

1. Go to Hugging Face Spaces and create a new Space.
2. Choose **Docker** as the Space SDK.
3. Use a public or private Space depending on the demo.
4. Push the contents of `plantbrain-backend/` as the Space repository root. The Space root must contain:

```text
Dockerfile
requirements.txt
startup.sh
app/
```

The included `Dockerfile` exposes port `7860`, which is the default Hugging Face Spaces web port.

### 2. Configure Space Secrets

Add these in **Space settings -> Secrets**:

```env
GEMINI_API_KEY=your_real_gemini_key
GEMINI_MODEL=gemini-3.5-flash
GEMINI_EXTRACTION_MODEL=gemini-3.5-flash
MULTIMODAL_EXTRACTION_ENABLED=true

ENVIRONMENT=production
DATABASE_URL=postgresql+psycopg://user:password@host:5432/plantbrain

NEO4J_URI=neo4j+s://your-aura-instance.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
GRAPH_BACKEND=neo4j
REQUIRE_NEO4J_IN_PRODUCTION=true

ADMIN_API_KEY=generate_a_strong_random_value
CORS_ORIGINS=https://your-vercel-app.vercel.app

CHROMA_PERSIST_DIR=/data/chroma_db
UPLOAD_DIR=/data/uploads
DOCUMENT_PARSER=docling
OCR_CONFIDENCE_THRESHOLD=55.0
MAX_UPLOAD_SIZE_MB=50
LIGHTWEIGHT_EMBEDDINGS=true
```

Optional, when you have Redis/Celery available:

```env
WORKER_QUEUE_URL=redis://user:password@host:6379/0
```

### 3. Persistent Storage

For serious demos, enable Hugging Face persistent storage if available. Use:

```env
CHROMA_PERSIST_DIR=/data/chroma_db
UPLOAD_DIR=/data/uploads
GRAPH_PERSIST_PATH=/data/graph/equipment_graph.pkl
```

Without persistent storage, uploaded files and local Chroma indexes may be lost when the Space rebuilds or restarts. Neo4j and Postgres data remain safe because they live outside the Space.

### 4. Deploy And Verify

After pushing the backend folder to the Space, Hugging Face will build the Docker image. When the Space is running, verify:

```bash
python verify_deployment.py https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space
```

Manual checks:

```text
https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space/
https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space/docs
https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space/api/v1/health/deep
https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space/api/v1/startup-checks
```

Expected result for a fully configured demo:

- API health returns `healthy`.
- Deep health shows database, vector store, and graph checks healthy or explicitly degraded with a readable reason.
- `/docs` loads the FastAPI OpenAPI UI.
- Uploads can write under `/data/uploads`.
- Chroma can persist under `/data/chroma_db`.

### 5. Connect The Vercel Frontend

Set this in the frontend deployment environment:

```env
NEXT_PUBLIC_PLANTBRAIN_API_URL=https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space
```

Redeploy Vercel after changing the environment variable.

### 6. Demo Workflow On Hugging Face

1. Open `/api/v1/health/deep` and confirm the backend is reachable.
2. Seed compliance rules with `POST /api/v1/compliance/seed-rules`.
3. Upload a small PDF or scan from the frontend demo.
4. Watch `/api/v1/ingest/pipeline` for parser, Gemini extraction, confidence scoring, Neo4j merge, review queue, and query readiness stages.
5. Open `/api/v1/graph/stats` to confirm graph nodes and edges are being created.
6. Ask a cited Graph-RAG question from the frontend `/demo` page.

### 7. Common Hugging Face Issues

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Space builds but app does not open | App is not listening on port `7860` | Use the included `Dockerfile`; it runs Uvicorn on `${PORT:-7860}` |
| OCR fails | Missing native packages | Keep the included Docker `apt-get install` block for Tesseract, Poppler, FFmpeg, `libgl1`, and `libglib2.0-0` |
| Uploads disappear after restart | No persistent storage | Enable HF persistent storage or rely on external object storage for production |
| Deep health shows graph failure | Neo4j secrets are missing or Aura network/auth is wrong | Check `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` |
| Browser CORS error from Vercel | Wrong `CORS_ORIGINS` | Set `CORS_ORIGINS=https://your-vercel-app.vercel.app` |
| First request is slow | Space cold start | Open the Space before the demo or keep a small health monitor running |

## Deployment Stack

Recommended demo stack:

```text
Vercel                  Frontend dashboard
Hugging Face Spaces     Dockerized FastAPI backend
Neo4j Aura              Live graph database
Managed Postgres        Document/job metadata
Persistent volume       Chroma index and uploads where available
```

For a quick temporary backup demo, a Colab notebook can run the backend and expose it through ngrok/localtunnel. That is useful for a live pitch, but it is not production infrastructure.

See `HUGGINGFACE_DEPLOYMENT.md` for a shorter deployment checklist.

## API Endpoints

### Health

| Method | Path | Description |
| --- | --- | --- |
| GET | `/` | Basic health |
| GET | `/api/v1/health` | Versioned health |
| GET | `/api/v1/health/deep` | Database, vector store, graph checks |
| GET | `/api/v1/startup-checks` | Cached startup validation |
| GET | `/api/v1/version` | Runtime and package versions |

### Ingestion

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/ingest/upload` | Upload document, P&ID, or scanned log |
| GET | `/api/v1/ingest/pipeline` | Plant Intelligence Pipeline status |
| GET | `/api/v1/ingest/status/{document_id}` | Processing status |
| GET | `/api/v1/ingest/list` | List documents |
| GET | `/api/v1/ingest/stats` | Ingestion stats |

### Graph

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/graph/equipment` | Add/merge equipment |
| GET | `/api/v1/graph/equipment` | List equipment |
| GET | `/api/v1/graph/equipment/{tag}` | Equipment detail |
| POST | `/api/v1/graph/relationship` | Add/merge relationship |
| GET | `/api/v1/graph/neighbors/{tag}` | Neighbor search |
| GET | `/api/v1/graph/export` | Export nodes/edges for visualization |
| GET | `/api/v1/graph/stats` | Neo4j node/edge counts |

### Query And Compliance

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/v1/query/ask` | Ask PlantBrain with vector + graph context |
| GET | `/api/v1/query/history` | Query history |
| POST | `/api/v1/compliance/check` | Run compliance check |
| POST | `/api/v1/compliance/seed-rules` | Seed built-in rules |
| GET | `/api/v1/patterns/risk-summary` | Risk dashboard summary |
| GET | `/api/v1/patterns/failure-intelligence` | Lessons-learned warnings, systemic patterns, QMS signals, and validation metrics |

## Demo Workflow

1. Configure Gemini, Neo4j Aura, and Postgres environment variables.
2. Start the backend and confirm `/api/v1/health/deep` is healthy.
3. Upload a P&ID with `extraction_kind=pid` and a zone name.
4. Confirm the pipeline shows Gemini schema extraction, JSON validation, Neo4j MERGE, vector update, and query readiness.
5. Open the graph dashboard and inspect equipment, valves, instruments, and maintenance events.
6. Ask a Graph-RAG question such as `Which valves connect P-201 to HX-204 and what recent failures are linked to that path?`
7. Run a compliance check and show linked equipment/rules in Neo4j context.
8. Open Failure Intel or call `/api/v1/patterns/failure-intelligence` to show proactive warnings, P-201 connected assets, QMS signals, and validation metrics.

Verify deployment:

```bash
python verify_deployment.py https://YOUR_SPACE_OWNER-YOUR_SPACE_NAME.hf.space
```

## Production Notes

- Neo4j is primary for equipment, valves, instruments, zones, maintenance events, compliance rules, and relationships.
- NetworkX should stay out of the main production path and only serve local fallback/demo use.
- Use managed Postgres instead of SQLite for live deployments.
- Use persistent vector storage or managed vector-ready storage for production retrieval.
- Use a durable worker queue for long PDF/OCR/Gemini jobs instead of relying only on in-process tasks.
- OCR-heavy scans need Tesseract and enough memory to parse multi-page technical PDFs reliably.
- Repeated P&ID/log ingestion uses Neo4j `MERGE` semantics so reprocessing corrected scans updates the graph rather than duplicating it.

## Testing

```bash
pytest tests/ -v
python verify_deployment.py http://localhost:8000
```

## Investor Demo Positioning

PlantBrain is not a thin AI wrapper. The demo should show live evidence:

- Plant Intelligence Pipeline state
- Neo4j node/edge counts
- Equipment graph with relationship labels
- Low-confidence review queue
- Compliance risk and audit trail
- Query latency and recovered job metrics
- Source-cited Graph-RAG answers
