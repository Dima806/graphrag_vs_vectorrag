"""LLM-based named entity and relationship extractor via Ollama."""

import json
import re

import httpx
from loguru import logger

from src.config import get_settings
from src.corpus.schemas import Entity, EntityType, ExtractionResult, Relationship, RelationshipType
from src.network_guard import validate_url

_EXTRACTION_PROMPT = (
    "Extract entities and relationships from the following text.\n"
    "Return ONLY valid JSON matching this schema exactly:\n"
    "{{\n"
    '  "entities": [\n'
    '    {{"name": "...", "type": "Company|Person|AuditFirm|Regulator|'
    'RiskFactor|FinancialMetric|Report", "description": "..."}}\n'
    "  ],\n"
    '  "relationships": [\n'
    '    {{"source": "...", "target": "...", "type": "HAS_SUBSIDIARY|HAS_OFFICER|'
    "SERVES_ON_BOARD|AUDITED_BY|REGULATED_BY|ISSUED_SANCTION|FILED_REPORT|"
    'MENTIONS_RISK|HAS_METRIC", "properties": {{}}}}\n'
    "  ]\n"
    "}}\n\n"
    "Text:\n{text}"
)

_VALID_ENTITY_TYPES: frozenset[str] = frozenset(e.value for e in EntityType)
_VALID_REL_TYPES: frozenset[str] = frozenset(r.value for r in RelationshipType)


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for ch_a in a:
        curr = [prev[0] + 1]
        for j, ch_b in enumerate(b):
            curr.append(min(curr[-1] + 1, prev[j + 1] + 1, prev[j] + int(ch_a != ch_b)))
        prev = curr
    return prev[-1]


def _normalise(name: str) -> str:
    return name.lower().strip()


def dedup_entities(entities: list[Entity]) -> list[Entity]:
    """Remove near-duplicate entities (Levenshtein ≤ 2 after normalisation)."""
    seen: list[str] = []
    unique: list[Entity] = []
    for ent in entities:
        norm = _normalise(ent.name)
        if all(_levenshtein(norm, s) > 2 for s in seen):
            seen.append(norm)
            unique.append(ent)
    return unique


def _extract_json(raw: str) -> dict:
    """Pull the first JSON object out of an LLM response string."""
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return {"entities": [], "relationships": []}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {"entities": [], "relationships": []}


def _parse_entity(item: dict) -> Entity | None:
    if item.get("type") not in _VALID_ENTITY_TYPES:
        return None
    return Entity(
        name=str(item.get("name", "")),
        type=EntityType(item["type"]),
        description=str(item.get("description", "")),
    )


def _parse_relationship(item: dict) -> Relationship | None:
    if item.get("type") not in _VALID_REL_TYPES:
        return None
    return Relationship(
        source=str(item.get("source", "")),
        target=str(item.get("target", "")),
        type=RelationshipType(item["type"]),
        properties=item.get("properties") or {},
    )


class EntityExtractor:
    """LLM-based NER and relationship extractor using qwen2.5:1.5b via Ollama."""

    def __init__(self) -> None:
        cfg = get_settings().ollama
        self._url = validate_url(f"{cfg.base_url}/api/generate")
        self._model = cfg.generation_model
        self._timeout = cfg.timeout

    def extract(self, text: str) -> ExtractionResult:
        """Extract entities and relationships from a single text chunk."""
        prompt = _EXTRACTION_PROMPT.format(text=text[:1500])
        response = httpx.post(
            self._url,
            json={"model": self._model, "prompt": prompt, "stream": False},
            timeout=self._timeout,
        )
        response.raise_for_status()
        raw = response.json().get("response", "")
        data = _extract_json(raw)
        logger.debug(f"Extracted {len(data.get('entities', []))} entities from chunk.")

        entities = [e for item in data.get("entities", []) if (e := _parse_entity(item))]
        relationships = [
            r for item in data.get("relationships", []) if (r := _parse_relationship(item))
        ]
        return ExtractionResult(entities=dedup_entities(entities), relationships=relationships)


if __name__ == "__main__":
    import json
    from pathlib import Path

    from src.config import get_settings
    from src.corpus.generator import generate_corpus
    from src.ingestion.chunker import chunk_document

    extractor = EntityExtractor()
    all_entities: list[Entity] = []
    all_relationships: list[Relationship] = []

    for doc in generate_corpus():
        chunks = chunk_document(doc.content, doc.doc_id)
        for chunk in chunks:
            result = extractor.extract(chunk.text)
            all_entities.extend(result.entities)
            all_relationships.extend(result.relationships)

    all_entities = dedup_entities(all_entities)

    out_dir = Path(get_settings().corpus.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "extracted_entities.json").write_text(
        json.dumps([e.model_dump() for e in all_entities], indent=2), encoding="utf-8"
    )
    (out_dir / "extracted_relationships.json").write_text(
        json.dumps([r.model_dump() for r in all_relationships], indent=2), encoding="utf-8"
    )
    logger.info(
        f"Extraction complete: {len(all_entities)} entities, "
        f"{len(all_relationships)} relationships saved to {out_dir}"
    )
