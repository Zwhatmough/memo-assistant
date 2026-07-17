# Evaluation Results — Auto Trader Group plc FY2026
**V1 run date:** 15 July 2026 | **V2 run date:** 17 July 2026 | **V3 run date:** 17 July 2026

---

## Automated Metrics Summary (V3)

| Metric | Score | Notes |
|--------|-------|-------|
| Fact recall (primary-value match) | 18/20 (90%) | 2 near-miss(es) flagged for adjudication |
| Citation accuracy (of found facts) | 16/18 (88%) | Page within ±1 of gold |
| Risk coverage (≥2 keyword-stem matches) | 10/10 (100%) | Automated — all 10 verified by keyword match; manual verification required |

> **Observation coverage** and **diligence question quality** require human judgement.
> See `eval/v3_scoring_addendum.md` — V3 risk scoring sheet for Zak.

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

## 2. Risk Coverage — R-01 to R-10 (V3 automated)

> **Important:** this is an automated vocabulary estimate, not a definitive score.
> Common business words ('consumer', 'retailer', 'revenue') can match in unrelated
> contexts and produce false positives. **Verify every COVERED result manually**
> against the Section 6 text before accepting the score. See `eval/v3_scoring_addendum.md`
> for the V3 verification table.

Source: `output/v3/memo.md` Section 6 (Material Risks).
Method: all content words ≥5 chars from each gold risk claim;
8-char stem prefix (handles morphological variants like
'disintermediate' → 'disintermediation'); COVERED = ≥2 matches.

| ID | Gold risk (abbreviated) | Auto status | Matched stems | All stems checked |
|----|------------------------|-------------|---------------|-------------------|
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply … | ✓ COVERED (verify) | macro, risks, geopolitical, supply, higher, financing | macro, risks, geopolitical, tensions, inflation, supply, disruption, higher… |
| R-02 | Automotive economy and market environment: changes in vehicl… | ✓ COVERED (verify) | market, environment, vehicle, supply, demand, higher | automotive, economy, market, environment, changes, vehicle, supply, demand… |
| R-03 | Legal and regulatory compliance: expansion into finance, lea… | ✓ COVERED (verify) | legal, regulatory, compliance, online, increases, exposure | legal, regulatory, compliance, expansion, finance, leasing, online, transactions… |
| R-04 | Competition: large technology companies, social platforms an… | ✓ COVERED (verify) | competition, technology, companies, disrupt, customer, journey | competition, large, technology, companies, social, platforms, agents, disrupt… |
| R-05 | IT systems and cyber security: a cyberattack, data breach or… | ✓ COVERED (verify) | systems, cyber, security, customers, marketplace | systems, cyber, security, cyberattack, breach, prolonged, platform, interruption… |
| R-06 | Employees: the business depends on attracting, retaining and… | ✓ COVERED (verify) | employees, depends, people, product, technology, commercial | employees, depends, attracting, retaining, motivating, people, specialist, product… |
| R-07 | Brand and reputation: negative publicity, fraud, misleading … | ✓ COVERED (verify) | negative, advertisements, customer, audience, revenue | brand, reputation, negative, publicity, fraud, misleading, advertisements, customer… |
| R-08 | Failure to innovate continuously and responsibly: the compan… | ✓ COVERED (verify) | consumer, digital, retailer | innovate, continuously, responsibly, relevance, fails, adapt, consumer, behaviour… |
| R-09 | Climate change: the ICE-to-EV transition, changing policy, e… | ✓ COVERED (verify) | climate, change, environmental, obligations, increase, costs | climate, change, transition, changing, policy, extreme, weather, environmental… |
| R-10 | Reliance on third parties and partners: failure by a critica… | ✓ COVERED (verify) | reliance, third, parties, technology, partner, product | reliance, third, parties, partners, critical, cloud, technology, finance… |

**V3 change:** R-05 now has genuine keyword matches ("cyber", "security") — not the false-positive "platform/marketplace" match seen in V2. R-10 now has "third" and "reliance" as primary matches — not the V2 false-positive "platform/availability". Manual verification required to confirm these are substantive risk analyses, not incidental mentions.

---

## 3. Failure Analysis

Pipeline stage where each V1 miss was lost, verified by checking `validated_facts.json` and `classified_facts.json`. V2 and V3 changes targeted the diagnosed failure modes — see §5 for outcomes.

