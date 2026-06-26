#!/bin/bash
mkdir -p data/uploads data/chroma_db data/graph
echo "Data directories created"
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --log-level info
