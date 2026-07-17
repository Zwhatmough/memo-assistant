"""Stage 3: Fact extraction — send chunks to Claude and get structured facts.

Key design decisions (Milestone 2):
- Resumable: loads existing facts.json and skips already-extracted pages.
- Section-filtered: only extracts pages relevant to the investment memo.
- Batched: groups consecutive pages into single API calls (3-5 pages each).
- Tight prompt: material facts only, targeting 2-5 per page.
- Cost guard: estimates cost upfront, aborts if > $3.
- Uses Haiku for extraction (structured reading doesn't need Sonnet).

Usage:
    python extract.py documents/at-ar-fy26.pdf at-ar-fy26
"""

import argparse
import json
import os
import re
import sys

from dotenv import load_dotenv

load_dotenv()

from chunk import chunk_pdf
from llm import call_llm, estimate_cost, EXTRACTION_MODEL
from schemas.facts import ExtractedFacts
from section_filter import build_memo_sections


# Hard-coded fallback sections used when config.yaml is absent or when
# section_filter.py heading detection fails for every section.
# These are Auto Trader FY2026 page ranges — for a new company, supply a
# config.yaml with section_taxonomy and fallback_pages instead of editing here.
_AT_MEMO_SECTIONS_FALLBACK = [
    (3, 9, "CEO/Chairman review, business overview"),
    (10, 15, "Strategy and market position"),
    (19, 21, "Key performance indicators"),
    (23, 25, "Financial review"),
    (48, 54, "Principal risks and uncertainties"),
    (103, 107, "Primary financial statements"),
]

# Pages per API call. Trade-off: more pages = fewer calls but larger
# prompts. At ~4,200 chars/page, 4 pages ≈ 17k chars ≈ 4k input tokens.
BATCH_SIZE = 4

# Cost guard: abort if estimated cost exceeds this.
MAX_COST_USD = 3.00

# Average tokens per batch (estimated from the first run).
# Used for cost estimation only — actual usage is logged per call.
EST_INPUT_TOKENS_PER_BATCH = 5000
EST_OUTPUT_TOKENS_PER_BATCH = 2000


EXTRACTION_PROMPT = """You are extracting material facts from a company's annual report for an investment analyst.

The text below comes from {doc_id}. It is divided by PAGE markers (--- PAGE N ---).

Extract ONLY facts that an investment analyst would cite in a first-draft memo:
- Key financial figures (revenue, profit, margins, cash flow, debt, dividends)
- Operating KPIs (customer numbers, pricing metrics, volume metrics)
- Material business facts (what the company does, its market position, segments)
- Disclosed risks and strategic priorities
- Notable management commentary on outlook or performance drivers

Do NOT extract:
- Governance details (board composition, committee memberships, director biographies)
- Remuneration details
- Accounting policy descriptions
- Audit report language
- Minor or repetitive facts already covered by a headline number

SOURCE RULES — these are strict:
1. source.page must be the exact PAGE N number from the marker immediately before the text where you found the excerpt. Never use the batch range or another page number.
2. source.excerpt must be a single contiguous verbatim span copied exactly as it appears in the text — no ellipses, no joining of fragments from different sentences, no paraphrasing. It must be short enough to appear on one page as a consecutive string.
3. source.doc_id is always "{doc_id}".

OTHER RULES:
- Confidence: "high" = explicitly stated, "medium" = clearly implied, "low" = inferred.
- Financial figures: extract ONLY numbers as stated. Do NOT calculate ratios or growth rates.
- For values in parentheses like (235.7), the value is negative: -235.7.
- Target 2-5 material facts per page. Quality over quantity.

Document text:
---
{text}
---"""


def _get_page_num(chunk_id: str) -> int | None:
    """Extract page number from a chunk_id like 'at-ar-fy26_p103'."""
    m = re.search(r"(\d+)$", chunk_id)
    return int(m.group(1)) if m else None


