.PHONY: help setup sync lint format check typecheck test-unit test-integ \
        generate ingest eval compare run lab clean reset ci dev \
        neo4j-up neo4j-down audit-network audit-deps smoke pipeline

# ─── Meta ────────────────────────────────────────────────────────
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# ─── Environment ─────────────────────────────────────────────────
setup: ## First-time setup: install uv, Ollama, pull models, sync deps
	@command -v uv >/dev/null 2>&1 || curl -LsSf https://astral.sh/uv/install.sh | sh
	@command -v ollama >/dev/null 2>&1 || curl -fsSL https://ollama.com/install.sh | sh
	@pgrep -x ollama >/dev/null 2>&1 || (ollama serve &>/dev/null & sleep 3)
	uv sync --all-extras
	ollama pull nomic-embed-text
	ollama pull qwen2.5:1.5b
	uv run python -m ipykernel install --user --name graphrag
	@echo "\nReady. Run 'make neo4j-up && make smoke' to verify."

sync: ## Sync deps from lockfile (fast, after git pull)
	uv sync --all-extras

# ─── Neo4j ───────────────────────────────────────────────────────
neo4j-up: ## Start Neo4j container
	docker compose -f .devcontainer/docker-compose.yml up -d neo4j
	@echo "Waiting for Neo4j..." && sleep 15
	@echo "Neo4j ready at bolt://localhost:7687 (browser: http://localhost:7474)"

neo4j-down: ## Stop Neo4j container
	docker compose -f .devcontainer/docker-compose.yml down neo4j

# ─── Data Pipeline ───────────────────────────────────────────────
generate: ## Generate synthetic NordFinance corpus
	uv run python -m src.corpus.generator
	@echo "Corpus generated in data/corpus/"

ingest: ## Ingest into ChromaDB + extract entities + load Neo4j graph
	uv run python -m src.ingestion.vector_store
	uv run python -m src.ingestion.entity_extractor
	uv run python -m src.ingestion.graph_store
	@echo "Vector store + knowledge graph populated."

pipeline: generate ingest ## Full data pipeline: generate + ingest

# ─── Evaluation ──────────────────────────────────────────────────
eval: ## Run RAG Triad evaluation on both pipelines
	uv run python -m src.evaluation.comparison
	@echo "Results in data/eval/"

compare: eval ## Alias for eval

smoke: ## Quick end-to-end smoke test (3 docs, 1 question each pipeline)
	uv run python -m src.evaluation.comparison --smoke
	@echo "Smoke test passed."

# ─── Code Quality ────────────────────────────────────────────────
lint: format check typecheck ## Run all linters: format + check + typecheck + bandit

format: ## Auto-format code with ruff
	uv run ruff format src/ tests/ app/

check: ## Lint and auto-fix with ruff + bandit security scan
	uv run ruff check --fix src/ tests/ app/
	uv run bandit -r src/ -ll -q

typecheck: ## Type-check with ty
	uv run ty check src/

# ─── Testing ─────────────────────────────────────────────────────
test-unit: ## Run unit tests (no Ollama or Neo4j required)
	uv run pytest tests/unit/

test-integ: ## Run integration tests (requires Ollama + Neo4j)
	uv run pytest tests/integration/

test: test-unit ## Default test target (unit only)

# ─── Audits ──────────────────────────────────────────────────────
audit-network: ## Assert no non-loopback connections in source
	@! grep -rn 'https\?://' src/ --include='*.py' \
		| grep -v 'localhost' | grep -v '127.0.0.1' \
		| grep -v '#' | grep -v 'docstring' \
		&& echo "Network audit passed." \
		|| (echo "Non-localhost URL found in source." && exit 1)

audit-deps: ## Fail if any GPU/CUDA package detected
	@! uv pip list 2>/dev/null | grep -iE 'torch|tensorflow|onnxruntime-gpu|nvidia' \
		&& echo "No GPU packages." \
		|| (echo "GPU package detected." && exit 1)

# ─── Run ─────────────────────────────────────────────────────────
run: ## Launch Streamlit app
	uv run streamlit run app/streamlit_app.py --server.port 8501

lab: ## Launch JupyterLab
	uv run jupyter lab --no-browser --port 8888

# ─── Cleanup ─────────────────────────────────────────────────────
clean: ## Remove data, caches, notebook outputs
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf data/corpus/ data/chroma/ data/eval/ .mypy_cache htmlcov .coverage
	@echo "Cleaned."

reset: clean neo4j-down ## Full reset: clean + stop Neo4j + remove venv
	rm -rf .venv
	@echo "Reset. Run 'make setup' to rebuild."

# ─── CI (GitHub Actions — unit tests only, no Ollama/Neo4j) ─────
ci: sync lint test-unit audit-network audit-deps ## CI pipeline

# ─── Dev ─────────────────────────────────────────────────────────
dev: lint test-unit ## Fast offline dev loop
