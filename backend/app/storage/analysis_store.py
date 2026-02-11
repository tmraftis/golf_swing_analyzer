"""In-memory cache for analysis results."""

import logging

logger = logging.getLogger(__name__)

# Simple in-memory store: upload_id → analysis result dict
_results: dict[str, dict] = {}


def save_result(upload_id: str, result: dict) -> None:
    """Cache an analysis result."""
    _results[upload_id] = result
    logger.info(f"Cached analysis result for {upload_id}")


def get_result(upload_id: str) -> dict | None:
    """Retrieve a cached analysis result, or None if not found."""
    return _results.get(upload_id)


def has_result(upload_id: str) -> bool:
    """Check if we have a cached result for this upload."""
    return upload_id in _results
