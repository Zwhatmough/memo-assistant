"""Pipeline validation: verify every extracted fact's citation.

For each fact in facts.json, checks that the excerpt appears verbatim
on its cited page (using normalised string matching). If not found on
the cited page, scans the two pages above and below and auto-corrects
the page number if the excerpt is found there. Facts whose excerpts
cannot be located on any nearby page are flagged as unverifiable and
marked for exclusion from downstream stages.

Writes validated_facts.json with a 'citation_status' field on every
fact, and prints a verification report.

Usage:
    python validate.py                          # uses output/facts.json
    python validate.py --facts output/facts.json
"""

import argparse
import json
import re
import unicodedata

import pdfplumber


# How many pages either side to search when the cited page doesn't match.
NEARBY_WINDOW = 2

# Minimum excerpt length to attempt matching (very short strings
# match too easily by coincidence).
MIN_EXCERPT_LEN = 12


def _normalise(text: str) -> str:
    """Normalise text for matching.

    Handles the most common character-level divergences between
    pdfplumber's PDF extraction and the model's output:
    - Smart quotes → straight quotes
    - En/em dashes → hyphen
    - Footnote superscript digits attached to words removed
    - All whitespace collapsed to single space, lowercased
    """
    # Smart single quotes → straight apostrophe
    text = re.sub(r"[\u2018\u2019\u201a\u201b]", "'", text)
    # Smart double quotes → straight quote
    text = re.sub(r"[\u201c\u201d\u201e\u201f]", '"', text)
    # En-dash / em-dash → hyphen
    text = re.sub(r"[\u2013\u2014]", "-", text)
    # Footnote superscripts: digits/letters directly appended to a word
    # e.g. "retailer1" or "ARPR1" → "retailer" / "ARPR"
    text = re.sub(r"(?<=[a-zA-Z])\d(?=\s|$|['\",.)%])", "", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# Minimum words in a fragment for fragment-match to be meaningful.
FRAGMENT_WORDS = 6


def _fragment_match(norm_excerpt: str, norm_page: str) -> bool:
    """Check if any FRAGMENT_WORDS-word run from excerpt appears in page.

    This handles multi-column PDF layouts where pdfplumber interleaves
    column text, breaking what would otherwise be a contiguous excerpt.
    A 6-word run is specific enough to exclude coincidental matches.
    """
    words = norm_excerpt.split()
    if len(words) < FRAGMENT_WORDS:
        return norm_excerpt in norm_page  # short excerpts: exact only

    for i in range(len(words) - FRAGMENT_WORDS + 1):
        fragment = " ".join(words[i : i + FRAGMENT_WORDS])
        if fragment in norm_page:
            return True
    return False


def _load_page_texts(pdf_path: str) -> dict[int, str]:
    """Return a dict mapping 1-indexed page number -> normalised text."""
    pages = {}
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            pages[i + 1] = _normalise(text)
    return pages


def _check_excerpt(excerpt: str, page_texts: dict[int, str],
                   cited_page: int) -> tuple[str, int | None]:
    """Check whether an excerpt can be found near its cited page.

    Two-tier match:
    1. Exact normalised substring — handles single-column pages cleanly.
    2. Fragment match — handles multi-column pages where pdfplumber
       interleaves column text, splitting contiguous excerpts.

    Returns:
        (status, corrected_page) where status is one of:
          'verified'    — found on cited_page (exact or fragment)
          'corrected'   — found on a nearby page (auto-corrected)
          'unverifiable' — not found within cited_page ± NEARBY_WINDOW
        corrected_page is None for 'verified' and 'unverifiable'.
    """
    if not excerpt or len(excerpt.strip()) < MIN_EXCERPT_LEN:
        return "unverifiable", None

    norm_excerpt = _normalise(excerpt)

    def matches(page_num: int) -> bool:
        page_text = page_texts.get(page_num, "")
        return (norm_excerpt in page_text) or _fragment_match(norm_excerpt, page_text)

    # Check cited page first
    if matches(cited_page):
        return "verified", None

    # Check nearby pages
    for delta in range(1, NEARBY_WINDOW + 1):
        for candidate in (cited_page - delta, cited_page + delta):
            if matches(candidate):
                return "corrected", candidate

    return "unverifiable", None


FACT_KEYS = [
    "financial_figures",
    "business_facts",
    "risk_disclosures",
    "strategic_items",
    "management_commentary",
]


def validate_facts(facts_path: str, pdf_path: str) -> list[dict]:
    """Validate all facts and return the annotated facts list."""
    print(f"Loading {facts_path}...")
    with open(facts_path) as f:
        chunks = json.load(f)

    print(f"Loading page texts from {pdf_path}...")
    page_texts = _load_page_texts(pdf_path)
    print(f"  {len(page_texts)} pages loaded")

    counts = {"verified": 0, "corrected": 0, "unverifiable": 0, "total": 0}
    corrections: list[tuple[str, int, int]] = []   # (excerpt_preview, old, new)
    unverifiable: list[tuple[str, int, str]] = []  # (chunk_id, page, excerpt)

    validated_chunks = []

    for chunk in chunks:
        chunk_out = {k: [] for k in FACT_KEYS}
        chunk_out["chunk_id"] = chunk.get("chunk_id", "")

        for key in FACT_KEYS:
            for item in chunk.get(key, []):
                src = item.get("source", {})
                cited_page = src.get("page")
                excerpt = src.get("excerpt", "")

                if cited_page is None:
                    status, corrected = "unverifiable", None
                else:
                    status, corrected = _check_excerpt(
                        excerpt, page_texts, cited_page
                    )

                item_out = dict(item)
                item_out["citation_status"] = status

                if status == "corrected":
                    old_page = cited_page
                    item_out["source"] = dict(src)
                    item_out["source"]["page"] = corrected
                    item_out["source"]["page_original"] = old_page
                    corrections.append(
                        (excerpt[:60], old_page, corrected)
                    )
                elif status == "unverifiable":
                    unverifiable.append(
                        (chunk_out["chunk_id"], cited_page, excerpt[:80])
                    )

                counts[status] += 1
                counts["total"] += 1
                chunk_out[key].append(item_out)

        validated_chunks.append(chunk_out)

    # Print report
    total = counts["total"]
    print(f"\n{'='*60}")
    print(f"CITATION VERIFICATION REPORT")
    print(f"{'='*60}")
    print(f"Total facts:    {total}")
    print(f"  Verified:     {counts['verified']:3d}  ({100*counts['verified']//total}%)")
    print(f"  Corrected:    {counts['corrected']:3d}  (page auto-corrected)")
    print(f"  Unverifiable: {counts['unverifiable']:3d}  (excluded from downstream)")
    print(f"\nVerification rate (verified + corrected): "
          f"{counts['verified'] + counts['corrected']}/{total} "
          f"({100*(counts['verified']+counts['corrected'])//total}%)")

    if corrections:
        print(f"\nAuto-corrections ({len(corrections)}):")
        for excerpt, old, new in corrections:
            print(f"  p{old} → p{new}  \"{excerpt}\"")

    if unverifiable:
        print(f"\nUnverifiable facts ({len(unverifiable)}) — excluded downstream:")
        for chunk_id, page, excerpt in unverifiable:
            print(f"  [{chunk_id}] p{page}: \"{excerpt}\"")

    return validated_chunks


def main():
    parser = argparse.ArgumentParser(description="Validate fact citations")
    parser.add_argument("--facts", default="output/facts.json",
                        help="Path to facts.json")
    parser.add_argument("--pdf", default="documents/at-ar-fy26.pdf",
                        help="Path to the source PDF")
    parser.add_argument("--out", default="output/validated_facts.json",
                        help="Output path for validated facts")
    args = parser.parse_args()

    validated = validate_facts(args.facts, args.pdf)

    with open(args.out, "w") as f:
        json.dump(validated, f, indent=2)
    print(f"\nWrote {len(validated)} chunks to {args.out}")
    print("Downstream stages should use validated_facts.json, not facts.json.")


if __name__ == "__main__":
    main()
