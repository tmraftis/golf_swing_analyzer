"""Compute angle deltas between user and reference, rank differences."""

import logging

logger = logging.getLogger(__name__)

# Angles computed via atan2 that wrap around ±180°.
# These need angular difference (shortest path) instead of naive subtraction.
_WRAPAROUND_ANGLES = {"shoulder_line_angle", "hip_line_angle"}

# Weights for ranking angle importance.
# Higher weight = more significant when determining top faults.
# Only includes angles that survive the _EXCLUDE_ANGLES_FROM_RANKING filter.
#
# PROJECTION-AWARE WEIGHTING:
# Angles involving limbs that move toward/away from a single camera are
# heavily distorted by 2D projection.  arm-torso angles can have 30-50°
# of projection error in DTL view (arm moving along the camera axis).
# Knee flex has 5-15° of projection error.  These are downweighted so
# they don't dominate the top-3 over more reliable angles like spine
# and elbow measurements.
ANGLE_WEIGHTS = {
    # ── Reliable angles (< 5° projection error) ──────────────────
    # Spine angle maintenance is the #1 DTL metric
    ("spine_angle_dtl", "impact"): 1.5,
    ("spine_angle_dtl", "top"): 1.3,
    # Spine tilt at impact (reverse spine angle = injury risk)
    ("spine_tilt_fo", "impact"): 1.3,
    # Elbow angles — key swing plane indicators
    ("right_elbow", "top"): 1.2,
    ("left_elbow", "impact"): 1.3,
    # ── Projection-sensitive angles (downweighted) ────────────────
    # Arm-torso angles are fully excluded from ranking via _EXCLUDE_ANGLES_FROM_RANKING.
    # Knee flex: 5-15° projection error
    ("right_knee_flex", "address"): 0.7,
    ("right_knee_flex", "top"): 0.7,
    ("right_knee_flex", "impact"): 0.7,
    ("right_knee_flex", "follow_through"): 0.7,
    ("left_knee_flex", "address"): 0.7,
    ("left_knee_flex", "top"): 0.7,
    ("left_knee_flex", "impact"): 0.7,
    ("left_knee_flex", "follow_through"): 0.7,
}

# Minimum absolute delta (degrees) to consider a difference significant.
# Deltas below this floor are filtered out to prevent noise from surfacing.
MIN_DELTA_DEGREES = 5

# Angles to exclude from top-3 ranking entirely.
# These still appear in the angle comparison table for informational purposes
# — just not in the ranked coaching feedback or similarity rankings.
#
# shoulder_line_angle / hip_line_angle: measure 2D line tilt from horizontal,
#   NOT true 3D rotational turn. x_factor is derived from these two tilts.
#
# lead_arm_torso / trail_arm_torso: 15-50°+ projection error in DTL view
#   because the arm moves along the camera axis. A real 18° difference can
#   show as 66° in 2D, producing misleading "limited backswing arc" coaching.
_EXCLUDE_ANGLES_FROM_RANKING = {
    "shoulder_line_angle", "hip_line_angle", "x_factor",
    "lead_arm_torso", "trail_arm_torso",
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
                        if angle_name in _WRAPAROUND_ANGLES:
                            # Shortest angular distance for atan2-based angles
                            d = user_val - ref_val
                            d = (d + 180) % 360 - 180
                            phase_deltas[angle_name] = round(d, 1)
                        else:
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
                if abs(delta) < MIN_DELTA_DEGREES:
                    continue
                if angle_name in _EXCLUDE_ANGLES_FROM_RANKING:
                    continue

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

    # Select top 3 with view balance (max 2 from same view when multi-view)
    available_views = list(deltas.keys())
    max_per_view = 2 if len(available_views) > 1 else 3
    selected = []
    view_counts = {v: 0 for v in available_views}

    for diff in all_diffs:
        if len(selected) >= 3:
            break
        view = diff["view"]
        if view_counts.get(view, 0) >= max_per_view:
            continue
        view_counts[view] = view_counts.get(view, 0) + 1
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


def rank_similarities(
    deltas: dict,
    user_angles: dict,
    ref_angles: dict,
) -> list[dict]:
    """Rank all angle measurements by closeness to reference (smallest delta first).

    Returns a list of the top 3 most similar angles — the ones where the
    user most closely matches Tiger.  Only includes angles that survive the
    same exclusion filter as rank_differences for consistency.
    """
    all_sims = []

    for view, view_deltas in deltas.items():
        for phase, phase_deltas in view_deltas.items():
            for angle_name, delta in phase_deltas.items():
                if angle_name in _EXCLUDE_ANGLES_FROM_RANKING:
                    continue

                user_val = user_angles[view][phase]["angles"].get(angle_name)
                ref_val = ref_angles[view][phase]["angles"].get(angle_name)

                if user_val is None or ref_val is None:
                    continue

                all_sims.append(
                    {
                        "angle_name": angle_name,
                        "phase": phase,
                        "view": view,
                        "user_value": user_val,
                        "reference_value": ref_val,
                        "delta": delta,
                        "abs_delta": abs(delta),
                    }
                )

    # Sort by absolute delta (smallest first — most similar)
    all_sims.sort(key=lambda d: d["abs_delta"])

    # Select top 3 with view balance (max 2 from same view when multi-view)
    available_views = list(deltas.keys())
    max_per_view = 2 if len(available_views) > 1 else 3
    selected = []
    view_counts = {v: 0 for v in available_views}

    for sim in all_sims:
        if len(selected) >= 3:
            break
        view = sim["view"]
        if view_counts.get(view, 0) >= max_per_view:
            continue
        view_counts[view] = view_counts.get(view, 0) + 1
        selected.append(sim)

    # Add rank numbers and clean up
    for i, sim in enumerate(selected):
        sim["rank"] = i + 1
        sim.pop("abs_delta", None)

    logger.info(
        f"Top {len(selected)} similarities: "
        + ", ".join(
            f"{s['angle_name']}@{s['phase']} ({s['delta']:+.1f}°)"
            for s in selected
        )
    )

    return selected


def compute_similarity_score(deltas: dict) -> int:
    """Compute an overall similarity percentage from angle deltas.

    For each angle/phase pair the per-angle score is:
        max(0, 1 - |delta| / max_delta)
    where max_delta is scaled by projection reliability:
    - Reliable angles (spine, elbow, wrist): 45° → 0% similarity
    - Projection-sensitive angles (arm-torso, knee): wider tolerance

    The max_delta for projection-sensitive angles is widened rather than
    weighting the score, so a 60° arm-torso delta (which may be only ~20°
    in 3D) doesn't tank the overall score.

    The final score is the mean of all per-angle scores, as an integer 0-100.
    """
    scores: list[float] = []

    for view, view_deltas in deltas.items():
        for phase, phase_deltas in view_deltas.items():
            for angle_name, delta in phase_deltas.items():
                if not isinstance(delta, (int, float)):
                    continue
                # Widen the tolerance for projection-sensitive angles
                # so their inflated 2D deltas don't tank the score
                weight = ANGLE_WEIGHTS.get((angle_name, phase), 1.0)
                if weight < 1.0:
                    # e.g. 0.5 weight → max_delta = 45/0.5 = 90°
                    max_delta = 45.0 / weight
                else:
                    max_delta = 45.0
                scores.append(max(0.0, 1.0 - abs(delta) / max_delta))

    if not scores:
        return 0

    return round(sum(scores) / len(scores) * 100)
