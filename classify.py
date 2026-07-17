"""Milestone 4: fact classification and analytical synthesis.

Two-stage Claude pipeline — no raw document access. Inputs are:
  output/validated_facts.json — the verified extracted facts
  output/financials.json      — deterministic cross-checks and growth metrics

Stage 1: Per-fact classification (one batch call to claude-sonnet-5).
  Each verified fact gets a relevance score (1–5) and a memo section.

Stage 2: Analytical synthesis (one call to claude-sonnet-5).
  High-relevance facts → strengths, risks, value drivers, bull/bear case,
  diligence questions. Every item must cite fact_ids or declare inference=True.

Outputs output/classified_facts.json.

Usage:
    python classify.py                       # uses default paths, runs cost check first
    python classify.py --dry-run             # estimate cost only, no API calls
"""

import argparse
import json
import os
import sys
import time

from dotenv import load_dotenv
load_dotenv()

from llm import call_llm, estimate_cost, ANALYSIS_MODEL
from schemas.classify import ClassificationBatch, Analytics, MEMO_SECTIONS

# ── Standard risk-register taxonomy for relevance floor (Change 1 — V2) ───────
#
# When the AI classifier rates formal risk_disclosures facts as relevance 2
# (peripheral), important but diffuse corporate risk categories (cyber, climate,
# third-party, etc.) are excluded from synthesis. This taxonomy defines
# universally-material risk categories from standard frameworks (ISO 31000,
# COSO ERM, TCFD) so that any formally-disclosed fact matching one of these
# categories is guaranteed relevance ≥ 3 (contextual) regardless of how
# "interesting" it appears relative to more distinctive business-specific risks.
#
# These terms are derived from standard risk management frameworks, NOT from
# the evaluation gold set. Generalisability to a second company has not yet
# been tested (noted in BUILD_LOG.md).
RISK_REGISTER_TAXONOMY: dict[str, list[str]] = {
    # ISO 27001 / NIST CSF categories
    "cyber_it_security": [
        "cyber", "cybersecurity", "data breach", "malware", "ransomware",
        "it system", "it infrastructure", "information security", "data loss",
        "platform outage", "system failure", "data protection", "gdpr",
        "privacy", "hacking", "phishing", "incident response",
    ],
    # ISO 28001 / COSO supply chain
    "third_party_supply_chain": [
        "third party", "third-party", "supplier", "supply chain",
        "outsourcing", "vendor", "partner depend", "cloud provider",
        "critical supplier", "service provider", "outsource", "reliant on",
        "reliance on third",
    ],
    # TCFD / GRI environmental
    "climate_environmental": [
        "climate", "carbon", "emission", "ghg", "greenhouse gas",
        "net zero", "environmental", "sustainability", "transition risk",
        "physical risk", "tcfd", "electric vehicle", "ev transition",
        "ice to ev", "scope 1", "scope 2", "scope 3",
    ],
    # FCA / SEC / EU regulatory
    "regulatory_compliance": [
        "regulatory", "regulation", "compliance", "fca",
        "financial conduct", "legislation", "legal risk", "licence",
        "authorisation", "conduct risk", "consumer protection",
        "financial crime", "money laundering", "aml", "sanctions",
        "competition law", "antitrust", "dmcc",
    ],
    # Reputational risk (standard ERM category)
    "brand_reputation": [
        "brand", "reputation", "reputational", "fraud",
        "misleading", "public perception", "media risk",
        "scandal", "advertising standards", "negative publicity",
        "mis-selling", "customer trust",
    ],
    # People / HR risk
    "people_talent": [
        "employee engagement", "talent risk", "key person", "succession",
        "industrial action", "whistleblowing", "people risk",
        "workforce planning", "health and safety",
    ],
    # Business continuity / operational resilience
    "business_continuity": [
        "business continuity", "disaster recovery", "operational resilience",
        "pandemic", "operational disruption", "bcp",
        "recovery time", "site loss",
    ],
    # Financial / market risk
    "financial_market_risk": [
        "interest rate", "foreign exchange", "fx risk", "liquidity risk",
        "credit risk", "counterparty", "market risk", "financing cost",
        "debt covenant", "refinancing", "leverage risk",
    ],
    # Macro / geopolitical
    "geopolitical_macro": [
        "geopolitical", "political risk", "sanctions", "trade war",
        "tariff", "conflict", "war", "macroeconomic", "recession",
        "economic downturn", "fiscal policy", "inflation risk",
    ],
}

