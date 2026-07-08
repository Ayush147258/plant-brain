# Sample Document Collection Guide

The strongest submission uses real or realistic industrial documents. If real documents are sensitive, anonymize or synthesize them while preserving structure.

## Minimum Judge-Ready Sample Pack

Collect at least one document from each group:

1. P&ID or engineering drawing
   - Format: PDF, scanned image, TIFF, or DXF.
   - Include visible tags such as P-201, V-12, HX-204, PT-101.
   - Best demo question: "Which valves connect P-201 to HX-204?"

2. Maintenance work order or log
   - Format: PDF, spreadsheet, scanned form, or handwritten image.
   - Include asset ID, failure mode, date, action taken, technician notes.
   - Best demo question: "What failures happened on P-201 in the last year?"

3. Safety procedure
   - Format: PDF/DOCX/TXT.
   - Include lockout/tagout, confined space, hot work, or permit procedure.
   - Best demo question: "What are the mandatory steps before this work starts?"

4. Inspection report
   - Format: PDF, scan, spreadsheet, or email.
   - Include equipment condition, readings, findings, recommendations.
   - Best demo question: "Which inspection findings indicate rising risk?"

5. Compliance rule or standard excerpt
   - Format: PDF/TXT.
   - Use OISD, Factory Act, PESO, environmental, or internal quality standard text.
   - Best demo question: "Does this procedure satisfy the rule?"

6. Email or project note
   - Format: EML/MSG/TXT/PDF.
   - Include a decision, approval, repair note, or exception.
   - Best demo question: "Who approved the temporary change and when?"

## Anonymization Checklist

Before uploading or recording:

- Replace company name with `Demo Plant`.
- Replace real person names with roles such as `Technician A`.
- Replace phone numbers, emails, and addresses.
- Keep equipment tags realistic but fake if needed: P-201, HX-204, V-12.
- Remove GPS coordinates and client names.
- Keep document dates realistic so knowledge-decay scoring can be demonstrated.
- Do not show proprietary process chemistry or trade secrets.

## Synthetic Sample Strategy

If real documents are not available, create a small synthetic pack:

- One simple P&ID-style PDF with 5 equipment tags and 4 valves.
- One maintenance log spreadsheet with 8 events.
- One safety procedure document with 10 steps.
- One inspection report with 5 findings.
- One compliance rule excerpt with 3 requirements.

The key is not document size. The key is that the expected answers are known so accuracy can be scored.

## Expected Submission Evidence

For each sample document, capture:

- Filename.
- Format.
- Document type.
- What entities should be extracted.
- 2 benchmark questions.
- Expected answer.
- Screenshot of PlantBrain output.
- Pass/fail notes.
