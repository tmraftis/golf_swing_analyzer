"""PropelAuth initialization for FastAPI.

Provides `require_user` as a FastAPI dependency for protecting endpoints.

Usage in routes:
    from app.auth import require_user
    from fastapi import Depends

    @router.get("/protected")
    async def protected(current_user=Depends(require_user)):
        return {"user_id": current_user.user_id}
"""

import logging

from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

_auth = None

if settings.propelauth_auth_url and settings.propelauth_api_key:
    from propelauth_fastapi import init_auth

    _auth = init_auth(settings.propelauth_auth_url, settings.propelauth_api_key)
    logger.info(f"PropelAuth initialized with auth URL: {settings.propelauth_auth_url}")
else:
    logger.warning(
        "PropelAuth not configured — PROPELAUTH_AUTH_URL and PROPELAUTH_API_KEY "
        "must be set. All endpoints requiring auth will return 401."
    )


def _no_auth_configured():
    """Fallback dependency when PropelAuth is not configured."""
    raise HTTPException(
        status_code=401,
        detail="Authentication is not configured on this server.",
    )


# Export a single dependency that routes can use with Depends(require_user)
require_user = _auth.require_user if _auth else _no_auth_configured
