"""Milestone 3: deterministic finance module.

Pure functions over validated_facts.json. The rule: code does all
arithmetic. The model never calculates. Every derived value is
accompanied by its inputs, formula, and a tolerance so the cross-check
is reproducible and auditable.

Usage:
    python finance.py                                       # default paths
    python finance.py --facts output/validated_facts.json
    python finance.py --out output/financials.json
"""

import argparse
import json
import os
from dataclasses import dataclass, asdict, field
from typing import Optional

from prior_year import extract_prior_year_facts

# ── Tolerances ─────────────────────────────────────────────────────────────────

# Rounding in published accounts typically introduces ±0.1–0.2 residuals.
MONETARY_TOL = 0.2      # £m
PCT_TOL = 0.5           # percentage points
EPS_TOL = 0.05          # pence


# ── Result types ───────────────────────────────────────────────────────────────

@dataclass
class CrossCheck:
    """The result of one arithmetic cross-check between stated figures."""
    name: str
    formula: str
    inputs: dict            # label → value used in the formula
    calculated: float       # what the arithmetic says
    stated: Optional[float] # what the document says (None if not found)
    tolerance: float
    unit: str
    status: str             # "pass" | "fail" | "warn"
    note: str = ""


@dataclass
class DerivedMetric:
    """A metric computed from raw facts that isn't itself stated in the document."""
    name: str
    formula: str
    inputs: dict
    result: float
    unit: str
    note: str = ""


@dataclass
class MissingData:
    """A calculation that could not be completed due to missing facts."""
    name: str
    reason: str
    facts_needed: list


# ── Fact loading ───────────────────────────────────────────────────────────────

def load_verified_facts(path: str) -> tuple[list[dict], list[dict]]:
    """Load validated_facts.json. Returns (verified_figures, raw_chunks).

    verified_figures: flattened list of financial_figure dicts with
        citation_status 'verified' or 'corrected'. Used for cross-checks
        and derived metrics.
    raw_chunks: the original chunk list, passed to extract_prior_year_facts()
        so the prior-year parser can scan all excerpt text.
    """
    with open(path) as f:
        chunks = json.load(f)

    facts = []
    for chunk in chunks:
        for fig in chunk.get("financial_figures", []):
            if fig.get("citation_status") in ("verified", "corrected"):
                facts.append(fig)
    return facts, chunks


def find_fact(
    facts: list[dict],
    label_contains: str,
    period_contains: str,
    unit_contains: Optional[str] = None,
    label_not_contains: Optional[str] = None,
) -> Optional[float]:
    """Return the value of a fact matched by fuzzy label/period/unit search.

    All comparisons are case-insensitive substring matches. When the same
    fact appears in multiple chunks (duplicates from overlapping extraction),
    all matched values must agree within MONETARY_TOL or a ValueError is
    raised — that divergence indicates a real inconsistency worth surfacing.

    Returns None if no match is found.
    """
    lc = label_contains.lower()
    pc = period_contains.lower()
    uc = unit_contains.lower() if unit_contains else None
    nc = label_not_contains.lower() if label_not_contains else None

    matches = []
    for fact in facts:
        label = fact.get("label", "").lower()
        period = fact.get("period", "").lower()
        unit = fact.get("unit", "").lower()

        if lc not in label:
            continue
        if pc not in period:
            continue
        if uc is not None and uc not in unit:
            continue
        if nc is not None and nc in label:
            continue

        matches.append(fact["value"])

    if not matches:
        return None

    if max(matches) - min(matches) > MONETARY_TOL:
        raise ValueError(
            f"Conflicting values for '{label_contains}' / '{period_contains}': {matches}. "
            f"Check for label ambiguity."
        )

    return matches[0]


# ── Cross-check helpers ────────────────────────────────────────────────────────

def _check(
    name: str,
    formula: str,
    inputs: dict,
    calculated: float,
    stated: Optional[float],
    tolerance: float,
    unit: str,
    note: str = "",
) -> CrossCheck:
    """Assemble a CrossCheck result, determining pass / fail / warn."""
    if stated is None:
        status = "warn"
        note = note or "Stated value not found in facts — check passed by arithmetic only."
    elif abs(calculated - stated) <= tolerance:
        status = "pass"
    else:
        status = "fail"
        residual = round(calculated - stated, 3)
        note = (note + f" Residual: {residual:+.3f} {unit}.").strip()

    return CrossCheck(
        name=name,
        formula=formula,
        inputs=inputs,
        calculated=round(calculated, 3),
        stated=round(stated, 3) if stated is not None else None,
        tolerance=tolerance,
        unit=unit,
        status=status,
        note=note,
    )


# ── Cross-checks ───────────────────────────────────────────────────────────────

