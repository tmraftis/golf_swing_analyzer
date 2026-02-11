"""Rule-based feedback engine mapping angle deltas to coaching text."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FaultRule:
    """A rule that maps an angle delta to coaching feedback."""

    angle_name: str
    phase: str
    view: str
    min_delta: float | None  # Trigger if delta <= this (e.g., -15)
    max_delta: float | None  # Trigger if delta >= this (e.g., 15)
    severity: str  # major, moderate, minor
    title: str
    description: str  # Use {user_value}, {ref_value}, {abs_delta}
    coaching_tip: str


# Complete fault rule catalog for iron swings
FAULT_RULES: list[FaultRule] = [
    # --- DTL Faults ---
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="impact",
        view="dtl",
        min_delta=None,
        max_delta=None,
        severity="major",
        title="Spine Angle Change at Impact",
        description=(
            "Your spine angle at impact is {user_value:.1f} degrees compared to "
            "Tiger's {ref_value:.1f} degrees, a difference of {abs_delta:.1f} degrees. "
            "Maintaining spine angle through impact is critical for consistent ball striking."
        ),
        coaching_tip=(
            "Practice hitting balls with your head against a wall or door frame. "
            "Feel your spine angle stay constant from address through impact."
        ),
    ),
    FaultRule(
        angle_name="lead_arm_torso",
        phase="top",
        view="dtl",
        min_delta=-15.0,
        max_delta=None,
        severity="major",
        title="Limited Backswing Arm Lift",
        description=(
            "Your lead arm reaches {user_value:.1f} degrees of separation from your "
            "torso at the top, compared to Tiger's {ref_value:.1f} degrees. "
            "This {abs_delta:.1f}-degree gap limits your swing arc and power."
        ),
        coaching_tip=(
            "Focus on a fuller shoulder turn while keeping your left arm extended. "
            "Feel like your hands reach the 1 o'clock position at the top."
        ),
    ),
    FaultRule(
        angle_name="lead_arm_torso",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=15.0,
        severity="moderate",
        title="Overswinging Past Parallel",
        description=(
            "Your lead arm separation at the top is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Overswinging reduces control "
            "and consistency."
        ),
        coaching_tip=(
            "Try stopping your backswing when you feel your shoulder turn is "
            "complete. Use a mirror to check your top position."
        ),
    ),
    FaultRule(
        angle_name="right_elbow",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=20.0,
        severity="major",
        title="Flying Right Elbow",
        description=(
            "Your right elbow angle at the top is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. A wider elbow gets the club off-plane "
            "and makes it harder to return squarely at impact."
        ),
        coaching_tip=(
            "Keep a headcover or towel under your right arm during practice swings. "
            "Your right elbow should point down, not out."
        ),
    ),
    FaultRule(
        angle_name="left_elbow",
        phase="impact",
        view="dtl",
        min_delta=-15.0,
        max_delta=None,
        severity="major",
        title="Chicken Wing at Impact",
        description=(
            "Your left elbow is {user_value:.1f} degrees at impact compared to "
            "Tiger's {ref_value:.1f} degrees. A bent lead arm at impact causes "
            "inconsistent contact and loss of power."
        ),
        coaching_tip=(
            "Focus on extending your lead arm through the ball. Practice "
            "one-arm swings with your left arm to build extension."
        ),
    ),
    FaultRule(
        angle_name="right_knee_flex",
        phase="address",
        view="dtl",
        min_delta=-15.0,
        max_delta=None,
        severity="moderate",
        title="Excessive Knee Flex at Setup",
        description=(
            "Your right knee flex at address is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Too much knee bend can restrict "
            "your hip turn and cause balance issues."
        ),
        coaching_tip=(
            "Set up with athletic posture - feel like you're about to "
            "field a ground ball. Knees should be slightly flexed, not deeply bent."
        ),
    ),
    FaultRule(
        angle_name="right_knee_flex",
        phase="address",
        view="dtl",
        min_delta=None,
        max_delta=15.0,
        severity="moderate",
        title="Legs Too Straight at Setup",
        description=(
            "Your right knee flex at address is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Insufficient knee flex "
            "limits athletic movement."
        ),
        coaching_tip=(
            "Add a slight flex to your knees at address. You should feel "
            "balanced and ready to move in any direction."
        ),
    ),
    FaultRule(
        angle_name="right_wrist_cock",
        phase="top",
        view="dtl",
        min_delta=-20.0,
        max_delta=None,
        severity="moderate",
        title="Early Wrist Release",
        description=(
            "Your wrist cock at the top is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Losing wrist angle too early "
            "costs distance and control."
        ),
        coaching_tip=(
            "Practice half swings focusing on maintaining wrist hinge "
            "until your hands pass your right thigh in the downswing."
        ),
    ),
    # --- Face-On Faults ---
    FaultRule(
        angle_name="shoulder_line_angle",
        phase="top",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="major",
        title="Incomplete Shoulder Turn",
        description=(
            "Your shoulder line angle at the top is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. An incomplete shoulder turn limits "
            "power generation and coil."
        ),
        coaching_tip=(
            "Feel your back face the target at the top of the swing. "
            "Practice with a club across your shoulders to check rotation."
        ),
    ),
    FaultRule(
        angle_name="hip_line_angle",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="major",
        title="Hip Rotation Timing Issue",
        description=(
            "Your hip line angle at impact is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees, a {abs_delta:.1f}-degree difference. "
            "Proper hip rotation is the engine of the downswing."
        ),
        coaching_tip=(
            "Start your downswing by bumping your left hip toward the target, "
            "then rotate. Feel like your belt buckle faces the target at impact."
        ),
    ),
    FaultRule(
        angle_name="x_factor",
        phase="top",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="major",
        title="Shoulder-Hip Separation Off",
        description=(
            "Your X-factor (shoulder-hip separation) at the top is "
            "{user_value:.1f} degrees versus Tiger's {ref_value:.1f} degrees. "
            "This separation creates the coil that generates power."
        ),
        coaching_tip=(
            "Focus on turning your shoulders more while restricting your hip turn. "
            "Feel the stretch in your core at the top of the backswing."
        ),
    ),
    FaultRule(
        angle_name="spine_tilt_fo",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="major",
        title="Reverse Spine Angle",
        description=(
            "Your spine tilt at impact is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Incorrect spine tilt at impact "
            "affects contact quality and can cause back strain."
        ),
        coaching_tip=(
            "Maintain your spine tilt through the ball. Feel like your "
            "right shoulder works under and through, not over and around."
        ),
    ),
    FaultRule(
        angle_name="lead_arm_torso",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="moderate",
        title="Arm-Body Connection Lost at Impact",
        description=(
            "Your arm-body angle at impact is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. Maintaining connection between "
            "your arms and body produces more consistent strikes."
        ),
        coaching_tip=(
            "Practice with a glove under your lead armpit. If the glove "
            "drops before impact, you're losing connection."
        ),
    ),
    FaultRule(
        angle_name="right_knee_flex",
        phase="top",
        view="fo",
        min_delta=None,
        max_delta=15.0,
        severity="major",
        title="Lower Body Sway",
        description=(
            "Your right knee flex at the top is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. A straightening trail leg "
            "indicates lateral sway rather than rotational loading."
        ),
        coaching_tip=(
            "Keep flex in your right knee throughout the backswing. "
            "Practice with a ball under the outside of your right foot."
        ),
    ),
    FaultRule(
        angle_name="left_knee_flex",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=None,
        severity="moderate",
        title="Lead Leg Position at Impact",
        description=(
            "Your left knee flex at impact is {user_value:.1f} degrees versus "
            "Tiger's {ref_value:.1f} degrees. The lead leg's position "
            "at impact affects energy transfer to the ball."
        ),
        coaching_tip=(
            "Feel your left leg firm up through impact. "
            "Practice step-through drills to feel proper weight transfer."
        ),
    ),
]


def _rule_matches(rule: FaultRule, delta: float) -> bool:
    """Check if a rule's delta condition is met."""
    # For rules with specific thresholds
    if rule.min_delta is not None and delta <= rule.min_delta:
        return True
    if rule.max_delta is not None and delta >= rule.max_delta:
        return True
    # For rules without specific thresholds (None/None),
    # trigger if the absolute delta is significant (> 8 degrees)
    if rule.min_delta is None and rule.max_delta is None:
        return abs(delta) > 8
    return False


