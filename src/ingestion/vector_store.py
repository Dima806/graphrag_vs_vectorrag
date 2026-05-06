"""ChromaDB document store with idempotent SHA256-keyed upserts."""

import hashlib
from typing import cast

import chromadb
from chromadb import Embeddings
from loguru import logger

from src.config import get_settings
from src.ingestion.chunker import Chunk
from src.ingestion.embedder import OllamaEmbeddingClient


class ChromaDocumentStore:
    """Persistent ChromaDB vector store; upserts are safe to re-run."""

    def __init__(self) -> None:
        cfg = get_settings()
        self._client = chromadb.PersistentClient(path=cfg.chromadb.persist_directory)
        self._collection = self._client.get_or_create_collection(
            name=cfg.chromadb.collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        self._embedder = OllamaEmbeddingClient()

    @staticmethod
    def chunk_id(chunk: Chunk) -> str:
        """Return a stable 32-char SHA256 ID for a chunk."""
        key = f"{chunk.doc_id}:{chunk.chunk_index}:{chunk.text}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]

    def upsert(self, chunks: list[Chunk]) -> int:
        """Embed and upsert chunks; skip already-present IDs. Returns new count."""
        if not chunks:
            return 0
        ids = [self.chunk_id(c) for c in chunks]
        existing = set(self._collection.get(ids=ids)["ids"])
        new_chunks = [c for c, cid in zip(chunks, ids, strict=True) if cid not in existing]
        if not new_chunks:
            logger.debug("All chunks already present — skipping.")
            return 0
        new_ids = [self.chunk_id(c) for c in new_chunks]
        embeddings = cast(Embeddings, self._embedder.embed_batch([c.text for c in new_chunks]))
        self._collection.add(
            ids=new_ids,
            embeddings=embeddings,
            documents=[c.text for c in new_chunks],
            metadatas=[{"doc_id": c.doc_id, "chunk_index": c.chunk_index} for c in new_chunks],
        )
        logger.info(f"Upserted {len(new_chunks)} new chunks.")
        return len(new_chunks)

    def query(self, embedding: list[float], n_results: int = 5) -> list[dict]:
        """Return top-n chunks ranked by cosine similarity to the query embedding."""
        results = self._collection.query(
            query_embeddings=[embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        docs = (results["documents"] or [[]])[0]
        metas = (results["metadatas"] or [[]])[0]
        dists = (results["distances"] or [[]])[0]
        return [
            {"text": d, "metadata": m, "distance": dist}
            for d, m, dist in zip(docs, metas, dists, strict=True)
        ]


if __name__ == "__main__":
    from src.corpus.generator import generate_corpus
    from src.ingestion.chunker import chunk_document

    store = ChromaDocumentStore()
    total = 0
    for doc in generate_corpus():
        chunks = chunk_document(doc.content, doc.doc_id)
        total += store.upsert(chunks)
    logger.info(f"Vector ingestion complete. Total new chunks: {total}")
