# Pure — Golf Swing Analyzer

**"Swing pure"**

Compare your golf swing to Tiger Woods' iconic 2000 iron swing using computer vision. Choose a camera angle (down-the-line or face-on), upload a single video, and get back angle comparisons, top 3 faults, and drill recommendations — all in under 15 seconds with GPU acceleration.

**Current status:** Phase 4 in progress. Upload a single video (DTL or FO), get AI-powered swing analysis with side-by-side video comparison against Tiger Woods, phase-by-phase navigation, angle comparison tables, and coaching feedback. Toggleable skeleton overlay tracks your body in real-time during video playback (frame-by-frame on user video, phase-only on Tiger). Phase frame images extracted server-side as JPEGs for instant phase switching with zero seek latency. GPU-accelerated landmark extraction via Modal runs on T4 GPUs. Server-side video compression (ffmpeg H.264 ~4Mbps with VFR normalization) reduces storage by ~73% and speeds up video streaming. Authentication via PropelAuth with Google OAuth and Magic Link sign-in — live in both local dev and production (`swingpure.ai`). Phase detection uses preceding-address validation to prevent post-swing walking from being misidentified as the backswing. Angle comparison uses wraparound-aware deltas for atan2-based angles (shoulder/hip line), fixing incorrect 346° deltas that should be ~14°. Shareable 1080×1080 PNG image generated server-side with similarity score, top 3 similarities, and top 3 differences. Fully deterministic analysis pipeline: VFR-normalized compression, SHA-256 content-hash cross-upload deduplication, landmark caching with versioning, IMAGE mode for both extractors, landmark rounding, pinned model version, and hysteresis tie-breaking. V1 is iron-only; driver support is planned for a future release.

---

## How It Works

1. **Sign in** — Google OAuth or Magic Link via PropelAuth
2. **Choose a camera angle** — Down-the-line (DTL) or face-on (FO)
3. **Upload one video** — A single swing video from your chosen angle
3. **Extract landmarks** — MediaPipe Pose Landmarker (heavy model, 33 landmarks) processes every 2nd frame
4. **Detect phases** — Algorithm auto-detects address, top of backswing, impact, and follow-through from wrist trajectory
5. **Calculate angles** — Golf-specific angles computed at each phase (shoulder turn, hip rotation, spine tilt, X-factor, wrist cock, knee flex, etc.)
6. **Compare to Tiger** — User angles compared against Tiger Woods' 2000 iron reference data using weighted deltas
7. **Get coaching feedback** — Top 3 areas for improvement with severity ratings, descriptions, and practice drills; top 3 similarities highlighting what you do well
8. **Share** — Generate a 1080×1080 shareable image with your similarity score, top similarities, and top differences

```
Select view (DTL or FO) + Upload (.mov/.mp4 × 1)
    │
    ▼
POST /api/upload  →  Save file, compress (ffmpeg), return upload_id
    │
    ▼
POST /api/analyze/{upload_id}  (body: { view: "dtl" | "fo" })
    │
    ├─ Extract landmarks (single view)   ~3-5s (Modal GPU, warm start)
    │                                     ~15-25s (local CPU)
    ├─ Detect swing phases                ~0.5s
    ├─ Calculate angles                   ~0.5s
    ├─ Load Tiger reference data          cached
    ├─ Compute deltas                     ~0.1s
    └─ Generate coaching feedback         ~0.1s
    │
    ▼
Response: user_angles, reference_angles, deltas,
          similarity_score, top 3 differences with coaching tips,
          top 3 similarities, video_urls, reference_video_urls,
          user_all_landmarks (frame-by-frame),
          phase_images (JPEG snapshots)
    │
    ▼
/results/{upload_id}?view=dtl  →  Side-by-side video comparison,
                                   phase navigation, angle table,
                                   coaching feedback cards
```

---

## Project Structure

