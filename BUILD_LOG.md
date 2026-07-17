# Build log — problems found and fixed

A chronological record of real failures encountered while building this project, what caused them, and what changed as a result. Kept deliberately honest: the design principle is that failure analysis is part of the portfolio value.

## 14 Jul 2026 — Milestone 1: pdfplumber table extraction fails on financial statements

**Found:** `extract_tables()` returned one-column garbage with no labels and missing comparative-year columns on all four primary financial statements.
**Cause:** pdfplumber's table detection relies on ruled cell borders; Auto Trader's statements use whitespace alignment with no borders.
**Fix:** Use `extract_text()` only (which is clean on all statements, including the 8-column Changes in Equity) and let the extraction model parse tabular structure from text, with code validating every number afterwards. Recorded in DESIGN.md decision log; risk §10.1 retired.
**Lesson:** Testing the riskiest assumption first (a deliberate Milestone 1 choice) changed the design before any pipeline code existed.

## 14 Jul 2026 — Milestone 2: retired model string caused blanket 404s

**Found:** Every extraction API call returned 404.
**Cause:** `llm.py` defaulted to `claude-sonnet-4-20250514`, a model string retired between the model's training data and today. Not a key or billing problem, though it initially looked like one.
**Fix:** Updated to current model strings; later split models per stage (see next entry).
**Lesson:** Model identifiers are infrastructure that ages; pin them in one place (`llm.py`) so the fix is one line.

## 14 Jul 2026 — Milestone 2: first extraction run cost 10x the estimate

**Found:** First full extraction run burned $4.96 of a $5 credit balance in one pass, completing only 81 of 146 pages, and produced 1,522 facts (~19 per page) — mostly noise.
**Cause:** Three compounding design faults: (1) one API call per page across all 146 pages, including ~60 pages of governance/remuneration boilerplate an analyst would skim; (2) no materiality bar in the extraction prompt, so output tokens (5x the price of input) ballooned; (3) premium model (Sonnet) used for a mechanical extraction task.
**Fix:** Section filtering (extract only from strategic report, KPIs, financial review, principal risks, primary statements), multi-page batching per call, materiality target of 2–5 facts per page, extraction switched to `claude-haiku-4-5` (Sonnet reserved for judgement-heavy classification/memo stages), resumable runs so completed pages are never re-paid for, and a pre-run cost estimator that aborts above a threshold. Full-run cost dropped from ~$9 to well under $1.
**Lesson:** Token economics are a design constraint, not an afterthought. Output tokens dominate cost in extraction workloads.

## 14 Jul 2026 — Milestone 2: git index corruption

**Found:** `git status` failed with "unable to map index file".
**Cause:** Two processes (Claude Code and a second assistant session) writing to the repository concurrently.
**Fix:** Deleted `.git/index` and rebuilt with `git reset` (no work lost — working tree and commits were intact). Process change: one writer for code; the second session reads and advises only.
**Lesson:** Concurrent writers need coordination even in a one-person project.

## 14 Jul 2026 — Milestone 2: citation verification on the clean re-run (211/236)

**Found:** An independent script checked whether each extracted fact's excerpt actually appears on its cited page: 211 of 236 verified exactly; 25 failed.
**Cause:** Two failure modes. (1) Page drift in multi-page chunks: facts stamped with the chunk's first page rather than the excerpt's true page (a side effect of the cost-saving batching change — fixing one problem introduced another). (2) Non-verbatim excerpts: fragments joined with "…" or lightly paraphrased, which cannot be string-verified even when the underlying fact is correct.
**Fix (in progress):** Per-page markers embedded in chunk text so the model cites the true page; excerpts required to be single contiguous verbatim quotes; and `validate.py` added as a permanent pipeline stage — every excerpt is string-verified against its cited page after extraction, citations auto-corrected when the excerpt is found on a nearby page, unverifiable facts flagged and excluded from downstream stages.
**Lesson:** The project's core promise (every claim traceable to source) must be enforced by code, not assumed from prompts. ~89% prompt-level citation accuracy became a hard guarantee only when validation moved into the pipeline.

