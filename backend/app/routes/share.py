"""Share endpoints: create/retrieve public share tokens and generate share images."""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from app.auth import require_user
from app.config import settings
from app.models.schemas import ShareRequest, ShareResponse
from app.storage.analysis_store import get_result
from app.storage.share_store import (
    create_share,
    get_share,
    get_shares_for_upload,
    revoke_share,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/share", response_model=ShareResponse)
async def create_share_token(
    request: ShareRequest,
    current_user=Depends(require_user),
):
    """Create a share token for a completed analysis.

    Returns an existing active token if one already exists for this
    upload+view combination, to avoid duplicate shares.
    """
    # Verify the analysis exists
    cache_key = f"{request.upload_id}_{request.view}"
    result = get_result(cache_key)
    if result is None:
        raise HTTPException(
            404,
            f"No analysis found for upload '{request.upload_id}' (view={request.view}). "
            "Run the analysis first.",
        )

    # Check for existing active share
    existing = get_shares_for_upload(request.upload_id)
    for share in existing:
        if share["view"] == request.view:
            token = share["share_token"]
            logger.info(f"Returning existing share token {token[:8]}...")
            return ShareResponse(
                share_token=token,
                share_url=f"{settings.public_base_url}/shared/{token}",
                expires_at=share.get("expires_at"),
            )

    # Create new share token
    user_id = getattr(current_user, "user_id", None)
    token = create_share(
        upload_id=request.upload_id,
        view=request.view,
        user_id=user_id,
        expires_days=90,  # Free tier default
    )

    return ShareResponse(
        share_token=token,
        share_url=f"{settings.public_base_url}/shared/{token}",
        expires_at=None,  # Will be populated from DB on next fetch
    )


@router.get("/share/{share_token}")
async def get_shared_analysis(share_token: str):
    """Retrieve analysis data for a public share token.

    No authentication required — this is the public endpoint.
    """
    share = get_share(share_token)
    if share is None:
        raise HTTPException(
            404,
            "This swing analysis has expired or been made private.",
        )

    # Look up the cached analysis
    cache_key = f"{share['upload_id']}_{share['view']}"
    result = get_result(cache_key)
    if result is None:
        raise HTTPException(
            404,
            "Analysis data is no longer available. The analysis may need to be re-run.",
        )

    # Return a subset of the analysis data (no video URLs for public page)
    return {
        "status": result.get("status", "success"),
        "upload_id": share["upload_id"],
        "swing_type": result.get("swing_type", "iron"),
        "similarity_score": result.get("similarity_score", 0),
        "view": share["view"],
        "user_angles": result.get("user_angles", {}),
        "reference_angles": result.get("reference_angles", {}),
        "deltas": result.get("deltas", {}),
        "top_differences": result.get("top_differences", []),
        "user_phase_images": result.get("user_phase_images"),
        "reference_phase_images": result.get("reference_phase_images"),
    }


@router.get("/share/{share_token}/image")
async def get_share_image(share_token: str):
    """Generate and serve a branded share image (PNG).

    No authentication required.  Caches generated images to disk to avoid
    repeated Pillow work on the same token.
    """
    share = get_share(share_token)
    if share is None:
        raise HTTPException(404, "Share token not found or expired.")

    # Check disk cache first
    cache_dir = Path(settings.share_image_cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{share_token}.png"

    if cache_path.exists():
        return Response(
            content=cache_path.read_bytes(),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    # Load analysis data
    cache_key = f"{share['upload_id']}_{share['view']}"
    result = get_result(cache_key)
    if result is None:
        raise HTTPException(404, "Analysis data not available.")

    # Resolve phase image paths on disk
    upload_dir = str(settings.upload_dir)
    view = share["view"]
    upload_id = share["upload_id"]

    user_img_path = _resolve_phase_image(result, "user_phase_images", view, upload_dir)
    ref_img_path = _resolve_phase_image(result, "reference_phase_images", view, upload_dir)

    view_label = "Down the Line" if view == "dtl" else "Face On"

    # Generate image
    from app.pipeline.image_generator import generate

    try:
        img_bytes = generate(
            similarity_score=result.get("similarity_score", 0),
            top_differences=result.get("top_differences", []),
            user_phase_image_path=user_img_path,
            ref_phase_image_path=ref_img_path,
            view_label=view_label,
        )
    except Exception as e:
        logger.exception(f"Image generation failed for share {share_token}")
        raise HTTPException(500, f"Image generation failed: {e}")

    # Cache to disk
    try:
        cache_path.write_bytes(img_bytes)
    except Exception as e:
        logger.warning(f"Failed to cache share image: {e}")

    return Response(
        content=img_bytes,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.delete("/share/{share_token}")
async def revoke_share_token(
    share_token: str,
    current_user=Depends(require_user),
):
    """Revoke a share token. Requires authentication."""
    share = get_share(share_token)
    if share is None:
        raise HTTPException(404, "Share token not found.")

    # Verify ownership
    user_id = getattr(current_user, "user_id", None)
    if share.get("user_id") and share["user_id"] != user_id:
        raise HTTPException(403, "You can only revoke your own shares.")

    revoke_share(share_token)

    # Remove cached image
    cache_path = Path(settings.share_image_cache_dir) / f"{share_token}.png"
    if cache_path.exists():
        cache_path.unlink()

    return {"status": "revoked", "share_token": share_token}


def _resolve_phase_image(
    result: dict,
    key: str,
    view: str,
    upload_dir: str,
) -> str | None:
    """Resolve a phase image URL path to an absolute filesystem path.

    The analysis stores image URLs like "/uploads/abc_dtl_impact.jpg".
    We need the absolute path for Pillow to open.
    Prefers the impact phase; falls back to other phases.
    """
    images = result.get(key)
    if not images:
        return None

    view_images = images.get(view, {})

    # Prefer impact phase
    for phase in ["impact", "top", "address", "follow_through"]:
        url = view_images.get(phase)
        if url:
            # URL is like "/uploads/filename.jpg" — strip prefix to get filename
            filename = url.split("/")[-1]
            abs_path = os.path.join(upload_dir, filename)
            if os.path.exists(abs_path):
                return abs_path

    return None
