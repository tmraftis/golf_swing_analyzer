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
