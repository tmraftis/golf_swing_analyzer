"""
Phase 0: Build validated Tiger Woods 2000 iron reference data JSON files.

Creates:
  - reference_data/iron/tiger_2000_iron_dtl_reference.json
  - reference_data/iron/tiger_2000_iron_face_on_reference.json

Each file contains per-phase angle data with swing_type field,
frame numbers, timestamps, and measurement reliability notes.
"""

import json
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calculate_angles import (
    load_landmarks, DTL_PHASES, FO_PHASES,
    calc_forward_bend_dtl, calc_lead_arm_torso_angle, calc_trail_arm_torso_angle,
    calc_elbow_angle, calc_knee_flex, calc_wrist_cock, calc_shoulder_turn_dtl,
    calc_shoulder_turn_fo, calc_hip_turn_fo, calc_spine_tilt,
    calc_shoulder_hip_separation_fo, get_landmark_2d,
)


def build_dtl_reference(landmarks_data):
    """Build DTL reference data for all phases."""
    frames = landmarks_data["frames"]
    phases = []

    for phase_name, phase_info in DTL_PHASES.items():
        frame_num = phase_info["frame"]
        frame_data = next(f for f in frames if f["frame"] == frame_num)

        # Extract key landmark positions (normalized)
        key_landmarks = {}
        for lm_name in [
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle",
            "left_index", "right_index",
        ]:
            lm = frame_data["landmarks"][lm_name]
            key_landmarks[lm_name] = {
                "x": lm["x"], "y": lm["y"], "z": lm["z"],
                "visibility": lm["visibility"],
            }

        # Compute angles
        angles = {
            "spine_angle": round(calc_forward_bend_dtl(frame_data), 1),
            "lead_arm_torso": round(calc_lead_arm_torso_angle(frame_data), 1),
            "trail_arm_torso": round(calc_trail_arm_torso_angle(frame_data), 1),
            "right_elbow": round(calc_elbow_angle(frame_data, "right"), 1),
            "left_elbow": round(calc_elbow_angle(frame_data, "left"), 1),
            "right_knee_flex": round(calc_knee_flex(frame_data, "right"), 1),
        }

        # Add wrist cock if visibility is sufficient
        rw_vis = frame_data["landmarks"]["right_wrist"]["visibility"]
        if rw_vis > 0.4:
            angles["right_wrist_cock"] = round(calc_wrist_cock(frame_data, "right"), 1)

        sh_info = calc_shoulder_turn_dtl(frame_data)

        phase_entry = {
            "swing_type": "iron",
            "view": "dtl",
            "phase": phase_name,
            "frame": frame_num,
            "timestamp_sec": frame_data["timestamp_sec"],
            "description": phase_info["description"],
            "angles": angles,
            "shoulder_hip_geometry": sh_info,
            "key_landmarks": key_landmarks,
        }

        phases.append(phase_entry)

    return {
        "metadata": {
            "golfer": "Tiger Woods",
            "year": 2000,
            "swing_type": "iron",
            "view": "down_the_line",
            "source_video": "Tiger Woods DL Iron.mov",
            "video_resolution": landmarks_data["summary"]["resolution"],
            "video_fps": landmarks_data["summary"]["fps"],
            "total_frames": landmarks_data["summary"]["total_frames"],
            "detection_rate_pct": landmarks_data["summary"]["detection_rate_pct"],
            "pose_model": "mediapipe_pose_landmarker_heavy",
            "notes": [
                "DTL view compresses spine angle (appears lower than actual 3D value)",
                "Left-side landmarks have lower visibility due to body occlusion from this angle",
                "Shoulder/hip turn best measured from face-on view",
                "Spine angle maintenance across phases is the key DTL metric",
            ],
        },
        "phases": phases,
    }


