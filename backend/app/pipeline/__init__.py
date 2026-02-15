"""Golf swing analysis pipeline orchestrator.

Coordinates: landmark extraction → phase detection → angle calculation
→ reference comparison → feedback generation.
"""

import glob
import json
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

# Number of decimal places to keep for landmark coordinates.
# Absorbs GPU floating-point jitter across different workers while
# retaining enough precision for accurate phase detection and angles.
LANDMARK_ROUND_DECIMALS = 4

# Bump this when landmark extraction or rounding logic changes.
# Cached landmarks with an older version are treated as stale and re-extracted.
LANDMARK_CACHE_VERSION = 2


def _round_landmarks(landmarks_data: dict, decimals: int = LANDMARK_ROUND_DECIMALS) -> dict:
    """Round all landmark coordinates to absorb GPU floating-point jitter.

    Different GPU workers (or even different runs on the same GPU) can
    produce slightly different floating-point values for the same frame.
    Rounding to a fixed number of decimal places makes downstream
    phase detection and angle calculation deterministic regardless of
    which worker produced the landmarks.

    Modifies landmarks_data in-place and returns it for convenience.
    """
    # Parse resolution once for pixel coord recomputation
    res = landmarks_data.get("summary", {}).get("resolution", "0x0")
    parts = res.split("x") if "x" in res else ["0", "0"]
    img_w = int(parts[0])
    img_h = int(parts[1]) if len(parts) > 1 else 0

    for frame in landmarks_data.get("frames", []):
        if not frame.get("detected"):
            continue
        for name, lm in frame.get("landmarks", {}).items():
            if "x" in lm:
                lm["x"] = round(lm["x"], decimals)
            if "y" in lm:
                lm["y"] = round(lm["y"], decimals)
            if "z" in lm:
                lm["z"] = round(lm["z"], decimals)
            # Recompute pixel coords from rounded normalized coords
            if "pixel_x" in lm and img_w > 0:
                lm["pixel_x"] = int(lm["x"] * img_w)
            if "pixel_y" in lm and img_h > 0:
                lm["pixel_y"] = int(lm["y"] * img_h)
    return landmarks_data


def _landmark_cache_path(video_path: str) -> str:
    """Return the path to the cached landmarks JSON for a video file.

    Cache file sits alongside the video: /uploads/abc_dtl.mp4 → /uploads/abc_dtl_landmarks.json
    """
    base, _ = os.path.splitext(video_path)
    return f"{base}_landmarks.json"


def _load_cached_landmarks(video_path: str) -> dict | None:
    """Load cached landmark data from disk if it exists and is current version.

    Returns the landmark dict or None if no cache is found or version is stale.
    """
    cache_path = _landmark_cache_path(video_path)
    if not os.path.exists(cache_path):
        return None
    try:
        with open(cache_path) as f:
            data = json.load(f)

        # Reject stale caches from before IMAGE mode / rounding changes
        cached_version = data.get("_cache_version", 0)
        if cached_version < LANDMARK_CACHE_VERSION:
            logger.info(
                f"Stale landmark cache {os.path.basename(cache_path)} "
                f"(version {cached_version} < {LANDMARK_CACHE_VERSION}), ignoring"
            )
            return None

        total = len(data.get("frames", []))
        detected = sum(1 for fr in data.get("frames", []) if fr.get("detected"))
        logger.info(
            f"Loaded cached landmarks from {os.path.basename(cache_path)} "
            f"(v{cached_version}, {detected}/{total} frames detected)"
        )
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Failed to load landmark cache {cache_path}: {e}")
        return None


def _save_landmark_cache(video_path: str, landmarks_data: dict) -> None:
    """Save landmark data to disk cache alongside the video file.

    Stamps the data with the current LANDMARK_CACHE_VERSION so stale
    caches can be detected and rejected on load.
    """
    cache_path = _landmark_cache_path(video_path)
    landmarks_data["_cache_version"] = LANDMARK_CACHE_VERSION
    try:
        with open(cache_path, "w") as f:
            json.dump(landmarks_data, f)
        size_mb = os.path.getsize(cache_path) / 1e6
        logger.info(
            f"Cached landmarks to {os.path.basename(cache_path)} "
            f"(v{LANDMARK_CACHE_VERSION}, {size_mb:.1f}MB)"
        )
    except OSError as e:
        logger.warning(f"Failed to save landmark cache {cache_path}: {e}")


