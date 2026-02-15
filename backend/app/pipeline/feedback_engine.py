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


# Complete fault rule catalog for iron swings.
# Every rule has explicit directional thresholds — no catch-all rules.
# Each angle/phase has separate "too much" and "too little" rules with
# distinct coaching text so the user gets actionable, directional advice.
FAULT_RULES: list[FaultRule] = [
    # =====================================================================
    # DTL FAULTS
    # =====================================================================

    # --- Spine Angle (DTL) — address baseline ---
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="address",
        view="dtl",
        min_delta=None,
        max_delta=8.0,   # user more upright than Tiger
        severity="moderate",
        title="Too Upright at Setup",
        description=(
            "Your spine angle at address is {user_value:.1f}° compared to Tiger's "
            "{ref_value:.1f}° — you're standing {abs_delta:.1f}° more upright. "
            "Insufficient forward bend limits your ability to rotate on plane."
        ),
        coaching_tip=(
            "Hinge more from your hips at setup. Feel like your belt buckle "
            "points toward the ball. Your arms should hang naturally below your shoulders."
        ),
    ),
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="address",
        view="dtl",
        min_delta=-8.0,   # user bent over more than Tiger
        max_delta=None,
        severity="moderate",
        title="Too Much Forward Bend at Setup",
        description=(
            "Your spine angle at address is {user_value:.1f}° compared to Tiger's "
            "{ref_value:.1f}° — you're bending {abs_delta:.1f}° more forward. "
            "Excessive bend leads to balance issues and restricted rotation."
        ),
        coaching_tip=(
            "Stand slightly taller at address. Feel athletic, like a goalkeeper "
            "ready to move. Your weight should be balanced on the balls of your feet."
        ),
    ),

    # --- Spine Angle (DTL) — impact (the key DTL metric) ---
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="impact",
        view="dtl",
        min_delta=None,
        max_delta=6.0,   # user stood up through impact
        severity="major",
        title="Early Extension (Loss of Posture)",
        description=(
            "Your spine angle at impact is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — you've stood up {abs_delta:.1f}° through the ball. "
            "This is one of the most common amateur faults and causes thin shots and blocks."
        ),
        coaching_tip=(
            "Practice hitting balls with your backside against a wall or chair. "
            "If you lose contact before impact, you're extending early. "
            "Feel your belt buckle stay pointed at the ball through impact."
        ),
    ),
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="impact",
        view="dtl",
        min_delta=-6.0,   # user dipped toward ball
        max_delta=None,
        severity="major",
        title="Excessive Forward Bend at Impact",
        description=(
            "Your spine angle at impact is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — you've dipped {abs_delta:.1f}° more forward. "
            "Excessive dip causes fat shots and inconsistent low point."
        ),
        coaching_tip=(
            "Maintain your address spine angle through the swing. A drill: "
            "place a club across your shoulders and turn — if the club points "
            "at the ground in front of the ball at impact, you're dipping."
        ),
    ),

    # --- Spine Angle (DTL) — top of backswing ---
    FaultRule(
        angle_name="spine_angle_dtl",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=8.0,   # stood up during backswing
        severity="moderate",
        title="Posture Loss in Backswing",
        description=(
            "Your spine angle at the top is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — you've straightened {abs_delta:.1f}° during the "
            "backswing. Losing posture early makes it hard to recover at impact."
        ),
        coaching_tip=(
            "Feel like you maintain your address posture throughout the backswing. "
            "A slight knee flex and steady head position help preserve spine angle."
        ),
    ),

    # --- Lead Arm-Torso (DTL, top) ---
    FaultRule(
        angle_name="lead_arm_torso",
        phase="top",
        view="dtl",
        min_delta=-15.0,
        max_delta=None,
        severity="major",
        title="Limited Backswing Arc",
        description=(
            "Your lead arm reaches {user_value:.1f}° of separation from your "
            "torso at the top, compared to Tiger's {ref_value:.1f}°. "
            "This {abs_delta:.1f}° gap limits your swing arc and power."
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
            "Your lead arm separation at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}°. Overswinging {abs_delta:.1f}° past "
            "parallel reduces control and consistency."
        ),
        coaching_tip=(
            "Try stopping your backswing when you feel your shoulder turn is "
            "complete. Use a mirror to check your top position — the club "
            "shaft should not dip past parallel."
        ),
    ),

    # --- Lead Arm-Torso (DTL, impact) ---
    FaultRule(
        angle_name="lead_arm_torso",
        phase="impact",
        view="dtl",
        min_delta=None,
        max_delta=10.0,   # arms too far from body
        severity="moderate",
        title="Arms Cast Away from Body at Impact",
        description=(
            "Your lead arm-torso angle at impact is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — your arms are {abs_delta:.1f}° further "
            "from your body. This casting motion loses lag and power."
        ),
        coaching_tip=(
            "Feel your lead arm reconnect with your chest through impact. "
            "Practice with a glove under your lead armpit — if it drops "
            "before impact, you're casting."
        ),
    ),

    # --- Right Elbow (DTL, top) ---
    FaultRule(
        angle_name="right_elbow",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=15.0,   # elbow too open / flying
        severity="major",
        title="Flying Right Elbow",
        description=(
            "Your right elbow angle at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}°. A {abs_delta:.1f}° wider elbow gets "
            "the club off-plane and makes it harder to return square at impact."
        ),
        coaching_tip=(
            "Keep a headcover or towel under your right arm during practice swings. "
            "Your right elbow should point down, not out, at the top."
        ),
    ),
    FaultRule(
        angle_name="right_elbow",
        phase="top",
        view="dtl",
        min_delta=-15.0,   # elbow too tight / cramped
        max_delta=None,
        severity="moderate",
        title="Cramped Right Elbow at Top",
        description=(
            "Your right elbow angle at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — it's {abs_delta:.1f}° more folded. "
            "An overly compact top position limits swing width and power."
        ),
        coaching_tip=(
            "Allow your right elbow to fold naturally — it should point "
            "roughly at the ground. Don't squeeze your arms tight to your body."
        ),
    ),

    # --- Left Elbow (DTL, impact) ---
    FaultRule(
        angle_name="left_elbow",
        phase="impact",
        view="dtl",
        min_delta=-12.0,   # bent lead arm at impact
        max_delta=None,
        severity="major",
        title="Chicken Wing at Impact",
        description=(
            "Your left elbow is {user_value:.1f}° at impact compared to "
            "Tiger's {ref_value:.1f}° — your lead arm is {abs_delta:.1f}° "
            "more bent. A bent lead arm at impact causes inconsistent "
            "contact and loss of power."
        ),
        coaching_tip=(
            "Focus on extending your lead arm through the ball. Practice "
            "one-arm swings with your left arm to build extension. "
            "Feel the back of your left hand driving toward the target."
        ),
    ),

    # --- Right Knee Flex (DTL, address) ---
    FaultRule(
        angle_name="right_knee_flex",
        phase="address",
        view="dtl",
        min_delta=-12.0,   # too much flex
        max_delta=None,
        severity="moderate",
        title="Excessive Knee Flex at Setup",
        description=(
            "Your right knee flex at address is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° more bent. "
            "Too much knee bend restricts your hip turn and causes balance issues."
        ),
        coaching_tip=(
            "Set up with athletic posture — feel like you're about to "
            "field a ground ball. Knees should be slightly flexed, not deeply bent."
        ),
    ),
    FaultRule(
        angle_name="right_knee_flex",
        phase="address",
        view="dtl",
        min_delta=None,
        max_delta=12.0,   # too straight
        severity="moderate",
        title="Legs Too Straight at Setup",
        description=(
            "Your right knee flex at address is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° straighter. "
            "Locked knees limit athletic movement and weight transfer."
        ),
        coaching_tip=(
            "Add a slight flex to your knees at address. You should feel "
            "balanced and ready to move in any direction."
        ),
    ),

    # --- Right Knee Flex (top, both views) ---
    FaultRule(
        angle_name="right_knee_flex",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=10.0,   # knee straightened (sway)
        severity="major",
        title="Trail Leg Straightening (Sway)",
        description=(
            "Your right knee flex at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — it's straightened {abs_delta:.1f}°. "
            "A straightening trail leg means lateral sway instead of rotation."
        ),
        coaching_tip=(
            "Keep flex in your right knee throughout the backswing. "
            "Feel like you're loading into the inside of your right foot. "
            "Practice with a ball under the outside of your right foot."
        ),
    ),
    FaultRule(
        angle_name="right_knee_flex",
        phase="top",
        view="fo",
        min_delta=None,
        max_delta=10.0,   # knee straightened (sway)
        severity="major",
        title="Lower Body Sway",
        description=(
            "Your right knee flex at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — it's straightened {abs_delta:.1f}°. "
            "A straightening trail leg indicates lateral sway rather than "
            "rotational loading."
        ),
        coaching_tip=(
            "Keep flex in your right knee throughout the backswing. "
            "Practice with a ball under the outside of your right foot."
        ),
    ),

    # --- Wrist Cock (DTL, top) ---
    FaultRule(
        angle_name="right_wrist_cock",
        phase="top",
        view="dtl",
        min_delta=-15.0,   # less wrist hinge
        max_delta=None,
        severity="moderate",
        title="Insufficient Wrist Hinge",
        description=(
            "Your wrist cock at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° less hinge. "
            "Losing wrist angle too early costs distance and control."
        ),
        coaching_tip=(
            "Practice half swings focusing on maintaining wrist hinge "
            "until your hands pass your right thigh in the downswing."
        ),
    ),
    FaultRule(
        angle_name="right_wrist_cock",
        phase="top",
        view="dtl",
        min_delta=None,
        max_delta=15.0,   # excessive wrist hinge
        severity="minor",
        title="Excessive Wrist Hinge",
        description=(
            "Your wrist cock at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° more hinged. "
            "While wrist hinge generates power, excessive hinge can "
            "make the clubface harder to control."
        ),
        coaching_tip=(
            "Let your wrists hinge naturally during the backswing. "
            "Avoid forcing or over-cocking — the hinge should feel effortless."
        ),
    ),

    # =====================================================================
    # FACE-ON FAULTS (only biomechanically reliable angles)
    # =====================================================================
    # Note: shoulder_line_angle, hip_line_angle, and x_factor are excluded
    # from ranking since they measure 2D line tilt, not true rotation.
    # The rules below cover the FO angles that ARE reliable.

    # --- Spine Tilt (FO, impact) ---
    FaultRule(
        angle_name="spine_tilt_fo",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=10.0,   # less tilt away (reverse spine)
        severity="major",
        title="Reverse Spine Angle at Impact",
        description=(
            "Your spine tilt at impact is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — you're {abs_delta:.1f}° more upright or leaning "
            "toward the target. This 'reverse spine' puts stress on your back "
            "and reduces power."
        ),
        coaching_tip=(
            "Feel your right shoulder work under and through, not over and around. "
            "At impact, your spine should tilt slightly away from the target. "
            "Practice slow-motion swings focusing on keeping your head behind the ball."
        ),
    ),
    FaultRule(
        angle_name="spine_tilt_fo",
        phase="impact",
        view="fo",
        min_delta=-10.0,   # excessive tilt away
        max_delta=None,
        severity="moderate",
        title="Excessive Spine Tilt at Impact",
        description=(
            "Your spine tilt at impact is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — you're leaning {abs_delta:.1f}° more away from "
            "the target. Excessive tilt can cause thin and topped shots."
        ),
        coaching_tip=(
            "Focus on rotating through the ball rather than hanging back. "
            "Feel your weight shift to your lead foot while maintaining "
            "a centered pivot."
        ),
    ),

    # --- Spine Tilt (FO, address) ---
    FaultRule(
        angle_name="spine_tilt_fo",
        phase="address",
        view="fo",
        min_delta=None,
        max_delta=8.0,
        severity="moderate",
        title="Setup Spine Tilt Too Upright",
        description=(
            "Your spine tilt at address is {user_value:.1f}° versus Tiger's "
            "{ref_value:.1f}° — {abs_delta:.1f}° more upright. A slight tilt "
            "away from the target at setup helps promote a proper impact position."
        ),
        coaching_tip=(
            "At address, let your trail hand sit lower on the grip, which "
            "naturally creates a slight spine tilt away from the target."
        ),
    ),

    # --- Lead Arm-Torso (FO, top) ---
    FaultRule(
        angle_name="lead_arm_torso",
        phase="top",
        view="fo",
        min_delta=-15.0,
        max_delta=None,
        severity="moderate",
        title="Restricted Shoulder Turn (Face-On)",
        description=(
            "Your lead arm-torso angle at the top is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° less rotation. "
            "A restricted turn limits power generation."
        ),
        coaching_tip=(
            "Turn your lead shoulder behind the ball at the top. "
            "Feel like your back faces the target at the top of the backswing."
        ),
    ),

    # --- Lead Arm-Torso (FO, impact) ---
    FaultRule(
        angle_name="lead_arm_torso",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=8.0,
        severity="moderate",
        title="Arm-Body Connection Lost at Impact",
        description=(
            "Your arm-body angle at impact is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° more separated. "
            "Maintaining connection between your arms and body produces "
            "more consistent strikes."
        ),
        coaching_tip=(
            "Practice with a glove under your lead armpit. If the glove "
            "drops before impact, you're losing connection."
        ),
    ),

    # --- Left Knee Flex (FO, impact) ---
    FaultRule(
        angle_name="left_knee_flex",
        phase="impact",
        view="fo",
        min_delta=-12.0,   # lead knee too bent
        max_delta=None,
        severity="moderate",
        title="Lead Knee Collapsing at Impact",
        description=(
            "Your left knee flex at impact is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° more bent. "
            "A collapsing lead knee bleeds power and causes inconsistent contact."
        ),
        coaching_tip=(
            "Feel your left leg firm up through impact. The lead knee should "
            "straighten slightly, creating a solid post to rotate around. "
            "Practice step-through drills to feel proper weight transfer."
        ),
    ),
    FaultRule(
        angle_name="left_knee_flex",
        phase="impact",
        view="fo",
        min_delta=None,
        max_delta=12.0,   # lead knee too straight / locked
        severity="minor",
        title="Locked Lead Knee at Impact",
        description=(
            "Your left knee flex at impact is {user_value:.1f}° versus "
            "Tiger's {ref_value:.1f}° — {abs_delta:.1f}° straighter. "
            "While a firm lead leg is good, a fully locked knee limits rotation "
            "and can stress the joint."
        ),
        coaching_tip=(
            "Allow a slight flex in your lead knee at impact. "
            "It should be firm but not rigid."
        ),
    ),

    # --- Left Elbow (FO, impact) ---
    FaultRule(
        angle_name="left_elbow",
        phase="impact",
        view="fo",
        min_delta=-12.0,
        max_delta=None,
        severity="major",
        title="Lead Arm Breakdown at Impact",
        description=(
            "Your left elbow is {user_value:.1f}° at impact versus Tiger's "
            "{ref_value:.1f}° — {abs_delta:.1f}° more bent. A bent lead arm "
            "through impact causes inconsistent contact and loss of power."
        ),
        coaching_tip=(
            "Focus on extending your lead arm through the ball. The left arm "
            "should be nearly straight at impact. Practice half-swings focusing "
            "on lead arm extension."
        ),
    ),

    # --- Right Elbow (FO, impact) ---
    FaultRule(
        angle_name="right_elbow",
        phase="impact",
        view="fo",
        min_delta=-10.0,   # trail arm too bent still
        max_delta=None,
        severity="moderate",
        title="Trail Arm Still Bent at Impact",
        description=(
            "Your right elbow is {user_value:.1f}° at impact versus Tiger's "
            "{ref_value:.1f}° — {abs_delta:.1f}° more bent. The trail arm should "
            "be extending through impact to deliver power."
        ),
        coaching_tip=(
            "Feel your right arm extending through the ball, like you're "
            "throwing a ball underhand toward the target. The right arm "
            "straightens just after impact."
        ),
    ),
]


