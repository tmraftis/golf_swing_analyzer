"""Golf swing analysis pipeline orchestrator.

Coordinates: landmark extraction → phase detection → angle calculation
→ reference comparison → feedback generation.
"""

import glob
import logging
import os
import time

import cv2

from .models import PipelineError, VideoNotFoundError
from .landmark_extractor import extract_landmarks_from_video, GOLF_LANDMARKS
from .phase_detector import detect_swing_phases
from .angle_calculator import calculate_angles
from .reference_data import load_reference
from .comparison_engine import compute_deltas, rank_differences, rank_similarities, compute_similarity_score
from .feedback_engine import generate_feedback, generate_similarity_titles

logger = logging.getLogger(__name__)


def _extract_phase_landmarks(landmarks_data: dict, phases: dict) -> dict:
    """Extract golf-relevant joint positions at each detected phase frame.

    Returns dict keyed by phase name, each value is a dict of
    joint_name -> {"x": float, "y": float} (normalized 0-1 coords).
    """
    frame_lookup = {f["frame"]: f for f in landmarks_data["frames"]}
    result = {}
    for phase_name, phase_info in phases.items():
        frame_data = frame_lookup.get(phase_info["frame"])
        if not frame_data or not frame_data.get("detected"):
            result[phase_name] = {}
            continue
        lm = frame_data["landmarks"]
        phase_lm = {}
        for joint_name in GOLF_LANDMARKS:
            if joint_name in lm:
                phase_lm[joint_name] = {
                    "x": lm[joint_name]["x"],
                    "y": lm[joint_name]["y"],
                }
        result[phase_name] = phase_lm
    return result


def _extract_all_frame_landmarks(landmarks_data: dict) -> list:
    """Extract golf-relevant joint positions for ALL detected frames.

    Returns a list of {timestamp_sec, landmarks} dicts, sorted by time.
    Only includes frames where pose was successfully detected.
    Used for frame-by-frame skeleton overlay during video playback.
    """
    frames = []
    for frame_data in landmarks_data["frames"]:
        if not frame_data.get("detected"):
            continue
        lm = frame_data["landmarks"]
        frame_lm = {}
        for joint_name in GOLF_LANDMARKS:
            if joint_name in lm:
                frame_lm[joint_name] = {
                    "x": lm[joint_name]["x"],
                    "y": lm[joint_name]["y"],
                }
        if frame_lm:
            frames.append({
                "t": round(frame_data["timestamp_sec"], 4),
                "lm": frame_lm,
            })
    return frames


def _extract_phase_frame_images(
    video_path: str,
    phases: dict,
    upload_dir: str,
    upload_id: str,
    view: str,
) -> dict:
    """Extract JPEG images at each phase frame for instant phase switching.

    Saves images as {upload_id}_{view}_{phase}.jpg in the upload directory.
    Returns dict keyed by phase name with the URL path for each image.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Cannot open video for frame extraction: {video_path}")
        return {}

    result = {}
    for phase_name, phase_info in phases.items():
        frame_num = phase_info["frame"]
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Cannot read frame {frame_num} from {video_path}")
            continue

        filename = f"{upload_id}_{view}_{phase_name}.jpg"
        output_path = os.path.join(upload_dir, filename)
        cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        result[phase_name] = f"/uploads/{filename}"

    cap.release()
    return result


def _extract_ref_phase_frame_images(
    video_path: str,
    ref_data: dict,
    upload_dir: str,
    upload_id: str,
    view: str,
) -> dict:
    """Extract JPEG images from reference video at each phase timestamp.

    Reference data has timestamp_sec per phase; we seek by time.
    Saves images as {upload_id}_ref_{view}_{phase}.jpg in the upload directory.
    Returns dict keyed by phase name with the URL path for each image.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.warning(f"Cannot open reference video for frame extraction: {video_path}")
        return {}

    fps = cap.get(cv2.CAP_PROP_FPS)
    result = {}
    for phase_name, phase_info in ref_data.items():
        frame_num = phase_info.get("frame", 0)
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        if not ret:
            logger.warning(f"Cannot read frame {frame_num} from {video_path}")
            continue

        filename = f"{upload_id}_ref_{view}_{phase_name}.jpg"
        output_path = os.path.join(upload_dir, filename)
        cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        result[phase_name] = f"/uploads/{filename}"

    cap.release()
    return result


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


