"""Unit tests for src/ingestion/entity_extractor.py — LLM calls mocked."""

import json
from unittest.mock import MagicMock, patch

from src.corpus.schemas import Entity, EntityType, RelationshipType
from src.ingestion.entity_extractor import (
    EntityExtractor,
    _extract_json,
    _levenshtein,
    dedup_entities,
)


def _mock_response(payload: dict) -> MagicMock:
    mock = MagicMock()
    mock.json.return_value = {"response": json.dumps(payload)}
    mock.raise_for_status.return_value = None
    return mock


@patch("src.ingestion.entity_extractor.httpx.post")
def test_extract_returns_entities(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response(
        {
            "entities": [
                {"name": "NordBank", "type": "Company", "description": "A bank"},
            ],
            "relationships": [],
        }
    )
    extractor = EntityExtractor()
    result = extractor.extract("NordBank is a bank.")
    assert len(result.entities) == 1
    assert result.entities[0].name == "NordBank"
    assert result.entities[0].type == EntityType.COMPANY


@patch("src.ingestion.entity_extractor.httpx.post")
def test_extract_filters_invalid_entity_types(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response(
        {
            "entities": [
                {"name": "X", "type": "InvalidType", "description": ""},
                {"name": "Y", "type": "Person", "description": ""},
            ],
            "relationships": [],
        }
    )
    extractor = EntityExtractor()
    result = extractor.extract("some text")
    assert len(result.entities) == 1
    assert result.entities[0].type == EntityType.PERSON


@patch("src.ingestion.entity_extractor.httpx.post")
def test_extract_relationships(mock_post: MagicMock) -> None:
    mock_post.return_value = _mock_response(
        {
            "entities": [],
            "relationships": [
                {
                    "source": "NordBank",
                    "target": "Deloitte",
                    "type": "AUDITED_BY",
                    "properties": {},
                }
            ],
        }
    )
    extractor = EntityExtractor()
    result = extractor.extract("text")
    assert len(result.relationships) == 1
    assert result.relationships[0].type == RelationshipType.AUDITED_BY


@patch("src.ingestion.entity_extractor.httpx.post")
def test_extract_handles_malformed_json(mock_post: MagicMock) -> None:
    mock = MagicMock()
    mock.json.return_value = {"response": "not valid json at all {{{{"}
    mock.raise_for_status.return_value = None
    mock_post.return_value = mock
    extractor = EntityExtractor()
    result = extractor.extract("text")
    assert result.entities == []
    assert result.relationships == []


def test_extract_json_pulls_object_from_surrounding_text() -> None:
    raw = 'Here is the result: {"entities": [], "relationships": []} and more text.'
    data = _extract_json(raw)
    assert data == {"entities": [], "relationships": []}


def test_extract_json_returns_empty_on_no_json() -> None:
    data = _extract_json("no braces here")
    assert data == {"entities": [], "relationships": []}


def test_levenshtein_identical_strings() -> None:
    assert _levenshtein("nordbank", "nordbank") == 0


def test_levenshtein_single_edit() -> None:
    assert _levenshtein("nordbank", "nordban") == 1


def test_dedup_removes_near_duplicates() -> None:
    entities = [
        Entity(name="NordBank", type=EntityType.COMPANY),
        Entity(name="Nordbank", type=EntityType.COMPANY),  # Levenshtein 1 after normalise
        Entity(name="EY Nordic", type=EntityType.AUDIT_FIRM),
    ]
    unique = dedup_entities(entities)
    assert len(unique) == 2
    names = {e.name for e in unique}
    assert "EY Nordic" in names