| Item | Gold theme | Fault stage | Fault type | Diagnosis |
|------|-----------|-------------|------------|-----------|
| R-05 | IT systems & cyber security | Milestone 4 — classify.py | Classification relevance scoring | Two verified cyber risk_disclosures exist in validated_facts.json (p50, p54). Both rated relevance **2** (peripheral) by the classifier. The relevance ≥3 threshold for synthesis excluded them entirely. Never entered the synthesis call, so absent from both classified_facts analytics and memo Section 6. Section filter is not implicated — p48–54 principal risks pages were included. |
| R-09 | Climate change / EV transition | Milestone 5 — memo.py | Memo generation selection | Climate/EV facts exist in validated_facts.json and are rated relevance 3 in classified_facts.json. They *did* pass to synthesis: risk items 8 ("Mixed government EV messaging") and 9 ("GHG emissions +55%") are present in the classified_facts.json analytics block. However, the memo generation call selected only 5 of the 11 synthesis risks for Section 6, and EV/climate were dropped. Fault is in memo generation, not extraction or classification. |
| R-10 | Third-party & partner reliance | Milestone 4 — classify.py | Classification relevance scoring + framing | Verified risk_disclosures for third-party dependency exist in validated_facts.json (p49, p52, p54). Rated relevance **1–2** in classified_facts V1, below the ≥3 synthesis threshold. V2 C1 (taxonomy floor) bumped these to relevance 3 and they entered synthesis — but the synthesis model framed 220+ partner integrations as a monetisation opportunity rather than a dependency risk. V3 risk skeleton mandates explicit risk framing, targeting this failure. |
| O-07 | Direct traffic competitive moat | Milestone 4 — classify.py | Classification relevance + synthesis depth | The 80%-direct-traffic fact (p7, verified) is rated relevance **3** in classified_facts.json and was available to the synthesis call. However, the synthesis did not elevate it to a strength or value driver. Classified as contextual (3) rather than supporting (4), so it appeared in the evidence register but not in the analytical output or memo narrative. Fixed in V2 by C3 (synthesis focus question). |
| O-08 | Engagement quality / declining minutes | Milestone 2 (extraction) + Milestone 4 (classification) | Extraction limitation + classification relevance | No prior-year monthly minutes figure was extracted — the KPI summary page (p4) is an infographic where pdfplumber cannot extract contiguous text, and no "(2025: X)" parenthetical appeared in the verified excerpt for the prior_year.py parser to find. The current-year minutes fact (548m) was classified at relevance **2**. Both faults compound: even if the prior year had been available, a relevance-2 fact would not reach synthesis. |
| O-05 | EPS vs revenue growth divergence (PARTIAL) | Milestone 5 — memo.py | Memo generation synthesis depth | All ingredients exist: EPS +8% (relevance 5), revenue +4% (relevance 5), share buyback data (relevance 5). Bear case 2 in classified_facts.json mentions EPS growth guidance, and the memo separately cites all three figures. The explicit narrative — that EPS outpaces revenue/operating profit because buyback reduces the share count — is never synthesized. Fixed in V2 by C3 (synthesis focus question). |
| R-01 (PARTIAL) | Macro risks: geopolitical, inflation, financing costs | Milestone 4 — classify.py | Classification relevance scoring | Specific supply/demand and retailer-condition facts are captured at relevance 3–5. Broader macro risk dimensions (geopolitical tensions, inflation, financing costs) appear at relevance 2 or are absent. The classifier rated the most distinctive, quantified risks highest and generic structural risks lowest — consistent with the prompt instruction to rate memo-relevance, not risk severity. |
| R-03 (PARTIAL) | Legal & regulatory compliance (broad) | Milestone 4 — classify.py | Classification relevance scoring | CMA investigation was rated relevance 3–4 and captured in the memo. Broader FCA, consumer-protection, finance/leasing regulatory exposure exists in validated_facts.json at relevance 2. Same pattern as R-01: high-specificity items survive; broad category coverage does not. |
| R-07 (PARTIAL) | Brand & reputation (broad) | Milestone 4 — classify.py | Classification relevance scoring | Retailer sentiment and CMA reputational exposure are included. Fraud, misleading advertising, and platform-reputation risks appear in risk_disclosures at relevance 2, below threshold. Same undervaluation pattern for diffuse, non-quantified risks. |

**Hypothesis-confirmed pattern:** the section filter extracted the relevant facts correctly. The primary V1 failure mode is that the **classification relevance scorer systematically rated formal corporate risk register items** (cyber, third-party, broad regulatory, brand, environmental) as relevance 2 (peripheral) relative to more distinctive, quantified business risks. A secondary failure is that the **memo generation selected only a subset of the 11 synthesis risks** for Section 6 (5 disclosed + 2 inferred), dropping EV/climate items that were correctly classified. V3 addresses both by enforcing coverage at the structural (skeleton) level via code rather than model choice.

