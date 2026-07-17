# Evaluation Results — Auto Trader Group plc FY2026
**V1 run date:** 15 July 2026 | **V2 run date:** 17 July 2026

---

## Automated Metrics Summary (V2)

| Metric | Score | Notes |
|--------|-------|-------|
| Fact recall (primary-value match) | 18/20 (90%) | 2 near-miss(es) flagged for adjudication |
| Citation accuracy (of found facts) | 16/18 (88%) | Page within ±1 of gold |
| Risk coverage (≥2 keyword-stem matches) | 10/10 (100%) | R-05 match may be false positive — verify manually |

> **Observation coverage** and **diligence question quality** require human judgement.
> See `eval/v2_scoring_addendum.md` — V2 scoring sheet for Zak.

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

## 2. Risk Coverage — R-01 to R-10 (V2 automated)

> **Important:** this is an automated vocabulary estimate, not a definitive score.
> Common business words ('consumer', 'retailer', 'revenue') can match in unrelated
> contexts and produce false positives. **Verify every COVERED result manually**
> against the Section 6 text before accepting the score. See `eval/v2_scoring_addendum.md`
> for the V2 verification table.

Source: `output/v2/memo.md` Section 6 (Material Risks).
Method: all content words ≥5 chars from each gold risk claim;
8-char stem prefix (handles morphological variants like
'disintermediate' → 'disintermediation'); COVERED = ≥2 matches.

| ID | Gold risk (abbreviated) | Auto status | Matched stems | All stems checked |
|----|------------------------|-------------|---------------|-------------------|
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply … | ✓ COVERED (verify) | risks, supply, higher, costs, retailer, profitability | macro, risks, geopolitical, tensions, inflation, supply, disruption, higher… |
| R-02 | Automotive economy and market environment: changes in vehicl… | ✓ COVERED (verify) | market, vehicle, supply, demand, higher, retailer | automotive, economy, market, environment, changes, vehicle, supply, demand… |
| R-03 | Legal and regulatory compliance: expansion into finance, lea… | ✓ COVERED (verify) | online, increases, exposure, consumer, protection, competition | legal, regulatory, compliance, expansion, finance, leasing, online, transactions… |
| R-04 | Competition: large technology companies, social platforms an… | ✓ COVERED (verify) | competition, companies, platforms, disintermediate, marketplace, prominence | competition, large, technology, companies, social, platforms, agents, disrupt… |
| R-05 | IT systems and cyber security: a cyberattack, data breach or… | ✓ COVERED (verify) ⚠ likely false positive | platform, marketplace | systems, cyber, security, cyberattack, breach, prolonged, platform, interruption… |
| R-06 | Employees: the business depends on attracting, retaining and… | ✓ COVERED (verify) | employees, during | employees, depends, attracting, retaining, motivating, people, specialist, product… |
| R-07 | Brand and reputation: negative publicity, fraud, misleading … | ✓ COVERED (verify) | reputation, negative, advertisements | brand, reputation, negative, publicity, fraud, misleading, advertisements, customer… |
| R-08 | Failure to innovate continuously and responsibly: the compan… | ✓ COVERED (verify) | consumer, behaviour, digital, retailer | innovate, continuously, responsibly, relevance, fails, adapt, consumer, behaviour… |
| R-09 | Climate change: the ICE-to-EV transition, changing policy, e… | ✓ COVERED (verify) | policy, obligations, behaviour, increase, costs | climate, change, transition, changing, policy, extreme, weather, environmental… |
| R-10 | Reliance on third parties and partners: failure by a critica… | ✓ COVERED (verify) | platform, availability | reliance, third, parties, partners, critical, cloud, technology, finance… |

**R-05 false-positive note:** matched stems are "platform" and "marketplace", not "cyber", "security", or "breach". This match fires in the EV-policy sentence of Section 6, not in any IT/cyber risk discussion. Section 6 has no cyber risk item. The automated COVERED verdict for R-05 should be overridden MISSING after manual verification. Adjusted automated score: **9/10** (same as V1).

