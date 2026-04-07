import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List

from chains.query_enhance import enhance_query
from arxiv.search import search_arxiv, ArxivPaper
from chains.summarize import summarize_paper

app = FastAPI(title="AI Research Summarizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhanceRequest(BaseModel):
    query: str

class EnhanceResponse(BaseModel):
    variants: List[str]

class SearchRequest(BaseModel):
    query: str

class SearchResponse(BaseModel):
    papers: List[dict]

class SummarizeRequest(BaseModel):
    papers: List[dict]

class SummarizeResponse(BaseModel):
    summaries: List[dict]

@app.post("/api/enhance", response_model=EnhanceResponse)
def enhance(req: EnhanceRequest):
    try:
        variants = enhance_query(req.query.strip())
        return {"variants": variants}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search", response_model=SearchResponse)
def search(req: SearchRequest):
    try:
        results = search_arxiv(req.query.strip())
        papers = []
        for r in results:
            papers.append({
                "arxiv_id": getattr(r, "arxiv_id", ""),
                "title": getattr(r, "title", ""),
                "authors": getattr(r, "authors", ""),
                "year": getattr(r, "year", ""),
                "abstract": getattr(r, "abstract", ""),
                "pdf_url": getattr(r, "pdf_url", ""),
                "html_url": getattr(r, "html_url", ""),
                "categories": getattr(r, "categories", [])
            })
        return {"papers": papers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/summarize", response_model=SummarizeResponse)
def summarize(req: SummarizeRequest):
    try:
        summaries_list = []
        for p_dict in req.papers:
            # Reconstruct ArxivPaper
            paper = ArxivPaper(
                arxiv_id=p_dict.get("arxiv_id", ""),
                title=p_dict.get("title", ""),
                authors=p_dict.get("authors", ""),
                year=p_dict.get("year", ""),
                abstract=p_dict.get("abstract", ""),
                pdf_url=p_dict.get("pdf_url", ""),
                html_url=p_dict.get("html_url", ""),
                categories=p_dict.get("categories", []),
            )
            summary, run_info = summarize_paper(paper)
            # summary is a Pydantic object
            summaries_list.append(summary.model_dump() if hasattr(summary, "model_dump") else summary.dict())
            
        return {"summaries": summaries_list}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ─── Exports ────────────────────────────────────────────────────────────
from fastapi.responses import StreamingResponse
import io

class ExportRequest(BaseModel):
    summaries: List[dict]

@app.post("/api/export/csv")
def export_csv(req: ExportRequest):
    try:
        from models.paper_schema import PaperSummary
        from export.to_csv import summaries_to_dataframe
        pydantic_summaries = [PaperSummary(**s) for s in req.summaries]
        df = summaries_to_dataframe(pydantic_summaries)
        
        stream = io.StringIO()
        df.to_csv(stream, index=False)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/csv")
        response.headers["Content-Disposition"] = "attachment; filename=research_summary.csv"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/markdown")
def export_markdown(req: ExportRequest):
    try:
        from models.paper_schema import PaperSummary
        from export.to_markdown import _build_markdown
        pydantic_summaries = [PaperSummary(**s) for s in req.summaries]
        md_content = _build_markdown(pydantic_summaries)
        
        stream = io.StringIO()
        stream.write(md_content)
        response = StreamingResponse(iter([stream.getvalue()]), media_type="text/markdown")
        response.headers["Content-Disposition"] = "attachment; filename=research_summary.md"
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ─── Static ────────────────────────────────────────────────────────────
# Mount frontend
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_index():
    return FileResponse("frontend/index.html")
