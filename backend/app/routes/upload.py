import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.config import settings
from app.models.schemas import FileInfo, UploadResponse
from app.storage.local import save_upload

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
    video_dtl: UploadFile = File(...),
    video_fo: UploadFile = File(...),
):
    # Validate swing type
    if swing_type not in settings.allowed_swing_types:
        raise HTTPException(
            400,
            f"Invalid swing_type '{swing_type}'. Only 'iron' is supported in v1.",
        )

    # Validate files
    _validate_file(video_dtl, "video_dtl")
    _validate_file(video_fo, "video_fo")

    # Generate upload ID and save
    upload_id = str(uuid.uuid4())
    dtl_filename, dtl_size = await save_upload(upload_id, "dtl", video_dtl)
    fo_filename, fo_size = await save_upload(upload_id, "fo", video_fo)

    return UploadResponse(
        status="success",
        upload_id=upload_id,
        swing_type=swing_type,
        files={
            "dtl": FileInfo(
                filename=dtl_filename,
                size_bytes=dtl_size,
                content_type=video_dtl.content_type or "video/mp4",
            ),
            "fo": FileInfo(
                filename=fo_filename,
                size_bytes=fo_size,
                content_type=video_fo.content_type or "video/mp4",
            ),
        },
        message="Videos uploaded successfully. Call POST /api/analyze/{upload_id} to run analysis.",
    )
