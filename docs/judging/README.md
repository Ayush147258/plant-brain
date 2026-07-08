# PlantBrain Judging Pack

This folder turns the PlantBrain prototype into a judge-ready submission package. Use it with the live app, the presentation deck, and the demo video.

## Submission Positioning

PlantBrain is an Industrial Knowledge Intelligence platform. It is not just file search. It converts fragmented plant documents into a queryable, confidence-aware knowledge layer made of:

- Universal document ingestion for PDFs, scans, spreadsheets, logs, emails, and drawings.
- Multimodal structured extraction for P&IDs and maintenance logs.
- Vector search plus graph context for source-cited answers.
- Neo4j knowledge graph writes for equipment, valves, instruments, events, compliance rules, and review items.
- Role-aware user experience for technicians, managers, maintenance, stores, plant heads, and admins.
- Confidence gating so low-confidence extraction goes to review instead of polluting the real graph.

## Judging Alignment Snapshot

| Criterion | Weight | PlantBrain Evidence | Current Rating |
|---|---:|---|---:|
| Innovation | 25% | Multimodal extraction, Graph-RAG, confidence-gated graph writes, knowledge decay, role workspaces. | Strong |
| Business Impact | 25% | Targets search-time loss, downtime, compliance risk, knowledge retirement, and cross-functional discovery. | Strong |
| Technical Excellence | 20% | FastAPI backend, ingestion pipeline, vector store, Neo4j service, compliance/risk/voice modules, working frontend. | Strong, prove with tests/demo |
| Scalability | 15% | Modular routers/services, idempotent graph writes, async task pipeline, configurable deployment. | Good, improve with architecture slide |
| User Experience | 15% | Premium landing, role selection, collapsible demo sidebar, guided workflow panels. | Strong |

## Files In This Pack

- `architecture.md` - architecture diagram and data flow for deck/demo.
- `demo_video_script.md` - 5 minute recording script and shot list.
- `sample_document_collection_guide.md` - what real/sample documents the user should collect.
- `benchmark_questions.md` - judge-style domain questions and expected pass criteria.
- `benchmark_results_template.csv` - fill this while testing time-to-answer and answer quality.
- `claims_and_sources.md` - claim hygiene checklist so pitch/deck claims stay defensible.

## Recommended Demo Narrative

1. Select a workspace role.
2. Upload a real plant document or demo OSHA/safety PDF.
3. Show live ingestion stages and chunking.
4. Show graph nodes and relationships.
5. Ask a source-cited operational question.
6. Run a compliance check.
7. Show confidence/freshness/review caveats.
8. Close with quantified impact: faster answers, fewer fragmented searches, safer decisions.

## Minimum Before Submission

- Frontend build passes.
- Backend tests pass or known failing tests are documented.
- Demo video recorded from a stable local or deployed app.
- At least 5 benchmark questions answered with screenshots.
- At least 3 different document types shown in the demo or appendix.
- Architecture slide included.
- Claims in the deck cite either the official challenge brief or source URLs/PDFs.
