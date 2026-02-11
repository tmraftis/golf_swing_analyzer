"""Wrapper around scripts/detect_phases.py for API use.

Catches SystemExit from the original script and converts to PipelineError.
"""

import sys
import os
import logging
import io
from contextlib import redirect_stdout

from .models import PhaseDetectionError

logger = logging.getLogger(__name__)

# Add scripts/ to path so we can import detect_phases
_scripts_dir = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "scripts"
)
if _scripts_dir not in sys.path:
    sys.path.insert(0, os.path.abspath(_scripts_dir))

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

    try:
        # Suppress print output from the script
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            phases = _detect_phases(landmarks_data, view=view)
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
