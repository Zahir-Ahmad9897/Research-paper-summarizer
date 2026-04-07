<div align="center">
  <h1>Autonomous AI Research Engine</h1>
  <p>Generative AI pipeline for autonomous arXiv extraction and structural matrix parsing.</p>
  
  <img src="https://via.placeholder.com/800x400/1a1a2e/ffffff?text=[Insert+Dashboard+Screenshot+Here]" alt="UI Dashboard" width="80%">
  <br/><br/>
  
  <a href="https://fastapi.tiangolo.com"><img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi" /></a>
  <a href="https://groq.com"><img src="https://img.shields.io/badge/Groq_Llama_3.3-F55036?style=for-the-badge&logo=groq&logoColor=white" /></a>
  <a href="https://python.langchain.com/"><img src="https://img.shields.io/badge/LangChain-1C3C3C?style=for-the-badge&logo=langchain&logoColor=white" /></a>
  <a href="https://developer.mozilla.org/en-US/docs/Web/JavaScript"><img src="https://img.shields.io/badge/Vanilla_JS-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black" /></a>
</div>

## Overview
A high-performance Generative AI orchestrator designed to eliminate manual literature reviews. The system natively queries arXiv, splices raw PDF bytes, and forces Groq LLMs (Llama 3.3) to extract complex academic methodologies into strict JSON schemas, rendered on a decoupled front-end.

## Core Architecture

### Pipeline Workflow
```mermaid
 
    A
    [Input Query] --> B[Enhance Query via LLM]
    B --> C[User Selects Query]
    C --> D[Search arXiv API]
    D --> E[User Selects Paper]
    E --> F[Summarization via 70B LLM]
    F --> G[Matrix Table Generation]
```

- **API Core:** Asynchronous FastAPI backend managing pipeline states and data exports.
- **RAG & Extraction:** PyMuPDF context loading tightly constrained by custom token-truncation to organically bypass 12k TPM limits.
- **Deterministic Parsing:** LangChain `PydanticOutputParser` enforcing 18 immutable schema features per paper.
- **Network Resilience:** Custom exponential backoff algorithms defending against aggressive arXiv `HTTP 429` rate limits.
- **Micro-Frontend:** Vanilla HTML/JS implementation utilizing Glassmorphism design and deep horizontal CSS matrices.

## Quickstart

### 1. Environment
Requires `Python 3.10+`.

```bash
git clone https://github.com/your-username/ai-research-engine.git
cd ai-research-engine

python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

pip install -r requirements.txt
```

### 2. Configuration
The extraction engine requires a free Groq API key for Llama 3 inference. 
Create a `.env` file globally:
```env
GROQ_API_KEY=gsk_your_private_api_key_here
```

### 3. Deploy
```bash
uvicorn api:app --host 127.0.0.1 --port 8000
```
Application UI natively served at `http://localhost:8000/`.
