# Benchmark Questions

Use these questions to prove query answer quality, graph linkage completeness, compliance gap detection, and time-to-answer improvement.

Scoring suggestion per question:

- 2 points: correct answer.
- 2 points: cites the right source document/page/chunk.
- 2 points: uses graph/context when relevant.
- 2 points: confidence/caveat is appropriate.
- 2 points: answer is actionable for the role.

Total: 10 points per question.

## Core Demo Questions

| ID | Category | Question | Required Evidence | Pass Criteria |
|---|---|---|---|---|
| Q01 | Search replacement | Summarize the lockout/tagout steps for the uploaded procedure. | Safety procedure | Answer lists steps and cites source. |
| Q02 | Source citation | Which source did you use for the answer, and what page/chunk supports it? | Any indexed doc | Returns citation metadata or warns no citation exists. |
| Q03 | P&ID graph | Identify equipment connected to P-201 in Zone 3. | P&ID or synthetic drawing | Returns equipment IDs and connection caveats. |
| Q04 | Valve connectivity | Which valves connect P-201 and HX-204? | P&ID | Returns valve IDs or says not visible. No guessing. |
| Q05 | Maintenance history | What failures happened on asset P-201? | Maintenance log | Returns dated events and failure modes. |
| Q06 | RCA support | What is the most likely recurring failure pattern for P-201? | Work orders and logs | Links repeated failure modes with evidence. |
| Q07 | Compliance | Does this procedure satisfy OISD/Factory Act/PESO style requirements? | Rule excerpt plus procedure | Produces compliant/partial/non-compliant findings. |
| Q08 | Audit evidence | Generate an evidence pack for the compliance check. | Compliance output and source docs | Lists rule, finding, evidence, recommendation. |
| Q09 | Knowledge decay | Which sources look stale or low-confidence? | Docs with dates/confidence | Flags stale/uncertain docs instead of hiding caveats. |
| Q10 | Human review | What should be routed to manual review? | Low-confidence extraction | Low-confidence items do not become trusted graph facts. |
| Q11 | Role UX | As a technician, what should I do next? | Any answer | Actionable field-level next steps. |
| Q12 | Manager UX | As a manager, what risk needs attention first? | Risk/compliance data | Prioritized business/operations view. |
| Q13 | Cross-functional | Which equipment has maintenance, compliance, and inspection evidence? | Graph plus docs | Combines multiple document types. |
| Q14 | Missing info | What information is missing before approving this work? | Procedure or work order | Identifies gaps, does not fabricate. |
| Q15 | Time-to-answer | How long did PlantBrain take vs manual search? | Stopwatch result | Measured result recorded in CSV. |

## Good Demo Prompts

- "Show equipment connected to P-201 and cite the source."
- "Check if this procedure has stale or low-confidence sources."
- "Generate a source-cited work pack for the most relevant equipment in the uploaded documents."
- "Check compliance caveats and cite rules from the uploaded documents."
- "Identify stale, low-confidence, or missing-source information before answering."

## What Judges Should See

- The answer is not just fluent; it is traceable.
- The graph is not just visual; it changes what the system can answer.
- The system knows when it is uncertain.
- The workflow helps different plant roles, not only data scientists.