def _rule_matches(rule: FaultRule, delta: float) -> bool:
    """Check if a rule's directional delta condition is met.

    Every rule should have at least one of min_delta or max_delta set.
    Rules with both None will never match — this is intentional to prevent
    catch-all behavior that produces noisy, non-directional feedback.
    """
    if rule.min_delta is not None and delta <= rule.min_delta:
        return True
    if rule.max_delta is not None and delta >= rule.max_delta:
        return True
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
            # Directional fallback for angles without a specific rule.
            # Gives the user a sense of *which way* they're off.
            angle_label = _format_angle_name(angle_name).lower()
            phase_label = _format_phase(phase).lower()
            direction = "more" if delta > 0 else "less"

            enriched.append(
                {
                    **diff,
                    "severity": "moderate" if abs_delta > 12 else "minor",
                    "title": f"{_format_angle_name(angle_name)} at {_format_phase(phase)}",
                    "description": (
                        f"Your {angle_label} at {phase_label} is "
                        f"{user_val:.1f}° compared to Tiger's {ref_val:.1f}° — "
                        f"{abs_delta:.1f}° {direction}. "
                        f"Review your {phase_label} position in the side-by-side "
                        f"video to see the difference."
                    ),
                    "coaching_tip": (
                        f"Compare your {phase_label} position to Tiger's using "
                        f"the video player above. Focus on your {angle_label} — "
                        f"yours is {abs_delta:.1f}° {direction} than Tiger's at "
                        f"this point in the swing."
                    ),
                }
            )

    logger.info(f"Generated feedback for {len(enriched)} differences")
    return enriched


def generate_similarity_titles(ranked_sims: list[dict]) -> list[dict]:
    """Add human-readable titles to top similarity entries.

    Similarities don't need coaching tips — just a clear label.
    """
    enriched = []
    for sim in ranked_sims:
        angle_name = sim["angle_name"]
        phase = sim["phase"]
        title = f"{_format_angle_name(angle_name)} at {_format_phase(phase)}"
        enriched.append({**sim, "title": title})
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
        "shoulder_line_angle": "Shoulder Tilt",
        "hip_line_angle": "Hip Tilt",
        "x_factor": "Shoulder-Hip Tilt Gap",
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