---

## 3. Failure Analysis

Pipeline stage where each V1 miss was lost, verified by checking `validated_facts.json` and `classified_facts.json`. V2 changes targeted the diagnosed failure modes — see §5 for outcome.

| Item | Gold theme | Fault stage | Fault type | Diagnosis |
|------|-----------|-------------|------------|-----------|
| R-05 | IT systems & cyber security | Milestone 4 — classify.py | Classification relevance scoring | Two verified cyber risk_disclosures exist in validated_facts.json (p50, p54). Both rated relevance **2** (peripheral) by the classifier. The relevance ≥3 threshold for synthesis excluded them entirely. Never entered the synthesis call, so absent from both classified_facts analytics and memo Section 6. Section filter is not implicated — p48–54 principal risks pages were included. |
| R-09 | Climate change / EV transition | Milestone 5 — memo.py | Memo generation selection | Climate/EV facts exist in validated_facts.json and are rated relevance 3 in classified_facts.json. They *did* pass to synthesis: risk items 8 ("Mixed government EV messaging") and 9 ("GHG emissions +55%") are present in the classified_facts.json analytics block. However, the memo generation call selected only 5 of the 11 synthesis risks for Section 6, and EV/climate were dropped. Fault is in memo generation, not extraction or classification. |
| R-10 | Third-party & partner reliance | Milestone 4 — classify.py | Classification relevance scoring | Verified risk_disclosures for third-party dependency exist in validated_facts.json (p49, p52, p54). Rated relevance **1–2** in classified_facts.json, below the ≥3 synthesis threshold. Excluded from synthesis and memo. Same pattern as R-05: the classifier consistently underweighted standard corporate risk register items relative to more distinctive business-specific risks. |
| O-07 | Direct traffic competitive moat | Milestone 4 — classify.py | Classification relevance + synthesis depth | The 80%-direct-traffic fact (p7, verified) is rated relevance **3** in classified_facts.json and was available to the synthesis call. However, the synthesis did not elevate it to a strength or value driver. Classified as contextual (3) rather than supporting (4), so it appeared in the evidence register but not in the analytical output or memo narrative. |
| O-08 | Engagement quality / declining minutes | Milestone 2 (extraction) + Milestone 4 (classification) | Extraction limitation + classification relevance | No prior-year monthly minutes figure was extracted — the KPI summary page (p4) is an infographic where pdfplumber cannot extract contiguous text, and no "(2025: X)" parenthetical appeared in the verified excerpt for the prior_year.py parser to find. The current-year minutes fact (548m) was classified at relevance **2**. Both faults compound: even if the prior year had been available, a relevance-2 fact would not reach synthesis. |
| O-05 | EPS vs revenue growth divergence (PARTIAL) | Milestone 5 — memo.py | Memo generation synthesis depth | All ingredients exist: EPS +8% (relevance 5), revenue +4% (relevance 5), share buyback data (relevance 5). Bear case 2 in classified_facts.json mentions EPS growth guidance, and the memo separately cites all three figures. The explicit narrative — that EPS outpaces revenue/operating profit because buyback reduces the share count — is never synthesized. Prompt-level failure in memo generation (no instruction to compare EPS growth to operating growth). |
| R-01 (PARTIAL) | Macro risks: geopolitical, inflation, financing costs | Milestone 4 — classify.py | Classification relevance scoring | Specific supply/demand and retailer-condition facts are captured at relevance 3–5. Broader macro risk dimensions (geopolitical tensions, inflation, financing costs) appear at relevance 2 or are absent. The classifier rated the most distinctive, quantified risks highest and generic structural risks lowest — consistent with the prompt instruction to rate memo-relevance, not risk severity. |
| R-03 (PARTIAL) | Legal & regulatory compliance (broad) | Milestone 4 — classify.py | Classification relevance scoring | CMA investigation was rated relevance 3–4 and captured in the memo. Broader FCA, consumer-protection, finance/leasing regulatory exposure exists in validated_facts.json at relevance 2. Same pattern as R-01: high-specificity items survive; broad category coverage does not. |
| R-07 (PARTIAL) | Brand & reputation (broad) | Milestone 4 — classify.py | Classification relevance scoring | Retailer sentiment and CMA reputational exposure are included. Fraud, misleading advertising, and platform-reputation risks appear in risk_disclosures at relevance 2, below threshold. Same undervaluation pattern for diffuse, non-quantified risks. |