def _extract_landmarks_modal_single(
    video_path: str,
    frame_step: int,
    min_detection_rate: float,
    target_height: int,
    model_path: str,
) -> dict:
    """Extract landmarks via Modal GPU for a single video with fallback to local."""
    try:
        from .modal_extractor import extract_landmarks_single_modal

        logger.info("Extracting landmarks via Modal (GPU-accelerated)...")
        with open(video_path, "rb") as f:
            video_bytes = f.read()

        result = extract_landmarks_single_modal(
            video_bytes=video_bytes,
            frame_step=frame_step,
            min_detection_rate=min_detection_rate,
            target_height=target_height,
        )

        # Log extraction results for debugging
        total = len(result.get("frames", []))
        detected = sum(1 for f in result.get("frames", []) if f.get("detected"))
        fps = result.get("summary", {}).get("fps", 0)
        logger.info(
            f"Modal: {total} frames, {detected} detected "
            f"({detected/total*100:.0f}%), fps={fps}"
        )

        return result

    except PipelineError:
        raise

    except Exception as e:
        logger.warning(f"Modal extraction failed ({e}), falling back to local...")
        return extract_landmarks_from_video(
            video_path, model_path, frame_step, min_detection_rate
        )


def _extract_landmarks_modal(
    dtl_path: str,
    fo_path: str,
    frame_step: int,
    min_detection_rate: float,
    target_height: int,
    model_path: str,
) -> tuple:
    """Extract landmarks via Modal GPUs with fallback to local processing.

    Pipeline errors (e.g. low detection rate) are re-raised immediately.
    Modal infrastructure errors (connection, timeout, etc.) trigger fallback
    to local CPU extraction.
    """
    try:
        from .modal_extractor import extract_landmarks_parallel_modal

        logger.info("Extracting landmarks via Modal (GPU-accelerated)...")
        with open(dtl_path, "rb") as f:
            dtl_bytes = f.read()
        with open(fo_path, "rb") as f:
            fo_bytes = f.read()

        dtl_landmarks, fo_landmarks = extract_landmarks_parallel_modal(
            dtl_bytes=dtl_bytes,
            fo_bytes=fo_bytes,
            frame_step=frame_step,
            min_detection_rate=min_detection_rate,
            target_height=target_height,
        )

        # Log extraction results for debugging
        for label, lm in [("DTL", dtl_landmarks), ("FO", fo_landmarks)]:
            total = len(lm.get("frames", []))
            detected = sum(1 for f in lm.get("frames", []) if f.get("detected"))
            fps = lm.get("summary", {}).get("fps", 0)
            logger.info(
                f"Modal {label}: {total} frames, {detected} detected "
                f"({detected/total*100:.0f}%), fps={fps}"
            )

        return dtl_landmarks, fo_landmarks

    except PipelineError:
        # Real extraction failure (e.g. low detection rate) — don't retry locally
        raise

    except Exception as e:
        logger.warning(f"Modal extraction failed ({e}), falling back to local...")

        dtl_landmarks = extract_landmarks_from_video(
            dtl_path, model_path, frame_step, min_detection_rate
        )
        fo_landmarks = extract_landmarks_from_video(
            fo_path, model_path, frame_step, min_detection_rate
        )
        return dtl_landmarks, fo_landmarks


