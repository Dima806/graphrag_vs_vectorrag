"""RAG Triad evaluator: context relevance, groundedness, answer relevance."""

import math
import re

import httpx
from loguru import logger

from src.config import get_settings
from src.network_guard import validate_url

_CR_PROMPT = (
    "Rate how relevant this context is to the question.\n"
    "Reply with ONLY a decimal number between 0.0 (irrelevant) and 1.0 (highly relevant).\n\n"
    "Question: {question}\n"
    "Context: {context}\n"
    "Score:"
)

_GR_PROMPT = (
    "Is every claim in the answer supported by the context?\n"
    "Reply with ONLY a decimal number between 0.0 (mostly unsupported) and 1.0 (fully grounded).\n\n"
    "Context: {context}\n"
    "Answer: {answer}\n"
    "Score:"
)

_AR_PROMPT = (
    "How well does the answer address the question?\n"
    "Reply with ONLY a decimal number between 0.0 (irrelevant) and 1.0 (fully answers it).\n\n"
    "Question: {question}\n"
    "Answer: {answer}\n"
    "Score:"
)


def parse_score(raw: str) -> float:
    """Extract a float from LLM output and clamp to [0.0, 1.0]."""
    match = re.search(r"-?(?:[01]?\.\d+|[01])", raw.strip())
    if match:
        return max(0.0, min(1.0, float(match.group())))
    return 0.0


class RAGTriad:
    """Self-evaluating RAG Triad scorer using qwen2.5:1.5b as judge."""

    def __init__(self) -> None:
        cfg = get_settings().ollama
        self._url = validate_url(f"{cfg.base_url}/api/generate")
        self._model = cfg.generation_model
        self._timeout = cfg.timeout

    def _call(self, prompt: str) -> float:
        response = httpx.post(
            self._url,
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=self._timeout,
        )
        response.raise_for_status()
        raw = response.json().get("response", "0")
        score = parse_score(raw)
        logger.debug(f"RAGTriad score: {score} (raw={raw!r})")
        return score

    def score_context_relevance(self, question: str, context: str) -> float:
        """Score retrieved context relevance to the question (0–1)."""
        return self._call(_CR_PROMPT.format(question=question, context=context[:800]))

    def score_groundedness(self, context: str, answer: str) -> float:
        """Score how well the answer is grounded in the context (0–1)."""
        return self._call(_GR_PROMPT.format(context=context[:800], answer=answer[:400]))

    def score_answer_relevance(self, question: str, answer: str) -> float:
        """Score how well the answer addresses the question (0–1)."""
        return self._call(_AR_PROMPT.format(question=question, answer=answer[:400]))

    def evaluate(self, question: str, context: str, answer: str) -> dict[str, float]:
        """Return all three scores and their geometric mean as 'triad'."""
        cr = self.score_context_relevance(question, context)
        gr = self.score_groundedness(context, answer)
        ar = self.score_answer_relevance(question, answer)
        product = cr * gr * ar
        triad = math.pow(product, 1.0 / 3.0) if product > 0 else 0.0
        return {
            "context_relevance": cr,
            "groundedness": gr,
            "answer_relevance": ar,
            "triad": triad,
        }
