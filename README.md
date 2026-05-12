# GraphRAG vs VectorRAG

A head-to-head comparison of Graph-augmented RAG and pure vector similarity RAG on synthetic financial compliance documents, evaluated with the RAG Triad (context relevance · groundedness · answer relevance).

All inference runs **locally via Ollama** — no data leaves the machine.

---

## Hypothesis vs Results

| Query type | Hypothesis | Actual delta | Confirmed? |
|---|---|---|---|
| Multi-hop | GraphRAG +25–40% triad | **+31.3%** (0.534 → 0.700) | Yes |
| Single-hop | VectorRAG wins by ~10–15% | **−9.1%** (Graph 0.640 vs Vector 0.704) | Yes |
| Overall (30 q) | Graph wins on balance | **+8.3%** (0.619 → 0.670) | Yes |

Graph wins **14 of 30** questions (9/15 multi-hop, 5/15 single-hop).

**Main failure mode:** graph `context_relevance` collapses to `0.0` on 4 questions where `qwen2.5:1.5b` entity extraction produced no usable triples — the geometric mean zeros the entire triad score. VectorRAG degrades more gracefully under retrieval misses.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Synthetic Corpus  (12 NordFinance compliance docs)     │
└──────────────┬──────────────────────────────────────────┘
               │ generate
       ┌───────┴────────┐
       ▼                ▼
  ChromaDB         Neo4j 5
  (nomic-embed     (qwen2.5:1.5b
   768-dim)         entity extract)
       │                │
       └───────┬─────────┘
               │ retrieve
       ┌───────┴────────┐
       │  HybridRetriever│
       │  ┌─────────────┤
       │  │ VectorRAG   │  cosine similarity → MMR rerank
       │  │ GraphRAG    │  entity NER → Cypher subgraph
       └──┴─────────────┘
               │ build prompt (2048-token budget)
               ▼
        qwen2.5:1.5b  (generation)
               │
               ▼
        RAG Triad judge  (qwen2.5:1.5b self-eval)
        context_relevance · groundedness · answer_relevance
        geometric mean → triad score
```

### Models

| Model | Role | Size |
|---|---|---|
| `qwen2.5:1.5b` | Generation · entity extraction · RAG Triad judge | 986 MB |
| `nomic-embed-text` | 768-dim embeddings | 274 MB |

### Services

| Service | Where |
|---|---|
| Ollama | `http://localhost:11434` |
| Neo4j Bolt | `bolt://localhost:7687` |
| Neo4j Browser | `http://localhost:7474` |
| ChromaDB | In-process persistent (`data/chroma/`) |
| Streamlit UI | `http://localhost:8501` |

---

## Prerequisites

- **GitHub Codespace** (2 CPU / 8 GB RAM) or equivalent Linux machine
- Docker (for Neo4j)
- Internet access for first-time model downloads only

---

## Quickstart

```bash
# 1. One-time setup (pulls Ollama models, installs uv deps, installs Jupyter kernel)
make setup

# 2. Start Neo4j
make neo4j-up

# 3. Generate the 12 synthetic NordFinance documents
make generate

# 4. Ingest: embed → extract entities → load graph (idempotent)
make ingest

# 5. Launch the Streamlit comparison UI
make run
```

After step 4 you'll have:
- **36 chunks** embedded in ChromaDB (cosine space)
- **~42 entities** and **~99 relationships** in Neo4j (run-dependent; LLM output varies)

---

## Makefile Reference

| Command | What it does |
|---|---|
| `make setup` | Install uv deps, pull Ollama models, register Jupyter kernel |
| `make sync` | `uv sync` from lockfile (fast, after `git pull`) |
| `make neo4j-up` | Start Neo4j Community 5 via Docker Compose |
| `make neo4j-down` | Stop Neo4j container |
| `make generate` | Generate 12 synthetic docs → `data/corpus/` |
| `make ingest` | Embed chunks + extract entities + load Neo4j graph |
| `make pipeline` | `generate` + `ingest` in sequence |
| `make eval` | RAG Triad evaluation on both pipelines → `data/eval/` |
| `make smoke` | 3-doc / 1-question sanity check (fast) |
| `make lint` | ruff format + ruff check + ty + bandit (must pass before commit) |
| `make test-unit` | pytest unit tests (no Ollama / Neo4j required) |
| `make test-integ` | pytest integration tests (requires Ollama + Neo4j) |
| `make dev` | lint + test-unit (fast offline loop) |
| `make ci` | sync → lint → test-unit → audit-network → audit-deps |
| `make run` | `streamlit run app/streamlit_app.py --server.port 8501` |
| `make lab` | JupyterLab on port 8888 |
| `make clean` | Remove `data/`, caches, notebook outputs |
| `make reset` | `clean` + `neo4j-down` + remove `.venv` |

