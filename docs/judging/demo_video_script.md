# Demo Video Script

Target length: 4 to 5 minutes.
Recommended recording: 1920x1080, browser zoom 90-100%, no notifications, clear terminal windows.

## Setup Before Recording

1. Start the backend.
2. Start the frontend.
3. Confirm `/demo` loads.
4. Confirm at least one demo document or real sample is ready.
5. Confirm API docs load.
6. Confirm graph/compliance panels do not show blocking errors.
7. Keep this script visible on a second screen.

## Shot List

### 0:00 - 0:25 - Problem

Show landing hero.

Narration:

"Industrial plants do not lack documents. They lack connected, trusted answers. P&IDs, maintenance logs, safety procedures, inspection reports, and compliance records sit across disconnected systems. PlantBrain turns that fragmented knowledge into an operational intelligence layer."

### 0:25 - 0:55 - Role Workspace

Open `/demo`, show role selection.
Choose `Technician` or `Manager`.

Narration:

"The experience is role-aware. A technician, maintenance manager, plant head, stores team, or admin sees the workflow most relevant to their job. This matters because the point of need is different for every function."

### 0:55 - 1:40 - Ingest A Document

Open Connect Documents.
Upload a sample plant file or use the official demo PDF.
Show filename, document ID, processing status, chunk count.

Narration:

"PlantBrain ingests heterogeneous documents and preserves the source trail. The same pipeline can parse text, OCR scans, and run structured extraction for visual or industrial documents."

If Gemini is temporarily unavailable:

"The system degrades safely. Text indexing and citations continue, while structured graph enrichment can be retried later."

### 1:40 - 2:20 - Knowledge Graph

Open Knowledge Graph panel.
Show equipment/relationships/stats.

Narration:

"Extracted equipment, events, compliance rules, and relationships become graph context. This is what lets PlantBrain answer relationship questions that keyword search cannot answer."

### 2:20 - 3:10 - Ask With Citations

Open Ask PlantBrain.
Use one benchmark question:

"Show equipment connected to P-201 and cite the source."

Or if using safety document only:

"Summarize the lockout/tagout procedure and cite the source."

Show confidence badge, citations, source cards, caveats.

Narration:

"Every answer is evidence-aware. It includes source citations, confidence, and caveats when the evidence is incomplete. Low confidence is not hidden from the user."

### 3:10 - 3:45 - Compliance Intelligence

Open Compliance.
Paste or select procedure text.
Run against OISD/Factory Act/PESO style rules.
Show compliant/partial/non-compliant results.

Narration:

"PlantBrain also supports compliance intelligence. It compares procedures against rule requirements and surfaces gaps before an audit or incident."

### 3:45 - 4:20 - Risk, Decay, and Expert Knowledge

Show risk patterns, voice capture, or landing knowledge decay section.

Narration:

"The platform also captures expert knowledge, detects recurring patterns, and warns when stale documents should not be blindly trusted. This addresses the knowledge retirement cliff directly."

### 4:20 - 5:00 - Architecture and Impact Close

Show architecture slide or `docs/judging/architecture.md` diagram.

Narration:

"Technically, PlantBrain combines document intelligence, multimodal extraction, vector retrieval, knowledge graphs, compliance rules, and human review. The result is faster time-to-answer, better cross-functional discovery, and safer plant decisions."

## What To Capture As Proof

- Role selection screen.
- Successful document ingestion status.
- Source-cited answer.
- Graph context or graph stats.
- Compliance check result.
- At least one confidence or stale-source caveat.

## Avoid In The Video

- Do not show API keys or secrets.
- Do not show private plant names unless approved.
- Do not claim exact benchmark numbers unless your `benchmark_results_template.csv` is filled.
- Do not ignore low-confidence warnings. Use them as a strength.
