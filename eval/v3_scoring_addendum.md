# V3 Scoring Addendum — Risk Verdicts Required
**For:** Zak Whatmough | **V3 memo:** `output/v3/memo.md` | **Date:** 17 July 2026

V3 introduced structural enforcement: Section 6 now has one `###` sub-section per disclosed risk category. The validator confirmed all 8 skeleton categories are present. This addendum covers only Part B (Risk Coverage) — observation coverage and diligence question quality are unchanged from V2 (no O-specific changes, synthesis re-run with same structure).

Two things to do:
1. Open `output/v3/memo.md` Section 6 alongside this sheet.
2. Fill in each V3 verdict (COVERED / PARTIAL / MISSING).

Score each item: COVERED (1.0), PARTIAL (0.5), MISSING (0.0).

---

## V3 Risk Skeleton (8 disclosed categories)

The following categories were identified deterministically from the company's `risk_disclosures` facts and enforced structurally in Section 6. The validator confirmed all 8 keywords are present in the memo. Manual verification checks whether the *substance* is genuine risk analysis or merely incidental mention.

| # | Skeleton label | Keyword checked | Fact IDs |
|---|---------------|-----------------|----------|
| 1 | Climate change and environmental obligations | climate | 5 facts |
| 2 | People and talent | employee | 2 facts |
| 3 | Market | market | 2 facts |
| 4 | Macroeconomic and geopolitical risk | macro | 2 facts |
| 5 | Competitive | competitive | 2 facts |
| 6 | IT systems and cyber security | cyber | 2 facts |
| 7 | Legal and regulatory compliance | regulatory | 1 fact |
| 8 | Third-party and partner reliance | third | 1 fact |

---

## Part B — Risk Coverage (R-01 to R-10)

Key V3 expected changes vs V2:
- **R-05 (cyber/IT):** V2 MISSING because synthesis model didn't generate a cyber item even after taxonomy floor. V3 structural enforcement mandates a `### IT systems and cyber security` sub-section. Check: does Section 6 contain substantive cyber risk analysis, or just token mention?
- **R-10 (third-party reliance):** V2 MISSING due to framing failure (partners described as opportunity, not risk). V3 framing mandate + skeleton requires explicit risk framing under `### Third-party and partner reliance`. Check: is the failure-scenario of partner loss/outage addressed?
- **R-01, R-03, R-07 (PARTIAL in V2):** Skeleton adds `### Macroeconomic and geopolitical risk`, `### Legal and regulatory compliance`, no explicit brand sub-section (covered under `### Competitive` or `### Market`). Check breadth — do these now cover the full gold-set dimensions?

