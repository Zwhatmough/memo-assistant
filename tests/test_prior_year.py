"""Tests for prior_year.py — prior-year value extraction from excerpts."""

import pytest
from prior_year import extract_prior_year_facts, _parse_value, _select_match, _apply_sign


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _chunk(facts_list, chunk_id="test_chunk"):
    """Build a minimal validated_facts chunk."""
    return {
        "chunk_id": chunk_id,
        "financial_figures": facts_list,
        "business_facts": [],
        "risk_disclosures": [],
        "strategic_items": [],
        "management_commentary": [],
    }


def _fig(label, value, unit, period, excerpt, status="verified"):
    """Build a minimal financial figure dict."""
    return {
        "label": label,
        "value": value,
        "unit": unit,
        "period": period,
        "citation_status": status,
        "source": {"excerpt": excerpt},
    }


# ── Unit tests for helper functions ─────────────────────────────────────────────

class TestParseValue:
    def test_simple_decimal(self):
        assert _parse_value("601.1") == 601.1

    def test_integer(self):
        assert _parse_value("70") == 70.0

    def test_with_commas(self):
        assert _parse_value("14,013") == 14013.0

    def test_large_with_commas(self):
        assert _parse_value("449,000") == 449000.0

    def test_currency_amount(self):
        assert _parse_value("2,854") == 2854.0


class TestApplySign:
    def test_positive_parent_positive_child(self):
        assert _apply_sign(601.1, 624.3) == 601.1

    def test_negative_parent_positive_child_negated(self):
        # Loss fact: parent is -2.0, prior-year excerpt gives 4.3 → should be -4.3
        assert _apply_sign(4.3, -2.0) == -4.3

    def test_negative_parent_negative_child_unchanged(self):
        # If the pattern somehow already has a negative, don't double-negate
        assert _apply_sign(-4.3, -2.0) == -4.3

    def test_zero_parent(self):
        # Zero parent: no sign change
        assert _apply_sign(5.0, 0.0) == 5.0


class TestSelectMatch:
    def test_picks_currency_for_monetary_unit(self):
        matches = [("2025", "£", "93.1", "m"), ("2025", "", "25", "%")]
        year, prefix, digits, suffix = _select_match(matches, "£m")
        assert digits == "93.1"

    def test_picks_pct_for_percent_unit(self):
        matches = [("2025", "£", "93.1", "m"), ("2025", "", "25", "%")]
        year, prefix, digits, suffix = _select_match(matches, "%")
        assert digits == "25"

    def test_fallback_to_first(self):
        # Single match returns regardless of unit
        matches = [("2025", "£", "600.0", "m")]
        result = _select_match(matches, "£m")
        assert result[2] == "600.0"

    def test_count_unit_picks_bare_number(self):
        matches = [("2025", "", "14,013", "")]
        result = _select_match(matches, "count")
        assert result[2] == "14,013"


# ── Integration tests for extract_prior_year_facts ─────────────────────────────

