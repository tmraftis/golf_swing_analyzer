"""Shared fixtures for backend tests."""

import pytest


# ---------------------------------------------------------------------------
# Angle fixtures — realistic values with known deltas from Tiger reference
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_user_angles_dtl():
    """Amateur DTL angles with known faults:
    - spine_angle_dtl @ impact: +11.3° (early extension)
    - left_elbow @ impact: -17.5° (chicken wing)
    - lead_arm_torso @ top: -16.7° (limited backswing arc)
    """
    return {
        "dtl": {
            "address": {
                "frame": 15, "timestamp_sec": 0.5, "description": "Address",
                "angles": {
                    "spine_angle_dtl": 28.0,
                    "right_elbow": 170.0,
                    "right_knee_flex": 160.0,
                },
            },
            "top": {
                "frame": 45, "timestamp_sec": 1.5, "description": "Top",
                "angles": {
                    "spine_angle_dtl": 25.0,
                    "lead_arm_torso": 105.0,
                    "right_elbow": 80.0,
                    "right_knee_flex": 178.0,
                    "right_wrist_cock": 160.0,
                },
            },
            "impact": {
                "frame": 52, "timestamp_sec": 1.73, "description": "Impact",
                "angles": {
                    "spine_angle_dtl": 30.0,
                    "lead_arm_torso": 35.0,
                    "left_elbow": 158.0,
                    "right_knee_flex": 150.0,
                },
            },
            "follow_through": {
                "frame": 80, "timestamp_sec": 2.67, "description": "Follow-Through",
                "angles": {
                    "spine_angle_dtl": 12.0,
                    "lead_arm_torso": 75.0,
                    "left_elbow": 85.0,
                    "right_knee_flex": 170.0,
                },
            },
        },
    }


@pytest.fixture
def sample_ref_angles_dtl():
    """Tiger DTL reference angles (from actual reference JSON after remap)."""
    return {
        "dtl": {
            "address": {
                "frame": 0, "timestamp_sec": 0.0,
                "angles": {
                    "spine_angle_dtl": 18.9,
                    "right_elbow": 172.6,
                    "right_knee_flex": 166.3,
                },
            },
            "top": {
                "frame": 31, "timestamp_sec": 1.24,
                "angles": {
                    "spine_angle_dtl": 18.4,
                    "lead_arm_torso": 121.7,
                    "right_elbow": 65.1,
                    "right_knee_flex": 171.1,
                    "right_wrist_cock": 174.5,
                },
            },
            "impact": {
                "frame": 37, "timestamp_sec": 1.48,
                "angles": {
                    "spine_angle_dtl": 18.7,
                    "lead_arm_torso": 26.6,
                    "left_elbow": 175.5,
                    "right_knee_flex": 154.3,
                },
            },
            "follow_through": {
                "frame": 72, "timestamp_sec": 2.88,
                "angles": {
                    "spine_angle_dtl": 8.4,
                    "lead_arm_torso": 79.7,
                    "left_elbow": 81.4,
                    "right_knee_flex": 171.2,
                },
            },
        },
    }


@pytest.fixture
def sample_user_angles_fo():
    """Amateur FO angles — includes atan2 wraparound test values."""
    return {
        "fo": {
            "address": {
                "frame": 10, "timestamp_sec": 0.33, "description": "Address",
                "angles": {
                    "shoulder_line_angle": 177.0,
                    "hip_line_angle": 10.0,
                    "spine_tilt_fo": 2.0,
                    "left_knee_flex": 160.0,
                },
            },
            "top": {
                "frame": 42, "timestamp_sec": 1.4, "description": "Top",
                "angles": {
                    "shoulder_line_angle": 150.0,
                    "hip_line_angle": 170.0,
                    "x_factor": 20.0,
                    "spine_tilt_fo": 10.0,
                    "lead_arm_torso": 100.0,
                },
            },
            "impact": {
                "frame": 51, "timestamp_sec": 1.7, "description": "Impact",
                "angles": {
                    "shoulder_line_angle": -170.0,
                    "hip_line_angle": -175.0,
                    "spine_tilt_fo": 25.0,
                    "left_knee_flex": 168.0,
                    "left_elbow": 170.0,
                },
            },
            "follow_through": {
                "frame": 76, "timestamp_sec": 2.53, "description": "Follow-Through",
                "angles": {
                    "shoulder_line_angle": -160.0,
                    "hip_line_angle": -165.0,
                    "spine_tilt_fo": 15.0,
                },
            },
        },
    }


