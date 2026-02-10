from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    upload_dir: Path = Path("uploads")
    allowed_origins: list[str] = ["http://localhost:3000"]
    max_file_size_bytes: int = 100 * 1024 * 1024  # 100MB
    allowed_content_types: list[str] = ["video/mp4", "video/quicktime"]
    allowed_swing_types: list[str] = ["iron"]

    model_config = {"env_file": ".env"}


settings = Settings()
