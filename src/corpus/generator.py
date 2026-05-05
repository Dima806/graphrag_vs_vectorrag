"""Generate synthetic NordFinance Group financial compliance corpus."""

import hashlib
import json
from pathlib import Path

from loguru import logger

from src.config import get_settings
from src.corpus.schemas import Document, Entity, EntityType, Relationship, RelationshipType

# ---------------------------------------------------------------------------
# Document templates
# ---------------------------------------------------------------------------

_DOCS: list[tuple[str, str, str]] = [
    (
        "nordfinance_annual_report_2024",
        "annual_report",
        """NORDFINANCE GROUP — ANNUAL REPORT 2024

NordFinance Group is a Nordic financial conglomerate headquartered in Copenhagen, Denmark.
The Group comprises four wholly-owned subsidiaries: NordBank A/S, NordInsure A/S,
NordWealth A/S, and NordPay A/S.

Group Chief Executive Officer: Erik Lindqvist
Group Chief Financial Officer: Astrid Bergmann
Group Chief Risk Officer: Lars Henriksen
Chairman of the Board: Margarethe Solvang

In fiscal year 2024, NordFinance Group reported consolidated revenues of DKK 14.2 billion,
up 6.3% year-on-year. Return on equity reached 11.8%. The Group maintained a consolidated
Common Equity Tier 1 (CET1) ratio of 17.6%, well above the regulatory minimum of 10.5%.

NordBank A/S contributed 58% of Group revenues, followed by NordInsure A/S at 22%,
NordWealth A/S at 12%, and NordPay A/S at 8%.

The Group is subject to consolidated supervision by the Danish Financial Supervisory
Authority (Finanstilsynet) and the European Central Bank (ECB) under the Single
Supervisory Mechanism.

Deloitte Nordic served as Group auditor for fiscal year 2024.
""",
    ),
    (
        "nordbank_risk_assessment",
        "risk_report",
        """NORDBANK A/S — RISK ASSESSMENT REPORT 2024

NordBank A/S is the primary banking subsidiary of NordFinance Group, holding a universal
banking licence issued by Finanstilsynet. CEO: Søren Møller. CFO: Camilla Dahl.

Tier 1 Capital Ratio: 18.4% (regulatory minimum: 6%)
Total Capital Ratio: 21.1%
Leverage Ratio: 5.2%
Liquidity Coverage Ratio (LCR): 142%
Net Stable Funding Ratio (NSFR): 118%

MATERIAL RISK FACTORS:
1. Credit Risk — Exposure to Danish commercial real estate sector (DKK 8.4bn).
2. Market Risk — Interest rate sensitivity; 100bp parallel shift impacts NII by DKK 340m.
3. Operational Risk — Legacy core banking system migration risk; estimated DKK 120m exposure.
4. Compliance Risk — AML framework post-FSA remediation order (ref. FSA-2023-NB-004).
5. Concentration Risk — Top 10 borrowers represent 22% of total credit exposure.
6. Liquidity Risk — Funding concentration in short-term wholesale markets.
7. Model Risk — Internal rating model validation overdue for three sub-portfolios.
8. Reputational Risk — Residual impact from 2023 AML sanction.

NordBank is audited by Deloitte Nordic. The bank is regulated by Finanstilsynet and
subject to ECB oversight as part of the NordFinance Group SSM supervision.
""",
    ),
    (
        "nordinsure_compliance_filing",
        "regulatory_filing",
        """NORDINSURE A/S — SOLVENCY II COMPLIANCE FILING Q4 2024

NordInsure A/S is the insurance subsidiary of NordFinance Group, licensed under
Solvency II by Finanstilsynet. CEO: Birthe Kastrup. CFO: Henrik Sørensen.

Solvency Capital Requirement (SCR) ratio: 187% (minimum: 100%)
Minimum Capital Requirement (MCR) ratio: 412%
Technical Provisions: DKK 22.1 billion
Own Funds eligible for SCR coverage: DKK 6.8 billion

NordInsure files quarterly Quantitative Reporting Templates (QRTs) with Finanstilsynet
under the Solvency II Directive (2009/138/EC). The ORSA (Own Risk and Solvency Assessment)
was submitted to Finanstilsynet on 15 March 2024.

Material risk factors: underwriting risk (natural catastrophe exposure, DKK 1.2bn PML),
market risk (equity and spread risk on investment portfolio), counterparty risk.

NordInsure is audited by EY Nordic. The company has not received any regulatory sanctions
in the reporting period.
""",
    ),
    (
        "nordwealth_audit_report",
        "audit_report",
        """NORDWEALTH A/S — INDEPENDENT AUDITOR'S REPORT 2024

To the shareholders of NordWealth A/S

We have audited the financial statements of NordWealth A/S for the year ended 31 December
2024. In our opinion, the financial statements present fairly, in all material respects,
the financial position of NordWealth A/S.

Engagement Partner: Thomas Ravn (Deloitte Nordic)
Audit Firm: Deloitte Nordic, Copenhagen

NordWealth A/S — CEO: Katrina Halvorsen. CFO: Mikkel Strandberg.
Assets Under Management (AUM): DKK 98.4 billion
Fee income: DKK 1.68 billion
Cost-to-income ratio: 62%

Key Audit Matter: Valuation of illiquid alternative investments (DKK 4.2bn, level 3 fair
value). We applied additional procedures including independent third-party valuations for
assets above DKK 50m.

NordWealth is regulated by Finanstilsynet under the UCITS and AIFMD frameworks.
No material misstatements were identified.
""",
    ),
    (
        "nordpay_board_minutes",
        "board_minutes",
        """NORDPAY A/S — BOARD OF DIRECTORS MEETING MINUTES
Date: 14 November 2024

Present:
- Margarethe Solvang (Chair, NordFinance Group Chairman serving on NordPay Board)
- Erik Lindqvist (NordFinance Group CEO, serving on NordPay Board)
- Rasmus Elkjær (Independent Director)
- Ingrid Thorvaldsen (Independent Director)
- Bjørn Christensen (Employee Representative)
- Silje Andersen (CEO, NordPay A/S)

NordPay A/S processes DKK 420 billion in annual payment volumes. The company holds a
Payment Institution licence issued by Finanstilsynet under PSD2.

Items discussed:
1. Q3 2024 financial results: Net revenue DKK 284m, EBITDA DKK 89m.
2. PSD2 strong customer authentication (SCA) compliance — full compliance achieved.
3. SEPA Instant Payments adoption: NordPay joined the SCT Inst scheme in October 2024.
4. KPMG appointed as NordPay statutory auditor from 1 January 2025, replacing Deloitte Nordic.

Rasmus Elkjær also serves on the board of NordBank A/S.
Ingrid Thorvaldsen also serves on the board of NordInsure A/S.
""",
    ),
    (
        "fsa_sanction_nordbank",
        "sanction_notice",
        """FINANSTILSYNET — SUPERVISORY DECISION
Reference: FSA-2023-NB-004
Date: 22 September 2023
Subject: Administrative Sanction — NordBank A/S — AML Framework Deficiencies

Finanstilsynet (the Danish Financial Supervisory Authority) hereby issues the following
supervisory decision against NordBank A/S.

FINDINGS:
Finanstilsynet's on-site inspection conducted in March–April 2023 identified material
deficiencies in NordBank's Anti-Money Laundering (AML) framework, specifically:
(a) Inadequate Customer Due Diligence (CDD) procedures for high-risk correspondent
    banking relationships;
(b) Failure to file timely Suspicious Activity Reports (SARs) in 14 identified cases;
(c) Deficient transaction monitoring system calibration.

SANCTION:
Administrative fine: DKK 25,000,000 (twenty-five million Danish kroner).
NordBank A/S is required to submit a remediation plan within 60 days.

NordBank's CEO Søren Møller acknowledged the findings and confirmed engagement of
external AML consultants to support remediation.
""",
    ),
    (
        "cross_board_membership",
        "governance_report",
        """NORDFINANCE GROUP — CORPORATE GOVERNANCE REPORT 2024: BOARD INTERLOCKS

This report documents officers who serve on multiple boards within the NordFinance Group
and on external bodies, in accordance with CRD IV Article 91 fit-and-proper requirements.

BOARD INTERLOCK REGISTER:

1. Margarethe Solvang
   - Chairman, NordFinance Group Board
   - Board Member, NordPay A/S
   - External: Chairman, Copenhagen Business School Foundation Board

2. Erik Lindqvist
   - CEO, NordFinance Group
   - Board Member, NordPay A/S
   - External: Board Member, Danish Bankers Association

3. Rasmus Elkjær
   - Independent Director, NordPay A/S
   - Independent Director, NordBank A/S
   - External: Board Member, Nordic Capital Partners A/S

4. Ingrid Thorvaldsen
   - Independent Director, NordPay A/S
   - Independent Director, NordInsure A/S
   - External: Advisory Board, Danish Insurance Association

Deloitte Nordic is the auditor for NordFinance Group, NordBank A/S, and NordWealth A/S.
KPMG is the auditor for NordPay A/S (from 2025). EY Nordic audits NordInsure A/S.
""",
    ),
    (
        "auditor_rotation_memo",
        "internal_memo",
        """NORDFINANCE GROUP — INTERNAL MEMORANDUM
To: Group Audit Committee
From: Group CFO Astrid Bergmann
Subject: Auditor Rotation and Appointment — NordPay A/S
Date: 3 October 2024

Per EU Regulation 537/2014 on statutory audit, mandatory auditor rotation applies after
a maximum engagement of 10 years for public interest entities. Deloitte Nordic has served
as NordPay A/S statutory auditor since 2014. Following a competitive tender, the Audit
Committee recommends appointment of KPMG as NordPay A/S statutory auditor effective
1 January 2025.

Historical auditor assignments within NordFinance Group:
- NordFinance Group (consolidated): Deloitte Nordic (2016–present)
- NordBank A/S: Deloitte Nordic (2012–present)
- NordInsure A/S: EY Nordic (2018–present); previously KPMG (2010–2017)
- NordWealth A/S: Deloitte Nordic (2019–present)
- NordPay A/S: Deloitte Nordic (2014–2024); KPMG from 2025

The tender process evaluated EY Nordic, KPMG, and PwC Nordic. KPMG was selected based
on demonstrated expertise in payment services regulation and competitive fee structure.
""",
    ),
    (
        "consolidated_financials",
        "financial_statement",
        """NORDFINANCE GROUP — CONSOLIDATED FINANCIAL HIGHLIGHTS 2024

All figures in DKK millions unless otherwise stated.

GROUP INCOME STATEMENT (2024):
  Net interest income:        8,420
  Net fee and commission:     3,180
  Net trading income:           890
  Other income:                 710
  Total revenue:             14,200
  Operating expenses:        (8,650)
  Loan impairments:            (420)
  Pre-tax profit:             5,130
  Tax expense:               (1,180)
  Net profit:                 3,950

GROUP BALANCE SHEET (31 Dec 2024):
  Total assets:             412,000
  Customer loans:           198,000
  Customer deposits:        164,000
  Total equity:              36,800

SUBSIDIARY KEY METRICS:
NordBank:     Total assets DKK 298bn, Tier 1 ratio 18.4%, ROE 12.1%
NordInsure:   Technical provisions DKK 22.1bn, SCR ratio 187%, combined ratio 93%
NordWealth:   AUM DKK 98.4bn, fee income DKK 1.68bn, cost-income 62%
NordPay:      Payment volumes DKK 420bn, net revenue DKK 1.14bn, EBITDA margin 31%
""",
    ),
    (
        "regulatory_correspondence",
        "regulatory_correspondence",
        """NORDFINANCE GROUP — REGULATORY CORRESPONDENCE LOG 2024

1. ECB Letter (ref. SSM-2024-DNORDFI-0041) dated 12 February 2024
   Subject: SREP outcome — NordFinance Group
   Pillar 2 Requirement (P2R): 1.5% CET1 add-on
   Pillar 2 Guidance (P2G): 0.5% CET1

2. Finanstilsynet Letter (ref. FT-2024-0892) dated 8 April 2024
   Subject: NordBank AML remediation — progress review
   Outcome: Satisfactory progress confirmed. Monitoring continues quarterly.

3. Finanstilsynet Letter (ref. FT-2024-1105) dated 19 June 2024
   Subject: NordInsure ORSA review
   Outcome: No material findings. Next review scheduled Q2 2025.

4. ECB Letter (ref. SSM-2024-DNORDFI-0198) dated 3 October 2024
   Subject: NordFinance Group — climate risk disclosure requirements (EBA/GL/2022/03)
   Action required: Enhanced scenario analysis by 31 March 2025.

Regulated entities: NordBank A/S, NordInsure A/S, NordWealth A/S, NordPay A/S
Regulators: Finanstilsynet, ECB
""",
    ),
    (
        "officer_cv_summaries",
        "biographical",
        """NORDFINANCE GROUP — SENIOR OFFICER BIOGRAPHICAL SUMMARIES 2024

ERIK LINDQVIST — Group CEO
MSc Finance, Stockholm School of Economics. Previously CEO of Skandia Bank (2014–2019),
CFO of Nordea Group (2009–2014). Board member NordPay A/S, Danish Bankers Association.

ASTRID BERGMANN — Group CFO
MSc Accounting, Copenhagen Business School. Previously CFO Tryg A/S (2016–2021),
Partner PwC Nordic (2010–2016). CFA charterholder.

LARS HENRIKSEN — Group CRO
MSc Mathematics, University of Copenhagen. Previously Head of Market Risk, Danske Bank
(2012–2019). Published author on credit risk modelling.

SØREN MØLLER — NordBank CEO
MSc Economics, Aarhus University. Previously Deputy CEO NordBank (2016–2020),
Head of Corporate Banking Jyske Bank (2011–2016). Board member, Finance Denmark.

CAMILLA DAHL — NordBank CFO
MSc Finance, CBS. Previously VP Finance, Nykredit (2015–2020).

KATRINA HALVORSEN — NordWealth CEO
MBA, INSEAD. Previously MD, BlackRock Nordic (2013–2019).

RASMUS ELKJÆR — Independent Director (NordBank, NordPay)
MSc Law, University of Copenhagen. Partner, Kromann Reumert (2008–2018).
Board NordBank A/S and NordPay A/S simultaneously since 2019.

MARGARETHE SOLVANG — Group Board Chairman
MSc Economics, Norwegian School of Economics. Former Governor, Norges Bank (2008–2014).
""",
    ),
    (
        "risk_taxonomy",
        "reference",
        """NORDFINANCE GROUP — ENTERPRISE RISK TAXONOMY 2024

This document defines the 15 risk categories recognised across all NordFinance subsidiaries.

1.  Credit Risk — Risk of loss from borrower/counterparty default.
2.  Market Risk — Risk from adverse movements in interest rates, FX, equities, commodities.
3.  Operational Risk — Risk from inadequate processes, systems, people, or external events.
4.  Liquidity Risk — Risk of inability to meet financial obligations as they fall due.
5.  Compliance Risk — Risk of regulatory penalties from failure to comply with laws/rules.
6.  Reputational Risk — Risk of stakeholder confidence loss affecting franchise value.
7.  Strategic Risk — Risk from adverse business decisions or failure to implement strategy.
8.  Model Risk — Risk of material error due to incorrect model development or application.
9.  Concentration Risk — Risk from exposure to a single counterparty, sector, or geography.
10. Underwriting Risk — Insurance-specific risk from mispriced policies or claims volatility.
11. Cyber Risk — Risk from IT security incidents, data breaches, or ransomware attacks.
12. Climate Risk — Physical and transition risks from climate change and policy responses.
13. Counterparty Credit Risk — Specific risk in derivative and SFT exposures.
14. Interest Rate Risk in the Banking Book (IRRBB) — NII and EVE sensitivity.
15. AML/Financial Crime Risk — Risk of involvement in money laundering or terrorist financing.

Each risk category is owned by a named Risk Owner and reviewed quarterly by the Group CRO.
""",
    ),
]