def check_revenue_entity_split(facts: list[dict]) -> CrossCheck:
    """Autotrader Revenue + Autorama Revenue = Group Revenue.

    Tests the top-level entity split: the group is Core Autotrader
    (the digital marketplace) plus Autorama (the used-car retail arm).
    """
    at_rev = find_fact(facts, "autotrader revenue", "2026", "£m")
    auto_rev = find_fact(facts, "autorama revenue", "2026", "£m")
    group_rev = find_fact(facts, "group revenue", "2026", "£m")

    calculated = (at_rev or 0.0) + (auto_rev or 0.0)
    return _check(
        name="Revenue: Autotrader + Autorama = Group",
        formula="Autotrader Revenue + Autorama Revenue = Group Revenue",
        inputs={"autotrader_revenue_m": at_rev, "autorama_revenue_m": auto_rev},
        calculated=calculated,
        stated=group_rev,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_autotrader_revenue_by_channel(facts: list[dict]) -> CrossCheck:
    """Trade Revenue + Consumer Services Revenue = Autotrader Revenue (approx).

    Note: the reported Autotrader Revenue (£585.3m) is made up of Trade
    (£531.3m) and Consumer Services (£38.8m), with a residual of £15.2m
    that the document labels both 'Manufacturer & Agency' and 'Motoring
    Services' in different places. The check uses only the two clearly
    defined channels; the residual is flagged in the note.
    """
    trade = find_fact(facts, "trade revenue", "2026", "£m")
    consumer = find_fact(facts, "consumer services revenue", "2026", "£m")
    at_rev = find_fact(facts, "autotrader revenue", "2026", "£m")

    calculated = (trade or 0.0) + (consumer or 0.0)
    return _check(
        name="Autotrader Revenue: Trade + Consumer Services (partial)",
        formula="Trade Revenue + Consumer Services Revenue ≈ Autotrader Revenue",
        inputs={"trade_revenue_m": trade, "consumer_services_revenue_m": consumer},
        calculated=calculated,
        stated=at_rev,
        tolerance=16.0,  # wide tolerance: up to £16m residual expected (Manufacturer & Agency)
        unit="£m",
        note=(
            "Residual of ~£15.2m represents Manufacturer & Agency / Motoring Services revenue. "
            "These labels appear inconsistently across chapters; included in group totals."
        ),
    )


def check_consumer_services_split(facts: list[dict]) -> CrossCheck:
    """Private Revenue + Motoring Services = Consumer Services Revenue.

    Consumer Services is the revenue Auto Trader earns from private
    sellers and motoring-adjacent services (insurance, finance leads).
    """
    private = find_fact(facts, "private revenue", "2026", "£m")
    motoring = find_fact(facts, "motoring services", "2026", "£m")
    consumer = find_fact(facts, "consumer services revenue", "2026", "£m")

    calculated = (private or 0.0) + (motoring or 0.0)
    return _check(
        name="Consumer Services: Private + Motoring Services",
        formula="Private Revenue + Motoring Services Revenue = Consumer Services Revenue",
        inputs={"private_revenue_m": private, "motoring_services_m": motoring},
        calculated=calculated,
        stated=consumer,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_operating_profit_bridge(facts: list[dict]) -> CrossCheck:
    """Core Autotrader OP − Central Costs + Autorama Loss = Group OP.

    This is the segment profit reconciliation. Central costs (£13.3m)
    are unallocated and subtracted from Core AT's OP; Autorama's loss
    (stated as −£2.0m) is added (i.e. further reduces group OP).
    """
    at_op = find_fact(facts, "autotrader operating profit", "2026", "£m")
    central = find_fact(facts, "central costs", "2026", "£m")
    auto_loss = find_fact(facts, "autorama operating loss", "2026", "£m")
    group_op = find_fact(facts, "group operating profit", "2026", "£m")

    # Central costs: stated positive (13.3) → subtract as a cost.
    # Autorama loss: stated negative (−2.0) → adding a negative subtracts it.
    calculated = (at_op or 0.0) - (central or 0.0) + (auto_loss or 0.0)
    return _check(
        name="Operating Profit Bridge: AT − Central Costs + Autorama = Group",
        formula="Autotrader OP − Central Costs + Autorama Operating Loss = Group OP",
        inputs={
            "autotrader_op_m": at_op,
            "central_costs_m": central,
            "autorama_op_m": auto_loss,
        },
        calculated=calculated,
        stated=group_op,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_pbt_bridge(facts: list[dict]) -> CrossCheck:
    """Group Operating Profit − Net Finance Costs = Profit Before Tax."""
    op = find_fact(facts, "group operating profit", "2026", "£m")
    finance_costs = find_fact(facts, "net finance costs", "2026", "£m")
    pbt = find_fact(facts, "profit before tax", "2026", "£m")

    calculated = (op or 0.0) - (finance_costs or 0.0)
    return _check(
        name="PBT Bridge: Operating Profit − Net Finance Costs = PBT",
        formula="Group Operating Profit − Net Finance Costs = Profit Before Tax",
        inputs={"group_op_m": op, "net_finance_costs_m": finance_costs},
        calculated=calculated,
        stated=pbt,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_profit_after_tax(facts: list[dict]) -> CrossCheck:
    """Profit Before Tax − Tax Charge = Profit for the Year."""
    pbt = find_fact(facts, "profit before tax", "2026", "£m")
    tax = find_fact(facts, "tax charge", "2026", "£m")
    pat = find_fact(facts, "profit for the year", "2026", "£m")

    calculated = (pbt or 0.0) - (tax or 0.0)
    return _check(
        name="PAT: PBT − Tax Charge = Profit for Year",
        formula="Profit Before Tax − Tax Charge = Profit for the Year",
        inputs={"pbt_m": pbt, "tax_charge_m": tax},
        calculated=calculated,
        stated=pat,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_effective_tax_rate(facts: list[dict]) -> CrossCheck:
    """Tax Charge / PBT = Effective Tax Rate."""
    tax = find_fact(facts, "tax charge", "2026", "£m")
    pbt = find_fact(facts, "profit before tax", "2026", "£m")
    stated_rate = find_fact(facts, "effective tax rate", "2026")

    if pbt and pbt != 0:
        calculated = (tax / pbt) * 100
    else:
        calculated = 0.0

    return _check(
        name="Effective Tax Rate: Tax / PBT",
        formula="Tax Charge / Profit Before Tax × 100",
        inputs={"tax_charge_m": tax, "pbt_m": pbt},
        calculated=calculated,
        stated=stated_rate,
        tolerance=PCT_TOL,
        unit="%",
        note="Published rate is rounded to 24%; calculated rate may differ by up to 0.5pp.",
    )


def check_basic_eps(facts: list[dict]) -> CrossCheck:
    """Profit for Year / Weighted Average Shares = Basic EPS.

    Both inputs are in millions; the ratio × 100 converts to pence.
    Profit (£m) / Shares (m) × 100 = pence per share.
    """
    pat = find_fact(facts, "profit for the year", "2026", "£m")
    shares = find_fact(facts, "weighted average ordinary shares outstanding (basic)", "2026")
    stated_eps = find_fact(facts, "basic earnings per share", "2026",
                           label_not_contains="diluted")

    if pat and shares and shares != 0:
        calculated = (pat / shares) * 100
    else:
        calculated = 0.0

    return _check(
        name="Basic EPS: Profit / Weighted Avg Shares",
        formula="Profit for Year (£m) / Weighted Avg Shares (m) × 100 = EPS (pence)",
        inputs={"profit_for_year_m": pat, "weighted_avg_shares_m": shares},
        calculated=calculated,
        stated=stated_eps,
        tolerance=EPS_TOL,
        unit="pence",
    )


def check_group_op_margin(facts: list[dict]) -> CrossCheck:
    """Group Operating Profit / Group Revenue = Group Operating Profit Margin."""
    op = find_fact(facts, "group operating profit", "2026", "£m")
    rev = find_fact(facts, "group revenue", "2026", "£m")
    stated = find_fact(facts, "group operating profit margin", "2026")

    if op and rev and rev != 0:
        calculated = (op / rev) * 100
    else:
        calculated = 0.0

    return _check(
        name="Group Operating Profit Margin",
        formula="Group Operating Profit / Group Revenue × 100",
        inputs={"group_op_m": op, "group_revenue_m": rev},
        calculated=calculated,
        stated=stated,
        tolerance=PCT_TOL,
        unit="%",
    )


def check_at_op_margin(facts: list[dict]) -> CrossCheck:
    """Autotrader Operating Profit / Autotrader Revenue = AT Operating Margin."""
    at_op = find_fact(facts, "autotrader operating profit", "2026", "£m")
    at_rev = find_fact(facts, "autotrader revenue", "2026", "£m")
    stated = find_fact(facts, "autotrader operating profit margin", "2026")

    if at_op and at_rev and at_rev != 0:
        calculated = (at_op / at_rev) * 100
    else:
        calculated = 0.0

    return _check(
        name="Autotrader Core Operating Profit Margin",
        formula="Autotrader Operating Profit / Autotrader Revenue × 100",
        inputs={"at_op_m": at_op, "at_revenue_m": at_rev},
        calculated=calculated,
        stated=stated,
        tolerance=PCT_TOL,
        unit="%",
    )


def check_net_bank_debt(facts: list[dict]) -> CrossCheck:
    """RCF Drawn − Cash = Net Bank Debt.

    Uses the drawn facility amount (£165.0m), not the balance-sheet
    borrowings line (£163.4m, which nets capitalised issuance costs).
    """
    rcf = find_fact(facts, "rcf drawn", "2026", "£m")
    cash = find_fact(facts, "cash and cash equivalents", "2026", "£m",
                     label_not_contains="net cash generated")
    stated = find_fact(facts, "net bank debt", "2026")

    if rcf and cash:
        calculated = rcf - cash
    else:
        calculated = 0.0

    return _check(
        name="Net Bank Debt: RCF Drawn − Cash",
        formula="Syndicated RCF Drawn − Cash and Cash Equivalents = Net Bank Debt",
        inputs={"rcf_drawn_m": rcf, "cash_m": cash},
        calculated=calculated,
        stated=stated,
        tolerance=MONETARY_TOL,
        unit="£m",
        note="Balance-sheet 'Borrowings' (£163.4m) includes capitalised fees; "
             "net bank debt uses the gross drawn facility (£165.0m) less cash.",
    )


def check_shareholder_returns(facts: list[dict]) -> CrossCheck:
    """Dividends Paid + Share Buyback Consideration = Total Cash Returned."""
    # Exclude the cash flow version of dividends paid (which is negative)
    divs = find_fact(facts, "dividends paid", "2026", "£m",
                     label_not_contains="to company")
    buyback = find_fact(facts, "share buyback consideration", "2026", "£m")
    total = find_fact(facts, "total cash returned to shareholders", "2026", "£m")

    calculated = (divs or 0.0) + (buyback or 0.0)
    return _check(
        name="Shareholder Returns: Dividends + Buyback = Total Returned",
        formula="Dividends Paid + Share Buyback Consideration = Total Cash Returned",
        inputs={"dividends_paid_m": divs, "buyback_consideration_m": buyback},
        calculated=calculated,
        stated=total,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


# ── Derived metrics ────────────────────────────────────────────────────────────

def calc_cash_conversion(facts: list[dict]) -> DerivedMetric:
    """Cash Generated from Operations / Operating Profit.

    A ratio above 100% means the business is converting profit into cash
    more than 1:1 — typically because working capital is releasing cash
    or depreciation is a significant non-cash charge.
    """
    cash = find_fact(facts, "cash generated from operations", "2026", "£m")
    op = find_fact(facts, "group operating profit", "2026", "£m")

    result = (cash / op) * 100 if (cash and op and op != 0) else 0.0

    return DerivedMetric(
        name="Cash Conversion Rate",
        formula="Cash Generated from Operations / Group Operating Profit × 100",
        inputs={"cash_from_ops_m": cash, "group_op_m": op},
        result=round(result, 1),
        unit="%",
        note=(
            ">100% expected for asset-light digital platforms. "
            "AT's high margin leaves little room for working capital swings."
        ),
    )


def calc_free_cash_flow(facts: list[dict]) -> DerivedMetric:
    """Net Cash from Operations − Capex (PPE only) = Approximate Free Cash Flow.

    Capex here is purchases of property, plant and equipment only. Capitalised
    software and other intangibles are excluded because they are not separately
    available in the extracted facts. FCF is therefore an upper bound.
    """
    net_ops = find_fact(facts, "net cash generated from operating activities", "2026", "£m")
    ppe = find_fact(facts, "purchases of property, plant and equipment", "2026", "£m")

    if net_ops and ppe:
        # ppe is stated as negative in the cash flow (outflow); adding it subtracts
        result = net_ops + ppe
    else:
        result = 0.0

    return DerivedMetric(
        name="Approximate Free Cash Flow (PPE capex only)",
        formula="Net Cash from Operating Activities + PPE Purchases (negative outflow)",
        inputs={"net_cash_from_ops_m": net_ops, "ppe_purchases_m": ppe},
        result=round(result, 1),
        unit="£m",
        note=(
            "Upper bound — excludes capitalised software and intangible acquisitions. "
            "Full capex not available in extracted facts."
        ),
    )


def calc_autorama_revenue_contribution(facts: list[dict]) -> DerivedMetric:
    """Autorama Revenue as % of Group Revenue."""
    auto_rev = find_fact(facts, "autorama revenue", "2026", "£m")
    group_rev = find_fact(facts, "group revenue", "2026", "£m")

    result = (auto_rev / group_rev) * 100 if (auto_rev and group_rev and group_rev != 0) else 0.0

    return DerivedMetric(
        name="Autorama Revenue Contribution to Group",
        formula="Autorama Revenue / Group Revenue × 100",
        inputs={"autorama_revenue_m": auto_rev, "group_revenue_m": group_rev},
        result=round(result, 1),
        unit="%",
        note=(
            "Autorama contributes ~6% of group revenue but is dilutive to group margin: "
            "operating loss of −£2.0m on £39.0m revenue vs core AT margin of 70%."
        ),
    )


def calc_autorama_margin_drag(facts: list[dict]) -> DerivedMetric:
    """How many percentage points Autorama's loss suppresses the group margin.

    Without Autorama, the group operating margin would be higher by this amount.
    Calculated as: |Autorama Operating Loss| / Group Revenue × 100.
    """
    auto_loss = find_fact(facts, "autorama operating loss", "2026", "£m")
    group_rev = find_fact(facts, "group revenue", "2026", "£m")

    if auto_loss and group_rev and group_rev != 0:
        result = abs(auto_loss) / group_rev * 100
    else:
        result = 0.0

    return DerivedMetric(
        name="Autorama Margin Drag on Group (pp)",
        formula="|Autorama Operating Loss| / Group Revenue × 100",
        inputs={"autorama_op_loss_m": auto_loss, "group_revenue_m": group_rev},
        result=round(result, 2),
        unit="pp",
        note=(
            "Core AT margin is 70.0%; group margin is 63.0%. "
            "Of the ~7pp gap, ~0.3pp is attributable to Autorama's operating loss, "
            "the rest to unallocated central costs (£13.3m = ~2.1pp) and segment mix."
        ),
    )


def calc_arpr_implied_retailer_revenue(facts: list[dict]) -> DerivedMetric:
    """ARPR × Avg Forecourts × 12 = Implied Annual Retailer Revenue.

    A cross-reference between the KPI data (ARPR and forecourt count) and the
    reported Retailer Segment Revenue (£501.1m). Any divergence reflects
    volume discounts, package mix effects, or timing differences.
    """
    arpr = find_fact(facts, "average revenue per retailer", "2026")
    forecourts = find_fact(facts, "average retailer forecourts", "2026")
    stated_retailer = find_fact(facts, "retailer segment revenue", "2026", "£m")

    if arpr and forecourts:
        result = round((arpr * forecourts * 12) / 1_000_000, 1)
    else:
        result = 0.0

    note = f"Stated Retailer Segment Revenue: £{stated_retailer}m. " if stated_retailer else ""
    note += (
        "Divergence from ARPR × forecourts reflects average pricing: "
        "ARPR is an average across product tiers."
    )

    return DerivedMetric(
        name="Implied Retailer Revenue from ARPR × Forecourts",
        formula="ARPR (£/month) × Avg Forecourts × 12 / 1,000,000",
        inputs={"arpr_gbp_per_month": arpr, "avg_forecourts": forecourts},
        result=result,
        unit="£m",
        note=note,
    )


# ── Growth rate derived metrics (require prior-year facts) ─────────────────────

def _growth_pct(current: Optional[float], prior: Optional[float]) -> Optional[float]:
    """YoY growth rate as a percentage. Returns None if either input is missing or prior is 0."""
    if current is None or prior is None or prior == 0:
        return None
    return round((current - prior) / abs(prior) * 100, 1)


def calc_growth_metric(
    name: str,
    label_contains: str,
    facts: list[dict],
    prior_facts: list[dict],
    unit: str,
    note: str = "",
) -> DerivedMetric:
    """Generic YoY growth rate from current and prior-year fact lookups.

    current_period_contains is always "2026"; prior is always "2025".
    Unit is inherited for display; growth rate is in percentage points.
    """
    # Apply unit filter to disambiguate e.g. "operating profit" from "operating profit margin"
    unit_filter = unit if unit not in ("%", "count", "GBP") else None
    current = find_fact(facts, label_contains, "2026", unit_contains=unit_filter)
    prior = find_fact(prior_facts, label_contains, "2025", unit_contains=unit_filter)

    growth = _growth_pct(current, prior)
    result = growth if growth is not None else 0.0

    if current is None:
        note_extra = "Current-year value not found in verified facts."
    elif prior is None:
        note_extra = "Prior-year value not found — not parsed from excerpts."
    else:
        note_extra = f"FY2025: {prior} {unit} → FY2026: {current} {unit}."
    full_note = (note_extra + " " + note).strip()

    return DerivedMetric(
        name=name,
        formula="(FY2026 − FY2025) / |FY2025| × 100",
        inputs={"fy2026": current, "fy2025": prior},
        result=result,
        unit="%",
        note=full_note,
    )


# ── Missing data catalogue ─────────────────────────────────────────────────────

def identify_missing_data(prior_facts: list[dict]) -> list[MissingData]:
    """List calculations still blocked after prior-year extraction.

    After prior_year.py runs, most growth metrics become available. What
    remains missing is documented here so the memo writer knows the gaps.
    """
    missing = []

    missing.append(MissingData(
        name="Full Free Cash Flow",
        reason=(
            "Total capex (including capitalised software development) not available "
            "in extracted facts. Only PPE purchases (£27.3m) are captured; "
            "intangible additions are not."
        ),
        facts_needed=["Capitalised software / intangible additions FY2026"],
    ))

    # Check whether EPS growth is now computable
    prior_eps = find_fact(prior_facts, "basic earnings per share", "2025")
    if prior_eps is None:
        missing.append(MissingData(
            name="Basic EPS Growth Rate (YoY)",
            reason=(
                "FY2025 EPS not present in any verified excerpt — the EPS row in the "
                "annual report does not include a prior-year comparative in the form "
                "'(2025: Xp)'. Prior-year EPS must be obtained from the FY2025 annual report."
            ),
            facts_needed=["Basic EPS FY2025"],
        ))

    return missing


# ── Greggs-specific checks ────────────────────────────────────────────────────
#
# Greggs is a single-segment retailer. There is no Autorama-equivalent entity
# split, no ARPR × forecourts reconciliation, and no channel revenue bridge.
# The universal checks (PBT walk, EPS, cash conversion, leverage, returns)
# handle the core arithmetic. The one genuinely Greggs-specific check is the
# shop count reconciliation: Greggs publishes opening count, openings, closures,
# and period-end count as discrete KPI facts. This verifies their internal
# consistency and validates a key growth driver for the investment thesis.

def check_greggs_shop_count(facts: list[dict]) -> CrossCheck:
    """Shops at start + openings - closures = shops at period end.

    Greggs reports these four figures as part of its KPI disclosure.
    The check verifies the reported net movement is internally consistent
    with opening and closing shop counts.
    """
    year = "2025"
    shops_start = find_fact(facts, "shops at start", year, "count")
    if shops_start is None:
        shops_start = find_fact(facts, "total shops", "2024", "count")  # prior year end = start
    openings = find_fact(facts, "new shop openings", year, "count")
    if openings is None:
        openings = find_fact(facts, "shop openings", year, "count")
    closures = find_fact(facts, "shop closures", year, "count")
    shops_end = find_fact(facts, "total shops", year, "count")
    if shops_end is None:
        shops_end = find_fact(facts, "shops at period end", year, "count")

    calculated = (shops_start or 0.0) + (openings or 0.0) - (closures or 0.0)
    return _check(
        name="Greggs: Shop Count (start + openings − closures = end)",
        formula="Shops at start + New openings − Closures = Shops at period end",
        inputs={
            "shops_start": shops_start,
            "new_openings": openings,
            "closures": closures,
        },
        calculated=calculated,
        stated=shops_end,
        tolerance=1.0,   # shop counts are integers; allow ±1 for rounding
        unit="shops",
    )


def _find_fact_multi_exclude(
    facts: list[dict],
    label_contains: str,
    period_contains: str,
    unit_contains: str,
    label_not_contains: list[str],
) -> Optional[float]:
    """Like find_fact() but accepts multiple label_not_contains exclusions.

    Used by GW checks where the total label ("Revenue", "Operating profit") is
    a substring of segment labels ("Core revenue", "Licensing revenue"), so a
    single exclusion is insufficient to isolate the total.
    """
    lc = label_contains.lower()
    pc = period_contains.lower()
    uc = unit_contains.lower()
    excludes = [e.lower() for e in label_not_contains]

    matches = []
    for fact in facts:
        label = fact.get("label", "").lower()
        period = fact.get("period", "").lower()
        unit = fact.get("unit", "").lower()
        if lc not in label:
            continue
        if pc not in period:
            continue
        if uc not in unit:
            continue
        if any(exc in label for exc in excludes):
            continue
        if fact.get("citation_status") not in ("verified", "corrected"):
            continue
        try:
            matches.append(float(fact["value"]))
        except (TypeError, ValueError):
            pass

    if not matches:
        return None
    if max(matches) - min(matches) > MONETARY_TOL:
        return None   # ambiguous — treat as missing rather than raise
    return matches[0]


def check_gw_revenue_bridge(facts: list[dict]) -> CrossCheck:
    """Core revenue + Licensing revenue = Total revenue.

    Games Workshop reports two revenue streams separately: Core (miniatures,
    direct IP sales) and Licensing (royalties from video games, media, etc.).
    The income statement shows both plus the total. This check verifies the
    extraction captured all three consistently.
    """
    year = "2025"
    core_rev = find_fact(facts, "core revenue", year, "£m")
    lic_rev = find_fact(facts, "licensing revenue", year, "£m")
    total_rev = _find_fact_multi_exclude(facts, "revenue", year, "£m",
                                         ["core", "licensing"])
    calculated = (core_rev or 0.0) + (lic_rev or 0.0)
    return _check(
        name="GW: Revenue bridge (Core + Licensing = Total revenue)",
        formula="Core revenue + Licensing revenue = Revenue",
        inputs={"core_revenue": core_rev, "licensing_revenue": lic_rev},
        calculated=calculated,
        stated=total_rev,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


def check_gw_operating_profit_bridge(facts: list[dict]) -> CrossCheck:
    """Core operating profit + Licensing operating profit = Total operating profit.

    GW's two-segment structure carries through from revenue to operating profit.
    Core OP (miniatures/direct) and Licensing OP are disclosed separately.
    """
    year = "2025"
    core_op = find_fact(facts, "core operating profit", year, "£m")
    lic_op = find_fact(facts, "licensing operating profit", year, "£m")
    total_op = _find_fact_multi_exclude(facts, "operating profit", year, "£m",
                                        ["core", "licensing", "finance"])
    calculated = (core_op or 0.0) + (lic_op or 0.0)
    return _check(
        name="GW: Operating profit bridge (Core + Licensing = Total)",
        formula="Core operating profit + Licensing operating profit = Operating profit",
        inputs={"core_operating_profit": core_op, "licensing_operating_profit": lic_op},
        calculated=calculated,
        stated=total_op,
        tolerance=MONETARY_TOL,
        unit="£m",
    )


# ── Orchestration ──────────────────────────────────────────────────────────────
#
# Cross-checks are split into two groups:
#
#   UNIVERSAL_CROSS_CHECKS — run for any company. These check the structural
#     integrity of the P&L walk, EPS, cash conversion, leverage, and returns.
#     Their formulas hold for any public company reporting under UK GAAP / IFRS.
#     Fact labels are generic (e.g. "group operating profit", "profit before tax").
#
#   COMPANY_CROSS_CHECKS  — keyed by company_id. These check structures that
#     are specific to one company's reporting: segment revenue splits, entity
#     bridges, proprietary KPI reconciliations. A new company gets a new key.
#     No changes to the universal checks or orchestration are needed.
#
# COMPANY_DERIVED_METRICS follows the same pattern.

UNIVERSAL_CROSS_CHECKS = [
    check_pbt_bridge,               # OP − Net Finance Costs = PBT
    check_profit_after_tax,         # PBT − Tax = PAT
    check_effective_tax_rate,       # Tax / PBT × 100
    check_basic_eps,                # PAT / Weighted Avg Shares × 100
    check_group_op_margin,          # OP / Revenue × 100
    check_net_bank_debt,            # Drawn RCF − Cash = Net Bank Debt
    check_shareholder_returns,      # Dividends + Buyback = Total Returned
]

# Company-specific cross-checks: entity splits, segment bridges, KPI reconciliations.
# Key = company_id from config.yaml. Add a new key to support a new company.
COMPANY_CROSS_CHECKS: dict[str, list] = {
    "at": [
        check_revenue_entity_split,             # Core AT + Autorama = Group
        check_autotrader_revenue_by_channel,    # Trade + Consumer Services ≈ AT Revenue
        check_consumer_services_split,          # Private + Motoring Services = Consumer Services
        check_operating_profit_bridge,          # AT OP − Central Costs + Autorama = Group OP
        check_at_op_margin,                     # AT OP / AT Revenue × 100
    ],
    "greggs": [
        check_greggs_shop_count,    # Shops start + openings − closures = period-end count
        # No segment revenue split (single-segment retailer)
        # No ARPR × forecourts (not applicable to Greggs' business model)
    ],
    "gw": [
        check_gw_revenue_bridge,            # Core + Licensing = Total revenue
        check_gw_operating_profit_bridge,   # Core OP + Licensing OP = Total OP
        # No store-count reconciliation in V1 (store openings not consistently
        # disclosed as a numeric KPI in the financial highlights or review pages).
    ],
}

UNIVERSAL_DERIVED_METRICS = [
    calc_cash_conversion,   # Cash from Ops / OP × 100
    calc_free_cash_flow,    # Net Cash from Ops + PPE purchases
]

# Company-specific derived metrics.
COMPANY_DERIVED_METRICS: dict[str, list] = {
    "at": [
        calc_autorama_revenue_contribution,     # Autorama / Group Revenue %
        calc_autorama_margin_drag,              # How much Autorama loss suppresses group margin
        calc_arpr_implied_retailer_revenue,     # ARPR × Forecourts × 12 / 1M
    ],
    "greggs": [
        # No Autorama-equivalent segment metrics.
        # Universal metrics (cash conversion, FCF) are sufficient for Greggs.
    ],
    "gw": [
        # Universal metrics (cash conversion, FCF) are sufficient for GW.
        # Core vs Licensing margin analysis is a V2 extension.
    ],
}

# Growth metrics computed using prior-year facts from prior_year.py.
# Each tuple: (display_name, label_fragment, unit, explanatory_note)
GROWTH_METRIC_SPECS = [
    ("Group Revenue Growth (YoY)", "group revenue", "£m",
     "Group includes Autotrader + Autorama."),
    ("Autotrader Core Revenue Growth (YoY)", "autotrader revenue", "£m",
     "Core digital marketplace only."),
    ("Group Operating Profit Growth (YoY)", "group operating profit", "£m",
     "Stated +4% in the annual report."),
    ("Autotrader Operating Profit Growth (YoY)", "autotrader operating profit", "£m",
     "Core operating profit excl. central costs and Autorama."),
    ("ARPR Growth (YoY)", "average revenue per retailer", "GBP",
     "ARPR is the key pricing KPI — revenue per retailer per month."),
    ("Autorama Revenue Growth (YoY)", "autorama revenue", "£m",
     "Autorama is growing revenue but still at operating loss."),
    ("Group PBT Growth (YoY)", "group profit before tax", "£m", ""),
    ("Cash from Operations Growth (YoY)", "cash generated from operations", "£m", ""),
]


def run_all(facts: list[dict], validated_chunks: list[dict], company_id: str = "at") -> dict:
    """Run all cross-checks, derived metrics, and growth rates.

    Args:
        facts: flattened list of verified financial_figure dicts
        validated_chunks: raw chunks from validated_facts.json
                          (needed to extract prior-year facts)
        company_id: key into COMPANY_CROSS_CHECKS / COMPANY_DERIVED_METRICS.
                    Defaults to "at" (Auto Trader). Add a new key to support
                    a new company without changing any universal logic.
    """
    prior_facts = extract_prior_year_facts(validated_chunks)

    company_checks = COMPANY_CROSS_CHECKS.get(company_id, [])
    company_metrics = COMPANY_DERIVED_METRICS.get(company_id, [])

    if company_id not in COMPANY_CROSS_CHECKS:
        print(f"  Warning: no company-specific checks registered for '{company_id}'. "
              f"Running universal checks only.")

    checks = [fn(facts) for fn in UNIVERSAL_CROSS_CHECKS + company_checks]
    metrics = [fn(facts) for fn in UNIVERSAL_DERIVED_METRICS + company_metrics]

    growth_metrics = [
        calc_growth_metric(name, label, facts, prior_facts, unit, note)
        for name, label, unit, note in GROWTH_METRIC_SPECS
    ]

    # ARPR absolute increase: stated as "£141" in the report
    arpr_26 = find_fact(facts, "average revenue per retailer", "2026")
    arpr_25 = find_fact(prior_facts, "average revenue per retailer", "2025")
    if arpr_26 and arpr_25:
        arpr_abs = DerivedMetric(
            name="ARPR Absolute Increase (£/month)",
            formula="ARPR FY2026 − ARPR FY2025",
            inputs={"arpr_fy2026": arpr_26, "arpr_fy2025": arpr_25},
            result=round(arpr_26 - arpr_25, 0),
            unit="£/month",
            note="Stated as '£141 increase' in the annual report.",
        )
        growth_metrics.append(arpr_abs)

    missing = identify_missing_data(prior_facts)

    passes = sum(1 for c in checks if c.status == "pass")
    fails = sum(1 for c in checks if c.status == "fail")
    warns = sum(1 for c in checks if c.status == "warn")

    return {
        "metadata": {
            "total_checks": len(checks),
            "passed": passes,
            "failed": fails,
            "warned": warns,
            "prior_year_facts_extracted": len(prior_facts),
            "note": (
                "Warn = stated value not in extracted facts; arithmetic still performed. "
                "Fail = stated value found but arithmetic doesn't reconcile within tolerance."
            ),
        },
        "cross_checks": [asdict(c) for c in checks],
        "derived_metrics": [asdict(m) for m in metrics + growth_metrics],
        "missing_data": [asdict(m) for m in missing],
    }


def print_report(result: dict) -> None:
    """Print a human-readable summary of the finance run."""
    meta = result["metadata"]
    checks = result["cross_checks"]
    metrics = result["derived_metrics"]
    missing = result["missing_data"]

    width = 60
    print(f"\n{'='*width}")
    print("FINANCE MODULE — CROSS-CHECK REPORT")
    print(f"{'='*width}")
    print(f"Checks run:  {meta['total_checks']}")
    print(f"  PASS:      {meta['passed']}")
    print(f"  FAIL:      {meta['failed']}")
    print(f"  WARN:      {meta['warned']}  (stated value missing from facts)")
    print(f"Prior-year facts extracted: {meta.get('prior_year_facts_extracted', '—')}")

    if meta["failed"]:
        print(f"\n{'─'*width}")
        print("FAILURES:")
        for c in checks:
            if c["status"] == "fail":
                print(f"  ✗ {c['name']}")
                print(f"    Calculated: {c['calculated']} {c['unit']}")
                print(f"    Stated:     {c['stated']} {c['unit']}")
                print(f"    Note:       {c['note']}")

    print(f"\n{'─'*width}")
    print("DERIVED METRICS (incl. growth rates):")
    for m in metrics:
        print(f"  {m['name']}: {m['result']} {m['unit']}")
        if m["note"]:
            print(f"    Note: {m['note']}")

    print(f"\n{'─'*width}")
    print(f"MISSING DATA ({len(missing)} items — calculations blocked):")
    for m in missing:
        print(f"  • {m['name']}")
        print(f"    {m['reason'][:100]}...")


def main():
    parser = argparse.ArgumentParser(description="Deterministic finance module")
    parser.add_argument("--facts", default="output/validated_facts.json")
    parser.add_argument("--out", default="output/financials.json")
    parser.add_argument("--company", default="at",
                        help="Company ID for company-specific checks (default: at)")
    args = parser.parse_args()

    print(f"Loading facts from {args.facts}...")
    facts, chunks = load_verified_facts(args.facts)
    print(f"  {len(facts)} verified/corrected financial figures loaded")

    result = run_all(facts, chunks, company_id=args.company)
    print_report(result)

    os.makedirs("output", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nWrote {args.out}")


if __name__ == "__main__":
    main()
