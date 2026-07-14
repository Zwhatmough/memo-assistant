"""Stage 3: Fact extraction — send chunks to Claude and get structured facts.

Processes each chunk through call_llm() with the ExtractedFacts schema.
Outputs facts.json (all extracted facts) and run_log.json (API call records).

Usage:
    python extract.py documents/at-ar-fy26.pdf at-ar-fy26

    Optional: pass page ranges to extract only specific pages:
    python extract.py documents/at-ar-fy26.pdf at-ar-fy26 --pages 1-30
"""

import argparse
import json
import sys
import os

from dotenv import load_dotenv

load_dotenv()

from chunk import chunk_pdf
from llm import call_llm
from schemas.facts import ExtractedFacts


EXTRACTION_PROMPT = """You are an investment analyst assistant extracting structured facts from a company document.

Below is a page of text from {doc_id} (page {page}).

Extract ALL factual information into the structured format. For each fact, include:
- The exact source: doc_id="{doc_id}", page={page}, and a short excerpt (direct quote) supporting it.

Rules:
- Financial figures: extract ONLY numbers as reported in the document. Do NOT calculate ratios, growth rates, or derived values.
- For values in parentheses like (235.7), the value is negative: -235.7
- Confidence: "high" = explicitly stated, "medium" = clearly implied, "low" = inferred from context.
- risk_type: "disclosed" if the company explicitly names it as a risk, "inferred" if you identify it from context.
- Do NOT invent or hallucinate any information. If the page contains no extractable facts, return empty lists.
- Excerpts must be short direct quotes from the text, not paraphrases.

Document text:
---
{text}
---"""


def run_extraction(
    pdf_path: str,
    doc_id: str,
    page_start: int | None = None,
    page_end: int | None = None,
) -> tuple[list[dict], list[dict]]:
    """Run fact extraction on a PDF.

    Returns:
        (all_facts, call_log) — lists of dicts ready to write as JSON.
    """
    print(f"Chunking {pdf_path}...")
    doc = chunk_pdf(pdf_path, doc_id)
    print(f"  {len(doc.chunks)} non-empty pages from {doc.total_pages} total")

    # Filter to requested page range
    chunks = doc.chunks
    if page_start or page_end:
        start = page_start or 1
        end = page_end or 999
        chunks = [c for c in chunks if start <= c.page <= end]
        print(f"  Filtered to pages {start}-{end}: {len(chunks)} chunks")

    all_facts = []
    call_log = []

    for i, chunk in enumerate(chunks):
        print(f"  Extracting page {chunk.page} ({i + 1}/{len(chunks)})...", end=" ")

        prompt = EXTRACTION_PROMPT.format(
            doc_id=chunk.doc_id,
            page=chunk.page,
            text=chunk.text,
        )

        try:
            facts = call_llm(
                prompt=prompt,
                schema_class=ExtractedFacts,
                tool_name="extract_facts",
                log=call_log,
            )
            n = (
                len(facts.financial_figures)
                + len(facts.business_facts)
                + len(facts.risk_disclosures)
                + len(facts.strategic_items)
                + len(facts.management_commentary)
            )
            print(f"{n} facts")
            all_facts.append(facts.model_dump())

        except Exception as e:
            print(f"FAILED: {e}")
            call_log.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "error": str(e),
                    "success": False,
                }
            )

    return all_facts, call_log


def main():
    parser = argparse.ArgumentParser(description="Extract facts from a PDF")
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument("doc_id", help="Document identifier")
    parser.add_argument(
        "--pages", help="Page range, e.g. 1-30", default=None
    )
    args = parser.parse_args()

    page_start = page_end = None
    if args.pages:
        parts = args.pages.split("-")
        page_start = int(parts[0])
        page_end = int(parts[1]) if len(parts) > 1 else page_start

    facts, log = run_extraction(args.pdf_path, args.doc_id, page_start, page_end)

    os.makedirs("output", exist_ok=True)

    with open("output/facts.json", "w") as f:
        json.dump(facts, f, indent=2)
    print(f"\nWrote {len(facts)} chunk results to output/facts.json")

    with open("output/run_log.json", "w") as f:
        json.dump(log, f, indent=2)
    print(f"Wrote {len(log)} call records to output/run_log.json")

    # Summary
    total_cost = sum(r.get("cost_usd", 0) for r in log)
    total_input = sum(r.get("input_tokens", 0) for r in log)
    total_output = sum(r.get("output_tokens", 0) for r in log)
    print(f"\nTotal: {total_input:,} input + {total_output:,} output tokens, ${total_cost:.4f}")


if __name__ == "__main__":
    main()
