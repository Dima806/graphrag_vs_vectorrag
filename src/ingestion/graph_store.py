"""Neo4j graph writer using the official Python driver."""

from loguru import logger
from neo4j import GraphDatabase

from src.config import get_settings
from src.corpus.schemas import Entity, Relationship


class Neo4jGraphStore:
    """Neo4j graph store with idempotent MERGE-based upserts."""

    def __init__(self) -> None:
        cfg = get_settings().neo4j
        self._driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))

    def close(self) -> None:
        """Close the Neo4j driver connection."""
        self._driver.close()

    def upsert_entity(self, entity: Entity) -> None:
        """MERGE entity node; set description property."""
        query = f"MERGE (n:`{entity.type}` {{name: $name}}) SET n.description = $description"
        with self._driver.session() as session:
            session.run(query, name=entity.name, description=entity.description)

    def upsert_relationship(self, rel: Relationship) -> None:
        """MERGE directed relationship between two entity nodes."""
        query = (
            "MATCH (a {name: $source}), (b {name: $target}) "
            f"MERGE (a)-[r:`{rel.type}`]->(b) "
            "SET r += $props"
        )
        with self._driver.session() as session:
            session.run(
                query,
                source=rel.source,
                target=rel.target,
                props=rel.properties,
            )

    def upsert_entities(self, entities: list[Entity]) -> int:
        """Merge all entities; return count."""
        for entity in entities:
            self.upsert_entity(entity)
        logger.info(f"Upserted {len(entities)} entities.")
        return len(entities)

    def upsert_relationships(self, relationships: list[Relationship]) -> int:
        """Merge all relationships; return count."""
        for rel in relationships:
            self.upsert_relationship(rel)
        logger.info(f"Upserted {len(relationships)} relationships.")
        return len(relationships)

    def query_subgraph(self, entity_names: list[str], max_triples: int = 10) -> list[dict]:
        """Return up to max_triples triples involving the given entity names."""
        query = (
            "MATCH (a)-[r]->(b) "
            "WHERE a.name IN $names OR b.name IN $names "
            "RETURN a.name AS source, type(r) AS rel, b.name AS target "
            "LIMIT $limit"
        )
        with self._driver.session() as session:
            result = session.run(query, names=entity_names, limit=max_triples)
            return [
                {"source": row["source"], "rel": row["rel"], "target": row["target"]}
                for row in result
            ]
