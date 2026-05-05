"""Hybrid retriever that merges graph triples with vector chunks."""

from src.retrieval.graph_retriever import GraphRetriever
from src.retrieval.vector_retriever import VectorRetriever


class HybridRetriever:
    """Combine graph context and vector chunks for GraphRAG pipeline."""

    def __init__(self) -> None:
        self._vector = VectorRetriever()
        self._graph = GraphRetriever()

    def retrieve(self, query: str) -> dict[str, list]:
        """Return {'graph': [triples], 'vector': [chunks]} for a query."""
        graph_ctx = self._graph.retrieve(query)
        vector_ctx = self._vector.retrieve(query)
        return {"graph": graph_ctx, "vector": vector_ctx}
