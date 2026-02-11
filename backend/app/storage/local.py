import logging
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.video.compress import compress_video, is_ffmpeg_available

logger = logging.getLogger(__name__)


async def save_upload(
    upload_id: str, angle: str, file: UploadFile
) -> tuple[str, int]:
    """Save an uploaded file to local storage, compressing if possible.

    Returns (filename, size_bytes) of the final stored file.
    """
    settings.upload_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".mp4"
    raw_filename = f"{upload_id}_{angle}{ext}"
    raw_filepath = settings.upload_dir / raw_filename

    # Step 1: Write raw upload to disk
    raw_size = 0
    with open(raw_filepath, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            raw_size += len(chunk)

    # Step 2: Compress to H.264 .mp4 (if enabled)
    if not settings.compress_uploads:
        return raw_filename, raw_size

    if not is_ffmpeg_available():
        logger.warning("Compression enabled but ffmpeg not found — keeping raw file")
        return raw_filename, raw_size

    final_filename = f"{upload_id}_{angle}.mp4"
    final_filepath = settings.upload_dir / final_filename

    # Handle edge case: input is already .mp4 (same path as output)
    if raw_filepath == final_filepath:
        temp_path = settings.upload_dir / f"{upload_id}_{angle}_compressing.mp4"
        if compress_video(raw_filepath, temp_path):
            raw_filepath.unlink()           # delete original
            temp_path.rename(final_filepath) # move compressed into place
            final_size = final_filepath.stat().st_size
            logger.info(
                "Compressed %s: %s -> %s (%.0f%% reduction)",
                raw_filename,
                _fmt_size(raw_size),
                _fmt_size(final_size),
                (1 - final_size / raw_size) * 100,
            )
            return final_filename, final_size
        else:
            temp_path.unlink(missing_ok=True)
            logger.warning("Compression failed for %s — keeping raw file", raw_filename)
            return raw_filename, raw_size
    else:
        # Input is .MOV or other extension — compress to .mp4
        if compress_video(raw_filepath, final_filepath):
            raw_filepath.unlink()  # delete original .MOV
            final_size = final_filepath.stat().st_size
            logger.info(
                "Compressed %s: %s -> %s (%.0f%% reduction)",
                raw_filename,
                _fmt_size(raw_size),
                _fmt_size(final_size),
                (1 - final_size / raw_size) * 100,
            )
            return final_filename, final_size
        else:
            final_filepath.unlink(missing_ok=True)
            logger.warning("Compression failed for %s — keeping raw file", raw_filename)
            return raw_filename, raw_size


def _fmt_size(size_bytes: int) -> str:
    """Format bytes as a human-readable string."""
    if size_bytes >= 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f}MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f}KB"
    return f"{size_bytes}B"
