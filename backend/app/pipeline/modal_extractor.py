"""Call Modal for GPU-accelerated landmark extraction.

Supports both parallel dual-video extraction (DTL + FO simultaneously)
and single-video extraction. Falls back gracefully if Modal is unavailable.
"""

import logging

from .models import LandmarkExtractionError

logger = logging.getLogger(__name__)


def extract_landmarks_single_modal(
    video_bytes: bytes,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
    target_height: int = 960,
) -> dict:
    """Extract landmarks from a single video via Modal.

    Args:
        video_bytes: Raw bytes of the video file.
        frame_step: Process every Nth frame.
        min_detection_rate: Minimum acceptable detection rate.
        target_height: Downscale frames to this height before inference.

    Returns:
        Landmark dict with 'summary' and 'frames' keys.

    Raises:
        LandmarkExtractionError: If detection rate is too low after retry.
        Exception: If Modal call fails for any other reason.
    """
    import modal

    extract_fn = modal.Function.from_name(
        "pure-landmark-extractor", "extract_landmarks"
    )

    logger.info(f"Sending video to Modal ({len(video_bytes)/1e6:.1f}MB)...")

    result = extract_fn.remote(
        video_bytes=video_bytes,
        frame_step=frame_step,
        min_detection_rate=min_detection_rate,
        target_height=target_height,
    )

    # Retry once with lower threshold if detection rate too low
    if "error" in result:
        retry_rate = 0.5
        logger.info(
            f"Detection rate {result.get('detection_rate', 0)}% "
            f"below threshold, retrying with {retry_rate}..."
        )
        result = extract_fn.remote(
            video_bytes=video_bytes,
            frame_step=frame_step,
            min_detection_rate=retry_rate,
            target_height=target_height,
        )

    if "error" in result:
        raise LandmarkExtractionError("video", result.get("detection_rate", 0))

    logger.info(
        f"Modal extraction complete: "
        f"{result['summary']['detected_frames']} frames detected"
    )

    return result


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

    # Check for extraction errors — retry failed videos once with lower threshold
    dtl_failed = "error" in dtl_result
    fo_failed = "error" in fo_result

    if dtl_failed or fo_failed:
        retry_rate = 0.5  # lower threshold for retry attempt

        if dtl_failed:
            logger.info(
                f"DTL detection rate {dtl_result.get('detection_rate', 0)}% "
                f"below threshold, retrying..."
            )
            dtl_call = extract_fn.spawn(
                video_bytes=dtl_bytes,
                frame_step=frame_step,
                min_detection_rate=retry_rate,
                target_height=target_height,
            )

        if fo_failed:
            logger.info(
                f"FO detection rate {fo_result.get('detection_rate', 0)}% "
                f"below threshold, retrying..."
            )
            fo_call = extract_fn.spawn(
                video_bytes=fo_bytes,
                frame_step=frame_step,
                min_detection_rate=retry_rate,
                target_height=target_height,
            )

        if dtl_failed:
            dtl_result = dtl_call.get()
        if fo_failed:
            fo_result = fo_call.get()

    # Final error check after possible retry
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
