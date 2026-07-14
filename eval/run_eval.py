"""Evaluation harness for the memo-assistant pipeline.

Automated metrics (no API calls, no human judgement):
  1. Fact recall    — gold facts F-01..F-20 vs output/validated_facts.json
  2. Citation accuracy — pipeline page citations vs gold page numbers
  3. Risk coverage  — gold risks R-01..R-10 vs memo's Section 6

Human-judgement outputs (generated, never scored by the model):
  4. Observation coverage scoring sheet — O-01..O-10 for Zak to fill in
  5. Diligence question quality rating  — pipeline vs gold Q-01..Q-10

Outputs:
  eval/results.md       — automated per-item detail + summary scores
  eval/scoring_sheet.md — blank form for manual metrics

Usage:
    python eval/run_eval.py
    python eval/run_eval.py --memo output/memo.md  # override any path
"""

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Constants ────────────────────────────────────────────────────────────────

TOLERANCE = 0.02            # 2% relative tolerance for value matching
ABS_FLOOR = 0.05            # absolute floor so small values aren't too loose
CITATION_TOL = 1            # ±N pages accepted as correct citation
RISK_KEYWORD_STEM = 8       # prefix length for morphological matching
RISK_KEYWORD_THRESHOLD = 2  # minimum stem-matches to count as COVERED

STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "for", "with", "on", "at",
    "by", "from", "as", "is", "are", "was", "were", "be", "been", "has", "have",
    "had", "this", "that", "these", "those", "it", "its", "can", "could", "would",
    "may", "might", "will", "shall", "our", "us", "we", "their", "they", "them",
    "not", "no", "if", "which", "who", "what", "how", "when", "where", "such",
    "any", "all", "also", "about", "into", "than", "other", "more", "affect",
    "include", "reduce", "lead", "impact", "failure", "ensure", "continued",
    "company", "business", "group", "auto", "trader", "autotrader",
}


# ── Value extraction ─────────────────────────────────────────────────────────

def extract_candidate_values(text: str) -> list[tuple[float, str]]:
    """Extract significant numeric values from text in priority order.

    Priority: £Xm > pence > non-million-£ > X million > large integers > % > Xx.
    Skips year numbers (2019–2031) and values ≤ 0.
    Returns list of (float_value, display_string) pairs, deduplicated.
    """
    candidates: list[tuple[float, str]] = []
    seen: set[float] = set()

    def add(v: float, label: str) -> None:
        v = round(v, 4)
        if v > 0 and not (2019 <= v <= 2031) and v not in seen:
            seen.add(v)
            candidates.append((v, label))

    # Priority 1: £Xm (monetary millions)
    for m in re.finditer(r'£\s*([\d,]+(?:\.\d+)?)\s*m\b', text, re.I):
        add(float(m.group(1).replace(',', '')), f'£{m.group(1)}m')

    # Priority 2: pence (e.g. 34.17p, 11.6p)
    for m in re.finditer(r'\b(\d+\.\d+)\s*p\b', text):
        add(float(m.group(1)), f'{m.group(1)}p')

    # Priority 3: non-million £ values (e.g. £2,995, £141)
    # Negative lookahead excludes £Xm and £Xbn already captured above.
    for m in re.finditer(r'£\s*([\d,]+(?:\.\d+)?)(?!\s*(?:m|bn)\b)', text, re.I):
        v = float(m.group(1).replace(',', ''))
        if v > 0:
            add(v, f'£{m.group(1)}')

    # Priority 4: X million (visits, calls, shares when not preceded by £)
    for m in re.finditer(r'(?<![£$])\b([\d]+(?:\.\d+)?)\s+million\b', text, re.I):
        add(float(m.group(1)), f'{m.group(1)} million')

    # Priority 5: large integers — 4+ digits, excluding year range
    for m in re.finditer(r'\b(\d[\d,]{3,})\b', text):
        v = float(m.group(1).replace(',', ''))
        add(v, m.group(1))

    # Priority 6: percentages
    for m in re.finditer(r'\b(\d+(?:\.\d+)?)\s*%', text):
        add(float(m.group(1)), f'{m.group(1)}%')

    # Priority 7: multiples (0.3x, 1.0x)
    for m in re.finditer(r'\b(\d+\.\d+)\s*x\b', text, re.I):
        add(float(m.group(1)), f'{m.group(1)}x')

    return candidates