# ---------------------------------------------------------------------------
# Ground-truth entity and relationship catalogue
# ---------------------------------------------------------------------------

_ENTITIES: list[Entity] = [
    Entity(
        name="NordFinance Group",
        type=EntityType.COMPANY,
        description="Nordic financial conglomerate, parent company",
    ),
    Entity(
        name="NordBank A/S",
        type=EntityType.COMPANY,
        description="Banking subsidiary of NordFinance Group",
    ),
    Entity(
        name="NordInsure A/S",
        type=EntityType.COMPANY,
        description="Insurance subsidiary of NordFinance Group",
    ),
    Entity(
        name="NordWealth A/S",
        type=EntityType.COMPANY,
        description="Wealth management subsidiary of NordFinance Group",
    ),
    Entity(
        name="NordPay A/S",
        type=EntityType.COMPANY,
        description="Payment processing subsidiary of NordFinance Group",
    ),
    Entity(
        name="Erik Lindqvist", type=EntityType.PERSON, description="Group CEO of NordFinance Group"
    ),
    Entity(
        name="Astrid Bergmann",
        type=EntityType.PERSON,
        description="Group CFO of NordFinance Group",
    ),
    Entity(
        name="Lars Henriksen", type=EntityType.PERSON, description="Group CRO of NordFinance Group"
    ),
    Entity(
        name="Margarethe Solvang",
        type=EntityType.PERSON,
        description="Chairman of the Board, NordFinance Group",
    ),
    Entity(name="Søren Møller", type=EntityType.PERSON, description="CEO of NordBank A/S"),
    Entity(name="Camilla Dahl", type=EntityType.PERSON, description="CFO of NordBank A/S"),
    Entity(name="Birthe Kastrup", type=EntityType.PERSON, description="CEO of NordInsure A/S"),
    Entity(name="Katrina Halvorsen", type=EntityType.PERSON, description="CEO of NordWealth A/S"),
    Entity(name="Silje Andersen", type=EntityType.PERSON, description="CEO of NordPay A/S"),
    Entity(
        name="Rasmus Elkjær",
        type=EntityType.PERSON,
        description="Independent Director on NordBank and NordPay boards",
    ),
    Entity(
        name="Ingrid Thorvaldsen",
        type=EntityType.PERSON,
        description="Independent Director on NordPay and NordInsure boards",
    ),
    Entity(
        name="Deloitte Nordic",
        type=EntityType.AUDIT_FIRM,
        description="Auditor for NordFinance Group, NordBank, NordWealth",
    ),
    Entity(name="EY Nordic", type=EntityType.AUDIT_FIRM, description="Auditor for NordInsure A/S"),
    Entity(
        name="KPMG", type=EntityType.AUDIT_FIRM, description="Auditor for NordPay A/S from 2025"
    ),
    Entity(
        name="Finanstilsynet",
        type=EntityType.REGULATOR,
        description="Danish Financial Supervisory Authority",
    ),
    Entity(
        name="ECB", type=EntityType.REGULATOR, description="European Central Bank, SSM supervisor"
    ),
    Entity(
        name="Credit Risk", type=EntityType.RISK_FACTOR, description="Risk of borrower default"
    ),
    Entity(
        name="Market Risk",
        type=EntityType.RISK_FACTOR,
        description="Risk from adverse market movements",
    ),
    Entity(
        name="Operational Risk",
        type=EntityType.RISK_FACTOR,
        description="Risk from process/system failures",
    ),
    Entity(
        name="Compliance Risk",
        type=EntityType.RISK_FACTOR,
        description="Risk of regulatory penalties",
    ),
    Entity(
        name="AML/Financial Crime Risk",
        type=EntityType.RISK_FACTOR,
        description="Money laundering and financial crime risk",
    ),
    Entity(
        name="Tier 1 Capital Ratio",
        type=EntityType.FINANCIAL_METRIC,
        description="NordBank Tier 1 ratio 18.4%",
    ),
    Entity(
        name="SCR Ratio", type=EntityType.FINANCIAL_METRIC, description="NordInsure SCR ratio 187%"
    ),
    Entity(name="AUM", type=EntityType.FINANCIAL_METRIC, description="NordWealth AUM DKK 98.4bn"),
    Entity(
        name="NordBank Risk Assessment 2024",
        type=EntityType.REPORT,
        description="NordBank annual risk report",
    ),
]

