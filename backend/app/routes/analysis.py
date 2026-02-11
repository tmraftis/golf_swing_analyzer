"""Analysis endpoints: run pipeline and retrieve results."""

import asyncio
import glob
import logging
import os
from functools import partial

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models.schemas import AnalyzeRequest, AnalysisResponse
from app.pipeline import run_analysis
from app.pipeline.models import PipelineError, VideoNotFoundError
from app.storage.analysis_store import get_result, has_result, save_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze/{upload_id}", response_model=AnalysisResponse)
async def analyze_swing(upload_id: str, request: AnalyzeRequest):
    """Run the full analysis pipeline on previously uploaded videos.

    This is a synchronous endpoint that runs the pipeline in a thread pool
    to avoid blocking the event loop. Processing takes ~30-50 seconds.
    """
    # Validate swing type
    if request.swing_type not in settings.allowed_swing_types:
        raise HTTPException(
            422,
            f"Invalid swing_type '{request.swing_type}'. "
            f"Supported: {settings.allowed_swing_types}",
        )

    # Return cached result if available
    if has_result(upload_id):
        logger.info(f"Returning cached result for {upload_id}")
        return _ensure_video_urls(get_result(upload_id), upload_id)

    # Run pipeline in thread pool (CPU-bound work)
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                run_analysis,
                upload_id=upload_id,
                swing_type=request.swing_type,
                upload_dir=str(settings.upload_dir),
                model_path=settings.model_path,
                frame_step=settings.frame_step,
                min_detection_rate=settings.min_detection_rate,
                use_modal=settings.use_modal,
                modal_target_height=settings.modal_target_height,
            ),
        )
    except VideoNotFoundError as e:
        raise HTTPException(404, str(e))
    except PipelineError as e:
        logger.error(f"Pipeline error for {upload_id}: {e}")
        raise HTTPException(422, str(e))
    except Exception as e:
        logger.exception(f"Unexpected error analyzing {upload_id}")
        raise HTTPException(500, f"Analysis failed: {str(e)}")

    # Cache and return
    save_result(upload_id, result)
    return result


def _ensure_video_urls(result: dict, upload_id: str) -> dict:
    """Backfill video URLs if missing from cached results."""
    if result.get("video_urls") is None:
        video_urls = {}
        for view in ("dtl", "fo"):
            matches = glob.glob(f"{settings.upload_dir}/{upload_id}_{view}.*")
            if matches:
                video_urls[view] = f"/uploads/{os.path.basename(matches[0])}"
        if video_urls:
            result["video_urls"] = video_urls

    if result.get("reference_video_urls") is None:
        swing_type = result.get("swing_type", "iron")
        result["reference_video_urls"] = {
            "dtl": f"/reference/{swing_type}/tiger_2000_{swing_type}_dtl.mov",
            "fo": f"/reference/{swing_type}/tiger_2000_{swing_type}_fo.mov",
        }

    return result


@router.get("/analysis/{upload_id}", response_model=AnalysisResponse)
async def get_analysis(upload_id: str):
    """Retrieve a previously computed analysis result."""
    result = get_result(upload_id)
    if result is None:
        raise HTTPException(
            404,
            f"No analysis found for upload '{upload_id}'. "
            "Run POST /api/analyze/{upload_id} first.",
        )
    result = _ensure_video_urls(result, upload_id)
    return result
