"""Schemas for facts extracted from document chunks by Claude.

Each fact category has different required fields, but all share a
common source-tracking pattern: doc_id, page, excerpt. This is how
every claim in the final memo traces back to a specific location in
the source document.

Financial figures are RAW REPORTED NUMBERS only — no derived values.
Growth rates, margins, and ratios are calculated by code in finance.py.
"""

from enum import Enum
from pydantic import BaseModel


class Confidence(str, Enum):
    """How confident the extraction is."""

    HIGH = "high"  # explicitly stated in the document
    MEDIUM = "medium"  # clearly implied or requires minor interpretation
    LOW = "low"  # inferred from context, not directly stated


# -- Source tracking (shared by all fact types) --


class SourceRef(BaseModel):
    """Where in the source document this fact comes from."""

    doc_id: str
    page: int
    excerpt: str  # short quote from the document supporting the fact


# -- Fact categories --


class FinancialFigure(BaseModel):
    """A single reported financial figure (revenue, profit, KPI, etc.).

    Only raw numbers as stated in the document. No calculations.
    """

    label: str  # e.g. "Revenue", "Operating profit", "ARPR"
    value: float  # the number (e.g. 624.3)
    unit: str  # e.g. "£m", "pence", "%", "million"
    period: str  # e.g. "FY2026", "H1 FY2026", "year ended 31 March 2026"
    note_ref: str | None = None  # note number if referenced (e.g. "5")
    confidence: Confidence
    source: SourceRef


class BusinessFact(BaseModel):
    """A factual statement about the business (not a number).

    Examples: what the company does, its products, customers, segments,
    geography, number of employees, corporate structure.
    """

    category: str  # e.g. "business_description", "products", "customers",
    #      "segments", "geography", "corporate_structure"
    statement: str  # the fact in plain English
    confidence: Confidence
    source: SourceRef


class RiskDisclosure(BaseModel):
    """A risk mentioned or implied in the document."""

    description: str  # what the risk is
    risk_type: str  # "disclosed" (company states it) or "inferred" (implied)
    confidence: Confidence
    source: SourceRef


class StrategicItem(BaseModel):
    """A strategic priority, initiative, or forward-looking statement."""

    description: str
    item_type: str  # e.g. "priority", "initiative", "target", "guidance"
    confidence: Confidence
    source: SourceRef


class ManagementCommentary(BaseModel):
    """A notable management statement, outlook, or qualitative commentary."""

    statement: str
    topic: str  # e.g. "outlook", "market_conditions", "capital_allocation"
    confidence: Confidence
    source: SourceRef


# -- Container for all facts from a single chunk --


class ExtractedFacts(BaseModel):
    """All facts extracted from a single chunk of text.

    This is the schema Claude must return when processing a chunk.
    chunk_id is set by extract.py after the fact, not by the model.
    """

    financial_figures: list[FinancialFigure] = []
    business_facts: list[BusinessFact] = []
    risk_disclosures: list[RiskDisclosure] = []
    strategic_items: list[StrategicItem] = []
    management_commentary: list[ManagementCommentary] = []
