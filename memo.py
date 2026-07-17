"""Milestone 5: investment memo generation and post-generation validation.

Generates the ten-section investment memo for Auto Trader Group plc.

Inputs (never raw documents):
  output/classified_facts.json  — verified facts + analytical synthesis
  output/financials.json        — deterministic cross-checks and derived metrics

Outputs:
  output/memo.md                — the ten-section markdown memo
  output/evidence_register.json — {E-001: {fact, page, excerpt, …}, …}

Pipeline:
  1. Build evidence register (E-001 … E-NNN) from high-relevance classified facts
  2. Generate sections 1–5 via claude-sonnet-5 (prose, no tool use)
  3. Generate sections 6–8 via claude-sonnet-5 (prose, no tool use)
  4. Auto-populate sections 9–10 from data (no AI)
  5. Validate: every [E-NNN] resolves; every financial figure traces to source
  6. Write memo.md and evidence_register.json

Usage:
    python memo.py                  # uses default paths
    python memo.py --dry-run        # cost estimate only
"""

import argparse
import json
import os
import re
import sys
from datetime import date

from dotenv import load_dotenv
load_dotenv()

from llm import call_llm_text, estimate_cost, ANALYSIS_MODEL

# ── Constants ──────────────────────────────────────────────────────────────────

MEMO_GENERATION_MODEL = ANALYSIS_MODEL   # claude-sonnet-5
MIN_RELEVANCE_FOR_REGISTER = 3           # facts below this are not in the register

MAX_COST_USD = 2.00

# Generous estimates — splits 1-5 and 6-8 into two calls
EST_SECTIONS_15_INPUT  = 18_000
EST_SECTIONS_15_OUTPUT =  4_000
EST_SECTIONS_68_INPUT  = 12_000
EST_SECTIONS_68_OUTPUT =  3_000

# Number validation: allow up to 2% relative error to handle rounding
NUMBER_TOLERANCE = 0.02

# Min length of a financial number match (avoids matching years like "2026")
MIN_NUMBER_CHARS = 2


# ── Evidence register ──────────────────────────────────────────────────────────

def build_evidence_register(
    classified_facts: list[dict],
    min_relevance: int = MIN_RELEVANCE_FOR_REGISTER,
) -> dict[str, dict]:
    """Assign E-IDs to every classified fact with relevance >= min_relevance.

    Returns a dict {E_ID: enriched_fact_dict}. E-IDs are assigned in order
    of memo_section (business_overview first, investment_case last) so the
    register reads logically in the memo.
    """
    SECTION_ORDER = [
        "business_overview",
        "financial_performance",
        "strategy",
        "risks",
        "management",
        "investment_case",
    ]

    # Filter and sort
    eligible = [
        f for f in classified_facts
        if f.get("relevance", 0) >= min_relevance
    ]
    eligible.sort(key=lambda f: (
        SECTION_ORDER.index(f.get("memo_section", "investment_case"))
        if f.get("memo_section") in SECTION_ORDER else 99,
        -(f.get("relevance", 0)),  # higher relevance first within section
    ))

    register = {}
    for idx, fact in enumerate(eligible, start=1):
        e_id = f"E-{idx:03d}"
        # Concise label for the register
        label = (
            fact.get("label") or
            fact.get("statement") or
            fact.get("description") or ""
        )[:80]
        register[e_id] = {
            "fact_id": fact["id"],
            "category": fact["category"],
            "label": label,
            "value": fact.get("value", ""),
            "unit": fact.get("unit", ""),
            "period": fact.get("period", ""),
            "memo_section": fact.get("memo_section", ""),
            "relevance": fact.get("relevance", 0),
            "source_page": fact.get("source_page"),
            "citation_status": fact.get("citation_status", ""),
            # Store back-reference so the prompt can show E-IDs to the model
            "_fact_idx": fact["id"],
        }
        # Also annotate the fact so we can look up E-IDs by fact_id later
        fact["_e_id"] = e_id

    return register


def _fact_id_to_e_id(classified_facts: list[dict]) -> dict[str, str]:
    """Return {fact_id: E-ID} for all facts that have been assigned an E-ID."""
    return {
        f["id"]: f["_e_id"]
        for f in classified_facts
        if "_e_id" in f
    }


# ── Prompt builders ─────────────────────────────────────────────────────────────

