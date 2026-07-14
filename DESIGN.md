# Evidence-Grounded AI Investment Memo Assistant — Project Design Document

**Author:** Zak Whatmough · **Status:** v1.0 — awaiting review · **Date:** 14 July 2026

---

## 1. Problem statement

Early-stage investment review requires an analyst to read hundreds of pages of company documents to answer a small set of recurring questions: what the business does, how it makes money, how it is performing, what could go wrong, and what to investigate next. This is slow, and the bottleneck is search and organisation, not judgement.

LLMs can draft a memo in seconds, but a raw LLM draft is unusable for real work because claims are not traceable to source, numbers may be invented, and confidence is not distinguished from inference.

**The problem this project solves:** produce a structured first-draft investment memo from a small set of company documents where every material claim is linked to a specific source location, numbers are calculated by code rather than by the model, inference is clearly separated from documented fact, and the system's accuracy is measured rather than assumed.

The central question: *can AI accelerate early-stage investment research while keeping important claims traceable to source evidence?*

## 2. Intended user

An investment, private equity, corporate finance, credit or research analyst performing a first-pass review of a company. The tool prepares their work; it does not replace their judgement. It must never produce a buy/sell recommendation, invent financial data, or hide uncertainty.

## 3. Version 1 scope

**In scope:**

- One company (Auto Trader Group plc — see §5), 2–3 PDF documents
- A single end-to-end pipeline run from the command line: PDFs in → memo + evidence register out
- All ten memo sections from the brief (executive summary through limitations)
- An evidence register linking every material claim to document, page and excerpt
- Deterministic financial calculations (growth, margins, period movements)
- An evaluation harness with a manually built gold-standard set and honest error analysis

**Out of scope for V1** (explicitly deferred, not forgotten):

- Multiple companies, document comparison across companies
- Virtual data room scale (hundreds of documents)
- Streamlit/web interface (Milestone 6)
- Vector database / semantic retrieval (see §7 — not needed at this document volume)
- OCR of scanned documents, non-PDF formats
- Synthetic private-company pack (a strong V2 extension for the PE-diligence angle)

## 4. Inputs and outputs

**Inputs:** 2–3 PDFs placed in a `documents/` folder, plus a small `config.yaml` recording company name, ticker, fiscal year end, and document metadata (type, period covered).

**Outputs, per run:**

| File | Contents |
|---|---|
| `output/memo.md` | The ten-section structured memo, with inline evidence references like `[E-014]` |
| `output/evidence_register.json` | Every claim: text, source doc, page, excerpt, confidence, factual-vs-inferred flag |
| `output/facts.json` | Structured extracted facts (validated against schemas) |
| `output/financials.json` | Extracted financial figures plus code-calculated ratios, growth and movements, with assumptions |
| `output/run_log.json` | Model calls, token counts, timings, validation failures — for cost tracking and debugging |
| `eval/results.md` | Evaluation metrics and error analysis (produced by the eval harness, not every run) |

## 5. Recommended first company: Auto Trader Group plc

**Choice confirmed with Zak.** Rationale:

- **Relevance to target employers.** Auto Trader is a high-margin UK marketplace/platform business. A memo on a software-economics company speaks directly to the audiences you are targeting (Capsa AI, 9fin, Beauhurst, PE-tech, investment tech) in a way a grocer or airline does not.
- **Clean, rich disclosure.** Clear single-segment-dominant model, strong operating KPIs (retailer numbers, average revenue per retailer, stock levels), understandable financial statements, plus real complexity to extract (Autorama/Deal Builder, platform strategy, cyclical used-car market exposure).
- **Free, accessible documents.** Verified available at the investor results centre ([plc.autotrader.co.uk/investors/results-centre](https://plc.autotrader.co.uk/investors/results-centre/)), including the Annual Report for the year ended 31 March 2026.
- **Shows range.** A new company demonstrates the pipeline generalises beyond businesses you have already modelled; Tesco/easyJet remain available as a second test case later.

**Trade-off accepted:** with Tesco you could build the evaluation gold set faster from existing knowledge. Mitigation: Auto Trader's annual report is shorter and simpler than Tesco's, so building the gold set is still a bounded task (~1 day).

**V1 document set (2–3 documents):**

1. Annual Report and Financial Statements FY2026 (year ended 31 March 2026) — primary source
2. FY2026 full-year results analyst presentation — secondary source, different format (slides), which usefully stress-tests extraction
3. Optional third: half-year FY26 results presentation, to test period handling and cross-document consistency

## 6. Proposed workflow

Seven stages, each producing a validated artifact that the next stage consumes. The pipeline is a straight line; no stage reads raw PDFs except Stage 2, and Stage 6 (memo generation) may only cite the evidence register — it never sees raw documents.

```
PDFs ──▶ 1 INGEST ──▶ 2 EXTRACT & CHUNK ──▶ 3 FACT EXTRACTION ──▶ 4 FINANCIAL ANALYSIS
              │                │                    │                       │
         manifest.json    chunks.json          facts.json            financials.json
                                                    └──────────┬────────────┘
                                                               ▼
                                              5 CLASSIFICATION (strengths/risks/drivers/questions)
                                                               │
                                                        analysis.json
                                                               ▼
                                                   6 MEMO GENERATION ──▶ memo.md + evidence_register.json
                                                               ▼
                                                   7 REVIEW (human) ──▶ edits / flags / export
```

1. **Ingestion.** Read PDFs from `documents/`, record metadata from `config.yaml`, capture page count and structure. Output: `manifest.json`.
2. **Text extraction and chunking.** Extract text page-by-page (page number retained on every chunk — this is the foundation of citation accuracy). Chunk by document structure (headings/sections) rather than fixed token windows, keeping tables intact where possible. Tables extracted separately with a table-aware extractor. Output: `chunks.json`, each chunk carrying `{doc_id, pages, section, text, is_table}`.
3. **Fact extraction (AI).** Send chunks to Claude with strict JSON schemas (via tool use) for each fact category: business description, products, customers, segments, geography, financial figures, stated risks, strategic priorities, management commentary. Every fact must include the chunk ID it came from; facts failing schema validation are rejected and retried once, then logged. **Financial figures are extracted as raw reported numbers only — no derived values.** Output: `facts.json`.
4. **Financial analysis (code, no AI).** Pure Python over the extracted figures: growth rates, margins, period comparisons, material movement flags (threshold-based), cross-checks (e.g. revenue ≥ segment sum within tolerance; flag if not). Assumptions stored alongside every calculation. Output: `financials.json`.
5. **Analytical classification (AI, constrained).** Claude receives only `facts.json` + `financials.json` (not raw documents) and classifies evidence into strengths, risks (split: disclosed / inferred / needs-investigation), value drivers, bull and bear arguments, and prioritised diligence questions. Every item must reference the fact IDs supporting it; items with no supporting fact ID must be explicitly labelled `inference`. Output: `analysis.json`.
6. **Memo generation (AI, constrained).** Claude drafts the ten-section memo using only `analysis.json`, `financials.json` and the evidence register. Post-generation validation in code: every `[E-xxx]` reference must resolve; every number in the memo must match a value in `financials.json` or `facts.json` (string-match check on figures) — mismatches fail the run.
7. **Review (human).** V1: the analyst reads `memo.md` and inspects `evidence_register.json`. Milestone 6 adds a Streamlit view for claim-by-claim inspection and editing.

## 7. Recommended technical approach

Deliberately boring. Every component is explainable in one sentence.

| Component | Choice | Why |
|---|---|---|
| Language | Python 3.11+ | Your existing skill; universal in the target job market |
| PDF extraction | `pdfplumber` (text + tables); `PyMuPDF` fallback | pdfplumber's table extraction is the best free option for financial PDFs |
| Schemas/validation | `pydantic` v2 | Typed models for every artifact; validation failures are visible, not silent |
| LLM | Anthropic Claude API — Sonnet for extraction, with structured outputs via tool use | Confirmed choice; tool use gives schema-enforced JSON. Thin `llm.py` wrapper so provider could be swapped |
| Orchestration | Plain Python modules + a `run.py` CLI (argparse). Each stage runnable independently | No LangChain/agent framework — you must be able to explain every line |
| Storage | JSON files on disk between stages | Inspectable, diffable, no database to explain |
| Retrieval | **None in V1.** Chunks routed to extraction prompts by section type; long sections processed in batches | 2–3 documents fit through direct processing. A vector DB adds a component you'd have to defend without needing it. If V2 scales to data-room volume, add retrieval then — and you'll have a good story about why |
| Testing | `pytest` for the deterministic modules; eval harness for the AI stages | Different tools for different failure modes |
| Cost control | Run log tracks tokens; cache extraction outputs so downstream stages re-run without re-calling the API | Full pipeline run estimated well under £1; total project under ~£10 |

Repository shape: `ingest.py`, `chunk.py`, `extract.py`, `finance.py` (pure functions, unit-tested), `classify.py`, `memo.py`, `validate.py`, `llm.py`, `run.py`, plus `schemas/`, `prompts/`, `eval/`, `documents/`, `output/`.

## 8. Deterministic vs AI-driven

| Deterministic (code) | AI (Claude) |
|---|---|
| All arithmetic: growth, margins, ratios, movements | Reading and interpreting document text |
| Period alignment and comparison | Classifying text into fact categories |
| Cross-checks and consistency flags | Summarisation for the memo narrative |
| Schema validation of every AI output | Identifying risks and strengths from evidence |
| Citation resolution (does E-014 exist and match?) | Generating diligence questions |
| Number-match validation of memo vs source data | Connecting evidence into bull/bear arguments |
| Duplicate detection, sorting, filtering | Classifying confidence and factual-vs-inferred |
| Cost/token logging | — |

Rule of thumb applied throughout: **AI reads and writes prose; code counts and checks.** The model never performs arithmetic, and code checks the model's citations and numbers after every AI stage.

## 9. Evaluation plan

The evaluation is a first-class deliverable, built in Milestone 5 but with the gold set drafted early (Milestone 2) so it can't be unconsciously tuned to the system's outputs.

**Gold-standard set** (built manually by Zak from the Auto Trader documents, before final pipeline tuning):

- 20 factual data points (figures, KPIs, segment facts) with page references
- 10 key risks the documents disclose or clearly imply
- 10 important business observations a competent analyst should surface
- 10 diligence questions a competent analyst would ask

**Metrics:**

| Metric | Definition | Method |
|---|---|---|
| Fact extraction recall | Gold facts found / 20 | Automated match + manual adjudication of near-misses |
| Fact extraction precision | Extracted facts that are correct / total extracted (sample of 30) | Manual check against documents |
| Citation accuracy | Cited page actually supports the claim (sample of 30 claims) | Manual check |
| Unsupported claim rate | Memo claims with no resolving evidence reference or wrong evidence | Automated (unresolved refs) + manual (wrong refs) |
| Calculation accuracy | Pipeline calculations vs hand-calculated values | Automated comparison, should be 100% — any miss is a bug |
| Risk/observation coverage | Gold risks and observations surfaced / 20 | Manual |
| Question relevance | Diligence questions rated 1–3 (irrelevant / plausible / genuinely useful) | Human rating, report distribution |
| Duplication | Near-duplicate items in memo lists | Manual count |
| False confidence | Items marked "factual/high confidence" that are actually inferred or wrong | Manual, from the precision and citation samples |

**Process:** run the pipeline, score, write up every failure with a diagnosis (extraction miss vs chunking fault vs prompt fault vs validation gap), fix the top failure modes once, re-run, and report **both** rounds. The error analysis and the before/after comparison are the most credible part of the portfolio — do not cherry-pick.

## 10. Key risks

1. **PDF table extraction fails on the financial statements** (highest likelihood, highest impact). Financial PDFs have merged cells, multi-line headers, footnote markers. *Mitigation:* test pdfplumber on the Auto Trader statements in week 1 before building anything downstream; fall back to targeted per-statement parsing or manual table transcription for V1 if needed (declared honestly as a limitation).
2. **Citation drift.** The model attributes a fact to the wrong chunk/page. *Mitigation:* excerpt stored with every fact; code verifies the excerpt appears in the cited chunk; eval measures the residual rate.
3. **Hallucinated or transposed numbers.** *Mitigation:* numbers only enter the memo via `facts.json`/`financials.json`; string-match validation of every figure in the memo; failures block the run.
4. **Eval subjectivity.** Several metrics need human judgement. *Mitigation:* write judging criteria before scoring; keep samples fixed; report the method openly.
5. **Scope creep / overengineering.** The known failure mode of portfolio projects. *Mitigation:* the out-of-scope list in §3 is a contract; anything new goes to a V2 list.
6. **Gold-set contamination.** Tuning prompts on the same facts you evaluate on. *Mitigation:* build the gold set early and freeze it; develop prompts against different sections/documents where possible.
7. **Cost/context limits.** Low risk at this scale; run log makes it visible.

## 11. Milestone plan

Assumes part-time effort alongside the job search; each milestone ends with something working and demonstrable.

| # | Milestone | Contents | Est. effort |
|---|---|---|---|
| 0 | Design sign-off | This document reviewed and agreed | Done at review |
| 1 | Ingestion + extraction spike | Download docs; pdfplumber over the full annual report; page-referenced chunks; **table extraction risk retired or re-planned** | 3–4 days |
| 2 | Gold set + fact extraction | Build and freeze the 50-item gold set; schemas; Claude fact extraction with citations on one document; spot-check quality | 4–5 days |
| 3 | Deterministic finance module | `finance.py` pure functions; unit tests; cross-checks; `financials.json` | 2–3 days |
| 4 | Classification + memo | `classify.py`, `memo.py`, citation/number validators; first end-to-end memo | 4–5 days |
| 5 | Evaluation | Eval harness; score; error analysis; one improvement round; re-score; write up honestly | 4–5 days |
| 6 | Review UX + repo polish | Streamlit claim-inspection view; README; architecture diagram; example outputs; screenshots | 3–4 days |
| 7 | Portfolio packaging | One-page case study; short demo video; interview talking points | 2 days |

Roughly 4–6 weeks part-time. Milestones 1–5 are the substance; 6–7 are presentation. If time pressure hits, cut Milestone 6's polish, never Milestone 5.

## 12. What Zak needs to understand before implementation

Each of these will come up in interviews; we cover them as they arise in the relevant milestone:

1. **How structured outputs via tool use work** — why schema-enforced JSON beats "please return JSON" prompting, and what still goes wrong (M2).
2. **PDF extraction limitations** — why PDFs are a layout format not a data format, and why tables are hard (M1).
3. **Chunking trade-offs** — structure-based vs fixed-window; why page references must survive chunking (M1).
4. **Why no vector database in V1** — retrieval solves a scale problem this project doesn't have; being able to argue this is more impressive than having one (M0 — now).
5. **Precision vs recall** — and which matters more here (an unsupported claim in a memo is worse than a missed fact, so precision on claims is the priority metric) (M2/M5).
6. **Prompt design for extraction vs generation** — extraction prompts constrain and enumerate; generation prompts synthesise from validated inputs only (M2/M4).
7. **Pydantic validation as a safety layer** — how typed schemas turn silent model errors into visible failures (M2).
8. **Token/cost budgeting** — reading the run log, roughly what a document costs to process (M2).
9. **Evaluation honesty** — why the frozen gold set and reported failure analysis are the difference between a demo and evidence (M5).

---

## Decision log

| Decision | Choice | Status |
|---|---|---|
| First company | Auto Trader Group plc | Confirmed 14 Jul 2026 |
| LLM provider | Anthropic Claude API (thin wrapper for portability) | Confirmed 14 Jul 2026 |
| V1 interface | CLI first; Streamlit at Milestone 6 | Confirmed 14 Jul 2026 |
| Retrieval/vector DB | None in V1 | Proposed — confirm at review |
| Document set | FY2026 AR + FY2026 results presentation (+ optional H1 FY26) | Proposed — confirm at review |
| Eval gold-set timing | Built and frozen in Milestone 2, before prompt tuning | Confirmed 14 Jul 2026 |
| Gold set frozen | `eval/gold_set.json` — 50 items (20 facts, 10 risks, 10 observations, 10 questions) built manually by Zak from the PDFs. Frozen as of 14 Jul 2026. Must not be edited or tuned against. | Frozen 14 Jul 2026 |
| PDF table extraction | Use `extract_text()` only, not `extract_tables()`. pdfplumber table detection fails on Auto Trader statements (1-column output, no labels, missing comparative year) because pages lack explicit ruled borders. Text extraction is clean on all four primary statements including the 8-column Changes in Equity. Claude parses tabular structure from text in Stage 3. Risk §10.1 retired. | Confirmed 14 Jul 2026 |
| Extraction model split | Haiku (`claude-haiku-4-5-20251001`) for fact extraction (structured reading); Sonnet (`claude-sonnet-5`) reserved for classification and memo generation (analytical judgement). Haiku is ~4x cheaper. | Confirmed 14 Jul 2026 |
| Extraction cost controls | Lesson from M2: page-by-page extraction across 146 pages at Sonnet pricing cost $4.96 for 81 pages. Five mitigations applied: (1) section filtering — only ~40 memo-relevant pages, not all 146; (2) batch 3-5 pages per API call to amortise overhead; (3) tighter prompt targeting 2-5 material facts per page instead of "extract ALL"; (4) cost guard — estimate before run, abort if >$3; (5) resumable — skip already-extracted pages, merge results. | Confirmed 14 Jul 2026 |
