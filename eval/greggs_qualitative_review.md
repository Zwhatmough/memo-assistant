# Greggs memo — qualitative analyst review (generalisation test)

**Reviewer:** Zak Whatmough | **Date:** 17 July 2026 | **Subject:** `output/greggs/memo.md`

The Greggs run had no gold set: the quantitative generalisation result is the code-verified
citation rate (249/252, 98%) and zero validation errors; this review is the qualitative half —
an analyst read of whether the memo is credible investment work.

## Ratings

| Dimension | Score |
|-----------|-------|
| Financial accuracy | 9.5/10 |
| Business understanding | 9/10 |
| Investment usefulness | 8.5/10 |
| Professional polish | 8/10 |
| **Overall** | **8.8–9.0/10** |

Overall verdict: "beyond an AI summary — it reads like a junior analyst's first draft that a
senior analyst would edit before an investment committee."

## What worked (section by section)

- **Executive summary:** better than the Auto Trader equivalent — states what Greggs is, how it
  makes money, what happened this year, the thesis, and the principal concern ("multi-year margin
  and ROCE compression") inside a minute's read. Genuine analysis rather than description.
- **Business overview:** explains the vertically integrated model, delivery, franchises,
  Tesco/Iceland partnerships, app, evening trade, digital — rather than rewriting the report.
  The "53% of new openings without an existing Greggs within a mile" point is an investment
  insight most readers would miss.
- **Financial section:** a proper narrative walk (revenue → margins → cash → capex → ROCE →
  dividend → 2026 guidance), not a number dump.
- **Value drivers:** strongest section — white space, evening trade, delivery, Derby/Kettering
  capacity, Tesco partnership, app. Genuinely Greggs' growth engines.
- **Risks:** adapted to Greggs rather than forcing Auto Trader's risk profile. Inflation, supplier
  dependence, cyber (justified — Greggs' own report discusses it extensively), brand (one food
  scare is a huge issue for this business), macro/consumer confidence: all correct calls.
- **GLP-1 observation:** correctly labelled as inference ("it appears…") — good analyst discipline.
- **Bull/bear cases and diligence questions:** the reviewer would ask almost every question
  (ROCE, cyber, capex, GLP-1).
- **Biggest positive:** the memo feels like *Greggs*, not "Annual Report Template #27" —
  specificity of drivers, risks and questions is the hardest thing to achieve and it landed.

## Improvements identified

1. **Skeleton duplication (defect):** "Financial" and "Financial and market risk" sub-sections
   overlap and should be merged — a risk-skeleton dedup issue.
2. **Operational risk breadth:** should include execution of the 3,500-shop rollout, Derby/
   Kettering delays, and rollout complexity — bigger Greggs risks than those listed.
3. **Commodity costs:** wheat, dairy, meat, energy are implied but should be explicit.
4. **Employment cost inflation:** National Insurance, minimum wage — deserves more prominence;
   consider combining with commodities as "Cost inflation".
5. **Reporting → interpretation:** the memo still sometimes reads "Evidence A, Evidence B" rather
   than "here is why this changes my investment view" (e.g. delivery at 6.8% of company-managed
   sales should be framed as headroom-if-penetration-rises, not just stated).
6. **Missing "Investment Verdict" section:** a closing conviction view (high/medium/low, positives,
   concerns, and a synthesis paragraph). The reviewer's own example: "Greggs appears to be
   sacrificing short-term returns to build supply-chain capacity capable of supporting a
   substantially larger estate. The investment question is therefore not whether 2026 earnings
   recover, but whether the current investment cycle ultimately delivers materially higher
   returns beyond 2027."
7. **Bear case addition:** "management is investing ahead of demand" — the real ROCE story.

## Disposition

Item 1 is a defect (fix before go-live). Items 2–7 are product-evolution directions — they
describe the gap between a well-organised evidence draft and opinionated equity research, which
is by design the human reviewer's contribution in V1. Recorded on the V2 roadmap: a synthesis
stage that converts facts into explicit investment interpretation, and an optional
Investment Verdict section (would require relaxing the no-recommendation design constraint —
a deliberate product decision to revisit, not an oversight).
