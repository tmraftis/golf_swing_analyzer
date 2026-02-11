from pathlib import Path
from pydantic_settings import BaseSettings

# Project root (one level up from backend/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent


def _find_model_path() -> str:
    """Find the MediaPipe model, checking multiple locations."""
    candidates = [
        _PROJECT_ROOT / "scripts" / "pose_landmarker_heavy.task",  # local dev
        Path("/app/models/pose_landmarker_heavy.task"),  # Docker / Railway
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return str(candidates[0])  # fallback to local dev path


class Settings(BaseSettings):
    # Upload settings
    upload_dir: Path = Path("uploads")
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    allowed_content_types: list[str] = ["video/mp4", "video/quicktime"]
    allowed_swing_types: list[str] = ["iron"]

    # Pipeline settings
    model_path: str = _find_model_path()
    frame_step: int = 2  # Process every Nth frame
    min_detection_rate: float = 0.7  # Minimum pose detection rate

    # Video compression settings
    compress_uploads: bool = True  # Compress uploaded videos to H.264 ~4Mbps

    # Modal settings (GPU-accelerated landmark extraction)
    use_modal: bool = False  # Enable Modal for landmark extraction
    modal_target_height: int = 960  # Downscale frames before inference

    # PropelAuth settings
    propelauth_auth_url: str = ""
    propelauth_api_key: str = ""

    model_config = {"env_file": ".env", "protected_namespaces": ("settings_",)}


settings = Settings()
