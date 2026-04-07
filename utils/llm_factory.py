"""
utils/llm_factory.py
Returns the correct LangChain LLM instance based on config.py.
Switching from free models to production: change config.py only.
Supports: Groq (cloud free), Ollama (local free), Custom (production).
"""

from config import (
    LLM_PROVIDER, LLM_MODEL_FAST, LLM_MODEL_STRONG,
    GROQ_API_KEY, OLLAMA_BASE_URL, OLLAMA_MODEL,
    ENABLE_CACHE, CACHE_PATH,
    LLM_TEMPERATURE, LLM_MAX_TOKENS,
)
from utils.logger import get_logger

logger = get_logger(__name__)


def _setup_cache():
    """Enable SQLite LLM response cache if configured."""
    if not ENABLE_CACHE:
        return
    try:
        from langchain.globals import set_llm_cache
        from langchain_community.cache import SQLiteCache
        import os
        os.makedirs("cache", exist_ok=True)
        set_llm_cache(SQLiteCache(database_path=CACHE_PATH))
    except Exception as e:
        logger.warning(f"Could not enable LLM cache: {e}")


_cache_initialized = False


def get_llm(mode: str = "strong"):
    """
    Return a LangChain-compatible LLM instance.

    Args:
        mode: "fast" (query enhancement) or "strong" (summarization)

    Returns:
        LangChain BaseChatModel instance
    """
    global _cache_initialized
    if not _cache_initialized:
        _setup_cache()
        _cache_initialized = True

    model_name = LLM_MODEL_FAST if mode == "fast" else LLM_MODEL_STRONG

    if LLM_PROVIDER == "groq":
        return _get_groq_llm(model_name)
    elif LLM_PROVIDER == "ollama":
        return _get_ollama_llm()
    elif LLM_PROVIDER == "custom":
        return _get_custom_llm(model_name)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Check config.py.")


def _get_groq_llm(model_name: str):
    """Groq cloud — free tier. Fast and capable."""
    try:
        from langchain_groq import ChatGroq
        if not GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY not set. Add it to your .env file.\n"
                "Get a free key at: https://console.groq.com"
            )
        return ChatGroq(
            model=model_name,
            api_key=GROQ_API_KEY,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
    except ImportError:
        raise ImportError("Run: pip install langchain-groq")


def _get_ollama_llm():
    """Ollama local — zero cost, zero internet needed."""
    try:
        from langchain_community.llms import Ollama
        return Ollama(
            base_url=OLLAMA_BASE_URL,
            model=OLLAMA_MODEL,
            temperature=LLM_TEMPERATURE,
        )
    except ImportError:
        raise ImportError("Run: pip install langchain-community && ollama pull mistral")


def _get_custom_llm(model_name: str):
    """
    Production custom model endpoint.
    Replace this with your fine-tuned model integration.
    Must return a LangChain-compatible chat model.
    """
    raise NotImplementedError(
        "Custom production model not configured. "
        "Implement _get_custom_llm() in utils/llm_factory.py "
        "or update config.py to use 'groq' or 'ollama'."
    )
