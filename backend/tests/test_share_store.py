"""Tests for app.storage.share_store — SQLite share token management."""

import pytest

from app.storage import share_store


@pytest.fixture(autouse=True)
def tmp_share_db(tmp_path, monkeypatch):
    """Point share_store at a temporary SQLite database for each test."""
    db_path = tmp_path / "test_shares.db"
    # Reset the cached _DB_PATH so _get_db_path() re-reads from settings
    monkeypatch.setattr(share_store, "_DB_PATH", None)
    monkeypatch.setattr("app.config.settings.share_db_path", str(db_path))
    share_store.init_db()
    return db_path


class TestShareStore:
    def test_create_returns_token(self):
        token = share_store.create_share("upload1", "dtl")
        assert isinstance(token, str)
        assert len(token) == 32  # uuid4().hex is 32 chars

    def test_get_valid_token(self):
        token = share_store.create_share("upload1", "dtl")
        share = share_store.get_share(token)
        assert share is not None
        assert share["upload_id"] == "upload1"
        assert share["view"] == "dtl"
        assert share["is_public"] == 1

    def test_get_nonexistent(self):
        assert share_store.get_share("fake-token-00000000") is None

    def test_revoke_then_get(self):
        token = share_store.create_share("upload1", "dtl")
        assert share_store.revoke_share(token) is True
        assert share_store.get_share(token) is None

    def test_revoke_unknown(self):
        assert share_store.revoke_share("nonexistent") is False

    def test_get_shares_for_upload(self):
        t1 = share_store.create_share("upload1", "dtl")
        t2 = share_store.create_share("upload1", "fo")
        share_store.revoke_share(t1)
        active = share_store.get_shares_for_upload("upload1")
        assert len(active) == 1
        assert active[0]["share_token"] == t2

    def test_create_with_user_id(self):
        token = share_store.create_share("upload1", "dtl", user_id="user-abc")
        share = share_store.get_share(token)
        assert share["user_id"] == "user-abc"
