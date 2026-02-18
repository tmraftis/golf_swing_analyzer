"""Server-side Segment analytics for reliable event tracking.

Initializes the segment-analytics-python (v2) client with the SEGMENT_WRITE_KEY
env var.  No-ops when the key is missing (local dev).  All public functions
accept user_id as the first argument for Segment's identity resolution.
"""

import logging
import os

logger = logging.getLogger(__name__)

_client = None
_initialized = False


def _get_client():
    global _client, _initialized
    if _initialized:
        return _client

    _initialized = True
    write_key = os.environ.get("SEGMENT_WRITE_KEY")
    if not write_key:
        logger.info("SEGMENT_WRITE_KEY not set — analytics disabled")
        return None

    try:
        import segment.analytics as segment_analytics

        segment_analytics.write_key = write_key
        segment_analytics.max_queue_size = 10
        segment_analytics.send = True
        _client = segment_analytics
        logger.info("Segment analytics initialized (server-side)")
    except ImportError:
        logger.warning("segment-analytics-python not installed — analytics disabled")

    return _client


# ─── Typed tracking functions ─────────────────────────────────────


def track_upload_completed(
    user_id: str,
    upload_id: str,
    view: str,
    swing_type: str,
    file_size_bytes: int,
    content_type: str,
):
    client = _get_client()
    if client:
        client.track(user_id, "Upload Completed", {
            "upload_id": upload_id,
            "view": view,
            "swing_type": swing_type,
            "file_size_bytes": file_size_bytes,
            "content_type": content_type,
        })


def track_analysis_completed(
    user_id: str,
    upload_id: str,
    view: str,
    swing_type: str,
    processing_time_sec: float,
    similarity_score: int,
    top_faults: list[str],
):
    client = _get_client()
    if client:
        client.track(user_id, "Analysis Completed", {
            "upload_id": upload_id,
            "view": view,
            "swing_type": swing_type,
            "processing_time_sec": processing_time_sec,
            "similarity_score": similarity_score,
            "top_faults": top_faults,
        })


def track_analysis_failed(
    user_id: str,
    upload_id: str,
    view: str,
    swing_type: str,
    error_code: int,
    error_message: str,
):
    client = _get_client()
    if client:
        client.track(user_id, "Analysis Failed", {
            "upload_id": upload_id,
            "view": view,
            "swing_type": swing_type,
            "error_code": error_code,
            "error_message": error_message,
        })


def track_share_created(
    user_id: str,
    upload_id: str,
    share_token: str,
    view: str,
):
    client = _get_client()
    if client:
        client.track(user_id, "Share Created", {
            "upload_id": upload_id,
            "share_token": share_token,
            "view": view,
        })


def track_share_viewed(
    share_token: str,
    upload_id: str,
    view: str,
):
    """Track a public share page view. No user_id — uses anonymous_id."""
    client = _get_client()
    if client:
        client.track(
            None,
            "Share Viewed",
            {
                "share_token": share_token,
                "upload_id": upload_id,
                "view": view,
            },
            anonymous_id=f"share_{share_token}",
        )


def flush():
    """Flush pending events. Call during shutdown."""
    client = _get_client()
    if client:
        client.flush()
