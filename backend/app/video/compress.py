"""Video compression utility using ffmpeg.

Compresses uploaded videos to H.264 1080p ~4Mbps for reduced storage
and faster streaming. Falls back gracefully if ffmpeg is not installed.
"""

import logging
import shutil
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def is_ffmpeg_available() -> bool:
    """Check if ffmpeg is installed and accessible on PATH."""
    return shutil.which("ffmpeg") is not None


def compress_video(input_path: Path, output_path: Path) -> bool:
    """Compress a video to H.264 1080p ~4Mbps.

    Args:
        input_path: Path to the raw uploaded video file.
        output_path: Path for the compressed .mp4 output.

    Returns:
        True if compression succeeded, False otherwise.
    """
    if not is_ffmpeg_available():
        logger.warning("ffmpeg not found on PATH — skipping compression")
        return False

    cmd = [
        "ffmpeg",
        "-y",                       # overwrite output if exists
        "-i", str(input_path),      # input file
        "-vsync", "vfr",            # normalize VFR timing metadata (no frame dup/drop)
        "-c:v", "libx264",          # H.264 video codec
        "-preset", "fast",          # speed/quality tradeoff
        "-b:v", "4M",               # target video bitrate
        "-maxrate", "6M",           # cap peak bitrate
        "-bufsize", "8M",           # VBV buffer size
        "-vf", "scale='if(gte(iw,ih),min(1920,iw),-2)':'if(gte(iw,ih),-2,min(1920,ih))'",  # cap longest side at 1920, preserve orientation
        "-c:a", "aac",              # AAC audio codec
        "-b:a", "128k",             # audio bitrate
        "-movflags", "+faststart",  # moov atom at start for HTTP streaming
        str(output_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute safety timeout
        )
        if result.returncode != 0:
            logger.error(
                "ffmpeg failed (rc=%d): %s",
                result.returncode,
                result.stderr[-500:] if result.stderr else "(no stderr)",
            )
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg timed out after 120 seconds")
        # Clean up partial output
        output_path.unlink(missing_ok=True)
        return False
    except Exception as e:
        logger.error("ffmpeg execution error: %s", e)
        output_path.unlink(missing_ok=True)
        return False