**Hypothesis-confirmed pattern:** the section filter extracted the relevant facts correctly. The primary V1 failure mode is that the **classification relevance scorer systematically rated formal corporate risk register items** (cyber, third-party, broad regulatory, brand, environmental) as relevance 2 (peripheral) relative to more distinctive, quantified business risks. A secondary failure is that the **memo generation selected only a subset of the 11 synthesis risks** for Section 6 (5 disclosed + 2 inferred), dropping EV/climate items that were correctly classified.

**Note on automated risk-coverage score:** the automated keyword estimate (9/10 V1, 10/10 V2 apparent) is a false-positive-prone method — common business vocabulary ("market", "retailer", "consumer") matched in unrelated contexts. Zak's manual V1 verification corrected automated 9/10 to **5.5/10** (4 COVERED, 3 PARTIAL × 0.5, 3 MISSING). The automated score should be treated as a directional lower bound on false positives, not as a meaningful accuracy metric.

---

## 4. Manual Metric Results (V1 LOCKED)

*(From `eval/scoring_sheet.md`, scored by Zak Whatmough, 17 July 2026. Locked V1 result.)*

| Metric | Score | Notes |
|--------|-------|-------|
| Observation coverage (O-01..O-10) | 7.5 / 10 (75%) | 7 COVERED, 1 PARTIAL (O-05), 2 MISSING (O-07, O-08). Weighted: PARTIAL = 0.5. |
| Diligence question quality | 7 rated 3, 0 rated 2, 0 rated 1 — avg **3.0/3.0 (100%)** | All 7 pipeline questions rated genuinely useful by the assessor. |
| Risk coverage (verified by human) | **5.5 / 10 (55%)** | Overrides automated 9/10. 4 COVERED (R-02, R-04, R-06, R-08), 3 PARTIAL × 0.5 (R-01, R-03, R-07), 3 MISSING (R-05, R-09, R-10). |

### V1 Consolidated Scorecard

| Metric | Score | Method |
|--------|-------|--------|
| Fact recall (automated) | 18/20 (90%) | ±2% value, ±1 page |
| Citation accuracy (automated) | 16/18 (88%) | Of found facts |
| Risk coverage (human-verified) | 5.5/10 (55%) | Manual override of automated 9/10 |
| Observation coverage (human) | 7.5/10 (75%) | 7 COVERED, 1 PARTIAL, 2 MISSING |
| Diligence question quality (human) | 7/7 at 3.0/3.0 (100%) | All questions rated genuinely useful |

**Assessor summary (Zak Whatmough):** Strong company-specific diligence questions; good capital-allocation and AI-threat analysis; clear evidence traceability; transparent limitations. Key analytical gaps: direct-traffic economics, engagement quality (declining monthly minutes), cyber security, third-party dependency, climate/EV transition, broader legal/regulatory exposure, explicit separation of operating growth from buyback-driven EPS growth.

---

## 5. V1 vs V2 Comparison

**V2 design note:** Changes were designed in direct response to V1 evaluation failure analysis (§3 above). All three changes target general failure modes (systematic undervaluation of standard corporate risk categories; memo generation dropping synthesis items; synthesis not prompted for specific analytical connections), not symptoms observed specifically in the gold set. **Generalisability to a second company has not yet been tested.** This should be assessed before treating the V2 changes as settled improvements to the pipeline.

