"""Compute angle deltas between user and reference, rank differences."""

import logging

logger = logging.getLogger(__name__)

# Weights for ranking angle importance.
# Higher weight = more significant when determining top faults.
ANGLE_WEIGHTS = {
    ("lead_arm_torso", "top"): 1.5,
    ("spine_angle_dtl", "impact"): 1.5,
    ("x_factor", "top"): 1.3,
    ("shoulder_line_angle", "top"): 1.2,
    ("shoulder_line_angle", "impact"): 1.2,
    ("spine_tilt_fo", "impact"): 1.2,
    ("right_elbow", "top"): 1.1,
    ("left_elbow", "impact"): 1.1,
}


def compute_deltas(user_angles: dict, ref_angles: dict) -> dict:
    """Compute angle deltas: user - reference for each view/phase/angle.

    Args:
        user_angles: { "dtl": { "address": { "angles": {...} }, ... }, "fo": {...} }
        ref_angles: Same structure from reference_data.load_reference().

    Returns:
        Nested dict: { view: { phase: { angle_name: delta } } }
    """
    deltas = {}

    for view in ["dtl", "fo"]:
        if view not in user_angles or view not in ref_angles:
            continue

        deltas[view] = {}
        for phase in ["address", "top", "impact", "follow_through"]:
            if phase not in user_angles[view] or phase not in ref_angles[view]:
                continue

            user_phase_angles = user_angles[view][phase].get("angles", {})
            ref_phase_angles = ref_angles[view][phase].get("angles", {})

            phase_deltas = {}
            for angle_name, user_val in user_phase_angles.items():
                if angle_name in ref_phase_angles:
                    ref_val = ref_phase_angles[angle_name]
                    if isinstance(user_val, (int, float)) and isinstance(
                        ref_val, (int, float)
                    ):
                        phase_deltas[angle_name] = round(user_val - ref_val, 1)

            deltas[view][phase] = phase_deltas

    return deltas


def rank_differences(
    deltas: dict,
    user_angles: dict,
    ref_angles: dict,
) -> list[dict]:
    """Rank all angle differences by weighted absolute delta.

    Returns a list sorted by significance (most important first).
    Ensures no more than 2 differences come from the same view
    for balanced feedback.
    """
    all_diffs = []

    for view, view_deltas in deltas.items():
        for phase, phase_deltas in view_deltas.items():
            for angle_name, delta in phase_deltas.items():
                weight = ANGLE_WEIGHTS.get((angle_name, phase), 1.0)
                weighted_abs = abs(delta) * weight

                user_val = user_angles[view][phase]["angles"].get(angle_name)
                ref_val = ref_angles[view][phase]["angles"].get(angle_name)

                if user_val is None or ref_val is None:
                    continue

                all_diffs.append(
                    {
                        "angle_name": angle_name,
                        "phase": phase,
                        "view": view,
                        "user_value": user_val,
                        "reference_value": ref_val,
                        "delta": delta,
                        "weighted_abs": weighted_abs,
                    }
                )

    # Sort by weighted absolute delta (largest first)
    all_diffs.sort(key=lambda d: d["weighted_abs"], reverse=True)

    # Select top 3 with view balance (max 2 from same view)
    selected = []
    view_counts = {"dtl": 0, "fo": 0}

    for diff in all_diffs:
        if len(selected) >= 3:
            break
        view = diff["view"]
        if view_counts[view] >= 2:
            continue
        view_counts[view] += 1
        selected.append(diff)

    # Add rank numbers
    for i, diff in enumerate(selected):
        diff["rank"] = i + 1
        diff.pop("weighted_abs", None)

    logger.info(
        f"Top {len(selected)} differences: "
        + ", ".join(
            f"{d['angle_name']}@{d['phase']} ({d['delta']:+.1f}°)"
            for d in selected
        )
    )

    return selected
