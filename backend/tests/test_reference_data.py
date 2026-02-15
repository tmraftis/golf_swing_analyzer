"""Tests for app.pipeline.reference_data — loading and angle remapping."""

import pytest

from app.pipeline.models import PipelineError
from app.pipeline.reference_data import load_reference


@pytest.fixture(autouse=True)
def clear_lru_cache():
    """Clear the LRU cache before each test."""
    load_reference.cache_clear()
    yield
    load_reference.cache_clear()


class TestLoadReference:
    """Test reference data loading from JSON files on disk."""

    def test_dtl_has_all_phases(self):
        ref = load_reference("iron", "dtl")
        assert set(ref.keys()) == {"address", "top", "impact", "follow_through"}
        for phase_data in ref.values():
            assert "angles" in phase_data
            assert "frame" in phase_data

    def test_dtl_remaps_spine_angle(self):
        """Raw JSON has 'spine_angle' → should become 'spine_angle_dtl'."""
        ref = load_reference("iron", "dtl")
        address_angles = ref["address"]["angles"]
        assert "spine_angle_dtl" in address_angles
        assert "spine_angle" not in address_angles

    def test_fo_remaps_spine_tilt(self):
        """Raw JSON has 'spine_tilt' → should become 'spine_tilt_fo'."""
        ref = load_reference("iron", "fo")
        # Check at least one phase has the remapped key
        has_remapped = any(
            "spine_tilt_fo" in phase["angles"]
            for phase in ref.values()
        )
        assert has_remapped

    def test_fo_has_wraparound_angles(self):
        """FO reference should contain shoulder_line_angle and hip_line_angle."""
        ref = load_reference("iron", "fo")
        all_angle_names = set()
        for phase_data in ref.values():
            all_angle_names.update(phase_data["angles"].keys())
        assert "shoulder_line_angle" in all_angle_names
        assert "hip_line_angle" in all_angle_names

    def test_invalid_view_raises(self):
        with pytest.raises(PipelineError):
            load_reference("iron", "invalid")

    def test_missing_file_raises(self):
        with pytest.raises(PipelineError) as exc_info:
            load_reference("driver", "dtl")
        assert exc_info.value.error_code == "REFERENCE_DATA_NOT_FOUND"

    def test_caching(self):
        """Two calls return the same object (LRU cache hit)."""
        ref1 = load_reference("iron", "dtl")
        ref2 = load_reference("iron", "dtl")
        assert ref1 is ref2
