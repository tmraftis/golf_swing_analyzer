# Pure — Golf Swing Analyzer

**"Swing pure"**

Compare your golf swing to Tiger Woods' iconic 2000 iron swing using computer vision. Upload down-the-line (DTL) and face-on (FO) videos, and get back angle comparisons, top 3 faults, and drill recommendations — all in under 60 seconds.

**Current status:** Phase 2 complete. Upload videos, get AI-powered swing analysis with coaching feedback. V1 is iron-only; driver support is planned for a future release.

---

## How It Works

1. **Upload two videos** — Down-the-line (DTL) and face-on (FO) angles of your swing
2. **Extract landmarks** — MediaPipe Pose Landmarker (heavy model, 33 landmarks) processes every 2nd frame
3. **Detect phases** — Algorithm auto-detects address, top of backswing, impact, and follow-through from wrist trajectory
4. **Calculate angles** — Golf-specific angles computed at each phase (shoulder turn, hip rotation, spine tilt, X-factor, wrist cock, knee flex, etc.)
5. **Compare to Tiger** — User angles compared against Tiger Woods' 2000 iron reference data using weighted deltas
6. **Get coaching feedback** — Top 3 areas for improvement with severity ratings, descriptions, and practice drills

```
Upload (.mov/.mp4 × 2)
    │
    ▼
POST /api/upload  →  Save files, return upload_id
    │
    ▼
POST /api/analyze/{upload_id}
    │
    ├─ Extract landmarks (DTL + FO)     ~15-25s each
    ├─ Detect swing phases               ~1s
    ├─ Calculate angles                   ~0.5s
    ├─ Load Tiger reference data          cached
    ├─ Compute deltas                     ~0.1s
    └─ Generate coaching feedback         ~0.1s
    │
    ▼
Response: user_angles, reference_angles, deltas,
          top 3 differences with coaching tips
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
│   │   ├── app/
│   │   │   ├── layout.tsx                 # Root layout: Inter font, dark bg
│   │   │   ├── page.tsx                   # Landing page
│   │   │   ├── globals.css                # Tailwind + Pure design tokens
│   │   │   └── upload/
│   │   │       └── page.tsx               # Upload page
│   │   ├── components/
│   │   │   ├── Header.tsx                 # Nav bar: logo, brand name, CTA
│   │   │   ├── Footer.tsx                 # Minimal footer
│   │   │   ├── HeroSection.tsx            # Landing hero: tagline + CTA
│   │   │   ├── FeatureCards.tsx            # 3 value proposition cards
│   │   │   ├── SwingTypeSelector.tsx       # Iron (active) / Driver ("Coming Soon")
│   │   │   ├── VideoDropZone.tsx           # Drag-and-drop upload area
│   │   │   ├── UploadForm.tsx             # Full upload → analyze → results flow
│   │   │   └── Button.tsx                 # Branded button component
│   │   ├── lib/
│   │   │   ├── api.ts                     # API client (upload, analyze, getAnalysis)
│   │   │   ├── validation.ts              # File type, size, duration checks
│   │   │   └── constants.ts               # Brand values, limits, accepted types
│   │   └── types/
│   │       └── index.ts                   # TypeScript interfaces
│   ├── public/
│   │   └── pure-logo.jpeg                 # Logo for frontend
│   ├── .env.local                         # NEXT_PUBLIC_API_URL
│   └── package.json
│
├── backend/                               # FastAPI app (deploys to Railway)
│   ├── main.py                            # App entry, CORS, lifespan, routers
│   ├── app/
│   │   ├── config.py                      # Settings (upload, pipeline, origins)
│   │   ├── routes/
│   │   │   ├── upload.py                  # POST /api/upload
│   │   │   └── analysis.py               # POST /api/analyze, GET /api/analysis
│   │   ├── models/
│   │   │   └── schemas.py                 # Pydantic models (upload + analysis)
│   │   ├── storage/
│   │   │   ├── local.py                   # Save files to local filesystem
│   │   │   └── analysis_store.py          # In-memory analysis result cache
│   │   └── pipeline/                      # Swing analysis pipeline
│   │       ├── __init__.py                # run_analysis() orchestrator
│   │       ├── models.py                  # Pipeline exception hierarchy
│   │       ├── landmark_extractor.py      # MediaPipe pose extraction wrapper
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
- **MediaPipe model** (~30MB, see below)

### 1. Download the MediaPipe model

```bash
curl -o scripts/pose_landmarker_heavy.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
```

### 2. Run the backend

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

The backend will verify the MediaPipe model exists at startup and report its status via `/api/health`.

### 3. Run the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` (already configured for local dev).

