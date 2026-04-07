"""
chains/query_enhance.py — Step 1: Query Enhancement Chain
Takes a plain user query and rewrites it as precise academic search keywords
using a fast free LLM (Groq Llama 3.1 8B by default).

Input:  raw_query (str)  — e.g. "face recognition AI system"
Output: enhanced_query (str) — e.g. "deep learning facial recognition CNN biometric"
"""

import json
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from utils.llm_factory import get_llm
from utils.retry import retry
from utils.logger import get_logger

logger = get_logger(__name__)


ENHANCE_PROMPT = PromptTemplate(
    input_variables=["raw_query"],
    template="""You are an expert academic search assistant.

Your task: Rewrite the user's plain query into 3 distinct and precise academic search keyword variations suitable for searching arXiv.

Rules:
- Output ONLY a valid JSON list of exactly 3 strings. No explanation.
- Each string should use 4 to 8 specific technical keywords.
- Include synonyms and related academic terms.
- Do NOT include generic words like "system", "AI", "tool", or "using".
- Ensure the variations explore different aspects of the query.

User query: {raw_query}

JSON Output:"""
)


def enhance_query(raw_query: str) -> list[str]:
    """
    Enhance a plain user query into precise academic search terms.

    Args:
        raw_query: Plain language query from the user

    Returns:
        List of enhanced query strings ready for arXiv search

    Raises:
        Exception: If LLM call fails after retries (caller handles gracefully)
    """
    llm = get_llm(mode="fast")
    chain = ENHANCE_PROMPT | llm | StrOutputParser()
    enhanced_str = _invoke_chain(chain, raw_query)
    
    try:
        import re
        match = re.search(r"\[.*\]", enhanced_str, re.DOTALL)
        if match:
            enhanced_str = match.group(0)
        variants = json.loads(enhanced_str)
        if isinstance(variants, list) and len(variants) > 0:
            logger.info(f"Query enhanced into {len(variants)} variants.")
            return [str(v).strip() for v in variants[:3]]
    except Exception as e:
        logger.warning(f"Failed to parse enhanced queries as JSON: {e}")
        
    # Fallback parsing
    fallback = enhanced_str.replace('"', '').replace('[', '').replace(']', '').split('\\n')
    fallback = [f.strip() for f in fallback if f.strip() and len(f.strip()) > 5]
    if fallback:
        return fallback[:3]
    return [raw_query]


@retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
def _invoke_chain(chain, raw_query: str) -> str:
    """Invoke the enhancement chain with retry for transient LLM failures."""
    result = chain.invoke({"raw_query": raw_query})
    return result.strip()


def build_search_variants(raw_query: str, enhanced_query: str) -> list[str]:
    """
    Return up to 3 search variants to try if primary search returns no results.
    Priority: enhanced → raw → first 3 words of enhanced.
    """
    variants = [enhanced_query, raw_query]
    short = " ".join(enhanced_query.split()[:3])
    if short not in variants:
        variants.append(short)
    return variants