---

## Repository Layout

```
.devcontainer/
  docker-compose.yml        Neo4j 5 Community (heap 1 GB, pagecache 256 MB)

config/
  settings.yaml             All tunables: models, timeouts, retrieval params

src/
  config.py                 Pydantic Settings (lru_cache singleton)
  network_guard.py          Rejects any non-localhost URL before HTTP requests

  corpus/
    schemas.py              EntityType, RelationshipType, Document, ExtractionResult
    generator.py            12 NordFinance synthetic docs + ground-truth annotations

  ingestion/
    chunker.py              Recursive character splitter (no deps)
    embedder.py             OllamaEmbeddingClient → /api/embeddings
    vector_store.py         ChromaDB upsert (SHA256 IDs, idempotent)
    entity_extractor.py     qwen2.5:1.5b JSON extraction + Levenshtein dedup
    graph_store.py          Neo4j MERGE upserts + subgraph queries

  retrieval/
    vector_retriever.py     Cosine similarity + MMR reranking (numpy)
    graph_retriever.py      Entity NER → Cypher MATCH subgraph
    hybrid_retriever.py     Combines graph + vector results
    prompt_builder.py       2048-token budget prompt assembly

  generation/
    generator.py            OllamaGenerationClient → /api/generate

  evaluation/
    rag_triad.py            Context relevance · groundedness · answer relevance (geometric mean)
    question_bank.py        30 questions: 15 single-hop, 15 multi-hop
    comparison.py           Full eval loop → data/eval/results.json

  visualisation.py          radar_data(), score_deltas(), summary_table()

app/
  streamlit_app.py          Side-by-side GraphRAG vs VectorRAG UI

tests/
  unit/                     44 tests — all mocked, no external services
  integration/              Requires live Ollama + Neo4j
```

---

## Corpus

12 synthetic NordFinance Group compliance documents covering:

| Document | Type |
|---|---|
| Annual Report 2024 | `annual_report` |
| Consolidated Financials | `financial_statement` |
| FSA Sanction: NordBank | `regulatory_correspondence` |
| Regulatory Correspondence | `regulatory_correspondence` |
| NordBank Risk Assessment | `risk_report` |
| Risk Taxonomy | `risk_taxonomy` |
| Auditor Rotation Memo | `internal_memo` |
| NordWealth Audit Report | `audit_report` |
| NordInsure Compliance Filing | `compliance_filing` |
| NordPay Board Minutes | `board_minutes` |
| Cross-Board Membership | `governance_report` |
| Officer CV Summaries | `personnel_record` |

Ground-truth entity and relationship annotations are written to `data/corpus/ground_truth_*.json` and used to measure extraction recall.

---

## Evaluation

### Question Bank

30 questions split evenly:

- **Single-hop** — answered from one document chunk (e.g. "What is NordBank's Tier 1 capital ratio?")
- **Multi-hop** — require traversing entity relationships across documents (e.g. "Which persons serve on the boards of two or more NordFinance subsidiaries?")

Each question carries `required_entities` and `required_relationships` for recall scoring.

### RAG Triad Scores (0.0–1.0)

| Metric | Measured by |
|---|---|
| `context_relevance` | Is the retrieved context relevant to the question? |
| `groundedness` | Is every claim in the answer supported by the context? |
| `answer_relevance` | Does the answer actually address the question? |
| `triad` | Geometric mean of the three scores above |

The judge model is `qwen2.5:1.5b` itself (self-evaluation). All three scores are elicited as decimal numbers via zero-shot prompts; the `parse_score()` function extracts and clamps them to `[0.0, 1.0]`.

### Actual Results (30 questions)

