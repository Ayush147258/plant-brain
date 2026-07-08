# Presentation Deck Outline

Target: 8 to 10 slides. Keep it judge-focused and evidence-driven.

## Slide 1 - Title

PlantBrain: Industrial Knowledge Intelligence

Subtitle: From fragmented plant documents to source-cited operational answers.

Show: hero screenshot or role workspace screenshot.

## Slide 2 - Problem

Use the challenge-brief numbers:

- 35% of work time lost to searching, clarifying, or recreating information.
- 7-12 disconnected document systems per large plant.
- 18-22% downtime contribution from fragmented knowledge.
- 25% experienced workforce retirement cliff.

Message: this is a safety, quality, compliance, and downtime problem, not a file-management problem.

## Slide 3 - Solution

PlantBrain ingests documents, extracts industrial entities, builds a knowledge graph, and answers questions with citations and confidence.

Show: one screenshot of landing/demo workflow.

## Slide 4 - Architecture

Use the Mermaid diagram from `architecture.md`.

Explain:

- Parsing/OCR.
- Multimodal structured extraction.
- Vector retrieval.
- Neo4j graph.
- Compliance/risk services.
- Pending review for low confidence.

## Slide 5 - Demo Workflow

Show the actual workflow:

1. Select role.
2. Upload document.
3. Watch pipeline.
4. Inspect graph.
5. Ask with citations.
6. Run compliance.
7. Review risk/stale source warnings.

## Slide 6 - Technical Differentiation

Highlight:

- Multimodal extraction for P&IDs and scanned logs.
- Strict JSON schema outputs.
- Idempotent graph writes.
- Graph-RAG context.
- Confidence-gated PendingReview.
- Role-aware UX.

## Slide 7 - Benchmark Results

Fill from `benchmark_results_template.csv`.

Minimum chart:

- Manual search time vs PlantBrain time for 5 questions.
- Answer quality score out of 10.
- Citation coverage count.

If benchmark is not complete, mark this slide as "pilot benchmark design" rather than claiming results.

## Slide 8 - Business Impact

Map features to impact:

- Faster answers -> less wasted work time.
- Graph context -> fewer incomplete maintenance decisions.
- Compliance checks -> earlier gap detection.
- Expert capture -> preserves retiring knowledge.
- Confidence caveats -> safer use of AI in industrial workflows.

## Slide 9 - Scalability And Deployment

Show:

- FastAPI backend.
- Next.js frontend.
- Neo4j graph.
- Vector store.
- Hugging Face/Vercel deployment path.
- Modular services.

## Slide 10 - Closing

One sentence:

"PlantBrain gives every plant worker a trusted, source-cited answer layer over the knowledge their plant already has."

End with demo link, GitHub link, and team contact.
