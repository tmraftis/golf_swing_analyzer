"""Video serving endpoints with HTTP range request support.

Browsers need range requests to seek in video files. FastAPI's StaticFiles
does not support range requests, so we serve videos through a custom endpoint.
"""

import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings

router = APIRouter()

# Project root for reference data
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
_REFERENCE_DIR = _PROJECT_ROOT / "reference_data"


def _stream_file(path: Path, start: int, end: int, chunk_size: int = 64 * 1024):
    """Generator that yields file chunks for a byte range."""
    with open(path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


def _serve_video(file_path: Path, request: Request):
    """Serve a video file with range request support."""
    if not file_path.exists():
        raise HTTPException(404, "Video not found")

    file_size = file_path.stat().st_size
    content_type = mimetypes.guess_type(str(file_path))[0] or "video/mp4"

    range_header = request.headers.get("range")

    if range_header:
        # Parse "bytes=START-END"
        range_spec = range_header.replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1
        end = min(end, file_size - 1)
        content_length = end - start + 1

        return StreamingResponse(
            _stream_file(file_path, start, end),
            status_code=206,
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "Content-Type": content_type,
            },
        )

    # No range header — return full file with Accept-Ranges
    return StreamingResponse(
        _stream_file(file_path, 0, file_size - 1),
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": content_type,
        },
    )


@router.get("/uploads/{filename:path}")
async def serve_upload(filename: str, request: Request):
    """Serve uploaded video files with range request support."""
    file_path = Path(settings.upload_dir) / filename
    return _serve_video(file_path, request)


@router.get("/reference/{filepath:path}")
async def serve_reference(filepath: str, request: Request):
    """Serve reference video files with range request support."""
    file_path = _REFERENCE_DIR / filepath
    return _serve_video(file_path, request)
