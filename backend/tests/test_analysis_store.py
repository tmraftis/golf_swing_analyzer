"""Tests for app.storage.analysis_store — in-memory result cache."""

import pytest

from app.storage import analysis_store


@pytest.fixture(autouse=True)
def isolate_store(monkeypatch):
    """Replace the module-level _results dict with a fresh one for each test."""
    monkeypatch.setattr(analysis_store, "_results", {})


class TestAnalysisStore:
    def test_save_and_get(self):
        analysis_store.save_result("abc_dtl", {"score": 85})
        result = analysis_store.get_result("abc_dtl")
        assert result == {"score": 85}

    def test_get_not_found(self):
        assert analysis_store.get_result("nonexistent") is None

    def test_has_result(self):
        assert analysis_store.has_result("abc_dtl") is False
        analysis_store.save_result("abc_dtl", {"score": 85})
        assert analysis_store.has_result("abc_dtl") is True

    def test_overwrite(self):
        analysis_store.save_result("abc_dtl", {"score": 85})
        analysis_store.save_result("abc_dtl", {"score": 90})
        assert analysis_store.get_result("abc_dtl") == {"score": 90}

    def test_key_isolation(self):
        analysis_store.save_result("a", {"val": 1})
        analysis_store.save_result("b", {"val": 2})
        assert analysis_store.get_result("a") == {"val": 1}
        assert analysis_store.get_result("b") == {"val": 2}
