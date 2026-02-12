# Pure — Golf Swing Analyzer

**"Swing pure"**

Compare your golf swing to Tiger Woods' iconic 2000 iron swing using computer vision. Upload down-the-line (DTL) and face-on (FO) videos, and get back angle comparisons, top 3 faults, and drill recommendations — all in under 20 seconds with GPU acceleration.

**Current status:** Phase 4 in progress. Upload videos, get AI-powered swing analysis with side-by-side video comparison against Tiger Woods, phase-by-phase navigation, angle comparison tables, and coaching feedback. Toggleable skeleton overlay tracks your body in real-time during video playback (frame-by-frame on user video, phase-only on Tiger). Phase frame images extracted server-side as JPEGs for instant phase/view switching with zero seek latency. GPU-accelerated landmark extraction via Modal runs both videos in parallel on T4 GPUs. Server-side video compression (ffmpeg H.264 ~4Mbps) reduces storage by ~73% and speeds up video streaming. Authentication via PropelAuth with Google OAuth and Magic Link sign-in — live in both local dev and production (`swingpure.ai`). Phase detection now includes a swing window constraint to prevent post-swing walking from being misidentified as the backswing. Angle comparison uses wraparound-aware deltas for atan2-based angles (shoulder/hip line), fixing incorrect 346° deltas that should be ~14°. V1 is iron-only; driver support is planned for a future release.

---

## How It Works

1. **Sign in** — Google OAuth or Magic Link via PropelAuth
2. **Upload two videos** — Down-the-line (DTL) and face-on (FO) angles of your swing
2. **Extract landmarks** — MediaPipe Pose Landmarker (heavy model, 33 landmarks) processes every 2nd frame
3. **Detect phases** — Algorithm auto-detects address, top of backswing, impact, and follow-through from wrist trajectory
4. **Calculate angles** — Golf-specific angles computed at each phase (shoulder turn, hip rotation, spine tilt, X-factor, wrist cock, knee flex, etc.)
5. **Compare to Tiger** — User angles compared against Tiger Woods' 2000 iron reference data using weighted deltas
6. **Get coaching feedback** — Top 3 areas for improvement with severity ratings, descriptions, and practice drills

```
Upload (.mov/.mp4 × 2)
    │
    ▼
POST /api/upload  →  Save files, compress (ffmpeg), return upload_id
    │
    ▼
POST /api/analyze/{upload_id}
    │
    ├─ Extract landmarks (DTL + FO)     ~5-8s (Modal GPU, warm start)
    │                                    ~15-25s each (local CPU, sequential)
    ├─ Detect swing phases               ~1s
    ├─ Calculate angles                   ~0.5s
    ├─ Load Tiger reference data          cached
    ├─ Compute deltas                     ~0.1s
    └─ Generate coaching feedback         ~0.1s
    │
    ▼
Response: user_angles, reference_angles, deltas,
          top 3 differences with coaching tips,
          video_urls, reference_video_urls,
          user_all_landmarks (frame-by-frame),
          phase_images (JPEG snapshots)
    │
    ▼
/results/{upload_id}  →  Side-by-side video comparison,
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
│   │   │   └── results/
│   │   │       └── [uploadId]/
│   │   │           ├── page.tsx           # Results page (auth required)
│   │   │           └── ResultsPageClient.tsx # Client-side results fetcher
│   │   ├── components/
│   │   │   ├── Header.tsx                 # Nav bar: logo, auth state, sign in/out
│   │   │   ├── Footer.tsx                 # Minimal footer
│   │   │   ├── HeroSection.tsx            # Landing hero: tagline + auth-aware CTA
│   │   │   ├── FeatureCards.tsx            # 3 value proposition cards
│   │   │   ├── SwingTypeSelector.tsx       # Iron (active) / Driver ("Coming Soon")
│   │   │   ├── VideoDropZone.tsx           # Drag-and-drop upload area
│   │   │   ├── UploadForm.tsx             # Upload → analyze → redirect (sends auth token)
│   │   │   ├── Button.tsx                 # Branded button component
│   │   │   └── results/                   # Results dashboard components
│   │   │       ├── ResultsDashboard.tsx   # Main orchestrator (state, layout)
│   │   │       ├── VideoComparison.tsx    # Side-by-side video player with phase seeking (all views preloaded)
│   │   │       ├── PhaseTimeline.tsx      # Horizontal 4-phase navigator
│   │   │       ├── ViewToggle.tsx         # DTL/FO segmented control
│   │   │       ├── AngleComparisonTable.tsx # Angle comparison table (collapsible)
│   │   │       ├── SkeletonOverlay.tsx    # Canvas overlay: frame-by-frame skeleton on video
│   │   │       ├── DifferenceCard.tsx     # Coaching feedback card
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
│   │   ├── auth.py                        # PropelAuth init + require_user dependency
│   │   ├── routes/
│   │   │   ├── upload.py                  # POST /api/upload (auth required)
│   │   │   ├── analysis.py               # POST /api/analyze, GET /api/analysis (auth required)
│   │   │   └── video.py                  # Video serving with HTTP range requests (public)
│   │   ├── models/
│   │   │   └── schemas.py                 # Pydantic models (upload + analysis)
│   │   ├── video/
│   │   │   ├── __init__.py
│   │   │   └── compress.py                # ffmpeg H.264 compression (orientation-aware)
│   │   ├── storage/
│   │   │   ├── local.py                   # Save files to local filesystem + compress
│   │   │   └── analysis_store.py          # In-memory analysis result cache
│   │   └── pipeline/                      # Swing analysis pipeline
│   │       ├── __init__.py                # run_analysis() orchestrator
│   │       ├── models.py                  # Pipeline exception hierarchy
│   │       ├── landmark_extractor.py      # MediaPipe pose extraction (local CPU)
│   │       ├── modal_extractor.py         # Modal GPU client (parallel extraction)
│   │       ├── phase_detector.py          # Swing phase detection wrapper
│   │       ├── angle_calculator.py        # Angle calculation wrapper
│   │       ├── reference_data.py          # Tiger reference data loader
│   │       ├── comparison_engine.py       # Delta computation + weighted ranking
│   │       └── feedback_engine.py         # Fault rules → coaching text
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
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
```