def _format_register_for_prompt(register: dict[str, dict]) -> str:
    """Compact one-line-per-entry representation of the evidence register."""
    lines = []
    current_section = None
    for e_id, entry in register.items():
        section = entry.get("memo_section", "")
        if section != current_section:
            lines.append(f"\n  -- {section.upper().replace('_',' ')} --")
            current_section = section

        value_str = ""
        if entry["value"] != "":
            value_str = f" | {entry['value']} {entry['unit']}"
        period_str = f" | {entry['period']}" if entry["period"] else ""
        page_str = f" | p{entry['source_page']}" if entry["source_page"] else ""

        lines.append(
            f"  {e_id}: {entry['label']}{value_str}{period_str}{page_str}"
        )
    return "\n".join(lines)


def _format_analytics_with_e_ids(
    analytics: dict,
    fact_to_e: dict[str, str],
) -> str:
    """Format the analytical synthesis, replacing fact_ids with E-IDs."""

    def _item_str(item: dict, prefix: str = "") -> str:
        e_ids = [fact_to_e.get(fid, fid) for fid in item.get("fact_ids", [])]
        refs = " [" + ", ".join(e_ids) + "]" if e_ids else ""
        infer = " [INFERENCE — write as hedged prose]" if item.get("inference") else ""
        risk_type = f" ({item['risk_type']})" if "risk_type" in item else ""
        return f"  {prefix}{item['statement']}{risk_type}{refs}{infer}"

    parts = []

    parts.append("STRENGTHS:")
    for s in analytics.get("strengths", []):
        parts.append(_item_str(s, "• "))

    parts.append("\nRISKS:")
    for r in analytics.get("risks", []):
        parts.append(_item_str(r, "• "))

    parts.append("\nVALUE DRIVERS:")
    for v in analytics.get("value_drivers", []):
        parts.append(_item_str(v, "• "))

    parts.append("\nBULL CASE:")
    for b in analytics.get("bull_case", []):
        parts.append(_item_str(b, "• "))

    parts.append("\nBEAR CASE:")
    for b in analytics.get("bear_case", []):
        parts.append(_item_str(b, "• "))

    parts.append("\nDILIGENCE QUESTIONS:")
    for q in analytics.get("diligence_questions", []):
        parts.append(_item_str(q, f"{analytics['diligence_questions'].index(q)+1}. "))

    return "\n".join(parts)


def _format_metrics_for_prompt(financials: dict) -> str:
    """Format derived metrics (including growth rates) for the prompt."""
    lines = []
    for m in financials.get("derived_metrics", []):
        if m["result"] == 0.0:
            continue
        note = f" — {m['note'][:60]}" if m.get("note") else ""
        lines.append(f"  {m['name']}: {m['result']} {m['unit']}{note}")
    return "\n".join(lines)


MEMO_SYSTEM = """You are writing a professional investment memo on Auto Trader Group plc (LSE: AUTO) for an investment analyst's first-pass review. The memo is based solely on the evidence register and analytical synthesis provided below — you must not invent facts, numbers, or citations.

ABSOLUTE RULES:
1. Every material claim must end with an inline evidence citation: [E-NNN]
   • You may cite multiple references: [E-001, E-002]
   • Only cite E-IDs that appear in the EVIDENCE REGISTER below
2. Numbers: copy EXACTLY as they appear in the EVIDENCE REGISTER or FINANCIAL METRICS below
   • Do not round, convert units, or paraphrase figures
   • If the register says "£624.3m", write "£624.3m" — not "~£624m" or "over £600m"
3. Items marked [INFERENCE] must be written as hedged prose:
   • Use "This may suggest...", "It appears that...", "The pace of buybacks implies..."
   • Do not state inferences as documented facts
4. Do not produce a buy / sell / hold recommendation under any circumstances
5. Write in British English; past tense for reported results; present tense for strategy

FORMAT: output clean Markdown with the section headers exactly as specified."""


