from pathlib import Path
from pydantic_settings import BaseSettings

# Project root (one level up from backend/)
_PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # Upload settings
    upload_dir: Path = Path("uploads")
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    allowed_content_types: list[str] = ["video/mp4", "video/quicktime"]
    allowed_swing_types: list[str] = ["iron"]

    # Pipeline settings
    model_path: str = str(_PROJECT_ROOT / "scripts" / "pose_landmarker_heavy.task")
    frame_step: int = 2  # Process every Nth frame
    min_detection_rate: float = 0.7  # Minimum pose detection rate

    model_config = {"env_file": ".env"}


settings = Settings()
