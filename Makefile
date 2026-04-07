# Makefile — AI Research Paper Summarizer
# Common development commands

.PHONY: install run test clean lint

## Install all dependencies
install:
	pip install -r requirements.txt

## Run the Streamlit app
run:
	streamlit run app.py

## Run all unit tests
test:
	python -m pytest tests/ -v

## Run a single test module (usage: make test-module MOD=test_query)
test-module:
	python -m pytest tests/$(MOD).py -v

## Quick smoke test: query enhancement only (no Groq key needed for imports)
smoke:
	python -c "from models.paper_schema import PaperSummary; print('Schema OK:', len(PaperSummary.model_fields), 'fields')"
	python -c "from arxiv.search import ArxivPaper; print('ArxivPaper OK')"
	python -c "from export.to_csv import summaries_to_dataframe; print('Export CSV OK')"
	python -c "from export.to_markdown import summaries_to_markdown_string; print('Export MD OK')"
	python -c "from utils.validators import validate_query; print('Validators OK')"
	python -c "from config import LLM_PROVIDER, APP_TITLE; print(f'Config OK: {APP_TITLE} / {LLM_PROVIDER}')"
	@echo "All smoke tests passed ✅"

## Test arXiv connection (no API key needed)
test-arxiv:
	python tests/test_arxiv.py

## Clear LLM cache
clear-cache:
	rm -f cache/llm_cache.db
	@echo "Cache cleared."

## Remove all exported files
clean-exports:
	rm -f exports/*
	@echo "Exports cleared."

## Full clean
clean: clear-cache clean-exports
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete
	@echo "Clean done."

## Show current config
config:
	python -c "import config; print('Provider:', config.LLM_PROVIDER); print('Model:', config.LLM_MODEL_STRONG); print('Cache:', config.ENABLE_CACHE)"