### 4. Analyze a swing

1. Go to `http://localhost:3000/upload`
2. Select "Iron" as the swing type
3. Upload a down-the-line (DTL) and face-on (FO) video of your swing
4. Click "Submit for Analysis" — the pipeline takes ~30-50 seconds
5. View your top 3 areas for improvement with coaching tips

---

## Tech Stack

| Layer | Technology | Deploy target |
|-------|-----------|--------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 | Vercel |
| Backend | FastAPI, Python 3.10+ | Railway |
| Pose estimation | MediaPipe Pose Landmarker (heavy, 33 landmarks) | Runs on backend |
| Analysis pipeline | Custom Python (landmark extraction, phase detection, angle math, comparison, feedback) | Backend |
| Storage | Local filesystem (v1), cloud bucket planned | — |
| Auth | Google OAuth (deferred, not yet implemented) | — |

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

### `POST /api/upload`

Upload two swing videos for analysis.

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
    "dtl": { "filename": "...", "size_bytes": 33461107, "content_type": "video/quicktime" },
    "fo": { "filename": "...", "size_bytes": 38934444, "content_type": "video/quicktime" }
  },
  "message": "Videos uploaded successfully. Call POST /api/analyze/{upload_id} to run analysis."
}
```

**Errors:** `400` for invalid swing type or file type.

### `POST /api/analyze/{upload_id}`

Run the full analysis pipeline on previously uploaded videos. Processing takes ~30-50 seconds.

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

### `GET /api/analysis/{upload_id}`

Retrieve a previously computed analysis result from cache.

**Success (200):** Same schema as `POST /api/analyze`.

**Errors:** `404` if not yet analyzed.

---

## Analysis Pipeline

The pipeline runs as a sequence of steps, each with error handling and logging:

| Step | Module | What it does | Time |
|------|--------|-------------|------|
| 1 | `landmark_extractor.py` | MediaPipe pose extraction, every 2nd frame | ~15-25s per video |
| 2 | `phase_detector.py` | Auto-detect address, top, impact, follow-through | ~0.5s |
| 3 | `angle_calculator.py` | Compute golf-specific angles at each phase | ~0.5s |
| 4 | `reference_data.py` | Load Tiger Woods reference (cached with `lru_cache`) | instant |
| 5 | `comparison_engine.py` | Compute deltas, apply weights, rank by significance | ~0.1s |
| 6 | `feedback_engine.py` | Match fault rules, generate coaching text | ~0.1s |

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

18 fault rules map specific angle/phase/view combinations to coaching feedback. Each rule includes:

- **Severity** — major, moderate, or minor
- **Title** — human-readable fault name (e.g., "Flying Right Elbow")
- **Description** — templated text with user/reference values
- **Coaching tip** — actionable drill or practice suggestion

Rules without specific thresholds trigger when `abs(delta) > 8°`. A generic fallback handles angles without dedicated rules.

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
- **Auth deferred** — upload flow built first, Google OAuth to be added later
- **Local filesystem storage for v1** — will move to cloud bucket with 24-hour auto-delete
- **Client-side validation before upload** — reduces backend load and gives instant feedback
- **Tailwind CSS v4 with `@theme` tokens** — design system colors defined as CSS custom properties, no `tailwind.config.ts`
- **`react-dropzone` for file upload UX** — handles drag-and-drop and file selection cleanly
- **`useReducer` for upload form state** — manages the multi-step flow (upload → analyzing → results) without a global store

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Tiger reference data & pipeline validation | Done |
| **1** | Landing page, upload UI, FastAPI backend skeleton | Done |
| **2** | Analysis pipeline, comparison engine, coaching feedback, results UI | Done |
| **3** | Results UI enhancements, side-by-side video player with skeleton overlays, angle table | Not started |
| **4** | Drill content curation, onboarding, polish, QA | Not started |
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

### Phase 3 (next)

- Side-by-side video player with skeleton overlays at key phases
- Detailed angle comparison table
- Visual indicators on the body showing where corrections are needed
- Shareable results page

---

## Performance Targets

| Metric | Target | Actual (Phase 2) |
|--------|--------|------------------|
| End-to-end processing time | <60s | ~50s |
| Landmark detection rate | >70% | Varies by video quality |
| Top differences returned | 3 | 3 |
| System uptime (once deployed) | 99% | — |

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
