"""Tests for finance.py — deterministic cross-checks and derived metrics.

Every function in finance.py is a pure function (no API calls, no file I/O).
These tests exercise correct arithmetic, edge cases (zero denominators,
missing facts, sign conventions), and the fact-lookup helper.
"""

import pytest
from finance import (
    find_fact,
    check_revenue_entity_split,
    check_consumer_services_split,
    check_operating_profit_bridge,
    check_pbt_bridge,
    check_profit_after_tax,
    check_effective_tax_rate,
    check_basic_eps,
    check_group_op_margin,
    check_at_op_margin,
    check_net_bank_debt,
    check_shareholder_returns,
    calc_cash_conversion,
    calc_free_cash_flow,
    calc_autorama_revenue_contribution,
    calc_autorama_margin_drag,
    calc_arpr_implied_retailer_revenue,
    MONETARY_TOL,
    PCT_TOL,
    EPS_TOL,
)


# ── Fixture helpers ─────────────────────────────────────────────────────────────

def _fact(label, value, period="FY2026", unit="£m", status="verified"):
    """Build a minimal financial figure dict as produced by the extraction pipeline."""
    return {
        "label": label,
        "value": value,
        "unit": unit,
        "period": period,
        "citation_status": status,
    }


# Realistic Auto Trader FY2026 figures, matching the actual validated_facts.json.
AT_FACTS = [
    _fact("Group Revenue", 624.3),
    _fact("Autotrader Revenue", 585.3),
    _fact("Autorama Revenue", 39.0),
    _fact("Trade Revenue", 531.3),
    _fact("Consumer Services Revenue", 38.8),
    _fact("Private Revenue (Consumer Services)", 23.6),
    _fact("Motoring Services Revenue", 15.2),
    _fact("Group Operating Profit", 392.7),
    _fact("Autotrader Operating Profit", 408.0),
    _fact("Core Autotrader operating profit", 408.0),  # duplicate label, same value
    _fact("Group Central Costs", 13.3),
    _fact("Autorama Operating Loss", -2.0),
    _fact("Group Operating Profit Margin", 63.0, unit="%"),
    _fact("Autotrader Operating Profit Margin", 70.0, unit="%"),
    _fact("Group Net Finance Costs", 3.9),
    _fact("Group Profit Before Tax", 388.8),
    _fact("Group Tax Charge", 94.9),
    _fact("Effective Tax Rate", 24.0, unit="%"),
    _fact("Profit for the year", 293.9),
    _fact("Basic earnings per share", 34.17, unit="pence"),
    _fact("Diluted Earnings Per Share", 34.07, unit="pence"),
    _fact("Weighted Average Ordinary Shares Outstanding (Basic)", 860.2, unit="million"),
    _fact("Syndicated RCF Drawn", 165.0, period="31 March 2026"),
    _fact("Cash and cash equivalents", 18.2),
    _fact("Net Bank Debt", 146.8),
    _fact("Dividends Paid", 94.1),
    _fact("Dividends paid to Company shareholders", -94.1),   # cash flow version (outflow)
    _fact("Share Buyback Consideration", 369.1),
    _fact("Total Cash Returned to Shareholders", 463.2),
    _fact("Cash Generated from Operations", 418.0),
    _fact("Net cash generated from operating activities", 322.8),
    _fact("Purchases of property, plant and equipment", -27.3),
    _fact("Average Revenue Per Retailer (ARPR)", 2995.0, unit="GBP", period="FY2026"),
    _fact("Average retailer forecourts", 13942.0, unit="count", period="FY2026"),
    _fact("Retailer Segment Revenue", 501.1),
]


# ── find_fact tests ─────────────────────────────────────────────────────────────

