"""Centralised path resolution for local dev and Docker/Railway.

This replaces the duplicated project-root detection that was previously
copy-pasted into reference_data.py, video.py, phase_detector.py,
angle_calculator.py, and config.py.

Layout assumptions:
    Local dev:  backend/app/paths.py  →  project root is 2 levels up
    Docker:     /app/app/paths.py     →  project root is 2 levels up (/app)
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Resolve once at import time.  Two levels up from backend/app/paths.py
# gives us the repo root (local) or /app (Docker) — both contain
# reference_data/ and scripts/.
_THIS_DIR = Path(__file__).resolve().parent          # backend/app
_BACKEND_DIR = _THIS_DIR.parent                       # backend/
_PROJECT_ROOT_CANDIDATES = [
    _BACKEND_DIR.parent,   # local dev: repo root
    _BACKEND_DIR,          # Docker/Railway: backend IS the root (/app)
]

PROJECT_ROOT: Path = next(
    (p for p in _PROJECT_ROOT_CANDIDATES if (p / "reference_data").is_dir()),
    _PROJECT_ROOT_CANDIDATES[0],
)

REFERENCE_DATA_DIR: Path = PROJECT_ROOT / "reference_data"
SCRIPTS_DIR: Path = PROJECT_ROOT / "scripts"


def ensure_scripts_importable() -> None:
    """Add scripts/ to sys.path once so legacy scripts are importable.

    Called at module level by phase_detector.py and angle_calculator.py
    instead of each doing their own sys.path manipulation.
    """
    scripts_path = str(SCRIPTS_DIR.resolve())
    if SCRIPTS_DIR.is_dir() and scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
        logger.debug(f"Added {scripts_path} to sys.path")