### 2. Set up Modal (optional, for GPU acceleration)

```bash
pip install modal
modal token set --token-id <your-id> --token-secret <your-secret>
modal deploy modal_app/landmark_worker.py
```

Then set `USE_MODAL=true` in `backend/.env`. Without Modal, landmark extraction runs locally on CPU (~50s). With Modal, both videos are processed in parallel on T4 GPUs (~5-8s). Cold starts add ~18-35s on the first request after idle; optionally add `min_containers=1` to the `@app.function()` decorator to keep a warm instance ready.

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
5. Upload a down-the-line (DTL) and face-on (FO) video of your swing
6. Click "Submit for Analysis" — takes ~10-15s with Modal, ~50s without
7. View your results dashboard: side-by-side video comparison against Tiger, phase-by-phase navigation, angle comparisons, and coaching tips

---

## Tech Stack

| Layer | Technology | Deploy target |
|-------|-----------|--------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 | Vercel |
| Backend | FastAPI, Python 3.10+ | Railway |
| GPU worker | Modal (T4 GPU, parallel extraction) | Modal |
| Pose estimation | MediaPipe Pose Landmarker (heavy, 33 landmarks) | Modal GPU or local CPU |
| Analysis pipeline | Custom Python (landmark extraction, phase detection, angle math, comparison, feedback) | Backend |
| Video compression | ffmpeg (H.264, ~4Mbps, orientation-aware) | Backend |
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

Upload two swing videos for analysis. Requires `Authorization: Bearer <token>` header.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `swing_type` | string | Yes | `"iron"` (only valid value in v1) |
| `video_dtl` | file | Yes | Down-the-line video (.mov/.mp4, max 30s) |
| `video_fo` | file | Yes | Face-on video (.mov/.mp4, max 30s) |

**Success (200):**
```json
{
  "status": "success",
  "upload_id": "c524d280-57ec-4944-be20-7269cb66a63a",
  "swing_type": "iron",
  "files": {
    "dtl": { "filename": "..._dtl.mp4", "size_bytes": 8365277, "content_type": "video/quicktime" },
    "fo": { "filename": "..._fo.mp4", "size_bytes": 9733611, "content_type": "video/quicktime" }
  },
  "message": "Videos uploaded successfully. Call POST /api/analyze/{upload_id} to run analysis."
}
```

**Errors:** `400` for invalid swing type or file type, `401` for missing/invalid auth token.

### `POST /api/analyze/{upload_id}` *(auth required)*

Run the full analysis pipeline on previously uploaded videos. Processing takes ~10-15s with Modal GPU, ~50s with local CPU. Requires `Authorization: Bearer <token>` header.