def _load_existing_facts(path: str) -> tuple[list[dict], set[int]]:
    """Load existing facts.json, return (facts_list, set_of_done_pages).

    A page is only considered "done" if at least one fact cites it.
    Empty batch results (0 facts) are dropped — they indicate a failed
    or mis-batched extraction and should be retried.
    """
    if not os.path.exists(path):
        return [], set()

    with open(path) as f:
        raw = json.load(f)

    facts = []
    done_pages = set()

    for chunk in raw:
        # Collect pages cited by actual facts
        cited = set()
        for key in ["financial_figures", "business_facts", "risk_disclosures",
                     "strategic_items", "management_commentary"]:
            for item in chunk.get(key, []):
                p = item.get("source", {}).get("page")
                if p:
                    cited.add(p)

        # Drop chunks with zero extracted facts — treat as not done
        if not cited:
            continue

        facts.append(chunk)
        done_pages.update(cited)

    return facts, done_pages


def _pages_in_memo_sections(memo_sections: list[tuple[int, int, str]]) -> list[int]:
    """Return sorted list of all page numbers covered by memo_sections."""
    pages = []
    for start, end, _ in memo_sections:
        pages.extend(range(start, end + 1))
    return sorted(set(pages))


def _resolve_memo_sections(pdf_path: str, config_path: str = "config.yaml") -> list[tuple[int, int, str]]:
    """Return section page ranges, auto-detected from PDF headings where possible.

    Tries config.yaml + section_filter.py first. Falls back to the hardcoded
    Auto Trader ranges if config.yaml is absent or returns no sections.
    """
    import os
    if os.path.exists(config_path):
        try:
            sections, _ = build_memo_sections(pdf_path, config_path, detect_offset=True)
            if sections:
                return sections
            print("  [section_filter] Auto-detection returned no sections — "
                  "using hardcoded fallback")
        except Exception as e:
            print(f"  [section_filter] Error during auto-detection ({e}) — "
                  f"using hardcoded fallback")
    else:
        print(f"  [section_filter] {config_path} not found — using hardcoded fallback")
    return _AT_MEMO_SECTIONS_FALLBACK


def _make_batches(chunks: list, batch_size: int) -> list[list]:
    """Group chunks into batches of up to batch_size consecutive pages.

    Only pages that are truly adjacent (page numbers differ by 1) are
    grouped together. A gap in page numbers starts a new batch, regardless
    of batch_size. This prevents cross-section batches that confuse the
    model with non-contiguous text.
    """
    if not chunks:
        return []

    batches = []
    current = [chunks[0]]

    for chunk in chunks[1:]:
        prev_page = current[-1].page
        this_page = chunk.page
        # Start a new batch if pages aren't adjacent or batch is full
        if this_page != prev_page + 1 or len(current) >= batch_size:
            batches.append(current)
            current = [chunk]
        else:
            current.append(chunk)

    batches.append(current)
    return batches
    return batches