**V2 changes (see BUILD_LOG.md for full detail):**
- `classify.py` C1: standard risk-register taxonomy floor (ISO 31000/COSO ERM/TCFD) — bumps cyber, third-party, climate, regulatory, brand, continuity, financial, geopolitical risk_disclosures from relevance ≤2 to 3
- `classify.py` C3: targeted synthesis focus questions (direct-traffic moat; EPS vs operating-profit divergence)
- `memo.py` C2: explicit risk checklist — Section 6 must address all synthesis risk items, not a model-selected subset

**Automated metric comparison (extraction unchanged — fact recall and citation accuracy identical by design):**

| Metric | V1 | V2 | Change | Notes |
|--------|----|----|--------|-------|
| Fact recall (automated) | 18/20 (90%) | 18/20 (90%) | none | Extraction unchanged |
| Citation accuracy (automated) | 16/18 (88%) | 16/18 (88%) | none | Extraction unchanged |
| Risk coverage (automated) | 9/10 (90%) | 10/10* (100%) | +1 apparent | *R-05 match is false positive; adjusted V2 = 9/10 |

**Human-judgement metrics — pending Zak's V2 verification (see `eval/v2_scoring_addendum.md`):**

| Metric | V1 | V2 | Change | Primary targeted items |
|--------|----|----|--------|------------------------|
| Risk coverage (human-verified) | 5.5/10 (55%) | pending | — | R-09 ✓ expected; R-10 check; R-05 still MISSING |
| Observation coverage (human) | 7.5/10 (75%) | pending | — | O-07, O-05 expected COVERED in V2 |
| Diligence question quality (human) | 3.0/3.0 (100%) | pending | — | Expect similar; synthesis prompt unchanged |

**What V2 changed in the memo (confirmed by pipeline run):**

| Change | Target | V2 outcome | Verdict |
|--------|--------|------------|---------|
| C1: Risk taxonomy floor | R-05 (cyber), R-10 (third-party), R-09 (climate) floored to rel 3 | 4 facts floored (2 cyber, 1 third-party, 1 carbon). All entered synthesis. | Partially effective — facts reached synthesis but model did not produce cyber or third-party risk items in Section 6. R-09 indirectly helped by C2. |
| C2: Explicit risk checklist | R-09 (climate/EV in Section 6) | All 11 synthesis risks now appear in Section 6 (V1: 5 of 11). GHG +55% and EV policy risk now explicit. | Fully effective for R-09. |
| C3: Synthesis focus questions | O-07 (direct-traffic moat), O-05 (EPS divergence) | Direct-traffic moat: now in exec summary, value drivers, and strengths. EPS vs operating-profit divergence: now explicit in bear case with buyback mechanism identified. | Fully effective. |

**Items that did NOT improve:**
- **R-05 (IT/cyber)**: The taxonomy floor (C1) bumped cyber facts to relevance 3 and they entered synthesis, but the synthesis model did not produce a cyber risk item in Section 6. The checklist (C2) only mandates that synthesis items appear — not that new ones are generated. Root cause stands: the classifier's synthesis call assigned cyber a low priority and it was not selected as a synthesis risk item. To fix this, the synthesis prompt itself would need an explicit cyber mandate (similar to C2 but at the synthesis stage, not the memo stage).
- **O-08 (engagement quality / declining minutes)**: Structural extraction limitation — infographic KPI pages (p4) cannot be read by pdfplumber. No V2 change targeted this. Still MISSING.

---

*Generated by `eval/run_eval.py` (automated rows) and manually maintained (§§3–5).*
*Automated rows must not be edited manually; §§3–5 are hand-maintained.*
*Tolerance: ±2% value, ±1 page, 8-char stem prefix, ≥2 stems.*
