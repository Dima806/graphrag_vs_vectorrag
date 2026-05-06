"""Neo4j graph writer using the official Python driver."""

from loguru import logger
from neo4j import GraphDatabase
from neo4j import Query as CypherQuery

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
        cypher = CypherQuery(
            f"MERGE (n:`{entity.type}` {{name: $name}}) SET n.description = $description"  # type: ignore
        )
        with self._driver.session() as session:
            session.run(cypher, name=entity.name, description=entity.description)

    def upsert_relationship(self, rel: Relationship) -> None:
        """MERGE directed relationship between two entity nodes."""
        rel_label = f"`{rel.type}`"
        cypher = CypherQuery(
            f"MATCH (a {{name: $source}}), (b {{name: $target}}) MERGE (a)-[r:{rel_label}]->(b) SET r += $props"  # type: ignore
        )
        with self._driver.session() as session:
            session.run(cypher, source=rel.source, target=rel.target, props=rel.properties)

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


if __name__ == "__main__":
    import json
    from pathlib import Path

    from src.config import get_settings
    from src.corpus.schemas import Entity, Relationship

    out_dir = Path(get_settings().corpus.output_dir)
    entities_path = out_dir / "extracted_entities.json"
    relationships_path = out_dir / "extracted_relationships.json"

    if not entities_path.exists():
        logger.warning(
            f"No extracted entities found at {entities_path}. Run entity_extractor first."
        )
    else:
        store = Neo4jGraphStore()
        try:
            raw_entities = json.loads(entities_path.read_text(encoding="utf-8"))
            entities = [Entity(**e) for e in raw_entities]
            store.upsert_entities(entities)

            if relationships_path.exists():
                raw_rels = json.loads(relationships_path.read_text(encoding="utf-8"))
                relationships = [Relationship(**r) for r in raw_rels]
                store.upsert_relationships(relationships)
            else:
                logger.warning(f"No extracted relationships found at {relationships_path}.")
        finally:
            store.close()
        logger.info("Graph store population complete.")
