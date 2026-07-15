"""app.py — Streamlit review application for the Auto Trader investment memo.

Loads the AI-generated memo and its evidence register, and provides two views:

  Tab 1 – Memo & Evidence
    Read the investment memo on the left. Select any [E-NNN] reference from the
    dropdown on the right to see the underlying evidence: the extracted claim,
    which PDF page it came from, and the exact verbatim quote that was verified
    against the source document.

  Tab 2 – Facts Browser
    Browse all 249 facts extracted from the annual report, with filters by
    memo section, relevance score (1 = exclude, 5 = headline), and citation
    status (verified / corrected).

No database, no back-end API — just local JSON files and Streamlit.

Run with:
    streamlit run app.py
"""

import json
import re
from pathlib import Path

import streamlit as st

# ── File paths ────────────────────────────────────────────────────────────────

ROOT = Path(__file__).parent
MEMO_PATH       = ROOT / "output" / "memo.md"
REGISTER_PATH   = ROOT / "output" / "evidence_register.json"
CLASSIFIED_PATH = ROOT / "output" / "classified_facts.json"
VALIDATED_PATH  = ROOT / "output" / "validated_facts.json"

# ── Human-readable labels ─────────────────────────────────────────────────────

SECTION_LABELS = {
    "business_overview":    "Business Overview",
    "financial_performance":"Financial Performance",
    "strategy":             "Strategy",
    "risks":                "Risks",
    "management":           "Management",
    "investment_case":      "Investment Case",
}

CATEGORY_LABELS = {
    "financial_figures":    "Financial Figure",
    "business_facts":       "Business Fact",
    "risk_disclosures":     "Risk Disclosure",
    "strategic_items":      "Strategic Item",
    "management_commentary":"Management Commentary",
}

RELEVANCE_LABELS = {
    5: "5 – Headline",
    4: "4 – Supporting",
    3: "3 – Contextual",
    2: "2 – Peripheral",
    1: "1 – Exclude",
}

ALL_FACT_CATEGORIES = [
    "financial_figures", "business_facts", "risk_disclosures",
    "strategic_items", "management_commentary",
]


# ── Data loading (cached so files are only read once per session) ─────────────

@st.cache_data
def load_all() -> tuple[str, dict, list, dict]:
    """Load and cross-reference all output files.

    Returns:
        memo_text        — raw markdown of the memo
        register         — {E-001: {...}, ...} evidence register
        classified_facts — list of all 249 classified fact dicts
        excerpt_lookup   — {fact_id: {excerpt, doc_id}} for inline source quotes
    """
    memo_text = MEMO_PATH.read_text()

    with open(REGISTER_PATH) as f:
        register = json.load(f)

    with open(CLASSIFIED_PATH) as f:
        cf = json.load(f)
    classified_facts = cf.get("classified_facts", [])

    # Build excerpt lookup from validated_facts.json.
    # The fact_id key format is: {chunk_id}__{category}__{index}
    excerpt_lookup: dict[str, dict] = {}
    with open(VALIDATED_PATH) as f:
        chunks = json.load(f)
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        for cat in ALL_FACT_CATEGORIES:
            for idx, item in enumerate(chunk.get(cat, [])):
                fact_id = f"{chunk_id}__{cat}__{idx}"
                src = item.get("source", {})
                excerpt_lookup[fact_id] = {
                    "excerpt": src.get("excerpt", ""),
                    "doc_id":  src.get("doc_id", "at-ar-fy26"),
                }

    return memo_text, register, classified_facts, excerpt_lookup


# ── Shared helpers ────────────────────────────────────────────────────────────

def bold_references(text: str) -> str:
    """Make [E-NNN] citations bold so they stand out in the rendered memo."""
    return re.sub(r'\[E-(\d+)\]', r'**[E-\1]**', text)