## 14 Jul 2026 — Milestone 2 (late): 34 unverifiable facts after first validation run

**Found:** validate.py flagged 34/254 facts (13%) unverifiable — excerpt not found on cited page or nearby. Manual check confirmed all 34 are believed correct; the excerpts just couldn't be string-matched.
**Cause:** Three structural categories: (1) infographic/KPI summary pages where pdfplumber extracts only figure labels and no surrounding prose; (2) two-column body text pages (e.g. CEO/Chairman statement) where pdfplumber interleaves both columns, breaking contiguous spans; (3) model-assembled excerpts joining fragments from different paragraphs.
**Fix:** Reduced `FRAGMENT_WORDS` from 6 to 4 and added a second matching pass with punctuation stripped from both sides. Rate improved from 220/254 (86%) to 249/254 (98%). 5 truly unverifiable remain — all infographic KPI boxes that don't exist as verbatim text in the PDF.
**Lesson:** Fragment window size is a hyperparameter of the matching algorithm, not a fixed correctness threshold. Diagnosis-first: running a diagnostic on a known false negative (Autorama revenue) showed column interleaving was the mechanism, which suggested reducing the window before trying more exotic solutions.

## 14 Jul 2026 — Milestone 3: what the cross-checks found in Auto Trader's numbers

All 12 cross-checks passed (0 failures, 0 warns). Key findings:

- **Revenue entity split** (585.3 + 39.0 = 624.3 ✓): The group is cleanly split into Core Autotrader (the digital marketplace, contributing 94%) and Autorama (used-car retail arm, contributing 6%).
- **Operating profit bridge** (408.0 − 13.3 + (−2.0) = 392.7 ✓): Sign conventions matter — Autorama's operating loss is stored as −2.0 and must be *added* (not subtracted) to the bridge. Central costs of £13.3m account for ~2.1pp of the 7pp gap between Core AT's 70% margin and the group's 63% margin. Autorama's loss accounts for only ~0.3pp.
- **PBT bridge** (392.7 − 3.9 = 388.8 ✓) and **PAT bridge** (388.8 − 94.9 = 293.9 ✓): Full P&L walks vertically.
- **EPS check** (293.9 / 860.2 × 100 = 34.17p ✓): Exact to 0.01p.
- **Net bank debt** (165.0 − 18.2 = 146.8 ✓): Uses the gross drawn facility amount, not the balance-sheet 'Borrowings' line (163.4m, which nets capitalised issuance fees).
- **ARPR × forecourts** (2995 × 13,942 × 12 = 501.1 ✓): The KPI data and the segment revenue are internally consistent to within rounding.
- **Cash conversion** (418.0 / 392.7 = 106.4%): Converting more than 100p per £1 of profit — typical for asset-light marketplaces.

**What the module could not compute (missing data):**
- Revenue, operating profit, and ARPR growth rates — no FY2025 comparatives extracted
- Autorama segment revenue growth — prior-year figure (£36.3m) is in the excerpt text but wasn't extracted as a separate fact
- Full free cash flow — capitalised software/intangible additions not in extracted facts (only PPE purchases: −£27.3m)

## 15 Jul 2026 — Milestone 3 extension: prior-year values from excerpt text

**Found:** Growth rate calculations for the 5 key metrics (group revenue, core revenue, operating profit, ARPR, Autorama) were blocked because FY2025 comparatives weren't extracted as separate facts. But they were hiding in plain sight inside verified excerpts as "(2025: £601.1m)" patterns.
**Cause:** The extraction model correctly captured the FY2026 headline value but left the prior-year parenthetical in the excerpt string rather than extracting it as a second fact.
**Fix:** `prior_year.py` — a deterministic regex parser that scans all verified excerpt strings for `(YYYY: VALUE)` patterns, inherits the parent fact's unit and citation, and applies sign inheritance for loss facts (e.g. "Autorama operating loss" parent is -2.0, so prior-year "£4.3m" → -4.3). 38 prior-year facts extracted from 249 verified facts.
**Lesson:** Verified excerpts are a rich secondary source for prior-year data. The verification step ("this excerpt appears verbatim on page X") doubles as provenance for any structured data embedded within the excerpt.

