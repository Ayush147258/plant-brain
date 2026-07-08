# Verification Report

Last verified in this workspace after resolving conflicts and adding judge assets.

## Frontend

Command:

```powershell
npm run build
```

Working directory:

```text
frontend
```

Result:

```text
PASS
Compiled successfully
Static pages generated: 5/5
Routes: /, /_not-found, /demo
```

## Backend

Command:

```powershell
.\venv\Scripts\python.exe -m pytest tests -q --basetemp .\.pytest-tmp
```

Working directory:

```text
plantbrain-backend
```

Result:

```text
42 passed, 5 skipped, 1 warning in 167.64s
```

Warning:

```text
pytest_asyncio deprecation warning: custom event_loop fixture in tests/conftest.py.
```

This warning does not fail the suite, but should be cleaned later by moving to pytest-asyncio's supported loop-scope configuration.

## Conflict Status

The previous unresolved files were fixed:

- README.md
- plantbrain-backend/app/services/ingestion_service.py

The ingestion service keeps the safer behavior: if Gemini structured extraction is temporarily unavailable, PlantBrain continues indexing parsed text and citations instead of failing the whole ingestion job.
