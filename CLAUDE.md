# Project: Evidence-Grounded AI Investment Memo Assistant

## Before any work

Read `DESIGN.md` in full. It is the agreed project design and is the source of truth for scope, architecture, workflow, evaluation and milestones. Do not deviate from it without discussing the change with Zak first and recording it in the DESIGN.md decision log.

## Current status

**Milestone 1** — Complete. pdfplumber spike confirmed `extract_text()` works cleanly on all financial statements; `extract_tables()` fails (no borders). Decision recorded in DESIGN.md decision log.

**Milestone 2** — Complete. Gold set frozen (50 items). Schemas, LLM wrapper, and extraction pipeline built. Citation validator (`validate.py`) implemented with two-tier matching and auto-correction. Validation rate improved to 249/254 (98%) after loosening fragment matching (4-word runs, punctuation-stripped second pass). 5 unverifiable remain: all infographic KPI boxes (model-assembled summaries, not verbatim text). Failure analysis recorded in DESIGN.md.

**Milestone 3** — Complete. `finance.py` pure deterministic functions over `output/validated_facts.json`. 12 cross-checks, all passing. 5 derived metrics + 9 growth rate metrics (all formerly blocked). `prior_year.py` deterministic parser extracts 38 prior-year facts from verified excerpts — no API calls. 63 pytest unit tests total (36 finance + 27 prior_year). Missing-data catalogue: only FCF and EPS growth still blocked. Output: `output/financials.json`, `output/prior_year_facts.json`. See BUILD_LOG.md for findings.

**Milestone 4** — Complete. `classify.py` uses `claude-sonnet-5` over `validated_facts.json` + `financials.json` (never raw documents). Two-stage pipeline: (1) per-fact classification in batches of 80 (relevance 1–5 + memo section), (2) analytical synthesis over high-relevance facts. Every analytic item cites fact_ids or is flagged inference=True. Actual cost: $0.699. Output: `output/classified_facts.json`. Schema: `schemas/classify.py`.

**Milestone 5** — Memo generation. Use classified_facts.json + financials.json to draft the investment memo in structured sections.

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
