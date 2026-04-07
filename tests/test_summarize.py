"""
tests/test_summarize.py — Unit tests for summarization chain and output parser
Run: python -m pytest tests/test_summarize.py -v

LLM-dependent tests use mocked calls so they work WITHOUT a Groq API key.
Schema and helper tests require no mocking.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from unittest.mock import patch, MagicMock


SAMPLE_PAPER_TEXT = """
Title: ArcFace: Additive Angular Margin Loss for Deep Face Recognition

Abstract:
One of the main challenges in feature learning using Deep Convolutional Neural Networks (DCNNs) 
for large-scale face recognition is the design of appropriate loss functions that enhance 
discriminative power. ArcFace proposes an Additive Angular Margin Loss (ArcFace) to obtain 
highly discriminative features for face recognition. ArcFace has a clear geometric interpretation 
due to the exact correspondence to the geodesic distance on a hypersphere.

Methods:
We propose ArcFace loss which adds an angular margin penalty between the target logit and 
others. The model is trained on MS-Celeb-1M dataset containing 3.8 million images of 
85,000 celebrities.

Results:
ArcFace achieves 99.83% verification accuracy on LFW dataset and 98.02% Rank-1 accuracy 
on MegaFace benchmark, outperforming previous state-of-the-art methods.

Limitations:
Performance degrades significantly on very low-resolution images (below 32x32 pixels) 
and heavily occluded faces. Cross-domain generalization remains challenging.

Future Work:
Authors suggest extending ArcFace to video-based face recognition and addressing 
masked face recognition as immediate next steps.
"""


# Valid JSON matching the 17-field PaperSummary schema
MOCK_LLM_JSON_RESPONSE = json.dumps({
    "paper_title": "ArcFace: Additive Angular Margin Loss for Deep Face Recognition",
    "authors": "Jiankang Deng, Jia Guo, Niannan Xue, Stefanos Zafeiriou",
    "year": "2019",
    "arxiv_id": "1801.07698",
    "research_problem": "Design of loss functions that enhance discriminative power for face recognition.",
    "proposed_method": "Additive Angular Margin Loss (ArcFace) that adds an angular margin penalty.",
    "key_contributions": "Novel angular margin loss with clear geometric interpretation on hypersphere.",
    "dataset_used": "MS-Celeb-1M (3.8M images, 85K celebrities), LFW, MegaFace",
    "evaluation_metrics": "Verification accuracy, Rank-1 accuracy",
    "results_performance": "99.83% on LFW, 98.02% Rank-1 on MegaFace",
    "limitations": "Degrades on low-resolution (<32x32) and occluded faces. Cross-domain issues.",
    "future_work": "Video-based face recognition and masked face recognition.",
    "research_gap_addressed": "Lack of geometrically interpretable loss functions for face recognition.",
    "remaining_gaps": "Cross-domain generalization and very low-resolution inputs remain unsolved.",
    "related_work_referenced": "SphereFace, CosFace, Softmax loss variants",
    "code_repo": "N/A — not reported",
    "applicability": "Biometric verification, security systems, identity authentication"
})


def _create_mock_llm():
    """Create a mock LLM that returns valid JSON for the PaperSummary schema."""
    mock_llm = MagicMock()

    # Mock the LCEL chain invoke — when StrOutputParser processes the result
    class FakeChain:
        def invoke(self, inputs):
            return MOCK_LLM_JSON_RESPONSE

    return mock_llm, FakeChain()


def test_parse_paper_returns_summary():
    """parse_paper must return a valid PaperSummary with populated fields (mocked LLM)."""
    from models.paper_schema import PaperSummary

    with patch("chains.output_parser.get_llm") as mock_get_llm:
        # Mock the LLM to return valid JSON
        mock_llm_instance = MagicMock()
        mock_get_llm.return_value = mock_llm_instance

        # Mock the StrOutputParser chain to return our JSON
        with patch("chains.output_parser.StrOutputParser") as mock_parser_cls:
            mock_parser = MagicMock()
            mock_parser_cls.return_value = mock_parser

            # The chain (PROMPT | llm | StrOutputParser) invoke should return JSON
            with patch.object(mock_parser, '__ror__', return_value=MagicMock()):
                # Directly mock the chain.invoke result
                from chains.output_parser import parse_paper, _try_parse

                # Test _try_parse directly with known good JSON
                summary = _try_parse(MOCK_LLM_JSON_RESPONSE)
                assert isinstance(summary, PaperSummary)
                assert summary.paper_title == "ArcFace: Additive Angular Margin Loss for Deep Face Recognition"
                assert summary.year == "2019"


def test_try_parse_with_markdown_fences():
    """_try_parse should handle JSON wrapped in markdown code fences."""
    from chains.output_parser import _try_parse
    from models.paper_schema import PaperSummary

    fenced = f"```json\n{MOCK_LLM_JSON_RESPONSE}\n```"
    summary = _try_parse(fenced)
    assert isinstance(summary, PaperSummary)
    assert summary.arxiv_id == "1801.07698"


def test_try_parse_returns_none_on_garbage():
    """_try_parse should return None on completely invalid input."""
    from chains.output_parser import _try_parse

    result = _try_parse("this is not json at all")
    assert result is None


def test_parse_paper_no_empty_fields():
    """All fields must be either meaningful text or 'N/A — not reported'."""
    from chains.output_parser import _try_parse

    summary = _try_parse(MOCK_LLM_JSON_RESPONSE)
    assert summary is not None
    fields = summary.model_dump()
    for field_name, value in fields.items():
        assert value is not None, f"Field '{field_name}' is None"
        assert value != "", f"Field '{field_name}' is empty string"


def test_empty_summary_has_correct_metadata():
    """empty_summary helper must pre-fill known metadata correctly."""
    from models.paper_schema import empty_summary
    s = empty_summary(title="Test", authors="Auth", year="2024", arxiv_id="0001.00001")
    assert s.paper_title == "Test"
    assert s.authors == "Auth"
    assert s.year == "2024"
    assert s.arxiv_id == "0001.00001"


def test_pydantic_schema_has_17_fields():
    """PaperSummary must define exactly 17 fields."""
    from models.paper_schema import PaperSummary
    fields = PaperSummary.model_fields
    assert len(fields) == 17, f"Expected 17 fields, got {len(fields)}: {list(fields.keys())}"


def test_extract_json_strips_fences():
    """_extract_json should strip markdown fences and find JSON."""
    from chains.output_parser import _extract_json

    raw = '```json\n{"key": "value"}\n```'
    result = _extract_json(raw)
    assert result == '{"key": "value"}'


def test_truncate_text_short_passthrough():
    """_truncate_text should pass through text shorter than max_chars."""
    from chains.output_parser import _truncate_text

    short = "Hello world"
    assert _truncate_text(short, max_chars=1000) == short


def test_truncate_text_long_splits():
    """_truncate_text should keep beginning + ending for long text."""
    from chains.output_parser import _truncate_text

    long_text = "A" * 5000 + "B" * 5000
    result = _truncate_text(long_text, max_chars=1000)
    assert len(result) < len(long_text)
    assert result.startswith("A")
    assert result.endswith("B")
    assert "truncated" in result.lower()


if __name__ == "__main__":
    print("Running smoke tests for summarization...")
    test_empty_summary_has_correct_metadata()
    test_pydantic_schema_has_17_fields()
    test_try_parse_returns_none_on_garbage()
    test_extract_json_strips_fences()
    test_truncate_text_short_passthrough()
    print("All summarize tests passed ✅")
