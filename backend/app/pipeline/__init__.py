"""Golf swing analysis pipeline orchestrator.

Coordinates: landmark extraction → phase detection → angle calculation
→ reference comparison → feedback generation.
"""

import glob
import logging
import os
import time

from .models import PipelineError, VideoNotFoundError
from .landmark_extractor import extract_landmarks_from_video
from .phase_detector import detect_swing_phases
from .angle_calculator import calculate_angles
from .reference_data import load_reference
from .comparison_engine import compute_deltas, rank_differences
from .feedback_engine import generate_feedback

logger = logging.getLogger(__name__)


def _find_video(upload_dir: str, upload_id: str, view: str) -> str:
    """Find the uploaded video file for a given upload_id and view.

    Files are saved as {upload_id}_{view}.{ext} by the upload endpoint.
    The extension may vary (.mp4, .mov, .MOV, etc.).
    """
    pattern = f"{upload_dir}/{upload_id}_{view}.*"
    matches = glob.glob(pattern)
    if not matches:
        raise VideoNotFoundError(upload_id, view)
    return matches[0]


def run_analysis(
    upload_id: str,
    swing_type: str,
    upload_dir: str,
    model_path: str,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
) -> dict:
    """Run the full analysis pipeline on uploaded swing videos.

    Args:
        upload_id: UUID from the upload endpoint.
        swing_type: 'iron' (only option in v1).
        upload_dir: Path to the uploads directory.
        model_path: Path to the MediaPipe model file.
        frame_step: Process every Nth frame (default 2).
        min_detection_rate: Minimum acceptable pose detection rate.

    Returns:
        Complete analysis result dict matching the API response schema.

    Raises:
        VideoNotFoundError: If uploaded videos not found.
        PipelineError: On any pipeline failure.
    """
    start_time = time.time()
    logger.info(f"Starting analysis for upload {upload_id} (swing_type={swing_type})")

    # Step 1: Locate uploaded videos
    dtl_path = _find_video(upload_dir, upload_id, "dtl")
    fo_path = _find_video(upload_dir, upload_id, "fo")
    logger.info(f"Found videos: DTL={dtl_path}, FO={fo_path}")

    # Step 2: Extract landmarks
    logger.info("Extracting landmarks from DTL video...")
    dtl_landmarks = extract_landmarks_from_video(
        dtl_path, model_path, frame_step, min_detection_rate
    )

    logger.info("Extracting landmarks from FO video...")
    fo_landmarks = extract_landmarks_from_video(
        fo_path, model_path, frame_step, min_detection_rate
    )

    # Step 3: Detect phases
    dtl_phases = detect_swing_phases(dtl_landmarks, "dtl")
    fo_phases = detect_swing_phases(fo_landmarks, "fo")

    # Step 4: Calculate angles
    dtl_angle_results = calculate_angles(dtl_landmarks, dtl_phases, "dtl")
    fo_angle_results = calculate_angles(fo_landmarks, fo_phases, "fo")

    user_angles = {
        "dtl": dtl_angle_results,
        "fo": fo_angle_results,
    }

    # Step 5: Load reference data
    dtl_ref = load_reference(swing_type, "dtl")
    fo_ref = load_reference(swing_type, "fo")

    ref_angles = {
        "dtl": dtl_ref,
        "fo": fo_ref,
    }

    # Step 6: Compute deltas
    deltas = compute_deltas(user_angles, ref_angles)

    # Step 7: Rank differences and generate feedback
    ranked = rank_differences(deltas, user_angles, ref_angles)
    top_differences = generate_feedback(ranked, user_angles, ref_angles)

    processing_time = round(time.time() - start_time, 1)
    logger.info(f"Analysis complete in {processing_time}s")

    # Build phase frames summary
    phase_frames = {
        "dtl": {k: v["frame"] for k, v in dtl_phases.items()},
        "fo": {k: v["frame"] for k, v in fo_phases.items()},
    }

    # Build video URLs for the frontend
    video_urls = {
        "dtl": f"/uploads/{os.path.basename(dtl_path)}",
        "fo": f"/uploads/{os.path.basename(fo_path)}",
    }

    # Reference video URLs (Tiger)
    ref_video_urls = {
        "dtl": f"/reference/{swing_type}/tiger_2000_{swing_type}_dtl.mov",
        "fo": f"/reference/{swing_type}/tiger_2000_{swing_type}_fo.mov",
    }

    return {
        "status": "success",
        "upload_id": upload_id,
        "swing_type": swing_type,
        "processing_time_sec": processing_time,
        "user_angles": user_angles,
        "reference_angles": ref_angles,
        "deltas": deltas,
        "top_differences": top_differences,
        "phase_frames": phase_frames,
        "video_urls": video_urls,
        "reference_video_urls": ref_video_urls,
    }
