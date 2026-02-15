"""Tests for app.pipeline.feedback_engine — rule matching and coaching feedback."""

import pytest

from app.pipeline.feedback_engine import (
    FaultRule,
    _format_angle_name,
    _rule_matches,
    generate_feedback,
)


# ===================================================================
# _rule_matches
# ===================================================================


class TestRuleMatches:
    """Test directional delta matching logic."""

    def _make_rule(self, min_delta=None, max_delta=None):
        return FaultRule(
            angle_name="test_angle",
            phase="impact",
            view="dtl",
            min_delta=min_delta,
            max_delta=max_delta,
            severity="major",
            title="Test",
            description="Test {user_value:.1f}",
            coaching_tip="Test tip",
        )

    def test_max_delta_trigger(self):
        rule = self._make_rule(max_delta=8.0)
        assert _rule_matches(rule, 9.0) is True
        assert _rule_matches(rule, 7.0) is False

    def test_min_delta_trigger(self):
        rule = self._make_rule(min_delta=-8.0)
        assert _rule_matches(rule, -9.0) is True
        assert _rule_matches(rule, -7.0) is False

    def test_at_threshold(self):
        """Exactly at boundary should trigger (>= and <=)."""
        assert _rule_matches(self._make_rule(max_delta=8.0), 8.0) is True
        assert _rule_matches(self._make_rule(min_delta=-8.0), -8.0) is True

    def test_both_none_never_matches(self):
        rule = self._make_rule(min_delta=None, max_delta=None)
        assert _rule_matches(rule, 100.0) is False
        assert _rule_matches(rule, -100.0) is False
        assert _rule_matches(rule, 0.0) is False


# ===================================================================
# generate_feedback
# ===================================================================


class TestGenerateFeedback:
    """Test coaching feedback generation with rule matching and fallback."""

    def _make_ranked_diff(self, angle_name, phase, view, delta, user_val, ref_val):
        return {
            "rank": 1,
            "angle_name": angle_name,
            "phase": phase,
            "view": view,
            "delta": delta,
            "user_value": user_val,
            "reference_value": ref_val,
        }

    def test_early_extension_match(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """spine_angle_dtl @ impact, delta=+11.3 → Early Extension rule."""
        diff = self._make_ranked_diff(
            "spine_angle_dtl", "impact", "dtl", 11.3, 30.0, 18.7
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert len(result) == 1
        assert result[0]["title"] == "Early Extension (Loss of Posture)"
        assert result[0]["severity"] == "major"

    def test_chicken_wing_match(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """left_elbow @ impact, delta=-17.5 → Chicken Wing rule."""
        diff = self._make_ranked_diff(
            "left_elbow", "impact", "dtl", -17.5, 158.0, 175.5
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert len(result) == 1
        assert "Chicken Wing" in result[0]["title"]
        assert result[0]["severity"] == "major"

    def test_first_matching_rule_wins(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """Only the first matching rule should be returned."""
        diff = self._make_ranked_diff(
            "spine_angle_dtl", "address", "dtl", 10.0, 28.0, 18.0
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert len(result) == 1
        # Should match "Too Upright at Setup" (max_delta=8.0), not any other rule
        assert result[0]["title"] == "Too Upright at Setup"

    def test_fallback_no_rule_moderate(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """Unmatched angle/phase/view combo → generic fallback, moderate if >12°."""
        diff = self._make_ranked_diff(
            "right_wrist_cock", "impact", "dtl", 15.0, 178.0, 163.0
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert len(result) == 1
        assert result[0]["severity"] == "moderate"
        # Fallback title format: "{Angle Name} at {Phase}"
        assert "Wrist Cock" in result[0]["title"]
        assert "Impact" in result[0]["title"]

    def test_fallback_minor_severity(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """Unmatched with |delta| <= 12 → severity minor."""
        diff = self._make_ranked_diff(
            "right_wrist_cock", "impact", "dtl", 8.0, 178.0, 170.0
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert result[0]["severity"] == "minor"

    def test_template_interpolation(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """Matched rule description should contain actual numeric values."""
        diff = self._make_ranked_diff(
            "spine_angle_dtl", "impact", "dtl", 11.3, 30.0, 18.7
        )
        result = generate_feedback(
            [diff], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        desc = result[0]["description"]
        assert "30.0" in desc
        assert "18.7" in desc

    def test_fallback_direction(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        """Positive delta → 'more'; negative delta → 'less' in fallback."""
        diff_pos = self._make_ranked_diff(
            "right_wrist_cock", "impact", "dtl", 15.0, 178.0, 163.0
        )
        diff_neg = self._make_ranked_diff(
            "right_wrist_cock", "impact", "dtl", -15.0, 148.0, 163.0
        )
        result_pos = generate_feedback(
            [diff_pos], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        result_neg = generate_feedback(
            [diff_neg], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert "more" in result_pos[0]["description"]
        assert "less" in result_neg[0]["description"]

    def test_empty_input(self, sample_user_angles_dtl, sample_ref_angles_dtl):
        result = generate_feedback(
            [], sample_user_angles_dtl, sample_ref_angles_dtl
        )
        assert result == []


# ===================================================================
# _format_angle_name
# ===================================================================


class TestFormatAngleName:
    def test_known_name(self):
        assert _format_angle_name("spine_angle_dtl") == "Spine Angle"
        assert _format_angle_name("left_elbow") == "Left Elbow Angle"
        assert _format_angle_name("x_factor") == "Shoulder-Hip Tilt Gap"

    def test_unknown_name(self):
        assert _format_angle_name("foo_bar") == "Foo Bar"
        assert _format_angle_name("my_custom_angle") == "My Custom Angle"