class TestFindFact:
    def test_basic_match(self):
        assert find_fact(AT_FACTS, "group revenue", "2026") == 624.3

    def test_case_insensitive(self):
        assert find_fact(AT_FACTS, "GROUP REVENUE", "FY2026") == 624.3

    def test_unit_filter(self):
        # "Group Operating Profit Margin" has unit %, not £m
        assert find_fact(AT_FACTS, "group operating profit margin", "2026", unit_contains="%") == 63.0
        assert find_fact(AT_FACTS, "group operating profit margin", "2026", unit_contains="£m") is None

    def test_not_found_returns_none(self):
        assert find_fact(AT_FACTS, "revenue growth rate", "2026") is None

    def test_label_not_contains_excludes(self):
        # Without exclusion, "dividends paid" matches both 94.1 and -94.1 → ValueError
        with pytest.raises(ValueError, match="Conflicting values"):
            find_fact(AT_FACTS, "dividends paid", "2026", unit_contains="£m")

        # With exclusion of the cash flow version, only 94.1 remains
        result = find_fact(AT_FACTS, "dividends paid", "2026", unit_contains="£m",
                           label_not_contains="to company")
        assert result == 94.1

    def test_duplicate_same_value_ok(self):
        # "Autotrader Operating Profit" and "Core Autotrader operating profit" both = 408.0.
        # Must filter by unit "£m" to exclude "Autotrader Operating Profit Margin" (70.0%).
        result = find_fact(AT_FACTS, "autotrader operating profit", "2026", unit_contains="£m")
        assert result == 408.0

    def test_duplicate_conflicting_raises(self):
        conflicting = AT_FACTS + [_fact("Group Revenue", 625.0)]
        with pytest.raises(ValueError, match="Conflicting values"):
            find_fact(conflicting, "group revenue", "2026")

    def test_period_filter(self):
        # Only FY2026 facts in AT_FACTS; searching for 2025 returns None
        assert find_fact(AT_FACTS, "group revenue", "2025") is None

    def test_unverifiable_facts_excluded(self):
        # load_verified_facts filters these out, but find_fact itself doesn't —
        # tests call find_fact directly on already-filtered lists. This test
        # confirms that if an unverifiable fact sneaks through, it IS included.
        # (The filtering responsibility lies with load_verified_facts.)
        unverifiable = [_fact("Group Revenue", 624.3, status="unverifiable")]
        assert find_fact(unverifiable, "group revenue", "2026") == 624.3


# ── Cross-check tests ───────────────────────────────────────────────────────────

class TestCrossChecks:

    def test_revenue_entity_split_passes(self):
        result = check_revenue_entity_split(AT_FACTS)
        assert result.status == "pass"
        assert abs(result.calculated - 624.3) < 0.01

    def test_revenue_entity_split_fails_on_wrong_data(self):
        wrong = [f for f in AT_FACTS if f["label"] != "Autorama Revenue"]
        wrong.append(_fact("Autorama Revenue", 50.0))  # wrong value
        result = check_revenue_entity_split(wrong)
        assert result.status == "fail"

    def test_consumer_services_split_passes(self):
        result = check_consumer_services_split(AT_FACTS)
        assert result.status == "pass"
        # 23.6 + 15.2 = 38.8
        assert abs(result.calculated - 38.8) < 0.01

    def test_operating_profit_bridge_passes(self):
        result = check_operating_profit_bridge(AT_FACTS)
        assert result.status == "pass"
        # 408.0 - 13.3 + (-2.0) = 392.7
        assert abs(result.calculated - 392.7) < 0.01

    def test_operating_profit_bridge_sign_convention(self):
        # Autorama loss is -2.0; adding it should reduce the total.
        # Use unit_contains="£m" to exclude the operating profit margin (70.0%).
        result = check_operating_profit_bridge(AT_FACTS)
        at_op = find_fact(AT_FACTS, "autotrader operating profit", "2026", unit_contains="£m")
        central = find_fact(AT_FACTS, "central costs", "2026")
        # calculated = 408 - 13.3 + (-2) = 392.7, NOT 408 - 13.3 - (-2) = 396.7
        assert result.calculated < at_op - central

    def test_pbt_bridge_passes(self):
        result = check_pbt_bridge(AT_FACTS)
        assert result.status == "pass"
        assert abs(result.calculated - 388.8) < 0.01  # 392.7 - 3.9

    def test_profit_after_tax_passes(self):
        result = check_profit_after_tax(AT_FACTS)
        assert result.status == "pass"
        assert abs(result.calculated - 293.9) < 0.01  # 388.8 - 94.9

    def test_effective_tax_rate_passes(self):
        result = check_effective_tax_rate(AT_FACTS)
        assert result.status == "pass"
        # 94.9 / 388.8 * 100 = 24.41%; stated 24%; within 0.5pp
        assert 23.5 < result.calculated < 25.5

    def test_effective_tax_rate_zero_denominator(self):
        # Remove both the PBT input and the stated tax rate so the check can only warn.
        # (If the stated rate is present but calculated is 0, the check correctly fails.)
        no_pbt_no_rate = [
            f for f in AT_FACTS
            if "profit before tax" not in f["label"].lower()
            and "effective tax rate" not in f["label"].lower()
        ]
        result = check_effective_tax_rate(no_pbt_no_rate)
        assert result.calculated == 0.0
        assert result.status == "warn"

    def test_basic_eps_passes(self):
        result = check_basic_eps(AT_FACTS)
        assert result.status == "pass"
        # 293.9 / 860.2 * 100 = 34.17p
        assert abs(result.calculated - 34.17) < EPS_TOL

    def test_basic_eps_excludes_diluted(self):
        # Diluted EPS (34.07p) should not be found by basic EPS lookup
        result = check_basic_eps(AT_FACTS)
        # The stated value should be 34.17, not 34.07
        assert result.stated == pytest.approx(34.17, abs=EPS_TOL)

    def test_group_op_margin_passes(self):
        result = check_group_op_margin(AT_FACTS)
        assert result.status == "pass"
        # 392.7 / 624.3 * 100 = 62.9%; stated 63%; within 0.5pp
        assert abs(result.calculated - 63.0) < PCT_TOL

    def test_at_op_margin_passes(self):
        result = check_at_op_margin(AT_FACTS)
        assert result.status == "pass"
        # 408.0 / 585.3 * 100 = 69.7%; stated 70%; within 0.5pp
        assert abs(result.calculated - 70.0) < PCT_TOL

    def test_net_bank_debt_passes(self):
        result = check_net_bank_debt(AT_FACTS)
        assert result.status == "pass"
        # 165.0 - 18.2 = 146.8; stated 146.8
        assert abs(result.calculated - 146.8) < MONETARY_TOL

    def test_shareholder_returns_passes(self):
        result = check_shareholder_returns(AT_FACTS)
        assert result.status == "pass"
        # 94.1 + 369.1 = 463.2
        assert abs(result.calculated - 463.2) < MONETARY_TOL

    def test_shareholder_returns_excludes_negative_dividends(self):
        # The cash flow statement has dividends paid as −94.1; the capital
        # allocation section has +94.1. The check must use the positive version.
        result = check_shareholder_returns(AT_FACTS)
        assert result.calculated > 0

    def test_warns_when_stated_value_missing(self):
        # Remove the stated group revenue to trigger a warn status
        no_stated = [f for f in AT_FACTS
                     if not (f["label"] == "Group Revenue" and f["value"] == 624.3)]
        result = check_revenue_entity_split(no_stated)
        assert result.status == "warn"