@pytest.fixture
def sample_ref_angles_fo():
    """Tiger FO reference angles — shoulder_line_angle near -180 boundary."""
    return {
        "fo": {
            "address": {
                "frame": 0, "timestamp_sec": 0.0,
                "angles": {
                    "shoulder_line_angle": -169.0,
                    "hip_line_angle": 5.0,
                    "spine_tilt_fo": 1.0,
                    "left_knee_flex": 165.0,
                },
            },
            "top": {
                "frame": 42, "timestamp_sec": 1.68,
                "angles": {
                    "shoulder_line_angle": 145.0,
                    "hip_line_angle": 168.0,
                    "x_factor": 23.0,
                    "spine_tilt_fo": 8.0,
                    "lead_arm_torso": 115.0,
                },
            },
            "impact": {
                "frame": 51, "timestamp_sec": 2.04,
                "angles": {
                    "shoulder_line_angle": -175.0,
                    "hip_line_angle": -178.0,
                    "spine_tilt_fo": 18.0,
                    "left_knee_flex": 162.0,
                    "left_elbow": 174.0,
                },
            },
            "follow_through": {
                "frame": 76, "timestamp_sec": 3.04,
                "angles": {
                    "shoulder_line_angle": -155.0,
                    "hip_line_angle": -160.0,
                    "spine_tilt_fo": 12.0,
                },
            },
        },
    }


@pytest.fixture
def sample_user_angles_both(sample_user_angles_dtl, sample_user_angles_fo):
    """Combined DTL + FO user angles."""
    return {**sample_user_angles_dtl, **sample_user_angles_fo}


@pytest.fixture
def sample_ref_angles_both(sample_ref_angles_dtl, sample_ref_angles_fo):
    """Combined DTL + FO reference angles."""
    return {**sample_ref_angles_dtl, **sample_ref_angles_fo}


# ---------------------------------------------------------------------------
# Phase / landmarks fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_phases():
    """Pre-computed phases dict (typical output of detect_swing_phases)."""
    return {
        "address": {"frame": 10, "description": "Address"},
        "top": {"frame": 40, "description": "Top of backswing"},
        "impact": {"frame": 50, "description": "Impact"},
        "follow_through": {"frame": 75, "description": "Follow-through"},
    }


@pytest.fixture
def sample_landmarks_data():
    """Minimal 100-frame landmarks data with all frames detected."""
    frames = []
    for i in range(100):
        frames.append({
            "frame": i,
            "timestamp_sec": i / 30.0,
            "detected": True,
            "landmarks": {
                "right_wrist": {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95},
                "left_wrist": {"x": 0.5, "y": 0.5, "z": 0.0, "visibility": 0.95},
                "right_shoulder": {"x": 0.45, "y": 0.3, "z": 0.0, "visibility": 0.9},
                "left_shoulder": {"x": 0.55, "y": 0.3, "z": 0.0, "visibility": 0.9},
                "right_hip": {"x": 0.47, "y": 0.5, "z": 0.0, "visibility": 0.9},
                "left_hip": {"x": 0.53, "y": 0.5, "z": 0.0, "visibility": 0.9},
                "right_knee": {"x": 0.47, "y": 0.7, "z": 0.0, "visibility": 0.9},
                "left_knee": {"x": 0.53, "y": 0.7, "z": 0.0, "visibility": 0.9},
                "right_ankle": {"x": 0.47, "y": 0.9, "z": 0.0, "visibility": 0.9},
                "left_ankle": {"x": 0.53, "y": 0.9, "z": 0.0, "visibility": 0.9},
                "right_elbow": {"x": 0.45, "y": 0.4, "z": 0.0, "visibility": 0.9},
                "left_elbow": {"x": 0.55, "y": 0.4, "z": 0.0, "visibility": 0.9},
            },
        })
    return {
        "summary": {"fps": 30.0, "total_frames": 100, "detection_rate_pct": 100.0},
        "frames": frames,
    }
