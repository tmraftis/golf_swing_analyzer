from pathlib import Path

from fastapi import UploadFile

from app.config import settings


async def save_upload(
    upload_id: str, angle: str, file: UploadFile
) -> tuple[str, int]:
    """Save an uploaded file to local storage. Returns (filename, size_bytes)."""
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".mp4"
    filename = f"{upload_id}_{angle}{ext}"
    filepath = settings.upload_dir / filename

    size = 0
    with open(filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            size += len(chunk)

    return filename, size