# Flatten all taxonomy terms for efficient lookup
_RISK_TAXONOMY_TERMS: list[str] = [
    term
    for terms in RISK_REGISTER_TAXONOMY.values()
    for term in terms
]


def apply_risk_floor(classified: list[dict], floor: int = 3) -> tuple[list[dict], int]:
    """Bump risk_disclosures facts in the 'risks' section from relevance ≤2 to floor.

    This prevents the classifier from systematically under-rating formal
    corporate risk register items relative to more distinctive business-specific
    risks. Only applies when the fact's label matches one of the standard
    risk taxonomy terms defined in RISK_REGISTER_TAXONOMY.

    Returns the modified list and the count of facts adjusted.
    """
    adjusted = 0
    for fact in classified:
        if fact.get("category") != "risk_disclosures":
            continue
        if fact.get("memo_section") != "risks":
            continue
        if fact.get("relevance", 0) >= floor:
            continue

        label_lower = fact.get("label", "").lower()
        if any(term in label_lower for term in _RISK_TAXONOMY_TERMS):
            fact["relevance"] = floor
            fact["rationale"] = (
                fact.get("rationale", "") +
                " [V2: relevance floored to 3 — matches standard risk-register taxonomy]"
            )
            adjusted += 1

    return classified, adjusted


# All categories of facts that can be classified
FACT_CATEGORIES = [
    "financial_figures",
    "business_facts",
    "risk_disclosures",
    "strategic_items",
    "management_commentary",
]

# Facts with relevance >= this threshold are passed to the synthesis stage.
SYNTHESIS_RELEVANCE_THRESHOLD = 3

# Pre-run cost guard
MAX_COST_USD = 2.00

# Batch size for classification: keep each call to ~80 facts so the
# output fits comfortably within token limits and avoids empty responses.
CLASSIFICATION_BATCH_SIZE = 80

# Estimated tokens per call (used for pre-run cost check only)
EST_CLASSIFICATION_INPUT = 6_000   # per batch of ~80 facts
EST_CLASSIFICATION_OUTPUT = 3_000  # per batch of ~80 facts
EST_SYNTHESIS_INPUT = 15_000
EST_SYNTHESIS_OUTPUT = 4_000


# ── Fact loading and ID assignment ─────────────────────────────────────────────

def load_facts_with_ids(validated_path: str) -> list[dict]:
    """Load all verified/corrected facts from validated_facts.json.

    Assigns a stable id to each fact: {chunk_id}__{category}__{index}
    This id is used throughout the classification and synthesis stages.
    """
    with open(validated_path) as f:
        chunks = json.load(f)

    facts = []
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "unknown")
        for cat in FACT_CATEGORIES:
            for idx, item in enumerate(chunk.get(cat, [])):
                if item.get("citation_status") not in ("verified", "corrected"):
                    continue

                # Build a flat, model-friendly representation
                fact = {
                    "id": f"{chunk_id}__{cat}__{idx}",
                    "category": cat,
                    "citation_status": item["citation_status"],
                    "source_page": item.get("source", {}).get("page"),
                    "period": item.get("period", ""),
                    "confidence": item.get("confidence", ""),
                }

                # Category-specific fields
                if cat == "financial_figures":
                    fact["label"] = item.get("label", "")
                    fact["value"] = item.get("value", "")
                    fact["unit"] = item.get("unit", "")
                elif cat == "business_facts":
                    fact["label"] = item.get("statement", "")
                    fact["category_tag"] = item.get("category", "")
                elif cat == "risk_disclosures":
                    fact["label"] = item.get("description", "")
                    fact["risk_type"] = item.get("risk_type", "")
                elif cat == "strategic_items":
                    fact["label"] = item.get("description", "")
                    fact["item_type"] = item.get("item_type", "")
                elif cat == "management_commentary":
                    fact["label"] = item.get("statement", "")
                    fact["topic"] = item.get("topic", "")

                facts.append(fact)

    return facts


def load_financials(financials_path: str) -> dict:
    """Load financials.json for the synthesis context."""
    with open(financials_path) as f:
        return json.load(f)


# ── Prompt builders ─────────────────────────────────────────────────────────────

