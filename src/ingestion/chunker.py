"""Recursive character text splitter — no external dependencies."""

from dataclasses import dataclass

_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class Chunk:
    """A text chunk derived from a document."""

    text: str
    doc_id: str
    chunk_index: int
    start_char: int


def _split_on_separator(text: str, sep: str) -> list[str]:
    return text.split(sep) if sep else list(text)


def _merge_splits(splits: list[str], sep: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Merge short splits into chunks respecting size and overlap constraints."""
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for piece in splits:
        piece_len = len(piece)
        join_len = len(sep) if current else 0

        if current and current_len + join_len + piece_len > chunk_size:
            chunks.append(sep.join(current))
            # retain overlap
            while current and current_len > chunk_overlap:
                removed = current.pop(0)
                current_len -= len(removed) + len(sep)

        current.append(piece)
        current_len += piece_len + (len(sep) if len(current) > 1 else 0)

    if current:
        chunks.append(sep.join(current))

    return chunks


def _recursive_split(
    text: str, separators: list[str], chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Split text by trying separators in order, recursing on oversized pieces."""
    if not text.strip():
        return []

    sep = ""
    remaining_seps: list[str] = []
    for i, candidate in enumerate(separators):
        if candidate == "" or candidate in text:
            sep = candidate
            remaining_seps = separators[i + 1 :]
            break

    raw_splits = _split_on_separator(text, sep)
    good: list[str] = []
    too_big: list[str] = []

    for piece in raw_splits:
        if len(piece) <= chunk_size:
            good.append(piece)
        else:
            too_big.append(piece)

    merged = _merge_splits(good, sep, chunk_size, chunk_overlap)

    result: list[str] = []
    for chunk in merged:
        if len(chunk) > chunk_size and remaining_seps:
            result.extend(_recursive_split(chunk, remaining_seps, chunk_size, chunk_overlap))
        elif chunk.strip():
            result.append(chunk)

    for piece in too_big:
        if remaining_seps:
            result.extend(_recursive_split(piece, remaining_seps, chunk_size, chunk_overlap))
        elif piece.strip():
            result.append(piece)

    return result


def chunk_document(
    text: str,
    doc_id: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Chunk]:
    """Split a document into overlapping chunks and return annotated Chunk objects."""
    raw = _recursive_split(text, _SEPARATORS, chunk_size, chunk_overlap)
    chunks: list[Chunk] = []
    search_from = 0
    for i, chunk_text in enumerate(raw):
        pos = text.find(chunk_text, search_from)
        start = pos if pos != -1 else search_from
        chunks.append(Chunk(text=chunk_text, doc_id=doc_id, chunk_index=i, start_char=start))
        if pos != -1:
            search_from = pos
    return chunks
