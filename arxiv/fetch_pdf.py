"""
arxiv/fetch_pdf.py — PDF Download and Text Extraction
Downloads the paper PDF from arXiv, extracts clean text using PyMuPDF.
Falls back gracefully to abstract + metadata if PDF is unavailable or fails to parse.

Two-level fallback:
  1. Full PDF text (primary)
  2. Abstract + metadata only (fallback)
"""

import time
import requests
from typing import Optional

from config import ARXIV_RATE_LIMIT_SLEEP
from utils.retry import retry
from utils.logger import get_logger

logger = get_logger(__name__)


def fetch_paper_text(pdf_url: str, abstract: str = "", title: str = "") -> tuple[str, str]:
    """
    Attempt to download and extract text from a paper PDF.

    Args:
        pdf_url:  Direct URL to the arXiv PDF
        abstract: Paper abstract (used as fallback)
        title:    Paper title (used in fallback text)

    Returns:
        Tuple of (extracted_text, source)
        source is "full_pdf" or "abstract_only"
    """
    try:
        pdf_bytes = _download_pdf(pdf_url)
        if pdf_bytes:
            text = _extract_text_pymupdf(pdf_bytes)
            if text and len(text.strip()) > 200:
                return text, "full_pdf"
    except Exception as e:
        logger.warning(f"PDF fetch/extract failed for {pdf_url}: {e}")

    # Fallback: abstract + metadata
    fallback = _build_fallback_text(title, abstract)
    return fallback, "abstract_only"


@retry(max_attempts=3, delay=3.0, exceptions=(requests.RequestException,), on_fail_return=None)
def _download_pdf(url: str, timeout: int = 20) -> Optional[bytes]:
    """Download PDF bytes from URL. Returns None on failure."""
    time.sleep(ARXIV_RATE_LIMIT_SLEEP)
    headers = {"User-Agent": "ResearchSummarizer/1.0 (research tool; contact via github)"}
    response = requests.get(url, headers=headers, timeout=timeout)
    if response.status_code == 200 and "pdf" in response.headers.get("content-type", "").lower():
        return response.content
    # arXiv sometimes returns HTML landing page — check content type
    if response.status_code == 200 and len(response.content) > 10000:
        return response.content  # Try anyway
    return None


def _extract_text_pymupdf(pdf_bytes: bytes) -> str:
    """
    Extract text from PDF bytes using PyMuPDF.
    Handles multi-column layouts better than pdfplumber for academic papers.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        pages_text = []
        for page_num, page in enumerate(doc):
            # Sort text blocks by vertical position for correct reading order
            blocks = page.get_text("blocks")
            blocks.sort(key=lambda b: (b[1], b[0]))  # Sort by y then x
            page_text = "\n".join(b[4] for b in blocks if b[4].strip())
            pages_text.append(page_text)
        doc.close()
        full_text = "\n\n".join(pages_text)
        # Basic cleanup
        full_text = _clean_text(full_text)
        return full_text
    except ImportError:
        raise ImportError("PyMuPDF not installed. Run: pip install pymupdf")
    except Exception as e:
        raise RuntimeError(f"PDF text extraction failed: {e}")


def _clean_text(text: str) -> str:
    """Remove common PDF extraction artifacts."""
    import re
    # Remove excessive whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {3,}", " ", text)
    # Remove lines that are just page numbers or short artifacts
    lines = [l for l in text.splitlines() if len(l.strip()) > 2]
    return "\n".join(lines)


def _build_fallback_text(title: str, abstract: str) -> str:
    """Build a structured text block from title and abstract for fallback processing."""
    return f"""Title: {title}

Abstract:
{abstract}

Note: Full PDF text was unavailable. Summary is based on title and abstract only.
Fields requiring full paper content may be marked N/A — not reported.
"""


def estimate_token_count(text: str) -> int:
    """Rough token estimate: ~1 token per 4 characters."""
    return len(text) // 4
