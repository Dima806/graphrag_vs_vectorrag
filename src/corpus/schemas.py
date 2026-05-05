from enum import StrEnum

from pydantic import BaseModel


class EntityType(StrEnum):
    """Typed entity categories for the NordFinance knowledge graph."""

    COMPANY = "Company"
    PERSON = "Person"
    AUDIT_FIRM = "AuditFirm"
    REGULATOR = "Regulator"
    RISK_FACTOR = "RiskFactor"
    FINANCIAL_METRIC = "FinancialMetric"
    REPORT = "Report"


class RelationshipType(StrEnum):
    """Typed relationship categories for the NordFinance knowledge graph."""

    HAS_SUBSIDIARY = "HAS_SUBSIDIARY"
    HAS_OFFICER = "HAS_OFFICER"
    SERVES_ON_BOARD = "SERVES_ON_BOARD"
    AUDITED_BY = "AUDITED_BY"
    REGULATED_BY = "REGULATED_BY"
    ISSUED_SANCTION = "ISSUED_SANCTION"
    FILED_REPORT = "FILED_REPORT"
    MENTIONS_RISK = "MENTIONS_RISK"
    HAS_METRIC = "HAS_METRIC"


class Entity(BaseModel):
    """A named entity node in the knowledge graph."""

    name: str
    type: EntityType
    description: str = ""


class Relationship(BaseModel):
    """A directed relationship edge between two entity nodes."""

    source: str
    target: str
    type: RelationshipType
    properties: dict[str, str | float | int] = {}


class Document(BaseModel):
    """A synthetic NordFinance compliance document with ground-truth annotations."""

    doc_id: str
    filename: str
    content: str
    doc_type: str
    entities: list[Entity] = []
    relationships: list[Relationship] = []


class ExtractionResult(BaseModel):
    """LLM entity-extraction output for a single chunk."""

    entities: list[Entity] = []
    relationships: list[Relationship] = []
