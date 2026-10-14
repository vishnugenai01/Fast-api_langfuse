"""Langfuse client configuration for the Food Ordering API."""
import os
from dotenv import load_dotenv
from langfuse import get_client

load_dotenv()

def _enabled() -> bool:
    """Tracing is enabled unless explicitly disabled in .env."""
    return os.getenv("LANGFUSE_TRACKER_ENABLED", "true").strip().lower() not in {
        "0", "false", "no", "off"
    }

LANGFUSE_ENABLED = _enabled()
langfuse = get_client() if LANGFUSE_ENABLED else None

def flush_langfuse() -> None:
    """Flush buffered observations during application shutdown."""
    if langfuse is not None:
        try:
            langfuse.flush()
        except Exception:
            # Observability must not prevent the API from shutting down.
            pass
