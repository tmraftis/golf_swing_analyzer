"""Wrapper around scripts/extract_landmarks.py for API use.

Extracts MediaPipe pose landmarks from a video file without writing
annotated frames to disk. Supports frame stepping for performance.
"""

import os
import sys
import logging

import cv2
import mediapipe as mp
import numpy as np

from .models import LandmarkExtractionError, PipelineError

logger = logging.getLogger(__name__)

# MediaPipe Tasks API
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
RunningMode = mp.tasks.vision.RunningMode
BaseOptions = mp.tasks.BaseOptions

# All 33 pose landmark names (indexed 0-32)
LANDMARK_NAMES = [
    "nose", "left_eye_inner", "left_eye", "left_eye_outer",
    "right_eye_inner", "right_eye", "right_eye_outer",
    "left_ear", "right_ear", "mouth_left", "mouth_right",
    "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
    "left_wrist", "right_wrist", "left_pinky", "right_pinky",
    "left_index", "right_index", "left_thumb", "right_thumb",
    "left_hip", "right_hip", "left_knee", "right_knee",
    "left_ankle", "right_ankle", "left_heel", "right_heel",
    "left_foot_index", "right_foot_index",
]

GOLF_LANDMARKS = {
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
}


def extract_landmarks_from_video(
    video_path: str,
    model_path: str,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
) -> dict:
    """Extract pose landmarks from a video file.

    Args:
        video_path: Path to the video file.
        model_path: Path to the MediaPipe pose_landmarker_heavy.task model.
        frame_step: Process every Nth frame (1 = every frame, 2 = every other).
        min_detection_rate: Minimum fraction of frames with successful detection.

    Returns:
        Dict with 'summary' and 'frames' keys, matching the structure
        produced by scripts/extract_landmarks.py.

    Raises:
        PipelineError: If video cannot be opened.
        LandmarkExtractionError: If detection rate is below threshold.
    """
    if not os.path.exists(video_path):
        raise PipelineError(
            f"Video file not found: {video_path}",
            error_code="VIDEO_NOT_FOUND",
        )

    if not os.path.exists(model_path):
        raise PipelineError(
            f"MediaPipe model not found: {model_path}. "
            f"Download pose_landmarker_heavy.task into scripts/.",
            error_code="MODEL_NOT_FOUND",
        )

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise PipelineError(
            f"Cannot open video file: {video_path}",
            error_code="VIDEO_OPEN_FAILED",
        )

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    logger.info(
        f"Processing video: {os.path.basename(video_path)} "
        f"({width}x{height}, {fps:.1f}fps, {total_frames} frames, "
        f"frame_step={frame_step})"
    )

    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
    )

    all_landmarks = []
    detected_count = 0

    with PoseLandmarker.create_from_options(options) as landmarker:
        frame_idx = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            timestamp_ms = int(frame_idx * 1000 / fps)

            frame_data = {
                "frame": frame_idx,
                "timestamp_sec": round(frame_idx / fps, 4),
                "timestamp_ms": timestamp_ms,
                "detected": False,
                "landmarks": {},
            }

            # Only run inference on sampled frames
            if frame_idx % frame_step == 0:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB, data=rgb_frame
                )

                results = landmarker.detect(mp_image)

                if results.pose_landmarks and len(results.pose_landmarks) > 0:
                    detected_count += 1
                    frame_data["detected"] = True
                    landmarks = results.pose_landmarks[0]

                    for idx, lm in enumerate(landmarks):
                        frame_data["landmarks"][LANDMARK_NAMES[idx]] = {
                            "x": round(lm.x, 6),
                            "y": round(lm.y, 6),
                            "z": round(lm.z, 6),
                            "visibility": round(lm.visibility, 4),
                            "pixel_x": int(lm.x * width),
                            "pixel_y": int(lm.y * height),
                        }

            all_landmarks.append(frame_data)
            frame_idx += 1

    cap.release()

    # Calculate detection rate (only among sampled frames)
    sampled_count = len([f for f in all_landmarks if f["frame"] % frame_step == 0])
    detection_rate = detected_count / sampled_count if sampled_count > 0 else 0

    logger.info(
        f"Extraction complete: {detected_count}/{sampled_count} sampled frames "
        f"detected ({detection_rate:.0%})"
    )

    if detection_rate < min_detection_rate:
        view = "dtl" if "dtl" in os.path.basename(video_path).lower() else "fo"
        raise LandmarkExtractionError(view, detection_rate * 100)

    # Build summary
    avg_visibility = {}
    for name in GOLF_LANDMARKS:
        visibilities = [
            f["landmarks"][name]["visibility"]
            for f in all_landmarks
            if f["detected"] and name in f["landmarks"]
        ]
        avg_visibility[name] = (
            round(float(np.mean(visibilities)), 4) if visibilities else 0
        )

    summary = {
        "video_file": os.path.basename(video_path),
        "label": "",
        "resolution": f"{width}x{height}",
        "fps": round(fps, 2),
        "total_frames": frame_idx,
        "detected_frames": detected_count,
        "detection_rate_pct": round(detection_rate * 100, 1),
        "frame_step": frame_step,
        "avg_golf_landmark_visibility": avg_visibility,
    }

    return {
        "summary": summary,
        "frames": all_landmarks,
    }
