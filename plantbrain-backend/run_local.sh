#!/bin/bash
# PlantBrain Local Development Quick Start

set -e

echo "=== PlantBrain Backend Local Setup ==="
echo ""

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d " " -f 2 | cut -d "." -f 1,2)
echo "Python version: $PYTHON_VERSION"
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"; then
  echo "✓ Python 3.10+ detected"
else
  echo "✗ Python 3.10+ required. Please upgrade."
  exit 1
fi

if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi
source venv/bin/activate
echo "✓ Virtual environment activated"

echo ""
echo "Installing dependencies (this may take 5-10 minutes first time)..."
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

if [ ! -f ".env" ]; then
  cp .env.example .env
  echo ""
  echo "⚠️  .env file created from .env.example"
  echo "    Please set your GEMINI_API_KEY in .env before continuing."
  echo "    Then re-run this script."
  exit 0
fi
echo "✓ .env file found"

mkdir -p data/uploads data/chroma_db data/graph
echo "✓ Data directories created"

if grep -q "GEMINI_API_KEY=your_key_here" .env || ! grep -q "^GEMINI_API_KEY=" .env; then
  echo ""
  echo "✗ GEMINI_API_KEY is not set in .env"
  echo "  Get your key from https://aistudio.google.com/app/apikey"
  echo "  Set it in .env: GEMINI_API_KEY=your_key_here"
  exit 1
fi
echo "✓ GEMINI_API_KEY is set"

if command -v tesseract &> /dev/null; then
  echo "✓ Tesseract OCR available"
else
  echo "⚠️  Tesseract OCR not found. Image/scanned PDF OCR will not work."
  echo "   Install: sudo apt-get install tesseract-ocr (Ubuntu) or brew install tesseract (Mac)"
fi

echo ""
echo "Starting PlantBrain backend..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
SERVER_PID=$!

cleanup() {
  echo ""
  echo "Stopping PlantBrain backend..."
  kill "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT

echo "Waiting for server to start..."
for i in {1..30}; do
  if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✓ Server is running at http://localhost:8000"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "✗ Server did not start within 30 seconds"
    exit 1
  fi
  sleep 1
done

echo ""
echo "Seeding demo data..."
python seed_demo_data.py || echo "⚠️  Seeding failed (check if GEMINI_API_KEY is valid)"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "API:  http://localhost:8000"
echo "Docs: http://localhost:8000/docs"
echo ""
echo "Run verification: python verify_deployment.py http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
wait "$SERVER_PID"
