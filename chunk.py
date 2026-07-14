"""Extract text from PDFs and produce page-level chunks.

Uses pdfplumber's extract_text() (not extract_tables() — see decision
log in DESIGN.md). Each page becomes one chunk carrying its page number,
so every downstream fact can cite its source location.

Page-level chunking is deliberately simple for Milestone 2. If pages
prove too long or too short, we can refine to section-based chunking
later — but we start simple and only add complexity when we see a
concrete problem.
"""

import pdfplumber

from schemas.chunks import Chunk, ChunkedDocument


def chunk_pdf(pdf_path: str, doc_id: str) -> ChunkedDocument:
    """Extract text from a PDF, one chunk per page.

    Args:
        pdf_path: Path to the PDF file.
        doc_id: Identifier for this document (e.g. "at-ar-fy26").

    Returns:
        A ChunkedDocument with one Chunk per non-empty page.
    """
    chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)

        for i, page in enumerate(pdf.pages):
            page_num = i + 1
            text = page.extract_text() or ""

            # Skip pages with negligible text (blank, image-only, etc.)
            if len(text.strip()) < 20:
                continue

            chunks.append(
                Chunk(
                    chunk_id=f"{doc_id}_p{page_num}",
                    doc_id=doc_id,
                    page=page_num,
                    text=text,
                )
            )

    return ChunkedDocument(doc_id=doc_id, total_pages=total_pages, chunks=chunks)