_RELATIONSHIPS: list[Relationship] = [
    Relationship(
        source="NordFinance Group", target="NordBank A/S", type=RelationshipType.HAS_SUBSIDIARY
    ),
    Relationship(
        source="NordFinance Group", target="NordInsure A/S", type=RelationshipType.HAS_SUBSIDIARY
    ),
    Relationship(
        source="NordFinance Group", target="NordWealth A/S", type=RelationshipType.HAS_SUBSIDIARY
    ),
    Relationship(
        source="NordFinance Group", target="NordPay A/S", type=RelationshipType.HAS_SUBSIDIARY
    ),
    Relationship(
        source="NordFinance Group",
        target="Erik Lindqvist",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CEO"},
    ),
    Relationship(
        source="NordFinance Group",
        target="Astrid Bergmann",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CFO"},
    ),
    Relationship(
        source="NordFinance Group",
        target="Margarethe Solvang",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "Chairman"},
    ),
    Relationship(
        source="NordBank A/S",
        target="Søren Møller",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CEO"},
    ),
    Relationship(
        source="NordBank A/S",
        target="Camilla Dahl",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CFO"},
    ),
    Relationship(
        source="NordInsure A/S",
        target="Birthe Kastrup",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CEO"},
    ),
    Relationship(
        source="NordWealth A/S",
        target="Katrina Halvorsen",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CEO"},
    ),
    Relationship(
        source="NordPay A/S",
        target="Silje Andersen",
        type=RelationshipType.HAS_OFFICER,
        properties={"role": "CEO"},
    ),
    Relationship(
        source="Rasmus Elkjær", target="NordBank A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="Rasmus Elkjær", target="NordPay A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="Ingrid Thorvaldsen", target="NordPay A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="Ingrid Thorvaldsen", target="NordInsure A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="Margarethe Solvang", target="NordPay A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="Erik Lindqvist", target="NordPay A/S", type=RelationshipType.SERVES_ON_BOARD
    ),
    Relationship(
        source="NordFinance Group", target="Deloitte Nordic", type=RelationshipType.AUDITED_BY
    ),
    Relationship(
        source="NordBank A/S", target="Deloitte Nordic", type=RelationshipType.AUDITED_BY
    ),
    Relationship(source="NordInsure A/S", target="EY Nordic", type=RelationshipType.AUDITED_BY),
    Relationship(
        source="NordWealth A/S", target="Deloitte Nordic", type=RelationshipType.AUDITED_BY
    ),
    Relationship(source="NordPay A/S", target="KPMG", type=RelationshipType.AUDITED_BY),
    Relationship(
        source="NordBank A/S", target="Finanstilsynet", type=RelationshipType.REGULATED_BY
    ),
    Relationship(
        source="NordInsure A/S", target="Finanstilsynet", type=RelationshipType.REGULATED_BY
    ),
    Relationship(
        source="NordWealth A/S", target="Finanstilsynet", type=RelationshipType.REGULATED_BY
    ),
    Relationship(
        source="NordPay A/S", target="Finanstilsynet", type=RelationshipType.REGULATED_BY
    ),
    Relationship(source="NordFinance Group", target="ECB", type=RelationshipType.REGULATED_BY),
    Relationship(
        source="Finanstilsynet",
        target="NordBank A/S",
        type=RelationshipType.ISSUED_SANCTION,
        properties={"date": "2023-09-22", "amount": 25000000, "reference": "FSA-2023-NB-004"},
    ),
    Relationship(
        source="NordBank A/S",
        target="NordBank Risk Assessment 2024",
        type=RelationshipType.FILED_REPORT,
    ),
    Relationship(
        source="NordBank Risk Assessment 2024",
        target="Credit Risk",
        type=RelationshipType.MENTIONS_RISK,
    ),
    Relationship(
        source="NordBank Risk Assessment 2024",
        target="AML/Financial Crime Risk",
        type=RelationshipType.MENTIONS_RISK,
    ),
    Relationship(
        source="NordBank A/S",
        target="Tier 1 Capital Ratio",
        type=RelationshipType.HAS_METRIC,
        properties={"value": 18.4, "unit": "%", "period": "2024"},
    ),
    Relationship(
        source="NordInsure A/S",
        target="SCR Ratio",
        type=RelationshipType.HAS_METRIC,
        properties={"value": 187.0, "unit": "%", "period": "2024"},
    ),
    Relationship(
        source="NordWealth A/S",
        target="AUM",
        type=RelationshipType.HAS_METRIC,
        properties={"value": 98400.0, "unit": "DKK_m", "period": "2024"},
    ),
]