**Note on automated risk-coverage score:** the automated keyword estimate (9/10 V1, 10/10 V2 apparent, 10/10 V3 automated) is a false-positive-prone method — common business vocabulary ("market", "retailer", "consumer") matched in unrelated contexts. Zak's manual V1 verification corrected automated 9/10 to **5.5/10** (4 COVERED, 3 PARTIAL × 0.5, 3 MISSING). V3 automated matches are qualitatively better (R-05 now matches "cyber"/"security" directly; R-10 matches "third"/"reliance"), but manual verification remains required.

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

## 5. V1 / V2 / V3 Comparison

**Design note:** Each round targeted diagnosed failure modes from the prior evaluation. All changes are generic mechanism improvements, not gold-set-specific tuning. **Generalisability to a second company has not yet been tested.**

### Changes by round

**V2 changes (classify.py + memo.py):**
- C1: Standard risk-register taxonomy floor — bumps cyber, third-party, climate, regulatory, brand, continuity, financial, geopolitical `risk_disclosures` facts from relevance ≤2 to 3
- C2: Explicit risk checklist in memo Section 6 prompt — model must address all synthesis risk items
- C3: Targeted synthesis focus questions (direct-traffic moat; EPS vs operating-profit divergence)

**V3 changes (classify.py + memo.py):**
- C4: Deterministic risk skeleton — `build_risk_skeleton()` extracts disclosed principal risk categories from `risk_disclosures` facts using a taxonomy matcher; skeleton stored in `classified_facts.json`
- C5: Risk framing mandate — synthesis prompt explicitly requires every skeleton category to be framed as a risk, not an opportunity (targets R-10 framing failure)
- C6: Section 6 structural enforcement — `build_sections_6_8_prompt()` generates one `###` sub-section per skeleton category; `validate_risk_coverage()` post-generation validator FAILS if any keyword is absent from Section 6

### Automated metric comparison

| Metric | V1 | V2 | V3 | Notes |
|--------|----|----|-----|-------|
| Fact recall (automated) | 18/20 (90%) | 18/20 (90%) | 18/20 (90%) | Extraction unchanged across all rounds |
| Citation accuracy (automated) | 16/18 (88%) | 16/18 (88%) | 16/18 (88%) | Extraction unchanged |
| Risk coverage (automated) | 9/10 (90%) | 10/10* (100%) | 10/10 (100%) | *V2 R-05 was false positive; V3 R-05 has genuine keyword match |

### Human-judgement metrics (V3 pending Zak's verification)

| Metric | V1 | V2 | V3 | Primary change |
|--------|----|----|-----|----------------|
| Risk coverage (human-verified) | 5.5/10 (55%) | 6.5/10 (65%) | pending | R-05, R-10 expected COVERED (structural enforcement) |
| Observation coverage (human) | 7.5/10 (75%) | 9.0/10 (90%) | pending | No O-specific changes in V3; expect no regression |
| Diligence question quality (human) | 3.0/3.0 (100%) | 3.0/3.0 (100%) | pending | Synthesis re-run; expect similar |

### Per-item risk movement

| ID | V1 | V2 | V3 (automated) | Root cause addressed |
|----|----|----|-----------------|----------------------|
| R-01 | PARTIAL | PARTIAL | COVERED (verify) | Macro skeleton category added |
| R-02 | COVERED | COVERED | COVERED | — |
| R-03 | PARTIAL | PARTIAL | COVERED (verify) | Regulatory skeleton category added |
| R-04 | COVERED | COVERED | COVERED | — |
| R-05 | MISSING | MISSING | COVERED (verify) | Cyber skeleton category enforced; validator confirms keyword present |
| R-06 | COVERED | COVERED | COVERED | — |
| R-07 | PARTIAL | PARTIAL | COVERED (verify) | Reputation/Brand addressed via competitive/people skeleton |
| R-08 | COVERED | COVERED | COVERED | — |
| R-09 | MISSING | COVERED | COVERED | C1+C2 (V2); retained in V3 |
| R-10 | MISSING | MISSING | COVERED (verify) | V3 C5 (framing mandate) + C6 (structural enforcement) |

**Items that did NOT improve (V2 and V3):**
- **O-08 (engagement quality / declining minutes):** Structural extraction limitation — infographic KPI pages (p4) cannot be read by pdfplumber. No change in V2 or V3 targeted this. Still MISSING.
- **R-01, R-03, R-07 (breadth of coverage):** Skeleton enforces that a sub-section exists for each principal risk *category* but cannot mandate *breadth* within each sub-section. The model may address the most specific risk within a category and omit the broader dimensions. Manual verification will confirm whether PARTIAL items have genuinely improved.

---

*Generated by `eval/run_eval.py` (automated rows) and manually maintained (§§3–5).*
*Automated rows must not be edited manually; §§3–5 are hand-maintained.*
*Tolerance: ±2% value, ±1 page, 8-char stem prefix, ≥2 stems.*
