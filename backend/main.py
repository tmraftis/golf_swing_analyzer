import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.upload import router as upload_router
from app.routes.analysis import router as analysis_router
from app.routes.video import router as video_router
from app.routes.share import router as share_router
from app.storage.share_store import init_db as init_share_db

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle events."""
    # Startup: verify required resources exist
    model_path = Path(settings.model_path)
    if not model_path.exists():
        logger.warning(
            f"MediaPipe model not found at '{model_path}'. "
            "Analysis endpoints will fail until model is available."
        )
    else:
        logger.info(f"MediaPipe model found: {model_path} ({model_path.stat().st_size / 1e6:.1f} MB)")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(exist_ok=True)
    logger.info(f"Upload directory: {upload_dir.resolve()}")

    # Initialise the share token database
    init_share_db()

    yield  # App runs here

    # Shutdown
    logger.info("Shutting down Pure API")


app = FastAPI(title="Pure API", version="0.2.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/api")
app.include_router(analysis_router, prefix="/api")
app.include_router(share_router, prefix="/api")

# Serve videos with range request support (needed for browser seeking)
app.include_router(video_router)


@app.get("/api/health")
async def health():
    model_available = Path(settings.model_path).exists()
    return {
        "status": "ok",
        "version": "0.2.0",
        "model_available": model_available,
    }
