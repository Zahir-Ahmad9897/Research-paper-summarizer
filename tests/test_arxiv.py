"""
tests/test_arxiv.py — Unit tests for arXiv search and PDF fetch
Run: python -m pytest tests/test_arxiv.py -v
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_search_returns_papers():
    """arXiv search must return at least 1 result for a known topic."""
    from arxiv.search import search_arxiv
    papers = search_arxiv("deep learning image classification convolutional neural network", max_results=3)
    assert len(papers) >= 1, "Expected at least 1 paper"


def test_paper_has_required_fields():
    """Each ArxivPaper must have title, authors, year, arxiv_id, pdf_url."""
    from arxiv.search import search_arxiv
    papers = search_arxiv("transformer attention mechanism natural language processing", max_results=2)
    for p in papers:
        assert p.title, "Missing title"
        assert p.authors, "Missing authors"
        assert p.arxiv_id, "Missing arxiv_id"
        assert p.pdf_url.startswith("http"), "Invalid pdf_url"
        assert len(p.year) == 4, f"Invalid year: {p.year}"


def test_short_abstract_truncates():
    """short_abstract property must truncate long abstracts to ~60 words."""
    from arxiv.search import ArxivPaper
    long_abstract = " ".join(["word"] * 200)
    paper = ArxivPaper(
        arxiv_id="test.001",
        title="Test Paper",
        authors="Author A",
        year="2024",
        abstract=long_abstract,
        pdf_url="https://arxiv.org/pdf/test.001.pdf",
        html_url="https://arxiv.org/abs/test.001",
    )
    short = paper.short_abstract
    assert short.endswith("…"), "Long abstract should end with ellipsis"
    assert len(short.split()) <= 65, "Short abstract too long"


def test_fetch_fallback_on_bad_url():
    """fetch_paper_text must return abstract_only fallback on bad URL."""
    from arxiv.fetch_pdf import fetch_paper_text
    text, source = fetch_paper_text(
        pdf_url="https://arxiv.org/pdf/0000.00000.pdf",
        abstract="This is the abstract fallback text.",
        title="Test Paper",
    )
    assert source == "abstract_only"
    assert "abstract" in text.lower() or "Test Paper" in text


def test_estimate_token_count():
    """Token estimate should be positive for non-empty text."""
    from arxiv.fetch_pdf import estimate_token_count
    count = estimate_token_count("Hello world this is a test sentence.")
    assert count > 0


if __name__ == "__main__":
    from arxiv.search import search_arxiv
    print("Testing arXiv search…")
    papers = search_arxiv("face recognition deep learning", max_results=3)
    print(f"Found {len(papers)} papers:")
    for p in papers:
        print(f"  - [{p.year}] {p.title[:60]} | {p.display_id}")
