"""
config.py — Central configuration for AI Research Paper Summarizer
To switch from free dev models to production: change the two lines marked PRODUCTION.
No other file needs to change.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Model Configuration ───────────────────────────────────────────────────────────────────
# During development and testing — FREE
LLM_PROVIDER = "groq"                          # "groq" | "ollama" | "custom"
LLM_MODEL_FAST = "llama-3.1-8b-instant"        # Query enhancement (fast)
LLM_MODEL_STRONG = "llama-3.3-70b-versatile"   # Summarization (strong)
LLM_TEMPERATURE = 0                            # Deterministic for structured extraction
LLM_MAX_TOKENS = 2048                          # Max tokens per LLM response

# PRODUCTION — uncomment these two lines at deployment:
# LLM_PROVIDER = "custom"
# LLM_MODEL_STRONG = "your-finetuned-model-endpoint"

# ─── API Keys ─────────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")   # Set in .env file

# ─── Ollama (local fallback) ───────────────────────────────────────────────────
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "mistral"

# ─── arXiv Settings ───────────────────────────────────────────────────────────
ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
ARXIV_MAX_RESULTS = 10          # Results fetched per search
ARXIV_RATE_LIMIT_SLEEP = 3      # Seconds between requests (arXiv policy)
ARXIV_MIN_PAPERS = 1
ARXIV_MAX_PAPERS = 5

# ─── Text Processing ──────────────────────────────────────────────────────────
CHUNK_SIZE = 1000               # Tokens per chunk
CHUNK_OVERLAP = 150             # Overlap between chunks
MAX_CHUNKS_PER_PAPER = 20       # Safety cap to avoid runaway processing
TRUNCATE_MAX_CHARS = 24000      # Max chars sent to LLM natively (Large Context mode)
# ─── Cache ────────────────────────────────────────────────────────────────────
CACHE_PATH = "cache/llm_cache.db"
ENABLE_CACHE = True

# ─── Export ───────────────────────────────────────────────────────────────────
EXPORT_DIR = "exports"

# ─── Retry Settings ─────────────────────────────────────────────────────────────────
RETRY_MAX_ATTEMPTS = 3
RETRY_INITIAL_DELAY = 2.0       # Seconds
RETRY_BACKOFF_FACTOR = 2.0

# ─── UI ───────────────────────────────────────────────────────────────────────
APP_TITLE = "AI Research Paper Summarizer"
APP_ICON = "🔬"