def build_fo_reference(landmarks_data):
    """Build face-on reference data for all phases."""
    frames = landmarks_data["frames"]
    phases = []

    for phase_name, phase_info in FO_PHASES.items():
        frame_num = phase_info["frame"]
        frame_data = next(f for f in frames if f["frame"] == frame_num)

        # Extract key landmark positions
        key_landmarks = {}
        for lm_name in [
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle",
            "left_index", "right_index",
        ]:
            lm = frame_data["landmarks"][lm_name]
            key_landmarks[lm_name] = {
                "x": lm["x"], "y": lm["y"], "z": lm["z"],
                "visibility": lm["visibility"],
            }

        # Compute angles
        angles = {
            "shoulder_line_angle": round(calc_shoulder_turn_fo(frame_data), 1),
            "hip_line_angle": round(calc_hip_turn_fo(frame_data), 1),
            "x_factor": round(calc_shoulder_hip_separation_fo(frame_data), 1),
            "spine_tilt": round(calc_spine_tilt(frame_data), 1),
            "lead_arm_torso": round(calc_lead_arm_torso_angle(frame_data), 1),
            "right_knee_flex": round(calc_knee_flex(frame_data, "right"), 1),
            "left_knee_flex": round(calc_knee_flex(frame_data, "left"), 1),
            "right_elbow": round(calc_elbow_angle(frame_data, "right"), 1),
            "left_elbow": round(calc_elbow_angle(frame_data, "left"), 1),
        }

        phase_entry = {
            "swing_type": "iron",
            "view": "face_on",
            "phase": phase_name,
            "frame": frame_num,
            "timestamp_sec": frame_data["timestamp_sec"],
            "description": phase_info["description"],
            "angles": angles,
            "key_landmarks": key_landmarks,
        }

        phases.append(phase_entry)

    return {
        "metadata": {
            "golfer": "Tiger Woods",
            "year": 2000,
            "swing_type": "iron",
            "view": "face_on",
            "source_video": "Tiger Woods FO Iron.mov",
            "video_resolution": landmarks_data["summary"]["resolution"],
            "video_fps": landmarks_data["summary"]["fps"],
            "total_frames": landmarks_data["summary"]["total_frames"],
            "detection_rate_pct": landmarks_data["summary"]["detection_rate_pct"],
            "pose_model": "mediapipe_pose_landmarker_heavy",
            "notes": [
                "FO view compresses knee flex (appears straighter than actual 3D value)",
                "Shoulder/hip rotation measured via line angle relative to horizontal",
                "X-factor (shoulder-hip separation) is the key rotation metric from this view",
                "Spine tilt measured as lateral lean of spine from vertical",
            ],
        },
        "phases": phases,
    }


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")
    ref_dir = os.path.join(base_dir, "reference_data", "iron")
    os.makedirs(ref_dir, exist_ok=True)

    # Load landmark data
    dtl_data = load_landmarks(os.path.join(output_dir, "dtl_landmarks.json"))
    fo_data = load_landmarks(os.path.join(output_dir, "fo_landmarks.json"))

    # Build reference JSONs
    dtl_ref = build_dtl_reference(dtl_data)
    fo_ref = build_fo_reference(fo_data)

    # Save
    dtl_path = os.path.join(ref_dir, "tiger_2000_iron_dtl_reference.json")
    fo_path = os.path.join(ref_dir, "tiger_2000_iron_face_on_reference.json")

    with open(dtl_path, "w") as f:
        json.dump(dtl_ref, f, indent=2)
    print(f"Saved DTL reference: {dtl_path}")

    with open(fo_path, "w") as f:
        json.dump(fo_ref, f, indent=2)
    print(f"Saved FO reference: {fo_path}")

    # Print summary
    print(f"\n{'='*60}")
    print("REFERENCE DATA SUMMARY")
    print(f"{'='*60}")

    for label, ref in [("DTL", dtl_ref), ("FO", fo_ref)]:
        print(f"\n  {label} ({ref['metadata']['view']}):")
        print(f"    Golfer: {ref['metadata']['golfer']} ({ref['metadata']['year']})")
        print(f"    Swing type: {ref['metadata']['swing_type']}")
        print(f"    Detection rate: {ref['metadata']['detection_rate_pct']}%")
        print(f"    Phases:")
        for phase in ref["phases"]:
            print(f"      {phase['phase']:20s} frame={phase['frame']:3d}  t={phase['timestamp_sec']:.3f}s")
            for angle_name, angle_val in phase["angles"].items():
                print(f"        {angle_name:30s}: {angle_val}°")

    print(f"\n  Files saved to: {ref_dir}/")
    print(f"  Ready for Phase 1 integration.")


if __name__ == "__main__":
    main()
