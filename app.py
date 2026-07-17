"""app.py — Investment Memo Assistant: demo and "run your own" modes.

Demo mode (default)
  Choose Auto Trader (V3), Greggs, or Games Workshop from the sidebar.
  The finished memo loads instantly with its full evidence chain.
  No API key needed — all data is pre-committed to the repo.

Run your own
  Upload a UK-listed company annual report PDF and paste your Anthropic
  API key (held in session memory only, never written to disk). A
  deterministic pre-flight check runs first; if it passes, the full
  pipeline runs and produces a new memo in 5–10 minutes for roughly $1
  of your API credits.

No database. One file. Explainable to a non-engineer.
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

import pdfplumber
import streamlit as st
import yaml

# ── Demo company registry ──────────────────────────────────────────────────────
# Pre-committed data lets the demo run without any API key or source PDF.

ROOT = Path(__file__).parent

DEMO_COMPANIES = {
    "Auto Trader Group plc (FY2026 — evaluated)": {
        "memo":       ROOT / "output" / "memo.md",
        "register":   ROOT / "output" / "evidence_register.json",
        "classified": ROOT / "output" / "classified_facts.json",
        "validated":  ROOT / "output" / "validated_facts.json",
        "blurb": (
            "UK's largest digital automotive marketplace. "
            "V3 pipeline, scored against a 50-item gold set: "
            "fact recall 90%, risk coverage 80%, observation coverage 90%."
        ),
    },
    "Greggs plc (FY2025)": {
        "memo":       ROOT / "output" / "greggs" / "memo.md",
        "register":   ROOT / "output" / "greggs" / "evidence_register.json",
        "classified": ROOT / "output" / "greggs" / "classified_facts.json",
        "validated":  ROOT / "output" / "greggs" / "validated_facts.json",
        "blurb": (
            "UK's leading food-to-go bakery retailer. "
            "Second-company generalisation test: 249/252 facts verified (98%), "
            "qualitative review 8.8–9.0/10."
        ),
    },
    "Games Workshop Group PLC (FY2025)": {
        "memo":       ROOT / "output" / "gw" / "memo.md",
        "register":   ROOT / "output" / "gw" / "evidence_register.json",
        "classified": ROOT / "output" / "gw" / "classified_facts.json",
        "validated":  ROOT / "output" / "gw" / "validated_facts.json",
        "blurb": (
            "Warhammer IP owner: Core miniatures + Licensing (Amazon Prime). "
            "Third-company config-only test: 145/145 facts verified (100%), "
            "qualitative review 9.4/10."
        ),
    },
}

# ── Human-readable label maps ──────────────────────────────────────────────────

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

FACT_KEYS = [
    "financial_figures", "business_facts", "risk_disclosures",
    "strategic_items", "management_commentary",
]

# Terms that signal a bank or insurer — reject politely if 2+ present.
_BANK_INSURER_TERMS = [
    "net interest income", "net interest margin", "underwriting",
    "solvency ii", "combined ratio", "tier 1 capital", "insurance premium",
    "loan book", "loan to value", "credit risk weighted", "premium income",
    "claims incurred", "loss ratio",
]

# Heading variants that work for most UK FTSE annual reports.
_GENERIC_TAXONOMY = {
    "strategic_overview": {
        "heading_variants": [
            "strategic report", "chair's statement", "chairman's statement",
            "chief executive", "business review", "ceo review",
        ],
        "description": "Strategic overview and business review",
        "max_pages": 25,
        "fallback_pages": [2, 35],
    },
    "principal_risks": {
        "heading_variants": [
            "principal risks and uncertainties", "principal risks",
            "risks and uncertainties", "key risks", "risk management",
        ],
        "description": "Principal risks and uncertainties",
        "max_pages": 15,
        "fallback_pages": [36, 60],
    },
    "financial_statements": {
        "heading_variants": [
            "consolidated income statement",
            "consolidated statement of profit",
            "income statement",
            "profit and loss",
        ],
        "description": "Primary financial statements",
        "max_pages": 8,
        "fallback_pages": [61, 85],
    },
}


# ── Pre-flight suitability checks (no API calls) ──────────────────────────────

def run_preflight(pdf_bytes: bytes) -> list[dict]:
    """Run deterministic checks on uploaded PDF bytes.

    Returns a list of result dicts:
      {"label": str, "passed": bool, "detail": str}

    All checks are cheap (pdfplumber text extraction only).
    No API calls are made here.
    """
    results = []

    # ── 1. Text extractable ────────────────────────────────────────────────────
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            total_pages = len(pdf.pages)
            sample_texts = []
            for page in pdf.pages[:10]:
                t = page.extract_text() or ""
                if t.strip():
                    sample_texts.append(t)
            full_texts = []
            for page in pdf.pages:
                t = page.extract_text() or ""
                full_texts.append(t)
    except Exception as e:
        results.append({
            "label": "Text extractable",
            "passed": False,
            "detail": f"Could not open PDF: {e}",
        })
        return results  # can't continue if PDF won't open

    text_pages = sum(1 for t in full_texts if len(t.strip()) > 50)
    if text_pages < 5:
        results.append({
            "label": "Text extractable (not a scanned image PDF)",
            "passed": False,
            "detail": (
                f"Only {text_pages} pages contain extractable text. "
                "This tool requires a digitally-created PDF. "
                "Scanned documents are not supported."
            ),
        })
        return results
    results.append({
        "label": "Text extractable (not a scanned image PDF)",
        "passed": True,
        "detail": f"{text_pages} of {total_pages} pages contain extractable text.",
    })

    # ── 2. Page count ──────────────────────────────────────────────────────────
    if total_pages < 40:
        results.append({
            "label": "Page count in expected range",
            "passed": False,
            "detail": (
                f"{total_pages} pages. UK annual reports are typically 80–350 pages. "
                "This looks too short — it may be an interim report or a different document type."
            ),
        })
    elif total_pages > 500:
        results.append({
            "label": "Page count in expected range",
            "passed": False,
            "detail": (
                f"{total_pages} pages. This is unusually long. "
                "The pipeline is designed for single-company annual reports (typically up to 350 pages). "
                "Please check you've uploaded the right file."
            ),
        })
    else:
        results.append({
            "label": "Page count in expected range",
            "passed": True,
            "detail": f"{total_pages} pages.",
        })

    # ── 3. Annual-report heading signals ──────────────────────────────────────
    combined = " ".join(full_texts).lower()
    ar_signals = [
        ("strategic report", "strategic report"),
        ("principal risks", "principal risks"),
        ("directors' report", "directors' report"),
        ("annual report", "annual report"),
    ]
    found_signals = [label for term, label in ar_signals if term in combined]
    if len(found_signals) >= 2:
        results.append({
            "label": "Looks like a UK annual report",
            "passed": True,
            "detail": f"Found: {', '.join(found_signals)}.",
        })
    else:
        results.append({
            "label": "Looks like a UK annual report",
            "passed": False,
            "detail": (
                f"Expected heading signals not found (found: {found_signals or 'none'}). "
                "This tool is designed for UK listed-company annual reports containing "
                "a Strategic Report and Principal Risks section."
            ),
        })

    # ── 4. Not a bank or insurer ───────────────────────────────────────────────
    hits = [term for term in _BANK_INSURER_TERMS if term in combined]
    if len(hits) >= 3:
        results.append({
            "label": "Not a bank or insurer",
            "passed": False,
            "detail": (
                f"Found {len(hits)} financial-sector terms ({', '.join(hits[:5])}…). "
                "Banks and insurers use specialised financial reporting frameworks "
                "(IFRS 9 / 17, Solvency II) that this pipeline does not support. "
                "Please use the tool with non-financial-sector annual reports."
            ),
        })
    else:
        results.append({
            "label": "Not a bank or insurer",
            "passed": True,
            "detail": (
                "No strong bank/insurance signals detected."
                if not hits else
                f"Minor hits ({', '.join(hits)}) — below rejection threshold."
            ),
        })

    return results


# ── Data loading ───────────────────────────────────────────────────────────────

@st.cache_data
def load_demo_data(company_key: str) -> tuple[str, dict, list, dict]:
    """Load pre-committed output files for a demo company.

    Returns (memo_text, register, classified_facts, excerpt_lookup).
    Cached per company_key so files are only read once per session.
    """
    cfg = DEMO_COMPANIES[company_key]
    return _load_from_paths(
        cfg["memo"], cfg["register"], cfg["classified"], cfg["validated"]
    )


def _load_from_paths(
    memo_path, register_path, classified_path, validated_path
) -> tuple[str, dict, list, dict]:
    """Load and cross-reference the four output files."""
    memo_text = Path(memo_path).read_text()

    with open(register_path) as f:
        register = json.load(f)

    with open(classified_path) as f:
        cf = json.load(f)
    classified_facts = cf.get("classified_facts", [])

    # Build fact_id → excerpt lookup from validated chunks
    excerpt_lookup: dict[str, dict] = {}
    with open(validated_path) as f:
        chunks = json.load(f)
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id", "")
        for cat in FACT_KEYS:
            for idx, item in enumerate(chunk.get(cat, [])):
                fact_id = f"{chunk_id}__{cat}__{idx}"
                src = item.get("source", {})
                excerpt_lookup[fact_id] = {
                    "excerpt": src.get("excerpt", ""),
                    "doc_id":  src.get("doc_id", ""),
                }

    return memo_text, register, classified_facts, excerpt_lookup


def _load_from_dicts(
    memo_text: str,
    register: dict,
    classified_facts: list,
    validated_chunks: list,
) -> tuple[str, dict, list, dict]:
    """Same as _load_from_paths but from already-parsed data (for 'run your own')."""
    excerpt_lookup: dict[str, dict] = {}
    for chunk in validated_chunks:
        chunk_id = chunk.get("chunk_id", "")
        for cat in FACT_KEYS:
            for idx, item in enumerate(chunk.get(cat, [])):
                fact_id = f"{chunk_id}__{cat}__{idx}"
                src = item.get("source", {})
                excerpt_lookup[fact_id] = {
                    "excerpt": src.get("excerpt", ""),
                    "doc_id":  src.get("doc_id", ""),
                }
    return memo_text, register, classified_facts, excerpt_lookup


# ── Shared renderers ───────────────────────────────────────────────────────────

def _bold_refs(text: str) -> str:
    return re.sub(r'\[E-(\d+)\]', r'**[E-\1]**', text)


def render_evidence_card(e_id: str, entry: dict, excerpt_lookup: dict) -> None:
    """Render one evidence register entry with its verified source excerpt."""
    fact_id = entry.get("fact_id", "")
    src     = excerpt_lookup.get(fact_id, {})
    excerpt = src.get("excerpt", "")
    doc_id  = src.get("doc_id", "")

    st.markdown(f"#### {e_id}")

    label = entry.get("label", "—")
    if entry.get("value") not in (None, ""):
        label += f" = **{entry['value']} {entry.get('unit', '')}**"
    if entry.get("period"):
        label += f" ({entry['period']})"
    st.markdown(f"**Claim:** {label}")

    section  = SECTION_LABELS.get(entry.get("memo_section", ""), entry.get("memo_section", "—"))
    category = CATEGORY_LABELS.get(entry.get("category", ""), entry.get("category", "—"))
    status   = entry.get("citation_status", "—")
    rel      = entry.get("relevance", "—")
    page     = entry.get("source_page", "—")

    doc_label = f"`{doc_id}.pdf` · " if doc_id else ""
    st.markdown(
        f"📄 {doc_label}page **{page}** &nbsp;|&nbsp; "
        f"Section: *{section}* &nbsp;|&nbsp; "
        f"Category: *{category}* &nbsp;|&nbsp; "
        f"Relevance: **{rel}**/5 &nbsp;|&nbsp; "
        f"Status: `{status}`",
        unsafe_allow_html=True,
    )

    if excerpt:
        st.markdown("**Verified source excerpt** *(exact quote found in the PDF):*")
        st.info(f"> {excerpt}")
    else:
        st.caption(
            "No verbatim excerpt — this fact comes from an infographic or KPI "
            "summary box where pdfplumber cannot extract contiguous text."
        )


def tab_memo(memo_text: str, register: dict, excerpt_lookup: dict,
             company_label: str = "", download: bool = False) -> None:
    """Render the Memo & Evidence tab."""
    col_memo, col_panel = st.columns([3, 2], gap="large")

    with col_panel:
        st.subheader("Evidence Panel")
        st.caption(
            "Each **[E-NNN]** in the memo cites a fact from this register. "
            "Select a reference to see the verified source excerpt."
        )
        e_ids = list(register.keys())
        selected = st.selectbox(
            "Select a reference",
            options=e_ids,
            format_func=lambda x: f"{x} — {register[x].get('label', '')[:55]}",
            key=f"ev_select_{company_label}",
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

    with col_memo:
        st.subheader("Investment Memo")
        if download:
            st.download_button(
                "⬇ Download memo (.md)",
                data=memo_text,
                file_name="investment_memo.md",
                mime="text/markdown",
            )
        st.caption(
            "**[E-NNN]** references mark claims with verified source evidence. "
            "Select any reference in the panel → to inspect the underlying quote."
        )
        st.divider()
        display = re.sub(r'^#\s+Investment Memo[^\n]*\n', '', memo_text, count=1)
        display = re.sub(
            r'\*\*Prepared by:\*\*.*?---\n+', '', display, flags=re.DOTALL, count=1
        )
        st.markdown(_bold_refs(display))


def tab_facts(classified_facts: list, excerpt_lookup: dict,
              company_label: str = "") -> None:
    """Render the Facts Browser tab."""
    st.subheader("Facts Browser")
    st.caption(
        "All facts extracted from the annual report. "
        "**Relevance** is the AI's 1–5 rating (5 = headline, 1 = excluded). "
        "**Citation status** shows whether the verbatim excerpt was found in the source PDF."
    )

    all_sections = sorted({f.get("memo_section", "") for f in classified_facts if f.get("memo_section")})
    all_statuses = sorted({f.get("citation_status", "") for f in classified_facts if f.get("citation_status")})

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        section_filter = st.multiselect(
            "Memo section", options=all_sections, default=all_sections,
            format_func=lambda s: SECTION_LABELS.get(s, s),
            key=f"sec_{company_label}",
        )
    with fc2:
        relevance_filter = st.multiselect(
            "Relevance", options=[5, 4, 3, 2, 1], default=[5, 4, 3],
            format_func=lambda r: RELEVANCE_LABELS.get(r, str(r)),
            key=f"rel_{company_label}",
        )
    with fc3:
        status_filter = st.multiselect(
            "Citation status", options=all_statuses, default=all_statuses,
            key=f"stat_{company_label}",
        )

    filtered = [
        f for f in classified_facts
        if f.get("memo_section") in section_filter
        and f.get("relevance") in relevance_filter
        and f.get("citation_status") in status_filter
    ]

    st.caption(f"Showing **{len(filtered)}** of {len(classified_facts)} facts")
    st.divider()

    for fact in filtered:
        label    = fact.get("label", "—")
        category = CATEGORY_LABELS.get(fact.get("category", ""), fact.get("category", ""))
        relevance = fact.get("relevance", "—")
        page      = fact.get("source_page", "—")
        status    = fact.get("citation_status", "—")

        value_str = ""
        if fact.get("value") not in (None, ""):
            value_str = f" = {fact['value']} {fact.get('unit', '')} ({fact.get('period', '')})"

        chunk_prefix = (fact.get("id") or "").split("__")[0]
        title = f"[p{page}] {label[:80]}{value_str}"

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
            fact_id = fact.get("id", "")
            src_info = excerpt_lookup.get(fact_id, {})
            excerpt  = src_info.get("excerpt", "")
            if excerpt:
                st.markdown("**Source excerpt:**")
                st.info(f"> {excerpt}")


# ── "Run your own" pipeline ───────────────────────────────────────────────────

def _capture(fn, *args, **kwargs):
    """Call fn(*args, **kwargs), capturing stdout. Returns (result, output_str)."""
    buf = io.StringIO()
    result = None
    try:
        with contextlib.redirect_stdout(buf):
            result = fn(*args, **kwargs)
    except SystemExit as e:
        pass  # cost guard or explicit exit — output will show what happened
    return result, buf.getvalue()


def _write_generic_config(path: str, company_name: str, ticker: str, doc_id: str) -> None:
    """Write a generic config.yaml for an unknown UK annual report."""
    cfg = {
        "company_id": doc_id,
        "company_name": company_name,
        "ticker": ticker or doc_id.upper(),
        "fiscal_year_end": "",
        "fiscal_year": "",
        "report_year": "",
        "currency": "GBP",
        "currency_symbol": "£",
        "section_taxonomy": _GENERIC_TAXONOMY,
    }
    with open(path, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)


def run_own_pipeline(
    pdf_bytes: bytes,
    company_name: str,
    ticker: str,
    api_key: str,
    status_container,
) -> dict | None:
    """Run the full pipeline on uploaded PDF bytes.

    The API key is placed in os.environ for the duration of the run and
    removed in the finally block. It is never written to disk.

    Returns a dict with memo_text, register, classified_facts, validated_chunks,
    or None if a stage failed.
    """
    # Import pipeline modules here so any import-time side effects are
    # scoped to when the user actually triggers a run.
    import extract as ext_mod
    import validate as val_mod
    import finance as fin_mod
    import prior_year as py_mod
    import classify as cls_mod
    import memo as memo_mod

    os.environ["ANTHROPIC_API_KEY"] = api_key

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            # ── Write PDF and config ──────────────────────────────────────────
            pdf_path = os.path.join(tmpdir, "report.pdf")
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)

            doc_id = re.sub(r'[^a-z0-9]', '-', company_name.lower())[:20].strip('-')
            config_path = os.path.join(tmpdir, "config.yaml")
            _write_generic_config(config_path, company_name, ticker, doc_id)

            facts_path      = os.path.join(tmpdir, "facts.json")
            validated_path  = os.path.join(tmpdir, "validated_facts.json")
            financials_path = os.path.join(tmpdir, "financials.json")
            prior_year_path = os.path.join(tmpdir, "prior_year_facts.json")
            classified_path = os.path.join(tmpdir, "classified_facts.json")
            memo_out        = os.path.join(tmpdir, "memo.md")
            register_out    = os.path.join(tmpdir, "evidence_register.json")

            # ── Stage 1: Extract ──────────────────────────────────────────────
            status_container.write("**Stage 1/6 — Fact extraction** (Haiku, batched)")
            _, log1 = _capture(
                ext_mod.run_extraction, pdf_path, doc_id, config_path, facts_path
            )
            if not os.path.exists(facts_path):
                status_container.error("Extraction failed — see log for details.")
                with st.expander("Extraction log"):
                    st.code(log1)
                return None
            with open(facts_path) as f:
                raw_chunks = json.load(f)
            n_chunks = len(raw_chunks)
            status_container.write(f"   ✅ {n_chunks} batch(es) extracted")
            with st.expander("Extraction log"):
                st.code(log1)

            # ── Stage 2: Validate citations ───────────────────────────────────
            status_container.write("**Stage 2/6 — Citation validation** (deterministic)")
            _, log2 = _capture(
                _run_validate, val_mod, facts_path, pdf_path, validated_path
            )
            if not os.path.exists(validated_path):
                status_container.error("Validation failed.")
                with st.expander("Validation log"):
                    st.code(log2)
                return None
            with open(validated_path) as f:
                validated_chunks = json.load(f)
            n_facts = sum(
                len(c.get(k, [])) for c in validated_chunks for k in FACT_KEYS
            )
            verified = sum(
                1 for c in validated_chunks for k in FACT_KEYS
                for item in c.get(k, [])
                if item.get("citation_status") in ("verified", "corrected")
            )
            status_container.write(f"   ✅ {verified}/{n_facts} facts verified")
            with st.expander("Validation log"):
                st.code(log2)

            # ── Stage 3: Finance cross-checks ─────────────────────────────────
            status_container.write("**Stage 3/6 — Finance cross-checks** (deterministic)")
            facts_flat, chunks_raw = fin_mod.load_verified_facts(validated_path)
            fin_result = fin_mod.run_all(facts_flat, chunks_raw, company_id="upload")
            with open(financials_path, "w") as f:
                json.dump(fin_result, f, indent=2)
            meta = fin_result["metadata"]
            status_container.write(
                f"   ✅ {meta['passed']} PASS / {meta['warned']} WARN / {meta['failed']} FAIL"
            )

            # ── Stage 4: Prior-year facts ─────────────────────────────────────
            status_container.write("**Stage 4/6 — Prior-year extraction** (deterministic)")
            prior_facts = py_mod.extract_prior_year_facts(validated_chunks)
            with open(prior_year_path, "w") as f:
                json.dump(prior_facts, f, indent=2)
            status_container.write(f"   ✅ {len(prior_facts)} prior-year value(s) found")

            # ── Stage 5: Classify and synthesise ─────────────────────────────
            status_container.write("**Stage 5/6 — Classification and synthesis** (Sonnet — this takes a few minutes)")
            _, log5 = _capture(
                cls_mod.classify_and_synthesise,
                validated_path, financials_path, classified_path
            )
            if not os.path.exists(classified_path):
                status_container.error("Classification failed.")
                with st.expander("Classification log"):
                    st.code(log5)
                return None
            with open(classified_path) as f:
                cf = json.load(f)
            n_classified = len(cf.get("classified_facts", []))
            status_container.write(f"   ✅ {n_classified} facts classified and synthesised")
            with st.expander("Classification log"):
                st.code(log5)

            # ── Stage 6: Memo generation ──────────────────────────────────────
            status_container.write("**Stage 6/6 — Memo generation** (Sonnet)")
            _, log6 = _capture(
                memo_mod.run_memo_pipeline,
                classified_path, financials_path, validated_path, prior_year_path,
                memo_out, register_out, config_path=config_path,
            )
            if not os.path.exists(memo_out):
                status_container.error("Memo generation failed.")
                with st.expander("Memo log"):
                    st.code(log6)
                return None
            with st.expander("Memo generation log"):
                st.code(log6)

            # ── Load results into memory before tmpdir is deleted ─────────────
            memo_text = Path(memo_out).read_text()
            with open(register_out) as f:
                register = json.load(f)
            classified_facts = cf.get("classified_facts", [])

            return {
                "memo_text":         memo_text,
                "register":          register,
                "classified_facts":  classified_facts,
                "validated_chunks":  validated_chunks,
            }

    except Exception as e:
        status_container.error(f"Unexpected error: {e}")
        return None
    finally:
        # Always clear the API key from environment — even if an error occurred.
        os.environ.pop("ANTHROPIC_API_KEY", None)


def _run_validate(val_mod, facts_path: str, pdf_path: str, validated_path: str) -> None:
    """Thin wrapper so _capture() can call validate_facts() and write the result."""
    validated = val_mod.validate_facts(facts_path, pdf_path)
    with open(validated_path, "w") as f:
        json.dump(validated, f, indent=2)


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="AI Investment Memo Assistant",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ── Sidebar — mode selector ────────────────────────────────────────────────
    with st.sidebar:
        st.title("📄 Memo Assistant")
        st.caption(
            "AI-assisted investment memos where every claim is traceable "
            "to a verified source excerpt."
        )
        st.divider()

        mode = st.radio(
            "Mode",
            ["🏛 Demo — explore finished memos", "🔬 Run your own company"],
            index=0,
        )
        st.divider()
        st.caption(
            "**Design principle:** AI reads and writes prose. "
            "Code counts and checks. Every [E-NNN] reference resolves to a "
            "verbatim quote verified against the source PDF."
        )
        st.caption(
            "Built as a portfolio project — see [GitHub]"
            "(https://github.com/zwhatmough/memo-assistant)."
        )

    # ── Demo mode ──────────────────────────────────────────────────────────────
    if "Demo" in mode:
        st.title("AI Investment Memo Assistant — Demo")
        st.caption(
            "Select a company to explore the pipeline output. "
            "No API key needed — all data is pre-loaded."
        )

        company_key = st.selectbox(
            "Company",
            options=list(DEMO_COMPANIES.keys()),
        )
        st.info(DEMO_COMPANIES[company_key]["blurb"])

        try:
            memo_text, register, classified_facts, excerpt_lookup = load_demo_data(company_key)
        except FileNotFoundError as e:
            st.error(
                f"**Data file missing:** `{e}`\n\n"
                "Run `python extract.py … && python validate.py … && "
                "python classify.py … && python memo.py …` first, "
                "or clone the repo which includes pre-committed outputs."
            )
            st.stop()

        tab1, tab2 = st.tabs(["📄 Memo & Evidence", "🔍 Facts Browser"])
        with tab1:
            tab_memo(memo_text, register, excerpt_lookup, company_label=company_key)
        with tab2:
            tab_facts(classified_facts, excerpt_lookup, company_label=company_key)

    # ── Run your own mode ──────────────────────────────────────────────────────
    else:
        st.title("Run your own company")
        st.caption(
            "Upload a UK-listed company annual report PDF. "
            "The pipeline runs on your API credits (~$1, 5–10 minutes)."
        )

        # ── Inputs ────────────────────────────────────────────────────────────
        with st.expander("ℹ️ What this mode does", expanded=False):
            st.markdown(
                "1. **Pre-flight check** — validates the PDF before any API spend: "
                "text extractable, page count sensible, annual-report headings present, "
                "not a bank or insurer.\n"
                "2. **Fact extraction** — Claude Haiku reads the memo-relevant sections "
                "and extracts structured facts (~$0.10–0.20).\n"
                "3. **Citation validation** — every excerpt is string-matched against "
                "the source PDF. No API calls.\n"
                "4. **Finance cross-checks** — arithmetic verified deterministically. "
                "No API calls.\n"
                "5. **Classification and synthesis** — Claude Sonnet classifies facts "
                "and synthesises analytical observations (~$0.50–0.70).\n"
                "6. **Memo generation** — Claude Sonnet writes the ten-section memo "
                "with post-generation validation (~$0.13–0.20).\n\n"
                "**API key:** held in session memory only. Never written to disk. "
                "Never logged. Removed from memory immediately when the pipeline finishes."
            )

        col1, col2 = st.columns(2)
        with col1:
            uploaded = st.file_uploader("Annual report PDF", type=["pdf"])
        with col2:
            company_name = st.text_input("Company name", placeholder="e.g. Rolls-Royce Holdings plc")
            ticker = st.text_input("Ticker (optional)", placeholder="e.g. RR.")

        api_key = st.text_input(
            "Anthropic API key",
            type="password",
            placeholder="sk-ant-…",
            help=(
                "Your key is stored in session memory only and is never written to disk, "
                "logged, or sent anywhere other than the Anthropic API. "
                "It is deleted from memory as soon as the pipeline completes."
            ),
        )
        st.caption(
            "🔒 **API key privacy:** held in session state only. Never written to disk, "
            "never logged, removed after the run. A run costs roughly **$1** of your credits."
        )

        # ── Pre-flight check ──────────────────────────────────────────────────
        preflight_ok = False
        if uploaded is not None:
            st.divider()
            st.subheader("Pre-flight check")
            pdf_bytes = uploaded.getvalue()
            checks = run_preflight(pdf_bytes)

            all_passed = all(c["passed"] for c in checks)
            for check in checks:
                icon = "✅" if check["passed"] else "❌"
                st.markdown(f"{icon} **{check['label']}** — {check['detail']}")

            if all_passed:
                st.success("All checks passed. Ready to run.")
                preflight_ok = True
            else:
                failed = [c["label"] for c in checks if not c["passed"]]
                st.error(
                    f"Pre-flight failed: {', '.join(failed)}. "
                    "Please resolve the issues above before running."
                )

        # ── Run button ────────────────────────────────────────────────────────
        st.divider()
        run_disabled = not (preflight_ok and company_name.strip() and api_key.strip())
        run_clicked = st.button(
            "▶ Run pipeline",
            disabled=run_disabled,
            help="Upload a PDF, enter the company name, and paste your API key first.",
        )

        # Display previous results if they exist in session state
        if "own_results" in st.session_state and not run_clicked:
            results = st.session_state["own_results"]
            memo_text, register, classified_facts, excerpt_lookup = _load_from_dicts(
                results["memo_text"], results["register"],
                results["classified_facts"], results["validated_chunks"],
            )
            st.success("Pipeline complete — results below.")
            tab1, tab2 = st.tabs(["📄 Memo & Evidence", "🔍 Facts Browser"])
            with tab1:
                tab_memo(memo_text, register, excerpt_lookup,
                         company_label="own", download=True)
            with tab2:
                tab_facts(classified_facts, excerpt_lookup, company_label="own")

        elif run_clicked:
            # Clear any previous results
            st.session_state.pop("own_results", None)

            with st.status("Running pipeline…", expanded=True) as pipeline_status:
                results = run_own_pipeline(
                    pdf_bytes=uploaded.getvalue(),
                    company_name=company_name.strip(),
                    ticker=ticker.strip(),
                    api_key=api_key.strip(),
                    status_container=pipeline_status,
                )
                if results:
                    pipeline_status.update(
                        label="Pipeline complete ✅", state="complete", expanded=False
                    )
                    st.session_state["own_results"] = results
                else:
                    pipeline_status.update(
                        label="Pipeline failed ❌", state="error", expanded=True
                    )

            if results:
                memo_text, register, classified_facts, excerpt_lookup = _load_from_dicts(
                    results["memo_text"], results["register"],
                    results["classified_facts"], results["validated_chunks"],
                )
                tab1, tab2 = st.tabs(["📄 Memo & Evidence", "🔍 Facts Browser"])
                with tab1:
                    tab_memo(memo_text, register, excerpt_lookup,
                             company_label="own", download=True)
                with tab2:
                    tab_facts(classified_facts, excerpt_lookup, company_label="own")


if __name__ == "__main__":
    main()
