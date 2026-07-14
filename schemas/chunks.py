"""Schema for text chunks extracted from PDFs."""

from pydantic import BaseModel


class Chunk(BaseModel):
    """A single chunk of text from a document, with its source location."""

    chunk_id: str  # e.g. "at-ar-fy26_p103"
    doc_id: str  # e.g. "at-ar-fy26"
    page: int  # PDF page number (1-indexed)
    text: str  # the extracted text


class ChunkedDocument(BaseModel):
    """All chunks from a single document."""

    doc_id: str
    total_pages: int
    chunks: list[Chunk]
