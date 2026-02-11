"""Load and cache Tiger Woods reference data for comparison."""

import json
import logging
from functools import lru_cache
from pathlib import Path

from .models import PipelineError

logger = logging.getLogger(__name__)

# Project root — check local dev (4 levels up) and Docker (3 levels up)
_candidates = [
    Path(__file__).parent.parent.parent.parent,  # local dev: backend/app/pipeline -> repo root
    Path(__file__).parent.parent.parent,          # Docker: /app/app/pipeline -> /app
]
PROJECT_ROOT = next((p for p in _candidates if (p / "reference_data").is_dir()), _candidates[0])
REFERENCE_DATA_DIR = PROJECT_ROOT / "reference_data"

# Map from reference JSON angle names to calculate_angles.py output names.
# The reference data was built with slightly different naming conventions.
DTL_ANGLE_MAP = {
    "spine_angle": "spine_angle_dtl",
    "lead_arm_torso": "lead_arm_torso",
    "trail_arm_torso": "trail_arm_torso",
    "right_elbow": "right_elbow",
    "left_elbow": "left_elbow",
    "right_knee_flex": "right_knee_flex",
    "right_wrist_cock": "right_wrist_cock",
}

FO_ANGLE_MAP = {
    "shoulder_line_angle": "shoulder_line_angle",
    "hip_line_angle": "hip_line_angle",
    "x_factor": "x_factor",
    "spine_tilt": "spine_tilt_fo",
    "lead_arm_torso": "lead_arm_torso",
    "right_knee_flex": "right_knee_flex",
    "left_knee_flex": "left_knee_flex",
    "right_elbow": "right_elbow",
    "left_elbow": "left_elbow",
}


def _file_for_view(swing_type: str, view: str) -> Path:
    """Get the reference file path for a swing type and view."""
    if view == "dtl":
        filename = f"tiger_2000_{swing_type}_dtl_reference.json"
    elif view == "fo":
        filename = f"tiger_2000_{swing_type}_face_on_reference.json"
    else:
        raise PipelineError(f"Unknown view: {view}")
    return REFERENCE_DATA_DIR / swing_type / filename


@lru_cache(maxsize=4)
def load_reference(swing_type: str, view: str) -> dict:
    """Load reference data for a swing type and view.

    Args:
        swing_type: 'iron' (only option in v1).
        view: 'dtl' or 'fo'.

    Returns:
        Dict keyed by phase name ('address', 'top', 'impact',
        'follow_through'). Each value has 'angles' dict with keys
        matching calculate_angles.py output names.

    Raises:
        PipelineError: If reference data not found.
    """
    filepath = _file_for_view(swing_type, view)
    if not filepath.exists():
        raise PipelineError(
            f"Reference data not found for {swing_type}/{view}: {filepath}",
            error_code="REFERENCE_DATA_NOT_FOUND",
        )

    logger.info(f"Loading reference data: {filepath.name}")

    with open(filepath) as f:
        data = json.load(f)

    angle_map = DTL_ANGLE_MAP if view == "dtl" else FO_ANGLE_MAP

    # Restructure: array of phases → dict keyed by phase name
    # Also remap angle names to match calculate_angles.py output
    result = {}
    for phase in data["phases"]:
        phase_name = phase["phase"]

        # Remap angle keys to match user angle output
        remapped_angles = {}
        for ref_key, user_key in angle_map.items():
            if ref_key in phase["angles"]:
                remapped_angles[user_key] = phase["angles"][ref_key]

        result[phase_name] = {
            "frame": phase["frame"],
            "timestamp_sec": phase.get("timestamp_sec", 0),
            "angles": remapped_angles,
        }

    return result