**Request body:**
```json
{ "swing_type": "iron" }
```

**Success (200):**
```json
{
  "status": "success",
  "upload_id": "c524d280-...",
  "swing_type": "iron",
  "processing_time_sec": 50.8,
  "user_angles": {
    "dtl": { "address": { "frame": 0, "angles": { "spine_angle_dtl": 159.7, ... } }, ... },
    "fo": { "top": { "frame": 20, "angles": { "shoulder_line_angle": 95.7, ... } }, ... }
  },
  "reference_angles": {
    "dtl": { "address": { "angles": { "spine_angle_dtl": 18.9, ... } }, ... },
    "fo": { ... }
  },
  "deltas": {
    "dtl": { "address": { "spine_angle_dtl": 140.8, ... }, ... },
    "fo": { ... }
  },
  "top_differences": [
    {
      "rank": 1,
      "angle_name": "right_elbow",
      "phase": "top",
      "view": "fo",
      "user_value": 7.4,
      "reference_value": 164.7,
      "delta": -157.3,
      "severity": "moderate",
      "title": "Right Elbow Angle Difference at Top of Backswing",
      "description": "Your right elbow angle at top of backswing is 7.4 degrees compared to Tiger's 164.7 degrees...",
      "coaching_tip": "Focus on matching Tiger's right elbow angle at the top of backswing position..."
    },
    { "rank": 2, "..." : "..." },
    { "rank": 3, "..." : "..." }
  ],
  "phase_frames": {
    "dtl": { "address": 0, "top": 7, "impact": 11, "follow_through": 18 },
    "fo": { "address": 7, "top": 20, "impact": 26, "follow_through": 33 }
  }
}
```

**Errors:** `404` (upload not found), `422` (pipeline failure), `500` (unexpected error).

### `GET /api/analysis/{upload_id}` *(auth required)*

Retrieve a previously computed analysis result from cache. Requires `Authorization: Bearer <token>` header.

**Success (200):** Same schema as `POST /api/analyze`.

**Errors:** `401` for missing/invalid auth token, `404` if not yet analyzed.

---

## Analysis Pipeline

The pipeline runs as a sequence of steps, each with error handling and logging:

| Step | Module | What it does | Time (Modal) | Time (local) |
|------|--------|-------------|:---:|:---:|
| 1 | `modal_extractor.py` / `landmark_extractor.py` | MediaPipe pose extraction (parallel on GPU or sequential on CPU) | ~5-8s total (warm) | ~15-25s × 2 |
| 2 | `phase_detector.py` | Auto-detect address, top, impact, follow-through | ~0.5s | ~0.5s |
| 3 | `angle_calculator.py` | Compute golf-specific angles at each phase | ~0.5s | ~0.5s |
| 4 | `reference_data.py` | Load Tiger Woods reference (cached with `lru_cache`) | instant | instant |
| 5 | `comparison_engine.py` | Compute deltas, apply weights, rank by significance | ~0.1s | ~0.1s |
| 6 | `feedback_engine.py` | Match fault rules, generate coaching text | ~0.1s | ~0.1s |

### Comparison Engine

Differences are ranked using **weighted absolute deltas**. Biomechanically important angles get higher weights:

| Angle + Phase | Weight |
|--------------|--------|
| Lead arm-torso @ top | 1.5x |
| Spine angle @ impact | 1.5x |
| X-factor @ top | 1.3x |
| Shoulder line @ top/impact | 1.2x |
| Spine tilt @ impact | 1.2x |
| Right elbow @ top | 1.1x |
| Left elbow @ impact | 1.1x |
| All others | 1.0x |

The top 3 differences are selected with **view balance** — no more than 2 from the same camera angle (DTL or FO).

### Feedback Engine

16 fault rules map specific angle/phase/view combinations to coaching feedback. Each rule includes:

- **Severity** — major, moderate, or minor
- **Title** — human-readable fault name (e.g., "Flying Right Elbow")
- **Description** — templated text with user/reference values
- **Coaching tip** — actionable drill or practice suggestion

Rules without specific thresholds use per-view catch-all triggers: DTL at `abs(delta) > 8°`, face-on at `abs(delta) > 15°` (face-on angles are noisier due to 2D projection). A minimum delta floor of 5° filters noise before ranking. Angles from low-visibility landmarks (< 0.3) are skipped entirely. A generic fallback handles angles without dedicated rules.

