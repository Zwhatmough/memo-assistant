# Games Workshop memo — qualitative analyst review (third-company test)

**Reviewer:** Zak Whatmough | **Date:** 17 July 2026 | **Subject:** `output/gw/memo.md`

Third-company config-only generalisation test (one additive helper function in `finance.py`;
zero other code changes). Quantitative result: 145/145 facts verified by the pipeline validator
(121/145 under a stricter exact-prefix independent check), 0 reference errors, 0 number errors,
all 4 disclosed risk categories present, $0.82 total cost.

## Ratings

| Dimension | Score |
|-----------|-------|
| Business understanding | 9.7/10 |
| Financial analysis | 9.4/10 |
| Company-specific insight | 9.6/10 |
| Investment usefulness | 9.2/10 |
| Writing and structure | 9.2/10 |
| **Overall** | **9.4/10** — strongest memo of the three |

Verdict: "This no longer reads like an AI summary. It reads like a junior equity research
analyst's first draft that requires editorial refinement rather than factual reconstruction."

## What worked

- **Executive summary:** answers what the business is, why profits increased, the thesis, and
  the principal risk — correctly identifying that FY25's licensing surge may be difficult to
  repeat as the real investment story rather than just reporting revenue growth.
- **Business overview (strongest section):** explains the ecosystem — retail, trade, online,
  Black Library, licensing, Warhammer+, MyWarhammer, manufacturing, Factory 4 — giving a
  genuine mental model rather than a fact list.
- **Financials:** correctly separates Core from Licensing, recognising their materially
  different economics — where many junior analysts would report only total revenue.
- **Value drivers:** genuine earnings drivers (licensing, Amazon partnership, pricing power,
  store rollout, trade growth, digital engagement), not generic positives.
- **Risks:** company-specific — licensing dependence, IP protection, cyber, manufacturing
  concentration, operational capacity.
- **Analytical observations:** the observation that manufacturing concentration links multiple
  disclosed risks (operations, climate, IT, supply chain) is genuine synthesis.
- **Bull/bear and diligence questions:** focused on the real issues — licensing durability,
  Factory 4 execution, Amazon economics, manufacturing redundancy.

## Critical finding: an erroneous inference caught by human review

The memo's analytical observation suggesting EPS growth "may have been meaningfully supported
by share count reduction / buybacks" was flagged by the reviewer as doubtful (Games Workshop
historically returns capital through dividends, not buybacks) and then **verified against the
annual report as factually wrong**:

- p.23: "During the period no shares were purchased in the market for cancellation."
- p.103: the Board "has no current intention to exercise this authority" (market purchase of own shares).

Games Workshop repurchased zero shares in the period; EPS growth was driven by profit growth.
The claim was correctly labelled as inference by the pipeline, sounded plausible (the same
mechanism was genuinely true for Auto Trader), and passed every automated check — because
citation validation verifies quotes, not reasoning. It was caught by exactly the mechanism the
tool is designed around: **a human analyst with domain knowledge reviewing the draft.** This is
the clearest demonstration in the project of why the human-review design constraint exists, and
why inference labelling matters. The locked memo is unchanged; this review is the correction of
record.

## Areas to improve (V2 roadmap themes, consistent with the Greggs review)

1. **Decisiveness:** too many hedges ("may suggest", "appears to", "could indicate") — hedging
   should mark real uncertainty, not every conclusion.
2. **More investment judgement:** e.g. rather than reporting licensing growth, address whether
   FY25 represents peak licensing earnings and whether investors should normalise it.
3. **Explicit investment thinking (not valuation):** does Factory 4 imply management sees
   significant long-term demand? Is the market likely to overestimate licensing margin
   durability?

## Conclusion

"The pipeline is now producing something that could genuinely save analysts time. The next
stage is less about improving extraction accuracy and more about improving synthesis,
conviction and investment judgement."
