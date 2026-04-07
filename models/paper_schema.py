"""
models/paper_schema.py
Pydantic schema enforcing all 17 researcher-grade table fields.
Used by PydanticOutputParser in the summarization chain.
If a field is not found in the paper, value must be "N/A — not reported".
"""

from pydantic import BaseModel, Field
from typing import Optional


NA = "N/A — not reported"


class PaperSummary(BaseModel):
    """All 17 researcher-grade output table fields. Enforced strictly."""

    # ── Essential fields ──────────────────────────────────────────────────────
    paper_title: str = Field(
        description="Full title of the research paper exactly as stated.",
        default=NA,
    )
    authors: str = Field(
        description="All author names separated by commas.",
        default=NA,
    )
    year: str = Field(
        description="Publication year (4-digit integer as string).",
        default=NA,
    )
    arxiv_id: str = Field(
        description="arXiv ID (e.g. 1801.07698) or DOI if arXiv ID unavailable.",
        default=NA,
    )
    summary: str = Field(
        description="A comprehensive summary of the paper including context, methods, and results.",
        default=NA,
    )
    research_problem: str = Field(
        description="The specific problem this paper sets out to solve. 1–3 sentences.",
        default=NA,
    )
    proposed_method: str = Field(
        description="Core technique, model, or algorithm proposed. 1–3 sentences.",
        default=NA,
    )
    key_contributions: str = Field(
        description="What is new or novel about this paper. Bullet-style, 1–4 points.",
        default=NA,
    )
    dataset_used: str = Field(
        description="Name and size of dataset(s) used for training and/or evaluation.",
        default=NA,
    )
    evaluation_metrics: str = Field(
        description="Metrics used to evaluate the method (e.g., Accuracy, F1, mAP, BLEU).",
        default=NA,
    )
    results_performance: str = Field(
        description="Quantitative results reported in the paper. Include specific numbers.",
        default=NA,
    )
    limitations: str = Field(
        description="Weaknesses, constraints, or failure cases acknowledged by the authors.",
        default=NA,
    )
    future_work: str = Field(
        description="What the authors suggest as directions for future research.",
        default=NA,
    )
    research_gap_addressed: str = Field(
        description="Which specific gap in prior work does this paper fill?",
        default=NA,
    )
    remaining_gaps: str = Field(
        description="Gaps that still exist in this area even after this paper's contribution.",
        default=NA,
    )

    # ── Optional fields ───────────────────────────────────────────────────────
    related_work_referenced: Optional[str] = Field(
        description="Key prior papers or methods cited by this paper.",
        default=NA,
    )
    code_repo: Optional[str] = Field(
        description="GitHub or project URL if provided by the authors.",
        default=NA,
    )
    applicability: Optional[str] = Field(
        description="Real-world domains or applications where this method can be used.",
        default=NA,
    )

    class Config:
        populate_by_name = True


def empty_summary(title: str = NA, authors: str = NA, year: str = NA, arxiv_id: str = NA) -> PaperSummary:
    """Return a blank PaperSummary pre-filled with known metadata and N/A for the rest."""
    return PaperSummary(
        paper_title=title,
        authors=authors,
        year=year,
        arxiv_id=arxiv_id,
    )