## 15 Jul 2026 — Milestone 4: first classification call returned empty tool block

**Found:** `call_llm` with 249 facts in one JSON blob returned a pydantic `ValidationError: classifications field required, input_value={}` — the model invoked the tool with an empty object.
**Cause:** The prompt was too long (249 facts × ~50 tokens = ~12,500 tokens of dense JSON). The model ran out of usable context for generating the schema-constrained response and returned an empty call rather than a partial one.
**Fix:** Batched classification to 80 facts per call (4 classification batches + 1 synthesis call). The compressed JSON format (no indentation) helps token efficiency within each batch; the schema is still enforced by tool use.
**Lesson:** Schema-constrained tool calls have an implicit output token budget. With 249 facts × ~20 tokens per classification = ~5,000 output tokens, the model needs headroom in a single call. Batching is the right fix: not just for cost, but for reliability.

## 15 Jul 2026 — Milestone 4: what the classification found

- **31 facts rated relevance 5** (headline): revenue, margins, ARPR, EPS, cash conversion, Autorama operating loss, key KPIs, D&B scale, Amazon threat, leverage.
- **69 facts rated relevance 4** (supporting): segment breakdown, operating profit bridge, shareholder returns, risk disclosures, strategic commentary.
- **61 facts rated relevance 3** (contextual): operating cost lines, employee metrics, stock volume data.
- **75 facts rated relevance 2** (peripheral): minor P&L lines, accounting details.
- **13 facts rated relevance 1** (excluded): governance notes, boilerplate.
- **161 facts passed to synthesis** (relevance ≥ 3).
- **Analytics produced**: 6 strengths, 11 risks (10 disclosed + 1 inferred — AI disintermediation), 6 value drivers, 4 bull/5 bear points, 7 diligence questions. 3 items flagged inference=True.
- **Actual cost**: $0.699 (vs $0.357 dry-run estimate — synthesis used more tokens than estimated for the analytical depth).

## 15 Jul 2026 — Milestone 5: two validation failures on first memo generation run

**Found:** Post-generation validator flagged 5 number errors: `75%`, `8,056`, and `£27.3m` could not be matched against permitted source values within 2% tolerance. All references resolved correctly (0 reference errors).
**Cause:** Two separate bugs in `build_permitted_values`. (1) Non-financial facts (`business_facts`, `risk_disclosures`, etc.) have no numeric `value` field — their label text contains legitimate numbers like "over 75% of minutes" or "8,056 vehicles", but the function only scraped `float(fact["value"])` from `financial_figures`, so those quantities were absent from the permitted set. (2) Cash outflows are stored as negative values (e.g. PPE purchases = −27.3) but the memo writes their magnitude as a positive number (£27.3m), so the tolerance check `abs(val − pv) ≤ max(|pv| × 2%, 0.5)` always failed because `abs(27.3 − (−27.3)) = 54.6 ≫ 0.55`.
**Fix:** (1) Added a pass that runs `_FINANCIAL_NUMBER_RE` over the `label` and related text fields of every registered fact and adds parsed numbers to permitted values. (2) Added `abs(v)` to permitted values whenever a financial fact is negative. Re-running validation against the existing memo.md (without new API calls) produced 0 reference errors and 0 number errors.
**Lesson:** A validator that misses legitimate numbers becomes noise, not a guard. The permitted-values set must cover every representation of a source figure that can legitimately appear in prose — both positive magnitudes of negative cash flows and numbers embedded in text-only (non-financial) facts.

## 15 Jul 2026 — Milestone 6 (evaluation): automated metrics from run_eval.py

First run of the evaluation harness against the frozen gold set. Automated scores:

- **Fact recall**: 18/20 (90%). 2 near-misses flagged for manual adjudication (F-12: £600m FY2027 return target; F-16: ARPR primary value £141 not extracted as standalone fact — £2,995 matches as secondary).
- **Citation accuracy**: 16/18 (88%). F-07 (EPS 34.17p) and F-15 (forecourts 13,942) cited on wrong pages.
- **Risk coverage (automated estimate)**: 9/10 by keyword-stem matching (≥2 of 8-char stems in Section 6). R-05 (IT/cyber) flagged. Automated score requires manual verification — common words produce false positives.

**Near-miss detail (F-12, F-16):** The pipeline extracted forward-guidance facts (£600m shareholder return target) and ARPR (£2,995) but not as the exact primary value the gold claim leads with. These facts are in the pipeline output; the value extraction ordering in the eval script picks a different lead number.

**Citation miss detail (F-07, F-15):** EPS appears across multiple pages; the pipeline cited the wrong one. Forecourts KPI: pipeline page vs gold page differ by >1.

**Risk coverage caveats added:** Keyword matching uses 8-char stem prefixes (handles morphological variants like 'disintermediate' → 'disintermediation') but is vulnerable to context-blind false positives (e.g., "consumer" matches in an AI-behavior context when the gold risk is about consumer demand). The scoring sheet (eval/scoring_sheet.md Part C) asks Zak to verify each automated COVERED result.

## 17 Jul 2026 — V2 improvement round: changes implemented, run blocked by API monthly limit

**Context:** V2 improvements were designed in direct response to V1 evaluation findings (failure analysis in `eval/results.md §3`). All three changes target diagnosed failure modes, not gold-set-specific symptoms. **Generalisability to a second company has not yet been tested** — this is recorded as a caveat in `eval/results.md` and should be assessed when a second company pipeline run is conducted.

**Changes implemented:**

1. **`classify.py` Change 1 — risk-register taxonomy floor**: Added `RISK_REGISTER_TAXONOMY` constant (9 standard categories drawn from ISO 31000, COSO ERM, TCFD frameworks — not from the gold set). Added `apply_risk_floor()` function: any `risk_disclosures` fact assigned to the `risks` section with relevance ≤2 that matches a taxonomy term is bumped to relevance 3. Called after Stage 1 classification, before synthesis. This targets R-05 (cyber, relevance 2→3) and R-10 (third-party, relevance 2→3); also expected to broaden R-01, R-03, R-07 partial coverage.

2. **`classify.py` Change 3 — targeted synthesis focus questions**: Two analytical questions added to `build_synthesis_prompt()` via an `ANALYTICAL FOCUS` block. Question 1 asks whether direct-traffic mix data constitutes a competitive moat (targets O-07). Question 2 asks the model to compare EPS growth to operating profit growth and identify the buyback mechanism if they diverge (targets O-05 partial). Both are framed as conditional ("if the facts support them") so the model does not hallucinate answers.

3. **`memo.py` Change 2 — explicit risk checklist for Section 6**: Added `_format_risks_checklist()` function and updated `build_sections_6_8_prompt()` to pass an explicit numbered list of all analytics risk items with a mandate: "Section 6 must address every one." This targets R-09 (climate/EV — items 8 and 9 in the V1 synthesis analytics were dropped during memo generation).

**Blocked:** `anthropic.BadRequestError: You have reached your specified API usage limits. You will regain access on 2026-08-01 at 00:00 UTC.` V2 run to resume from 1 August 2026. V1 outputs unchanged.

## 17 Jul 2026 — V2 run complete; section_filter.py + finance.py generalisation refactor

**V2 pipeline run results** (API limit cleared, run completed same session):