class TestExtractPriorYearFacts:
    def test_basic_extraction(self):
        fig = _fig("Group Revenue", 624.3, "£m", "FY2026",
                   "Group revenue increased 4% to £624.3m (2025: £601.1m)")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert len(prior) == 1
        assert prior[0]["label"] == "Group Revenue"
        assert prior[0]["value"] == 601.1
        assert prior[0]["unit"] == "£m"
        assert prior[0]["period"] == "FY2025"
        assert prior[0]["citation_status"] == "derived_from_excerpt"

    def test_sign_inherited_for_loss(self):
        fig = _fig("Autorama Operating Loss", -2.0, "£m", "FY2026",
                   "Autorama saw reduced operating losses of £2.0m (2025: £4.3m).")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert len(prior) == 1
        assert prior[0]["value"] == -4.3

    def test_percent_unit_selects_pct_match(self):
        fig = _fig("Effective Tax Rate", 24.0, "%", "FY2026",
                   "effective tax rate of 24% (2025: 25%)")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior[0]["value"] == 25.0
        assert prior[0]["unit"] == "%"

    def test_multiple_matches_selects_correct_one_for_currency(self):
        # Excerpt has both a £ value and a % value
        fig = _fig("Group Tax Charge", 94.9, "£m", "FY2026",
                   "The Group tax charge of £94.9m (2025: £93.1m) represents "
                   "an effective tax rate of 24% (2025: 25%)")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert len(prior) == 1
        assert prior[0]["value"] == 93.1  # not 25.0

    def test_multiple_matches_selects_pct_for_rate(self):
        fig = _fig("Effective Tax Rate", 24.0, "%", "FY2026",
                   "effective tax rate of 24% (2025: 25%)")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior[0]["value"] == 25.0

    def test_count_unit_extracts_bare_number(self):
        fig = _fig("Average Retailer Forecourts", 13942.0, "count", "FY2026",
                   "forecourts in the period was down 0.5% to 13,942 (2025: 14,013)")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior[0]["value"] == 14013.0

    def test_gbp_unit_extracts_correctly(self):
        fig = _fig("Average Revenue Per Retailer (ARPR)", 2995.0, "GBP", "FY2026",
                   "ARPR increased 5% (or £141) to £2,995 (2025: £2,854).")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior[0]["value"] == 2854.0

    def test_no_match_returns_empty(self):
        fig = _fig("Group Revenue", 624.3, "£m", "FY2026",
                   "Revenue was £624.3m")  # no prior-year pattern
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior == []

    def test_no_excerpt_skipped(self):
        fig = {"label": "Group Revenue", "value": 624.3, "unit": "£m",
               "period": "FY2026", "citation_status": "verified", "source": {}}
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior == []

    def test_unverifiable_skipped(self):
        fig = _fig("Group Revenue", 624.3, "£m", "FY2026",
                   "Revenue was £624.3m (2025: £601.1m)", status="unverifiable")
        prior = extract_prior_year_facts([_chunk([fig])])
        assert prior == []

    def test_deduplication_across_chunks(self):
        # Same label + period from two chunks should produce one prior-year fact
        fig1 = _fig("Group Revenue", 624.3, "£m", "FY2026",
                    "Revenue was £624.3m (2025: £601.1m)")
        fig2 = _fig("Group Revenue", 624.3, "£m", "FY2026",
                    "Group revenue also increased 4% to £624.3m (2025: £601.1m)")
        prior = extract_prior_year_facts([
            _chunk([fig1], "chunk_a"),
            _chunk([fig2], "chunk_b"),
        ])
        assert len(prior) == 1
        assert prior[0]["value"] == 601.1

    def test_two_different_facts_both_extracted(self):
        figs = [
            _fig("Group Revenue", 624.3, "£m", "FY2026",
                 "Revenue was £624.3m (2025: £601.1m)"),
            _fig("Group Operating Profit", 392.7, "£m", "FY2026",
                 "Operating profit was £392.7m (2025: £376.8m)"),
        ]
        prior = extract_prior_year_facts([_chunk(figs)])
        assert len(prior) == 2
        labels = {p["label"] for p in prior}
        assert "Group Revenue" in labels
        assert "Group Operating Profit" in labels

    def test_derived_from_audit_trail(self):
        fig = _fig("Group Revenue", 624.3, "£m", "FY2026",
                   "Revenue was £624.3m (2025: £601.1m)")
        prior = extract_prior_year_facts([_chunk([fig], "test_chunk_p1")])
        df = prior[0]["derived_from"]
        assert df["chunk_id"] == "test_chunk_p1"
        assert "(2025: £601.1m)" in df["matched_text"]
        assert "601.1m" in df["excerpt"]

    def test_all_five_key_metrics_extracted(self):
        """Regression test: the five growth metrics the user needs are all present."""
        with open("output/prior_year_facts.json") as f:
            import json
            prior = json.load(f)

        labels = {p["label"].lower() for p in prior}
        assert any("group revenue" in l for l in labels)
        assert any("autotrader revenue" in l for l in labels)
        assert any("group operating profit" in l for l in labels)
        assert any("arpr" in l or "average revenue per retailer" in l for l in labels)
        assert any("autorama revenue" in l for l in labels)
