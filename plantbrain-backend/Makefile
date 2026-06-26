.PHONY: setup run test seed verify verify-prod clean lint

setup:
	bash run_local.sh

run:
	source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	source venv/bin/activate && pytest tests/ -v

seed:
	source venv/bin/activate && python seed_demo_data.py

verify:
	source venv/bin/activate && python verify_deployment.py http://localhost:8000

verify-prod:
	python verify_deployment.py $(URL)

clean:
	rm -rf data/uploads/* data/chroma_db/* data/graph/*.pkl data/*.db __pycache__ .pytest_cache

lint:
	pip install ruff -q && ruff check app/ --fix