- **Classify** (`output/v2/classified_facts.json`): 249 facts → 4 batches of 80, then synthesis over 175 facts (rel ≥3). Risk-floor adjustment: 4 facts bumped to relevance 3 by taxonomy match (2 cyber, 1 third-party, 1 carbon). Actual cost: $0.7396. Relevance distribution unchanged from V1 except for the 4 floored facts.
- **Memo** (`output/v2/memo.md`): All 11 synthesis risks now appear in Section 6 (V1 had 5 of 11). Direct-traffic moat appears in exec summary, Section 4 (value drivers), and Section 5 (strengths). EPS-vs-operating-profit divergence now explicit in bear case with buyback mechanism identified. Actual cost: part of $0.7396 total.
- **Eval** (`python3 eval/run_eval.py`): Automated fact recall 18/20 (90%), citation accuracy 16/18 (88%), risk coverage automated 10/10 — but R-05 is a false positive (matched stems "platform" + "marketplace" from an EV policy sentence, not from any cyber/IT discussion). Adjusted automated = 9/10.

**What worked:**
- **C2 (explicit risk checklist) — fully effective**: All 11 synthesis risks now in Section 6. GHG +55% y/y and EV policy uncertainty (pay-per-mile tax, mixed government messaging) now explicitly addressed. This directly fixes R-09 (climate/EV = MISSING in V1).
- **C3 (synthesis focus questions) — fully effective**: Direct-traffic moat and EPS-buyback mechanism both appear in V2 memo. These were the two most specific analytical gaps flagged in Zak's V1 assessment. O-07 and O-05 expected to move from MISSING/PARTIAL to COVERED.

**What did not work:**
- **C1 (taxonomy floor) → R-05 (cyber)**: 2 cyber facts were successfully floored from relevance 2 to 3 and entered the synthesis call. However, the synthesis model did not produce a cyber/IT risk as one of its 11 items — so no cyber risk entry existed for the C2 checklist to mandate in Section 6. The floor targeted the right bottleneck (synthesis exclusion) but the synthesis model still deprioritised cyber. To fix: the synthesis prompt itself would need a cyber mandate, not just the memo-generation prompt.
- **C1 (taxonomy floor) → R-10 (third-party)**: Same pattern. Facts floored, entered synthesis, but no third-party synthesis item generated.
- **O-08 (engagement quality)**: No V2 change targeted this. Structural pdfplumber limitation on infographic pages (p4) — still MISSING.

**Automated risk-coverage false positive (known issue):** R-05 auto-shows COVERED in V2 because "platform" and "marketplace" appear in Section 6 in the context of the EV policy sentence ("...EV tax...platform..."). These are not cyber keywords. The adjusted V2 automated score is 9/10 (same as V1 signal). Zak must verify R-05 as MISSING in the manual scoring addendum.

**Section filter and finance.py generalisation refactor (same session):**

1. **`section_filter.py`** (new file): Generic heading-taxonomy matcher replaces the hard-coded `MEMO_SECTIONS` constant in `extract.py`. Uses case-insensitive substring match of the first 400 characters of each PDF page against `heading_variants` lists defined in `config.yaml`. Also detects the printed-page offset (scans first 20 pages for an isolated "1" in the page footer — typical UK AR front-matter convention). Falls back to `fallback_pages` per section if heading detection fails. Design note: exact substring match chosen deliberately (not fuzzy edit-distance) because UK annual report headings are formulaic and verbatim matching is reliable without added complexity.

2. **`config.yaml`** (new file): Company configuration for Auto Trader. Includes `section_taxonomy` block with 6 section types (`strategic_overview`, `strategy`, `kpis`, `financial_review`, `principal_risks`, `financial_statements`), each with `heading_variants`, `description`, `max_pages`, and `fallback_pages`. Adding a new company needs only a new `config.yaml`.

3. **`extract.py`** (modified): `MEMO_SECTIONS` renamed to `_AT_MEMO_SECTIONS_FALLBACK` and made truly a fallback. Added `_resolve_memo_sections()` which tries `config.yaml` + `section_filter.py` first; falls back to the AT-specific constant only if config absent or returns nothing.

