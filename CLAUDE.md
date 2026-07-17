# Project: Evidence-Grounded AI Investment Memo Assistant

## Before any work

Read `DESIGN.md` in full. It is the agreed project design and is the source of truth for scope, architecture, workflow, evaluation and milestones. Do not deviate from it without discussing the change with Zak first and recording it in the DESIGN.md decision log.

## Current status

**Milestone 1** — Complete. pdfplumber spike confirmed `extract_text()` works cleanly on all financial statements; `extract_tables()` fails (no borders). Decision recorded in DESIGN.md decision log.

**Milestone 2** — Complete. Gold set frozen (50 items). Schemas, LLM wrapper, and extraction pipeline built. Citation validator (`validate.py`) implemented with two-tier matching and auto-correction. Validation rate improved to 249/254 (98%) after loosening fragment matching (4-word runs, punctuation-stripped second pass). 5 unverifiable remain: all infographic KPI boxes (model-assembled summaries, not verbatim text). Failure analysis recorded in DESIGN.md.

**Milestone 3** — Complete. `finance.py` pure deterministic functions over `output/validated_facts.json`. 12 cross-checks, all passing. 5 derived metrics + 9 growth rate metrics (all formerly blocked). `prior_year.py` deterministic parser extracts 38 prior-year facts from verified excerpts — no API calls. 63 pytest unit tests total (36 finance + 27 prior_year). Missing-data catalogue: only FCF and EPS growth still blocked. Output: `output/financials.json`, `output/prior_year_facts.json`. See BUILD_LOG.md for findings.

**Milestone 4** — Complete. `classify.py` uses `claude-sonnet-5` over `validated_facts.json` + `financials.json` (never raw documents). Two-stage pipeline: (1) per-fact classification in batches of 80 (relevance 1–5 + memo section), (2) analytical synthesis over high-relevance facts. Every analytic item cites fact_ids or is flagged inference=True. Actual cost: $0.699. Output: `output/classified_facts.json`. Schema: `schemas/classify.py`.

**Milestone 5** — Complete. `memo.py` generates the ten-section investment memo using only `classified_facts.json` + `financials.json` (never raw documents). Evidence register pre-built (E-001–E-161) from all relevance ≥ 3 facts. Two-call generation strategy (sections 1–5, then 6–8) using `claude-sonnet-5` plain text; sections 9 (evidence table) and 10 (limitations) auto-generated deterministically. Post-generation validator checks every [E-NNN] reference resolves and every financial number matches a permitted source value within 2% tolerance. Actual cost: $0.137. Output: `output/memo.md`, `output/evidence_register.json`. Validation: 0 reference errors, 0 number errors.

**Milestone 6 (Evaluation)** — Complete (automated portion). `eval/run_eval.py` scores the pipeline against the frozen `eval/gold_set.json`. Automated metrics: fact recall (18/20, 90%), citation accuracy (16/18, 88%), risk coverage estimate (9/10 automated — requires manual verification). Human-judgement scoring sheet generated at `eval/scoring_sheet.md` (Parts A–C) for Zak to complete: observation coverage (O-01..O-10), diligence question quality (pipeline questions rated 1–3), and risk coverage verification. `eval/results.md` has per-item detail and a placeholder for manual metric results. No prompt tuning against gold set.

**Milestone 6 (Polish)** — Complete. `app.py`: single-file Streamlit review app (no database). Two tabs — Memo & Evidence (3:2 column split; memo with bold [E-NNN] references; selectbox evidence panel showing claim, doc/page/section/category/relevance/status, verified excerpt) and Facts Browser (multiselect filters by memo section, relevance, and citation status; expandable fact cards). `streamlit` added to `requirements.txt`. `README.md` written: problem, intended user, system design, AI-vs-deterministic split, cost engineering story, evaluation methodology, limitations, go-live checklist. Mermaid architecture diagram included.

**Milestone 6 (Evaluation) — V1 LOCKED.** Manual scoring by Zak (17 Jul 2026) complete. V1 results: fact recall 18/20 (90%), citation accuracy 16/18 (88%), risk coverage 5.5/10 (55% human-verified, overrides automated 9/10), observation coverage 7.5/10 (75%), diligence question quality 7/7 at 3.0/3.0 (100%). `eval/results.md` updated with manual scores and full failure analysis. V1 outputs (`output/memo.md`, `output/evidence_register.json`) must not be altered or regenerated.

