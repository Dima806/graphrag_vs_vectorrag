"""Ollama embedding client via httpx."""

import httpx
from loguru import logger

from src.config import get_settings
from src.network_guard import validate_url


class OllamaEmbeddingClient:
    """HTTP client for the Ollama /api/embeddings endpoint."""

    def __init__(self) -> None:
        cfg = get_settings().ollama
        self._url = validate_url(f"{cfg.base_url}/api/embeddings")
        self._model = cfg.embedding_model
        self._timeout = cfg.timeout

    def embed(self, text: str) -> list[float]:
        """Return a 768-dim embedding vector for a single text string."""
        response = httpx.post(
            self._url,
            json={"model": self._model, "prompt": text},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts sequentially (2-CPU safe, no parallelism)."""
        results = []
        for i, text in enumerate(texts):
            logger.debug(f"Embedding {i + 1}/{len(texts)}")
            results.append(self.embed(text))
        return results
