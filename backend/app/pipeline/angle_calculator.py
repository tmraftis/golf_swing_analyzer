"""Wrapper around scripts/calculate_angles.py for API use."""

import logging
import io
from contextlib import redirect_stdout

from app.paths import ensure_scripts_importable
from .models import AngleCalculationError

logger = logging.getLogger(__name__)

ensure_scripts_importable()

from calculate_angles import analyze_video as _analyze_video  # noqa: E402


def calculate_angles(
    landmarks_data: dict, phases: dict, view: str
) -> dict:
    """Calculate golf-specific angles at each swing phase.

    Args:
        landmarks_data: Dict with 'summary' and 'frames' keys.
        phases: Dict with phase frames from detect_swing_phases().
        view: 'dtl' or 'fo'.

    Returns:
        Dict keyed by phase name. Each value has 'frame',
        'timestamp_sec', 'description', and 'angles' dict.

    Raises:
        AngleCalculationError: If angles cannot be computed.
    """
    logger.info(f"Calculating angles for {view} view...")

    try:
        stdout_capture = io.StringIO()
        with redirect_stdout(stdout_capture):
            results = _analyze_video(landmarks_data, phases, view)
    except Exception as e:
        raise AngleCalculationError(view, "all", str(e))

    if not results:
        raise AngleCalculationError(
            view, "all", "No angle results produced"
        )

    logger.info(
        f"Angles calculated ({view}): "
        f"{len(results)} phases with angles"
    )

    return results