def build_sections_1_5_prompt(
    register: dict[str, dict],
    analytics: dict,
    metrics: str,
    fact_to_e: dict[str, str],
) -> str:
    reg_text = _format_register_for_prompt(register)
    analytics_text = _format_analytics_with_e_ids(analytics, fact_to_e)

    return f"""{MEMO_SYSTEM}

EVIDENCE REGISTER (your only permitted citations — E-001 through E-{len(register):03d}):
{reg_text}

FINANCIAL METRICS (pre-calculated by code — use these exact figures):
{metrics}

ANALYTICAL SYNTHESIS (use this to guide the narrative — E-IDs already shown):
{analytics_text}

---

Write sections 1 through 5 only. Do not write sections 6–10.

## 1. Executive Summary
~200 words. Cover: what Auto Trader does, FY2026 headline results, key investment thesis points, one sentence on the main risk. Cite the 4–5 most important E-IDs.

## 2. Business Overview
~300 words. Cover: the core marketplace model, how the company makes money (ARPR, retailer base, consumer services), Autorama's role, Deal Builder as the key strategic product. Cite E-IDs throughout.

## 3. Financial and Operating Performance
~400 words. Walk through the P&L and key KPIs: revenue growth, operating profit, margins (core vs group), EPS, cash generation, leverage, and capital returns. Use the FINANCIAL METRICS for growth rates. Cite E-IDs on every figure.

## 4. Value Drivers
3–5 bullet points, each ~40 words. Draw from the VALUE DRIVERS in the analytical synthesis. Each bullet must cite [E-NNN].

## 5. Strengths
3–5 bullet points, each ~40 words. Draw from STRENGTHS in the analytical synthesis. Each bullet must cite [E-NNN]."""


def _format_risks_checklist(analytics: dict, fact_to_e: dict[str, str]) -> str:
    """Format all analytics risk items as an explicit numbered checklist.

    V2 Change 2: V1 memo generation selected only 5 of 11 synthesis risks for
    Section 6, silently dropping EV/climate and other items. Passing the full
    list as an explicit mandate ensures every synthesised risk is addressed.
    """
    risks = analytics.get("risks", [])
    lines = [
        f"ALL {len(risks)} RISK ITEMS FROM SYNTHESIS — Section 6 must address every one:",
    ]
    for i, r in enumerate(risks, 1):
        e_ids = [fact_to_e.get(fid, fid) for fid in r.get("fact_ids", [])]
        refs = " [" + ", ".join(e_ids) + "]" if e_ids else ""
        infer = " [INFERENCE]" if r.get("inference") else ""
        rtype = r.get("risk_type", "disclosed")
        lines.append(f"  {i}. ({rtype}){infer} {r['statement']}{refs}")
    return "\n".join(lines)


def build_sections_6_8_prompt(
    register: dict[str, dict],
    analytics: dict,
    metrics: str,
    fact_to_e: dict[str, str],
    sections_1_5_text: str,
) -> str:
    reg_text = _format_register_for_prompt(register)
    analytics_text = _format_analytics_with_e_ids(analytics, fact_to_e)
    risks_checklist = _format_risks_checklist(analytics, fact_to_e)

    return f"""{MEMO_SYSTEM}

EVIDENCE REGISTER:
{reg_text}

FINANCIAL METRICS:
{metrics}

ANALYTICAL SYNTHESIS:
{analytics_text}

{risks_checklist}

SECTIONS 1–5 ALREADY WRITTEN (for context — do not repeat):
{sections_1_5_text[:2000]}
[... truncated for brevity ...]

---

Write sections 6 through 8 only. Do not write sections 1–5 or 9–10.

## 6. Material Risks
Organise under three sub-headers. You MUST address every item in the risk checklist above —
group them under the appropriate sub-header. Do not omit any item.

### Disclosed risks
Risks explicitly stated in the annual report. Draw from RISKS with risk_type=disclosed. Each point ~40 words with [E-NNN].

### Inferred risks
Patterns visible in the data not explicitly called out by management. Draw from RISKS with risk_type=inferred. Items marked [INFERENCE] must be written as hedged prose. 1–2 points.

### Items requiring further investigation
Draw from the diligence questions where they surface data gaps (not yet answered by the evidence). 1–2 points, framed as "The available evidence does not clarify..."

## 7. Bull and Bear Cases
Two sub-sections, 3–4 points each (~30 words per point), with [E-NNN] citations.

### Bull case

### Bear case

## 8. Prioritised Diligence Questions
Numbered list of 5–7 questions, each ~30 words, most-important first. Draw from DILIGENCE QUESTIONS in the synthesis. Each must cite the E-IDs of facts that motivate the question. Items marked [INFERENCE] must explain why the question arises from observable data patterns."""


# ── Auto-generated sections ─────────────────────────────────────────────────────

