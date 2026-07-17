# V2 Scoring Addendum — Manual Verdicts Required
**For:** Zak Whatmough | **V2 memo:** `output/v2/memo.md` | **Date:** 17 July 2026

This is your manual scoring sheet for the V2 memo. It mirrors the structure of `eval/scoring_sheet.md` (V1), but pre-annotated with what V2 targeted so you know where to focus.

Three things to do:
1. Open `output/v2/memo.md` alongside this sheet.
2. Fill in each verdict (COVERED / PARTIAL / MISSING) and score.
3. Update `eval/results.md §5` with the final human-verified scores.

---

## Part A — Observation Coverage (O-01 to O-10)

Score each item: COVERED (1.0), PARTIAL (0.5), MISSING (0.0).

**V2 targeted O-07 and O-05** via Change 3 (synthesis focus questions). Check those two first.

| ID | Observation (abbreviated) | V1 verdict | V2 expected | V2 actual | Notes |
|----|--------------------------|------------|-------------|-----------|-------|
| O-01 | Revenue grew 4% to £624.3m, with core AT (94%) growing faster than Autorama (6%) | COVERED | no change | | |
| O-02 | Operating margin compressed from 62.6% to 62.9% — flat, core AT margin 69.7% | COVERED | no change | | |
| O-03 | EPS +8% to 34.17p, outpacing revenue/operating profit growth | COVERED | no change | | |
| O-04 | Capital allocation: £463m returned (buyback + dividend), leverage 0.4× EBITDA | COVERED | no change | | |
| O-05 | **EPS outpaces revenue/op profit because buybacks reduce share count** (explicit narrative) | PARTIAL | **COVERED** (C3) | | Check bear case / Section 5 for explicit buyback-EPS mechanism |
| O-06 | Autorama: revenue growing, losses narrowing from £4.3m to £2.0m, path to breakeven | COVERED | no change | | |
| O-07 | **80% of visits direct (not paid search): structural traffic advantage vs. competitors** | MISSING | **COVERED** (C3) | | Check Section 1 exec summary, Section 4 (value drivers), Section 5 (strengths) |
| O-08 | Monthly minutes declining (engagement quality concern despite rising visit volumes) | MISSING | no change | MISSING | Structural extraction limitation — infographic page; no fix in V2 |
| O-09 | CMA investigation into market information products | COVERED | no change | | |
| O-10 | Autotrader's D&B dataset (470k vehicles, 3.3 trillion data points) as a competitive moat | COVERED | no change | | |

**O-05 verification hint:** Look in the bear case section. V2 should say something like "EPS (+8%) outpaces operating profit (+4%) because the buyback reduced the weighted average share count, not because underlying earnings accelerated."

**O-07 verification hint:** Look in Section 1 (executive summary) and Section 5 (strengths). V2 should mention that ~80% of visits arrive directly (typed URL or app) rather than via paid search, and explain why this reduces customer acquisition cost relative to competitors reliant on Google/Meta spend.

---

## Part B — Diligence Question Quality (1–3 scale)

Rate each V2 pipeline diligence question: 3 = genuinely useful to an analyst, 2 = generic/boilerplate, 1 = misleading or off-target.

*(V2 changes did not specifically target diligence questions — Section 8 prompt was unchanged. Expect similar to V1 average of 3.0/3.0. Verify in `output/v2/memo.md` Section 8.)*

| # | Question (from V2 memo Section 8) | Score (1–3) | Notes |
|---|----------------------------------|-------------|-------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |
| 6 | | | |
| 7 | | | |

**Average:** ___ / 3.0

---

## Part C — Risk Coverage Verification (R-01 to R-10)

Score each risk item: COVERED (1.0), PARTIAL (0.5), MISSING (0.0).

**Open `output/v2/memo.md` Section 6 and check each item.** The automated scores are shown but known to be unreliable (keyword false positives).

**V2 priority items — read Section 6 carefully for these:**

| ID | Gold risk (abbreviated) | V1 verdict | Auto V2 | V2 expected | V2 actual | Notes |
|----|--------------------------|------------|---------|-------------|-----------|-------|
| R-05 | IT systems and cyber security | MISSING | ✓ (false positive) | **MISSING** | | Auto match = "platform" + "marketplace" in EV policy sentence. No cyber/IT risk discussion expected. Confirm MISSING. |
| R-09 | Climate change: ICE-to-EV transition, changing policy, emissions obligations | MISSING | ✓ | **COVERED** | | V2 Section 6 should explicitly mention GHG emissions up 55% y/y and EV policy uncertainty (pay-per-mile tax, mixed government messaging). |
| R-10 | Reliance on third parties and partners (critical cloud, technology providers) | MISSING | ✓ | **PARTIAL?** | | Auto match = "platform" + "availability". The taxonomy floor (C1) bumped a third-party fact to rel 3, but the synthesis did not produce a third-party risk item. May still be absent from Section 6 prose. Verify. |

**Other items — re-verify against V2 Section 6 (not just assumed same as V1):**

| ID | Gold risk (abbreviated) | V1 verdict | Auto V2 | V2 actual | Notes |
|----|--------------------------|------------|---------|-----------|-------|
| R-01 | Macro risks: geopolitical tensions, inflation, supply disruption, financing costs | PARTIAL | ✓ | | Did the checklist pull in more macro breadth? |
| R-02 | Automotive economy and market environment | COVERED | ✓ | | Expect COVERED — unchanged |
| R-03 | Legal and regulatory compliance (FCA, CMA, finance/leasing expansion) | PARTIAL | ✓ | | |
| R-04 | Competition: large tech, social platforms, AI agents disintermediating | COVERED | ✓ | | Expect COVERED — unchanged |
| R-06 | Employees: attracting, retaining specialist talent | COVERED | ✓ | | Expect COVERED — unchanged |
| R-07 | Brand and reputation | PARTIAL | ✓ | | |
| R-08 | Failure to innovate continuously and responsibly | COVERED | ✓ | | Expect COVERED — unchanged |

---

## Scoring Summary (fill in and copy to `eval/results.md §5`)

| Metric | V1 | V2 | Change |
|--------|----|----|--------|
| Fact recall (automated) | 18/20 (90%) | 18/20 (90%) | none |
| Citation accuracy (automated) | 16/18 (88%) | 16/18 (88%) | none |
| Risk coverage (human-verified) | 5.5/10 (55%) | _/10 (_%) | |
| Observation coverage (human) | 7.5/10 (75%) | _/10 (_%) | |
| Diligence question quality (human) | 3.0/3.0 (100%) | _/3.0 (_%) | |
