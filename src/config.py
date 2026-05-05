from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

_SETTINGS_PATH = Path("config/settings.yaml")


class OllamaConfig(BaseModel):
    """Ollama inference service configuration."""

    base_url: str = "http://localhost:11434"
    generation_model: str = "qwen2.5:1.5b"
    embedding_model: str = "nomic-embed-text"
    timeout: int = 120


class Neo4jConfig(BaseModel):
    """Neo4j graph database configuration."""

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "graphrag_demo"


class ChromaDBConfig(BaseModel):
    """ChromaDB vector store configuration."""

    persist_directory: str = "data/chroma"
    collection_name: str = "nordfinance"


class CorpusConfig(BaseModel):
    """Synthetic corpus output configuration."""

    output_dir: str = "data/corpus"


class EvalConfig(BaseModel):
    """Evaluation output configuration."""

    output_dir: str = "data/eval"


class RetrievalConfig(BaseModel):
    """Retrieval pipeline parameters."""

    vector_top_k: int = 5
    graph_top_k: int = 3
    mmr_lambda: float = 0.7
    max_graph_triples: int = 10
    context_budget_tokens: int = 2048


class Settings(BaseModel):
    """Top-level project settings loaded from config/settings.yaml."""

    ollama: OllamaConfig = OllamaConfig()
    neo4j: Neo4jConfig = Neo4jConfig()
    chromadb: ChromaDBConfig = ChromaDBConfig()
    corpus: CorpusConfig = CorpusConfig()
    eval: EvalConfig = EvalConfig()
    retrieval: RetrievalConfig = RetrievalConfig()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings from config/settings.yaml, falling back to defaults."""
    if _SETTINGS_PATH.exists():
        with _SETTINGS_PATH.open() as fh:
            data = yaml.safe_load(fh) or {}
        return Settings.model_validate(data)
    return Settings()
