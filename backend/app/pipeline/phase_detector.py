"""Wrapper around scripts/detect_phases.py for API use.

Catches SystemExit from the original script and converts to PipelineError.
"""

import logging
import io
from contextlib import redirect_stdout

from app.paths import ensure_scripts_importable
from .models import PhaseDetectionError

logger = logging.getLogger(__name__)

ensure_scripts_importable()

from detect_phases import detect_phases as _detect_phases  # noqa: E402


def detect_swing_phases(landmarks_data: dict, view: str) -> dict:
    """Detect the 4 swing phases from landmark data.

    Args:
        landmarks_data: Dict with 'summary' and 'frames' keys from
                        landmark extraction.
        view: 'dtl' or 'fo'.

    Returns:
        Dict with keys: address, top, impact, follow_through.
        Each value has 'frame' and 'description'.

    Raises:
        PhaseDetectionError: If phases cannot be detected.
    """
    logger.info(f"Detecting phases for {view} view...")

    # Debug: log landmark data summary
    total_frames = len(landmarks_data.get("frames", []))
    detected_count = sum(1 for f in landmarks_data.get("frames", []) if f.get("detected"))
    fps = landmarks_data.get("summary", {}).get("fps", 0)
    logger.info(
        f"{view}: {total_frames} total frames, {detected_count} detected, fps={fps}"
    )

    try:
        # Capture print output from the script for debug logging
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            phases = _detect_phases(landmarks_data, view=view)
        # Log captured output for debugging
        captured = stdout_capture.getvalue().strip()
        if captured:
            for line in captured.split("\n"):
                logger.info(f"{view} detect_phases: {line.strip()}")
    except SystemExit:
        raise PhaseDetectionError(
            view,
            "Could not detect top of backswing. Ensure the video "
            "contains a complete golf swing.",
        )
    except Exception as e:
        raise PhaseDetectionError(view, str(e))

    # Remove diagnostics from the result (internal use only)
    phases.pop("_diagnostics", None)

    # Snap phase frames to nearest detected frame so that
    # calculate_angles can always find valid landmark data.
    detected_frames = {
        f["frame"] for f in landmarks_data["frames"] if f["detected"]
    }
    for phase_name in list(phases.keys()):
        frame = phases[phase_name]["frame"]
        if frame not in detected_frames and detected_frames:
            nearest = min(detected_frames, key=lambda f: abs(f - frame))
            logger.info(
                f"{view}: Snapping {phase_name} frame {frame} -> {nearest} "
                f"(nearest detected)"
            )
            phases[phase_name]["frame"] = nearest

    # Validate that all phases were found
    for phase_name in ["address", "top", "impact", "follow_through"]:
        if phase_name not in phases:
            raise PhaseDetectionError(view, f"Missing phase: {phase_name}")
        if phases[phase_name]["frame"] <= 0 and phase_name != "address":
            logger.warning(f"{view}: {phase_name} frame is {phases[phase_name]['frame']}")

    logger.info(
        f"Phases detected ({view}): "
        + ", ".join(f"{k}={v['frame']}" for k, v in phases.items())
    )

    return phases