CLASSIFICATION_SYSTEM = """You are classifying facts from Auto Trader Group plc's FY2026 annual report for an investment analyst's first-draft memo.

MEMO SECTIONS:
  business_overview      — what the company does, market position, KPIs, customers
  financial_performance  — revenue, profit, margins, cash flow, EPS, dividends
  strategy               — strategic priorities, market trends, product initiatives
  risks                  — disclosed or observable risks
  management             — management commentary, ESG, culture, employee metrics
  investment_case        — capital allocation, shareholder returns, valuation context

RELEVANCE SCALE (1–5):
  5 = headline — the analyst will cite this directly in the memo
  4 = supporting — adds important depth to a key section point
  3 = contextual — useful colour but not essential to the narrative
  2 = peripheral — minor, repetitive, or admin detail
  1 = exclude — governance boilerplate, accounting policy notes, immaterial items

Classify every fact. Be selective: a typical memo has ~30–40 directly cited facts, not 250.
Facts with relevance 4–5 should be the ones a sell-side analyst would actually quote."""


def build_classification_prompt(facts: list[dict]) -> str:
    return (
        f"{CLASSIFICATION_SYSTEM}\n\n"
        f"FACTS TO CLASSIFY ({len(facts)} items):\n"
        + json.dumps(facts, indent=None, separators=(',', ':'))
    )


SYNTHESIS_SYSTEM = """You are an investment analyst writing a first-draft memo on Auto Trader Group plc (LSE: AUTO), the UK's leading digital automotive marketplace.

GROUNDING RULES — these are absolute:
1. Every statement must either:
   (a) cite one or more fact_ids from the provided VERIFIED FACTS list, OR
   (b) set "inference": true to flag it as analytical judgement beyond the data.
2. Never state a specific number that is not in the VERIFIED FACTS or FINANCIAL METRICS below.
3. Disclosed risks must come from the "risk_disclosures" category facts.
4. Inferred risks are patterns you observe in the data not explicitly called out.
5. needs_investigation items are diligence gaps — things you'd want to know before investing.

CONFIDENCE LEVELS:
  high   = directly supported by the data
  medium = reasonable interpretation of the data
  low    = speculative, based on general industry knowledge"""


def build_synthesis_prompt(
    classified_facts: list[dict],
    financials: dict,
) -> str:
    # Format the derived metrics compactly
    metrics_text = "\n".join(
        f"  {m['name']}: {m['result']} {m['unit']} — {m.get('note', '')[:80]}"
        for m in financials.get("derived_metrics", [])
        if m["result"] != 0.0
    )

    # Format only high-relevance facts for synthesis
    facts_text = json.dumps(
        [{"id": f["id"], "category": f["category"],
          "label": f["label"], "memo_section": f.get("memo_section", ""),
          "value": f.get("value", ""), "unit": f.get("unit", ""),
          "period": f.get("period", "")}
         for f in classified_facts],
        indent=None,
        separators=(',', ':'),
    )

    # V2 Change 3: targeted analytical focus questions surface two specific
    # insights the V1 synthesis missed: the direct-traffic competitive moat
    # and the EPS-vs-operating-growth divergence from buyback mechanics.
    # These are phrased as open questions (not assertions) so the model only
    # includes them if supporting facts exist.
    analytical_focus = (
        "ANALYTICAL FOCUS — address these specific questions if the facts support them:\n"
        "1. TRAFFIC ACQUISITION MIX: Is there data on the proportion of visits arriving\n"
        "   via direct channels (app, URL, branded search) vs paid acquisition? If so,\n"
        "   assess whether this mix represents a structural competitive advantage through\n"
        "   lower customer acquisition cost and include it as a strength or value driver.\n"
        "2. EPS vs OPERATING GROWTH: Compare reported EPS growth to revenue and operating\n"
        "   profit growth. If EPS is growing materially faster than operating profit,\n"
        "   explicitly identify the mechanism (share count reduction from buybacks) and\n"
        "   include it as a bear case point about the sustainability of earnings growth."
    )

    return (
        f"{SYNTHESIS_SYSTEM}\n\n"
        f"{analytical_focus}\n\n"
        f"FINANCIAL METRICS (deterministic calculations — cite these by quoting the name):\n"
        f"{metrics_text}\n\n"
        f"VERIFIED FACTS FOR ANALYSIS ({len(classified_facts)} high-relevance items):\n"
        f"{facts_text}\n\n"
        f"Produce the full analytical output per the schema."
    )


