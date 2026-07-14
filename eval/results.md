# Evaluation Results — Auto Trader Group plc FY2026
**Run date:** 15 July 2026

---

## Automated Metrics Summary

| Metric | Score | Notes |
|--------|-------|-------|
| Fact recall (primary-value match) | 18/20 (90%) | 2 near-miss(es) flagged for adjudication |
| Citation accuracy (of found facts) | 16/18 (88%) | Page within ±1 of gold |
| Risk coverage (≥2 keyword-stem matches) | 9/10 (90%) | 1 flagged for adjudication, 0 missing |

> **Observation coverage** and **diligence question quality** require human judgement.
> See `eval/scoring_sheet.md` — fill that in before updating this file.

---

## 1. Fact Recall — F-01 to F-20

Source: `output/validated_facts.json` (verified + corrected financial figures).
Match: primary value from claim within ±2% of pipeline fact value.
Citation: pipeline page within ±1 of gold page.

### Found ✓

| ID | Claim (abbreviated) | Matched | Pipeline label | Gold pg | Pipeline pg | Cite |
|----|---------------------|---------|----------------|---------|-------------|------|
| F-01 | Group revenue for FY2026 was £624.3m, up 4% from £601.1m in FY202… | £624.3m | Group revenue | 6 | 6 | ✓ |
| F-02 | Core Autotrader business revenue was £585.3m in FY2026, an increa… | £585.3m | Core Autotrader revenue | 6 | 6 | ✓ |
| F-03 | Autorama contributed revenue of £39.0m in FY2026 (FY2025: £36.3m) | £39.0m | Autorama revenue | 6 | 6 | ✓ |
| F-04 | Core Autotrader operating profit was £408.0m in FY2026 (FY2025: £… | £408.0m | Core Autotrader operating profit | 6 | 6 | ✓ |
| F-05 | Autorama's operating losses reduced to £2.0m in FY2026 from £4.3m… | £2.0m | Autorama operating loss | 6 | 6 | ✓ |
| F-06 | Group operating profit increased 4% to £392.7m in FY2026 (FY2025:… | £392.7m | Group operating profit | 6 | 6 | ✓ |
| F-07 | Basic earnings per share increased 8% to 34.17p in FY2026 (FY2025… | 34.17p | Basic earnings per share | 6 | 4 | ✗ |
| F-08 | The proposed final dividend is 7.8p per share, giving total divid… | 7.8p | Final dividend per share | 6 | 6 | ✓ |
| F-09 | The company bought back 58.5 million shares in FY2026, 6.6% of is… | 58.5 million | Shares purchased under buyback programme | 6 | 6 | ✓ |
| F-10 | At year end £165m of the debt facility was drawn, taking leverage… | £165m | Debt facility drawn | 6 | 6 | ✓ |
| F-11 | Total returns to shareholders (buybacks plus dividends) were £463… | £463.2m | Total returned to shareholders | 6 | 6 | ✓ |
| F-13 | Cash generated from operations increased to £418.0m in FY2026 (FY… | £418.0m | Cash Generated from Operations | 23 | 23 | ✓ |
| F-14 | Net cash generated from operating activities was £322.8m in FY202… | £322.8m | Net Cash Generated from Operating Activities | 25 | 25 | ✓ |
| F-15 | The average number of retailer forecourts advertising on the plat… | 13,942 | Number of Retailer Forecourts | 23 | 20 | ✗ |
| F-17 | Average monthly cross-platform visits were 81.7 million in FY2026… | 81.7 million | Cross-platform Visits | 20 | 20 | ✓ |
| F-18 | Profit for the year attributable to equity holders was £293.9m in… | £293.9m | Profit for the year | 103 | 103 | ✓ |
| F-19 | At 31 March 2026 the Group had net bank debt of £146.8m (31 March… | £146.8m | Net Bank Debt | 25 | 25 | ✓ |
| F-20 | Calls on the Group's technology and data services increased to an… | 155 million | Technology and data service calls | 7 | 7 | ✓ |

### Near-miss — manual adjudication needed ⚠

Primary value not in pipeline facts; a secondary value matched.
Check whether the pipeline captured the same fact under a different label.

| ID | Claim (abbreviated) | Secondary match | Pipeline label | Gold pg | Pipeline pg |
|----|---------------------|-----------------|----------------|---------|-------------|
| F-12 | For 2027 the company expects to return £600m to shareholders, inc… | £500m | Retailer Segment Revenue | 6 | 23 |
| F-16 | Average revenue per retailer (ARPR) per month increased 5%, or £1… | £2,995 | Average Revenue Per Retailer (ARPR) per month | 23 | 23 |

---

## 2. Risk Coverage — R-01 to R-10

> **Important:** this is an automated vocabulary estimate, not a definitive score.
> Common business words ('consumer', 'retailer', 'revenue') can match in unrelated
> contexts and produce false positives. **Verify every COVERED result manually**
> against the Section 6 text before accepting the score. See `eval/scoring_sheet.md`
> Part C for a verification table.

Source: memo Section 6 (Material Risks).
Method: all content words ≥5 chars from each gold risk claim;
8-char stem prefix (handles morphological variants like
'disintermediate' → 'disintermediation'); COVERED = ≥2 matches.

| ID | Gold risk (abbreviated) | Auto status | Matched stems | All stems checked |
|----|------------------------|-------------|---------------|-------------------|
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply … | ✓ COVERED (verify) | risks, supply, retailer, consumer | macro, risks, geopolitical, tensions, inflation, supply, disruption, higher… |
| R-02 | Automotive economy and market environment: changes in vehicl… | ✓ COVERED (verify) | market, changes, vehicle, supply, retailer, consumer | automotive, economy, market, environment, changes, vehicle, supply, demand… |
| R-03 | Legal and regulatory compliance: expansion into finance, lea… | ✓ COVERED (verify) | online, increases, exposure, consumer | legal, regulatory, compliance, expansion, finance, leasing, online, transactions… |
| R-04 | Competition: large technology companies, social platforms an… | ✓ COVERED (verify) | disintermediate, marketplace, reducing, prominence | competition, large, technology, companies, social, platforms, agents, disrupt… |
| R-05 | IT systems and cyber security: a cyberattack, data breach or… | ⚠ FLAGGED | marketplace | systems, cyber, security, cyberattack, breach, prolonged, platform, interruption… |
| R-06 | Employees: the business depends on attracting, retaining and… | ✓ COVERED (verify) | employees, product, during, change | employees, depends, attracting, retaining, motivating, people, specialist, product… |
| R-07 | Brand and reputation: negative publicity, fraud, misleading … | ✓ COVERED (verify) | reputation, negative, revenue | brand, reputation, negative, publicity, fraud, misleading, advertisements, customer… |
| R-08 | Failure to innovate continuously and responsibly: the compan… | ✓ COVERED (verify) | consumer, behaviour, retailer | innovate, continuously, responsibly, relevance, fails, adapt, consumer, behaviour… |
| R-09 | Climate change: the ICE-to-EV transition, changing policy, e… | ✓ COVERED (verify) | change, behaviour, increase | climate, change, transition, changing, policy, extreme, weather, environmental… |
| R-10 | Reliance on third parties and partners: failure by a critica… | ✓ COVERED (verify) | reliance, availability, product | reliance, third, parties, partners, critical, cloud, technology, finance… |

**Flagged (auto):** 1 stem match — may be coincidental. Check Section 6 directly.

---

## 3. Failure Analysis

*(Complete manually after reviewing the per-item detail above.)*
*(For each miss, classify: extraction fault / chunking fault / prompt fault / validation gap.)*

| Item | Category | Fault type | Diagnosis |
|------|----------|------------|-----------|
| — | — | — | — |

---

## 4. Manual Metric Results

*(Paste results from `eval/scoring_sheet.md` here after scoring.)*

| Metric | Score | Notes |
|--------|-------|-------|
| Observation coverage (O-01..O-10) | ? / 10 | |
| Diligence question quality | ? rated 3, ? rated 2, ? rated 1 | |

---

*Generated by `eval/run_eval.py`. Automated rows must not be edited manually.*
*Tolerance: ±2% value, ±1 page, 8-char stem prefix, ≥2 stems.*
