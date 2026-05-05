"""Unit tests for src/ingestion/vector_store.py — ChromaDB and embedder mocked."""

from unittest.mock import MagicMock, patch

import pytest

from src.ingestion.chunker import Chunk
from src.ingestion.vector_store import ChromaDocumentStore


def _make_store() -> tuple[ChromaDocumentStore, MagicMock, MagicMock]:
    with (
        patch("src.ingestion.vector_store.chromadb.PersistentClient") as mock_chroma,
        patch("src.ingestion.vector_store.OllamaEmbeddingClient") as mock_embedder_cls,
    ):
        mock_collection = MagicMock()
        mock_chroma.return_value.get_or_create_collection.return_value = mock_collection
        mock_embedder = MagicMock()
        mock_embedder_cls.return_value = mock_embedder
        store = ChromaDocumentStore()
    return store, mock_collection, mock_embedder


def _chunk(text: str = "test chunk", doc_id: str = "d1", idx: int = 0) -> Chunk:
    return Chunk(text=text, doc_id=doc_id, chunk_index=idx, start_char=0)


def test_chunk_id_is_deterministic() -> None:
    c = _chunk("hello", "doc1", 0)
    assert ChromaDocumentStore.chunk_id(c) == ChromaDocumentStore.chunk_id(c)


def test_chunk_id_differs_for_different_chunks() -> None:
    c1 = _chunk("text A", "doc1", 0)
    c2 = _chunk("text B", "doc1", 1)
    assert ChromaDocumentStore.chunk_id(c1) != ChromaDocumentStore.chunk_id(c2)


def test_upsert_skips_existing_chunks() -> None:
    store, mock_collection, mock_embedder = _make_store()
    chunk = _chunk("already there")
    existing_id = ChromaDocumentStore.chunk_id(chunk)
    mock_collection.get.return_value = {"ids": [existing_id]}

    count = store.upsert([chunk])
    assert count == 0
    mock_collection.add.assert_not_called()


def test_upsert_adds_new_chunks() -> None:
    store, mock_collection, mock_embedder = _make_store()
    chunk = _chunk("brand new content")
    mock_collection.get.return_value = {"ids": []}
    mock_embedder.embed_batch.return_value = [[0.1, 0.2, 0.3]]

    count = store.upsert([chunk])
    assert count == 1
    mock_collection.add.assert_called_once()


def test_upsert_empty_list_returns_zero() -> None:
    store, mock_collection, _ = _make_store()
    count = store.upsert([])
    assert count == 0
    mock_collection.get.assert_not_called()


def test_query_returns_formatted_results() -> None:
    store, mock_collection, _ = _make_store()
    mock_collection.query.return_value = {
        "documents": [["chunk text"]],
        "metadatas": [[{"doc_id": "d1", "chunk_index": 0}]],
        "distances": [[0.12]],
    }
    results = store.query([0.1, 0.2], n_results=1)
    assert len(results) == 1
    assert results[0]["text"] == "chunk text"
    assert results[0]["distance"] == pytest.approx(0.12)