def generate_feedback(
    ranked_diffs: list[dict],
    user_angles: dict,
    ref_angles: dict,
) -> list[dict]:
    """Generate coaching feedback for the top differences.

    Takes the ranked differences from comparison_engine and enriches
    them with fault-specific coaching text from the rule catalog.

    Args:
        ranked_diffs: List from comparison_engine.rank_differences().
        user_angles: User angle results by view.
        ref_angles: Reference angle results by view.

    Returns:
        List of top differences with added severity, title,
        description, and coaching_tip fields.
    """
    enriched = []

    for diff in ranked_diffs:
        angle_name = diff["angle_name"]
        phase = diff["phase"]
        view = diff["view"]
        delta = diff["delta"]
        user_val = diff["user_value"]
        ref_val = diff["reference_value"]
        abs_delta = abs(delta)

        # Find the best matching rule
        matched_rule = None
        for rule in FAULT_RULES:
            if (
                rule.angle_name == angle_name
                and rule.phase == phase
                and rule.view == view
                and _rule_matches(rule, delta)
            ):
                matched_rule = rule
                break

        if matched_rule:
            description = matched_rule.description.format(
                user_value=user_val,
                ref_value=ref_val,
                abs_delta=abs_delta,
                delta=delta,
            )
            enriched.append(
                {
                    **diff,
                    "severity": matched_rule.severity,
                    "title": matched_rule.title,
                    "description": description,
                    "coaching_tip": matched_rule.coaching_tip,
                }
            )
        else:
            # Generic fallback for angles without a specific rule
            enriched.append(
                {
                    **diff,
                    "severity": "moderate" if abs_delta > 10 else "minor",
                    "title": f"{_format_angle_name(angle_name)} Difference at {_format_phase(phase)}",
                    "description": (
                        f"Your {_format_angle_name(angle_name).lower()} "
                        f"at {_format_phase(phase).lower()} is "
                        f"{user_val:.1f} degrees compared to Tiger's {ref_val:.1f} "
                        f"degrees, a difference of {abs_delta:.1f} degrees."
                    ),
                    "coaching_tip": (
                        f"Focus on matching Tiger's {_format_angle_name(angle_name).lower()} "
                        f"at the {_format_phase(phase).lower()} position. "
                        f"Film yourself and compare side by side."
                    ),
                }
            )

    logger.info(f"Generated feedback for {len(enriched)} differences")
    return enriched


def _format_angle_name(name: str) -> str:
    """Convert angle_name to human-readable format."""
    replacements = {
        "spine_angle_dtl": "Spine Angle",
        "lead_arm_torso": "Lead Arm-Torso Angle",
        "trail_arm_torso": "Trail Arm-Torso Angle",
        "right_elbow": "Right Elbow Angle",
        "left_elbow": "Left Elbow Angle",
        "right_knee_flex": "Right Knee Flex",
        "left_knee_flex": "Left Knee Flex",
        "right_wrist_cock": "Wrist Cock",
        "shoulder_line_angle": "Shoulder Turn",
        "hip_line_angle": "Hip Rotation",
        "x_factor": "X-Factor",
        "spine_tilt_fo": "Spine Tilt",
    }
    return replacements.get(name, name.replace("_", " ").title())


def _format_phase(phase: str) -> str:
    """Convert phase name to human-readable format."""
    replacements = {
        "address": "Address",
        "top": "Top of Backswing",
        "impact": "Impact",
        "follow_through": "Follow-Through",
    }
    return replacements.get(phase, phase.replace("_", " ").title())
