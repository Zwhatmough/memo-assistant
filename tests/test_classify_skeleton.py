"""Tests for classify.py risk skeleton deduplication.

build_risk_skeleton() must not produce duplicate or overlapping sub-section
labels when the extraction model assigns a risk_type that is a subset of a
taxonomy-matched category label (e.g. "Financial" inside "Financial and market
risk"). These tests exercise the generic _dedupe_subset_labels helper.
"""

from classify import _dedupe_subset_labels, _sig_words, build_risk_skeleton


# ── _sig_words ───────────────────────────────────────────────────────────────

def test_sig_words_strips_stop_words():
    assert _sig_words("Financial and market risk") == {"financial", "market", "risk"}


def test_sig_words_single_word():
    assert _sig_words("Financial") == {"financial"}


# ── _dedupe_subset_labels ────────────────────────────────────────────────────

def _meta(fact_ids, is_taxonomy=False):
    return {"keyword": fact_ids[0], "fact_ids": list(fact_ids), "is_taxonomy": is_taxonomy}


def test_dedup_absorbs_subset_into_superset():
    """'Financial' words ⊂ 'Financial and market risk' words — merge into superset."""
    cats = {
        "Financial and market risk": _meta(["f1", "f2"], is_taxonomy=True),
        "Financial": _meta(["f3"]),
    }
    result = _dedupe_subset_labels(cats)
    assert "Financial and market risk" in result
    assert "Financial" not in result
    # fact_ids from the absorbed label are added to the superset
    assert "f3" in result["Financial and market risk"]["fact_ids"]
    assert "f1" in result["Financial and market risk"]["fact_ids"]


def test_dedup_absorbs_subset_into_superset_risk_suffix():
    """'Financial' words ⊂ 'Financial risk' words — 'Financial' is absorbed."""
    cats = {
        "Financial risk": _meta(["f1"]),
        "Financial": _meta(["f2"]),
    }
    # {"financial"} is a strict subset of {"financial", "risk"}
    result = _dedupe_subset_labels(cats)
    assert "Financial risk" in result
    assert "Financial" not in result
    assert "f2" in result["Financial risk"]["fact_ids"]


def test_dedup_no_merge_when_disjoint():
    """Completely different labels are not merged."""
    cats = {
        "Cyber security": _meta(["c1"]),
        "Brand and reputation": _meta(["b1"]),
    }
    result = _dedupe_subset_labels(cats)
    assert len(result) == 2


def test_dedup_no_spurious_removal_of_macro():
    """'Macroeconomic and geopolitical risk' should not absorb 'Operational'."""
    cats = {
        "Macroeconomic and geopolitical risk": _meta(["m1", "m2"], is_taxonomy=True),
        "Operational": _meta(["o1", "o2"], is_taxonomy=True),
    }
    result = _dedupe_subset_labels(cats)
    assert len(result) == 2


def test_dedup_deduplicates_fact_ids():
    """If the same fact_id appears in both the narrow and broad label, it appears once."""
    cats = {
        "Financial and market risk": _meta(["f1", "f2"], is_taxonomy=True),
        "Financial": _meta(["f1", "f3"]),  # f1 already in superset
    }
    result = _dedupe_subset_labels(cats)
    ids = result["Financial and market risk"]["fact_ids"]
    assert ids.count("f1") == 1
    assert "f3" in ids


def test_dedup_preserves_keyword_of_target():
    """Absorbed label's keyword does not overwrite the target's keyword."""
    cats = {
        "Financial and market risk": {"keyword": "financial", "fact_ids": ["f1"],
                                       "is_taxonomy": True},
        "Financial": {"keyword": "fin", "fact_ids": ["f2"], "is_taxonomy": False},
    }
    result = _dedupe_subset_labels(cats)
    assert result["Financial and market risk"]["keyword"] == "financial"


# ── build_risk_skeleton end-to-end dedup ────────────────────────────────────

def _risk_fact(fact_id, label, risk_type):
    """Minimal classified fact for risk skeleton construction."""
    return {
        "id": fact_id,
        "category": "risk_disclosures",
        "label": label,
        "risk_type": risk_type,
        "citation_status": "verified",
        "relevance": 3,
        "memo_section": "risks",
    }


def test_build_risk_skeleton_no_financial_overlap():
    """build_risk_skeleton must not emit both 'Financial' and 'Financial and market risk'.

    Regression test for Greggs generalisation finding: the extraction model can
    assign risk_type='Financial' to some facts while other facts in the same
    batch match the taxonomy term 'debt covenant' → label 'Financial and market
    risk'. Without dedup, both appear as skeleton categories.
    """
    facts = [
        # Taxonomy match: 'debt covenant' maps to financial_market_risk
        _risk_fact("f1", "Stress testing showed potential covenant breach", "Financial risk"),
        _risk_fact("f2", "Liquidity access may be impaired", "Financial risk"),
        # Fallback: risk_type 'Financial' → normalises to label 'Financial'
        _risk_fact("f3", "Cost inflation squeezed margins", "Financial"),
        _risk_fact("f4", "NIC increases compressed profitability", "Financial"),
        # Unrelated taxonomy category
        _risk_fact("c1", "Cyber threats are intensifying", "IT systems and cyber security"),
        _risk_fact("c2", "Data breach risk", "Cyber security"),
    ]
    skeleton = build_risk_skeleton(facts)
    labels = [s["label"] for s in skeleton]

    # There must be exactly one financial-related sub-section
    financial_labels = [l for l in labels if "financial" in l.lower()]
    assert len(financial_labels) == 1, (
        f"Expected 1 financial-related skeleton label, got {financial_labels}"
    )
