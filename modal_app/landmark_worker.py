"""Modal function for GPU-accelerated MediaPipe landmark extraction.

Runs pose estimation on golf swing videos using MediaPipe's heavy model
on Modal's GPU infrastructure. Videos are sent as bytes, processed in
a temporary file, and landmarks returned as a dict.

Deploy:   modal deploy modal_app/landmark_worker.py
Test:     modal run modal_app/landmark_worker.py -- backend/uploads/<video>.MOV
"""

import modal

app = modal.App("pure-landmark-extractor")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1-mesa-glx", "libglib2.0-0", "wget")
    .pip_install(
        "mediapipe>=0.10.9",
        "opencv-python-headless>=4.8.0",
        "numpy>=1.24.0",
    )
    .run_commands(
        "mkdir -p /models",
        "wget -O /models/pose_landmarker_heavy.task "
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task",
    )
)

MODEL_PATH = "/models/pose_landmarker_heavy.task"

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


@app.function(
    image=image,
    gpu="T4",
    timeout=120,
    retries=1,
)
def extract_landmarks(
    video_bytes: bytes,
    frame_step: int = 2,
    min_detection_rate: float = 0.7,
    target_height: int = 960,
) -> dict:
    """Extract MediaPipe pose landmarks from video bytes.

    Args:
        video_bytes: Raw video file bytes (.mov/.mp4).
        frame_step: Process every Nth frame (default 2).
        min_detection_rate: Minimum acceptable detection rate (0-1).
        target_height: Downscale frames to this height before inference.
                       Set to 0 to disable downscaling.

    Returns:
        Dict with 'summary' and 'frames' keys on success.
        Dict with 'error' and 'detection_rate' keys on failure.
    """
    import tempfile
    import os

    import cv2
    import mediapipe as mp
    import numpy as np

    # Write bytes to temp file (cv2.VideoCapture needs a file path)
    with tempfile.NamedTemporaryFile(suffix=".mov", delete=False) as f:
        f.write(video_bytes)
        tmp_path = f.name

    try:
        cap = cv2.VideoCapture(tmp_path)
        if not cap.isOpened():
            return {"error": "VIDEO_OPEN_FAILED", "message": "Cannot open video"}

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Determine downscale factor
        do_downscale = target_height > 0 and orig_height > target_height
        if do_downscale:
            scale = target_height / orig_height
            inf_width = int(orig_width * scale)
            inf_height = target_height
        else:
            inf_width = orig_width
            inf_height = orig_height

        print(
            f"Processing: {orig_width}x{orig_height} @ {fps:.1f}fps, "
            f"{total_frames} frames, step={frame_step}"
        )
        if do_downscale:
            print(f"Downscaling to {inf_width}x{inf_height} for inference")

        # Set up MediaPipe
        PoseLandmarker = mp.tasks.vision.PoseLandmarker
        PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
        RunningMode = mp.tasks.vision.RunningMode
        BaseOptions = mp.tasks.BaseOptions

        options = PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
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
                    # Downscale for inference if configured
                    if do_downscale:
                        inf_frame = cv2.resize(frame, (inf_width, inf_height))
                    else:
                        inf_frame = frame

                    rgb_frame = cv2.cvtColor(inf_frame, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(
                        image_format=mp.ImageFormat.SRGB, data=rgb_frame
                    )

                    results = landmarker.detect_for_video(mp_image, timestamp_ms)

                    if results.pose_landmarks and len(results.pose_landmarks) > 0:
                        detected_count += 1
                        frame_data["detected"] = True
                        landmarks = results.pose_landmarks[0]

                        for idx, lm in enumerate(landmarks):
                            # Landmark coords are normalized (0-1), so they're
                            # resolution-independent. pixel_x/y use original
                            # dimensions for frontend overlay compatibility.
                            frame_data["landmarks"][LANDMARK_NAMES[idx]] = {
                                "x": round(lm.x, 6),
                                "y": round(lm.y, 6),
                                "z": round(lm.z, 6),
                                "visibility": round(lm.visibility, 4),
                                "pixel_x": int(lm.x * orig_width),
                                "pixel_y": int(lm.y * orig_height),
                            }

                all_landmarks.append(frame_data)
                frame_idx += 1

        cap.release()

        # Calculate detection rate (only among sampled frames)
        sampled_count = len(
            [f for f in all_landmarks if f["frame"] % frame_step == 0]
        )
        detection_rate = detected_count / sampled_count if sampled_count > 0 else 0

        print(
            f"Extraction complete: {detected_count}/{sampled_count} sampled "
            f"frames detected ({detection_rate:.0%})"
        )

        if detection_rate < min_detection_rate:
            return {
                "error": "LANDMARK_EXTRACTION_FAILED",
                "detection_rate": round(detection_rate * 100, 1),
            }

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
            "video_file": "uploaded_video",
            "label": "",
            "resolution": f"{orig_width}x{orig_height}",
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

    finally:
        os.unlink(tmp_path)


@app.local_entrypoint()
def main():
    """Test entrypoint: extract landmarks from a local video file."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: modal run modal_app/landmark_worker.py -- <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    print(f"Reading video: {video_path}")

    with open(video_path, "rb") as f:
        video_bytes = f.read()

    print(f"Sending {len(video_bytes) / 1e6:.1f}MB to Modal...")
    result = extract_landmarks.remote(
        video_bytes=video_bytes,
        frame_step=2,
        min_detection_rate=0.7,
        target_height=960,
    )

    if "error" in result:
        print(f"ERROR: {result['error']}")
        if "detection_rate" in result:
            print(f"Detection rate: {result['detection_rate']}%")
    else:
        summary = result["summary"]
        print(f"\nSuccess!")
        print(f"  Frames: {summary['total_frames']}")
        print(f"  FPS: {summary['fps']}")
        print(f"  Resolution: {summary['resolution']}")
        print(f"  Detection rate: {summary['detection_rate_pct']}%")
        print(f"  Detected frames: {summary['detected_frames']}")
