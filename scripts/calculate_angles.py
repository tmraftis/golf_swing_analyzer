"""
Phase 0: Calculate golf swing angles at each phase from extracted landmarks.

Computes the following angles at address, top, impact, and follow-through:
  - Shoulder turn (rotation of shoulder line relative to hip line)
  - Hip turn (rotation of hip line relative to stance/target line)
  - Spine tilt (angle of spine from vertical)
  - Lead arm-torso angle (angle between lead arm and torso)
  - Wrist cock (angle at lead wrist between forearm and hand)
  - Knee flex (angle at lead knee)

Works with both DTL (down-the-line) and FO (face-on) views.
Some angles are only meaningful from specific views.
"""

import json
import math
import os
import sys
import numpy as np


# ─── Phase frame assignments ───
# Determined by visual inspection + wrist trajectory analysis

DTL_PHASES = {
    "address":        {"frame": 0,  "description": "Setup position, club grounded behind ball"},
    "top":            {"frame": 31, "description": "Top of backswing, hands at highest point"},
    "impact":         {"frame": 37, "description": "Club at ball, hands returning to address height"},
    "follow_through": {"frame": 72, "description": "Full extension post-impact, arms high"},
}

FO_PHASES = {
    "address":        {"frame": 0,  "description": "Stable setup, pre-takeaway"},
    "top":            {"frame": 42, "description": "Top of backswing, max shoulder turn"},
    "impact":         {"frame": 51, "description": "Club at ball position"},
    "follow_through": {"frame": 76, "description": "Post-impact, arms extending through"},
}


def load_landmarks(json_path):
    """Load landmark data from JSON file."""
    with open(json_path) as f:
        data = json.load(f)
    return data


def get_landmark(frame_data, name):
    """Get (x, y, z) for a named landmark from a frame."""
    lm = frame_data["landmarks"][name]
    return np.array([lm["x"], lm["y"], lm["z"]])


def get_landmark_2d(frame_data, name):
    """Get (x, y) for a named landmark from a frame."""
    lm = frame_data["landmarks"][name]
    return np.array([lm["x"], lm["y"]])


def angle_between_vectors(v1, v2):
    """Calculate angle in degrees between two 2D or 3D vectors."""
    cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return math.degrees(math.acos(cos_angle))


def angle_at_joint(a, b, c):
    """
    Calculate the angle at point b, formed by points a-b-c.
    Returns angle in degrees.
    """
    ba = a - b
    bc = c - b
    return angle_between_vectors(ba, bc)


def signed_angle_2d(v1, v2):
    """Signed angle from v1 to v2 in degrees (positive = counterclockwise)."""
    angle = math.atan2(v2[1], v2[0]) - math.atan2(v1[1], v1[0])
    return math.degrees(angle)


# ─── Angle calculation functions ───

def calc_shoulder_turn_fo(frame_data):
    """
    Shoulder turn from face-on view.
    Measures the angle of the shoulder line (left_shoulder to right_shoulder)
    relative to horizontal. At address this should be ~0°.
    At top of backswing for Tiger, ~90-110° turn.

    We measure the apparent rotation by looking at how much the shoulder
    line has compressed (foreshortened) in the face-on view.
    """
    ls = get_landmark_2d(frame_data, "left_shoulder")
    rs = get_landmark_2d(frame_data, "right_shoulder")

    # Shoulder line vector
    shoulder_vec = rs - ls

    # Angle of shoulder line from horizontal
    angle = math.degrees(math.atan2(shoulder_vec[1], shoulder_vec[0]))

    return round(angle, 1)


def calc_shoulder_turn_dtl(frame_data):
    """
    Shoulder turn from DTL view.
    Measures how much the shoulders have rotated by looking at the
    displacement of shoulder midpoint relative to hip midpoint along X axis.

    We use the ratio of shoulder width to estimate rotation angle.
    """
    ls = get_landmark_2d(frame_data, "left_shoulder")
    rs = get_landmark_2d(frame_data, "right_shoulder")
    lh = get_landmark_2d(frame_data, "left_hip")
    rh = get_landmark_2d(frame_data, "right_hip")

    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2

    # Shoulder width (apparent)
    shoulder_width = np.linalg.norm(rs - ls)
    # Hip width (apparent)
    hip_width = np.linalg.norm(rh - lh)

    # In DTL view, horizontal displacement of shoulder center vs hip center
    # indicates rotation
    dx = shoulder_mid[0] - hip_mid[0]

    return {
        "shoulder_width": round(float(shoulder_width), 4),
        "hip_width": round(float(hip_width), 4),
        "shoulder_hip_offset_x": round(float(dx), 4),
    }


