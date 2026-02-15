"""Tests for app.pipeline.comparison_engine — delta computation, ranking, similarity."""

import pytest

from app.pipeline.comparison_engine import (
    compute_deltas,
    compute_similarity_score,
    rank_differences,
)


# ===================================================================
# compute_deltas
# ===================================================================


class TestComputeDeltas:
    """Test angle delta computation including atan2 wraparound."""

    def test_basic_subtraction(
        self, sample_user_angles_dtl, sample_ref_angles_dtl
    ):
        deltas = compute_deltas(sample_user_angles_dtl, sample_ref_angles_dtl)
        # spine_angle_dtl @ address: 28.0 - 18.9 = 9.1
        assert deltas["dtl"]["address"]["spine_angle_dtl"] == 9.1

    def test_wraparound_positive(
        self, sample_user_angles_fo, sample_ref_angles_fo
    ):
        """User=177, Ref=-169 → naive=346, correct=-14 (shortest path)."""
        deltas = compute_deltas(sample_user_angles_fo, sample_ref_angles_fo)
        # shoulder_line_angle @ address: 177 - (-169)
        # Naive: 346. Wraparound: (346+180)%360-180 = -14
        delta = deltas["fo"]["address"]["shoulder_line_angle"]
        assert delta == pytest.approx(-14.0, abs=0.1)

    def test_wraparound_negative(self):
        """User=-169, Ref=177 → naive=-346, correct=14."""
        user = {"fo": {"address": {"angles": {"shoulder_line_angle": -169.0}}}}
        ref = {"fo": {"address": {"angles": {"shoulder_line_angle": 177.0}}}}
        deltas = compute_deltas(user, ref)
        assert deltas["fo"]["address"]["shoulder_line_angle"] == pytest.approx(
            14.0, abs=0.1
        )

    def test_wraparound_small_difference(self):
        """Small differences are unaffected by wraparound logic."""
        user = {"fo": {"address": {"angles": {"hip_line_angle": 10.0}}}}
        ref = {"fo": {"address": {"angles": {"hip_line_angle": 5.0}}}}
        deltas = compute_deltas(user, ref)
        assert deltas["fo"]["address"]["hip_line_angle"] == 5.0

    def test_wraparound_at_180_boundary(self):
        """180° difference: (180+180)%360-180 = 180 or -180."""
        user = {"fo": {"address": {"angles": {"shoulder_line_angle": 180.0}}}}
        ref = {"fo": {"address": {"angles": {"shoulder_line_angle": 0.0}}}}
        deltas = compute_deltas(user, ref)
        assert abs(deltas["fo"]["address"]["shoulder_line_angle"]) == pytest.approx(
            180.0, abs=0.1
        )

    def test_missing_view_skipped(
        self, sample_user_angles_dtl, sample_ref_angles_fo
    ):
        """User has dtl only, ref has fo only → empty deltas."""
        deltas = compute_deltas(sample_user_angles_dtl, sample_ref_angles_fo)
        assert "dtl" not in deltas
        assert "fo" not in deltas

    def test_missing_phase_skipped(self, sample_ref_angles_dtl):
        """User missing follow_through → not in output."""
        user = {
            "dtl": {
                "address": {
                    "angles": {"spine_angle_dtl": 28.0},
                },
            },
        }
        deltas = compute_deltas(user, sample_ref_angles_dtl)
        assert "address" in deltas["dtl"]
        assert "follow_through" not in deltas["dtl"]

    def test_missing_angle_skipped(self):
        """Angle in user but not in ref → not in output."""
        user = {"dtl": {"address": {"angles": {"spine_angle_dtl": 28.0, "custom_angle": 50.0}}}}
        ref = {"dtl": {"address": {"angles": {"spine_angle_dtl": 18.9}}}}
        deltas = compute_deltas(user, ref)
        assert "custom_angle" not in deltas["dtl"]["address"]
        assert "spine_angle_dtl" in deltas["dtl"]["address"]

    def test_non_numeric_skipped(self):
        """String angle values are silently skipped."""
        user = {"dtl": {"address": {"angles": {"spine_angle_dtl": "N/A"}}}}
        ref = {"dtl": {"address": {"angles": {"spine_angle_dtl": 18.9}}}}
        deltas = compute_deltas(user, ref)
        assert "spine_angle_dtl" not in deltas["dtl"]["address"]


# ===================================================================
# rank_differences
# ===================================================================


