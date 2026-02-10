# Pure — Golf Swing Analyzer

**"Swing pure"**

Compare your golf swing to Tiger Woods' iconic 2000 iron swing using computer vision. Upload down-the-line (DTL) and face-on (FO) videos, and get back angle comparisons, top 3 faults, and drill recommendations.

**Current status:** Phase 1 complete. V1 is iron-only; driver support is planned for a future release.

---

## How It Works

1. **Extract landmarks** — MediaPipe Pose Landmarker (heavy, 33 landmarks) processes every frame of a swing video
2. **Detect phases** — Algorithm auto-detects address, top of backswing, impact, and follow-through from wrist trajectory
3. **Calculate angles** — Golf-specific angles computed at each phase (shoulder turn, hip turn, spine tilt, X-factor, wrist cock, knee flex, etc.)
4. **Compare to reference** — User angles are compared against Tiger Woods 2000 iron reference data to produce deltas and coaching feedback

```
Video (.mov/.mp4)
    │
    ▼
extract_landmarks.py  →  33 landmarks/frame (JSON + annotated frames)
    │
    ▼
detect_phases.py      →  4 swing phases auto-detected
    │
    ▼
calculate_angles.py   →  angles at each phase + validation
    │
    ▼
Compare vs reference_data/iron/*.json  →  deltas + top 3 faults
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
│   │   │   ├── UploadForm.tsx             # Orchestrates upload flow + state
│   │   │   └── Button.tsx                 # Branded button component
│   │   ├── lib/
│   │   │   ├── api.ts                     # API client (uploadVideos)
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
│   ├── main.py                            # App entry, CORS, router mount
│   ├── app/
│   │   ├── config.py                      # Settings (upload dir, origins, limits)
│   │   ├── routes/
│   │   │   └── upload.py                  # POST /api/upload endpoint
│   │   ├── models/
│   │   │   └── schemas.py                 # Pydantic response models
│   │   └── storage/
│   │       └── local.py                   # Save files to local filesystem
│   ├── requirements.txt
│   ├── Procfile                           # Railway start command
│   └── .env.example
│
├── scripts/                               # Python processing pipeline
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

### Run the frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### Run the backend

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
# → http://localhost:8000
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `frontend/.env.local` (already configured).

### Run the pose pipeline (scripts)

```bash
pip install mediapipe opencv-python numpy
```

Download the MediaPipe model (~30MB):
```bash
curl -o scripts/pose_landmarker_heavy.task \
  https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
```

---

## Tech Stack

| Layer | Technology | Deploy target |
|-------|-----------|--------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS v4 | Vercel |
| Backend | FastAPI, Python 3.10+ | Railway |
| Pose estimation | MediaPipe Pose Landmarker (heavy) | Pipeline scripts |
| Storage | Local filesystem (Phase 1), cloud bucket planned | — |
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
- **Cardinal Red** — CTA buttons, error states, alerts

Font: **Inter** (Google Fonts)

---

## API Reference

### `GET /api/health`

Health check. Returns `{ "status": "ok", "version": "0.1.0" }`.

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
  "upload_id": "uuid",
  "swing_type": "iron",
  "files": {
    "dtl": { "filename": "...", "size_bytes": 0, "content_type": "video/mp4" },
    "fo": { "filename": "...", "size_bytes": 0, "content_type": "video/mp4" }
  },
  "message": "Videos uploaded successfully. Analysis will be available in Phase 2."
}
```

**Errors:** `400` for invalid swing type or file type.

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

## Pipeline Scripts

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

- **Every frame analyzed** — no keyframe sampling, maximizes fidelity for short (<30s) swing clips
- **View-specific calculations** — some angles are only meaningful from one camera angle (e.g., X-factor from FO, spine angle from DTL)
- **`swing_type` field in all data** — enables future expansion to driver, fairway woods, etc. without schema changes
- **Reference data organized by club** — `reference_data/iron/`, with `reference_data/driver/` reserved
- **Right-handed golfer assumed** — lead arm = left, trail arm = right
- **Frontend and backend independently deployable** — Next.js on Vercel, FastAPI on Railway
- **Auth deferred** — upload flow built first, Google OAuth to be added later
- **Local filesystem storage for Phase 1** — will move to cloud bucket with 24-hour auto-delete
- **Client-side validation before upload** — reduces backend load and gives instant feedback
- **Tailwind CSS v4 with `@theme` tokens** — design system colors defined as CSS custom properties, no `tailwind.config.ts`
- **`react-dropzone` for file upload UX** — handles drag-and-drop and file selection cleanly
- **`useReducer` for upload form state** — manages the multi-step upload flow (swing type + two files + submission) without a global store

---

## Roadmap

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Tiger reference data & pipeline validation | Done |
| **1** | Landing page, upload UI, FastAPI backend skeleton | Done |
| **2** | Pose estimation API, phase auto-detection, comparison engine, feedback rules | Not started |
| **3** | Results UI, side-by-side video player with skeleton overlays, angle table | Not started |
| **4** | Drill content curation, onboarding, polish, QA | Not started |
| **5+** | Driver swing support, additional clubs, more pro references | Future |

### Phase 1 deliverables (completed)

- Next.js 16 frontend with Tailwind CSS v4 and Pure design system
- Landing page: header, hero section ("Swing pure"), 3 feature cards, footer
- Upload page: swing type selector (Iron active, Driver "Coming Soon"), dual drag-and-drop video upload, client-side validation, submit flow
- FastAPI backend with `POST /api/upload` (accepts swing_type + two videos, saves to local filesystem)
- `GET /api/health` endpoint
- CORS configured for local development
- Responsive design (mobile → desktop)

### Phase 2 (next)

- Integrate MediaPipe pipeline into FastAPI (`POST /api/analyze-swing`)
- Auto-detect swing phases from uploaded videos
- Compare user angles to Tiger reference data
- Return top 3 differences with coaching feedback
- Target: <60 seconds processing time

---

## Performance Targets

- Processing time: **<60 seconds** for both videos combined
- Landmark detection rate: **>90%** of frames
- System uptime: **99%** (once deployed)

---

## Contributing

1. Clone the repo
2. Set up the Python environment (see [Quick Start](#quick-start))
3. Download the MediaPipe model into `scripts/`
4. Run `npm install` in `frontend/` and `pip install -r requirements.txt` in `backend/`

When adding a new swing type (e.g., driver):
1. Source high-quality DTL and FO reference videos
2. Process through `extract_landmarks.py`
3. Identify phase frames and run `calculate_angles.py`
4. Use `build_reference_json.py` as a template to generate `reference_data/<swing_type>/` files
5. Ensure all reference JSON includes `"swing_type": "<type>"` in every phase entry