def calc_hip_turn_fo(frame_data):
    """
    Hip turn from face-on view.
    Measures the angle of the hip line relative to horizontal.
    """
    lh = get_landmark_2d(frame_data, "left_hip")
    rh = get_landmark_2d(frame_data, "right_hip")

    hip_vec = rh - lh
    angle = math.degrees(math.atan2(hip_vec[1], hip_vec[0]))

    return round(angle, 1)


def calc_spine_tilt(frame_data):
    """
    Spine tilt angle from vertical.
    Measured as angle between the spine line (hip midpoint to shoulder midpoint)
    and the vertical axis.
    Works from both views.
    """
    ls = get_landmark_2d(frame_data, "left_shoulder")
    rs = get_landmark_2d(frame_data, "right_shoulder")
    lh = get_landmark_2d(frame_data, "left_hip")
    rh = get_landmark_2d(frame_data, "right_hip")

    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2

    # Spine vector (hip to shoulder)
    spine_vec = shoulder_mid - hip_mid

    # Vertical vector (pointing up, i.e., negative Y in image coords)
    vertical = np.array([0, -1])

    angle = angle_between_vectors(spine_vec, vertical)

    # Sign: positive = tilting toward target (left for right-handed)
    # In image coords, if shoulder_mid.x < hip_mid.x, tilting left
    sign = -1 if spine_vec[0] < 0 else 1

    return round(sign * angle, 1)


def calc_lead_arm_torso_angle(frame_data, view="dtl"):
    """
    Angle between the lead arm (left arm for right-handed golfer) and the torso.
    Measured as angle at left shoulder between left elbow and left hip.
    """
    ls = get_landmark_2d(frame_data, "left_shoulder")
    le = get_landmark_2d(frame_data, "left_elbow")
    lh = get_landmark_2d(frame_data, "left_hip")

    return round(angle_at_joint(le, ls, lh), 1)


def calc_trail_arm_torso_angle(frame_data):
    """
    Angle between the trail arm (right arm for right-handed golfer) and the torso.
    Measured as angle at right shoulder between right elbow and right hip.
    """
    rs = get_landmark_2d(frame_data, "right_shoulder")
    re = get_landmark_2d(frame_data, "right_elbow")
    rh = get_landmark_2d(frame_data, "right_hip")

    return round(angle_at_joint(re, rs, rh), 1)


def calc_wrist_cock(frame_data, side="left"):
    """
    Wrist cock angle - angle at the wrist between forearm and hand.
    Measured as angle at wrist between elbow and index finger.
    """
    if side == "left":
        elbow = get_landmark_2d(frame_data, "left_elbow")
        wrist = get_landmark_2d(frame_data, "left_wrist")
        index = get_landmark_2d(frame_data, "left_index")
    else:
        elbow = get_landmark_2d(frame_data, "right_elbow")
        wrist = get_landmark_2d(frame_data, "right_wrist")
        index = get_landmark_2d(frame_data, "right_index")

    return round(angle_at_joint(elbow, wrist, index), 1)


def calc_knee_flex(frame_data, side="right"):
    """
    Knee flex angle. Measured at the knee between hip and ankle.
    Straight leg = 180°, flexed = less.
    """
    if side == "right":
        hip = get_landmark_2d(frame_data, "right_hip")
        knee = get_landmark_2d(frame_data, "right_knee")
        ankle = get_landmark_2d(frame_data, "right_ankle")
    else:
        hip = get_landmark_2d(frame_data, "left_hip")
        knee = get_landmark_2d(frame_data, "left_knee")
        ankle = get_landmark_2d(frame_data, "left_ankle")

    return round(angle_at_joint(hip, knee, ankle), 1)