def build_section_9(register: dict[str, dict]) -> str:
    """Section 9: evidence register as a markdown table. No AI involved."""
    lines = [
        "## 9. Evidence Register\n",
        "All evidence references used in this memo. Citation status confirmed by the "
        "pipeline's string-match validator against the source document.\n",
        "| Ref | Category | Label | Value | Period | Page | Status |",
        "|-----|----------|-------|-------|--------|------|--------|",
    ]
    for e_id, entry in register.items():
        value_str = f"{entry['value']} {entry['unit']}".strip() if entry["value"] != "" else "—"
        page_str = f"p{entry['source_page']}" if entry["source_page"] else "—"
        label = entry["label"][:55].replace("|", "∣")
        lines.append(
            f"| {e_id} | {entry['category']} | {label} | "
            f"{value_str} | {entry['period'][:20]} | {page_str} | {entry['citation_status']} |"
        )
    return "\n".join(lines)


def build_section_10(missing_data: list[dict], unverifiable_facts: list[dict]) -> str:
    """Section 10: limitations auto-populated from the missing-data catalogue
    and the 5 unverifiable facts. No AI involved."""
    lines = [
        "## 10. Limitations\n",
        "The following limitations apply to this memo and should be borne in mind "
        "during review. They are reported transparently rather than concealed.\n",
        "### Calculations not available (missing prior-year data)",
    ]

    for item in missing_data:
        lines.append(f"- **{item['name']}**: {item['reason']}")

    lines.append("\n### Facts excluded from downstream use (citation unverifiable)")
    lines.append(
        "The following facts were extracted by the model but their supporting excerpt "
        "could not be string-matched against the source PDF, typically because the fact "
        "appears on an infographic page where pdfplumber cannot extract contiguous text. "
        "The underlying values are believed correct but are excluded from citation:\n"
    )
    for fact in unverifiable_facts:
        chunk = fact.get("chunk_id", "")
        page = fact.get("page")
        label = fact.get("label", "")
        lines.append(f"- [{chunk}] p{page}: {label}")

    lines.append(
        "\n### General limitations\n"
        "- This memo is an AI-assisted first draft. All material claims should be "
        "independently verified against the source documents before use in investment decisions.\n"
        "- The pipeline was run on the FY2026 Annual Report only. "
        "The analyst presentation, half-year results, and prior-year annual reports "
        "were not included in V1.\n"
        "- Forward-looking statements (FY2027 guidance, long-term capital return targets) "
        "are reproduced from management commentary and reflect management's views at the "
        "time of publication, not the pipeline's projections.\n"
        "- No buy, sell, or hold recommendation is made or implied."
    )
    return "\n".join(lines)


# ── Post-generation validator ───────────────────────────────────────────────────

# Financial number patterns: £Xm, X%, Xp, £X,XXX, ratios like 0.3x
# Excludes plain years (2025, 2026), page numbers (p4), section numbers
_FINANCIAL_NUMBER_RE = re.compile(
    r'(?:'
    r'£\s*[\d,]+(?:\.\d+)?\s*(?:m\b|bn\b)?'   # £624.3m, £2,995, £1.1bn
    r'|[\d,]+(?:\.\d+)?\s*%'                    # 63%, 3.9%, +4%
    r'|[\d,]+(?:\.\d+)?\s*p\b'                  # 34.17p
    r'|[\d,]+(?:\.\d+)?\s*x\b'                  # 0.3x
    r'|\b[\d,]{5,}(?:\.\d+)?\b'                 # large bare numbers: 13,942 / 451,000
    r')',
    re.I,
)

_STRIP_CURRENCY_RE = re.compile(r'[£$,\s]')
_UNIT_RE = re.compile(r'[m%pbx]+$', re.I)


