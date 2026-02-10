"""
Phase 0: Extract MediaPipe Pose landmarks from Tiger Woods swing videos.

Uses the MediaPipe Tasks API (PoseLandmarker) to process each frame.
Outputs:
  - Raw landmark data as JSON (coordinates + visibility per frame)
  - Annotated frames as images for visual inspection
  - Summary stats (detection rate, avg confidence)
"""

import cv2
import mediapipe as mp
import json
import os
import sys
import numpy as np

# MediaPipe Tasks API imports
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
    "left_foot_index", "right_foot_index"
]

# Key body landmarks for golf swing analysis
GOLF_LANDMARKS = {
    "left_shoulder": 11, "right_shoulder": 12,
    "left_elbow": 13, "right_elbow": 14,
    "left_wrist": 15, "right_wrist": 16,
    "left_hip": 23, "right_hip": 24,
    "left_knee": 25, "right_knee": 26,
    "left_ankle": 27, "right_ankle": 28,
}

# Pose connections for drawing skeleton
POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),  # Arms
    (11, 23), (12, 24), (23, 24),  # Torso
    (23, 25), (25, 27), (24, 26), (26, 28),  # Legs
    (15, 17), (15, 19), (15, 21),  # Left hand
    (16, 18), (16, 20), (16, 22),  # Right hand
    (27, 29), (27, 31), (28, 30), (28, 32),  # Feet
]


def draw_landmarks_on_frame(frame, landmarks, width, height):
    """Draw pose skeleton on a frame using landmark data."""
    annotated = frame.copy()

    # Draw connections
    for start_idx, end_idx in POSE_CONNECTIONS:
        start = landmarks[start_idx]
        end = landmarks[end_idx]
        if start.visibility > 0.3 and end.visibility > 0.3:
            pt1 = (int(start.x * width), int(start.y * height))
            pt2 = (int(end.x * width), int(end.y * height))
            cv2.line(annotated, pt1, pt2, (0, 255, 0), 2)

    # Draw landmark points
    for i, lm in enumerate(landmarks):
        if lm.visibility > 0.3:
            px = int(lm.x * width)
            py = int(lm.y * height)
            color = (0, 0, 255) if i in GOLF_LANDMARKS.values() else (0, 255, 0)
            cv2.circle(annotated, (px, py), 4, color, -1)

    return annotated


def process_video(video_path, output_dir, label, model_path):
    """Process a single video and extract landmarks from every frame."""

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"ERROR: Cannot open video: {video_path}")
        sys.exit(1)

    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"\n{'='*60}")
    print(f"Processing: {label}")
    print(f"  File: {os.path.basename(video_path)}")
    print(f"  Resolution: {width}x{height}")
    print(f"  FPS: {fps:.2f}")
    print(f"  Total frames: {total_frames}")
    print(f"  Duration: {total_frames/fps:.2f}s")
    print(f"{'='*60}")

    frames_dir = os.path.join(output_dir, f"{label}_frames")
    os.makedirs(frames_dir, exist_ok=True)

    # Create PoseLandmarker for VIDEO mode
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
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

            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # Timestamp in milliseconds
            timestamp_ms = int(frame_idx * 1000 / fps)

            results = landmarker.detect_for_video(mp_image, timestamp_ms)

            frame_data = {
                "frame": frame_idx,
                "timestamp_sec": round(frame_idx / fps, 4),
                "timestamp_ms": timestamp_ms,
                "detected": False,
                "landmarks": {}
            }

            if results.pose_landmarks and len(results.pose_landmarks) > 0:
                detected_count += 1
                frame_data["detected"] = True
                landmarks = results.pose_landmarks[0]  # First (only) person

                # Extract all 33 landmarks
                for idx, lm in enumerate(landmarks):
                    frame_data["landmarks"][LANDMARK_NAMES[idx]] = {
                        "x": round(lm.x, 6),
                        "y": round(lm.y, 6),
                        "z": round(lm.z, 6),
                        "visibility": round(lm.visibility, 4),
                        "pixel_x": int(lm.x * width),
                        "pixel_y": int(lm.y * height),
                    }

                # Draw pose on frame
                annotated = draw_landmarks_on_frame(frame, landmarks, width, height)

                # Add frame number overlay
                cv2.putText(
                    annotated, f"Frame {frame_idx} | t={frame_data['timestamp_sec']:.3f}s",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                )

                # Add visibility scores for key golf landmarks
                y_offset = 55
                for name, lm_idx in GOLF_LANDMARKS.items():
                    vis = landmarks[lm_idx].visibility
                    color = (0, 255, 0) if vis > 0.7 else (0, 165, 255) if vis > 0.4 else (0, 0, 255)
                    cv2.putText(
                        annotated, f"{name}: {vis:.2f}",
                        (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1
                    )
                    y_offset += 15
            else:
                annotated = frame.copy()
                cv2.putText(
                    annotated, f"Frame {frame_idx} - NO DETECTION",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )

            cv2.imwrite(os.path.join(frames_dir, f"frame_{frame_idx:04d}.jpg"), annotated)
            all_landmarks.append(frame_data)
            frame_idx += 1

    cap.release()

    detection_rate = (detected_count / frame_idx * 100) if frame_idx > 0 else 0

    # Compute average visibility for key golf landmarks
    avg_visibility = {}
    for name in GOLF_LANDMARKS:
        visibilities = [
            f["landmarks"][name]["visibility"]
            for f in all_landmarks
            if f["detected"] and name in f["landmarks"]
        ]
        avg_visibility[name] = round(np.mean(visibilities), 4) if visibilities else 0

    summary = {
        "video_file": os.path.basename(video_path),
        "label": label,
        "resolution": f"{width}x{height}",
        "fps": round(fps, 2),
        "total_frames": frame_idx,
        "detected_frames": detected_count,
        "detection_rate_pct": round(detection_rate, 1),
        "avg_golf_landmark_visibility": avg_visibility,
    }

    print(f"\n  Detection rate: {detected_count}/{frame_idx} frames ({detection_rate:.1f}%)")
    print(f"\n  Key landmark avg visibility:")
    for name, vis in avg_visibility.items():
        indicator = "OK" if vis > 0.7 else "WARN" if vis > 0.4 else "LOW"
        print(f"    {name:20s}: {vis:.4f} [{indicator}]")

    # Save raw landmark data
    output = {
        "summary": summary,
        "frames": all_landmarks,
    }

    json_path = os.path.join(output_dir, f"{label}_landmarks.json")
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n  Landmarks saved to: {json_path}")
    print(f"  Annotated frames saved to: {frames_dir}/")

    return output


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    model_path = os.path.join(base_dir, "scripts", "pose_landmarker_heavy.task")

    if not os.path.exists(model_path):
        print(f"ERROR: Model not found at {model_path}")
        print("Download from: https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    videos = {
        "dtl": "/Users/timraftis/Desktop/Tiger DTL 2.mov",
        "fo": "/Users/timraftis/Desktop/Tiger FO 2.mov",
    }

    results = {}
    for label, path in videos.items():
        if not os.path.exists(path):
            print(f"WARNING: Video not found: {path}")
            continue
        results[label] = process_video(path, output_dir, label, model_path)

    print(f"\n{'='*60}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*60}")
    for label, data in results.items():
        s = data["summary"]
        print(f"  {label}: {s['detected_frames']}/{s['total_frames']} frames detected ({s['detection_rate_pct']}%)")


if __name__ == "__main__":
    main()
