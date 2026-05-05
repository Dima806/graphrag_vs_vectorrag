"""ChromaDB vector retrieval with numpy MMR re-ranking."""

import numpy as np
from loguru import logger

from src.config import get_settings
from src.ingestion.embedder import OllamaEmbeddingClient
from src.ingestion.vector_store import ChromaDocumentStore


def mmr_rerank(
    query_emb: list[float],
    doc_embs: list[list[float]],
    docs: list[dict],
    k: int,
    lambda_mult: float,
) -> list[dict]:
    """Maximal Marginal Relevance re-ranking to balance relevance and diversity."""
    if not docs:
        return []
    q = np.array(query_emb, dtype=np.float32)
    d = np.array(doc_embs, dtype=np.float32)
    q_norm = q / (np.linalg.norm(q) + 1e-10)
    d_norms = np.linalg.norm(d, axis=1, keepdims=True) + 1e-10
    d_unit = d / d_norms
    relevance: np.ndarray = d_unit @ q_norm

    selected: list[int] = []
    remaining = list(range(len(docs)))

    for _ in range(min(k, len(docs))):
        if not selected:
            chosen = remaining[int(np.argmax(relevance[remaining]))]
        else:
            sel_unit = d_unit[selected]
            redundancy: np.ndarray = (d_unit[remaining] @ sel_unit.T).max(axis=1)
            scores: np.ndarray = (
                lambda_mult * relevance[remaining] - (1 - lambda_mult) * redundancy
            )
            chosen = remaining[int(np.argmax(scores))]
        selected.append(chosen)
        remaining.remove(chosen)

    return [docs[i] for i in selected]


class VectorRetriever:
    """Top-k vector retrieval with MMR re-ranking."""

    def __init__(self) -> None:
        cfg = get_settings().retrieval
        self._store = ChromaDocumentStore()
        self._embedder = OllamaEmbeddingClient()
        self._top_k = cfg.vector_top_k
        self._mmr_lambda = cfg.mmr_lambda

    def retrieve(self, query: str) -> list[dict]:
        """Embed the query, fetch candidates, and return MMR-ranked top-k chunks."""
        logger.debug(f"VectorRetriever: query={query[:60]!r}")
        emb = self._embedder.embed(query)
        candidates = self._store.query(emb, n_results=self._top_k * 2)
        if not candidates:
            return []
        doc_embs = [self._embedder.embed(c["text"]) for c in candidates]
        return mmr_rerank(emb, doc_embs, candidates, self._top_k, self._mmr_lambda)