4. **`finance.py`** (modified): Cross-check functions split into `UNIVERSAL_CROSS_CHECKS` (P&L walk, EPS, cash conversion, net bank debt, shareholder returns — applicable to any company) and `COMPANY_CROSS_CHECKS["at"]` (segment revenue splits, ARPR × forecourts reconciliation, AT-specific margin bridge — AT-specific). Similarly for derived metrics. `run_all()` now accepts `company_id="at"` and merges universal + company-specific lists. Adding Greggs or a third company needs only a new key in `COMPANY_CROSS_CHECKS` and `COMPANY_DERIVED_METRICS` with the relevant check functions.

**DESIGN.md generalisation principle recorded:** All company adaptations must be generic mechanisms — configurable or auto-detected, never hardcoded to a specific company — such that adding a new company requires only a `config.yaml` entry and a company-specific checks registry entry, with no changes to pipeline logic. Confirmed 17 Jul 2026.

**pytest suite: 63 tests, 0 failures.** All finance.py and prior_year.py tests pass after the refactor (function names unchanged; only the list constants and `run_all` signature changed).

## 17 Jul 2026 — Milestone 6 (Evaluation): manual scoring complete, V1 locked

**Found:** Human evaluation by Zak (17 July 2026) produced materially different risk-coverage scores from the automated keyword estimate. Automated: 9/10 (90%). Human-verified: 5.5/10 (55%). Three risks are MISSING (cyber/IT, climate/EV, third-party dependency) and three are PARTIAL (macro, legal/regulatory, brand/reputation). Observation coverage: 7.5/10 (75%). Diligence question quality: 7/7 at 3.0/3.0 (100%).

**Cause (diagnosed from pipeline artifacts):** Two compounding faults:

1. **Classification relevance undervaluation of standard AR risk register items (primary)**: Cyber/IT risk facts (p50, p54) are present in `validated_facts.json` but rated relevance **2** by `classify.py`, below the ≥3 threshold for synthesis. Third-party reliance facts are rated **1–2**. The classification prompt correctly asked for memo-relevance, but this caused the classifier to systematically rate distinctive, quantified risks higher and diffuse, formally-disclosed risks lower. Consistent pattern across R-05, R-10, R-01 (partial), R-03 (partial), R-07 (partial).

2. **Memo generation dropped synthesis risks (secondary)**: Climate/EV risk facts (EV government messaging, GHG +55%) *did* pass through classification to synthesis (risks 8 and 9 in classified_facts.json analytics). However, `memo.py` Section 6 included only 5 of 11 synthesis risks. The two-call generation strategy with no explicit instruction to include all synthesis risk items caused the model to drop EV/climate items.

**Automated risk-coverage keyword method is confirmed unreliable**: 8-char stem prefix matching on all content words ≥5 chars produces false positives from common business vocabulary ("market", "retailer", "consumer", "change"). The 9/10 automated estimate was wrong; manual verification corrected to 5.5/10. This method is retained in `eval/run_eval.py` as a directional signal only — the scoring sheet explicitly asks for manual verification of every COVERED result.

**V1 result locked.** No alterations to V1 outputs. V2 will produce separately labelled outputs scored against the same frozen gold set.

## 15 Jul 2026 — Milestone 6 (Polish): Streamlit app and README

No failures during this milestone. Key decisions:

- **`app.py`** — single-file Streamlit review app; `@st.cache_data` keeps all JSON loaded once per session; excerpt lookup built from `validated_facts.json` using the `{chunk_id}__{category}__{index}` key scheme that matches `classified_facts.json`'s `id` field. No database, no back-end. Explainable to a non-engineer.
- **README.md** — drafted following DESIGN.md portfolio spec: problem, intended user, system design with AI-vs-deterministic split, cost engineering story, evaluation methodology, limitations, go-live checklist.
- **Mermaid architecture diagram** — seven-stage pipeline with JSON artifacts shown as intermediate nodes.
- **Go-live checklist** — three sections: security (verify .env history, grep for API key), data (.gitignore coverage, gold set freeze date), example outputs worth committing (`memo.md` and `evidence_register.json` via `.gitignore` exceptions).

---

*Update this file whenever a real failure is found and fixed. Each entry: Found / Cause / Fix / Lesson.*