def run_extraction(
    pdf_path: str,
    doc_id: str,
    config_path: str = "config.yaml",
    facts_out: str = "output/facts.json",
) -> None:
    """Run fact extraction on memo-relevant sections of a PDF."""

    facts_path = facts_out
    log_path = os.path.join(os.path.dirname(facts_out) or "output", "run_log.json")

    # 1. Load existing results (resumable)
    existing_facts, done_pages = _load_existing_facts(facts_path)
    if done_pages:
        print(f"Loaded {len(existing_facts)} existing chunk results "
              f"(pages already done: {sorted(done_pages)})")

    # 2. Chunk the PDF
    print(f"Chunking {pdf_path}...")
    doc = chunk_pdf(pdf_path, doc_id)
    print(f"  {len(doc.chunks)} non-empty pages from {doc.total_pages} total")

    # 3. Filter to memo-relevant sections (auto-detected from headings or fallback)
    memo_sections = _resolve_memo_sections(pdf_path, config_path=config_path)
    target_pages = _pages_in_memo_sections(memo_sections)
    chunks = [c for c in doc.chunks if c.page in target_pages]
    print(f"  Filtered to memo sections: {len(chunks)} pages")
    for start, end, label in memo_sections:
        print(f"    p{start}-{end}: {label}")

    # 4. Skip already-extracted pages
    chunks = [c for c in chunks if c.page not in done_pages]
    if not chunks:
        print("  All target pages already extracted. Nothing to do.")
        return
    print(f"  After skipping done pages: {len(chunks)} pages to extract")

    # 5. Batch pages
    batches = _make_batches(chunks, BATCH_SIZE)
    print(f"  Grouped into {len(batches)} batches of up to {BATCH_SIZE} pages")

    # 6. Cost guard
    est_cost = estimate_cost(
        n_calls=len(batches),
        avg_input_tokens=EST_INPUT_TOKENS_PER_BATCH,
        avg_output_tokens=EST_OUTPUT_TOKENS_PER_BATCH,
        model=EXTRACTION_MODEL,
    )
    print(f"\n  Estimated cost: ${est_cost:.2f} "
          f"({len(batches)} calls × ~{EST_INPUT_TOKENS_PER_BATCH}+{EST_OUTPUT_TOKENS_PER_BATCH} tokens "
          f"@ {EXTRACTION_MODEL})")
    if est_cost > MAX_COST_USD:
        print(f"  ABORTED: estimated cost ${est_cost:.2f} exceeds "
              f"${MAX_COST_USD:.2f} limit.")
        sys.exit(1)

    # 7. Extract
    new_facts = []
    call_log = []

    for batch_idx, batch in enumerate(batches):
        page_nums = [c.page for c in batch]
        page_range = f"{page_nums[0]}-{page_nums[-1]}" if len(page_nums) > 1 else str(page_nums[0])
        batch_id = f"{doc_id}_p{page_range}"

        print(f"  Batch {batch_idx + 1}/{len(batches)} "
              f"(pages {page_range})...", end=" ", flush=True)

        # Combine text from all pages in the batch
        combined_text = ""
        for chunk in batch:
            combined_text += f"\n--- PAGE {chunk.page} ---\n{chunk.text}\n"

        prompt = EXTRACTION_PROMPT.format(
            doc_id=doc_id,
            page_range=page_range,
            text=combined_text,
        )

        try:
            facts = call_llm(
                prompt=prompt,
                schema_class=ExtractedFacts,
                tool_name="extract_facts",
                model=EXTRACTION_MODEL,
                max_tokens=8192,
                log=call_log,
            )
            # chunk_id is not part of the model schema — set it here
            facts_dict = facts.model_dump()
            facts_dict["chunk_id"] = batch_id

            n = sum(
                len(facts_dict[k])
                for k in ["financial_figures", "business_facts",
                           "risk_disclosures", "strategic_items",
                           "management_commentary"]
            )
            print(f"{n} facts")
            new_facts.append(facts_dict)

        except Exception as e:
            print(f"FAILED: {e}")
            call_log.append({
                "batch_id": batch_id,
                "pages": page_nums,
                "error": str(e),
                "success": False,
            })

    # 8. Merge with existing and save
    os.makedirs(os.path.dirname(facts_path) or "output", exist_ok=True)

    all_facts = existing_facts + new_facts
    with open(facts_path, "w") as f:
        json.dump(all_facts, f, indent=2)
    print(f"\nWrote {len(all_facts)} total chunk results to {facts_path} "
          f"({len(existing_facts)} existing + {len(new_facts)} new)")

    # Append to run log (don't overwrite previous runs)
    existing_log = []
    if os.path.exists(log_path):
        with open(log_path) as f:
            existing_log = json.load(f)
    with open(log_path, "w") as f:
        json.dump(existing_log + call_log, f, indent=2)

    # Summary
    total_cost = sum(r.get("cost_usd", 0) for r in call_log)
    total_input = sum(r.get("input_tokens", 0) for r in call_log)
    total_output = sum(r.get("output_tokens", 0) for r in call_log)
    print(f"This run: {total_input:,} input + {total_output:,} output tokens, "
          f"${total_cost:.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract facts from memo-relevant sections of a PDF"
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("doc_id", help="Document identifier")
    parser.add_argument("--config", default="config.yaml",
                        help="Path to company config YAML (default: config.yaml)")
    parser.add_argument("--out", default="output/facts.json",
                        help="Output path for extracted facts JSON (default: output/facts.json)")
    args = parser.parse_args()

    run_extraction(args.pdf_path, args.doc_id, config_path=args.config, facts_out=args.out)


if __name__ == "__main__":
    main()