def render_evidence_card(
    e_id: str,
    entry: dict,
    excerpt_lookup: dict,
) -> None:
    """Render the full details of one evidence register entry."""
    fact_id = entry.get("fact_id", "")
    src     = excerpt_lookup.get(fact_id, {})
    excerpt = src.get("excerpt", "")
    doc_id  = src.get("doc_id", "at-ar-fy26")

    st.markdown(f"#### {e_id}")

    # Claim / label — add the numeric value if this is a financial figure
    label = entry.get("label", "—")
    if entry.get("value") not in (None, ""):
        label += f" = **{entry['value']} {entry.get('unit', '')}**"
    if entry.get("period"):
        label += f" ({entry['period']})"
    st.markdown(f"**Claim:** {label}")

    # Metadata row
    section  = SECTION_LABELS.get(entry.get("memo_section", ""), entry.get("memo_section", "—"))
    category = CATEGORY_LABELS.get(entry.get("category", ""), entry.get("category", "—"))
    status   = entry.get("citation_status", "—")
    rel      = entry.get("relevance", "—")
    page     = entry.get("source_page", "—")

    st.markdown(
        f"📄 `{doc_id}.pdf` · page **{page}** &nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Section: *{section}* &nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Category: *{category}* &nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Relevance: **{rel}**/5 &nbsp;&nbsp;|&nbsp;&nbsp;"
        f"Status: `{status}`",
        unsafe_allow_html=True,
    )

    # Verified excerpt (the verbatim quote from the PDF that was string-matched)
    if excerpt:
        st.markdown("**Verified source excerpt** *(exact quote found in the PDF):*")
        st.info(f"> {excerpt}")
    else:
        st.caption(
            "No verbatim excerpt available — this fact comes from an infographic "
            "or KPI summary box where pdfplumber cannot extract contiguous text."
        )


# ── Tab 1: Memo & Evidence ────────────────────────────────────────────────────

def tab_memo(memo_text: str, register: dict, excerpt_lookup: dict) -> None:
    col_memo, col_panel = st.columns([3, 2], gap="large")

    # Right panel — evidence lookup (render first so it appears fixed visually)
    with col_panel:
        st.subheader("Evidence Panel")
        st.caption(
            "Each **[E-NNN]** reference in the memo cites a fact from this register. "
            "Select a reference to see the underlying evidence."
        )

        e_ids = list(register.keys())
        selected = st.selectbox(
            "Select a reference",
            options=e_ids,
            format_func=lambda x: f"{x} — {register[x].get('label', '')[:55]}",
        )

        st.divider()

        if selected and selected in register:
            render_evidence_card(selected, register[selected], excerpt_lookup)

        st.divider()
        n_cited = sum(1 for v in register.values() if v.get("cited_in_memo"))
        st.caption(
            f"Register: {len(register)} entries (E-001 – E-{len(register):03d}) · "
            f"{n_cited} cited in memo"
        )

    # Left column — memo text
    with col_memo:
        st.subheader("Investment Memo")
        st.caption(
            "References like **[E-003]** mark claims with source evidence. "
            "Select any reference in the panel → to see the underlying quote."
        )
        st.divider()

        # Strip the top-level H1 and the metadata block (already shown in page title)
        display = re.sub(r'^#\s+Investment Memo[^\n]*\n', '', memo_text, count=1)
        display = re.sub(
            r'\*\*Prepared by:\*\*.*?---\n+', '', display,
            flags=re.DOTALL, count=1,
        )
        st.markdown(bold_references(display))


# ── Tab 2: Facts Browser ──────────────────────────────────────────────────────

