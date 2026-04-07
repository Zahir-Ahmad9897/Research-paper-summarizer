"""
utils/retry.py — Retry decorator for network and LLM calls
Used by arXiv search, PDF fetch, and LLM chain calls.
Implements exponential backoff with configurable max attempts.
"""

import time
import functools
from typing import Callable, Type, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)


def retry(
    max_attempts: int = 3,
    delay: float = 2.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_fail_return=None,
):
    """
    Decorator: retry a function up to max_attempts times with exponential backoff.

    Args:
        max_attempts:   Maximum number of attempts (including first try)
        delay:          Initial delay between retries in seconds
        backoff:        Multiply delay by this factor on each retry
        exceptions:     Exception types to catch and retry on
        on_fail_return: Value to return if all attempts fail (None = re-raise)

    Usage:
        @retry(max_attempts=3, delay=2.0, exceptions=(requests.RequestException,))
        def fetch_from_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        logger.warning(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        if on_fail_return is not None:
                            return on_fail_return
                        raise
                    logger.info(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {current_delay:.1f}s…"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            if on_fail_return is not None:
                return on_fail_return
            raise last_exception

        return wrapper
    return decorator