| ID | Gold risk (from frozen gold set) | V1 verdict | V2 verdict | V3 actual | Notes |
|----|----------------------------------|------------|------------|-----------|-------|
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply disruption and higher financing costs affecting the automotive market and consumer confidence | PARTIAL | PARTIAL | **COVERED** | Macroeconomic/geopolitical sub-section links global macro events and geopolitical instability to stock pipelines, affordability, consumers' ability to trade, revenue, engagement and market share; Market sub-section adds retailer costs and rates. Inflation and war not individually named but the combined analysis captures the core risk sufficiently. |
| R-02 | Automotive economy and market environment: vehicle supply/demand, retailer costs, interest rates, used-car volume, structural used-car supply constraints | COVERED | COVERED | COVERED | Market sub-section covers supply-demand changes, retailer costs, rates, profitability, advertising spend, declining forecourts, negative stock contribution to ARPR; structural supply constraints covered elsewhere. |
| R-03 | Legal and regulatory compliance: FCA, consumer-protection, privacy and competition exposure beyond the CMA case | PARTIAL | PARTIAL | PARTIAL | DMCC Act, consumer protection, CMA investigation and possible enforcement covered; FCA, finance/leasing regulation, privacy/data protection, broader online-transaction regulation and the range of penalties still absent. |
| R-04 | Competition: large technology companies, social platforms and AI agents could disintermediate the marketplace or take over the customer journey | COVERED | COVERED | COVERED | Agentic-AI disintermediation, consumers directed straight to listings, reduced need for paid prominence, Amazon Autos as well-capitalised entrant. |
| R-05 | IT systems and cyber security: cyberattack, data breach or prolonged platform interruption causing revenue loss and reputational damage | MISSING | MISSING | **COVERED** | Substantive analysis, not token mention: IT infrastructure dependence, cyber/business-continuity incidents, downtime, AI-enabled attacks, zero-day vulnerabilities, potential GDPR fines up to 4% of Group revenue. Clear improvement from V1 and V2. |
| R-06 | Employees: attracting, retaining and motivating specialist product/tech/data/commercial people; engagement decline risk | COVERED | COVERED | COVERED | People and talent sub-section: 91% → 72% engagement decline, restructuring pressure, retention risk, execution-capability damage; analytics connect organisational strain to customer-facing execution. |
| R-07 | Brand and reputation: negative publicity, fraud, misleading advertisements, customer trust and audience revenue dependency | PARTIAL | PARTIAL | PARTIAL | CMA/consumer-protection and retailer dissatisfaction present; fraud, misleading advertisements, platform abuse, negative publicity, buyer-trust dependency and reputational consequences of cyber incidents still not analysed. |
| R-08 | Failure to innovate continuously and responsibly: losing relevance if slow to adapt to AI and digital retailing | COVERED | COVERED | COVERED | No separate "failure to innovate" heading but substance present: agentic AI, Amazon Autos, need to scale Deal Builder/Co-Driver/Buying Signals, digital-retailing execution risk. |
| R-09 | Climate change: ICE-to-EV transition, changing policy, extreme weather, environmental obligations and GHG trajectory | MISSING | COVERED | **PARTIAL (regression)** | Climate sub-section covers 55% GHG increase, footprint and compliance obligations — but loses V2's ICE-to-EV transition, EV policy, pay-per-mile tax, extreme weather and consumer-adoption analysis. Partial regression from V2: structural enforcement guaranteed presence but narrowed analytical breadth. |
| R-10 | Reliance on third parties and partners: failure of a critical cloud, technology, data or finance partner causing outage or data loss | MISSING | MISSING | **PARTIAL** | Now explicitly framed as risk: reliance on integrated lenders, technology infrastructure, vehicle-data suppliers, finance and fulfilment partners; operational dependency outside Group control. Failure consequences (outage, data loss, product non-delivery, regulatory breach, service disruption, financial loss) still not described. Materially better than V2. |

**Part B V3 summary:** 6 COVERED, 4 PARTIAL, 0 MISSING — weighted 8.0/10 (80%). V1: 5.5/10 (55%). V2: 6.5/10 (65%). V2→V3: +15pp. V1→V3: +25pp. Completely missing risks: 3 (V1) → 2 (V2) → 0 (V3).

---

## Final V3 human-verified scores (for results.md §5 and README)

| Metric | V1 | V2 | V3 |
|--------|----|----|-----|
| Observation coverage | 75% | 90% | 90% (carried forward — no O-specific changes) |
| Risk coverage (human-verified) | 55% | 65% | **80%** |
| Diligence question quality | 100% | 100% | 100% (carried forward) |

**Key V3 improvements:** cyber/IT resilience MISSING → COVERED; third-party reliance MISSING → PARTIAL; macro/geopolitical now sufficiently covered; every gold risk now receives some substantive treatment; structural risk headings prevented extracted evidence being silently omitted.

**Remaining V3 gaps (final limitations):** legal/regulatory coverage remains CMA-centric; brand and reputation incomplete; climate coverage lost some of V2's EV-transition and policy analysis (partial regression — see R-09); third-party risk identifies dependency but not failure consequences; **structural skeleton guarantees category presence, not analytical breadth.**

**Decision: evaluation closed at V3.** Remaining gaps are analytical-breadth issues appropriate to human review (the tool's design intent), not structural defects. Further rounds would risk overfitting to gold set wording. V3 is the final Auto Trader result; generalisation validated separately on a second company.

---

## Assessor sign-off

**V3 risk verdicts by:** Zak Whatmough  **Date:** 17 July 2026

**LOCKED V3 RESULT.** Do not regenerate or modify V3 outputs after this scoring.
