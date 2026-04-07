"""
export/to_pdf.py — Export researcher table as PDF report
Uses pdfkit (wkhtmltopdf) to render HTML → PDF.
Falls back to a plain-text .txt file if pdfkit is not available.
"""

import os
from datetime import datetime
from models.paper_schema import PaperSummary
from config import EXPORT_DIR
from utils.logger import get_logger

logger = get_logger(__name__)


def export_pdf(summaries: list[PaperSummary], query: str = "", enhanced_query: str = "") -> str:
    """
    Export list of PaperSummary objects to a PDF report.

    Returns:
        File path of the created PDF (or .txt fallback)
    """
    os.makedirs(EXPORT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    html_content = _build_html(summaries, query, enhanced_query, timestamp)

    try:
        import pdfkit
        filename = f"research_summary_{timestamp}.pdf"
        filepath = os.path.join(EXPORT_DIR, filename)
        options = {
            "page-size": "A4",
            "margin-top": "15mm",
            "margin-bottom": "15mm",
            "margin-left": "15mm",
            "margin-right": "15mm",
            "encoding": "UTF-8",
            "quiet": "",
        }
        pdfkit.from_string(html_content, filepath, options=options)
        return filepath
    except Exception as e:
        logger.warning(f"pdfkit PDF generation failed: {e}. Falling back to HTML.")
        # Fallback: save as HTML
        filename = f"research_summary_{timestamp}.html"
        filepath = os.path.join(EXPORT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        return filepath


def summaries_to_html_string(summaries: list[PaperSummary], query: str = "", enhanced_query: str = "") -> str:
    """Return HTML string for Streamlit download button."""
    return _build_html(summaries, query, enhanced_query, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


def _build_html(summaries: list[PaperSummary], query: str, enhanced_query: str, timestamp: str) -> str:
    rows_html = ""
    for i, s in enumerate(summaries, 1):
        fields = [
            ("Authors", s.authors),
            ("Year", s.year),
            ("arXiv ID", s.arxiv_id),
            ("Summary", s.summary),
            ("Research Problem", s.research_problem),
            ("Proposed Method", s.proposed_method),
            ("Key Contributions", s.key_contributions),
            ("Dataset Used", s.dataset_used),
            ("Evaluation Metrics", s.evaluation_metrics),
            ("Results / Performance", s.results_performance),
            ("Limitations", s.limitations),
            ("Future Work", s.future_work),
            ("Research Gap Addressed", s.research_gap_addressed),
            ("Remaining Gaps", s.remaining_gaps),
            ("Related Work Referenced", s.related_work_referenced),
            ("Code / Repo", s.code_repo),
            ("Applicability", s.applicability),
        ]
        field_rows = "".join(
            f"<tr><td class='label'>{k}</td><td>{v}</td></tr>" for k, v in fields
        )
        rows_html += f"""
        <div class="paper">
          <h2>{i}. {s.paper_title}</h2>
          <table>{field_rows}</table>
        </div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Research Summary Report</title>
<style>
  body {{ font-family: Arial, sans-serif; font-size: 12px; color: #1a1a1a; margin: 0; padding: 20px; }}
  h1 {{ color: #1d3557; font-size: 20px; border-bottom: 2px solid #1d3557; padding-bottom: 8px; }}
  h2 {{ color: #1d3557; font-size: 14px; margin-top: 24px; margin-bottom: 8px; }}
  .meta {{ color: #555; font-size: 11px; margin-bottom: 16px; }}
  .paper {{ margin-bottom: 32px; page-break-inside: avoid; }}
  table {{ width: 100%; border-collapse: collapse; }}
  td {{ border: 1px solid #ddd; padding: 6px 10px; vertical-align: top; }}
  td.label {{ font-weight: bold; width: 28%; background: #f0f4f8; color: #1d3557; white-space: nowrap; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
</style>
</head>
<body>
<h1>AI Research Paper Summary Report</h1>
<div class="meta">
  <strong>Generated:</strong> {timestamp} &nbsp;|&nbsp;
  <strong>Query:</strong> {query} &nbsp;|&nbsp;
  <strong>Enhanced Query:</strong> {enhanced_query} &nbsp;|&nbsp;
  <strong>Papers:</strong> {len(summaries)}
</div>
<hr>
{rows_html}
</body>
</html>"""
