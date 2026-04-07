"""
tests/test_query.py — Unit tests for Query Enhancement Chain
Run: python -m pytest tests/test_query.py -v

All tests use mocked LLM calls so they work WITHOUT a Groq API key.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock


def _make_mock_llm(response_text: str):
    """Create a mock LLM that returns a fixed response when used in an LCEL chain."""
    mock_llm = MagicMock()
    mock_llm.__or__ = MagicMock(side_effect=lambda other: other)
    # When chain.invoke() is called, simulate the full LCEL pipeline
    return mock_llm


def test_enhance_query_returns_string():
    """enhance_query must return a non-empty string (mocked LLM)."""
    with patch("chains.query_enhance.get_llm") as mock_get_llm, \
         patch("chains.query_enhance._invoke_chain") as mock_invoke:
        mock_invoke.return_value = "deep learning facial recognition convolutional neural network biometric verification"
        from chains.query_enhance import enhance_query
        result = enhance_query("face recognition AI system")
        assert isinstance(result, str)
        assert len(result.strip()) > 5, "Enhanced query too short"


def test_enhance_query_no_generic_words():
    """Enhanced query should not contain obvious generic filler words (mocked LLM)."""
    with patch("chains.query_enhance.get_llm") as mock_get_llm, \
         patch("chains.query_enhance._invoke_chain") as mock_invoke:
        mock_invoke.return_value = "deep learning oncology medical imaging cancer detection convolutional neural network"
        from chains.query_enhance import enhance_query
        result = enhance_query("machine learning for cancer detection")
        generic = ["using", "system", "tool"]
        lower = result.lower()
        for word in generic:
            assert word not in lower, f"Generic word '{word}' found in enhanced query: {result}"


def test_build_search_variants():
    """build_search_variants must return 2–3 unique variants."""
    from chains.query_enhance import build_search_variants
    variants = build_search_variants("raw query", "enhanced academic keywords deep learning")
    assert len(variants) >= 2
    assert "raw query" in variants
    assert "enhanced academic keywords deep learning" in variants
    assert len(set(variants)) == len(variants), "Variants must be unique"


def test_build_search_variants_short_fallback():
    """build_search_variants should add a 3-word short variant if unique."""
    from chains.query_enhance import build_search_variants
    variants = build_search_variants("original", "alpha beta gamma delta epsilon")
    assert "alpha beta gamma" in variants, "Short variant should be included"
    assert len(variants) == 3


def test_enhance_query_is_shorter_than_50_words():
    """Enhanced query should be concise (mocked LLM)."""
    with patch("chains.query_enhance.get_llm") as mock_get_llm, \
         patch("chains.query_enhance._invoke_chain") as mock_invoke:
        mock_invoke.return_value = "transformer self-attention mechanism natural language processing sequence-to-sequence"
        from chains.query_enhance import enhance_query
        result = enhance_query("explain transformer architecture attention mechanism")
        words = result.split()
        assert len(words) <= 50, f"Enhanced query too long: {len(words)} words"


if __name__ == "__main__":
    # Quick smoke test without pytest
    print("Running smoke tests for query enhancement...")
    test_build_search_variants()
    test_build_search_variants_short_fallback()
    print("All query tests passed ✅")