```
golf_swing_analyzer/
├── README.md
├── CLAUDE.md                              # Brand & design system reference
├── .gitignore
├── Golf Swing PRD Anlayzer v4.md          # Full product requirements document
│
├── assets/
│   └── pure-logo.jpeg                     # Brand logo (golfer silhouette)
│
├── frontend/                              # Next.js app (deploys to Vercel)
│   ├── src/
│   │   ├── middleware.ts                  # PropelAuth auth middleware
│   │   ├── app/
│   │   │   ├── layout.tsx                 # Root layout: Inter font, dark bg, AuthProvider
│   │   │   ├── page.tsx                   # Landing page (public)
│   │   │   ├── globals.css                # Tailwind + Pure design tokens
│   │   │   ├── api/auth/[slug]/
│   │   │   │   └── route.ts              # PropelAuth route handler (login/callback/logout)
│   │   │   ├── upload/
│   │   │   │   └── page.tsx               # Upload page (auth required)
│   │   │   ├── results/
│   │   │   │   └── [uploadId]/
│   │   │   │       ├── page.tsx           # Results page (auth required)
│   │   │   │       └── ResultsPageClient.tsx # Client-side results fetcher
│   │   │   └── shared/
│   │   │       └── [shareToken]/
│   │   │           ├── page.tsx           # Public shared results page
│   │   │           └── SharedResultsClient.tsx # Client-side shared results
│   │   ├── components/
│   │   │   ├── Header.tsx                 # Nav bar: logo, auth state, sign in/out
│   │   │   ├── Footer.tsx                 # Minimal footer
│   │   │   ├── HeroSection.tsx            # Landing hero: tagline + auth-aware CTA
│   │   │   ├── FeatureCards.tsx            # 3 value proposition cards
│   │   │   ├── SwingTypeSelector.tsx       # Iron (active) / Driver ("Coming Soon")
│   │   │   ├── VideoDropZone.tsx           # Drag-and-drop upload area
│   │   │   ├── UploadForm.tsx             # View selector + upload → analyze → redirect (sends auth token)
│   │   │   ├── SwingLoadingAnimation.tsx  # Loading animation: 4-pose golfer cross-fade + pipeline progress
│   │   │   ├── Button.tsx                 # Branded button component
│   │   │   └── results/                   # Results dashboard components
│   │   │       ├── ResultsDashboard.tsx   # Main orchestrator (state, layout)
│   │   │       ├── VideoComparison.tsx    # Side-by-side video player with phase seeking (single view)
│   │   │       ├── PhaseTimeline.tsx      # Horizontal 4-phase navigator
│   │   │       ├── AngleComparisonTable.tsx # Angle comparison table (collapsible)
│   │   │       ├── SkeletonOverlay.tsx    # Canvas overlay: frame-by-frame skeleton on video
│   │   │       ├── DifferenceCard.tsx     # Coaching feedback card
│   │   │       ├── ShareModal.tsx        # Share modal with link copy + image download
│   │   │       ├── LoadingSkeleton.tsx    # Loading placeholder
│   │   │       └── ErrorState.tsx         # Error display
│   │   ├── lib/
│   │   │   ├── api.ts                     # API client with auth token support
│   │   │   ├── validation.ts              # File type, size, duration checks
│   │   │   └── constants.ts               # Brand values, limits, accepted types
│   │   └── types/
│   │       └── index.ts                   # TypeScript interfaces (angles, phases, videos, landmarks, frame data)
│   ├── public/
│   │   └── pure-logo.jpeg                 # Logo for frontend
│   ├── .env.local                         # API URL + PropelAuth credentials
│   └── package.json
│
├── modal_app/                             # Modal GPU worker (deploys to Modal)
│   ├── __init__.py
│   └── landmark_worker.py                 # GPU-accelerated MediaPipe extraction
│
├── backend/                               # FastAPI app (deploys to Railway)
│   ├── main.py                            # App entry, CORS, lifespan, routers
│   ├── app/
│   │   ├── config.py                      # Settings (upload, pipeline, Modal, PropelAuth, compression)
│   │   ├── paths.py                       # Shared path constants (PROJECT_ROOT, SCRIPTS_DIR, etc.)
│   │   ├── auth.py                        # PropelAuth init + require_user dependency
│   │   ├── routes/
│   │   │   ├── upload.py                  # POST /api/upload (auth required)
│   │   │   ├── analysis.py               # POST /api/analyze, GET /api/analysis (auth required)
│   │   │   ├── share.py                   # POST/GET /api/share (share token + image generation)
│   │   │   └── video.py                  # Video serving with HTTP range requests (public)
│   │   ├── models/
│   │   │   └── schemas.py                 # Pydantic models (upload + analysis)
│   │   ├── video/
│   │   │   ├── __init__.py
│   │   │   └── compress.py                # ffmpeg H.264 compression (orientation-aware)
│   │   ├── storage/
│   │   │   ├── local.py                   # Save files to local filesystem + compress + SHA-256 hash
│   │   │   ├── analysis_store.py          # In-memory analysis result cache
│   │   │   └── share_store.py             # SQLite-backed share token store
│   │   └── pipeline/                      # Swing analysis pipeline
│   │       ├── __init__.py                # run_analysis() orchestrator
│   │       ├── models.py                  # Pipeline exception hierarchy
│   │       ├── landmark_extractor.py      # MediaPipe pose extraction (local CPU)
│   │       ├── modal_extractor.py         # Modal GPU client (parallel extraction)
│   │       ├── phase_detector.py          # Swing phase detection wrapper
│   │       ├── angle_calculator.py        # Angle calculation wrapper
│   │       ├── reference_data.py          # Tiger reference data loader
│   │       ├── comparison_engine.py       # Delta computation + weighted ranking
│   │       ├── feedback_engine.py         # Fault rules → coaching text
│   │       └── image_generator.py        # 1080×1080 shareable PNG (Pillow)
│   ├── tests/                             # Pytest test suite (60 tests)
│   │   ├── conftest.py                   # Shared fixtures
│   │   ├── test_comparison_engine.py     # Delta computation, ranking, similarities
│   │   ├── test_feedback_engine.py       # Coaching feedback generation
│   │   ├── test_image_generator.py       # Share image generation
│   │   ├── test_phase_detection.py       # Phase detection algorithms
│   │   └── test_schemas.py              # Pydantic model validation
│   ├── requirements.txt
│   ├── Procfile                           # Railway start command
│   └── .env.example
│
├── scripts/                               # Python processing pipeline (standalone)
│   ├── __init__.py                        # Makes scripts importable
│   ├── extract_landmarks.py               # MediaPipe pose extraction from video
│   ├── calculate_angles.py                # Golf angle calculations at each phase
│   ├── detect_phases.py                   # Auto-detect swing phases from landmarks
│   ├── build_reference_json.py            # Generate Tiger reference data files
│   └── pose_landmarker_heavy.task         # MediaPipe model binary (not in git)
│
├── reference_data/                        # Pre-computed reference swings
│   └── iron/                              # Tiger Woods 2000 iron
│       ├── tiger_2000_iron_dtl_reference.json
│       └── tiger_2000_iron_face_on_reference.json
│
├── output/                                # Tiger's processed data (not in git)
│   ├── dtl_landmarks.json
│   ├── fo_landmarks.json
│   ├── dtl_phases.json / fo_phases.json
│   ├── angle_analysis.json
│   └── dtl_frames/ / fo_frames/
│
└── output_user/                           # User test analysis (not in git)
    ├── *_landmarks.json
    ├── *_phases.json
    ├── *_angle_analysis.json
    └── *_frames/
```

---

## Quick Start

### Prerequisites

- **Node.js 18+** and npm
- **Python 3.10+** with pip
- **ffmpeg** (for video compression; `brew install ffmpeg` on macOS — optional, uploads work without it)
- **MediaPipe model** (~30MB, see below)
- **PropelAuth account** with a project configured (see step 2.5 below)

### 1. Download the MediaPipe model

```bash
curl -o scripts/pose_landmarker_heavy.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task
```

### 2. Set up Modal (optional, for GPU acceleration)

```bash
pip install modal
modal token set --token-id <your-id> --token-secret <your-secret>
modal deploy modal_app/landmark_worker.py
```

Then set `USE_MODAL=true` in `backend/.env`. Without Modal, landmark extraction runs locally on CPU (~15-25s per video). With Modal, the video is processed on a T4 GPU (~3-5s). Cold starts add ~18-35s on the first request after idle; optionally add `min_containers=1` to the `@app.function()` decorator to keep a warm instance ready.

