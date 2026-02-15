"""Tests for app.pipeline.angle_calculator — wrapper around calculate_angles script."""

from unittest.mock import patch

import pytest

from app.pipeline.angle_calculator import calculate_angles
from app.pipeline.models import AngleCalculationError


class TestCalculateAngles:
    """Test the wrapper's pass-through and error handling."""

    def _valid_result(self):
        return {
            "address": {
                "frame": 10,
                "timestamp_sec": 0.33,
                "description": "Address",
                "angles": {"spine_angle_dtl": 28.0, "right_elbow": 170.0},
            },
            "top": {
                "frame": 40,
                "timestamp_sec": 1.33,
                "description": "Top",
                "angles": {"spine_angle_dtl": 25.0, "lead_arm_torso": 105.0},
            },
        }

    @patch("app.pipeline.angle_calculator._analyze_video")
    def test_returns_result(self, mock_analyze, sample_landmarks_data, sample_phases):
        mock_analyze.return_value = self._valid_result()
        result = calculate_angles(sample_landmarks_data, sample_phases, "dtl")
        assert "address" in result
        assert result["address"]["angles"]["spine_angle_dtl"] == 28.0

    @patch("app.pipeline.angle_calculator._analyze_video")
    def test_empty_result_raises(self, mock_analyze, sample_landmarks_data, sample_phases):
        mock_analyze.return_value = {}
        with pytest.raises(AngleCalculationError):
            calculate_angles(sample_landmarks_data, sample_phases, "dtl")

    @patch("app.pipeline.angle_calculator._analyze_video")
    def test_exception_raises(self, mock_analyze, sample_landmarks_data, sample_phases):
        mock_analyze.side_effect = RuntimeError("computation failed")
        with pytest.raises(AngleCalculationError):
            calculate_angles(sample_landmarks_data, sample_phases, "dtl")