def tab_facts(classified_facts: list, excerpt_lookup: dict) -> None:
    st.subheader("Facts Browser")
    st.caption(
        "All facts extracted from the annual report by the pipeline. "
        "**Relevance** is the AI's 1–5 rating for memo importance (5 = cited directly, "
        "1 = excluded). **Citation status** shows whether the verbatim excerpt was "
        "found in the source PDF."
    )

    # ── Filters ──────────────────────────────────────────────────────────────
    all_sections = sorted({f.get("memo_section", "") for f in classified_facts if f.get("memo_section")})
    all_statuses = sorted({f.get("citation_status", "") for f in classified_facts if f.get("citation_status")})

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        section_filter = st.multiselect(
            "Memo section",
            options=all_sections,
            default=all_sections,
            format_func=lambda s: SECTION_LABELS.get(s, s),
        )
    with fc2:
        relevance_filter = st.multiselect(
            "Relevance",
            options=[5, 4, 3, 2, 1],
            default=[5, 4, 3],
            format_func=lambda r: RELEVANCE_LABELS.get(r, str(r)),
        )
    with fc3:
        status_filter = st.multiselect(
            "Citation status",
            options=all_statuses,
            default=all_statuses,
        )

    # ── Apply filters ─────────────────────────────────────────────────────────
    filtered = [
        f for f in classified_facts
        if f.get("memo_section") in section_filter
        and f.get("relevance") in relevance_filter
        and f.get("citation_status") in status_filter
    ]

    st.caption(f"Showing **{len(filtered)}** of {len(classified_facts)} facts")
    st.divider()

    # ── Render each fact ──────────────────────────────────────────────────────
    for fact in filtered:
        label    = fact.get("label", "—")
        category = CATEGORY_LABELS.get(fact.get("category", ""), fact.get("category", ""))
        relevance = fact.get("relevance", "—")
        page      = fact.get("source_page", "—")
        status    = fact.get("citation_status", "—")

        # Build a summary line for the expander title
        value_str = ""
        if fact.get("value") not in (None, ""):
            value_str = f" = {fact['value']} {fact.get('unit', '')} ({fact.get('period', '')})"

        chunk_prefix = fact.get("id", "").split("__")[0].replace("at-ar-fy26_", "")
        title = f"[p{page} · {chunk_prefix}] {label[:80]}{value_str}"

        with st.expander(title):
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Category:** {category}")
                st.markdown(f"**Memo section:** {SECTION_LABELS.get(fact.get('memo_section', ''), '—')}")
                st.markdown(f"**Relevance:** {relevance}/5")
            with c2:
                st.markdown(f"**Citation status:** `{status}`")
                st.markdown(f"**Source page:** {page}")
                st.markdown(f"**Confidence:** {fact.get('confidence', '—')}")

            if fact.get("rationale"):
                st.markdown(f"**Classification rationale:** *{fact['rationale']}*")

            # Excerpt from validated facts
            fact_id = fact.get("id", "")
            src_info = excerpt_lookup.get(fact_id, {})
            excerpt  = src_info.get("excerpt", "")
            if excerpt:
                st.markdown("**Source excerpt:**")
                st.info(f"> {excerpt}")


# ── Main entry point ──────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Auto Trader FY2026 — Memo Review",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Load all data (cached after first run)
    try:
        memo_text, register, classified_facts, excerpt_lookup = load_all()
    except FileNotFoundError as e:
        st.error(
            f"**Missing data file:** `{e}`\n\n"
            "Run the full pipeline first:\n"
            "```\npython extract.py\npython validate.py\n"
            "python finance.py\npython prior_year.py\n"
            "python classify.py\npython memo.py\n```"
        )
        st.stop()

    # Page title
    st.title("Auto Trader Group plc FY2026 — AI Memo Review")
    st.caption(
        "AI-assisted first draft. Every material claim is traceable to a verified "
        "source excerpt. This tool is for review, not for investment decisions."
    )

    tab1, tab2 = st.tabs(["📄 Memo & Evidence", "🔍 Facts Browser"])

    with tab1:
        tab_memo(memo_text, register, excerpt_lookup)

    with tab2:
        tab_facts(classified_facts, excerpt_lookup)


if __name__ == "__main__":
    main()