def _doc_id(slug: str) -> str:
    """Stable SHA256-derived document ID."""
    return hashlib.sha256(slug.encode()).hexdigest()[:16]


def generate_corpus() -> list[Document]:
    """Generate all 12 NordFinance synthetic documents with ground-truth annotations."""
    docs = []
    for slug, doc_type, content in _DOCS:
        docs.append(
            Document(
                doc_id=_doc_id(slug),
                filename=f"{slug}.txt",
                content=content.strip(),
                doc_type=doc_type,
                entities=_ENTITIES,
                relationships=_RELATIONSHIPS,
            )
        )
    return docs


def save_corpus(docs: list[Document]) -> None:
    """Save document text files and ground-truth JSON to data/corpus/."""
    out_dir = Path(get_settings().corpus.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for doc in docs:
        (out_dir / doc.filename).write_text(doc.content, encoding="utf-8")

    entity_gt = [e.model_dump() for e in _ENTITIES]
    rel_gt = [r.model_dump() for r in _RELATIONSHIPS]
    (out_dir / "ground_truth_entities.json").write_text(
        json.dumps(entity_gt, indent=2), encoding="utf-8"
    )
    (out_dir / "ground_truth_relationships.json").write_text(
        json.dumps(rel_gt, indent=2), encoding="utf-8"
    )
    logger.info(f"Saved {len(docs)} documents and ground-truth to {out_dir}")


if __name__ == "__main__":
    save_corpus(generate_corpus())