class TestRankDifferences:
    """Test weighted ranking, floor filtering, and view balance."""

    def _make_deltas_and_angles(self, entries):
        """Helper: build deltas, user_angles, ref_angles from a list of
        (view, phase, angle_name, user_val, ref_val) tuples.
        """
        deltas = {}
        user_angles = {}
        ref_angles = {}
        for view, phase, angle_name, user_val, ref_val in entries:
            deltas.setdefault(view, {}).setdefault(phase, {})[angle_name] = round(
                user_val - ref_val, 1
            )
            user_angles.setdefault(view, {}).setdefault(phase, {"angles": {}})[
                "angles"
            ][angle_name] = user_val
            ref_angles.setdefault(view, {}).setdefault(phase, {"angles": {}})[
                "angles"
            ][angle_name] = ref_val
        return deltas, user_angles, ref_angles

    def test_top_3_by_weighted_abs(self):
        """5 eligible angles → returns exactly 3, sorted by weighted |delta|."""
        d, u, r = self._make_deltas_and_angles([
            ("dtl", "address", "spine_angle_dtl", 30.0, 18.9),  # delta=11.1
            ("dtl", "top", "right_elbow", 80.0, 65.1),          # delta=14.9
            ("dtl", "impact", "left_elbow", 158.0, 175.5),      # delta=-17.5
            ("dtl", "top", "right_knee_flex", 178.0, 171.1),    # delta=6.9
            ("dtl", "impact", "right_knee_flex", 150.0, 154.3), # delta=-4.3 (below floor)
        ])
        result = rank_differences(d, u, r)
        assert len(result) == 3
        assert result[0]["rank"] == 1
        assert result[1]["rank"] == 2
        assert result[2]["rank"] == 3
        # Weighted abs should be descending
        # left_elbow@impact: 17.5*1.3=22.75, right_elbow@top: 14.9*1.2=17.88,
        # spine@address: 11.1*1.0=11.1
        assert result[0]["angle_name"] == "left_elbow"
        assert result[1]["angle_name"] == "right_elbow"

    def test_floor_filters_small_deltas(self):
        """All deltas below 5° → empty list."""
        d, u, r = self._make_deltas_and_angles([
            ("dtl", "address", "spine_angle_dtl", 20.0, 18.9),  # delta=1.1
            ("dtl", "top", "right_elbow", 67.0, 65.1),          # delta=1.9
            ("dtl", "impact", "left_elbow", 172.0, 175.5),      # delta=-3.5
        ])
        result = rank_differences(d, u, r)
        assert result == []

    def test_excludes_shoulder_hip_xfactor(self):
        """Excluded angles don't appear in output even with large deltas."""
        d, u, r = self._make_deltas_and_angles([
            ("fo", "address", "shoulder_line_angle", 177.0, 145.0),  # delta=32
            ("fo", "address", "hip_line_angle", 170.0, 140.0),      # delta=30
            ("fo", "top", "x_factor", 50.0, 23.0),                  # delta=27
            ("fo", "impact", "spine_tilt_fo", 25.0, 18.0),          # delta=7 (eligible)
        ])
        result = rank_differences(d, u, r)
        angle_names = {r["angle_name"] for r in result}
        assert "shoulder_line_angle" not in angle_names
        assert "hip_line_angle" not in angle_names
        assert "x_factor" not in angle_names
        assert "spine_tilt_fo" in angle_names

    def test_weight_boost(self):
        """spine_angle_dtl@impact (weight 1.5) beats larger raw delta (weight 1.0).
        spine: delta=11.3, weighted=11.3*1.5=16.95
        knee@impact: delta=-14.3, weighted=14.3*1.0=14.3 (no weight for knee@impact)
        """
        d, u, r = self._make_deltas_and_angles([
            ("dtl", "impact", "spine_angle_dtl", 30.0, 18.7),    # weighted=16.95
            ("dtl", "impact", "right_knee_flex", 140.0, 154.3),   # weighted=14.3
        ])
        result = rank_differences(d, u, r)
        assert len(result) == 2
        # spine_angle_dtl should rank first despite smaller raw delta
        assert result[0]["angle_name"] == "spine_angle_dtl"
        assert result[1]["angle_name"] == "right_knee_flex"

    def test_view_balance_multi_view(self):
        """Multi-view: max 2 from dtl, at least 1 from fo."""
        d, u, r = self._make_deltas_and_angles([
            ("dtl", "impact", "spine_angle_dtl", 30.0, 18.7),    # delta=11.3
            ("dtl", "top", "lead_arm_torso", 105.0, 121.7),      # delta=-16.7
            ("dtl", "top", "right_elbow", 80.0, 65.1),           # delta=14.9
            ("fo", "impact", "spine_tilt_fo", 25.0, 18.0),       # delta=7.0
        ])
        result = rank_differences(d, u, r)
        dtl_count = sum(1 for r in result if r["view"] == "dtl")
        fo_count = sum(1 for r in result if r["view"] == "fo")
        assert dtl_count <= 2
        assert fo_count >= 1
        assert len(result) == 3

    def test_single_view_allows_3(self):
        """Single view: all 3 can come from dtl."""
        d, u, r = self._make_deltas_and_angles([
            ("dtl", "impact", "spine_angle_dtl", 30.0, 18.7),
            ("dtl", "top", "lead_arm_torso", 105.0, 121.7),
            ("dtl", "top", "right_elbow", 80.0, 65.1),
            ("dtl", "impact", "left_elbow", 158.0, 175.5),
        ])
        result = rank_differences(d, u, r)
        assert len(result) == 3
        assert all(r["view"] == "dtl" for r in result)


# ===================================================================
# compute_similarity_score
# ===================================================================


class TestComputeSimilarityScore:
    """Test similarity scoring."""

    def test_perfect_match(self):
        deltas = {"dtl": {"address": {"spine_angle_dtl": 0.0, "right_elbow": 0.0}}}
        assert compute_similarity_score(deltas) == 100

    def test_all_bad(self):
        deltas = {"dtl": {"address": {"spine_angle_dtl": 45.0, "right_elbow": 50.0}}}
        assert compute_similarity_score(deltas) == 0

    def test_mixed(self):
        """[0, 22.5, 45] → per-angle [1.0, 0.5, 0.0] → mean 0.5 → 50."""
        deltas = {"dtl": {"address": {
            "a": 0.0,
            "b": 22.5,
            "c": 45.0,
        }}}
        assert compute_similarity_score(deltas) == 50

    def test_empty_deltas(self):
        assert compute_similarity_score({}) == 0
        assert compute_similarity_score({"dtl": {}}) == 0
        assert compute_similarity_score({"dtl": {"address": {}}}) == 0
