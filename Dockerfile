FROM python:3.11-slim

# Install system dependencies for OpenCV/MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# mediapipe pulls full opencv-python which needs X11 libs we don't have.
# Force-replace it with the headless build in a separate step.
RUN pip uninstall -y opencv-python opencv-contrib-python 2>/dev/null || true && \
    pip install --no-cache-dir --force-reinstall opencv-python-headless>=4.8.0

# Download MediaPipe model
RUN mkdir -p /app/models && \
    curl -L -o /app/models/pose_landmarker_heavy.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task

# Copy scripts directory (needed by phase_detector.py and angle_calculator.py)
COPY scripts/ /app/scripts/

# Copy reference data (Tiger Woods comparison data)
COPY reference_data/ /app/reference_data/

# Copy assets (fonts, logos — needed by image_generator.py)
COPY assets/ /app/assets/

# Copy backend application code
COPY backend/ /app/

# Create uploads directory
RUN mkdir -p /app/uploads

EXPOSE 8000

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
