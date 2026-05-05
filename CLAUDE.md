# Project: graphrag_vs_vectorrag

## Identity

GraphRAG vs VectorRAG comparison on synthetic financial compliance docs (NordFinance Group).
Thesis: GraphRAG +25–40% RAG Triad on multi-hop queries; −10–15% on single-hop due to noisy
entity extraction from a 1.5B model. All inference local via Ollama. No data leaves the machine.

## Stack

- Python 3.11 · httpx · neo4j driver · chromadb · numpy · networkx · streamlit · loguru
- Ollama models: `qwen2.5:1.5b` (generation + entity extraction + RAG Triad judge),
  `nomic-embed-text` (768-dim embeddings)
- Neo4j Community 5.x via Docker (heap=1g, pagecache=256m) — bolt://localhost:7687
- ChromaDB persistent in-process, `embedding_function=None`
- Deps: `uv` + `pyproject.toml`. Never use `pip`.
- Constraint: 2-CPU / 8 GB RAM GitHub Codespace. Sequential pipeline only.
- **Excluded:** LangChain, LlamaIndex, Haystack, RAGAS, torch, tensorflow, openai, tiktoken

## Repository Structure

```
config/           settings.yaml (Pydantic Settings)
src/corpus/       generator.py, schemas.py
src/ingestion/    chunker, embedder, vector_store, entity_extractor, graph_store
src/retrieval/    vector_retriever, graph_retriever, hybrid_retriever, prompt_builder
src/generation/   generator.py
src/evaluation/   rag_triad.py, question_bank.py, comparison.py
src/              config.py, network_guard.py, visualisation.py
app/              streamlit_app.py
tests/unit/       no Ollama/Neo4j needed (mocked)
tests/integration/ requires Ollama + Neo4j
notebooks/        01–06 (EDA → vector → extraction → graph → eval → failure modes)
```

## Key Design Rules

- All LLM/embedding calls: `httpx.post` to `localhost:11434` (Ollama) — never subprocess
- All graph calls: `neo4j` Python driver to `bolt://localhost:7687`
- `NetworkGuard` in `src/network_guard.py`: reject any non-localhost URL before request
- Entity extraction: structured JSON output from `qwen2.5:1.5b` with typed schema
  (Company | Person | AuditFirm | Regulator | RiskFactor | FinancialMetric | Report)
- Entity dedup: normalised string match + Levenshtein ≤ 2 before Neo4j upsert
- Context budget: 2048-token hard cap for `qwen2.5:1.5b`
- RAG Triad: self-evaluated via `qwen2.5:1.5b` — context relevance, groundedness,
  answer relevance — scored 0.0–1.0, aggregated as geometric mean
- Graph retrieval: max 10 Cypher triples per query, graph context merged before vector chunks
- `make ingest` is idempotent (ChromaDB SHA256 IDs, Neo4j MERGE)

## Makefile Commands

```
make setup        uv + ollama + pull models + kernel install (one-time, needs internet)
make sync         uv sync from lockfile (fast, after git pull)
make neo4j-up     start Neo4j Docker container
make neo4j-down   stop Neo4j
make generate     generate 12 NordFinance synthetic docs → data/corpus/
make ingest       ChromaDB ingest + entity extraction + Neo4j graph load
make pipeline     generate + ingest
make eval         RAG Triad evaluation on both pipelines → data/eval/
make smoke        3-doc / 1-question quick sanity check
make lint         ruff format + ruff check --fix + ty check + bandit (must pass before commit)
make format       ruff format only
make check        ruff check --fix + bandit
make typecheck    ty check src/
make test-unit    pytest tests/unit/ (no external services)
make test-integ   pytest tests/integration/ (requires Ollama + Neo4j)
make dev          lint + test-unit (fast offline loop)
make ci           sync → lint → test-unit → audit-network → audit-deps
make audit-network assert no non-localhost URLs in src/
make audit-deps   assert no GPU packages installed
make run          streamlit run app/streamlit_app.py --server.port 8501
make lab          jupyterlab --no-browser --port 8888
make clean        remove data/, caches, notebook outputs
make reset        clean + neo4j-down + rm .venv
```

## Conventions

- Docstrings: Google style, one-line summary only
- Commits: Conventional Commits format, subject ≤ 50 chars
- All code must pass `make lint` before commit
- `src/config.py`: Pydantic Settings loading from `config/settings.yaml`
- No comments unless the WHY is non-obvious; never comment what the code does

## Evaluation: Question Bank

30 questions — 15 single-hop ("What is NordBank's Tier 1 capital ratio?"),
15 multi-hop ("Which officers serve on boards of companies sharing the same auditor?").
Each question has `type`, `gold_answer`, `required_entities`, `required_relationships`.

## Token Rules (Caveman Mode ON)

- Code-first; explain only when asked
- No restatements of the question
- Use `/compact` at each notebook boundary
- Short responses; skip preamble and summaries
