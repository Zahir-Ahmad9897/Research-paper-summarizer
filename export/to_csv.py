"""
export/to_csv.py — Export researcher table as CSV
"""

import os
import pandas as pd
from datetime import datetime
from models.paper_schema import PaperSummary
from config import EXPORT_DIR


def export_csv(summaries: list[PaperSummary], query: str = "") -> str:
    """
    Export list of PaperSummary objects to a CSV file.

    Returns:
        File path of the created CSV
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    df = _to_dataframe(summaries)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"research_summary_{timestamp}.csv"
    filepath = os.path.join(EXPORT_DIR, filename)
    df.to_csv(filepath, index=False, encoding="utf-8")
    return filepath


def summaries_to_dataframe(summaries: list[PaperSummary]) -> pd.DataFrame:
    """Convert PaperSummary list to DataFrame. Used by Streamlit display."""
    return _to_dataframe(summaries)


def _to_dataframe(summaries: list[PaperSummary]) -> pd.DataFrame:
    rows = []
    for s in summaries:
        rows.append({
            "Paper Title": s.paper_title,
            "Authors": s.authors,
            "Year": s.year,
            "arXiv ID": s.arxiv_id,
            "Summary": s.summary,
            "Research Problem": s.research_problem,
            "Proposed Method": s.proposed_method,
            "Key Contributions": s.key_contributions,
            "Dataset Used": s.dataset_used,
            "Evaluation Metrics": s.evaluation_metrics,
            "Results / Performance": s.results_performance,
            "Limitations": s.limitations,
            "Future Work": s.future_work,
            "Research Gap Addressed": s.research_gap_addressed,
            "Remaining Gaps": s.remaining_gaps,
            "Related Work Referenced": s.related_work_referenced,
            "Code / Repo": s.code_repo,
            "Applicability": s.applicability,
        })
    return pd.DataFrame(rows)