### 2.5. Set up PropelAuth

1. Create a project at [auth.propelauth.com](https://auth.propelauth.com)
2. In **Frontend Integration**, set Application URL to `http://localhost:3000` and default redirect after login to `/api/auth/callback`
3. Enable **Google OAuth** and/or **Magic Link** under Sign-In Methods
4. Copy your **Auth URL**, **API Key**, and **Verifier Key** from Backend Integration

**Frontend** — add to `frontend/.env.local`:
```env
NEXT_PUBLIC_AUTH_URL=https://<your-id>.propelauthtest.com
PROPELAUTH_API_KEY=<your-api-key>
PROPELAUTH_VERIFIER_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
PROPELAUTH_REDIRECT_URI=http://localhost:3000/api/auth/callback
```

**Backend** — add to `backend/.env`:
```env
PROPELAUTH_AUTH_URL=https://<your-id>.propelauthtest.com
PROPELAUTH_API_KEY=<your-api-key>
```

### 3. Run the backend

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

The backend will verify the MediaPipe model exists at startup and report its status via `/api/health`.

### 4. Run the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` (already configured for local dev).

### 5. Analyze a swing

1. Go to `http://localhost:3000`
2. Click "Get Started" to sign up via Google or Magic Link
3. After signing in, you'll land on the upload page
4. Select "Iron" as the swing type
5. Choose your camera angle — Down the Line (DTL) or Face On (FO)
6. Upload a video of your swing from the selected angle
7. Click "Submit for Analysis" — takes ~5-10s with Modal, ~15-25s without
8. View your results dashboard: side-by-side video comparison against Tiger, phase-by-phase navigation, angle comparisons, and coaching tips

---

## Tech Stack

| Layer | Technology | Deploy target |
|-------|-----------|--------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 | Vercel |
| Backend | FastAPI, Python 3.10+ | Railway |
| GPU worker | Modal (T4 GPU, parallel extraction) | Modal |
| Pose estimation | MediaPipe Pose Landmarker (heavy, 33 landmarks) | Modal GPU or local CPU |
| Analysis pipeline | Custom Python (landmark extraction, phase detection, angle math, comparison, feedback) | Backend |
| Video compression | ffmpeg (H.264, ~4Mbps, VFR-normalized, orientation-aware) | Backend |
| Storage | Local filesystem (v1), cloud bucket planned | — |
| Auth | PropelAuth (Google OAuth + Magic Link) | PropelAuth hosted |

---

## Design System

Brand name: **Pure** — Tagline: **"Swing pure"**

| Role | Name | Hex |
|------|------|-----|
| Primary base | Blue Charcoal | `#021B22` |
| Primary accent | Cream | `#F6F1E5` |
| Secondary accent 1 | Forest Green | `#2E5B3B` |
| Secondary accent 2 | Pastel Yellow | `#F4D76A` |
| Pop accent | Cardinal Red | `#C53A3A` |

- **Blue Charcoal** — Core background / dark surfaces
- **Cream** — Text on dark backgrounds, light surfaces
- **Forest Green** — Secondary UI elements, success states, selected states
- **Pastel Yellow** — Highlights, callouts, "Coming Soon" badges
- **Cardinal Red** — CTA buttons, error states, severity badges for major faults

Font: **Inter** (Google Fonts)

---

## API Reference

### `GET /api/health`

Health check. Returns server status and whether the MediaPipe model is available.

```json
{ "status": "ok", "version": "0.2.0", "model_available": true }
```

### `POST /api/upload` *(auth required)*

Upload a single swing video for analysis. Requires `Authorization: Bearer <token>` header.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `swing_type` | string | Yes | `"iron"` (only valid value in v1) |
| `view` | string | Yes | `"dtl"` (down-the-line) or `"fo"` (face-on) |
| `video` | file | Yes | Swing video (.mov/.mp4, max 30s) |

**Success (200):**
```json
{
  "status": "success",
  "upload_id": "c524d280-57ec-4944-be20-7269cb66a63a",
  "swing_type": "iron",
  "files": {
    "dtl": { "filename": "..._dtl.mp4", "size_bytes": 8365277, "content_type": "video/quicktime" }
  },
  "message": "Video uploaded successfully. Call POST /api/analyze/{upload_id} to run analysis."
}
```

**Errors:** `400` for invalid swing type, view, or file type, `401` for missing/invalid auth token.

### `POST /api/analyze/{upload_id}` *(auth required)*

Run the analysis pipeline on a previously uploaded video. Processing takes ~5-10s with Modal GPU, ~15-25s with local CPU. Requires `Authorization: Bearer <token>` header.

**Request body:**
```json
{ "swing_type": "iron", "view": "dtl" }
```

**Success (200):**
```json
{
  "status": "success",
  "upload_id": "c524d280-...",
  "swing_type": "iron",
  "processing_time_sec": 12.3,
  "user_angles": {
    "dtl": { "address": { "frame": 0, "angles": { "spine_angle_dtl": 159.7, ... } }, ... }
  },
  "reference_angles": {
    "dtl": { "address": { "angles": { "spine_angle_dtl": 18.9, ... } }, ... }
  },
  "deltas": {
    "dtl": { "address": { "spine_angle_dtl": 140.8, ... }, ... }
  },
  "top_differences": [
    {
      "rank": 1,
      "angle_name": "spine_angle_dtl",
      "phase": "address",
      "view": "dtl",
      "user_value": 159.7,
      "reference_value": 18.9,
      "delta": 140.8,
      "severity": "major",
      "title": "Spine Angle Difference at Address",
      "description": "Your spine angle at address is 159.7 degrees compared to Tiger's 18.9 degrees...",
      "coaching_tip": "Focus on matching Tiger's spine angle at address..."
    },
    { "rank": 2, "..." : "..." },
    { "rank": 3, "..." : "..." }
  ],
  "top_similarities": [
    {
      "rank": 1,
      "angle_name": "right_knee_flex",
      "phase": "address",
      "view": "dtl",
      "user_value": 165.2,
      "reference_value": 165.8,
      "delta": -0.6,
      "title": "Right Knee Flex at Address"
    },
    { "rank": 2, "..." : "..." },
    { "rank": 3, "..." : "..." }
  ],
  "similarity_score": 83,
  "phase_frames": {
    "dtl": { "address": 0, "top": 7, "impact": 11, "follow_through": 18 }
  }
}
```

**Errors:** `404` (upload not found), `422` (pipeline failure), `500` (unexpected error).

### `GET /api/analysis/{upload_id}?view=dtl` *(auth required)*

Retrieve a previously computed analysis result from cache. Requires `Authorization: Bearer <token>` header. The `view` query param specifies which camera angle's results to retrieve (defaults to `"dtl"`).

**Success (200):** Same schema as `POST /api/analyze`.

**Errors:** `401` for missing/invalid auth token, `404` if not yet analyzed.

### `POST /api/share/{upload_id}` *(auth required)*

Create a shareable link for an analysis result. Returns a short share token and a 1080×1080 PNG image.

**Request body:**
```json
{ "view": "dtl" }
```

**Success (200):**
```json
{
  "share_token": "abc123",
  "share_url": "https://swingpure.ai/shared/abc123",
  "image_url": "/api/share/abc123/image"
}
```

### `GET /api/share/{share_token}` *(public)*

Retrieve a shared analysis result by token. Returns the analysis data for public viewing.

### `GET /api/share/{share_token}/image` *(public)*

Download the 1080×1080 shareable PNG image for a shared analysis.

---

## Analysis Pipeline

The pipeline runs as a sequence of steps, each with error handling and logging:

| Step | Module | What it does | Time (Modal) | Time (local) |
|------|--------|-------------|:---:|:---:|
| 1 | `modal_extractor.py` / `landmark_extractor.py` | MediaPipe pose extraction (single video on GPU or CPU); cached per upload with cross-upload hash dedup | ~3-5s (warm) | ~15-25s |
| 1b | `__init__.py` | Round landmarks to 4 decimal places + save cache | ~0.1s | ~0.1s |
| 2 | `phase_detector.py` | Auto-detect address, top, impact, follow-through (hysteresis tie-breaking) | ~0.5s | ~0.5s |
| 3 | `angle_calculator.py` | Compute golf-specific angles at each phase | ~0.5s | ~0.5s |
| 4 | `reference_data.py` | Load Tiger Woods reference (cached with `lru_cache`) | instant | instant |
| 5 | `comparison_engine.py` | Compute deltas, apply weights, rank differences + similarities | ~0.1s | ~0.1s |
| 6 | `feedback_engine.py` | Match fault rules, generate coaching text + similarity titles | ~0.1s | ~0.1s |

### Comparison Engine

Differences are ranked using **weighted absolute deltas**. Biomechanically important angles get higher weights:

| Angle + Phase | Weight |
|--------------|--------|
| Spine angle (DTL) @ impact | 1.5x |
| Lead arm-torso @ top | 1.5x |
| Spine angle (DTL) @ top | 1.3x |
| Spine tilt (FO) @ impact | 1.3x |
| Left elbow @ impact | 1.3x |
| Lead arm-torso @ impact | 1.2x |
| Right elbow @ top | 1.2x |
| Right knee flex @ top | 1.2x |
| Right knee flex @ address | 1.1x |
| Left knee flex @ impact | 1.1x |
| All others | 1.0x |

**Excluded from ranking:** `shoulder_line_angle`, `hip_line_angle`, and `x_factor` are excluded from the top-3 recommendations. These measure 2D line tilt from horizontal, not true 3D rotation, and produce misleading coaching advice. They still appear in the angle comparison table for informational purposes.

The top 3 differences are selected with **view balance** — when both views are analyzed, no more than 2 from the same camera angle; when a single view is analyzed, all 3 can come from that view.

**Similarities** are ranked using the same view-balanced approach but sorted by smallest absolute delta — angles where the user most closely matches Tiger. The top 3 similarities are displayed in the share image alongside the top 3 differences.

### Feedback Engine

26 directional fault rules map specific angle/phase/view/direction combinations to coaching feedback. Every rule has explicit `min_delta` or `max_delta` thresholds — no catch-all rules. Each angle/phase pair has separate "too much" and "too little" rules with distinct coaching text. Each rule includes:

- **Severity** — major, moderate, or minor
- **Title** — human-readable fault name (e.g., "Early Extension (Loss of Posture)")
- **Description** — templated text with user/reference values and directional context
- **Coaching tip** — actionable drill or practice suggestion specific to the direction of the fault

A minimum delta floor of 5° filters noise before ranking. Angles from low-visibility landmarks (< 0.3) are skipped entirely. A directional generic fallback handles angles without dedicated rules (tells the user which way they're off and by how much).

---

## Client-Side Validation

Videos are validated in the browser before upload:

1. **File type** — must be `.mp4` or `.mov` (checks MIME type with extension fallback)
2. **File size** — max 100MB
3. **Duration** — max 30 seconds (read via HTML5 `<video>` element metadata)
4. **Video required** — submit button disabled until a valid video is provided for the selected view

---

## Reference Data

The `reference_data/iron/` directory contains pre-computed Tiger Woods 2000 iron swing data. Each file includes:

- **Metadata:** golfer, year, swing type, video specs, detection rate, pose model
- **Per-phase data** (address, top, impact, follow-through): frame number, timestamp, computed angles, key landmark positions

### Angles by view

| View | Key angles |
|------|-----------|
| **DTL** (down-the-line) | Spine angle (forward bend), lead/trail arm-torso, elbow angles, knee flex, wrist cock, shoulder-hip geometry |
| **FO** (face-on) | Shoulder tilt, hip tilt, shoulder-hip tilt gap, spine tilt, knee flex (both legs), elbow angles |

### Tiger reference summary

| Phase | DTL Spine Angle | FO X-Factor | FO Shoulder Line |
|-------|:-:|:-:|:-:|
| Address | 18.9 | -3.1 | 172.7 |
| Top | 18.4 | -2.2 | 177.0 |
| Impact | 18.7 | -20.7 | 154.3 |
| Follow-through | 8.4 | -19.3 | 151.0 |

---

## Pipeline Scripts (Standalone)

These scripts can also be run independently for debugging or building new reference data:

### 1. Extract landmarks

```bash
python scripts/extract_landmarks.py
```

> **Note:** Video paths are hardcoded in `main()`. Update the `videos` dict to point to your files.

### 2. Detect swing phases

```bash
python scripts/detect_phases.py <landmarks.json> --view dtl|fo
```

### 3. Calculate angles

```bash
python scripts/calculate_angles.py --auto-detect
```

### 4. Build reference data (one-time)

```bash
python scripts/build_reference_json.py
```

---

## Architecture Decisions

- **Frame stepping (every 2nd frame)** — cuts processing time roughly in half while maintaining sufficient resolution for angle calculation
- **Thread pool execution** — analysis runs in `run_in_executor` to avoid blocking the FastAPI event loop
- **In-memory result caching** — analysis results are cached by `{upload_id}_{view}` for instant retrieval on subsequent requests; same upload can have separate DTL and FO results
- **View-specific calculations** — some angles are only meaningful from one camera angle (e.g., X-factor from FO, spine angle from DTL)
- **Weighted ranking** — biomechanically important angles (spine angle at impact, lead arm at top) are weighted higher when selecting top faults
- **View-balanced top 3** — when both views are analyzed, max 2 differences from the same camera angle; when single-view, all 3 can come from that view
- **Auto-trigger analysis after upload** — frontend automatically starts analysis after successful upload for a seamless UX
- **`swing_type` field in all data** — enables future expansion to driver, fairway woods, etc. without schema changes
- **Reference data organized by club** — `reference_data/iron/`, with `reference_data/driver/` reserved
- **Right-handed golfer assumed** — lead arm = left, trail arm = right
- **Frontend and backend independently deployable** — Next.js on Vercel, FastAPI on Railway
- **PropelAuth for authentication** — hosted auth service handles login UI, token issuance, and user management; frontend uses `@propelauth/nextjs` with `AuthProvider` and `useUser()` hook; backend validates JWT tokens via `propelauth-fastapi` with `Depends(require_user)` on protected endpoints; supports Google OAuth and Magic Link sign-in
- **Local filesystem storage for v1** — will move to cloud bucket with 24-hour auto-delete
- **Client-side validation before upload** — reduces backend load and gives instant feedback
- **Tailwind CSS v4 with `@theme` tokens** — design system colors defined as CSS custom properties, no `tailwind.config.ts`
- **`react-dropzone` for file upload UX** — handles drag-and-drop and file selection cleanly
- **`useReducer` for upload form state** — manages the multi-step flow (upload → analyzing → redirect) without a global store
- **HTTP range requests for video serving** — FastAPI's StaticFiles doesn't support range requests, which browsers need for video seeking; custom streaming endpoint returns `206 Partial Content` with proper `Content-Range` headers
- **Velocity-based phase detection** — more robust than Y-position thresholds; anchors on peak downswing speed (the most reliable signal in any swing video) and works backwards/forwards from there
- **Preceding-address validation** — each candidate top-of-backswing must have a still period (address) with hands low within 5 seconds before it; post-swing Y dips (walking away, lowering hands) have no preceding address and are rejected; uses a relaxed velocity threshold (3x `still_threshold`) and requires at least 0.5s of stillness to prevent brief waggle pauses from passing as address
- **Adaptive still_threshold** — auto-calibrated per video using `max(base_threshold, p25_velocity × 3.5)` to handle IMAGE mode's noisier signal; DTL (more tracking noise) gets a higher threshold (~0.002) while FO (cleaner signal) stays near the base (0.001)
- **Visibility-weighted signal filtering** — MediaPipe landmark visibility below 0.4 treated as NaN to prevent tracking artifacts from corrupting phase detection, especially at video boundaries and during fast motion
- **Wraparound-aware angle deltas** — shoulder/hip line angles computed via atan2 wrap at ±180°; comparison engine uses shortest angular distance `(d + 180) % 360 - 180` to avoid nonsensical 346° deltas when the actual difference is ~14°
- **Video readiness tracking in React** — `loadeddata` event listeners ensure video seeking works even when metadata hasn't loaded yet; pending seeks are queued and executed once the video is ready
- **Single-view upload flow** — user selects DTL or FO before uploading, and only one video is processed per analysis; halves processing time vs. dual-view and simplifies the UX
- **Modal GPU acceleration** — landmark extraction offloaded to Modal T4 GPUs. Single-view extraction uses `.remote()` for synchronous processing (~3-5s); dual-view (if both requested) uses `.spawn()` / `.get()` for parallel processing (~5-8s). Uses `RunningMode.IMAGE` for deterministic per-frame detection (VIDEO mode was non-deterministic due to temporal tracking state). Automatic retry on low detection rate with a relaxed threshold. Automatic fallback to local CPU if Modal is unavailable.
- **Video downscaling for inference** — frames downscaled to 960px height before MediaPipe inference on Modal; normalized landmark coordinates remain resolution-independent, with pixel positions mapped back to original dimensions
- **Lazy Modal import** — `modal` package only imported when `USE_MODAL=true`, so the backend works without Modal installed when running locally
- **Server-side video compression** — uploaded videos (typically iPhone HEVC .MOV, ~15Mbps, ~35MB each) are compressed to H.264 1080p ~4Mbps via ffmpeg after upload, reducing storage by ~73% (~35MB → ~8MB per file). Uses `-vsync vfr` to normalize Variable Frame Rate timing metadata without dropping or duplicating frames — this prevents iPhone VFR videos from producing different frame counts on re-encoding. Orientation-aware scale filter preserves portrait (1080×1920) and landscape (1920×1080) dimensions. `+faststart` moves moov atom for HTTP streaming. Graceful fallback: skips compression if ffmpeg is missing or compression fails. Controllable via `COMPRESS_UPLOADS=false` env var
- **Skeleton overlay via canvas** — toggleable pose skeleton drawn on an HTML5 `<canvas>` absolutely positioned over each video using `pointer-events-none`. Landmarks (normalized 0-1 coords) are mapped to pixel positions accounting for `object-contain` letterboxing/pillarboxing via `getVideoRenderRect()`. `ResizeObserver` redraws on container resize. User video has frame-by-frame skeleton tracking during playback via `requestAnimationFrame` loop with binary search for nearest landmark frame by timestamp (~60fps). Tiger video shows skeleton at phase frames only (reference data has 4 phase landmarks, not per-frame). Backend includes both phase landmarks and all-frame landmarks in the `AnalysisResponse` — compact keys (`t`, `lm`) keep payload to ~10-20KB
- **Phase frame image extraction** — server-side JPEG snapshots extracted at each of the 4 phase frames (address, top, impact, follow-through) for both user and reference videos using cv2. Images are preloaded on the frontend via `new Image()` and displayed as `<img>` overlays when paused, eliminating the 50-300ms video seeking latency when switching phases. 8 images per analysis (4 phases × 2 videos), ~85% JPEG quality
- **Shareable image generation** — 1080×1080 PNG rendered at 2× (2160×2160 canvas) with Lanczos downscaling for sharp text. 3-column layout: similarity score (percentage in a ring), top 3 similarities (green cards), and top 3 differences (red cards). Generated server-side with Pillow. Supersampled ring at 4× internal scale. Pixel-aware title truncation using `textbbox()` to measure rendered width
- **Share via token** — `POST /api/share/{upload_id}` creates a short token stored in SQLite, enabling public access to analysis results without authentication. Share URL and image URL returned for social sharing. Frontend ShareModal provides one-click link copy and image download
- **Deterministic analysis pipeline** — seven layers of determinism protection: (1) VFR normalization — ffmpeg `-vsync vfr` ensures iPhone VFR videos produce consistent frame counts across re-encodes; (2) SHA-256 content hashing — raw video bytes hashed before compression, enabling cross-upload deduplication (re-uploading the same video reuses identical landmarks from the first upload); (3) landmark caching with versioning — extracted landmarks saved as JSON with `_cache_version` stamp, reused on re-analysis, stale caches auto-rejected; (4) IMAGE mode for local extractor — matches Modal worker, each frame processed independently with no temporal state; (5) landmark rounding — coordinates rounded to 4 decimal places after extraction to absorb GPU floating-point jitter; (6) pinned model URL — Modal image downloads versioned model (`/float16/1/`) instead of `/latest/`; (7) hysteresis tie-breaking — `_argmin_hysteresis()` / `_argmax_hysteresis()` prefer earliest frame when values within epsilon, preventing phase frame flipping from tiny coordinate differences
- **Top 3 similarities** — `rank_similarities()` in comparison engine finds angles with smallest absolute deltas (closest match to Tiger), using the same view-balanced selection as differences (max 2 from same view). Displayed in share image and available in API response
- **Pytest test suite** — 60 tests covering comparison engine, feedback engine, image generator, phase detection, and schemas. Run with `cd backend && PYTHONPATH=. pytest tests/`
- **Shared paths module** — `app/paths.py` provides `PROJECT_ROOT`, `SCRIPTS_DIR`, `REFERENCE_DATA_DIR`, and `ensure_scripts_importable()` as a single source of truth, eliminating duplicated `sys.path` manipulation across pipeline modules

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Tiger reference data & pipeline validation | Done |
| **1** | Landing page, upload UI, FastAPI backend skeleton | Done |
| **2** | Analysis pipeline, comparison engine, coaching feedback, results UI | Done |
| **3** | Results dashboard: side-by-side video comparison, phase navigation, angle table | Done |
| **3.5** | Authentication: PropelAuth (Google OAuth + Magic Link), protected routes and API endpoints | Done |
| **4** | Skeleton overlays, drill content curation, onboarding, polish, QA | In progress |
| **5+** | Driver swing support, additional clubs, more pro references | Future |

### Phase 1 deliverables (completed)

- Next.js 16 frontend with Tailwind CSS v4 and Pure design system
- Landing page: header, hero section ("Swing pure"), 3 feature cards, footer
- Upload page: swing type selector (Iron active, Driver "Coming Soon"), dual drag-and-drop video upload, client-side validation, submit flow
- FastAPI backend with `POST /api/upload` (accepts swing_type + two videos, saves to local filesystem)
- `GET /api/health` endpoint
- CORS configured for local development
- Responsive design (mobile to desktop)

### Phase 2 deliverables (completed)

- **Analysis pipeline** integrated into FastAPI backend:
  - Landmark extraction via MediaPipe (frame stepping for performance)
  - Automatic swing phase detection (address, top, impact, follow-through)
  - Golf-specific angle calculation at each phase
  - Tiger Woods 2000 reference data loading with angle name mapping
  - Weighted delta computation and significance ranking
  - Rule-based coaching feedback engine (26 directional fault rules)
- **API endpoints:**
  - `POST /api/analyze/{upload_id}` — runs full pipeline (~30-50s), returns results
  - `GET /api/analysis/{upload_id}` — retrieves cached results
- **Frontend updates:**
  - Auto-triggers analysis after upload
  - Animated loading state during analysis
  - Results view: top 3 differences with severity badges, angle comparisons, coaching tips
  - "Analyze Another Swing" reset flow
- **Performance:** ~15-25 seconds end-to-end for single view (within 30s target)

### Phase 3 deliverables (completed)

- **Results dashboard** (`/results/[uploadId]`):
  - Side-by-side video comparison (user swing vs Tiger Woods 2000)
  - Single-view analysis — user chooses DTL or FO before uploading
  - Phase-by-phase navigation (Address, Top, Impact, Follow-Through) seeks both videos to their respective timestamps
  - Play/pause syncs both videos (user vs Tiger)
  - Progress bar with phase markers
  - Collapsible angle comparison table with delta color-coding
  - Top 3 coaching feedback cards with severity badges
- **Video serving with HTTP range requests** — custom endpoint replaces StaticFiles, enabling instant video seeking in the browser
- **Phase detection improvements:**
  - Velocity-based detection: anchors on peak downswing speed, backtracks to find top of backswing
  - Preceding-address validation: each backswing candidate must have a still period with hands low within 5s before it, rejecting post-swing false positives
  - Visibility filtering: frames with low MediaPipe confidence (< 0.4) excluded from signal analysis
  - Address detection picks the most settled frame within the still period (highest Y / hands lowest)
  - Follow-through detection uses midpoint of the first settled period after impact
  - Handles videos with pre-shot routines, waggles, and long setup periods
- **Frontend redirect** — upload form redirects to results page after analysis completes

### Phase 3.5 deliverables (completed)

- **PropelAuth integration** for authentication (Google OAuth + Magic Link):
  - Frontend: `@propelauth/nextjs` with `AuthProvider`, `useUser()`, `useLogoutFunction()`
  - Backend: `propelauth-fastapi` with `require_user` dependency on all protected endpoints
  - Auth route handler at `/api/auth/[slug]` (login, signup, callback, logout)
  - Next.js middleware attaches auth info to all requests
- **Protected routes:** `/upload` and `/results/[uploadId]` require authentication via `getUserOrRedirect()`
- **Protected API endpoints:** `POST /api/upload`, `POST /api/analyze`, `GET /api/analysis` require valid Bearer token
- **Auth-aware UI:**
  - Header shows Sign In / Get Started when logged out; email + Sign Out when logged in
  - Hero CTA switches between "Get Started" (→ signup) and "Start Your Analysis" (→ upload)
  - Landing page remains public
- **Environment configuration:**
  - Frontend: `NEXT_PUBLIC_AUTH_URL`, `PROPELAUTH_API_KEY`, `PROPELAUTH_VERIFIER_KEY`, `PROPELAUTH_REDIRECT_URI`
  - Backend: `PROPELAUTH_AUTH_URL`, `PROPELAUTH_API_KEY`
  - Graceful fallback when PropelAuth is not configured (returns 401)
- **Production deployment:**
  - Frontend live at `swingpure.ai` (Vercel) with production PropelAuth (`auth.swingpure.ai`)
  - Backend live at `golfswinganalyzer-production.up.railway.app` (Railway)
  - Google OAuth and Magic Link sign-in verified in production
- **Server-side video compression:**
  - ffmpeg H.264 compression at ~4Mbps reduces iPhone uploads from ~35MB to ~8MB (~73% reduction)
  - `-vsync vfr` normalizes Variable Frame Rate timing metadata, preventing non-deterministic frame counts
  - Orientation-aware scale filter preserves portrait (1080×1920) and landscape (1920×1080) dimensions
  - `+faststart` moov atom for HTTP streaming compatibility
  - Graceful fallback: skips compression if ffmpeg is unavailable or compression fails
  - Controllable via `COMPRESS_UPLOADS` env var (default: `true`)
  - ffmpeg added to Docker image for production deployment
- **UX improvements:**
  - Removed redundant "Analyze Your Swing" button from header nav
  - Single-view upload flow: user picks DTL or FO, uploads one video, results page auto-detects the view

### Phase 4 deliverables (in progress)

- **Skeleton overlay on video player:**
  - Toggleable pose skeleton drawn on both user and Tiger videos
  - 12 golf-relevant joints (shoulders, elbows, wrists, hips, knees, ankles) connected by skeleton lines
  - Canvas overlay with `object-contain` coordinate mapping for portrait and landscape videos
  - Forest Green lines, Cream joint dots matching design system
  - Toggle button next to play/pause controls
  - **Frame-by-frame tracking on user video:** skeleton follows the body in real-time during playback via `requestAnimationFrame` loop with binary search for nearest landmark frame (~60fps). Backend sends all detected frame landmarks (compact `{t, lm}` format, ~10-20KB)
  - **Phase-only on Tiger video:** skeleton shows at 4 phase frames when paused (reference data doesn't have per-frame landmarks)
  - Backend includes phase landmarks and all-frame landmarks in API response
  - Graceful degradation: toggle hidden if landmark data unavailable (old cached results)
- **Instant phase switching via server-side frame extraction:**
  - JPEG snapshots extracted at each phase frame for both user and Tiger videos (cv2)
  - 8 images per analysis (4 phases × 2 videos) at 85% JPEG quality
  - Frontend preloads all images on mount via `new Image()` for browser cache population
  - `<img>` overlay shown when paused (zIndex 5), hidden during playback — eliminates 50-300ms video seek latency
- **Swing loading animation during upload and analysis:**
  - 4-pose golfer silhouette cross-fade animation (address → backswing → impact → follow-through) on a 5-second loop
  - Custom SVG silhouettes from Figma with uniform sizing via `preserveAspectRatio="xMidYMid meet"`
  - Subtle glow pulse behind silhouette using design system Pastel Yellow
  - Timed pipeline progress steps that simulate backend processing stages (uploading → extracting landmarks → detecting phases → calculating angles → comparing to reference → generating feedback)
  - Phase-aware timer logic: upload step active during upload, remaining steps start when analysis begins
  - Step indicators: Forest Green checkmarks for completed steps, Pastel Yellow dots for active, dim dots for pending
  - Animated ellipsis on active step label with fixed-width container to prevent layout shift
  - Duration hint text ("This usually takes 15–25 seconds") to set user expectations
  - Shown during both video upload and analysis processing (~15-25s total)
- **Branding and UX polish:**
  - Custom favicon: white golfer silhouette on transparent background (multi-size ICO: 16, 32, 48px)
  - Tab title: "Swing Pure"
  - Driver card "Soon" badge positioned consistently with Iron checkmark, mobile-friendly
  - Similarity score displayed as percentage (e.g., "83%") on results page and share image
  - Consistent padding and styling across all pages
- **Shareable results:**
  - Share modal with one-click link copy and downloadable 1080×1080 PNG image
  - Share image: 3-column layout with similarity score ring (percentage), top 3 similarities (green cards), top 3 differences (red cards), footer with "Swing pure" branding
  - Public `/shared/[shareToken]` page for viewing shared results without authentication
  - SQLite-backed share token store
  - Top 3 similarities engine (`rank_similarities()`) — inverse of `rank_differences()`, finds angles with smallest absolute deltas
- **Deterministic pipeline (7 layers):**
  - VFR normalization: ffmpeg `-vsync vfr` ensures consistent frame counts from iPhone VFR videos
  - SHA-256 content hashing: raw video bytes hashed before compression for cross-upload deduplication
  - Landmark caching with versioning: JSON saved alongside video with `_cache_version` stamp; stale caches auto-rejected on version bump
  - Cross-upload landmark reuse: re-uploading the same video finds matching hash from previous upload and copies landmarks
  - Local extractor switched from VIDEO to IMAGE mode (matching Modal worker)
  - Landmark rounding to 4 decimal places absorbs GPU floating-point jitter
  - Modal model URL pinned to versioned path (`/float16/1/`) instead of `/latest/`
  - Hysteresis tie-breaking in phase detection (`_argmin_hysteresis()` / `_argmax_hysteresis()`)
- **Testing:**
  - Pytest test suite with 60 tests covering comparison engine, feedback engine, image generator, phase detection, and schemas
  - Pre-commit hook for running tests
- **Code quality:**
  - Extracted shared `app/paths.py` module (single source of truth for project paths)
  - Eliminated duplicated `sys.path` manipulation across pipeline modules

### Phase 4 remaining

- ~~**Angle calculation & feedback quality improvements**~~ — Done: FO tilt angles excluded from ranking, all catch-all rules replaced with 26 directional rules, reference data rebuilt with visibility filtering, angle weights re-tuned, frontend labels corrected
- Drill content curation and expanded coaching tips
- Onboarding flow and polish
- QA and edge case handling

---

## Performance Targets

| Metric | Target | Local CPU | Modal GPU (warm) |
|--------|--------|:---------:|:---------:|
| End-to-end processing time (single view) | <30s | ~15-25s | ~5-10s |
| Landmark detection rate | >70% | Varies by video quality | Same |
| Top differences returned | 3 | 3 | 3 |
| System uptime (once deployed) | 99% | — | — |

---

## Known Issues — Angle Calculation Audit

A thorough audit of the angle calculation pipeline found that the **core math is correct** (geometry functions, coordinate transforms, reference data generation). The system is internally consistent (same code computes user and reference angles), so relative comparisons are valid. Most feedback quality issues have been resolved.

### ~~Issue 1: Face-On "Rotation" Angles Are Actually Line Tilts~~ (FIXED)

`shoulder_line_angle`, `hip_line_angle`, and `x_factor` measure 2D line tilt from horizontal, not true 3D rotation. These are now **excluded from the top-3 ranking** entirely — they still appear in the angle comparison table for informational purposes but no longer drive coaching recommendations. Frontend labels renamed from "Shoulder Turn" / "Hip Rotation" / "X-Factor" to "Shoulder Tilt" / "Hip Tilt" / "Shoulder-Hip Tilt Gap" to accurately describe what they measure.

### ~~Issue 2: Too Many Rules Fire on Any Delta~~ (FIXED)

All 9 catch-all fault rules (`min_delta=None, max_delta=None`) have been replaced with **26 directional rules**, each with explicit thresholds. Every angle/phase pair now has separate "too much" and "too little" rules with distinct coaching text (e.g., "Early Extension" vs "Excessive Forward Bend" for spine angle at impact). No catch-all threshold logic remains.

### ~~Issue 3: No Minimum Delta Floor for Ranking~~ (FIXED)

A `MIN_DELTA_DEGREES = 5` floor was added to `rank_differences()` — deltas below 5° are filtered out before ranking.

### ~~Issue 4: Low-Visibility Landmarks Feed Into Rankings~~ (FIXED)

All angle calculations now use `get_landmark_2d()` with a `VISIBILITY_THRESHOLD = 0.3` — landmarks below this threshold return `None`, causing the angle to be skipped. The Tiger reference data has been rebuilt with visibility filtering, dropping unreliable angles (e.g., DTL `left_elbow` at address where visibility was 0.167, DTL `right_elbow` at follow-through where visibility was 0.121, FO `left_elbow` at follow-through where visibility was 0.091). Both `build_reference_json.py` and `calculate_angles.py` use the same threshold, ensuring consistent handling.

### Issue 5: Camera Orientation Assumption (LOW)

**File:** `scripts/calculate_angles.py` — `calc_spine_tilt()`

The sign of `spine_tilt_fo` depends on which side of the golfer the face-on camera is positioned. MediaPipe's left/right labels refer to anatomical sides, so this is usually consistent, but there's no handling for left-handed golfers or unusual camera angles.

**Fix for later:** Add left-handed golfer detection or a manual toggle.

### ~~Issue 6: atan2 Discontinuity Near 180°~~ (FIXED)

The comparison engine now uses wraparound-aware angular difference `(d + 180) % 360 - 180` for `shoulder_line_angle` and `hip_line_angle`. The X-factor calculation also uses this normalization.

### ~~Issue 7: IMAGE Mode Produces Noisier Velocity Signal~~ (FIXED)

Both Modal and local extractors now use `RunningMode.IMAGE` for deterministic extraction. Noisier velocity signal fixed with adaptive still_threshold, time-based minimum stillness, Y-minimum follow-through detection, and impact refinement. Additional determinism layers: VFR normalization (`-vsync vfr` in ffmpeg), SHA-256 content-hash cross-upload deduplication, landmark caching with versioning, landmark rounding (4 decimal places), pinned model version, and hysteresis tie-breaking in phase detection.

### Remaining Fix Priority

1. **Left-handed golfer support** — future enhancement
2. **Expand coaching drill content** — more drills per fault beyond the current single tip
3. **Onboarding flow** — tutorial pop-up on first login

---

## Contributing

1. Clone the repo
2. Download the MediaPipe model (see [Quick Start](#quick-start))
3. Run `npm install` in `frontend/` and `pip install -r requirements.txt` in `backend/`

When adding a new swing type (e.g., driver):
1. Source high-quality DTL and FO reference videos
2. Process through `extract_landmarks.py`
3. Identify phase frames and run `calculate_angles.py`
4. Use `build_reference_json.py` as a template to generate `reference_data/<swing_type>/` files
5. Add fault rules for the new swing type in `feedback_engine.py`
6. Add angle weights in `comparison_engine.py` if different from iron