def _parse_financial_number(text: str) -> float | None:
    """Parse a financial number string to float, stripping currency/unit suffixes."""
    cleaned = _STRIP_CURRENCY_RE.sub('', text)
    cleaned = _UNIT_RE.sub('', cleaned).strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def build_permitted_values(
    classified_facts: list[dict],
    financials: dict,
    prior_year_path: str | None = None,
) -> list[float]:
    """Build the set of all numeric values from verified source data.

    Returns a list of floats that any number in the memo must be near.
    """
    values = []

    # From classified facts — numeric value field (financial_figures)
    for fact in classified_facts:
        if fact.get("citation_status") not in ("verified", "corrected"):
            continue
        if fact.get("value") not in (None, ""):
            try:
                v = float(fact["value"])
                values.append(v)
                # Cash outflows are stored negative; memo writes their magnitude.
                if v < 0:
                    values.append(abs(v))
            except (TypeError, ValueError):
                pass
        # Non-financial facts (business_facts, risk_disclosures, etc.) have no
        # value field, but their label text can contain legitimate numbers (e.g.
        # "75% of all minutes", "8,056 vehicles"). Parse these so the validator
        # doesn't flag them as hallucinations.
        for text_field in ("label", "category_tag", "topic", "risk_type"):
            text = fact.get(text_field, "")
            if not text:
                continue
            for m in _FINANCIAL_NUMBER_RE.findall(text):
                pv = _parse_financial_number(m)
                if pv is not None:
                    values.append(pv)

    # From derived metrics and cross-checks
    for m in financials.get("derived_metrics", []):
        if m.get("result") is not None:
            values.append(float(m["result"]))
        for v in m.get("inputs", {}).values():
            if v is not None:
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    pass

    for c in financials.get("cross_checks", []):
        for v in c.get("inputs", {}).values():
            if v is not None:
                try:
                    values.append(float(v))
                except (TypeError, ValueError):
                    pass
        if c.get("calculated") is not None:
            values.append(float(c["calculated"]))
        if c.get("stated") is not None:
            values.append(float(c["stated"]))

    # From prior-year facts if available
    if prior_year_path and os.path.exists(prior_year_path):
        with open(prior_year_path) as f:
            prior = json.load(f)
        for p in prior:
            try:
                values.append(float(p["value"]))
            except (TypeError, ValueError):
                pass

    return values


def validate_references(memo_text: str, register: dict[str, dict]) -> list[str]:
    """Return a list of error messages for any [E-NNN] that doesn't resolve."""
    found = re.findall(r'\[E-\d+\]', memo_text)
    errors = []
    for ref in found:
        e_id = ref[1:-1]  # strip brackets
        if e_id not in register:
            errors.append(f"Unresolved reference {ref} — not in evidence register")
    return errors


def validate_numbers(
    memo_text: str,
    permitted_values: list[float],
    tolerance: float = NUMBER_TOLERANCE,
) -> list[str]:
    """Return error messages for financial numbers in the memo with no permitted match.

    Numbers < 2 are skipped (ratios like 0.3x have many legitimate values and
    are unlikely to be hallucinations). Years (four-digit numbers matching
    2020–2030) are also excluded.
    """
    errors = []
    lines = memo_text.split('\n')
    permitted_set = set(permitted_values)

    for line_no, line in enumerate(lines, 1):
        # Skip the evidence register section itself (it lists all our own data)
        if line.startswith('| E-') or line.startswith('|--'):
            continue

        matches = _FINANCIAL_NUMBER_RE.findall(line)
        for match_text in matches:
            val = _parse_financial_number(match_text)
            if val is None:
                continue
            if abs(val) < 2:
                continue   # ratios and very small numbers skipped
            # Skip years
            if 2019 <= val <= 2030:
                continue
            # Skip section numbers (1, 2, 3, … 10)
            if val <= 10 and val == int(val):
                continue

            # Check against all permitted values with tolerance
            found_match = any(
                (abs(val - pv) <= max(abs(pv) * tolerance, 0.5))
                for pv in permitted_values
                if pv is not None
            )
            if not found_match:
                errors.append(
                    f"Line {line_no}: '{match_text}' (parsed={val}) "
                    f"has no matching source value within {tolerance*100:.0f}% tolerance"
                )

    return errors


# ── Orchestration ───────────────────────────────────────────────────────────────

def load_inputs(classified_path: str, financials_path: str) -> tuple[dict, dict, dict]:
    """Load classified_facts.json and financials.json. Return (cf, financials, analytics)."""
    with open(classified_path) as f:
        cf = json.load(f)
    with open(financials_path) as f:
        financials = json.load(f)
    analytics = cf.get("analytics", {})
    return cf, financials, analytics


def load_unverifiable_facts(validated_path: str) -> list[dict]:
    """Return the 5 unverifiable facts for the limitations section."""
    with open(validated_path) as f:
        chunks = json.load(f)
    result = []
    for chunk in chunks:
        for cat in ["financial_figures", "business_facts", "risk_disclosures",
                    "strategic_items", "management_commentary"]:
            for item in chunk.get(cat, []):
                if item.get("citation_status") == "unverifiable":
                    result.append({
                        "chunk_id": chunk["chunk_id"],
                        "category": cat,
                        "label": item.get("label", item.get("statement",
                                  item.get("description", "")))[:80],
                        "page": item.get("source", {}).get("page"),
                    })
    return result


