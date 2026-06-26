# PlantBrain - AI-Powered Plant Intelligence Backend

> Built for hackathon · Free tier deployable · Works in 24 hours

PlantBrain is a FastAPI backend that ingests industrial plant documents such as P&IDs, maintenance records, OEM manuals, and OISD/PESO compliance guidelines, then enables natural language Q&A over them in English and Hindi. It builds a living equipment knowledge graph, monitors regulatory compliance, detects failure patterns, and captures voice knowledge from field technicians.

## Live Demo

API: [https://your-app.onrender.com](https://your-app.onrender.com)  
Docs: [https://your-app.onrender.com/docs](https://your-app.onrender.com/docs)

---

## Features

| Feature | Status | Details |
|---------|--------|---------|
| Document Q&A | Done | PDF, DOCX, TXT, scanned images |
| Hindi support | Done | Question and answer in Hindi |
| Equipment graph | Done | Auto-extracted from documents |
| Compliance check | Done | OISD, PESO, Factory Act rules |
| Failure patterns | Done | AI-powered cluster detection |
| Voice capture | Done | Whisper transcription to graph |
| WhatsApp bot | Done | Via Twilio webhook |
| Streamlit UI | Done | In `plantbrain-frontend/` |
| Next.js dashboard | Done | In `frontend/` |

---

## Architecture

```text
User / Engineer
    |
    | Web dashboard, Streamlit UI, WhatsApp, API client
    v
FastAPI Backend
    |
    |-- Document ingestion
    |   |-- File parser: PDF, DOCX, TXT, OCR images
    |   |-- Text chunker: English + Hindi sentence handling
    |   |-- Embeddings: sentence-transformers
    |   `-- Vector store: ChromaDB
    |
    |-- Q&A
    |   |-- Vector retrieval
    |   |-- Equipment graph context
    |   `-- Gemini 2.5 response generation
    |
    |-- Knowledge graph
    |   `-- NetworkX persisted graph
    |
    |-- Compliance
    |   `-- OISD, PESO, Factory Act rule checks
    |
    |-- Pattern detection
    |   `-- Inspection analytics + AI summaries
    |
    `-- Voice capture
        `-- Local Whisper transcription
```

## Tech Stack

| Layer | Technology |
|------|------------|
| API | FastAPI, Uvicorn |
| Database | SQLite + SQLAlchemy async + aiosqlite |
| Vector DB | ChromaDB persistent client |
| Embeddings | sentence-transformers multilingual model |
| LLM | Gemini 2.5 API via `google-genai` |
| Graph | NetworkX |
| OCR | PyMuPDF, Tesseract, Pillow |
| Voice | OpenAI Whisper local model |
| Analytics | pandas, NumPy |
| Frontend | Next.js dashboard and Streamlit UI |
| Deployment | Render free tier |

---

## Repository Layout

```text
plantbrain-backend/
  app/
    main.py                 FastAPI app and lifespan
    config.py               Environment settings
    database.py             Async SQLite setup
    middleware.py           Logging, errors, rate limiting
    scheduler.py            Lightweight background jobs
    startup_checks.py       Startup validation checks
    models/                 SQLAlchemy models
    routers/                API endpoints
    services/               Ingestion, LLM, graph, vector, voice, patterns
    utils/                  File parsing and text chunking
  data/
    uploads/
    chroma_db/
    graph/
  tests/
  verify_deployment.py
  seed_demo_data.py
  run_local.sh
  render.yaml
  requirements.txt
```

---

## Local Setup

### One-command setup

```bash
cd plantbrain-backend
bash run_local.sh
```

The script creates a virtual environment, installs dependencies, creates `.env`, starts the backend, and seeds demo data.

### Manual setup

```bash
cd plantbrain-backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set:

```env
GEMINI_API_KEY=your_real_key_here
```

Then run:

```bash
uvicorn app.main:app --reload
```

Open:

- API: [http://localhost:8000](http://localhost:8000)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## Frontends

### Next.js Dashboard

```bash
cd ../frontend
npm install
npm run dev
```

Set the backend URL in `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

The live backend demo page is available at:

```text
/dashboard/demo
```

### Streamlit Frontend

```bash
cd ../plantbrain-frontend
pip install -r requirements.txt
streamlit run app.py
```

The Streamlit sidebar lets you configure the backend URL.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Gemini API key for Q&A, compliance, summaries |
| `GEMINI_MODEL` | No | Default `gemini-2.5-flash` |
| `ENVIRONMENT` | No | `development` or `production` |
| `DATABASE_URL` | No | SQLite async URL |
| `CHROMA_PERSIST_DIR` | No | ChromaDB persistence directory |
| `GRAPH_PERSIST_PATH` | No | NetworkX graph pickle path |
| `UPLOAD_DIR` | No | Uploaded file directory |
| `MAX_UPLOAD_SIZE_MB` | No | Upload size limit |
| `CHUNK_SIZE` | No | Text chunk size |
| `CHUNK_OVERLAP` | No | Chunk overlap |
| `EMBEDDING_MODEL` | No | SentenceTransformer model |
| `TOP_K_RESULTS` | No | Retrieval result count |
| `WHISPER_MODEL` | No | Whisper model name |
| `CORS_ORIGINS` | No | CORS origins |
| `TWILIO_ACCOUNT_SID` | Optional | Twilio SID for WhatsApp alerts |
| `TWILIO_AUTH_TOKEN` | Optional | Twilio auth token |
| `TWILIO_WHATSAPP_FROM` | Optional | Twilio WhatsApp sender |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | No | Per-IP request limit |
| `RATE_LIMIT_ENABLED` | No | Enable or disable rate limiting |
| `ADMIN_API_KEY` | Recommended | Admin endpoint API key |
| `DEFAULT_LANGUAGE` | No | Default language |
| `SUPPORTED_LANGUAGES` | No | Comma-separated supported languages |

In production, defaults are tuned for Render free tier:

- `CHUNK_SIZE=600`
- `TOP_K_RESULTS=3`
- `WHISPER_MODEL=tiny`

---

## API Endpoints

### Health

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Basic health |
| GET | `/api/v1/health` | Versioned health |
| GET | `/api/v1/health/deep` | Database, vector store, graph checks |
| GET | `/api/v1/startup-checks` | Cached startup validation |
| GET | `/api/v1/version` | Runtime and package versions |
| GET | `/api/v1/docs-examples` | Curl examples |
| GET | `/api/v1/postman-collection` | Importable Postman collection |

### Document Ingestion

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/ingest/upload` | Upload document |
| GET | `/api/v1/ingest/status/{document_id}` | Processing status |
| GET | `/api/v1/ingest/list` | List documents |
| GET | `/api/v1/ingest/stats` | Ingestion stats |
| GET | `/api/v1/ingest/processing` | Active processing tasks |
| DELETE | `/api/v1/ingest/processing/{document_id}` | Cancel processing |
| DELETE | `/api/v1/ingest/{document_id}` | Delete document |

### Query

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/query/ask` | Ask PlantBrain |
| GET | `/api/v1/query/history` | Query history |
| GET | `/api/v1/query/history/{query_id}` | Query detail |
| POST | `/api/v1/query/feedback/{query_id}` | Answer feedback |
| GET | `/api/v1/query/search-chunks` | Raw vector search |

### Equipment Graph

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/graph/equipment` | Add equipment |
| GET | `/api/v1/graph/equipment` | List equipment |
| GET | `/api/v1/graph/equipment/{tag}` | Equipment detail |
| POST | `/api/v1/graph/relationship` | Add relationship |
| GET | `/api/v1/graph/neighbors/{tag}` | Neighbor search |
| GET | `/api/v1/graph/path/{source}/{target}` | Shortest path |
| GET | `/api/v1/graph/stats` | Graph stats |
| GET | `/api/v1/graph/export` | Export graph JSON |

### Compliance

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/compliance/rules` | Create rule |
| GET | `/api/v1/compliance/rules` | List rules |
| GET | `/api/v1/compliance/rules/{rule_code}` | Rule detail |
| DELETE | `/api/v1/compliance/rules/{rule_code}` | Deactivate rule |
| POST | `/api/v1/compliance/check` | Run compliance check |
| GET | `/api/v1/compliance/checks/document/{document_id}` | Document checks |
| POST | `/api/v1/compliance/seed-rules` | Seed built-in rules |

### Pattern Detection

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/patterns/clusters` | Failure clusters |
| GET | `/api/v1/patterns/overdue` | Overdue inspections |
| GET | `/api/v1/patterns/cooccurrence` | Co-occurrence patterns |
| GET | `/api/v1/patterns/risk-summary` | Risk dashboard summary |
| POST | `/api/v1/patterns/inspections/seed` | Seed demo inspections |
| POST | `/api/v1/patterns/inspections/manual` | Add inspection |

### Voice

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/voice/transcribe` | Upload voice note |
| GET | `/api/v1/voice/transcription/{document_id}` | Voice status |
| POST | `/api/v1/voice/transcribe-text` | Typed knowledge capture |
| GET | `/api/v1/voice/recent-captures` | Recent captures |

### WhatsApp

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/whatsapp/webhook` | Twilio webhook |
| GET | `/api/v1/whatsapp/webhook` | Webhook health |
| POST | `/api/v1/whatsapp/send-alert` | Send WhatsApp alert |

### Admin

Admin endpoints require `X-Admin-Key` in production.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/admin/stats` | System stats |
| DELETE | `/api/v1/admin/reset/vector-store` | Reset vectors |
| DELETE | `/api/v1/admin/reset/graph` | Reset graph |
| POST | `/api/v1/admin/reprocess/{document_id}` | Reprocess document |
| GET | `/api/v1/admin/query-stats` | Query analytics |
| POST | `/api/v1/admin/export/db` | Export database JSON |
| GET | `/api/v1/admin/logs/recent` | Recent logs |

---

## Demo Workflow

1. Seed built-in compliance rules.
2. Seed demo equipment and inspection data.
3. Upload a small document.
4. Ask: `What are the known issues with pump P-202?`
5. Open the equipment graph and inspect `P-202`.
6. Run a compliance check for `OISD-116-3.2`.
7. Open risk summary.
8. Test Hindi: `P-202 पंप की क्या समस्याएं हैं?`

Seed demo data:

```bash
python seed_demo_data.py
```

Verify deployment:

```bash
python verify_deployment.py https://your-app.onrender.com
```

Import Postman collection:

```text
https://your-app.onrender.com/api/v1/postman-collection
```

---

## Curl Examples

Upload a document:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -F "file=@manual.pdf"
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the issues with pump P-202?", "language": "auto"}'
```

Ask in Hindi:

```bash
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "P-202 पंप की क्या समस्याएं हैं?", "language": "hi"}'
```

Run compliance check:

```bash
curl -X POST http://localhost:8000/api/v1/compliance/check \
  -H "Content-Type: application/json" \
  -d '{"procedure_text": "PRV tested annually", "rule_codes": ["OISD-116-3.2"]}'
```

Get risk summary:

```bash
curl http://localhost:8000/api/v1/patterns/risk-summary
```

---

## Deploying to Render

1. Push this repository to GitHub.
2. Create a new Render Web Service.
3. Select the backend root directory: `plantbrain-backend`.
4. Use the included `render.yaml`, or configure manually:

```text
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

5. Add required environment variables:

```env
GEMINI_API_KEY=your_real_key
ENVIRONMENT=production
ADMIN_API_KEY=choose_a_real_admin_key
```

6. Deploy.
7. Run:

```bash
python verify_deployment.py https://your-app.onrender.com
```

---

## WhatsApp Setup

1. Create or open a Twilio WhatsApp sandbox.
2. Set the inbound webhook URL:

```text
https://your-app.onrender.com/api/v1/whatsapp/webhook
```

3. Send:

```text
HELP
STATUS
RISK
What are the known issues with pump P-202?
P-202 पंप की क्या समस्याएं हैं?
```

---

## Production Notes

PlantBrain is designed to run on a free-tier backend for a hackathon demo, but there are known tradeoffs:

- Render free tier cold starts can be slow.
- First embedding model load can take time.
- Whisper local transcription is CPU-heavy; production defaults use `tiny`.
- ChromaDB and SQLite are disk-based and suitable for demo scale.
- Render free tier disk persistence can be limited depending on service configuration.
- Tesseract must be available for OCR-heavy scanned documents.
- Long compliance or pattern scans may take time because they call the LLM.

---

## Testing

Run tests:

```bash
pytest tests/ -v
```

Run deployment verification locally:

```bash
python verify_deployment.py http://localhost:8000
```

Run the backend:

```bash
make run
```

Seed demo data:

```bash
make seed
```

---

## Hackathon Judge Notes

PlantBrain demonstrates:

- Retrieval-augmented Q&A over messy plant documents.
- Multilingual English/Hindi interaction.
- Automatic equipment knowledge graph construction.
- Compliance reasoning against industrial regulations.
- Reliability pattern detection from inspection history.
- Voice-to-knowledge capture for field teams.
- WhatsApp access for low-friction industrial use.
- Deployability on free-tier infrastructure.

The fastest demo path is:

```bash
cd plantbrain-backend
bash run_local.sh
```

Then open:

```text
http://localhost:8000/docs
```

or use the frontend dashboards in `frontend/` and `plantbrain-frontend/`.
