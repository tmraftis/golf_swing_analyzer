# Golf Swing Analyzer

Compare your golf swing to Tiger Woods' iconic 2000 iron swing using computer vision pose estimation. Upload down-the-line (DTL) and face-on (FO) videos, and get back angle comparisons, top 3 faults, and drill recommendations.

**Current status:** Phase 0 complete (pipeline validated). V1 is iron-only; driver support is planned for a future release.

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
├── .gitignore
├── Golf Swing PRD Anlayzer v4.md       # Full product requirements document
│
├── scripts/                            # Python processing pipeline
│   ├── extract_landmarks.py            # MediaPipe pose extraction from video
│   ├── calculate_angles.py             # Golf angle calculations at each phase
│   ├── detect_phases.py                # Auto-detect swing phases from landmarks
│   ├── build_reference_json.py         # Generate Tiger reference data files
│   └── pose_landmarker_heavy.task      # MediaPipe model binary (not in git)
│
├── reference_data/                     # Pre-computed reference swings
│   └── iron/                           # Tiger Woods 2000 iron
│       ├── tiger_2000_iron_dtl_reference.json
│       └── tiger_2000_iron_face_on_reference.json
│
├── output/                             # Tiger's processed data (not in git)
│   ├── dtl_landmarks.json
│   ├── fo_landmarks.json
│   ├── dtl_phases.json
│   ├── fo_phases.json
│   ├── angle_analysis.json
│   ├── dtl_frames/                     # Annotated frame images
│   └── fo_frames/
│
└── output_user/                        # User test analysis (not in git)
    ├── *_landmarks.json
    ├── *_phases.json
    ├── *_angle_analysis.json
    └── *_frames/
```

---

## Prerequisites

- **Python 3.10+**
- **MediaPipe model:** Download `pose_landmarker_heavy.task` (~30MB) into `scripts/`:
  ```
  curl -o scripts/pose_landmarker_heavy.task \
    https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/latest/pose_landmarker_heavy.task
  ```

### Install dependencies

```bash
pip install mediapipe opencv-python numpy
```

Or with a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install mediapipe opencv-python numpy
```

---

## Usage

### 1. Extract landmarks from a video

```bash
python scripts/extract_landmarks.py
```

> **Note:** Currently reads video paths hardcoded in `main()`. To process your own videos, update the `videos` dict in `extract_landmarks.py:249-252` to point to your `.mov` or `.mp4` files.

**Outputs:** `output/<label>_landmarks.json` and annotated frame images in `output/<label>_frames/`.

### 2. Detect swing phases

```bash
python scripts/detect_phases.py <landmarks.json> --view dtl|fo
```

Example:
```bash
python scripts/detect_phases.py output/dtl_landmarks.json --view dtl
python scripts/detect_phases.py output_user/tim_dtl_trim_landmarks.json --view dtl
```

Optional tuning parameters:
- `--smoothing-window N` — Rolling average window size (default: 5)
- `--velocity-window N` — Velocity computation window (default: 10)
- `--still-threshold F` — Max velocity for "still" classification (default: 0.001)

**Output:** `<input_basename>_phases.json`

### 3. Calculate angles

```bash
python scripts/calculate_angles.py
```

With auto-detected phases (instead of hardcoded Tiger frames):
```bash
python scripts/calculate_angles.py --auto-detect
```

Custom input/output paths:
```bash
python scripts/calculate_angles.py \
  --dtl output_user/tim_dtl_trim_landmarks.json \
  --fo output_user/tim_fo_landmarks.json \
  --output output_user/tim_angle_analysis.json \
  --auto-detect
```

**Output:** `output/angle_analysis.json` — angles at each phase for both views, plus validation results.

### 4. Build reference data (one-time)

Only needed if re-processing Tiger's source videos:
```bash
python scripts/build_reference_json.py
```

Reads from `output/dtl_landmarks.json` and `output/fo_landmarks.json`, writes to `reference_data/iron/`.

---

## Reference Data

The `reference_data/iron/` directory contains pre-computed Tiger Woods 2000 iron swing data used for comparison. Each file includes:

- **Metadata:** golfer, year, swing type, video specs, detection rate, pose model
- **Per-phase data** (address, top, impact, follow-through):
  - Frame number and timestamp
  - Computed angles
  - Key landmark positions (normalized 0-1 coordinates)

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

## Phase Detection Algorithm

The auto-detection in `detect_phases.py` works by tracking the right wrist Y-position:

1. **Smooth** the raw signal with a rolling average to remove jitter
2. **Find top of backswing** — first significant local minimum of hand Y (hands highest) followed by a velocity spike (downswing)
3. **Find address** — last period of stillness before takeaway where hands are low (near ball level)
4. **Find impact** — first frame after top where hand Y returns to near address level
5. **Find follow-through** — first local minimum of hand Y after impact (hands rise again to finish)

The algorithm handles videos with pre-shot routines, waggles, and variable start positions.

---

## Architecture Decisions

- **Every frame analyzed** — no keyframe sampling, maximizes fidelity for short (<30s) swing clips
- **View-specific calculations** — some angles are only meaningful from one camera angle (e.g., X-factor from FO, spine angle from DTL)
- **`swing_type` field in all data** — enables future expansion to driver, fairway woods, etc. without schema changes
- **Reference data organized by club** — `reference_data/iron/`, with `reference_data/driver/` reserved for future use
- **Right-handed golfer assumed** — lead arm = left, trail arm = right

---

## Validation

`calculate_angles.py` includes a validation step that checks computed angles against golf instruction norms:

| Check | Expected range |
|-------|---------------|
| DTL address spine angle | 20-50 |
| DTL address knee flex | 130-175 |
| DTL spine angle maintained (top/impact vs address) | within 15 |
| DTL top right elbow | 70-110 (folded) |
| FO top shoulder line change | >5 from address |
| FO top X-factor | non-zero |
| FO address knee flex (both) | 130-175 |

All checks passed on Tiger's reference data.

---

## Roadmap

The full PRD is in `Golf Swing PRD Anlayzer v4.md`. Summary of remaining phases:

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Tiger reference data & pipeline validation | Done |
| **1** | Auth (Google OAuth), upload UI, FastAPI backend skeleton | Not started |
| **2** | Pose estimation API, phase auto-detection, comparison engine, feedback rules | Not started |
| **3** | Results UI, side-by-side video player with skeleton overlays, angle table | Not started |
| **4** | Drill content curation, onboarding, polish, QA | Not started |
| **5+** | Driver swing support, additional clubs, more pro references | Future |

### Planned tech stack (Phases 1+)
- **Frontend:** React / Next.js
- **Backend:** FastAPI
- **Auth:** Google OAuth
- **Storage:** Temporary cloud bucket (24-hour auto-delete for uploaded videos)

---

## Performance Targets

- Processing time: **<60 seconds** for both videos combined
- Landmark detection rate: **>90%** of frames
- System uptime: **99%** (once deployed)

---

## Contributing

1. Clone the repo
2. Set up the Python environment (see [Prerequisites](#prerequisites))
3. Download the MediaPipe model into `scripts/`
4. Run the pipeline on your own swing video to verify everything works end-to-end

When adding a new swing type (e.g., driver):
1. Source high-quality DTL and FO reference videos
2. Process through `extract_landmarks.py`
3. Identify phase frames and run `calculate_angles.py`
4. Use `build_reference_json.py` as a template to generate `reference_data/<swing_type>/` files
5. Ensure all reference JSON includes `"swing_type": "<type>"` in every phase entry
