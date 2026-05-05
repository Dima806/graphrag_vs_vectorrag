"""Ollama text generation client via httpx."""

import httpx
from loguru import logger

from src.config import get_settings
from src.network_guard import validate_url


class OllamaGenerationClient:
    """HTTP client for the Ollama /api/generate endpoint."""

    def __init__(self) -> None:
        cfg = get_settings().ollama
        self._url = validate_url(f"{cfg.base_url}/api/generate")
        self._model = cfg.generation_model
        self._timeout = cfg.timeout

    def generate(self, prompt: str) -> str:
        """Generate a completion for the given prompt; return stripped response text."""
        logger.debug(f"Generating: model={self._model}, prompt_tokens~{len(prompt) // 4}")
        response = httpx.post(
            self._url,
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json().get("response", "").strip()