---

## Client-Side Validation

Videos are validated in the browser before upload:

1. **File type** — must be `.mp4` or `.mov` (checks MIME type with extension fallback)
2. **File size** — max 100MB
3. **Duration** — max 30 seconds (read via HTML5 `<video>` element metadata)
4. **Both angles required** — submit button disabled until both DTL and FO are valid

---

## Reference Data

The `reference_data/iron/` directory contains pre-computed Tiger Woods 2000 iron swing data. Each file includes:

- **Metadata:** golfer, year, swing type, video specs, detection rate, pose model
- **Per-phase data** (address, top, impact, follow-through): frame number, timestamp, computed angles, key landmark positions

### Angles by view

| View | Key angles |
|------|-----------|
| **DTL** (down-the-line) | Spine angle (forward bend), lead/trail arm-torso, elbow angles, knee flex, wrist cock, shoulder-hip geometry |
| **FO** (face-on) | Shoulder line angle, hip line angle, X-factor (shoulder-hip separation), spine tilt, knee flex (both legs), elbow angles |

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
- **In-memory result caching** — analysis results are cached by upload_id for instant retrieval on subsequent requests
- **View-specific calculations** — some angles are only meaningful from one camera angle (e.g., X-factor from FO, spine angle from DTL)
- **Weighted ranking** — biomechanically important angles (spine angle at impact, lead arm at top) are weighted higher when selecting top faults
- **View-balanced top 3** — max 2 differences from the same camera angle ensures balanced feedback
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
- **Swing window constraint** — phase detection limits the search to a 6-second window after the last still period (address), preventing post-swing walking/movement from being misidentified as the backswing; handles videos with long pre-shot routines and post-swing footage
- **Visibility-weighted signal filtering** — MediaPipe landmark visibility below 0.4 treated as NaN to prevent tracking artifacts from corrupting phase detection, especially at video boundaries and during fast motion
- **Wraparound-aware angle deltas** — shoulder/hip line angles computed via atan2 wrap at ±180°; comparison engine uses shortest angular distance `(d + 180) % 360 - 180` to avoid nonsensical 346° deltas when the actual difference is ~14°
- **Video readiness tracking in React** — `loadeddata` event listeners ensure video seeking works even when metadata hasn't loaded yet; pending seeks are queued and executed once the video is ready
- **Preloaded video views** — all 4 videos (user DTL, user FO, ref DTL, ref FO) are rendered simultaneously with `preload="auto"` and toggled via CSS visibility; switching between DTL and Face On is instant after initial load
- **Modal GPU acceleration** — landmark extraction offloaded to Modal T4 GPUs, with both DTL and FO videos processed in parallel via `.spawn()` / `.get()`. Reduces extraction from ~50s (sequential CPU) to ~5-8s (parallel GPU). Automatic fallback to local CPU if Modal is unavailable.
- **Video downscaling for inference** — frames downscaled to 960px height before MediaPipe inference on Modal; normalized landmark coordinates remain resolution-independent, with pixel positions mapped back to original dimensions
- **Lazy Modal import** — `modal` package only imported when `USE_MODAL=true`, so the backend works without Modal installed when running locally
- **Server-side video compression** — uploaded videos (typically iPhone HEVC .MOV, ~15Mbps, ~35MB each) are compressed to H.264 1080p ~4Mbps via ffmpeg after upload, reducing storage by ~73% (~35MB → ~8MB per file). Orientation-aware scale filter preserves portrait (1080×1920) and landscape (1920×1080) dimensions. `+faststart` moves moov atom for HTTP streaming. Graceful fallback: skips compression if ffmpeg is missing or compression fails. Controllable via `COMPRESS_UPLOADS=false` env var
- **Skeleton overlay via canvas** — toggleable pose skeleton drawn on an HTML5 `<canvas>` absolutely positioned over each video using `pointer-events-none`. Landmarks (normalized 0-1 coords) are mapped to pixel positions accounting for `object-contain` letterboxing/pillarboxing via `getVideoRenderRect()`. `ResizeObserver` redraws on container resize. User video has frame-by-frame skeleton tracking during playback via `requestAnimationFrame` loop with binary search for nearest landmark frame by timestamp (~60fps). Tiger video shows skeleton at phase frames only (reference data has 4 phase landmarks, not per-frame). Backend includes both phase landmarks and all-frame landmarks in the `AnalysisResponse` — compact keys (`t`, `lm`) keep payload to ~10-20KB
- **Phase frame image extraction** — server-side JPEG snapshots extracted at each of the 4 phase frames (address, top, impact, follow-through) for both user and reference videos using cv2. Images are preloaded on the frontend via `new Image()` and displayed as `<img>` overlays when paused, eliminating the 50-300ms video seeking latency when switching phases or views. 16 images total (4 phases × 2 views × 2 videos), ~85% JPEG quality

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
  - Rule-based coaching feedback engine (18 fault rules)