# ── Main pipeline ───────────────────────────────────────────────────────────────

def run_classification(
    facts: list[dict],
    call_log: list[dict],
) -> dict[str, dict]:
    """Stage 1: classify all facts in batches. Returns {fact_id: classification_dict}.

    249 facts in one prompt produces an empty tool call. Batching to
    CLASSIFICATION_BATCH_SIZE facts per call keeps output within limits.
    """
    all_classifications: dict[str, dict] = {}
    n_batches = (len(facts) + CLASSIFICATION_BATCH_SIZE - 1) // CLASSIFICATION_BATCH_SIZE

    print(f"  Stage 1: classifying {len(facts)} facts in {n_batches} batch(es)...")

    for i in range(n_batches):
        batch = facts[i * CLASSIFICATION_BATCH_SIZE : (i + 1) * CLASSIFICATION_BATCH_SIZE]
        print(f"    Batch {i+1}/{n_batches} ({len(batch)} facts)...", end=" ", flush=True)

        prompt = build_classification_prompt(batch)
        result: ClassificationBatch = call_llm(
            prompt=prompt,
            schema_class=ClassificationBatch,
            tool_name="classify_facts",
            model=ANALYSIS_MODEL,
            max_tokens=8192,
            log=call_log,
        )
        batch_count = len(result.classifications)
        print(f"{batch_count} classified")
        all_classifications.update({c.id: c.model_dump() for c in result.classifications})

    return all_classifications


def run_synthesis(
    classified_facts: list[dict],
    financials: dict,
    call_log: list[dict],
) -> dict:
    """Stage 2: analytical synthesis over high-relevance facts."""
    prompt = build_synthesis_prompt(classified_facts, financials)

    print(f"  Stage 2: synthesising analysis over {len(classified_facts)} facts...")
    result: Analytics = call_llm(
        prompt=prompt,
        schema_class=Analytics,
        tool_name="synthesise_analytics",
        model=ANALYSIS_MODEL,
        max_tokens=8192,
        log=call_log,
    )
    return result.model_dump()