**V2 improvement round — LOCKED (manual scoring complete, 17 Jul 2026).** Three changes in `classify.py` and `memo.py` (see BUILD_LOG.md). V2 outputs at `output/v2/`. Human-verified scores: risk coverage 6.5/10 (65%), observation coverage 9.0/10 (90%), diligence question quality 3.0/3.0 (100%). Key V2 improvements: O-05 and O-07 now COVERED (C3); R-09 climate/EV now COVERED (C2). Remaining gaps: R-05 cyber (synthesis did not generate a cyber item even after taxonomy floor — framing still absent); R-10 third-party (framing failure — facts described as opportunity not risk); O-08 engagement quality (structural extraction limitation). Full detail: `eval/v2_scoring_addendum.md`, `eval/results.md §5`.

**V3 improvement round — LOCKED (manual scoring complete, 17 Jul 2026).** Structural Section 6 enforcement: `build_risk_skeleton()` in `classify.py` derives disclosed risk categories deterministically from `risk_disclosures` facts; stored in `classified_facts.json`. Synthesis prompt updated with `RISK COVERAGE MANDATE` (explicit risk framing required per category). `memo.py` generates one `###` sub-section per skeleton category; `validate_risk_coverage()` post-generation validator fails if any skeleton keyword absent from Section 6. V3 outputs at `output/v3/`. Human-verified scores: risk coverage 8.0/10 (80%), observation coverage 9.0/10 (90%, carried from V2), diligence question quality 3.0/3.0 (100%, carried from V2). Key V3 movements: R-05 MISSING→COVERED (genuine cyber analysis); R-10 MISSING→PARTIAL (framing mandate produced explicit dependency risk); R-01 PARTIAL→COVERED. R-09 regression: COVERED→PARTIAL (structural sub-section narrower than V2's synthesis-driven narrative — skeleton guarantees presence, not breadth). Evaluation closed at V3; generalisation to Greggs is the next step. Full detail: `eval/v3_scoring_addendum.md`, `eval/results.md §5`.

**Generalisation refactor — complete.** `section_filter.py` (new): generic heading-taxonomy matcher using `config.yaml` section types with `heading_variants` and `fallback_pages`; replaces hard-coded page ranges in `extract.py`. `config.yaml` (new): Auto Trader company configuration. `finance.py`: cross-checks split into `UNIVERSAL_CROSS_CHECKS` + `COMPANY_CROSS_CHECKS["at"]`; `run_all()` takes `company_id` parameter. Adding a second company (e.g. Greggs) requires only a new `config.yaml` and `COMPANY_CROSS_CHECKS["greggs"]` entry — no pipeline logic changes. Generalisation principle recorded in DESIGN.md decision log. pytest suite: 63 tests, 0 failures.

## Working method (non-negotiable)

- Work in small, understandable stages. For each stage: explain what and why, propose the simplest credible implementation, flag important decisions, implement a small component, test it, explain failures.
- Zak is an Economics and Finance graduate, not an experienced software engineer. He must be able to explain every component in an interview. Do not build anything he cannot reasonably explain — teach as you build.
- Ask Zak to review major product decisions before implementing them.
- No overengineering. No LangChain or agent frameworks. No vector database in V1. Plain Python modules, pydantic schemas, JSON artifacts between stages.
- AI reads and writes prose; code counts and checks. The model never does arithmetic. Every AI output is schema-validated; every memo citation and number is verified by code.
- The evaluation gold set (Milestone 2) is built manually and frozen before prompt tuning. Never tune against it, and never manipulate evaluation results — honest failure analysis is part of the portfolio value.

## Conventions

- Python 3.11+, `pdfplumber` for PDF extraction, `pydantic` v2 for schemas, Anthropic Claude API via a thin `llm.py` wrapper, `pytest` for deterministic modules.
- API key lives in `.env` (never committed). `.env.example` documents required variables.
- Source PDFs live in `documents/` (gitignored — they are public but large). Pipeline outputs go to `output/` (gitignored). Evaluation gold set and results live in `eval/` (committed).
- Commit at the end of each working session with a clear message; commit history should show the milestone progression.
