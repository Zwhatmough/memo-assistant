"""Generic section filter for PDF annual-report extraction.

Replaces the hard-coded MEMO_SECTIONS page ranges in extract.py with a
heading-taxonomy matcher that auto-detects page ranges from PDF content.

Two mechanisms:
  1. detect_page_offset(pdf_path) — finds the difference between the PDF's
     internal page index and the printed page numbers in the document. Most
     UK annual reports have a cover page or contents section before page 1,
     so PDF page 1 may print as "1" or PDF page 6 may print as "1".
     Used so citations reference the page number the analyst sees, not the
     internal PDF index.

  2. detect_section_pages(pdf_path, section_taxonomy) — scans each PDF page's
     leading text for heading patterns defined in config.yaml's section_taxonomy.
     Returns (start_page, end_page, label) tuples compatible with MEMO_SECTIONS.
     Falls back to fallback_pages from config if detection misses a section.

Design note: heading detection uses simple case-insensitive substring matching —
no fuzzy edit-distance scoring. This is deliberate: UK annual report headings
are formulaic ("Principal Risks and Uncertainties" appears verbatim in most
FTSE annual reports), so exact substring matching is reliable without adding
the complexity of a fuzzy matcher. If a second company shows heading misses,
extend heading_variants in config.yaml rather than loosening the matcher.
"""

import re
from pathlib import Path
from typing import Optional

import pdfplumber
import yaml


# ── Heading scan window ───────────────────────────────────────────────────────

# How many characters of page text to scan for section headings.
# Headings appear at the top of a page; 400 chars covers ~3–4 lines.
HEADING_SCAN_CHARS = 400

# Pages to scan when detecting the printed-page offset.
# Most UK ARs have ≤15 front-matter pages before the report starts.
OFFSET_SCAN_PAGES = 20

# Regex for isolated page numbers in footer text.
# Matches a standalone integer on what is likely the last line of a page.
_PAGE_NUMBER_RE = re.compile(r'^\s*(\d{1,3})\s*$', re.MULTILINE)


# ── Page offset detection ─────────────────────────────────────────────────────

def detect_page_offset(pdf_path: str | Path) -> int:
    """Return printed-page offset: PDF_page_index − printed_page_number.

    Scans the first OFFSET_SCAN_PAGES pages looking for an isolated integer
    in the footer (last non-empty line). The first page where the footer
    shows "1" is the start of the numbered document; offset = its PDF index.

    Returns 0 if detection fails (safe default: PDF index = printed page).

    Example: if PDF page index 5 (0-based) has footer "1",
             offset = 5 and printed_page = pdf_index − offset.
    """
    with pdfplumber.open(str(pdf_path)) as pdf:
        for pdf_idx, page in enumerate(pdf.pages[:OFFSET_SCAN_PAGES]):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            # Look for an isolated digit on the last non-empty line
            lines = [ln for ln in text.splitlines() if ln.strip()]
            if not lines:
                continue
            footer = lines[-1].strip()
            if _PAGE_NUMBER_RE.match(footer):
                printed = int(footer)
                if printed == 1:
                    # This PDF page starts the numbered document at printed page 1
                    return pdf_idx  # offset = pdf_index - 0 (since printed=1 here)
    return 0


# ── Heading taxonomy matching ─────────────────────────────────────────────────

def _page_matches_section(leading_text: str, heading_variants: list[str]) -> bool:
    """True if any heading variant appears in the page's leading text."""
    lower = leading_text.lower()
    return any(variant.lower() in lower for variant in heading_variants)


def detect_section_pages(
    pdf_path: str | Path,
    section_taxonomy: dict,
    page_offset: int = 0,
) -> list[tuple[int, int, str]]:
    """Auto-detect page ranges for each section type in section_taxonomy.

    Scans each PDF page's leading HEADING_SCAN_CHARS characters against
    the heading_variants for each section. When a heading is found, the
    section starts there and continues until a different section's heading
    is found, or max_pages is reached.

    Returns a list of (start_page, end_page, label) tuples using the
    printed page numbers (pdf_index - page_offset + 1 if 1-indexed), but
    since pdfplumber and the citation system both use 1-based PDF indices,
    we return 1-based PDF indices without offset adjustment by default.

    Falls back to fallback_pages for any section where heading detection
    finds nothing. Logs a warning for each fallback used.
    """
    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)
        # (pdf_1based_page, leading_text) for all pages
        page_heads: list[tuple[int, str]] = []
        for pdf_idx, page in enumerate(pdf.pages):
            text = (page.extract_text() or "")[:HEADING_SCAN_CHARS]
            page_heads.append((pdf_idx + 1, text))  # 1-based

    # For each section, find which PDF pages contain a matching heading
    section_hit_pages: dict[str, list[int]] = {
        section_id: [] for section_id in section_taxonomy
    }
    for page_num, head_text in page_heads:
        for section_id, spec in section_taxonomy.items():
            if _page_matches_section(head_text, spec.get("heading_variants", [])):
                section_hit_pages[section_id].append(page_num)

    # Build (start, end, label) tuples
    results: list[tuple[int, int, str]] = []
    for section_id, spec in section_taxonomy.items():
        hits = section_hit_pages[section_id]
        label = spec.get("description", section_id)
        fallback = spec.get("fallback_pages")
        max_p = spec.get("max_pages", 10)

        if hits:
            start = hits[0]
            end = min(max(hits), start + max_p - 1, total_pages)
            results.append((start, end, label))
        elif fallback and len(fallback) == 2:
            print(f"  [section_filter] '{section_id}': no heading found — "
                  f"using fallback p{fallback[0]}–{fallback[1]}")
            results.append((fallback[0], fallback[1], label))
        else:
            print(f"  [section_filter] '{section_id}': no heading found and "
                  f"no fallback configured — section skipped")

    # Sort by start page
    results.sort(key=lambda t: t[0])
    return results


# ── Config loader ─────────────────────────────────────────────────────────────

def load_section_taxonomy(config_path: str | Path = "config.yaml") -> dict:
    """Load section_taxonomy from config.yaml."""
    with open(str(config_path)) as f:
        cfg = yaml.safe_load(f)
    return cfg.get("section_taxonomy", {})


def build_memo_sections(
    pdf_path: str | Path,
    config_path: str | Path = "config.yaml",
    detect_offset: bool = True,
) -> tuple[list[tuple[int, int, str]], int]:
    """High-level entry point: return (memo_sections, page_offset).

    memo_sections is a list of (start_page, end_page, label) tuples
    compatible with the MEMO_SECTIONS constant in extract.py.

    page_offset is 0 unless detect_offset=True and a printed-page start
    is successfully found.
    """
    taxonomy = load_section_taxonomy(config_path)
    offset = detect_page_offset(pdf_path) if detect_offset else 0
    if offset:
        print(f"  [section_filter] Detected printed-page offset: {offset} "
              f"(PDF page {offset+1} = printed page 1)")
    sections = detect_section_pages(pdf_path, taxonomy, page_offset=offset)
    return sections, offset
