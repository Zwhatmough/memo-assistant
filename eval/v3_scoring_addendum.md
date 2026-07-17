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
| R-01 | Macro risks: wars, geopolitical tensions, inflation, supply disruption and higher financing costs affecting the automotive market and consumer confidence | PARTIAL | PARTIAL | | |
| R-02 | Automotive economy and market environment: vehicle supply/demand, retailer costs, interest rates, used-car volume, structural used-car supply constraints | COVERED | COVERED | | |
| R-03 | Legal and regulatory compliance: FCA, consumer-protection, privacy and competition exposure beyond the CMA case | PARTIAL | PARTIAL | | |
| R-04 | Competition: large technology companies, social platforms and AI agents could disintermediate the marketplace or take over the customer journey | COVERED | COVERED | | |
| R-05 | IT systems and cyber security: cyberattack, data breach or prolonged platform interruption causing revenue loss and reputational damage | MISSING | MISSING | | **Primary V3 target** |
| R-06 | Employees: attracting, retaining and motivating specialist product/tech/data/commercial people; engagement decline risk | COVERED | COVERED | | |
| R-07 | Brand and reputation: negative publicity, fraud, misleading advertisements, customer trust and audience revenue dependency | PARTIAL | PARTIAL | | |
| R-08 | Failure to innovate continuously and responsibly: losing relevance if slow to adapt to AI and digital retailing | COVERED | COVERED | | |
| R-09 | Climate change: ICE-to-EV transition, changing policy, extreme weather, environmental obligations and GHG trajectory | MISSING | COVERED | | |
| R-10 | Reliance on third parties and partners: failure of a critical cloud, technology, data or finance partner causing outage or data loss | MISSING | MISSING | | **Primary V3 target** |

**Part B V3 summary:** ? COVERED, ? PARTIAL, ? MISSING — weighted ?/10 (?%). V1: 5.5/10. V2: 6.5/10.

---

## Final V3 risk score (for results.md §5)

| Metric | V1 | V2 | V3 | Change V2→V3 |
|--------|----|----|-----|--------------|
| Risk coverage (human-verified) | 5.5/10 (55%) | 6.5/10 (65%) | ?/10 | ? |

---

## Assessor sign-off

**V3 risk verdicts by:** _______________  **Date:** _______________

*Note: observation coverage and diligence question quality carry forward V2 verdicts (9.0/10 and 3.0/3.0) unless you notice material regression in `output/v3/memo.md` — if so, note here.*