def run_memo_pipeline(
    classified_path: str = "output/classified_facts.json",
    financials_path: str = "output/financials.json",
    validated_path: str = "output/validated_facts.json",
    prior_year_path: str = "output/prior_year_facts.json",
    memo_out: str = "output/memo.md",
    register_out: str = "output/evidence_register.json",
    dry_run: bool = False,
) -> None:
    """Full memo generation pipeline."""

    # 1. Load inputs
    print("Loading inputs...")
    cf, financials, analytics = load_inputs(classified_path, financials_path)
    classified_facts = cf["classified_facts"]
    missing_data = financials.get("missing_data", [])
    unverifiable_facts = load_unverifiable_facts(validated_path)

    print(f"  {len(classified_facts)} classified facts")
    print(f"  {len(analytics.get('strengths', []))} strengths, "
          f"{len(analytics.get('risks', []))} risks, "
          f"{len(analytics.get('diligence_questions', []))} diligence questions")
    print(f"  {len(missing_data)} missing-data items, {len(unverifiable_facts)} unverifiable facts")

    # 2. Build evidence register
    print("\nBuilding evidence register...")
    register = build_evidence_register(classified_facts, MIN_RELEVANCE_FOR_REGISTER)
    print(f"  {len(register)} entries (E-001 to E-{len(register):03d})")

    # 3. Build fact_id → E-ID lookup (needed to map analytics fact_ids to E-IDs)
    fact_to_e = _fact_id_to_e_id(classified_facts)

    # 4. Prepare prompt components
    metrics_text = _format_metrics_for_prompt(financials)

    # 5. Cost estimate
    est_cost = (
        estimate_cost(1, EST_SECTIONS_15_INPUT, EST_SECTIONS_15_OUTPUT, MEMO_GENERATION_MODEL)
        + estimate_cost(1, EST_SECTIONS_68_INPUT, EST_SECTIONS_68_OUTPUT, MEMO_GENERATION_MODEL)
    )
    print(f"\nEstimated cost: ${est_cost:.3f} (2 calls to {MEMO_GENERATION_MODEL})")
    print(f"  Call 1 (sections 1–5): ~{EST_SECTIONS_15_INPUT:,} in + {EST_SECTIONS_15_OUTPUT:,} out tokens")
    print(f"  Call 2 (sections 6–8): ~{EST_SECTIONS_68_INPUT:,} in + {EST_SECTIONS_68_OUTPUT:,} out tokens")
    print(f"  Sections 9–10: auto-generated (no API call)")

    if est_cost > MAX_COST_USD:
        print(f"ABORTED: estimated cost ${est_cost:.3f} exceeds ${MAX_COST_USD:.2f} limit.")
        sys.exit(1)

    if dry_run:
        print("\n--dry-run: stopping before API calls.")
        return

    print(f"\nProceeding (under ${MAX_COST_USD:.2f} limit)...\n")

    call_log: list[dict] = []

    # 6. Generate sections 1–5
    print("Generating sections 1–5 (exec summary through strengths)...")
    prompt_1_5 = build_sections_1_5_prompt(register, analytics, metrics_text, fact_to_e)
    sections_1_5 = call_llm_text(
        prompt=prompt_1_5,
        model=MEMO_GENERATION_MODEL,
        max_tokens=4096,
        log=call_log,
    )
    stop_reason = call_log[-1].get("stop_reason", "?")
    print(f"  Done ({call_log[-1]['output_tokens']} tokens, stop={stop_reason})")

    if stop_reason == "max_tokens":
        print("  WARNING: sections 1–5 were truncated at max_tokens.")

    # 7. Generate sections 6–8
    print("Generating sections 6–8 (risks through diligence)...")
    prompt_6_8 = build_sections_6_8_prompt(
        register, analytics, metrics_text, fact_to_e, sections_1_5
    )
    sections_6_8 = call_llm_text(
        prompt=prompt_6_8,
        model=MEMO_GENERATION_MODEL,
        max_tokens=4096,
        log=call_log,
    )
    stop_reason = call_log[-1].get("stop_reason", "?")
    print(f"  Done ({call_log[-1]['output_tokens']} tokens, stop={stop_reason})")

    if stop_reason == "max_tokens":
        print("  WARNING: sections 6–8 were truncated at max_tokens.")

    # 8. Auto-generate sections 9–10
    section_9 = build_section_9(register)
    section_10 = build_section_10(missing_data, unverifiable_facts)

    # 9. Assemble the full memo
    today = date.today().strftime("%-d %B %Y")
    header = (
        f"# Investment Memo: Auto Trader Group plc (LSE: AUTO)\n\n"
        f"**Prepared by:** Evidence-Grounded AI Memo Assistant  \n"
        f"**Source:** FY2026 Annual Report (year ended 31 March 2026)  \n"
        f"**Date:** {today}  \n"
        f"**Status:** AI-assisted first draft — requires human review before use  \n"
        f"**Model:** {MEMO_GENERATION_MODEL}  \n\n---\n\n"
    )
    # Strip any title the model echoed at the start of sections_1_5 — the
    # header already has one, so a duplicate would appear at line 11.
    s15_clean = re.sub(r'^#\s+Investment Memo:[^\n]*\n+', '', sections_1_5, count=1)
    memo_text = header + s15_clean + "\n\n" + sections_6_8 + "\n\n" + section_9 + "\n\n" + section_10

    # 10. Post-generation validation
    print("\nRunning post-generation validation...")
    permitted_values = build_permitted_values(classified_facts, financials, prior_year_path)
    ref_errors = validate_references(memo_text, register)
    num_errors = validate_numbers(memo_text, permitted_values)

    all_errors = ref_errors + num_errors
    if ref_errors:
        print(f"  REFERENCE ERRORS ({len(ref_errors)}):")
        for e in ref_errors:
            print(f"    ✗ {e}")
    else:
        print(f"  References: all [E-NNN] resolve ✓")

    if num_errors:
        print(f"  NUMBER ERRORS ({len(num_errors)}):")
        for e in num_errors[:10]:  # show first 10
            print(f"    ✗ {e}")
        if len(num_errors) > 10:
            print(f"    ... and {len(num_errors)-10} more")
    else:
        print(f"  Numbers: all financial figures verified ✓")

    if all_errors:
        print(f"\nValidation failed: {len(all_errors)} error(s). Memo written but FLAGGED.")
    else:
        print(f"\nValidation passed.")

    # 11. Count E-ID citations in the memo
    cited_ids = set(re.findall(r'E-\d+', memo_text))
    # Remove those that only appear in section 9 header
    print(f"  Unique E-IDs cited in prose: {len(cited_ids)}/{len(register)}")

    # 12. Write outputs
    os.makedirs("output", exist_ok=True)
    with open(memo_out, "w") as f:
        f.write(memo_text)
    print(f"\nWrote {memo_out}")

    # Enrich register with validation status
    register_output = {
        e_id: {**entry, "cited_in_memo": e_id in cited_ids}
        for e_id, entry in register.items()
    }
    # Add validation summary
    register_output["_validation"] = {
        "reference_errors": ref_errors,
        "number_errors": num_errors,
        "total_errors": len(all_errors),
        "passed": len(all_errors) == 0,
    }
    with open(register_out, "w") as f:
        json.dump(register_output, f, indent=2)
    print(f"Wrote {register_out}")

    # 13. Token / cost summary
    total_cost = sum(r.get("cost_usd", 0) for r in call_log)
    total_input = sum(r.get("input_tokens", 0) for r in call_log)
    total_output = sum(r.get("output_tokens", 0) for r in call_log)
    print(f"\nActual cost: {total_input:,} in + {total_output:,} out tokens = ${total_cost:.4f}")


def main():
    parser = argparse.ArgumentParser(description="Generate the investment memo")
    parser.add_argument("--classified", default="output/classified_facts.json")
    parser.add_argument("--financials", default="output/financials.json")
    parser.add_argument("--validated", default="output/validated_facts.json")
    parser.add_argument("--prior-year", default="output/prior_year_facts.json")
    parser.add_argument("--memo-out", default="output/memo.md")
    parser.add_argument("--register-out", default="output/evidence_register.json")
    parser.add_argument("--dry-run", action="store_true",
                        help="Estimate cost only; do not call the API")
    args = parser.parse_args()

    run_memo_pipeline(
        classified_path=args.classified,
        financials_path=args.financials,
        validated_path=args.validated,
        prior_year_path=args.prior_year,
        memo_out=args.memo_out,
        register_out=args.register_out,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
