"""Pipeline error types and internal data models."""


class PipelineError(Exception):
    """Base exception for all pipeline errors."""

    def __init__(self, message: str, error_code: str = "PIPELINE_ERROR"):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class VideoNotFoundError(PipelineError):
    """Uploaded video file not found on disk."""

    def __init__(self, upload_id: str, view: str):
        super().__init__(
            f"Video file for upload {upload_id} ({view}) not found. "
            f"Files may have been cleaned up.",
            error_code="VIDEO_NOT_FOUND",
        )


class LandmarkExtractionError(PipelineError):
    """MediaPipe failed to extract landmarks reliably."""

    def __init__(self, view: str, detection_rate: float):
        super().__init__(
            f"Pose detection rate too low for {view} video "
            f"({detection_rate:.0f}%). Ensure the golfer is fully visible "
            f"with good lighting.",
            error_code="LANDMARK_EXTRACTION_FAILED",
        )


class PhaseDetectionError(PipelineError):
    """Could not detect one or more swing phases."""

    def __init__(self, view: str, detail: str = ""):
        msg = (
            f"Could not detect swing phases in {view} video. "
            f"Ensure the video contains a complete golf swing."
        )
        if detail:
            msg += f" ({detail})"
        super().__init__(msg, error_code="PHASE_DETECTION_FAILED")


class AngleCalculationError(PipelineError):
    """Could not calculate angles at a phase."""

    def __init__(self, view: str, phase: str, detail: str = ""):
        msg = f"Could not calculate angles for {phase} phase in {view} video."
        if detail:
            msg += f" ({detail})"
        super().__init__(msg, error_code="ANGLE_CALCULATION_FAILED")
