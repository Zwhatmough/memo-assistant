# Project: Evidence-Grounded AI Investment Memo Assistant

## Before any work

Read `DESIGN.md` in full. It is the agreed project design and is the source of truth for scope, architecture, workflow, evaluation and milestones. Do not deviate from it without discussing the change with Zak first and recording it in the DESIGN.md decision log.

## Current status

**Milestone 1** — Ingestion + extraction spike. Goal: test pdfplumber text and table extraction on the Auto Trader FY2026 annual report (in `documents/`), focusing on the financial statements pages, and retire or re-plan the table-extraction risk before building any pipeline code.

Update this section as milestones complete.

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