- **API endpoints:**
  - `POST /api/analyze/{upload_id}` — runs full pipeline (~30-50s), returns results
  - `GET /api/analysis/{upload_id}` — retrieves cached results
- **Frontend updates:**
  - Auto-triggers analysis after upload
  - Animated loading state during analysis
  - Results view: top 3 differences with severity badges, angle comparisons, coaching tips
  - "Analyze Another Swing" reset flow
- **Performance:** ~50 seconds end-to-end (within 60s target)

### Phase 3 deliverables (completed)

- **Results dashboard** (`/results/[uploadId]`):
  - Side-by-side video comparison (user swing vs Tiger Woods 2000)
  - DTL/FO view toggle switches both videos simultaneously
  - Phase-by-phase navigation (Address, Top, Impact, Follow-Through) seeks both videos to their respective timestamps
  - Play/pause syncs both videos
  - Progress bar with phase markers
  - Collapsible angle comparison table with delta color-coding
  - Top 3 coaching feedback cards with severity badges
- **Video serving with HTTP range requests** — custom endpoint replaces StaticFiles, enabling instant video seeking in the browser
- **Phase detection improvements:**
  - Velocity-based detection: anchors on peak downswing speed, backtracks to find top of backswing
  - Swing window constraint: limits search to 6s after the last still period, preventing post-swing walking from being misidentified as the backswing
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
  - Orientation-aware scale filter preserves portrait (1080×1920) and landscape (1920×1080) dimensions
  - `+faststart` moov atom for HTTP streaming compatibility
  - Graceful fallback: skips compression if ffmpeg is unavailable or compression fails
  - Controllable via `COMPRESS_UPLOADS` env var (default: `true`)
  - ffmpeg added to Docker image for production deployment
- **UX improvements:**
  - Removed redundant "Analyze Your Swing" button from header nav
  - Preloaded all video views for instant DTL/Face On switching

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
  - 16 images total (4 phases × 2 views × 2 videos) at 85% JPEG quality
  - Frontend preloads all images on mount via `new Image()` for browser cache population
  - `<img>` overlay shown when paused (zIndex 5), hidden during playback — eliminates 50-300ms video seek latency
- **Branding and UX polish:**
  - Custom favicon: white golfer silhouette on transparent background (multi-size ICO: 16, 32, 48px)
  - Tab title: "Swing Pure"
  - Driver card "Soon" badge positioned consistently with Iron checkmark, mobile-friendly

### Phase 4 remaining

