# PlantBrain Architecture

Use this diagram in the deck and demo video to explain why PlantBrain is more than document search.

```mermaid
flowchart LR
  User["Plant user: technician, manager, safety, admin"] --> Frontend["Next.js role-aware demo UI"]
  Frontend --> API["FastAPI backend"]

  API --> Ingest["Ingestion router"]
  API --> Query["Query router"]
  API --> GraphAPI["Graph router"]
  API --> Compliance["Compliance router"]
  API --> Voice["Voice router"]
  API --> Patterns["Risk and pattern router"]

  Ingest --> Parser["File parsing and OCR"]
  Parser --> TextChunks["Chunked text with metadata"]
  Parser --> Multimodal["Gemini multimodal structured extraction"]
  Multimodal --> Schema["Strict JSON schemas: P&ID, maintenance log"]
  Schema --> Confidence["Confidence and uncertainty rules"]

  TextChunks --> Vector["Vector store retrieval"]
  Schema --> Neo4j["Neo4j knowledge graph"]
  Confidence --> Review["PendingReview queue"]

  Query --> Vector
  Query --> Neo4j
  Query --> LLM["LLM answer synthesis"]
  LLM --> Answer["Cited answer with confidence and caveats"]

  Compliance --> Rules["OISD, Factory Act, PESO rule base"]
  Rules --> Neo4j
  Compliance --> Evidence["Gap findings and audit evidence"]

  Voice --> Knowledge["Expert field knowledge capture"]
  Knowledge --> TextChunks
  Knowledge --> Neo4j

  Patterns --> Risk["Failure patterns and risk signals"]
  Risk --> Frontend
  Answer --> Frontend
  Evidence --> Frontend
  Review --> Frontend
```

## Data Flow

1. A user uploads or selects a document.
2. The backend detects file type, parses text, performs OCR when needed, and chunks the content.
3. If the document is visual or structured, Gemini multimodal extraction runs with strict JSON schema output.
4. Extracted entities and relationships are written to Neo4j using idempotent MERGE-style graph operations.
5. Low-confidence extractions are routed to PendingReview instead of polluting the trusted graph.
6. User questions retrieve vector chunks and graph context.
7. The answer layer returns citations, confidence, source freshness, and operational cards.

## Scalability Story

- Routers are separated by capability: ingest, query, graph, compliance, risk, voice, admin.
- Services are separated by responsibility: parsing, embeddings, LLM, Neo4j, compliance, patterns, voice.
- Graph writes are idempotent, so reprocessing corrected scans should update nodes instead of duplicating them.
- Neo4j is optional but preferred for full graph intelligence; local graph fallback keeps demos resilient.
- Confidence gating creates a human-in-the-loop path for messy industrial documents.

## Slide-Friendly One-Liner

PlantBrain turns messy industrial records into a living knowledge graph and answers operational questions with citations, confidence, and compliance context.
