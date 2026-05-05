"""30-question evaluation bank: 15 single-hop, 15 multi-hop."""

from dataclasses import dataclass, field

SINGLE_HOP = "single_hop"
MULTI_HOP = "multi_hop"


@dataclass
class EvalQuestion:
    """One evaluation question with ground-truth metadata."""

    question: str
    query_type: str
    gold_answer: str
    required_entities: list[str] = field(default_factory=list)
    required_relationships: list[str] = field(default_factory=list)


QUESTION_BANK: list[EvalQuestion] = [
    # ── Single-hop (15) ─────────────────────────────────────────────────────
    EvalQuestion(
        question="What was NordBank's Tier 1 capital ratio in 2024?",
        query_type=SINGLE_HOP,
        gold_answer="NordBank's Tier 1 capital ratio was 18.4% in 2024.",
        required_entities=["NordBank A/S"],
    ),
    EvalQuestion(
        question="Who is the CEO of NordInsure A/S?",
        query_type=SINGLE_HOP,
        gold_answer="The CEO of NordInsure A/S is Birthe Kastrup.",
        required_entities=["NordInsure A/S", "Birthe Kastrup"],
    ),
    EvalQuestion(
        question="Which audit firm prepared NordWealth's 2024 audit report?",
        query_type=SINGLE_HOP,
        gold_answer="Deloitte Nordic prepared NordWealth's 2024 audit report.",
        required_entities=["NordWealth A/S", "Deloitte Nordic"],
        required_relationships=["AUDITED_BY"],
    ),
    EvalQuestion(
        question="What was NordFinance Group's consolidated CET1 ratio in 2024?",
        query_type=SINGLE_HOP,
        gold_answer="NordFinance Group's consolidated CET1 ratio was 17.6% in 2024.",
        required_entities=["NordFinance Group"],
    ),
    EvalQuestion(
        question="What regulator issued a sanction against NordBank in 2023?",
        query_type=SINGLE_HOP,
        gold_answer="Finanstilsynet issued an administrative sanction against NordBank in September 2023.",
        required_entities=["NordBank A/S", "Finanstilsynet"],
        required_relationships=["ISSUED_SANCTION"],
    ),
    EvalQuestion(
        question="What was the amount of the FSA sanction against NordBank?",
        query_type=SINGLE_HOP,
        gold_answer="The FSA sanction against NordBank was DKK 25,000,000.",
        required_entities=["NordBank A/S", "Finanstilsynet"],
    ),
    EvalQuestion(
        question="What is NordInsure's Solvency Capital Requirement ratio?",
        query_type=SINGLE_HOP,
        gold_answer="NordInsure's SCR ratio is 187%.",
        required_entities=["NordInsure A/S"],
    ),
    EvalQuestion(
        question="Who is NordFinance Group's Group CFO?",
        query_type=SINGLE_HOP,
        gold_answer="Astrid Bergmann is the Group CFO of NordFinance Group.",
        required_entities=["NordFinance Group", "Astrid Bergmann"],
    ),
    EvalQuestion(
        question="What are the four subsidiaries of NordFinance Group?",
        query_type=SINGLE_HOP,
        gold_answer="The four subsidiaries are NordBank A/S, NordInsure A/S, NordWealth A/S, and NordPay A/S.",
        required_entities=[
            "NordFinance Group",
            "NordBank A/S",
            "NordInsure A/S",
            "NordWealth A/S",
            "NordPay A/S",
        ],
        required_relationships=["HAS_SUBSIDIARY"],
    ),
    EvalQuestion(
        question="Which auditor is assigned to NordInsure A/S?",
        query_type=SINGLE_HOP,
        gold_answer="EY Nordic is the auditor for NordInsure A/S.",
        required_entities=["NordInsure A/S", "EY Nordic"],
        required_relationships=["AUDITED_BY"],
    ),
    EvalQuestion(
        question="What was NordWealth's assets under management in 2024?",
        query_type=SINGLE_HOP,
        gold_answer="NordWealth's assets under management were DKK 98.4 billion in 2024.",
        required_entities=["NordWealth A/S"],
    ),
    EvalQuestion(
        question="What is the reference number of the FSA sanction against NordBank?",
        query_type=SINGLE_HOP,
        gold_answer="The FSA sanction reference is FSA-2023-NB-004.",
        required_entities=["NordBank A/S", "Finanstilsynet"],
    ),
    EvalQuestion(
        question="Who chairs the NordFinance Group board?",
        query_type=SINGLE_HOP,
        gold_answer="Margarethe Solvang is Chairman of the NordFinance Group Board.",
        required_entities=["NordFinance Group", "Margarethe Solvang"],
    ),
    EvalQuestion(
        question="What payment volume did NordPay process annually?",
        query_type=SINGLE_HOP,
        gold_answer="NordPay processed DKK 420 billion in annual payment volumes.",
        required_entities=["NordPay A/S"],
    ),
    EvalQuestion(
        question="Which risk factor led to the FSA sanction of NordBank?",
        query_type=SINGLE_HOP,
        gold_answer="AML framework deficiencies, specifically inadequate CDD and failure to file timely SARs.",
        required_entities=["NordBank A/S", "AML/Financial Crime Risk"],
    ),
    # ── Multi-hop (15) ──────────────────────────────────────────────────────
    EvalQuestion(
        question="Which officers serve on boards of companies that share the same auditor?",
        query_type=MULTI_HOP,
        gold_answer=(
            "Rasmus Elkjær serves on NordBank and NordPay boards; both were audited by Deloitte Nordic "
            "(NordPay until 2024). Margarethe Solvang and Erik Lindqvist serve on NordPay board, "
            "which shares Deloitte Nordic with NordBank and NordWealth."
        ),
        required_entities=["Rasmus Elkjær", "NordBank A/S", "NordPay A/S", "Deloitte Nordic"],
        required_relationships=["SERVES_ON_BOARD", "AUDITED_BY"],
    ),
    EvalQuestion(
        question="List all subsidiaries regulated by Finanstilsynet that were also audited by Deloitte Nordic.",
        query_type=MULTI_HOP,
        gold_answer="NordBank A/S and NordWealth A/S are regulated by Finanstilsynet and audited by Deloitte Nordic.",
        required_entities=["NordBank A/S", "NordWealth A/S", "Finanstilsynet", "Deloitte Nordic"],
        required_relationships=["REGULATED_BY", "AUDITED_BY"],
    ),
    EvalQuestion(
        question="Which board members of NordPay also served at companies that received FSA sanctions?",
        query_type=MULTI_HOP,
        gold_answer=(
            "Rasmus Elkjær serves on NordPay board and also on NordBank board. "
            "NordBank received a Finanstilsynet sanction in 2023."
        ),
        required_entities=["NordPay A/S", "NordBank A/S", "Rasmus Elkjær", "Finanstilsynet"],
        required_relationships=["SERVES_ON_BOARD", "ISSUED_SANCTION"],
    ),
    EvalQuestion(
        question="What risk factors are mentioned in reports filed by companies audited by Deloitte Nordic?",
        query_type=MULTI_HOP,
        gold_answer="Credit Risk, Operational Risk, Compliance Risk, and AML/Financial Crime Risk are mentioned in NordBank's risk report, which is filed by a Deloitte Nordic-audited company.",
        required_entities=[
            "NordBank A/S",
            "Deloitte Nordic",
            "Credit Risk",
            "AML/Financial Crime Risk",
        ],
        required_relationships=["AUDITED_BY", "FILED_REPORT", "MENTIONS_RISK"],
    ),
    EvalQuestion(
        question="Which subsidiaries share board members who also served during a regulatory sanction?",
        query_type=MULTI_HOP,
        gold_answer="NordBank A/S (sanctioned by Finanstilsynet in 2023) and NordPay A/S share Rasmus Elkjær as a board member.",
        required_entities=["NordBank A/S", "NordPay A/S", "Rasmus Elkjær", "Finanstilsynet"],
        required_relationships=["SERVES_ON_BOARD", "ISSUED_SANCTION"],
    ),
    EvalQuestion(
        question="Who are all the officers connected to companies regulated by both Finanstilsynet and ECB?",
        query_type=MULTI_HOP,
        gold_answer="NordFinance Group is regulated by ECB; Erik Lindqvist (CEO) and Astrid Bergmann (CFO) are Group officers.",
        required_entities=["NordFinance Group", "ECB", "Erik Lindqvist", "Astrid Bergmann"],
        required_relationships=["REGULATED_BY", "HAS_OFFICER"],
    ),
    EvalQuestion(
        question="Which auditor has the most subsidiaries of NordFinance Group as clients?",
        query_type=MULTI_HOP,
        gold_answer="Deloitte Nordic audits NordFinance Group, NordBank A/S, and NordWealth A/S — the most clients.",
        required_entities=[
            "Deloitte Nordic",
            "NordBank A/S",
            "NordWealth A/S",
            "NordFinance Group",
        ],
        required_relationships=["AUDITED_BY"],
    ),
    EvalQuestion(
        question="Which officers serve on multiple NordFinance subsidiary boards simultaneously?",
        query_type=MULTI_HOP,
        gold_answer="Rasmus Elkjær (NordBank + NordPay), Ingrid Thorvaldsen (NordPay + NordInsure), Margarethe Solvang and Erik Lindqvist (both NordPay board).",
        required_entities=[
            "Rasmus Elkjær",
            "Ingrid Thorvaldsen",
            "Margarethe Solvang",
            "Erik Lindqvist",
        ],
        required_relationships=["SERVES_ON_BOARD"],
    ),
    EvalQuestion(
        question="What companies are connected to NordBank through shared board members?",
        query_type=MULTI_HOP,
        gold_answer="NordPay A/S is connected to NordBank through Rasmus Elkjær, who serves on both boards.",
        required_entities=["NordBank A/S", "NordPay A/S", "Rasmus Elkjær"],
        required_relationships=["SERVES_ON_BOARD"],
    ),
    EvalQuestion(
        question="Which subsidiaries that have a Tier 1 capital metric are regulated by Finanstilsynet?",
        query_type=MULTI_HOP,
        gold_answer="NordBank A/S is regulated by Finanstilsynet and has the Tier 1 Capital Ratio metric (18.4%).",
        required_entities=["NordBank A/S", "Finanstilsynet", "Tier 1 Capital Ratio"],
        required_relationships=["REGULATED_BY", "HAS_METRIC"],
    ),
    EvalQuestion(
        question="List the chain from ECB supervision to a specific risk factor at a NordFinance subsidiary.",
        query_type=MULTI_HOP,
        gold_answer="ECB supervises NordFinance Group → NordBank A/S (subsidiary) → filed NordBank Risk Assessment 2024 → mentions Credit Risk.",
        required_entities=["ECB", "NordFinance Group", "NordBank A/S", "Credit Risk"],
        required_relationships=["REGULATED_BY", "HAS_SUBSIDIARY", "FILED_REPORT", "MENTIONS_RISK"],
    ),
    EvalQuestion(
        question="Which CEO leads a subsidiary audited by EY Nordic?",
        query_type=MULTI_HOP,
        gold_answer="Birthe Kastrup is CEO of NordInsure A/S, which is audited by EY Nordic.",
        required_entities=["NordInsure A/S", "EY Nordic", "Birthe Kastrup"],
        required_relationships=["AUDITED_BY", "HAS_OFFICER"],
    ),
    EvalQuestion(
        question="Which sanction-receiving subsidiary shares its auditor with another subsidiary, and who are that auditor's other clients?",
        query_type=MULTI_HOP,
        gold_answer="NordBank (sanctioned, audited by Deloitte Nordic) shares its auditor with NordFinance Group and NordWealth A/S.",
        required_entities=["NordBank A/S", "Deloitte Nordic", "NordWealth A/S", "Finanstilsynet"],
        required_relationships=["ISSUED_SANCTION", "AUDITED_BY"],
    ),
    EvalQuestion(
        question="Which person is connected to NordBank through a board role and to NordPay through another board role?",
        query_type=MULTI_HOP,
        gold_answer="Rasmus Elkjær serves as Independent Director on both NordBank A/S and NordPay A/S boards.",
        required_entities=["Rasmus Elkjær", "NordBank A/S", "NordPay A/S"],
        required_relationships=["SERVES_ON_BOARD"],
    ),
    EvalQuestion(
        question="Which subsidiaries are connected through an officer who also chairs the parent company board?",
        query_type=MULTI_HOP,
        gold_answer="Margarethe Solvang chairs NordFinance Group and serves on NordPay A/S board, linking the parent with NordPay.",
        required_entities=["Margarethe Solvang", "NordFinance Group", "NordPay A/S"],
        required_relationships=["HAS_OFFICER", "SERVES_ON_BOARD"],
    ),
]


def single_hop_questions() -> list[EvalQuestion]:
    """Return only single-hop questions from the bank."""
    return [q for q in QUESTION_BANK if q.query_type == SINGLE_HOP]


def multi_hop_questions() -> list[EvalQuestion]:
    """Return only multi-hop questions from the bank."""
    return [q for q in QUESTION_BANK if q.query_type == MULTI_HOP]