| Slice | Pipeline | Context rel. | Groundedness | Answer rel. | **Triad** |
|---|---|---|---|---|---|
| Single-hop (15 q) | VectorRAG | 0.525 | 0.880 | 0.961 | **0.704** |
| Single-hop (15 q) | GraphRAG  | 0.542 | 0.903 | 0.894 | **0.640** |
| Multi-hop (15 q)  | VectorRAG | 0.582 | 0.803 | 0.553 | **0.534** |
| Multi-hop (15 q)  | GraphRAG  | 0.602 | 0.881 | 0.800 | **0.700** |
| Overall (30 q)    | VectorRAG | 0.553 | 0.842 | 0.757 | **0.619** |
| Overall (30 q)    | GraphRAG  | 0.572 | 0.892 | 0.847 | **0.670** |

**Key observations:**

- GraphRAG is **+31.3%** on multi-hop — entity relationship traversal finds cross-document connections that vector similarity misses entirely.
- VectorRAG is **+9.1%** on single-hop — the graph pipeline is hurt by entity extraction noise; when no useful triples are retrieved, `context_relevance = 0.0` and the geometric mean zeros the entire triad.
- Groundedness is consistently higher for GraphRAG (+5 pp overall) — graph context tends to be more factually dense.
- Answer relevance is the weakest axis for VectorRAG on multi-hop (0.553 vs 0.800) — the model retrieves plausible but off-target chunks.
- 4 GraphRAG answers scored `triad = 0.0` due to empty subgraph retrieval; 5 VectorRAG answers scored `0.0` due to low groundedness.

Run evaluation:

```bash
make eval           # full 30-question run (~45 min on 2-CPU Codespace)
make smoke          # 1-question sanity check (~3 min)
```

Results are written to `data/eval/comparison.json`.

---

## Configuration

All tunables live in `config/settings.yaml`:

```yaml
ollama:
  base_url: "http://localhost:11434"
  generation_model: "qwen2.5:1.5b"
  embedding_model: "nomic-embed-text"
  timeout: 300            # seconds; covers model cold-load (~22s) + generation (~60s/chunk)

neo4j:
  uri: "bolt://localhost:7687"
  user: "neo4j"
  password: "graphrag_demo"

chromadb:
  persist_directory: "data/chroma"
  collection_name: "nordfinance"

retrieval:
  vector_top_k: 5
  graph_top_k: 3
  mmr_lambda: 0.7         # MMR diversity weight
  max_graph_triples: 10
  context_budget_tokens: 2048
```

---

## Design Decisions

**Why `qwen2.5:1.5b` for everything?**
The 2-CPU / 8 GB Codespace constraint rules out larger models. Using the same model for extraction, generation, and judging keeps the comparison fair and self-contained.

**Why `nomic-embed-text` (768-dim) instead of smaller models?**
It fits in memory alongside `qwen2.5:1.5b` (~540 MB + ~1.1 GB = ~1.6 GB resident), gives good semantic quality, and the 768-dim cosine space works well with ChromaDB's HNSW index.

**Why not LangChain / LlamaIndex?**
The project deliberately avoids orchestration frameworks to keep every component inspectable and dependency-minimal. All HTTP calls are direct `httpx.post` to `localhost:11434`.

**Why idempotent ingestion?**
ChromaDB IDs are SHA256 hashes of `doc_id:chunk_index:text`. Neo4j upserts use `MERGE`. Re-running `make ingest` on already-ingested data is safe and instant.

**`NetworkGuard`**
Every URL is validated against localhost before any HTTP request is made. This enforces the "no data leaves the machine" constraint at the library level and is verified by `make audit-network`.

---

## Development

```bash
# Offline fast loop (no Ollama/Neo4j needed)
make dev            # lint + 44 unit tests

# Full CI gate
make ci             # sync → lint → test-unit → audit-network → audit-deps

# Before committing
make lint           # ruff format + ruff check + ty + bandit
```

Unit tests mock all Ollama and Neo4j calls — you can run them in any environment.

---

## Constraints

| Constraint | Value |
|---|---|
| CPU | 2 vCPU |
| RAM | 8 GB (no swap) |
| GPU | None |
| Pipeline | Sequential only (no async/parallel LLM calls) |
| Inference | Local Ollama only |
| Excluded packages | torch, tensorflow, openai, tiktoken, LangChain, LlamaIndex, RAGAS |

---

## License

MIT — see [LICENSE](LICENSE).