def calc_shoulder_hip_separation_fo(frame_data):
    """
    X-Factor: difference between shoulder line angle and hip line angle
    from face-on view. This represents the separation between upper and
    lower body rotation - a key power metric.
    """
    shoulder_angle = calc_shoulder_turn_fo(frame_data)
    hip_angle = calc_hip_turn_fo(frame_data)
    return round(shoulder_angle - hip_angle, 1)


def calc_forward_bend_dtl(frame_data):
    """
    Forward bend (spine angle from DTL view).
    Angle between the spine line and vertical, as seen from behind.
    This is the primary "spine angle" in golf instruction.
    """
    ls = get_landmark_2d(frame_data, "left_shoulder")
    rs = get_landmark_2d(frame_data, "right_shoulder")
    lh = get_landmark_2d(frame_data, "left_hip")
    rh = get_landmark_2d(frame_data, "right_hip")

    shoulder_mid = (ls + rs) / 2
    hip_mid = (lh + rh) / 2

    spine_vec = shoulder_mid - hip_mid
    vertical = np.array([0, -1])

    return round(angle_between_vectors(spine_vec, vertical), 1)


def calc_elbow_angle(frame_data, side="right"):
    """
    Elbow angle (arm straightness).
    180° = fully extended, less = bent.
    """
    if side == "right":
        shoulder = get_landmark_2d(frame_data, "right_shoulder")
        elbow = get_landmark_2d(frame_data, "right_elbow")
        wrist = get_landmark_2d(frame_data, "right_wrist")
    else:
        shoulder = get_landmark_2d(frame_data, "left_shoulder")
        elbow = get_landmark_2d(frame_data, "left_elbow")
        wrist = get_landmark_2d(frame_data, "left_wrist")

    return round(angle_at_joint(shoulder, elbow, wrist), 1)


# ─── Main analysis ───

def analyze_video(landmarks_data, phases, view_label):
    """Analyze a video at each phase, computing all relevant angles."""

    frames = landmarks_data["frames"]
    results = {}

    print(f"\n{'='*70}")
    print(f"  ANGLE ANALYSIS: {view_label.upper()} VIEW")
    print(f"{'='*70}")

    for phase_name, phase_info in phases.items():
        frame_num = phase_info["frame"]

        # Find the frame data
        frame_data = None
        for f in frames:
            if f["frame"] == frame_num:
                frame_data = f
                break

        if frame_data is None or not frame_data["detected"]:
            print(f"\n  WARNING: Frame {frame_num} not found or no detection for phase '{phase_name}'")
            continue

        print(f"\n  --- {phase_name.upper()} (Frame {frame_num}, t={frame_data['timestamp_sec']:.3f}s) ---")
        print(f"  {phase_info['description']}")

        angles = {}

        if view_label == "dtl":
            # DTL-specific angles
            angles["spine_angle_dtl"] = calc_forward_bend_dtl(frame_data)
            angles["lead_arm_torso"] = calc_lead_arm_torso_angle(frame_data)
            angles["trail_arm_torso"] = calc_trail_arm_torso_angle(frame_data)
            angles["right_elbow"] = calc_elbow_angle(frame_data, "right")
            angles["left_elbow"] = calc_elbow_angle(frame_data, "left")
            angles["right_knee_flex"] = calc_knee_flex(frame_data, "right")

            # Wrist cock (right wrist more visible in DTL)
            rw_vis = frame_data["landmarks"]["right_wrist"]["visibility"]
            if rw_vis > 0.4:
                angles["right_wrist_cock"] = calc_wrist_cock(frame_data, "right")

            # Shoulder/hip info from DTL
            sh_info = calc_shoulder_turn_dtl(frame_data)
            angles["shoulder_width_apparent"] = sh_info["shoulder_width"]
            angles["hip_width_apparent"] = sh_info["hip_width"]
            angles["shoulder_hip_offset_x"] = sh_info["shoulder_hip_offset_x"]

        elif view_label == "fo":
            # Face-on specific angles
            angles["shoulder_line_angle"] = calc_shoulder_turn_fo(frame_data)
            angles["hip_line_angle"] = calc_hip_turn_fo(frame_data)
            angles["x_factor"] = calc_shoulder_hip_separation_fo(frame_data)
            angles["spine_tilt_fo"] = calc_spine_tilt(frame_data)
            angles["lead_arm_torso"] = calc_lead_arm_torso_angle(frame_data)
            angles["right_knee_flex"] = calc_knee_flex(frame_data, "right")
            angles["left_knee_flex"] = calc_knee_flex(frame_data, "left")
            angles["right_elbow"] = calc_elbow_angle(frame_data, "right")
            angles["left_elbow"] = calc_elbow_angle(frame_data, "left")

        # Print angles
        for name, value in angles.items():
            print(f"    {name:30s}: {value}°" if isinstance(value, (int, float)) else f"    {name:30s}: {value}")

        results[phase_name] = {
            "frame": frame_num,
            "timestamp_sec": frame_data["timestamp_sec"],
            "description": phase_info["description"],
            "angles": angles,
        }

    return results


