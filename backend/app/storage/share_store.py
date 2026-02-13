"""SQLite-backed store for share tokens.

Each share token maps an upload's analysis to a public URL that can be
accessed without authentication.
"""

import logging
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

_DB_PATH: Path | None = None


def _get_db_path() -> Path:
    global _DB_PATH
    if _DB_PATH is None:
        _DB_PATH = Path(settings.share_db_path)
    return _DB_PATH


def _connect() -> sqlite3.Connection:
    """Open a connection with row-factory for dict-like access."""
    conn = sqlite3.connect(str(_get_db_path()))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the shares table if it doesn't exist.

    Called once at application startup.
    """
    db_path = _get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS shares (
                share_token  TEXT PRIMARY KEY,
                upload_id    TEXT NOT NULL,
                view         TEXT NOT NULL,
                created_at   TEXT NOT NULL,
                expires_at   TEXT,
                is_public    INTEGER DEFAULT 1,
                user_id      TEXT
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_shares_upload ON shares(upload_id)"
        )
        conn.commit()
        logger.info(f"Share store initialised at {db_path}")
    finally:
        conn.close()


def create_share(
    upload_id: str,
    view: str,
    user_id: str | None = None,
    expires_days: int | None = 90,
) -> str:
    """Create a new share token and return it.

    Args:
        upload_id: The analysis upload ID.
        view: The video angle ("dtl" or "fo").
        user_id: Optional PropelAuth user ID.
        expires_days: Days until expiry. None = permanent.

    Returns:
        The UUID share token string.
    """
    token = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires_at = (
        (now + timedelta(days=expires_days)).isoformat() if expires_days else None
    )

    conn = _connect()
    try:
        conn.execute(
            """
            INSERT INTO shares (share_token, upload_id, view, created_at, expires_at, is_public, user_id)
            VALUES (?, ?, ?, ?, ?, 1, ?)
            """,
            (token, upload_id, view, now.isoformat(), expires_at, user_id),
        )
        conn.commit()
        logger.info(f"Created share token {token[:8]}... for {upload_id}/{view}")
    finally:
        conn.close()

    return token


def get_share(share_token: str) -> dict | None:
    """Look up a share token.

    Returns the share row as a dict if:
    - The token exists
    - It has not been revoked (is_public == 1)
    - It has not expired

    Otherwise returns None.
    """
    conn = _connect()
    try:
        row = conn.execute(
            "SELECT * FROM shares WHERE share_token = ?", (share_token,)
        ).fetchone()

        if row is None:
            return None

        share = dict(row)

        # Check revocation
        if not share["is_public"]:
            return None

        # Check expiry
        if share["expires_at"]:
            expires = datetime.fromisoformat(share["expires_at"])
            if datetime.now(timezone.utc) > expires:
                return None

        return share
    finally:
        conn.close()


def revoke_share(share_token: str) -> bool:
    """Revoke a share token. Returns True if a row was updated."""
    conn = _connect()
    try:
        cursor = conn.execute(
            "UPDATE shares SET is_public = 0 WHERE share_token = ?",
            (share_token,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_shares_for_upload(upload_id: str) -> list[dict]:
    """List all active share tokens for a given upload."""
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM shares WHERE upload_id = ? AND is_public = 1 ORDER BY created_at DESC",
            (upload_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
