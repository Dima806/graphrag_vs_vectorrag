"""Cypher-based subgraph retrieval from Neo4j."""

import json
import re

import httpx
from loguru import logger

from src.config import get_settings
from src.ingestion.graph_store import Neo4jGraphStore
from src.network_guard import validate_url

_ENTITY_PROMPT = (
    "List the named entities (companies, people, organisations) mentioned in this query.\n"
    'Return ONLY a JSON array of strings, e.g. ["NordBank", "Deloitte"].\n\n'
    "Query: {query}"
)


class GraphRetriever:
    """Retrieve knowledge graph triples relevant to a natural-language query."""

    def __init__(self) -> None:
        cfg = get_settings()
        self._graph = Neo4jGraphStore()
        self._ollama_url = validate_url(f"{cfg.ollama.base_url}/api/generate")
        self._model = cfg.ollama.generation_model
        self._timeout = cfg.ollama.timeout
        self._max_triples = cfg.retrieval.max_graph_triples

    def _extract_query_entities(self, query: str) -> list[str]:
        """Use the LLM to extract named entities from a query string."""
        prompt = _ENTITY_PROMPT.format(query=query)
        try:
            response = httpx.post(
                self._ollama_url,
                json={"model": self._model, "prompt": prompt, "stream": False},
                timeout=self._timeout,
            )
            response.raise_for_status()
            raw = response.json().get("response", "[]")
            match = re.search(r"\[.*?\]", raw, re.DOTALL)
            if match:
                parsed = json.loads(match.group())
                if isinstance(parsed, list):
                    return [str(e) for e in parsed]
        except Exception:  # noqa: BLE001
            logger.warning("Entity extraction from query failed; returning empty list.")
        return []

    def retrieve(self, query: str) -> list[dict]:
        """Return graph triples matching entities found in the query."""
        entities = self._extract_query_entities(query)
        if not entities:
            logger.debug("No entities extracted from query; skipping graph retrieval.")
            return []
        logger.debug(f"Graph retrieval for entities: {entities}")
        return self._graph.query_subgraph(entities, self._max_triples)
