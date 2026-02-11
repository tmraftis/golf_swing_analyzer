"""Call Modal for GPU-accelerated parallel landmark extraction.

Sends both DTL and FO video bytes to Modal simultaneously, waits for
both results, and returns the landmark dicts. Falls back gracefully
if Modal is unavailable.
"""

import logging

from .models import LandmarkExtractionError

logger = logging.getLogger(__name__)


def extract_landmarks_parallel_modal(
    dtl_bytes: bytes,
    fo_bytes: bytes,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
    target_height: int = 960,
) -> tuple:
    """Extract landmarks from both videos in parallel via Modal.

    Args:
        dtl_bytes: Raw bytes of the DTL video file.
        fo_bytes: Raw bytes of the FO video file.
        frame_step: Process every Nth frame.
        min_detection_rate: Minimum acceptable detection rate.
        target_height: Downscale frames to this height before inference.

    Returns:
        Tuple of (dtl_landmarks, fo_landmarks) dicts.

    Raises:
        LandmarkExtractionError: If detection rate is too low for either video.
        Exception: If Modal call fails for any other reason.
    """
    import modal

    # Look up the deployed Modal function
    extract_fn = modal.Function.from_name(
        "pure-landmark-extractor", "extract_landmarks"
    )

    logger.info(
        f"Sending videos to Modal (DTL={len(dtl_bytes)/1e6:.1f}MB, "
        f"FO={len(fo_bytes)/1e6:.1f}MB)..."
    )

    # Spawn both extractions in parallel
    dtl_call = extract_fn.spawn(
        video_bytes=dtl_bytes,
        frame_step=frame_step,
        min_detection_rate=min_detection_rate,
        target_height=target_height,
    )
    fo_call = extract_fn.spawn(
        video_bytes=fo_bytes,
        frame_step=frame_step,
        min_detection_rate=min_detection_rate,
        target_height=target_height,
    )

    # Wait for both to complete
    dtl_result = dtl_call.get()
    fo_result = fo_call.get()

    # Check for extraction errors
    if "error" in dtl_result:
        raise LandmarkExtractionError("dtl", dtl_result.get("detection_rate", 0))
    if "error" in fo_result:
        raise LandmarkExtractionError("fo", fo_result.get("detection_rate", 0))

    logger.info(
        f"Modal extraction complete: "
        f"DTL={dtl_result['summary']['detected_frames']} frames, "
        f"FO={fo_result['summary']['detected_frames']} frames"
    )

    return dtl_result, fo_result