def run_analysis(
    upload_id: str,
    swing_type: str,
    upload_dir: str,
    model_path: str,
    views: list[str] | None = None,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
    use_modal: bool = False,
    modal_target_height: int = 960,
) -> dict:
    """Run the full analysis pipeline on uploaded swing videos.

    Args:
        upload_id: UUID from the upload endpoint.
        swing_type: 'iron' (only option in v1).
        upload_dir: Path to the uploads directory.
        model_path: Path to the MediaPipe model file.
        views: List of views to process, e.g. ["dtl"] or ["fo"] or ["dtl", "fo"].
        frame_step: Process every Nth frame (default 2).
        min_detection_rate: Minimum acceptable pose detection rate.
        use_modal: If True, offload landmark extraction to Modal GPUs.
        modal_target_height: Downscale frames to this height for Modal inference.

    Returns:
        Complete analysis result dict matching the API response schema.

    Raises:
        VideoNotFoundError: If uploaded videos not found.
        PipelineError: On any pipeline failure.
    """
    if views is None:
        views = ["dtl", "fo"]

    start_time = time.time()
    logger.info(
        f"Starting analysis for upload {upload_id} "
        f"(swing_type={swing_type}, views={views})"
    )

    # Step 1: Locate uploaded videos
    video_paths = {}
    for view in views:
        video_paths[view] = _find_video(upload_dir, upload_id, view)
    logger.info(f"Found videos: {video_paths}")

    # Step 2: Extract landmarks
    landmarks = {}
    if use_modal:
        if len(views) == 2 and "dtl" in views and "fo" in views:
            # Both views — use parallel Modal extraction
            dtl_lm, fo_lm = _extract_landmarks_modal(
                video_paths["dtl"], video_paths["fo"],
                frame_step, min_detection_rate,
                modal_target_height, model_path,
            )
            landmarks["dtl"] = dtl_lm
            landmarks["fo"] = fo_lm
        else:
            # Single view — use single Modal extraction
            for view in views:
                landmarks[view] = _extract_landmarks_modal_single(
                    video_paths[view], frame_step, min_detection_rate,
                    modal_target_height, model_path,
                )
    else:
        for view in views:
            logger.info(f"Extracting landmarks from {view.upper()} video...")
            landmarks[view] = extract_landmarks_from_video(
                video_paths[view], model_path, frame_step, min_detection_rate
            )

    # Step 3: Detect phases
    phases = {}
    for view in views:
        phases[view] = detect_swing_phases(landmarks[view], view)

    # Step 4: Calculate angles
    user_angles = {}
    for view in views:
        user_angles[view] = calculate_angles(landmarks[view], phases[view], view)

    # Step 5: Load reference data
    ref_angles = {}
    for view in views:
        ref_angles[view] = load_reference(swing_type, view)

    # Step 6: Compute deltas
    deltas = compute_deltas(user_angles, ref_angles)

    # Step 6b: Compute overall similarity score
    similarity_score = compute_similarity_score(deltas)
    logger.info(f"Similarity score: {similarity_score}%")

    # Step 7: Rank differences and generate feedback
    ranked = rank_differences(deltas, user_angles, ref_angles)
    top_differences = generate_feedback(ranked, user_angles, ref_angles)

    # Step 7b: Rank similarities (closest matches to Tiger)
    ranked_sims = rank_similarities(deltas, user_angles, ref_angles)
    top_similarities = generate_similarity_titles(ranked_sims)

    # Step 4b: Extract phase landmarks for skeleton overlay
    user_phase_landmarks = {}
    reference_phase_landmarks = {}
    for view in views:
        user_phase_landmarks[view] = _extract_phase_landmarks(
            landmarks[view], phases[view]
        )
        reference_phase_landmarks[view] = {
            phase: data.get("landmarks", {})
            for phase, data in ref_angles[view].items()
        }

    # Step 4c: Extract ALL frame landmarks for continuous skeleton playback
    user_all_landmarks = {}
    for view in views:
        user_all_landmarks[view] = _extract_all_frame_landmarks(landmarks[view])

    # Step 4d: Extract phase frame JPEG images for instant phase switching
    logger.info("Extracting phase frame images...")
    user_phase_images = {}
    for view in views:
        user_phase_images[view] = _extract_phase_frame_images(
            video_paths[view], phases[view], upload_dir, upload_id, view
        )

    # Reference video phase frame images (Tiger)
    from app.paths import REFERENCE_DATA_DIR
    ref_phase_images = {}
    for view in views:
        ref_video = str(
            REFERENCE_DATA_DIR / swing_type
            / f"tiger_2000_{swing_type}_{view}.mov"
        )
        ref_phase_images[view] = _extract_ref_phase_frame_images(
            ref_video, ref_angles[view], upload_dir, upload_id, view
        )

    processing_time = round(time.time() - start_time, 1)
    logger.info(f"Analysis complete in {processing_time}s")

    # Build phase frames summary
    phase_frames = {}
    for view in views:
        phase_frames[view] = {k: v["frame"] for k, v in phases[view].items()}

    # Build video URLs for the frontend
    video_urls = {}
    for view in views:
        video_urls[view] = f"/uploads/{os.path.basename(video_paths[view])}"

    # Reference video URLs (Tiger)
    ref_video_urls = {}
    for view in views:
        ref_video_urls[view] = (
            f"/reference/{swing_type}/tiger_2000_{swing_type}_{view}.mov"
        )

    return {
        "status": "success",
        "upload_id": upload_id,
        "swing_type": swing_type,
        "processing_time_sec": processing_time,
        "similarity_score": similarity_score,
        "user_angles": user_angles,
        "reference_angles": ref_angles,
        "deltas": deltas,
        "top_differences": top_differences,
        "top_similarities": top_similarities,
        "phase_frames": phase_frames,
        "video_urls": video_urls,
        "reference_video_urls": ref_video_urls,
        "user_phase_landmarks": user_phase_landmarks,
        "reference_phase_landmarks": reference_phase_landmarks,
        "user_all_landmarks": user_all_landmarks,
        "user_phase_images": user_phase_images,
        "reference_phase_images": ref_phase_images,
    }