# ── Derived metric tests ────────────────────────────────────────────────────────

class TestDerivedMetrics:

    def test_cash_conversion_above_100(self):
        result = calc_cash_conversion(AT_FACTS)
        # 418.0 / 392.7 * 100 = 106.4%
        assert result.result == pytest.approx(106.4, abs=0.2)
        assert result.unit == "%"

    def test_cash_conversion_zero_denominator(self):
        no_op = [f for f in AT_FACTS if "group operating profit" not in f["label"].lower()]
        result = calc_cash_conversion(no_op)
        assert result.result == 0.0

    def test_free_cash_flow(self):
        result = calc_free_cash_flow(AT_FACTS)
        # 322.8 + (−27.3) = 295.5
        assert result.result == pytest.approx(295.5, abs=0.2)

    def test_free_cash_flow_ppe_is_outflow(self):
        # PPE purchase is stated as negative (outflow in cash flow statement)
        # Adding it to net ops cash should reduce the result
        result = calc_free_cash_flow(AT_FACTS)
        net_ops = find_fact(AT_FACTS, "net cash generated from operating activities", "2026")
        assert result.result < net_ops

    def test_autorama_revenue_contribution(self):
        result = calc_autorama_revenue_contribution(AT_FACTS)
        # 39.0 / 624.3 * 100 = 6.2%
        assert result.result == pytest.approx(6.2, abs=0.1)

    def test_autorama_margin_drag(self):
        result = calc_autorama_margin_drag(AT_FACTS)
        # |-2.0| / 624.3 * 100 = 0.32pp
        assert result.result == pytest.approx(0.32, abs=0.01)
        assert result.unit == "pp"

    def test_autorama_margin_drag_uses_absolute_loss(self):
        # The drag must be positive even though loss is negative
        result = calc_autorama_margin_drag(AT_FACTS)
        assert result.result > 0

    def test_arpr_implied_retailer_revenue(self):
        result = calc_arpr_implied_retailer_revenue(AT_FACTS)
        # 2995 * 13942 * 12 / 1,000,000 = 501.2 £m
        assert result.result == pytest.approx(501.2, abs=1.0)

    def test_arpr_implied_vs_stated_retailer_revenue(self):
        # Implied (~501m) should be close to stated Retailer Segment Revenue (501.1m)
        result = calc_arpr_implied_retailer_revenue(AT_FACTS)
        stated = find_fact(AT_FACTS, "retailer segment revenue", "2026")
        assert abs(result.result - stated) < 2.0  # within £2m

    def test_arpr_implied_missing_inputs(self):
        no_arpr = [f for f in AT_FACTS if "average revenue per retailer" not in f["label"].lower()]
        result = calc_arpr_implied_retailer_revenue(no_arpr)
        assert result.result == 0.0
