"""
chains/output_parser.py — Structured Output Parser
Uses LangChain PydanticOutputParser to enforce all 17 table fields as clean JSON.
Includes retry logic: if JSON parsing fails on first attempt, sends corrective prompt.
"""

import json
import re
from typing import Optional

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

from models.paper_schema import PaperSummary, empty_summary
from utils.llm_factory import get_llm
from utils.logger import get_logger

logger = get_logger(__name__)


# Parser instance — reused across calls
parser = PydanticOutputParser(pydantic_object=PaperSummary)


SUMMARIZE_PROMPT = PromptTemplate(
    input_variables=["paper_text", "title", "authors", "year", "arxiv_id", "format_instructions"],
    template="""You are an expert academic researcher. Extract structured information from the research paper below.

Paper Metadata:
- Title: {title}
- Authors: {authors}
- Year: {year}
- arXiv ID: {arxiv_id}

Paper Content:
{paper_text}

Task: Extract ALL of the following fields from this paper. 
For any field not found in the paper, use exactly: "N/A — not reported"
Never leave a field empty. Be specific and accurate.

{format_instructions}

IMPORTANT:
- Output ONLY valid JSON matching the schema above
- Do not include any text before or after the JSON
- Use "N/A — not reported" for missing fields
- Include specific numbers for results_performance
- Keep each field concise but complete

JSON Output:"""
)


RETRY_PROMPT = PromptTemplate(
    input_variables=["broken_json", "format_instructions", "error"],
    template="""The previous JSON output was malformed. Fix it.

Error: {error}

Broken output:
{broken_json}

Correct it to match this exact schema:
{format_instructions}

Output ONLY valid JSON, nothing else:"""
)


def parse_paper(
    paper_text: str,
    title: str,
    authors: str,
    year: str,
    arxiv_id: str,
) -> tuple[PaperSummary, str]:
    """
    Run the summarization chain and return a parsed PaperSummary.

    Args:
        paper_text:  Full paper text (or fallback abstract text)
        title, authors, year, arxiv_id: Paper metadata

    Returns:
        Tuple of (PaperSummary, status)
        status: "success" | "retry_success" | "fallback"
    """
    llm = get_llm(mode="strong")
    format_instructions = parser.get_format_instructions()

    # Truncate paper text to avoid exceeding context window
    from config import TRUNCATE_MAX_CHARS
    truncated = _truncate_text(paper_text, max_chars=TRUNCATE_MAX_CHARS)

    # ── Attempt 1 ──────────────────────────────────────────────────────────────
    try:
        chain = SUMMARIZE_PROMPT | llm | StrOutputParser()
        raw_output = chain.invoke({
            "paper_text": truncated,
            "title": title,
            "authors": authors,
            "year": year,
            "arxiv_id": arxiv_id,
            "format_instructions": format_instructions,
        })
        summary = _try_parse(raw_output)
        if summary:
            return summary, "success"
    except Exception as e:
        logger.warning(f"First parse attempt failed for '{title}': {e}")
        raw_output = str(e)

    # ── Attempt 2: Retry with corrective prompt ─────────────────────────────
    try:
        retry_chain = RETRY_PROMPT | llm | StrOutputParser()
        retry_output = retry_chain.invoke({
            "broken_json": raw_output[:3000],
            "format_instructions": format_instructions,
            "error": "JSON could not be parsed",
        })
        summary = _try_parse(retry_output)
        if summary:
            return summary, "retry_success"
    except Exception as e:
        logger.warning(f"Retry parse also failed for '{title}': {e}")

    # ── Fallback: Return empty summary with known metadata ───────────────────
    logger.warning(f"All parse attempts failed for '{title}'. Returning empty summary.")
    return empty_summary(title=title, authors=authors, year=year, arxiv_id=arxiv_id), "fallback"


def _try_parse(raw: str) -> Optional[PaperSummary]:
    """Attempt to parse raw LLM output into PaperSummary. Returns None on failure."""
    # Extract JSON if wrapped in markdown fences
    json_str = _extract_json(raw)
    try:
        return parser.parse(json_str)
    except Exception:
        pass
    # Try direct JSON parse and construct PaperSummary
    try:
        data = json.loads(json_str)
        return PaperSummary(**data)
    except Exception:
        return None


def _extract_json(text: str) -> str:
    """Strip markdown code fences and extract raw JSON string."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    # Find first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def _truncate_text(text: str, max_chars: int = 12000) -> str:
    """
    Truncate paper text intelligently.
    Keeps: beginning (intro/abstract) + end (conclusion/results).
    Sacrifices: middle sections if too long.
    """
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    beginning = text[:half]
    ending = text[-half:]
    return beginning + "\n\n[... middle sections truncated for length ...]\n\n" + ending
