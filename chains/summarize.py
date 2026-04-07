"""
chains/summarize.py — Step 4: Per-Paper Summarization Chain
Orchestrates the full per-paper processing pipeline:
  1. Fetch and extract PDF text
  2. Split into chunks (LangChain TextSplitter)
  3. MapReduce summarization across chunks
  4. Parse structured output via PydanticOutputParser
  5. Return populated PaperSummary

Design: Sequential execution per paper to respect free model rate limits.
"""

from typing import Callable, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from arxiv.fetch_pdf import fetch_paper_text
from arxiv.search import ArxivPaper
from chains.output_parser import parse_paper
from models.paper_schema import PaperSummary
from utils.llm_factory import get_llm
from config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_PAPER
from utils.logger import get_logger

logger = get_logger(__name__)


MAP_PROMPT = PromptTemplate(
    input_variables=["chunk"],
    template="""Extract key information from this section of a research paper.
Focus on: methods, results, datasets, metrics, limitations, contributions, future work.
Be concise. Preserve specific numbers and technical terms.

Paper section:
{chunk}

Key information extracted:"""
)


def summarize_paper(
    paper: ArxivPaper,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> tuple[PaperSummary, dict]:
    """
    Full summarization pipeline for a single paper.

    Args:
        paper: ArxivPaper metadata object
        progress_callback: Optional function called with progress status strings

    Returns:
        Tuple of (PaperSummary, run_info dict)
        run_info contains: source, chunks_processed, parse_status
    """
    def log(msg: str):
        if progress_callback:
            progress_callback(msg)

    run_info = {
        "arxiv_id": paper.arxiv_id,
        "source": "unknown",
        "chunks_processed": 0,
        "parse_status": "unknown",
    }

    # ── Step 1: Fetch paper text (Large Context Mode) ───────────────────────
    log(f"Downloading paper: {paper.title[:60]}…")
    paper_text, source = fetch_paper_text(
        pdf_url=paper.pdf_url,
        abstract=paper.abstract,
        title=paper.title,
    )
    run_info["source"] = source
    log(f"Text source: {source} ({len(paper_text):,} chars)")

    # ── Step 2: Track chunks ──────────────────────
    run_info["chunks_processed"] = 1

    # ── Step 3: Parse into structured summary ──────────────────────────────
    log("Extracting structured fields…")
    summary, parse_status = parse_paper(
        paper_text=paper_text,
        title=paper.title,
        authors=paper.authors,
        year=paper.year,
        arxiv_id=paper.arxiv_id,
    )
    run_info["parse_status"] = parse_status
    log(f"Parse status: {parse_status}")

    return summary, run_info



def summarize_papers_batch(
    papers: list[ArxivPaper],
    progress_callback: Optional[Callable[[str, int, int], None]] = None,
) -> list[tuple[PaperSummary, dict]]:
    """
    Summarize a batch of papers sequentially (1–5 papers).
    Sequential to respect free model rate limits and keep progress visible.

    Args:
        papers: List of selected ArxivPaper objects (max 5)
        progress_callback: Called with (status_msg, current_index, total)

    Returns:
        List of (PaperSummary, run_info) tuples, one per paper.
        If a paper fails, its slot contains (empty_summary, run_info_with_error).
    """
    results = []
    total = len(papers)

    for i, paper in enumerate(papers):
        if progress_callback:
            progress_callback(f"Processing paper {i + 1} of {total}: {paper.title[:50]}…", i + 1, total)

        def _cb(msg):
            if progress_callback:
                progress_callback(msg, i + 1, total)

        try:
            result = summarize_paper(paper, progress_callback=_cb)
            results.append(result)
        except Exception as e:
            from models.paper_schema import empty_summary
            fallback = empty_summary(
                title=paper.title,
                authors=paper.authors,
                year=paper.year,
                arxiv_id=paper.arxiv_id,
            )
            run_info = {
                "arxiv_id": paper.arxiv_id,
                "source": "error",
                "chunks_processed": 0,
                "parse_status": f"error: {str(e)[:100]}",
            }
            results.append((fallback, run_info))
            if progress_callback:
                progress_callback(f"Paper {i + 1} failed: {e}. Continuing…", i + 1, total)

    return results
