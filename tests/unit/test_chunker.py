"""Unit tests for src/ingestion/chunker.py — no external services needed."""

import pytest

from src.ingestion.chunker import Chunk, chunk_document


def test_basic_chunking_returns_chunks() -> None:
    text = "word " * 200
    chunks = chunk_document(text, "doc1", chunk_size=100, chunk_overlap=20)
    assert len(chunks) > 1


def test_chunk_dataclass_fields() -> None:
    chunks = chunk_document("hello world " * 10, "docA", chunk_size=50, chunk_overlap=10)
    for i, c in enumerate(chunks):
        assert isinstance(c, Chunk)
        assert c.doc_id == "docA"
        assert c.chunk_index == i
        assert isinstance(c.start_char, int)
        assert isinstance(c.text, str)


def test_chunk_size_respected() -> None:
    text = "abcde " * 300
    chunks = chunk_document(text, "doc2", chunk_size=80, chunk_overlap=10)
    oversized = [c for c in chunks if len(c.text) > 120]
    assert len(oversized) == 0, f"Chunks exceeded size limit: {[len(c.text) for c in oversized]}"


def test_empty_text_returns_no_chunks() -> None:
    chunks = chunk_document("", "doc3", chunk_size=512, chunk_overlap=64)
    assert chunks == []


def test_whitespace_only_returns_no_chunks() -> None:
    chunks = chunk_document("   \n\n   \t  ", "doc4", chunk_size=512, chunk_overlap=64)
    assert chunks == []


def test_short_text_single_chunk() -> None:
    text = "This is a short document."
    chunks = chunk_document(text, "doc5", chunk_size=512, chunk_overlap=64)
    assert len(chunks) == 1
    assert chunks[0].text.strip() == text.strip()


@pytest.mark.parametrize("size,overlap", [(256, 32), (512, 64), (128, 16)])
def test_various_chunk_sizes(size: int, overlap: int) -> None:
    text = "paragraph content\n\n" * 50
    chunks = chunk_document(text, "doc6", chunk_size=size, chunk_overlap=overlap)
    assert len(chunks) >= 1
    for c in chunks:
        assert c.text.strip() != ""