def values_close(a: float, b: float, tol: float = TOLERANCE) -> bool:
    """True if a ≈ b within relative tolerance.

    Also checks sign-flipped match: losses are stored as negative (e.g. -2.0)
    but gold claims write them as positive magnitudes ('£2.0m losses').
    """
    return (
        abs(a - b) <= max(abs(b) * tol, ABS_FLOOR)
        or abs(a + b) <= max(abs(b) * tol, ABS_FLOOR)  # sign-flip for losses
    )


# ── Data loading ─────────────────────────────────────────────────────────────

def load_gold_set(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def load_validated_facts(path: Path) -> list[dict]:
    """Return all verified/corrected financial_figures as a flat list."""
    with open(path) as f:
        chunks = json.load(f)
    facts = []
    for chunk in chunks:
        for fig in chunk.get("financial_figures", []):
            if fig.get("citation_status") in ("verified", "corrected"):
                facts.append(fig)
    return facts


def load_classified(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def extract_memo_section(memo_text: str, section_num: int) -> str:
    """Return the text of section N from the memo (stops at section N+1)."""
    m = re.search(rf'##\s+{section_num}\.', memo_text)
    if not m:
        return ""
    start = m.start()
    m2 = re.search(rf'##\s+{section_num + 1}\.', memo_text[start:])
    return memo_text[start: start + m2.start()] if m2 else memo_text[start:]


# ── Fact recall ──────────────────────────────────────────────────────────────

def score_fact(gold_fact: dict, pipeline_facts: list[dict]) -> dict:
    """Score one gold fact against all verified pipeline facts.

    Returns a result dict with keys: id, claim, gold_page, status, and details.

    Status values:
      FOUND_CORRECT_CITE — primary value matched, pipeline page ≈ gold page
      FOUND_WRONG_CITE   — primary value matched, page off by > CITATION_TOL
      NEAR_MISS          — only a secondary value matched (manual adjudication needed)
      MISSING            — no candidate value found in pipeline facts
    """
    candidates = extract_candidate_values(gold_fact["claim"])
    gold_page = gold_fact["page"]

    base = {
        "id": gold_fact["id"],
        "claim": gold_fact["claim"],
        "gold_page": gold_page,
    }

    if not candidates:
        return {**base, "status": "MISSING", "note": "No numeric values extracted from claim"}

    for rank, (val, val_label) in enumerate(candidates):
        matches = [f for f in pipeline_facts if values_close(val, f.get("value", 0))]
        if not matches:
            continue

        # Of multiple matches, pick the one whose page is closest to the gold page
        best = min(matches, key=lambda f: abs((f.get("source") or {}).get("page", 9999) - gold_page))
        pipeline_page = (best.get("source") or {}).get("page")
        pipeline_label = best.get("label", "—")

        page_ok = (
            pipeline_page is not None
            and abs(pipeline_page - gold_page) <= CITATION_TOL
        )

        if rank == 0:
            status = "FOUND_CORRECT_CITE" if page_ok else "FOUND_WRONG_CITE"
        else:
            status = "NEAR_MISS"

        return {
            **base,
            "status": status,
            "matched_value": val,
            "matched_label": val_label,
            "pipeline_label": pipeline_label,
            "pipeline_page": pipeline_page,
            "page_ok": page_ok,
            "rank": rank,
            "note": f"{'Primary' if rank == 0 else 'Secondary'} value {val_label} matched pipeline fact «{pipeline_label[:60]}»",
        }

    tried = [label for _, label in candidates[:5]]
    return {
        **base,
        "status": "MISSING",
        "candidates_tried": tried,
        "note": f"Tried {len(candidates)} candidate value(s), none found in pipeline facts",
    }


# ── Risk coverage ────────────────────────────────────────────────────────────

def risk_keywords(claim: str) -> list[str]:
    """Extract all distinctive content words (≥5 chars) from a gold risk claim.

    Returns unique words in order of appearance, filtered against stopwords.
    Using ≥5 chars avoids very generic short words; all words are included
    (not top-N) so the most relevant word is never accidentally excluded.
    """
    words = re.findall(r'\b[a-z]{5,}\b', claim.lower())
    seen: set[str] = set()
    result = []
    for w in words:
        if w not in STOPWORDS and w not in seen:
            seen.add(w)
            result.append(w)
    return result


def kw_in_text(kw: str, text: str) -> bool:
    """True if the first RISK_KEYWORD_STEM characters of kw appear anywhere in text.

    Using a stem prefix handles morphological variants:
      'disintermediate' matches 'disintermediation'
      'regulatory' matches 'regulation', 'regulators'
      'employees' matches 'employee', 'employment'
    """
    stem = kw[:RISK_KEYWORD_STEM].lower()
    return stem in text


def score_risk(gold_risk: dict, risk_section_text: str) -> dict:
    """Check keyword-stem presence in memo's risk section.

    COVERED  : ≥ RISK_KEYWORD_THRESHOLD stems matched
    FLAGGED  : exactly 1 stem matched (manual adjudication)
    MISSING  : 0 stems matched
    """
    keywords = risk_keywords(gold_risk["claim"])
    section_lower = risk_section_text.lower()
    matched = [kw for kw in keywords if kw_in_text(kw, section_lower)]

    if len(matched) >= RISK_KEYWORD_THRESHOLD:
        status = "COVERED"
    elif len(matched) == 1:
        status = "FLAGGED"
    else:
        status = "MISSING"

    return {
        "id": gold_risk["id"],
        "claim": gold_risk["claim"],
        "status": status,
        "keywords_used": keywords,
        "keywords_matched": matched,
    }


# ── Markdown writers ─────────────────────────────────────────────────────────

def write_results_md(
    fact_results: list[dict],
    risk_results: list[dict],
    out_path: Path,
) -> None:
    found = [r for r in fact_results if r["status"] in ("FOUND_CORRECT_CITE", "FOUND_WRONG_CITE")]
    correct_cite = [r for r in fact_results if r["status"] == "FOUND_CORRECT_CITE"]
    near_miss = [r for r in fact_results if r["status"] == "NEAR_MISS"]
    missing = [r for r in fact_results if r["status"] == "MISSING"]

    risks_covered = [r for r in risk_results if r["status"] == "COVERED"]
    risks_flagged = [r for r in risk_results if r["status"] == "FLAGGED"]
    risks_missing = [r for r in risk_results if r["status"] == "MISSING"]

    n_facts = len(fact_results)
    n_risks = len(risk_results)

    cite_str = (
        f"{len(correct_cite)}/{len(found)} ({100*len(correct_cite)//len(found)}%)"
        if found else "N/A"
    )

    today = date.today().strftime("%-d %B %Y")

    lines: list[str] = [
        "# Evaluation Results — Auto Trader Group plc FY2026",
        f"**Run date:** {today}",
        "",
        "---",
        "",
        "## Automated Metrics Summary",
        "",
        "| Metric | Score | Notes |",
        "|--------|-------|-------|",
        f"| Fact recall (primary-value match) | {len(found)}/{n_facts} "
        f"({100*len(found)//n_facts}%) | {len(near_miss)} near-miss(es) flagged for adjudication |",
        f"| Citation accuracy (of found facts) | {cite_str} | Page within ±{CITATION_TOL} of gold |",
        f"| Risk coverage (≥{RISK_KEYWORD_THRESHOLD} keyword-stem matches) | "
        f"{len(risks_covered)}/{n_risks} ({100*len(risks_covered)//n_risks}%) | "
        f"{len(risks_flagged)} flagged for adjudication, {len(risks_missing)} missing |",
        "",
        "> **Observation coverage** and **diligence question quality** require human judgement.",
        "> See `eval/scoring_sheet.md` — fill that in before updating this file.",
        "",
        "---",
        "",
        "## 1. Fact Recall — F-01 to F-20",
        "",
        "Source: `output/validated_facts.json` (verified + corrected financial figures).",
        f"Match: primary value from claim within ±{int(TOLERANCE*100)}% of pipeline fact value.",
        f"Citation: pipeline page within ±{CITATION_TOL} of gold page.",
        "",
    ]

    # ── Found ──
    if found:
        lines += ["### Found ✓", ""]
        lines += [
            "| ID | Claim (abbreviated) | Matched | Pipeline label | Gold pg | Pipeline pg | Cite |",
            "|----|---------------------|---------|----------------|---------|-------------|------|",
        ]
        for r in sorted(found, key=lambda x: x["id"]):
            short = (r["claim"][:65] + "…") if len(r["claim"]) > 65 else r["claim"]
            cite = "✓" if r.get("page_ok") else "✗"
            lines.append(
                f"| {r['id']} | {short} | {r.get('matched_label','?')} | "
                f"{r.get('pipeline_label','?')[:45]} | {r['gold_page']} | "
                f"{r.get('pipeline_page','?')} | {cite} |"
            )
        lines.append("")

    # ── Near-miss ──
    if near_miss:
        lines += [
            "### Near-miss — manual adjudication needed ⚠",
            "",
            "Primary value not in pipeline facts; a secondary value matched.",
            "Check whether the pipeline captured the same fact under a different label.",
            "",
            "| ID | Claim (abbreviated) | Secondary match | Pipeline label | Gold pg | Pipeline pg |",
            "|----|---------------------|-----------------|----------------|---------|-------------|",
        ]
        for r in sorted(near_miss, key=lambda x: x["id"]):
            short = (r["claim"][:65] + "…") if len(r["claim"]) > 65 else r["claim"]
            lines.append(
                f"| {r['id']} | {short} | {r.get('matched_label','?')} | "
                f"{r.get('pipeline_label','?')[:45]} | {r['gold_page']} | "
                f"{r.get('pipeline_page','?')} |"
            )
        lines.append("")

    # ── Missing ──
    if missing:
        lines += [
            "### Missing ✗",
            "",
            "| ID | Claim (abbreviated) | Values tried | Note |",
            "|----|---------------------|--------------|------|",
        ]
        for r in sorted(missing, key=lambda x: x["id"]):
            short = (r["claim"][:65] + "…") if len(r["claim"]) > 65 else r["claim"]
            tried = ", ".join(r.get("candidates_tried", [])[:4])
            lines.append(
                f"| {r['id']} | {short} | {tried} | {r.get('note','')} |"
            )
        lines.append("")

    # ── Risk coverage ──
    lines += [
        "---",
        "",
        "## 2. Risk Coverage — R-01 to R-10",
        "",
        "> **Important:** this is an automated vocabulary estimate, not a definitive score.",
        "> Common business words ('consumer', 'retailer', 'revenue') can match in unrelated",
        "> contexts and produce false positives. **Verify every COVERED result manually**",
        "> against the Section 6 text before accepting the score. See `eval/scoring_sheet.md`",
        "> Part C for a verification table.",
        "",
        f"Source: memo Section 6 (Material Risks).",
        f"Method: all content words ≥5 chars from each gold risk claim;",
        f"{RISK_KEYWORD_STEM}-char stem prefix (handles morphological variants like",
        f"'disintermediate' → 'disintermediation'); COVERED = ≥{RISK_KEYWORD_THRESHOLD} matches.",
        "",
        "| ID | Gold risk (abbreviated) | Auto status | Matched stems | All stems checked |",
        "|----|------------------------|-------------|---------------|-------------------|",
    ]
    status_icons = {"COVERED": "✓ COVERED (verify)", "FLAGGED": "⚠ FLAGGED", "MISSING": "✗ MISSING"}
    for r in risk_results:
        short = (r["claim"][:60] + "…") if len(r["claim"]) > 60 else r["claim"]
        matched_str = ", ".join(r["keywords_matched"][:6]) or "—"
        checked_str = ", ".join(r["keywords_used"][:8])
        lines.append(
            f"| {r['id']} | {short} | {status_icons.get(r['status'], r['status'])} | "
            f"{matched_str} | {checked_str}… |"
        )
    lines.append("")

    if risks_flagged:
        lines += [
            "**Flagged (auto):** 1 stem match — may be coincidental. Check Section 6 directly.",
            "",
        ]
    if risks_missing:
        lines += [
            "**Missing (auto):** 0 stem matches — risk likely not covered in Section 6.",
            "",
        ]

    # ── Failure analysis table ──
    lines += [
        "---",
        "",
        "## 3. Failure Analysis",
        "",
        "*(Complete manually after reviewing the per-item detail above.)*",
        "*(For each miss, classify: extraction fault / chunking fault / prompt fault / validation gap.)*",
        "",
        "| Item | Category | Fault type | Diagnosis |",
        "|------|----------|------------|-----------|",
        "| — | — | — | — |",
        "",
        "---",
        "",
        "## 4. Manual Metric Results",
        "",
        "*(Paste results from `eval/scoring_sheet.md` here after scoring.)*",
        "",
        "| Metric | Score | Notes |",
        "|--------|-------|-------|",
        "| Observation coverage (O-01..O-10) | ? / 10 | |",
        "| Diligence question quality | ? rated 3, ? rated 2, ? rated 1 | |",
        "",
        "---",
        "",
        "*Generated by `eval/run_eval.py`. Automated rows must not be edited manually.*",
        f"*Tolerance: ±{int(TOLERANCE*100)}% value, ±{CITATION_TOL} page, {RISK_KEYWORD_STEM}-char stem prefix, ≥{RISK_KEYWORD_THRESHOLD} stems.*",
    ]

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


def write_scoring_sheet(
    gold: dict,
    analytics: dict,
    out_path: Path,
) -> None:
    today = date.today().strftime("%-d %B %Y")
    pipeline_questions = analytics.get("diligence_questions", [])
    analytical_sections = [
        ("Strengths", analytics.get("strengths", [])),
        ("Value Drivers", analytics.get("value_drivers", [])),
        ("Bull Case", analytics.get("bull_case", [])),
        ("Bear Case", analytics.get("bear_case", [])),
        ("Risks", analytics.get("risks", [])),
    ]

    lines: list[str] = [
        "# Evaluation Scoring Sheet — Manual Metrics",
        f"**To be completed by:** Zak Whatmough  **Date generated:** {today}",
        "",
        "This file covers two metrics that require human judgement.",
        "**Do not ask the model to fill this in** — the model must not grade its own analytical quality.",
        "",
        "---",
        "",
        "## Instructions",
        "",
        "### Part A — Observation coverage",
        "For each gold observation (O-01..O-10), decide if the pipeline analytical output",
        "(the items listed below) captures the same insight:",
        "- **COVERED**: the pipeline makes the same core point",
        "- **PARTIAL**: it touches the theme but misses the key nuance",
        "- **MISSING**: the pipeline does not surface this insight at all",
        "",
        "### Part B — Diligence question quality",
        "Rate each of the pipeline's diligence questions on a 1–3 scale:",
        "- **1** = Irrelevant, generic, or trivially answered from the memo",
        "- **2** = Plausible but not specifically useful for this company or situation",
        "- **3** = Genuinely useful — a competent analyst would ask exactly this",
        "",
        "---",
        "",
        "## Part A: Observation Coverage (O-01 to O-10)",
        "",
        "| ID | Gold observation (first 120 chars) | Your rating | Notes |",
        "|----|-----------------------------------|-------------|-------|",
    ]
    for obs in gold.get("business_observations", []):
        short = (obs["claim"][:120] + "…") if len(obs["claim"]) > 120 else obs["claim"]
        lines.append(f"| {obs['id']} | {short} | COVERED / PARTIAL / MISSING | |")
    lines += [
        "",
        "**Part A summary:** ___ / 10 COVERED, ___ PARTIAL, ___ MISSING",
        "",
    ]

    # Pipeline analytical items for reference
    lines += [
        "### Pipeline analytical items (reference for Part A)",
        "",
        "Check these items when completing the table above.",
        "",
    ]
    for section_name, items in analytical_sections:
        if not items:
            continue
        lines.append(f"**{section_name}**")
        for i, item in enumerate(items, 1):
            stmt = item.get("statement", "")
            tag = " *(inference)*" if item.get("inference") else ""
            lines.append(f"{i}. {stmt}{tag}")
        lines.append("")

    # Part B
    lines += [
        "---",
        "",
        "## Part B: Diligence Question Quality",
        "",
        "### Pipeline's diligence questions",
        "",
        "| # | Pipeline question (first 130 chars) | Rating (1/2/3) | Notes |",
        "|---|-------------------------------------|----------------|-------|",
    ]
    for i, q in enumerate(pipeline_questions, 1):
        stmt = q.get("statement", "")
        short = (stmt[:130] + "…") if len(stmt) > 130 else stmt
        lines.append(f"| {i} | {short} | | |")
    lines += [
        "",
        "**Part B summary:** ___ questions rated 3, ___ rated 2, ___ rated 1",
        "",
        "### Gold diligence questions (benchmark)",
        "",
        "The pipeline need not reproduce these exactly — use them as a standard for",
        "what a competent analyst would ask. A pipeline question on the same theme",
        "with the same analytical depth deserves a 3.",
        "",
        "| ID | Gold question (first 130 chars) |",
        "|----|--------------------------------|",
    ]
    for q in gold.get("diligence_questions", []):
        short = (q["claim"][:130] + "…") if len(q["claim"]) > 130 else q["claim"]
        lines.append(f"| {q['id']} | {short} |")
    lines += [
        "",
        "---",
        "",
        "## Part C: Risk Coverage Verification (R-01 to R-10)",
        "",
        "The automated keyword score in `eval/results.md §2` may have false positives",
        "(common words matching in unrelated contexts). Verify each automated COVERED",
        "result by reading Section 6 of the memo and confirming the risk theme is genuinely",
        "present. Override automated status where it is wrong.",
        "",
        "| ID | Gold risk theme (abbreviated) | Auto score | Your verdict | Notes |",
        "|----|------------------------------|------------|-------------|-------|",
    ]
    for r in gold.get("key_risks", []):
        short = (r["claim"][:80] + "…") if len(r["claim"]) > 80 else r["claim"]
        lines.append(f"| {r['id']} | {short} | (see results.md §2) | COVERED / PARTIAL / MISSING | |")
    lines += [
        "",
        "**Part C summary:** ___ / 10 COVERED (verified), ___ PARTIAL, ___ MISSING",
        "",
        "---",
        "",
        "*Complete this sheet independently of the pipeline. Do not re-run or adjust*",
        "*outputs after scoring. Transfer results to `eval/results.md` Section 4.*",
    ]

    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Score the pipeline against the frozen gold set")
    parser.add_argument("--gold",       default=str(ROOT / "eval" / "gold_set.json"))
    parser.add_argument("--validated",  default=str(ROOT / "output" / "validated_facts.json"))
    parser.add_argument("--memo",       default=str(ROOT / "output" / "memo.md"))
    parser.add_argument("--classified", default=str(ROOT / "output" / "classified_facts.json"))
    parser.add_argument("--results",    default=str(ROOT / "eval" / "results.md"))
    parser.add_argument("--scoring",    default=str(ROOT / "eval" / "scoring_sheet.md"))
    args = parser.parse_args()

    print("Loading inputs...")
    gold = load_gold_set(Path(args.gold))
    pipeline_facts = load_validated_facts(Path(args.validated))
    with open(args.memo) as f:
        memo_text = f.read()
    classified = load_classified(Path(args.classified))
    analytics = classified.get("analytics", {})

    print(f"  {len(pipeline_facts)} verified pipeline facts")
    print(f"  {len(gold['factual_data_points'])} gold facts, {len(gold['key_risks'])} gold risks")

    # ── 1. Fact recall ──
    print("\nScoring fact recall (F-01..F-20)...")
    fact_results = []
    for gf in gold["factual_data_points"]:
        r = score_fact(gf, pipeline_facts)
        fact_results.append(r)
        icon = {
            "FOUND_CORRECT_CITE": "✓",
            "FOUND_WRONG_CITE":   "~",
            "NEAR_MISS":          "⚠",
            "MISSING":            "✗",
        }.get(r["status"], "?")
        claim_short = gf["claim"][:70] + "…" if len(gf["claim"]) > 70 else gf["claim"]
        print(f"  {icon} {gf['id']}: {claim_short}")

    found = [r for r in fact_results if r["status"] in ("FOUND_CORRECT_CITE", "FOUND_WRONG_CITE")]
    near_miss = [r for r in fact_results if r["status"] == "NEAR_MISS"]
    correct_cite = [r for r in fact_results if r["status"] == "FOUND_CORRECT_CITE"]

    print(f"\n  Recall:   {len(found)}/{len(fact_results)} found "
          f"({len(near_miss)} near-miss for adjudication)")
    if found:
        print(f"  Citation: {len(correct_cite)}/{len(found)} correct page")

    # ── 2. Risk coverage ──
    print("\nScoring risk coverage (R-01..R-10)...")
    risk_section = extract_memo_section(memo_text, 6)
    if not risk_section:
        print("  WARNING: could not extract Section 6 from memo.md")

    risk_results = []
    for gr in gold["key_risks"]:
        r = score_risk(gr, risk_section)
        risk_results.append(r)
        icon = {"COVERED": "✓", "FLAGGED": "⚠", "MISSING": "✗"}.get(r["status"], "?")
        claim_short = gr["claim"][:70] + "…" if len(gr["claim"]) > 70 else gr["claim"]
        print(f"  {icon} {gr['id']}: {claim_short}")

    covered = sum(1 for r in risk_results if r["status"] == "COVERED")
    flagged = sum(1 for r in risk_results if r["status"] == "FLAGGED")
    print(f"\n  Coverage: {covered}/{len(risk_results)} covered, {flagged} flagged")

    # ── 3. Write outputs ──
    print(f"\nWriting {args.results}...")
    write_results_md(fact_results, risk_results, Path(args.results))

    print(f"Writing {args.scoring}...")
    write_scoring_sheet(gold, analytics, Path(args.scoring))

    print("\nDone.")
    print(f"  {args.results} — automated results")
    print(f"  {args.scoring} — fill this in before updating results.md §4")


if __name__ == "__main__":
    main()
