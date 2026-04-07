"""
utils/validators.py — Input validation helpers
Used by app.py and pipeline modules to validate user inputs
before passing them into the processing chain.
"""

from config import ARXIV_MIN_PAPERS, ARXIV_MAX_PAPERS


class ValidationError(Exception):
    """Raised when user input fails validation."""
    pass


def validate_query(raw_query: str) -> str:
    """
    Validate and clean a raw user query.

    Args:
        raw_query: Raw string from the UI input

    Returns:
        Cleaned query string

    Raises:
        ValidationError: If query is empty or too short
    """
    cleaned = raw_query.strip()
    if not cleaned:
        raise ValidationError("Query cannot be empty. Please enter a research topic.")
    if len(cleaned) < 3:
        raise ValidationError("Query is too short. Please enter at least 3 characters.")
    if len(cleaned) > 500:
        raise ValidationError("Query is too long. Please keep it under 500 characters.")
    return cleaned


def validate_paper_selection(selected_indices: list[int], total_available: int) -> list[int]:
    """
    Validate the user's paper selection.

    Args:
        selected_indices: List of selected paper indices
        total_available:  Total papers returned by arXiv search

    Returns:
        Validated list of indices

    Raises:
        ValidationError: If selection count is out of bounds
    """
    if not selected_indices:
        raise ValidationError(
            f"Please select at least {ARXIV_MIN_PAPERS} paper to summarize."
        )
    if len(selected_indices) > ARXIV_MAX_PAPERS:
        raise ValidationError(
            f"Please select at most {ARXIV_MAX_PAPERS} papers. "
            f"You selected {len(selected_indices)}."
        )
    invalid = [i for i in selected_indices if i < 0 or i >= total_available]
    if invalid:
        raise ValidationError(f"Invalid paper indices: {invalid}")
    return selected_indices


def validate_groq_key(api_key: str) -> bool:
    """
    Basic check that a Groq API key looks valid (non-empty, starts with 'gsk_').
    Does NOT make a network call — just format validation.
    """
    if not api_key:
        return False
    return api_key.startswith("gsk_") and len(api_key) > 20


def sanitize_filename(name: str, max_len: int = 60) -> str:
    """
    Remove characters that are invalid in filenames.
    Used by export modules.
    """
    import re
    safe = re.sub(r'[\\/*?:"<>|]', "_", name)
    safe = safe.strip(". ")
    return safe[:max_len] if len(safe) > max_len else safe