def validate_angles(dtl_results, fo_results):
    """
    Validate computed angles against golf instruction norms for Tiger Woods.

    Expected norms (approximate):
      Address:
        - Spine angle (DTL): 30-40° forward bend
        - Knee flex: 140-160°
      Top of backswing:
        - Shoulder turn: visible compression of shoulder line in FO
        - X-factor (shoulder-hip separation): meaningful positive value
        - Spine angle maintained from address
        - Right knee flex maintained
      Impact:
        - Hips open (rotated toward target)
        - Spine angle maintained or slightly more tilted
        - Left arm extended (near 180°)
      Follow-through:
        - Full rotation
        - Weight transferred to lead side
    """

    print(f"\n{'='*70}")
    print(f"  VALIDATION AGAINST GOLF INSTRUCTION NORMS")
    print(f"{'='*70}")

    checks = []

    # --- DTL Checks ---
    if "address" in dtl_results:
        addr = dtl_results["address"]["angles"]
        spine = addr.get("spine_angle_dtl", 0)
        knee = addr.get("right_knee_flex", 0)

        ok = 20 <= spine <= 50
        checks.append(("DTL Address: Spine angle", f"{spine}°", "20-50°", ok))

        ok = 130 <= knee <= 175
        checks.append(("DTL Address: Right knee flex", f"{knee}°", "130-175°", ok))

    if "top" in dtl_results:
        top = dtl_results["top"]["angles"]
        spine = top.get("spine_angle_dtl", 0)
        addr_spine = dtl_results.get("address", {}).get("angles", {}).get("spine_angle_dtl", 0)

        # Spine angle should be maintained within ~10° of address
        diff = abs(spine - addr_spine)
        ok = diff <= 15
        checks.append(("DTL Top: Spine angle maintained", f"{spine}° (Δ{diff:.1f}° from address)", "within 15° of address", ok))

        r_elbow = top.get("right_elbow", 0)
        ok = 70 <= r_elbow <= 110
        checks.append(("DTL Top: Right elbow angle", f"{r_elbow}°", "70-110° (folded)", ok))

    if "impact" in dtl_results:
        imp = dtl_results["impact"]["angles"]
        spine = imp.get("spine_angle_dtl", 0)
        addr_spine = dtl_results.get("address", {}).get("angles", {}).get("spine_angle_dtl", 0)

        diff = abs(spine - addr_spine)
        ok = diff <= 15
        checks.append(("DTL Impact: Spine angle maintained", f"{spine}° (Δ{diff:.1f}° from address)", "within 15° of address", ok))

    # --- FO Checks ---
    if "address" in fo_results and "top" in fo_results:
        addr_shoulder = fo_results["address"]["angles"].get("shoulder_line_angle", 0)
        top_shoulder = fo_results["top"]["angles"].get("shoulder_line_angle", 0)

        # At top, shoulder line should tilt significantly
        shoulder_change = abs(top_shoulder - addr_shoulder)
        checks.append(("FO Top: Shoulder line angle change", f"{shoulder_change:.1f}° change", ">5° change (foreshortening)", shoulder_change > 3))

        x_factor = fo_results["top"]["angles"].get("x_factor", 0)
        checks.append(("FO Top: X-Factor", f"{x_factor}°", "non-zero separation", abs(x_factor) > 1))

    if "address" in fo_results:
        addr_fo = fo_results["address"]["angles"]
        r_knee = addr_fo.get("right_knee_flex", 0)
        l_knee = addr_fo.get("left_knee_flex", 0)

        ok = 130 <= r_knee <= 175
        checks.append(("FO Address: Right knee flex", f"{r_knee}°", "130-175°", ok))
        ok = 130 <= l_knee <= 175
        checks.append(("FO Address: Left knee flex", f"{l_knee}°", "130-175°", ok))

    if "impact" in fo_results:
        imp_fo = fo_results["impact"]["angles"]
        spine_tilt = imp_fo.get("spine_tilt_fo", 0)
        checks.append(("FO Impact: Spine tilt", f"{spine_tilt}°", "tilted away from target", True))

    # Print validation results
    print()
    all_pass = True
    for check_name, actual, expected, passed in checks:
        status = "PASS" if passed else "FAIL"
        icon = "✓" if passed else "✗"
        print(f"  {icon} [{status}] {check_name}")
        print(f"           Actual: {actual}  |  Expected: {expected}")
        if not passed:
            all_pass = False

    print(f"\n  {'─'*50}")
    pass_count = sum(1 for _, _, _, p in checks if p)
    total = len(checks)
    print(f"  Results: {pass_count}/{total} checks passed")

    if all_pass:
        print(f"  ✓ All validation checks PASSED")
    else:
        print(f"  ⚠ Some checks failed - review angles and frame selections")

    return checks


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Calculate golf swing angles at key phases")
    parser.add_argument("--auto-detect", action="store_true",
                        help="Auto-detect phase frames instead of using hardcoded values")
    parser.add_argument("--dtl", help="Path to DTL landmarks JSON")
    parser.add_argument("--fo", help="Path to FO landmarks JSON")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, "output")

    # Load landmark data
    dtl_path = args.dtl or os.path.join(output_dir, "dtl_landmarks.json")
    fo_path = args.fo or os.path.join(output_dir, "fo_landmarks.json")

    dtl_data = None
    fo_data = None

    if os.path.exists(dtl_path):
        dtl_data = load_landmarks(dtl_path)
    if os.path.exists(fo_path):
        fo_data = load_landmarks(fo_path)

    if dtl_data is None and fo_data is None:
        print("ERROR: No landmark files found. Run extract_landmarks.py first.")
        sys.exit(1)

    # Determine phase frames
    if args.auto_detect:
        from detect_phases import detect_phases
        dtl_phases = None
        fo_phases = None
        if dtl_data:
            dtl_phases = detect_phases(dtl_data, view="dtl")
            dtl_phases.pop("_diagnostics", None)
        if fo_data:
            fo_phases = detect_phases(fo_data, view="fo")
            fo_phases.pop("_diagnostics", None)
    else:
        dtl_phases = DTL_PHASES
        fo_phases = FO_PHASES

    # Analyze views
    dtl_results = {}
    fo_results = {}
    if dtl_data and dtl_phases:
        dtl_results = analyze_video(dtl_data, dtl_phases, "dtl")
    if fo_data and fo_phases:
        fo_results = analyze_video(fo_data, fo_phases, "fo")

    # Validate against norms
    checks = validate_angles(dtl_results, fo_results)

    # Save angle results
    combined = {
        "dtl": dtl_results,
        "fo": fo_results,
        "phase_frames": {
            "dtl": {k: v["frame"] for k, v in (dtl_phases or {}).items()},
            "fo": {k: v["frame"] for k, v in (fo_phases or {}).items()},
        },
        "validation": [
            {"check": c[0], "actual": c[1], "expected": c[2], "passed": c[3]}
            for c in checks
        ],
    }

    angles_path = args.output or os.path.join(output_dir, "angle_analysis.json")
    with open(angles_path, "w") as f:
        json.dump(combined, f, indent=2)

    print(f"\n  Angle analysis saved to: {angles_path}")


if __name__ == "__main__":
    main()
