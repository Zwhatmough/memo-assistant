# V2 Scoring Addendum — Manual Verdicts Required
**For:** Zak Whatmough | **V2 memo:** `output/v2/memo.md` | **Date:** 17 July 2026

Manual scoring sheet for the V2 memo. Item texts below are quoted from the frozen
`eval/gold_set.json`; V1 verdicts carried over verbatim from `eval/scoring_sheet.md`.
(This file was regenerated after the first version drifted from the gold set texts.)

Three things to do:
1. Open `output/v2/memo.md` alongside this sheet.
2. Fill in each V2 verdict (COVERED / PARTIAL / MISSING).
3. Transfer final human-verified scores to `eval/results.md` §5.

Score each item: COVERED (1.0), PARTIAL (0.5), MISSING (0.0).

---

## Part A — Observation Coverage (O-01 to O-10)

**V2 targeted O-05 and O-07** via Change 3 (synthesis focus questions). Check those two first; the rest should be unchanged from V1 but confirm nothing regressed.

| ID | Gold observation (from frozen gold set) | V1 verdict | V2 expected | V2 actual | Notes |
|----|----------------------------------------|------------|-------------|-----------|-------|
| O-01 | ARPR growth is masking pressure in the retailer base: ARPR rose 5% to £2,995 while retailer forecourts declined… | COVERED | no change | COVERED | Value Driver 1 (ARPR core monetisation engine despite flat-to-declining forecourts); Bear Case 2 (ARPR gains offset volume softness). |
| O-02 | The Deal Builder rollout exposed execution risk in digital retailing: management met retailer resistance to the speed and nature of the rollout… | COVERED | no change | COVERED | Material Risks (dissatisfaction with speed/nature of rollout); Inferred Risks (recurring pushback as execution pattern); DQ2 (churn/reactivation/remediation evidence). |
| O-03 | Auto Trader is evolving from a listings marketplace into embedded infrastructure: technology and data-service calls rose from 91m to 155m per month… | COVERED | no change | COVERED | Value Driver 5 (API-based expansion to finance/insurance/manufacturer partners; proprietary data; 220+ integrations). |
| O-04 | The accelerated buyback creates a more leveraged equity story: moved from net cash to net debt, intends to lever to c.1.0x to fund returns… | COVERED | no change | COVERED | Material Risks (£500m FY2027 buyback, rising leverage); DQ3 (management's leverage ceiling before moderating returns). |
| O-05 | **EPS growth increasingly reflects capital structure as well as operating growth: revenue and operating profit rose c.4% while basic EPS rose 8%, largely buyback-driven** | PARTIAL | **COVERED** (C3) | **COVERED** | Clear improvement from V1. Material Risks: EPS guidance "increasingly supported by capital-allocation mechanics rather than core business acceleration"; Bear Case 1 explicitly names share-count reduction; DQ1 asks to separate buyback-driven from organic EPS growth. |
| O-06 | AI is both a product opportunity and a distribution threat: proprietary data advantage vs. generative AI assistants as a new acquisition layer… | COVERED | no change | COVERED | Business Overview (Co-Driver, Buying Signals, Deal Builder); Material Risks (LLM discovery, agentic-AI disintermediation); Bear Case 4; DQ4. |
| O-07 | **Direct traffic is a major competitive advantage: over 80% of visits arrive direct via app, URL or branded search, reducing acquisition dependence…** | MISSING | **COVERED** (C3) | **COVERED** | Clear improvement from V1. Exec Summary (low-cost direct-traffic acquisition in thesis); Value Driver 3 (80%+ direct, ~4% paid, margin support); Strength 2 (structurally efficient acquisition vs paid-search competitors); Bull Case 1. |
| O-08 | Engagement quality deserves more attention than visit growth: visits edged up to 81.7m while total monthly minutes declined 557m → 548m… | MISSING | MISSING (no fix) | MISSING | Still missing — visits/minutes divergence not analysed. Known structural extraction limitation (infographic page); not targeted in V2. |
| O-09 | Employee engagement is a potentially material execution warning: employees proud to work at Auto Trader fell from 91% to 72%… | COVERED | no change | COVERED | Material Risks (91% → 72%); Bear Case 3 (links engagement and Deal Builder difficulties to execution risk); DQ7. |
| O-10 | The marketplace position gives optionality beyond advertising — audience, proprietary data, retailer integrations, finance connections… | COVERED | no change | COVERED | Value Drivers 2 and 5 (digital retailing; data/technology services); Business Overview (AI product suite, platform strategy). |

**Part A V2 summary:** 9 COVERED, 0 PARTIAL, 1 MISSING — weighted 9.0/10 (90%). V1: 7.5/10 (75%). Improvement: +15pp.

---

## Part B — Risk Coverage (R-01 to R-10)

**V2 Changes 1 and 2 targeted this section**: classifier floor for risk-register categories + Section 6 must address all 11 synthesis risks. Biggest expected movers: R-09 and R-10 (MISSING → COVERED). Known failure: R-05 cyber is expected to remain MISSING — the synthesis model did not generate a cyber risk item even after the taxonomy floor. Verify rather than assume.

| ID | Gold risk (from frozen gold set) | V1 verdict | V2 expected | V2 actual | Notes |
|----|----------------------------------|------------|-------------|-----------|-------|
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply disruption and higher financing costs… | PARTIAL | possibly improved | PARTIAL | Covers retailer costs, interest rates, supply/demand pressure, structural supply constraints — but not wars/geopolitics, general inflation, international supply-chain disruption or wider consumer-financing consequences. Evidence register contains a global macro item; Section 6 does not synthesise it fully. |
| R-02 | Automotive economy and market environment: vehicle supply/demand, retailer costs, interest rates… | COVERED | no change | COVERED | Retailer profitability pressure, costs/rates, supply-demand changes, declining forecourts, structural used-car shortages, advertising-demand pressure. |
| R-03 | Legal and regulatory compliance: FCA, consumer-protection, privacy and competition exposure beyond the CMA case… | PARTIAL | possibly improved | PARTIAL | CMA investigation, DMCC Act and consumer protection covered; FCA/finance/leasing, privacy and broader regulated-transaction exposure still not analysed. |
| R-04 | Competition: large technology companies, social platforms and AI agents could disintermediate the marketplace… | COVERED | no change | COVERED | Amazon Autos, conversational AI, agentic AI, disintermediation, erosion of position between buyers and retailers. |
| R-05 | IT systems and cyber security: cyberattack, data breach or prolonged platform interruption… | MISSING | **likely still MISSING** | MISSING | Confirmed still missing. Cyber evidence exists in the register (E-146, E-150) but did not reach Section 6 synthesis. Honest known V2 failure. |
| R-06 | Employees: attracting, retaining and motivating specialist product/tech/data/commercial people… | COVERED | no change | COVERED | Engagement decline 91% → 72%, restructuring/office-policy concerns, effects on product quality and execution. More engagement-focused than recruitment/retention, but core theme present. |
| R-07 | Brand and reputation: negative publicity, fraud, misleading advertisements, customer trust… | PARTIAL | possibly improved | PARTIAL | Retailer dissatisfaction and CMA-related reputational exposure present; fraud, misleading ads, platform abuse, security-incident trust damage still absent. |
| R-08 | Failure to innovate continuously and responsibly: losing relevance if slow to adapt to AI and digital retailing… | COVERED | no change | COVERED | Agentic AI, conversational interfaces, Amazon Autos, need to deepen AI/digital-retailing products, recurring Deal Builder execution issues. |
| R-09 | Climate change: ICE-to-EV transition, changing policy, extreme weather, environmental obligations… | MISSING | **COVERED** (C1+C2) | **COVERED** | Clear improvement from V1. GHG +55% to 144.1kt with ESG cost/reputation exposure; EV policy uncertainty including proposed pay-per-mile EV tax; risk that policy changes weaken EV adoption. |
| R-10 | Reliance on third parties and partners: failure of a critical cloud, technology, data or finance partner… | MISSING | **COVERED** (C1+C2) | MISSING | Did NOT improve despite expectation. 220+ partners and API integrations appear only as a monetisation opportunity; no analysis of critical cloud/tech/data/finance partner failure or outage. Underlying risk evidence (E-149) did not reach Section 6. Framing failure, not extraction failure. |

**Part B V2 summary:** 5 COVERED, 3 PARTIAL, 2 MISSING — weighted 6.5/10 (65%). V1: 5.5/10 (55%). Improvement: +10pp. Key notes: R-09 MISSING → COVERED; R-05 remains MISSING as expected; R-10 expected to improve but did not.

---

## Part C — Diligence Questions (only if changed)

V2 re-ran synthesis, so the diligence questions may differ from V1's seven. If the V2 questions are substantively the same, carry over the V1 rating (7/7 at 3.0). If any are new or changed, rate those on the same 1–3 scale.

V2 generated seven revised questions; all rated independently rather than carried forward.

| # | V2 question (abbreviated) | Same as V1? | Rating |
|---|---------------------------|-------------|--------|
| 1 | What proportion of FY2027's guided high-single-digit EPS growth derives from buyback-driven share count reduction vs organic operating profit growth? | Revised | 3 — financially sharp, addresses the operating-vs-per-share divergence directly |
| 2 | What is the retailer churn and reactivation rate specifically attributable to Deal Builder dissatisfaction? | Revised | 3 — seeks quantifiable evidence linking the rollout problem to revenue risk |
| 3 | What is management's leverage ceiling before capital-return pace would be moderated? | Revised | 3 — tests buyback sustainability under downside conditions |
| 4 | How sustainable is the low-cost direct-traffic acquisition advantage if AI increasingly mediates car search and discovery? | Revised | 3 — connects a current advantage to an emerging distribution risk |
| 5 | What are the anticipated terms and competitive impact of Amazon Autos' UK launch? | Revised | 3 — specific to an identifiable competitive development |
| 6 | What is the expected trajectory and cost impact of the CMA investigation, and could findings affect the trust proposition? | Revised | 3 — connects regulatory outcome to financial exposure and marketplace credibility |
| 7 | What actions are underway to reverse employee engagement decline, and has it contributed to Deal Builder problems? | Revised | 3 — links an internal indicator to a visible execution issue |

**Part C V2 summary:** 7/7 rated 3 (average 3.0/3.0, 100%). V1: 7/7 at 3.0. No regression.

---

## Final V2 human-verified scores (for results.md §5 and README)

| Metric | V1 | V2 | Change |
|--------|----|----|--------|
| Observation coverage | 7.5/10 (75%) | 9.0/10 (90%) | +15pp |
| Risk coverage | 5.5/10 (55%) | 6.5/10 (65%) | +10pp |
| Diligence question quality | 3.0/3.0 (100%) | 3.0/3.0 (100%) | no regression |

**V2 improvements confirmed:** EPS-vs-operating-growth mechanism explicit; direct traffic analysed as a low-cost acquisition/margin advantage; climate/EV risk genuinely included; question quality sustained; capital-allocation analysis more precise.

**Remaining V2 gaps (carried to limitations):** engagement-depth divergence (O-08, structural extraction limit); cyber/IT resilience (R-05 — extracted but never reached synthesis); third-party reliance framed only as opportunity (R-10 — framing failure); macro coverage incomplete (R-01); regulatory coverage CMA-centric (R-03); brand/reputation narrower than the principal-risk definition (R-07).

## Assessor sign-off

**V2 verdicts by:** Zak Whatmough  **Date:** 17 July 2026

**LOCKED V2 RESULT.** Do not regenerate or modify V2 outputs after this scoring.

*Reminder: score V2 against the same frozen gold set. Do not adjust V2 outputs after scoring — these results are then locked alongside V1 in results.md §5.*
