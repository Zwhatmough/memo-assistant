"""Schemas for Milestone 4: fact classification and analytical synthesis.

Two separate outputs, both schema-validated:
1. ClassificationBatch — per-fact relevance rating and memo-section mapping.
2. Analytics — the full analytical layer (strengths, risks, etc.)
   where every item must either cite fact_ids or declare inference=True.
"""

from pydantic import BaseModel, Field


# ── Per-fact classification ─────────────────────────────────────────────────────

MEMO_SECTIONS = [
    "business_overview",
    "financial_performance",
    "strategy",
    "risks",
    "management",
    "investment_case",
]


class FactClassification(BaseModel):
    """Classification output for a single fact."""
    id: str                  # matches the id assigned in classify.py
    relevance: int           # 1–5; 5 = headline, 1 = exclude
    memo_section: str        # one of MEMO_SECTIONS
    rationale: str           # one sentence explaining the classification


class ClassificationBatch(BaseModel):
    """All fact classifications from a single API call."""
    classifications: list[FactClassification]


# ── Analytical synthesis ────────────────────────────────────────────────────────

class AnalyticItem(BaseModel):
    """A single analytical point in the memo.

    Every item must either cite fact_ids (verifiable) or set
    inference=True (explicitly flagged as the model's judgement).
    Items cannot be both empty fact_ids and inference=False.
    """
    statement: str
    fact_ids: list[str] = Field(default_factory=list)
    inference: bool = False
    confidence: str          # "high" | "medium" | "low"

    def model_post_init(self, __context):
        if not self.fact_ids and not self.inference:
            raise ValueError(
                f"AnalyticItem must either cite fact_ids or set inference=True. "
                f"Statement: {self.statement[:60]}"
            )


class RiskItem(BaseModel):
    """A risk item with a mandatory risk_type."""
    statement: str
    risk_type: str           # "disclosed" | "inferred" | "needs_investigation"
    fact_ids: list[str] = Field(default_factory=list)
    inference: bool = False
    confidence: str

    def model_post_init(self, __context):
        valid_types = {"disclosed", "inferred", "needs_investigation"}
        if self.risk_type not in valid_types:
            raise ValueError(f"risk_type must be one of {valid_types}, got '{self.risk_type}'")
        if not self.fact_ids and not self.inference:
            raise ValueError(
                f"RiskItem must either cite fact_ids or set inference=True. "
                f"Statement: {self.statement[:60]}"
            )


class Analytics(BaseModel):
    """Full analytical synthesis output."""
    strengths: list[AnalyticItem]
    risks: list[RiskItem]
    value_drivers: list[AnalyticItem]
    bull_case: list[AnalyticItem]
    bear_case: list[AnalyticItem]
    diligence_questions: list[AnalyticItem]
