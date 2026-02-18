import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.auth import require_user
from app.config import settings
from app.models.schemas import FileInfo, UploadResponse
from app.analytics import track_upload_completed
from app.storage.local import save_upload

logger = logging.getLogger(__name__)
router = APIRouter()


def _validate_file(file: UploadFile, label: str) -> None:
    if file.content_type not in settings.allowed_content_types:
        raise HTTPException(
            400,
            f"{label}: Invalid file type '{file.content_type}'. Accepted: .mp4, .mov",
        )
    if not file.filename:
        raise HTTPException(400, f"{label}: Filename is required.")


@router.post("/upload", response_model=UploadResponse)
async def upload_videos(
    swing_type: str = Form(...),
    view: str = Form(...),
    video: UploadFile = File(...),
    current_user=Depends(require_user),
):
    # Validate swing type
    if swing_type not in settings.allowed_swing_types:
        raise HTTPException(
            400,
            f"Invalid swing_type '{swing_type}'. Only 'iron' is supported in v1.",
        )

    # Validate view
    if view not in ("dtl", "fo"):
        raise HTTPException(
            400,
            f"Invalid view '{view}'. Must be 'dtl' or 'fo'.",
        )

    # Validate file
    _validate_file(video, f"video_{view}")

    # Generate upload ID and save
    upload_id = str(uuid.uuid4())
    logger.info(f"Upload {upload_id} by user {current_user.user_id} (view={view})")

    filename, size = await save_upload(upload_id, view, video)

    track_upload_completed(
        user_id=current_user.user_id,
        upload_id=upload_id,
        view=view,
        swing_type=swing_type,
        file_size_bytes=size,
        content_type=video.content_type or "video/mp4",
    )

    return UploadResponse(
        status="success",
        upload_id=upload_id,
        swing_type=swing_type,
        files={
            view: FileInfo(
                filename=filename,
                size_bytes=size,
                content_type=video.content_type or "video/mp4",
            ),
        },
        message=f"Video uploaded successfully. Call POST /api/analyze/{upload_id} to run analysis.",
    )
