"""
arxiv/search.py — Step 2: arXiv Search
Sends enhanced query to the arXiv free API and returns structured paper metadata.
No API key required. Rate limit: 1 request per 3 seconds (handled automatically).

Returns list of ArxivPaper dicts with all metadata needed for display and processing.
"""

import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Optional
import requests

from config import ARXIV_BASE_URL, ARXIV_MAX_RESULTS, ARXIV_RATE_LIMIT_SLEEP
from utils.retry import retry
from utils.logger import get_logger

logger = get_logger(__name__)


NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}


@dataclass
class ArxivPaper:
    """Structured metadata for a single arXiv paper."""
    arxiv_id: str
    title: str
    authors: str           # comma-separated
    year: str
    abstract: str
    pdf_url: str
    html_url: str
    journal: str = "arXiv preprint"
    categories: list[str] = field(default_factory=list)

    @property
    def display_id(self) -> str:
        return f"arXiv:{self.arxiv_id}"

    @property
    def short_abstract(self) -> str:
        words = self.abstract.split()
        if len(words) > 60:
            return " ".join(words[:60]) + "…"
        return self.abstract


@retry(max_attempts=4, delay=5.0, exceptions=(requests.RequestException,), on_fail_return=[])
def search_arxiv(query: str, max_results: int = ARXIV_MAX_RESULTS) -> list[ArxivPaper]:
    """
    Search arXiv with the given query string.

    Args:
        query: Enhanced search query
        max_results: Maximum papers to return (capped at ARXIV_MAX_RESULTS)

    Returns:
        List of ArxivPaper objects, empty list on failure

    Raises:
        requests.RequestException: On network failure (caller handles)
    """
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(max_results, ARXIV_MAX_RESULTS),
        "sortBy": "relevance",
        "sortOrder": "descending",
    }

    # Custom loop to handle strict 429 rate limits beyond the standard retry wrap
    for attempt in range(4):
        time.sleep(ARXIV_RATE_LIMIT_SLEEP)  # Respect arXiv rate limit policy
        
        response = requests.get(ARXIV_BASE_URL, params=params, timeout=20)
        
        if response.status_code == 429:
            logger.warning(f"ArXiv Rate Limit Exceeded (429). Cooling down for 10 seconds... (Attempt {attempt+1}/4)")
            time.sleep(10)
            continue
            
        response.raise_for_status()
        return _parse_arxiv_response(response.text)
        
    return []


def _parse_arxiv_response(xml_text: str) -> list[ArxivPaper]:
    """Parse arXiv Atom XML response into ArxivPaper list."""
    papers = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return papers

    for entry in root.findall("atom:entry", NS):
        try:
            paper = _parse_entry(entry)
            if paper:
                papers.append(paper)
        except Exception as e:
            logger.warning(f"Skipping malformed arXiv entry: {e}")
            continue

    return papers


def _parse_entry(entry: ET.Element) -> Optional[ArxivPaper]:
    """Extract fields from a single arXiv Atom entry."""
    # ID — format: http://arxiv.org/abs/XXXX.XXXXX
    raw_id = _text(entry, "atom:id", "")
    arxiv_id = re.sub(r'v\d+$', '', raw_id.split("/abs/")[-1]).strip()
    if not arxiv_id:
        return None

    title = _text(entry, "atom:title", "No title").replace("\n", " ").strip()
    abstract = _text(entry, "atom:summary", "").replace("\n", " ").strip()

    # Authors
    author_els = entry.findall("atom:author", NS)
    authors = ", ".join(
        _text(a, "atom:name", "Unknown") for a in author_els
    ) or "Unknown"

    # Year from published date
    published = _text(entry, "atom:published", "")
    year = published[:4] if published else "N/A"

    # URLs
    pdf_url = ""
    html_url = f"https://arxiv.org/abs/{arxiv_id}"
    for link in entry.findall("atom:link", NS):
        rel = link.get("rel", "")
        title_attr = link.get("title", "")
        href = link.get("href", "")
        if title_attr == "pdf" or (rel == "related" and "pdf" in href):
            pdf_url = href
    if not pdf_url:
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    # Categories
    cats = [c.get("term", "") for c in entry.findall("arxiv:primary_category", NS)]
    cats += [c.get("term", "") for c in entry.findall("atom:category", NS)]
    categories = list(set(c for c in cats if c))

    return ArxivPaper(
        arxiv_id=arxiv_id,
        title=title,
        authors=authors,
        year=year,
        abstract=abstract,
        pdf_url=pdf_url,
        html_url=html_url,
        categories=categories[:3],
    )


def _text(el: ET.Element, tag: str, default: str = "") -> str:
    found = el.find(tag, NS)
    return (found.text or default).strip() if found is not None else default
