from pydantic import BaseModel


class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    content_type: str


class UploadResponse(BaseModel):
    status: str
    upload_id: str
    swing_type: str
    files: dict[str, FileInfo]
    message: str


# --- Analysis schemas ---


class AnalyzeRequest(BaseModel):
    swing_type: str = "iron"


class TopDifference(BaseModel):
    rank: int
    angle_name: str
    phase: str
    view: str
    user_value: float
    reference_value: float
    delta: float
    severity: str
    title: str
    description: str
    coaching_tip: str


class AnalysisResponse(BaseModel):
    status: str
    upload_id: str
    swing_type: str
    processing_time_sec: float
    user_angles: dict
    reference_angles: dict
    deltas: dict
    top_differences: list[TopDifference]
    phase_frames: dict
    video_urls: dict[str, str] | None = None
    reference_video_urls: dict[str, str] | None = None
    user_phase_landmarks: dict | None = None
    reference_phase_landmarks: dict | None = None
    user_all_landmarks: dict | None = None