def _find_landmarks_by_hash(upload_dir: str, upload_id: str, view: str) -> dict | None:
    """Look for cached landmarks from a previous upload with the same video hash.

    Scans the uploads directory for hash files matching the current upload's
    content hash. If a match is found AND that upload has cached landmarks,
    copies the landmarks and returns them. This ensures re-uploading the same
    video always produces identical results, regardless of ffmpeg non-determinism.

    Returns the landmark dict or None if no match is found.
    """
    # Read this upload's hash
    hash_path = os.path.join(upload_dir, f"{upload_id}_{view}_hash.txt")
    if not os.path.exists(hash_path):
        logger.debug(f"No hash file found for {upload_id}_{view}")
        return None

    try:
        our_hash = open(hash_path).read().strip()
    except OSError:
        return None

    if not our_hash:
        return None

    # Scan all hash files for the same view
    import glob as glob_mod
    pattern = os.path.join(upload_dir, f"*_{view}_hash.txt")
    for other_hash_path in glob_mod.glob(pattern):
        other_basename = os.path.basename(other_hash_path)
        # Skip our own hash file
        if other_basename == f"{upload_id}_{view}_hash.txt":
            continue

        try:
            other_hash = open(other_hash_path).read().strip()
        except OSError:
            continue

        if other_hash != our_hash:
            continue

        # Found a matching hash! Extract the other upload_id from filename
        # Format: {upload_id}_{view}_hash.txt
        other_upload_id = other_basename.rsplit(f"_{view}_hash.txt", 1)[0]

        # Look for cached landmarks from that upload
        # Try common video extensions
        for ext in (".mp4", ".mov", ".MOV"):
            other_video_path = os.path.join(
                upload_dir, f"{other_upload_id}_{view}{ext}"
            )
            cached = _load_cached_landmarks(other_video_path)
            if cached is not None:
                logger.info(
                    f"Reusing landmarks from matching hash: "
                    f"{other_upload_id} -> {upload_id} ({view}, hash={our_hash[:16]}...)"
                )
                return cached

    logger.debug(f"No matching hash found for {upload_id}_{view}")
    return None


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

    # Step 2: Extract landmarks (with caching for determinism)
    # Priority: (1) same-upload cache, (2) cross-upload hash match, (3) fresh extraction.
    # This guarantees identical results when re-uploading the same source video.
    landmarks = {}
    uncached_views = []

    for view in views:
        # Try same-upload cache first
        cached = _load_cached_landmarks(video_paths[view])
        if cached is not None:
            landmarks[view] = cached
            continue

        # Try cross-upload hash-based deduplication
        hash_cached = _find_landmarks_by_hash(upload_dir, upload_id, view)
        if hash_cached is not None:
            landmarks[view] = hash_cached
            # Save a copy for this upload so future re-analyses are fast
            _save_landmark_cache(video_paths[view], hash_cached)
            continue

        uncached_views.append(view)

    if uncached_views:
        if use_modal:
            if (
                len(uncached_views) == 2
                and "dtl" in uncached_views
                and "fo" in uncached_views
            ):
                # Both views need extraction — use parallel Modal
                dtl_lm, fo_lm = _extract_landmarks_modal(
                    video_paths["dtl"], video_paths["fo"],
                    frame_step, min_detection_rate,
                    modal_target_height, model_path,
                )
                landmarks["dtl"] = dtl_lm
                landmarks["fo"] = fo_lm
            else:
                # Single uncached view — use single Modal extraction
                for view in uncached_views:
                    landmarks[view] = _extract_landmarks_modal_single(
                        video_paths[view], frame_step, min_detection_rate,
                        modal_target_height, model_path,
                    )
        else:
            for view in uncached_views:
                logger.info(f"Extracting landmarks from {view.upper()} video...")
                landmarks[view] = extract_landmarks_from_video(
                    video_paths[view], model_path, frame_step, min_detection_rate
                )

        # Round landmarks to absorb GPU floating-point jitter, then cache
        for view in uncached_views:
            _round_landmarks(landmarks[view])
            _save_landmark_cache(video_paths[view], landmarks[view])

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
