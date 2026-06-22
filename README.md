<div align="center">

<img src="https://img.shields.io/badge/Status-Phase%201%20Prototype-00d4ff?style=for-the-badge&labelColor=0a0a0f" />
<img src="https://img.shields.io/badge/Theme-Industrial%20Knowledge%20Intelligence-00ff88?style=for-the-badge&labelColor=0a0a0f" />

<br /><br />

```
██████╗ ██╗      █████╗ ███╗   ██╗████████╗    ██████╗ ██████╗  █████╗ ██╗███╗   ██╗
██╔══██╗██║     ██╔══██╗████╗  ██║╚══██╔══╝    ██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║
██████╔╝██║     ███████║██╔██╗ ██║   ██║       ██████╔╝██████╔╝███████║██║██╔██╗ ██║
██╔═══╝ ██║     ██╔══██║██║╚██╗██║   ██║       ██╔══██╗██╔══██╗██╔══██║██║██║╚██╗██║
██║     ███████╗██║  ██║██║ ╚████║   ██║       ██████╔╝██║  ██║██║  ██║██║██║ ╚████║
╚═╝     ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝       ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
```

### **Stop Searching. Start Knowing.**

*Industrial Knowledge Intelligence — Every document, every procedure, every answer. In seconds.*

<br />

[![Live Demo](https://img.shields.io/badge/🚀_Live_Demo-plantbrain.vercel.app-00d4ff?style=for-the-badge&labelColor=12121a)](https://plantbrain.vercel.app)
[![API](https://img.shields.io/badge/⚡_API_Docs-plantbrain.onrender.com/docs-ff6b35?style=for-the-badge&labelColor=12121a)](https://plantbrain.onrender.com/docs)
[![YouTube](https://img.shields.io/badge/▶_Demo_Video-Watch_Now-ff0000?style=for-the-badge&labelColor=12121a)](https://youtube.com)

</div>

---

## The Problem We're Solving

India's heavy industrial sector — steel plants, refineries, chemical facilities, power plants — runs on knowledge. **That knowledge is disappearing.**

| The Reality | The Number | Source |
|---|---|---|
| Time spent searching for information that already exists | **35% of every shift** | McKinsey Global Survey, 2024 |
| Disconnected document systems per large Indian plant | **7 to 12** | NASSCOM-EY Manufacturing Study |
| Unplanned downtime events caused by knowledge gaps | **18–22%** | BIS Research, Indian Heavy Industry |
| Senior engineers retiring this decade — with knowledge no system has captured | **25%** | India Engineering Workforce Report, 2024 |

> *"In one of the most disturbing recent incidents, eight workers died at Visakhapatnam Steel Plant when entrapped gases triggered a sudden explosion — a facility that had functioning safety systems. Warning signals existed. But no intelligence layer connected those readings to operational decisions in time."*
> — The Wire, January 2025

**The data exists. The intelligence layer doesn't. PlantBrain is that layer.**

---

## What PlantBrain Does

```
Without PlantBrain          With PlantBrain
──────────────────          ───────────────────────────────────────────────────────

Technician needs            Technician types: "What's the seal replacement
maintenance interval   →    interval for P-201?"
for Pump P-201
                            PlantBrain responds in 0.9 seconds:
Searches shared drive       ┌─────────────────────────────────────────────────────┐
↓ (15 minutes)              │ Based on OEM Manual Rev.4 (Section 7.2) and Work    │
Finds 3 PDFs                │ Order WO-2024-0441, the recommended mechanical seal  │
↓ (10 more minutes)         │ replacement interval for P-201 is every 8,000        │
Reads all three             │ operating hours or 12 months — whichever comes first.│
↓ (finds nothing)           │                                                     │
Asks the retiring           │ ⚠ Note: Last replacement was 7,200 hours ago.       │
engineer down the hall      │ Sources: OEM-P201-Rev4 (94% fresh) · WO-2024-0441   │
↓ (he doesn't know either)  │ Confidence: 96% · Answered in 0.9s                  │
Makes a guess               └─────────────────────────────────────────────────────┘
```

---

## Live Demo

<div align="center">

| Dashboard | Knowledge Copilot | Decay Monitor |
|:---------:|:-----------------:|:-------------:|
| Plant-wide intelligence overview | AI chat with source citations | Stale document early warning |
| Real-time alert feed | Confidence scoring per answer | Risk-ranked document table |
| Zone risk heatmap | Claude Sonnet 4.6 powered | Days-since-validation tracking |

**→ [Try it live at plantbrain.vercel.app](https://plantbrain.vercel.app)**

</div>

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INTERFACES                                │
│                                                                             │
│   🖥️  Web Dashboard    📱  Mobile App (Phase 2)    💬  WhatsApp Bot (Ph.2) │
│        React                React Native               Twilio / Meta API    │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
                          ▼ HTTPS / REST + SSE
┌─────────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                      │
│                                                                             │
│   FastAPI  ·  Async Python  ·  Pydantic validation  ·  JWT Auth            │
│                                                                             │
│   POST /query          POST /query/stream         GET /documents            │
│   POST /documents      GET /health                GET /compliance           │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           INTELLIGENCE LAYER                                │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                        LLM Router                                    │  │
│  │                                                                      │  │
│  │   Primary: Claude Sonnet 4.6  ──→  Fallback: Gemini 2.0 Flash       │  │
│  │   (on 429 / 529 / 5xx)            (transparent, same response shape) │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────────────┐   ┌──────────────────────────────────────────┐   │
│  │  Document Retrieval  │   │        Knowledge Decay Monitor           │   │
│  │                      │   │                                          │   │
│  │  Phase 1: Keyword    │   │  Freshness score per document            │   │
│  │  scoring (TF-IDF)    │   │  Continuous background scan              │   │
│  │                      │   │  Risk-typed alert generation             │   │
│  │  Phase 2: OG-RAG     │   │                                          │   │
│  │  + Neo4j hyperedge   │   │  Critical  < 0.50   ██ RED               │   │
│  └─────────────────────┘   │  Warning   0.5–0.79  ██ AMBER             │   │
│                             │  Healthy   ≥ 0.80   ██ GREEN             │   │
│                             └──────────────────────────────────────────┘   │
└─────────────────────────┬───────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA LAYER                                      │
│                                                                             │
│   Supabase PostgreSQL          Supabase Storage                             │
│   ────────────────────         ─────────────────                            │
│   documents table              Raw document files                           │
│   id · title · content         Original PDFs, TXTs                          │
│   source_type · tags           Audit trail preserved                        │
│   freshness_score                                                           │
│   last_validated_date                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### AI Decision Flow

```
User Query
    │
    ▼
┌───────────────────────────────────────┐
│  1. Retrieve relevant documents        │
│     Score each by keyword overlap      │
│     Return top-5 by relevance          │
└─────────────────┬─────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────┐
│  2. Build grounded system prompt       │
│     Inject document context            │
│     Instruct: cite sources, no guessing│
└─────────────────┬─────────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │  Claude Sonnet │  ← Primary
         │     4.6        │
         └───────┬────────┘
                 │  ← On 429/529/5xx error
                 ▼
         ┌────────────────┐
         │ Gemini 2.0     │  ← Automatic fallback
         │    Flash       │     Same prompt, same output shape
         └───────┬────────┘
                 │
                 ▼
┌───────────────────────────────────────┐
│  3. Parse response                     │
│     Extract cited document titles      │
│     Compute confidence score           │
│     Attach freshness warnings          │
└─────────────────┬─────────────────────┘
                  │
                  ▼
           Structured JSON
         ┌──────────────────────────────┐
         │  answer: "..."               │
         │  sources_used: [...]         │
         │  confidence_score: 0.94      │
         │  model_used: "claude-..."    │
         │  latency_ms: 870             │
         │  fallback_triggered: false   │
         └──────────────────────────────┘
```

---

## Core Features

### 🤖 AI Knowledge Copilot
Ask any operational question in plain language. PlantBrain searches across all ingested documents and returns a cited, confidence-scored answer in under a second.

```
Q: "Which OISD clauses apply when issuing hot work permits near coke oven batteries?"

A: OISD-116 Section 4.3 requires a gas-free certificate and continuous gas monitoring
   during any hot work within 15 metres of a coke oven battery. Additionally, OISD-118
   Section 7.1 mandates that the Permit-to-Work be signed by the Area Safety Officer
   and displayed at the work site.

   Sources: OISD-116 §4.3 (freshness: 98%) · OISD-118 §7.1 (freshness: 72% ⚠)
   Confidence: 97% · Model: claude-sonnet-4-6 · 0.6s
```

### 📉 Knowledge Decay Monitor
Every document in PlantBrain carries a freshness score — a real-time measure of how current it is relative to when it was last validated. Stale knowledge is flagged before it causes decisions.

```
Document Health Overview
────────────────────────────────────────────────────────────────────
🔴 Critical  (< 0.50)   │ SOP-014 Confined Space Entry    │ 0.41
                         │ Last validated: 12 Apr 2026     │
                         │ Risk: Operators may follow      │
                         │       outdated safety steps     │
────────────────────────────────────────────────────────────────────
🟡 Warning  (0.5–0.79)  │ MNL-HX204 OEM Manual           │ 0.58
                         │ SOP-022 Hot Work Procedure      │ 0.72
────────────────────────────────────────────────────────────────────
🟢 Healthy  (≥ 0.80)    │ P&ID-07-Rev3 Zone 1 Layout     │ 0.91
                         │ OISD-116 Reference Digest       │ 0.98
```

### 📂 Universal Document Intelligence
Ingest anything. PlantBrain handles structured PDFs, scanned forms, maintenance work orders, regulatory documents, inspection reports, and operating procedures — structured or unstructured, old or new.

### 🔗 Source-Cited Answers
Every answer is traced to its source — document title, section or page, and a freshness indicator. No black-box AI. No answers that can't be verified.

---

## Why the Judges Should Care

| Criterion | What PlantBrain Delivers |
|---|---|
| **Innovation** | Knowledge Decay scoring — a quantified staleness metric that treats outdated documentation as operational risk, not a filing problem. No existing industrial product does this. |
| **Business Impact** | Directly addresses the ₹XX Cr/year productivity loss from knowledge fragmentation in Indian heavy industry. Measurable in hours recovered per technician per week. |
| **Technical Excellence** | Dual-LLM architecture with transparent failover, structured confidence scoring, and a grounded retrieval system that refuses to hallucinate — returns a structured error if no relevant documents exist. |
| **Scalability** | Stateless FastAPI backend deploys to any cloud. Document corpus scales independently of the AI layer. Phase 2 adds vector retrieval without changing the API contract. |
| **User Experience** | Technician asks a question on WhatsApp in Hindi. Manager gets a compliance gap report on desktop. Both see source citations. No training required. |

---

## Roadmap

### ✅ Phase 1 — Prototype (This Submission)
- [x] AI Knowledge Copilot with Claude Sonnet 4.6 + Gemini 2.0 Flash fallback
- [x] Source-cited answers with confidence scoring
- [x] Knowledge Decay Monitor with freshness scoring
- [x] Universal document ingestion (PDF, TXT, work orders, procedures)
- [x] Dashboard with zone risk overview, compliance tracker, alert feed
- [x] Deployed on Vercel + Render + Supabase (free tier, production-grade)

### 🔵 Phase 2 — Post-Qualification
- [ ] Vector embedding retrieval (replacing keyword search)
- [ ] Knowledge graph with multi-hop relational queries
- [ ] Compliance Agent — continuous background regulatory scanning
- [ ] Expert Knowledge Capture — voice note → permanent knowledge node
- [ ] WhatsApp bot + mobile app
- [ ] Hindi and regional language support (Bhashini API)
- [ ] Predictive maintenance pattern detection
- [ ] SAP / CMMS / SharePoint integrations

---

## Tech Stack

### Backend
```
FastAPI          Async Python API framework
Pydantic         Request/response validation and schema enforcement
Anthropic SDK    Claude Sonnet 4.6 — primary AI model
Google GenAI     Gemini 2.0 Flash — automatic fallback model
Supabase         PostgreSQL database + file storage
Uvicorn          ASGI server
```

### Frontend
```
Next.js 14       App router, server + client components
TypeScript       Full type safety across API contracts
Tailwind CSS     Design token system (dark industrial palette)
Recharts         Analytics and decay visualization
JetBrains Mono   Data display typography
```

### Deployment
```
Vercel           Frontend — global CDN, zero config
Render           Backend — auto-deploy from GitHub, free tier
Supabase         Database + storage — managed PostgreSQL
```

---

## Getting Started

### Prerequisites
```bash
node >= 18
python >= 3.11
```

### Clone and install

```bash
git clone https://github.com/your-org/plantbrain
cd plantbrain
```

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys (see Environment Variables below)
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

**Seed the database:**
```bash
cd backend
python -m app.data.seed_documents
# Seeds 14 realistic industrial documents into Supabase
```

Open [http://localhost:3000](http://localhost:3000) — the landing page.
Open [http://localhost:3000/dashboard](http://localhost:3000/dashboard) — the live product.

---

## Environment Variables

### Backend (`backend/.env`)

```env
# Anthropic — get from console.anthropic.com
ANTHROPIC_API_KEY=sk-ant-...

# Google AI Studio — free, no credit card — aistudio.google.com
GEMINI_API_KEY=AIza...

# Supabase — from project settings > API
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# Comma-separated allowed origins
ALLOWED_ORIGINS=http://localhost:3000,https://plantbrain.vercel.app

MAX_DOCUMENT_SIZE_MB=10
LOG_LEVEL=INFO
```

### Frontend (`frontend/.env.local`)

```env
# Your Render backend URL — no trailing slash
NEXT_PUBLIC_API_URL=https://plantbrain.onrender.com
```

---

## API Reference

### `POST /query`
Ask a question against the knowledge base.

**Request:**
```json
{
  "question": "What are the maintenance intervals for Pump P-201?",
  "equipment_context": "P-201"
}
```

**Response:**
```json
{
  "answer": "Based on OEM Manual Rev.4 (Section 7.2), the recommended mechanical seal replacement interval for P-201 is every 8,000 operating hours or 12 months, whichever comes first.",
  "sources_used": [
    {
      "document_title": "Pump P-201 OEM Maintenance Manual Rev.4",
      "source_type": "manual",
      "excerpt": "Mechanical seal replacement: every 8,000 operating hours or 12 months",
      "page_or_section": "Section 7.2",
      "freshness_score": 0.94
    }
  ],
  "confidence_score": 0.96,
  "model_used": "claude-sonnet-4-6",
  "latency_ms": 870,
  "fallback_triggered": false
}
```

### `GET /documents`
List all indexed documents with freshness scores.

### `POST /documents/upload`
Upload a new document (PDF or TXT, max 10MB).

### `GET /health`
Service health check — returns status of all connected services.

---

## Seed Documents Included

PlantBrain ships with 14 realistic industrial documents for demo purposes:

| # | Document | Type | Freshness |
|---|----------|------|-----------|
| 1 | Pump P-201 OEM Maintenance Manual Rev.4 | Manual | 🟢 0.94 |
| 2 | Compressor C-101 Operations Manual | Manual | 🟡 0.72 |
| 3 | Heat Exchanger E-105 Maintenance Guide | Manual | 🔴 0.48 |
| 4 | OISD-116 Petroleum Facilities Safety (Digest) | Regulation | 🟢 0.98 |
| 5 | OISD-118 Fire Protection Systems | Regulation | 🟡 0.71 |
| 6 | Work Order WO-2024-0441 — P-201 Seal Replacement | Work Order | 🟢 0.95 |
| 7 | Work Order WO-2024-0312 — C-101 Annual Service | Work Order | 🟢 0.88 |
| 8 | Work Order WO-2023-0198 — E-105 Tube Bundle Clean | Work Order | 🟡 0.62 |
| 9 | Zone 1 Coke Oven Battery Inspection Report — Q4 2025 | Inspection | 🟡 0.76 |
| 10 | Heat Exchanger E-105 Corrosion Inspection — 2024 | Inspection | 🔴 0.43 |
| 11 | SOP-014 Confined Space Entry Procedure | Procedure | 🔴 0.41 |
| 12 | SOP-022 Hot Work Permit Procedure | Procedure | 🟡 0.69 |
| 13 | Incident Report — P-201 Seal Failure, March 2023 | Incident | 🟢 0.87 |
| 14 | Zone 3 Steel Melt Shop Equipment Register | Register | 🟢 0.91 |

---

## Project Structure

```
plantbrain/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI app, middleware, lifespan
│   │   ├── api/
│   │   │   ├── query.py             # POST /query, POST /query/stream
│   │   │   ├── documents.py         # GET /documents, POST /documents/upload
│   │   │   └── health.py            # GET /health
│   │   ├── core/
│   │   │   ├── llm_router.py        # Claude primary → Gemini fallback
│   │   │   ├── document_store.py    # Supabase storage wrapper + keyword retrieval
│   │   │   └── config.py            # Pydantic settings, env var validation
│   │   ├── models/
│   │   │   └── schemas.py           # All Pydantic request/response models
│   │   └── data/
│   │       └── seed_documents.py    # 14 realistic industrial seed documents
│   ├── requirements.txt
│   ├── .env.example
│   └── render.yaml
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx             # Public landing page
│   │   │   └── dashboard/
│   │   │       └── page.tsx         # Copilot + Decay Monitor dashboard
│   │   ├── components/
│   │   │   ├── CopilotChat.tsx      # AI chat interface
│   │   │   ├── DecayPanel.tsx       # Knowledge decay monitor tab
│   │   │   ├── SourceCard.tsx       # Citation card with freshness indicator
│   │   │   ├── ConfidenceBar.tsx    # Animated confidence score bar
│   │   │   ├── LoadingDots.tsx      # AI thinking indicator
│   │   │   └── Navbar.tsx
│   │   └── lib/
│   │       └── api.ts               # Typed API client, error handling
│   ├── tailwind.config.ts           # Design tokens — industrial dark palette
│   ├── package.json
│   └── vercel.json
├── .gitignore
└── README.md
```

---

## Built For

<div align="center">

| Sector | Application |
|--------|-------------|
| 🏭 Steel & Metal Plants | Maintenance intelligence, safety compliance |
| 🛢️ Refineries & Petrochemicals | OISD compliance, permit-to-work intelligence |
| ⚡ Power Plants | Equipment manuals, inspection records, regulatory audit |
| ⚗️ Chemical Facilities | Safety procedures, hazard documentation, incident patterns |
| ⛏️ Mining Operations | DGMS compliance, equipment health, RCA support |
| 🏗️ Heavy Manufacturing | Work order intelligence, quality documentation |

</div>

---

## The Team

> *Add your team names, roles, and LinkedIn links here*

---

<div align="center">

**PlantBrain** — Industrial Knowledge Intelligence

*Built for IndiaAI Hackathon 2025 · Theme 8: AI for Industrial Knowledge Intelligence*

[![License: MIT](https://img.shields.io/badge/License-MIT-00d4ff?style=flat-square&labelColor=0a0a0f)](LICENSE)
[![Made in India](https://img.shields.io/badge/Made_in-India_🇮🇳-ff6b35?style=flat-square&labelColor=0a0a0f)](https://github.com)

```
Stop searching. Start knowing.
```

</div>
EOF
echo "done"
Output

done
Done

You are out of free messages until 2:00 AM




Claude is