- **Angle calculation & feedback quality improvements** (see [Known Issues](#known-issues--angle-calculation-audit) below)
- Drill content curation and expanded coaching tips
- Onboarding flow and polish
- QA and edge case handling

---

## Performance Targets

| Metric | Target | Local CPU | Modal GPU (warm) |
|--------|--------|:---------:|:---------:|
| End-to-end processing time | <60s | ~50s | ~10-15s |
| Landmark detection rate | >70% | Varies by video quality | Same |
| Top differences returned | 3 | 3 | 3 |
| System uptime (once deployed) | 99% | — | — |

---

## Known Issues — Angle Calculation Audit

A thorough audit of the angle calculation pipeline found that the **core math is correct** (geometry functions, coordinate transforms, reference data generation) but several issues cause the **top 3 recommendations to feel off**. The system is internally consistent (same code computes user and reference angles), so relative comparisons are valid, but the feedback quality suffers from the problems below.

### Issue 1: Face-On "Rotation" Angles Are Actually Line Tilts (HIGH)

**Files:** `scripts/calculate_angles.py` — `calc_shoulder_turn_fo()`, `calc_hip_turn_fo()`

`shoulder_line_angle` and `hip_line_angle` use `atan2(dy, dx)` to measure the **tilt** of the shoulder/hip line relative to horizontal in the 2D face-on image. This is fundamentally different from the **rotational turn** these names suggest. Tiger's reference X-factor at top is -2.2° (line tilt difference), whereas real golf instruction cites ~55° (3D rotational separation). The values are meaningless to any golfer who knows what "shoulder turn" or "X-factor" means.

**Impact:** Coaching titles like "Incomplete Shoulder Turn" and "Shoulder-Hip Separation Off" fire based on line tilt deltas, not actual rotation. The tips ("feel your back face the target") describe rotation — but the measurement doesn't capture rotation from this view.

**Fix options:**
- Rename these angles to reflect what they actually measure (e.g., "Shoulder Line Tilt", "Hip Line Tilt", "Shoulder-Hip Tilt Separation")
- Update fault rule titles and coaching descriptions to match the 2D measurement
- Or: remove these from the top-3 ranking entirely and focus on angles that are well-captured in 2D (elbow flex, knee flex, spine angle, arm-torso separation)

### Issue 2: Too Many Rules Fire on Any Delta > 8° (HIGH)

**File:** `backend/app/pipeline/feedback_engine.py` — `_rule_matches()`, `FAULT_RULES`

9 out of 16 fault rules have `min_delta=None, max_delta=None`, which means they trigger on **any** absolute delta > 8°. Face-on angles are inherently noisier (small body movements create large apparent angle changes in 2D projection), so an 8° threshold is too aggressive. Almost every swing will surface multiple face-on "faults" even if the golfer has great form.

**Affected rules:** Incomplete Shoulder Turn, Hip Rotation Timing, Shoulder-Hip Separation, Reverse Spine Angle, Arm-Body Connection Lost, Lead Leg Position, and Spine Angle Change at Impact (DTL).

**Fix options:**
- Raise the default threshold to 12-15° for face-on rules
- Add angle-specific thresholds instead of using `None/None` catch-all
- Add a minimum absolute delta floor (e.g., 5°) in `rank_differences()` so trivial deltas never surface

### ~~Issue 3: No Minimum Delta Floor for Ranking~~ (FIXED)

A `MIN_DELTA_DEGREES = 5` floor was added to `rank_differences()` — deltas below 5° are filtered out before ranking.

### Issue 4: Low-Visibility Landmarks Feed Into Rankings (MEDIUM)

**File:** `scripts/calculate_angles.py`

In the DTL reference data, left-side landmarks have visibility as low as 0.11 (left_elbow at address) and 0.11 (left_knee at address) due to body occlusion. Angles computed from these landmarks are unreliable. The only visibility check in the angle calculator is for `right_wrist_cock` (requires > 0.4). All other angles use landmarks regardless of visibility.

Both user and reference are affected equally (so deltas are at least consistently noisy), but junk angles can still surface as top recommendations.

**Fix:** Add a visibility threshold (e.g., 0.3) to all angle calculations. If any required landmark is below threshold, skip that angle for that phase. Propagate `None` values through the delta computation.

### Issue 5: Camera Orientation Assumption (LOW)

**File:** `scripts/calculate_angles.py` — `calc_spine_tilt()`

The sign of `spine_tilt_fo` depends on which side of the golfer the face-on camera is positioned. MediaPipe's left/right labels refer to anatomical sides, so this is usually consistent, but there's no handling for left-handed golfers or unusual camera angles.

**Fix for later:** Add left-handed golfer detection or a manual toggle.

### ~~Issue 6: atan2 Discontinuity Near 180°~~ (FIXED)

**Files:** `backend/app/pipeline/comparison_engine.py`, `scripts/calculate_angles.py`

The comparison engine now uses wraparound-aware angular difference `(d + 180) % 360 - 180` for `shoulder_line_angle` and `hip_line_angle`. The X-factor calculation (`shoulder_angle - hip_angle`) also uses this normalization. A user value of -169° vs Tiger's 177° now correctly computes as a 14° difference instead of 346°.

### Recommended Fix Priority

1. ~~**Add minimum delta floor** in `rank_differences()`~~ — Done (MIN_DELTA_DEGREES = 5)
2. **Raise face-on thresholds** — change `None/None` rules to require larger deltas (12-15°)
3. **Add visibility filtering** to angle calculations — skip unreliable landmarks
4. **Rename face-on rotation angles** — update titles/descriptions to match what's actually measured, or remove from top-3 ranking
5. **Left-handed golfer support** — future enhancement
6. ~~**Fix atan2 wraparound**~~ — Done (wraparound-aware deltas in comparison engine + X-factor calculation)

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
