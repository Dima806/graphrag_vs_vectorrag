"""Unit tests for src/ingestion/graph_store.py — Neo4j driver mocked."""

from unittest.mock import MagicMock, patch

from src.corpus.schemas import Entity, EntityType, Relationship, RelationshipType
from src.ingestion.graph_store import Neo4jGraphStore


def _make_store() -> tuple[Neo4jGraphStore, MagicMock]:
    with patch("src.ingestion.graph_store.GraphDatabase.driver") as mock_driver_fn:
        mock_driver = MagicMock()
        mock_driver_fn.return_value = mock_driver
        store = Neo4jGraphStore()
    return store, mock_driver


def test_upsert_entity_runs_merge_query() -> None:
    store, mock_driver = _make_store()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    entity = Entity(name="NordBank A/S", type=EntityType.COMPANY, description="A bank")
    store.upsert_entity(entity)

    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args
    query_arg = call_args[0][0]
    query_text = query_arg.text if hasattr(query_arg, "text") else str(query_arg)
    assert "MERGE" in query_text
    assert call_args[1]["name"] == "NordBank A/S"


def test_upsert_relationship_runs_merge_query() -> None:
    store, mock_driver = _make_store()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    rel = Relationship(
        source="NordBank A/S",
        target="Deloitte Nordic",
        type=RelationshipType.AUDITED_BY,
    )
    store.upsert_relationship(rel)

    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args
    query_arg = call_args[0][0]
    query_text = query_arg.text if hasattr(query_arg, "text") else str(query_arg)
    assert "MERGE" in query_text
    assert call_args[1]["source"] == "NordBank A/S"
    assert call_args[1]["target"] == "Deloitte Nordic"


def test_upsert_entities_returns_count() -> None:
    store, mock_driver = _make_store()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    entities = [
        Entity(name="NordBank A/S", type=EntityType.COMPANY),
        Entity(name="Deloitte Nordic", type=EntityType.AUDIT_FIRM),
    ]
    count = store.upsert_entities(entities)
    assert count == 2
    assert mock_session.run.call_count == 2


def test_upsert_relationships_returns_count() -> None:
    store, mock_driver = _make_store()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    rels = [
        Relationship(source="A", target="B", type=RelationshipType.AUDITED_BY),
        Relationship(source="C", target="D", type=RelationshipType.REGULATED_BY),
    ]
    count = store.upsert_relationships(rels)
    assert count == 2


def test_query_subgraph_returns_triples() -> None:
    store, mock_driver = _make_store()
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    fake_row = {"source": "NordBank A/S", "rel": "AUDITED_BY", "target": "Deloitte Nordic"}
    mock_session.run.return_value = [fake_row]

    result = store.query_subgraph(["NordBank A/S"], max_triples=5)
    assert len(result) == 1
    assert result[0]["source"] == "NordBank A/S"
    assert result[0]["rel"] == "AUDITED_BY"


def test_close_calls_driver_close() -> None:
    store, mock_driver = _make_store()
    store.close()
    mock_driver.close.assert_called_once()
