.PHONY: install up down api ui seed ingest eval test lint

install:
	pip install -r requirements.txt

up:
	docker compose up -d

down:
	docker compose down

api:
	uvicorn app.main:app --reload --port 8000

ui:
	streamlit run ui/streamlit_app.py

seed:
	python scripts/seed_db.py

ingest:
	python scripts/ingest_docs.py

eval:
	python -m evaluation.run_eval

test:
	pytest -q

lint:
	ruff check app evaluation tests
