"""Tests for app.pipeline.phase_detector — wrapper around detect_phases script."""

from unittest.mock import patch

import pytest

from app.pipeline.models import PhaseDetectionError
from app.pipeline.phase_detector import detect_swing_phases


class TestDetectSwingPhases:
    """Test the wrapper's error handling and frame snapping."""

    def _valid_phases(self):
        return {
            "address": {"frame": 10, "description": "Address"},
            "top": {"frame": 40, "description": "Top of backswing"},
            "impact": {"frame": 50, "description": "Impact"},
            "follow_through": {"frame": 75, "description": "Follow-through"},
        }

    @patch("app.pipeline.phase_detector._detect_phases")
    def test_returns_all_four_phases(self, mock_detect, sample_landmarks_data):
        mock_detect.return_value = self._valid_phases()
        result = detect_swing_phases(sample_landmarks_data, "dtl")
        assert set(result.keys()) == {"address", "top", "impact", "follow_through"}
        for phase in result.values():
            assert "frame" in phase
            assert "description" in phase

    @patch("app.pipeline.phase_detector._detect_phases")
    def test_snaps_to_detected_frames(self, mock_detect):
        """Phase frame 25 not in detected set → snaps to nearest (24 or 26)."""
        frames = []
        for i in range(100):
            frames.append({
                "frame": i,
                "timestamp_sec": i / 30.0,
                "detected": i in {0, 10, 20, 24, 26, 30, 50, 75},
            })
        landmarks = {
            "summary": {"fps": 30.0, "total_frames": 100},
            "frames": frames,
        }
        phases = self._valid_phases()
        phases["top"]["frame"] = 25  # not in detected set
        mock_detect.return_value = phases

        result = detect_swing_phases(landmarks, "dtl")
        # Should snap to 24 or 26 (both are distance 1)
        assert result["top"]["frame"] in {24, 26}

    @patch("app.pipeline.phase_detector._detect_phases")
    def test_system_exit_raises_phase_error(self, mock_detect, sample_landmarks_data):
        mock_detect.side_effect = SystemExit(1)
        with pytest.raises(PhaseDetectionError):
            detect_swing_phases(sample_landmarks_data, "dtl")

    @patch("app.pipeline.phase_detector._detect_phases")
    def test_exception_raises_phase_error(self, mock_detect, sample_landmarks_data):
        mock_detect.side_effect = ValueError("bad data")
        with pytest.raises(PhaseDetectionError):
            detect_swing_phases(sample_landmarks_data, "dtl")

    @patch("app.pipeline.phase_detector._detect_phases")
    def test_missing_phase_raises(self, mock_detect, sample_landmarks_data):
        """Only 3 of 4 phases returned → PhaseDetectionError."""
        phases = self._valid_phases()
        del phases["follow_through"]
        mock_detect.return_value = phases
        with pytest.raises(PhaseDetectionError):
            detect_swing_phases(sample_landmarks_data, "dtl")
