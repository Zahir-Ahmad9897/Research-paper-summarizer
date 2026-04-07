"""
export/to_markdown.py — Export researcher table as Markdown (.md)
"""

import os
from datetime import datetime
from models.paper_schema import PaperSummary
from config import EXPORT_DIR


def export_markdown(summaries: list[PaperSummary], query: str = "", enhanced_query: str = "") -> str:
    """
    Export list of PaperSummary objects to a Markdown file.

    Returns:
        File path of the created .md file
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    content = _build_markdown(summaries, query, enhanced_query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_summary_{timestamp}.md"
    filepath = os.path.join(EXPORT_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def summaries_to_markdown_string(summaries: list[PaperSummary], query: str = "", enhanced_query: str = "") -> str:
    """Return the Markdown content as a string (for Streamlit download button)."""
    return _build_markdown(summaries, query, enhanced_query)


def _build_markdown(summaries: list[PaperSummary], query: str, enhanced_query: str) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# AI Research Paper Summary Report",
        f"\n**Generated:** {timestamp}  ",
        f"**Query:** {query}  ",
        f"**Enhanced Query:** {enhanced_query}  ",
        f"**Papers Summarized:** {len(summaries)}",
        "\n---\n",
    ]

    for i, s in enumerate(summaries, 1):
        lines += [
            f"## {i}. {s.paper_title}",
            f"\n| Field | Value |",
            "| --- | --- |",
            f"| **Authors** | {s.authors} |",
            f"| **Year** | {s.year} |",
            f"| **arXiv ID** | {s.arxiv_id} |",
            f"| **Summary** | {s.summary} |",
            f"| **Research Problem** | {s.research_problem} |",
            f"| **Proposed Method** | {s.proposed_method} |",
            f"| **Key Contributions** | {s.key_contributions} |",
            f"| **Dataset Used** | {s.dataset_used} |",
            f"| **Evaluation Metrics** | {s.evaluation_metrics} |",
            f"| **Results / Performance** | {s.results_performance} |",
            f"| **Limitations** | {s.limitations} |",
            f"| **Future Work** | {s.future_work} |",
            f"| **Research Gap Addressed** | {s.research_gap_addressed} |",
            f"| **Remaining Gaps** | {s.remaining_gaps} |",
            f"| **Related Work** | {s.related_work_referenced} |",
            f"| **Code / Repo** | {s.code_repo} |",
            f"| **Applicability** | {s.applicability} |",
            "\n---\n",
        ]

    return "\n".join(lines)