def classify_and_synthesise(
    validated_path: str,
    financials_path: str,
    out_path: str,
    dry_run: bool = False,
) -> None:
    """Full Milestone 4 pipeline: classify facts, synthesise analytics, write output."""

    # 1. Load inputs
    print(f"Loading facts from {validated_path}...")
    facts = load_facts_with_ids(validated_path)
    print(f"  {len(facts)} verified facts across all categories")

    print(f"Loading financials from {financials_path}...")
    financials = load_financials(financials_path)
    n_metrics = len(financials.get("derived_metrics", []))
    print(f"  {n_metrics} derived metrics loaded")

    # 2. Cost estimate
    import math
    n_batches = math.ceil(len(facts) / CLASSIFICATION_BATCH_SIZE)
    total_classification_input = n_batches * EST_CLASSIFICATION_INPUT
    total_classification_output = n_batches * EST_CLASSIFICATION_OUTPUT
    total_calls = n_batches + 1  # batches + synthesis

    est_cost = (
        estimate_cost(n_batches, EST_CLASSIFICATION_INPUT, EST_CLASSIFICATION_OUTPUT, ANALYSIS_MODEL)
        + estimate_cost(1, EST_SYNTHESIS_INPUT, EST_SYNTHESIS_OUTPUT, ANALYSIS_MODEL)
    )
    print(f"\nEstimated cost: ${est_cost:.3f} ({total_calls} calls to {ANALYSIS_MODEL})")
    print(f"  Classification: {n_batches} batches of ~{CLASSIFICATION_BATCH_SIZE} facts, "
          f"~{total_classification_input:,} in + {total_classification_output:,} out tokens")
    print(f"  Synthesis:      ~{EST_SYNTHESIS_INPUT:,} in + {EST_SYNTHESIS_OUTPUT:,} out tokens")

    if est_cost > MAX_COST_USD:
        print(f"ABORTED: estimated cost ${est_cost:.3f} exceeds ${MAX_COST_USD:.2f} limit.")
        sys.exit(1)

    if dry_run:
        print("\n--dry-run: stopping before API calls.")
        return

    print(f"\nProceeding (under ${MAX_COST_USD:.2f} limit)...\n")

    call_log: list[dict] = []

    # 3. Stage 1: classification
    classifications = run_classification(facts, call_log)

    # Merge classification results back into facts
    classified = []
    unclassified = []
    for fact in facts:
        cls = classifications.get(fact["id"])
        if cls:
            fact["relevance"] = cls["relevance"]
            fact["memo_section"] = cls["memo_section"]
            fact["rationale"] = cls["rationale"]
            classified.append(fact)
        else:
            unclassified.append(fact["id"])

    if unclassified:
        print(f"  Warning: {len(unclassified)} facts not returned by classification model")

    # V2 Change 1: apply risk-register taxonomy floor before relevance distribution.
    # Bumps any risk_disclosures fact in the 'risks' section with relevance ≤2 to 3
    # if its label matches a standard corporate risk-register taxonomy term.
    classified, n_floored = apply_risk_floor(classified, floor=SYNTHESIS_RELEVANCE_THRESHOLD)
    if n_floored:
        print(f"  Risk-floor adjustment: {n_floored} fact(s) bumped to relevance "
              f"{SYNTHESIS_RELEVANCE_THRESHOLD} by taxonomy match")

    relevance_dist = {}
    for f in classified:
        r = f.get("relevance", 0)
        relevance_dist[r] = relevance_dist.get(r, 0) + 1

    print(f"  Classified: {len(classified)} facts")
    print(f"  Relevance distribution: {dict(sorted(relevance_dist.items()))}")

    # 4. Stage 2: synthesis (high-relevance only)
    synthesis_input = [
        f for f in classified
        if f.get("relevance", 0) >= SYNTHESIS_RELEVANCE_THRESHOLD
    ]
    print(f"  {len(synthesis_input)} facts with relevance ≥ {SYNTHESIS_RELEVANCE_THRESHOLD} "
          f"passed to synthesis")

    analytics = run_synthesis(synthesis_input, financials, call_log)

    # 5. Compile output
    total_cost = sum(r.get("cost_usd", 0) for r in call_log)
    total_input = sum(r.get("input_tokens", 0) for r in call_log)
    total_output = sum(r.get("output_tokens", 0) for r in call_log)

    output = {
        "metadata": {
            "total_facts_classified": len(classified),
            "facts_in_synthesis": len(synthesis_input),
            "unclassified": len(unclassified),
            "model": ANALYSIS_MODEL,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cost_usd": round(total_cost, 4),
            "relevance_distribution": {str(k): v for k, v in sorted(relevance_dist.items())},
        },
        "classified_facts": classified,
        "analytics": analytics,
    }

    os.makedirs("output", exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nWrote {out_path}")
    print(f"Actual cost: {total_input:,} input + {total_output:,} output tokens = ${total_cost:.4f}")

    # Analytics summary
    a = analytics
    print(f"\nAnalytics summary:")
    print(f"  Strengths:           {len(a['strengths'])}")
    print(f"  Risks:               {len(a['risks'])} "
          f"({sum(1 for r in a['risks'] if r['risk_type']=='disclosed')} disclosed, "
          f"{sum(1 for r in a['risks'] if r['risk_type']=='inferred')} inferred, "
          f"{sum(1 for r in a['risks'] if r['risk_type']=='needs_investigation')} needs-investigation)")
    print(f"  Value drivers:       {len(a['value_drivers'])}")
    print(f"  Bull case points:    {len(a['bull_case'])}")
    print(f"  Bear case points:    {len(a['bear_case'])}")
    print(f"  Diligence questions: {len(a['diligence_questions'])}")

    # Check for inference-heavy output
    all_items = (
        a["strengths"] + a["risks"] + a["value_drivers"] +
        a["bull_case"] + a["bear_case"] + a["diligence_questions"]
    )
    inferred_count = sum(1 for i in all_items if i.get("inference"))
    if inferred_count:
        print(f"\n  {inferred_count} items flagged as inference (no fact_id backing)")


def main():
    parser = argparse.ArgumentParser(description="Classify facts and synthesise analytics")
    parser.add_argument("--facts", default="output/validated_facts.json")
    parser.add_argument("--financials", default="output/financials.json")
    parser.add_argument("--out", default="output/classified_facts.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Estimate cost only; do not call the API")
    args = parser.parse_args()

    classify_and_synthesise(
        validated_path=args.facts,
        financials_path=args.financials,
        out_path=args.out,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
