# Analytics Data Dictionary

All events flow through **Segment** SDKs (frontend: `@segment/analytics-next`, backend: `analytics-python`) and are routed to **Amplitude** as a downstream destination configured in the Segment dashboard.

---

## Identity

| Method | SDK | Trigger | Properties |
|--------|-----|---------|------------|
| `identify` | Frontend | User logs in (PropelAuth resolves) | `userId` (PropelAuth user ID), `email` |
| `reset` | Frontend | User logs out | — |

The `AnalyticsIdentifier` client component in `layout.tsx` bridges PropelAuth's `useUser()` hook to Segment's identity graph. It uses a `useRef` guard to avoid re-identifying on every render.

---

## Page Views

| Page Name | Tracked In | Trigger |
|-----------|-----------|---------|
| `Home` | `HeroSection.tsx` | Component mounts |
| `Upload` | `UploadForm.tsx` | Component mounts |
| `Shared Results` | `SharedResultsClient.tsx` | Component mounts (public share page) |

All page views use `analytics.page(pageName, { page_name })`.

---

## Frontend Events

### CTA Clicked

Fired when a user clicks a call-to-action button.

| Property | Type | Description |
|----------|------|-------------|
| `cta_text` | `string` | Button label (e.g., "Get Started", "Analyze Your Swing") |
| `cta_location` | `"hero" \| "header"` | Where the CTA lives |
| `destination` | `string` | URL the CTA navigates to |

**Sources:** `HeroSection.tsx`, `Header.tsx`

---

### Auth Initiated

Fired when a user clicks a sign-in or sign-up link.

| Property | Type | Description |
|----------|------|-------------|
| `auth_type` | `"sign_up" \| "sign_in"` | Which auth flow was initiated |
| `source` | `"header" \| "hero"` | Where the link was clicked |

**Sources:** `HeroSection.tsx`, `Header.tsx`

---

### View Selected

Fired when the user switches camera angle on the upload form.

| Property | Type | Description |
|----------|------|-------------|
| `view` | `"dtl" \| "fo"` | Newly selected view (Down the Line / Face On) |
| `previous_view` | `"dtl" \| "fo"` | Previously selected view |

**Source:** `UploadForm.tsx`

---

### Video Dropped

Fired when a user drops or selects a video file in the upload zone.

| Property | Type | Description |
|----------|------|-------------|
| `file_size_bytes` | `number` | File size in bytes |
| `file_type` | `string` | MIME type (e.g., `video/mp4`) |
| `duration_seconds` | `number \| null` | Video duration if determinable |
| `view` | `"dtl" \| "fo"` | Currently selected camera angle |
| `valid` | `boolean` | Whether the file passed client-side validation |
| `error` | `string` (optional) | Validation error message if `valid` is false |

**Source:** `VideoDropZone.tsx`

---

### Upload Started

Fired when the upload HTTP request begins.

| Property | Type | Description |
|----------|------|-------------|
| `swing_type` | `string` | e.g., `"iron"` |
| `view` | `"dtl" \| "fo"` | Camera angle |
| `file_size_bytes` | `number` | File size in bytes |

**Source:** `UploadForm.tsx`

---

### Upload Completed

Fired when the upload HTTP request succeeds.

| Property | Type | Description |
|----------|------|-------------|
| `swing_type` | `string` | e.g., `"iron"` |
| `view` | `"dtl" \| "fo"` | Camera angle |
| `file_size_bytes` | `number` | File size in bytes |
| `upload_id` | `string` | UUID assigned by the backend |

**Sources:** `UploadForm.tsx` (frontend), `routes/upload.py` (backend — server-side duplicate for reliability)

Backend-only additional properties:
| Property | Type | Description |
|----------|------|-------------|
| `content_type` | `string` | MIME type of the uploaded file |

---

### Upload Failed

Fired when the upload HTTP request fails.

| Property | Type | Description |
|----------|------|-------------|
| `swing_type` | `string` | e.g., `"iron"` |
| `view` | `"dtl" \| "fo"` | Camera angle |
| `error_message` | `string` | Error message from the server or network |

**Source:** `UploadForm.tsx`

---

### Analysis Started

Fired when the analysis HTTP request begins (after upload succeeds).

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `swing_type` | `string` | e.g., `"iron"` |
| `view` | `"dtl" \| "fo"` | Camera angle |

**Source:** `UploadForm.tsx`

---

### Analysis Completed

Fired server-side when the analysis pipeline finishes successfully.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `view` | `string` | Camera angle |
| `swing_type` | `string` | e.g., `"iron"` |
| `processing_time_sec` | `float` | Wall-clock seconds for the pipeline |
| `similarity_score` | `int` | 0–100 similarity percentage vs reference |
| `top_faults` | `list[str]` | Angle names of the top 3 differences |

**Source:** `routes/analysis.py` (backend only)

---

### Analysis Failed

Fired server-side when the analysis pipeline errors.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `view` | `string` | Camera angle |
| `swing_type` | `string` | e.g., `"iron"` |
| `error_code` | `int` | HTTP status code (404, 422, or 500) |
| `error_message` | `string` | Error description |

**Source:** `routes/analysis.py` (backend only)

---

### Results Viewed

Fired when the results dashboard mounts.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `similarity_score` | `number` | 0–100 similarity percentage |
| `swing_type` | `string` | e.g., `"iron"` |
| `view` | `"dtl" \| "fo"` | Camera angle |
| `processing_time_sec` | `number` | Pipeline processing time |

**Source:** `ResultsDashboard.tsx`

---

### Phase Tab Switched

Fired when the user clicks a different swing phase.

| Property | Type | Description |
|----------|------|-------------|
| `phase` | `string` | Newly selected phase (`address`, `top`, `impact`, `follow_through`) |
| `previous_phase` | `string` | Previously active phase |
| `upload_id` | `string` | Upload UUID |

**Source:** `ResultsDashboard.tsx` (via PhaseTimeline and VideoComparison)

---

### Share Button Clicked

Fired when the user clicks the "Share Results" button.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `view` | `"dtl" \| "fo"` | Camera angle |

**Source:** `ResultsDashboard.tsx`

---

### Share Created

Fired server-side when a new share token is created.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `share_token` | `string` | Generated share token |
| `view` | `string` | Camera angle |

**Source:** `routes/share.py` (backend only)

---

### Share Link Copied

Fired when the user copies the share URL to clipboard.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `share_token` | `string` | Share token |

**Source:** `ShareModal.tsx`

---

### Share Image Downloaded

Fired when the user downloads the branded share image.

| Property | Type | Description |
|----------|------|-------------|
| `upload_id` | `string` | Upload UUID |
| `share_token` | `string` | Share token |

**Source:** `ShareModal.tsx`

---

### Social Share Clicked

Fired when the user clicks a social sharing button.

| Property | Type | Description |
|----------|------|-------------|
| `platform` | `"twitter" \| "facebook"` | Social platform |
| `upload_id` | `string` | Upload UUID |
| `share_token` | `string` | Share token |

**Source:** `ShareModal.tsx`

---

### Share Viewed

Fired server-side when someone views a public share link.

| Property | Type | Description |
|----------|------|-------------|
| `share_token` | `string` | Share token |
| `upload_id` | `string` | Upload UUID |
| `view` | `string` | Camera angle |

**Identity:** Anonymous (`anonymous_id = "share_{share_token}"`) — no authenticated user on public pages.

**Source:** `routes/share.py` (backend only)

---

### Analyze Another Clicked

Fired when the user clicks "Analyze Another Swing" from the results page.

| Property | Type | Description |
|----------|------|-------------|
| `from_upload_id` | `string` | Upload UUID of the current results |

**Source:** `ResultsDashboard.tsx`

---

## Environment Variables

| Variable | Location | Required | Description |
|----------|----------|----------|-------------|
| `NEXT_PUBLIC_SEGMENT_WRITE_KEY` | `frontend/.env.local` | No | Segment JavaScript source write key. Analytics no-op when missing. |
| `SEGMENT_WRITE_KEY` | `backend/.env` | No | Segment server-side write key. Analytics no-op when missing. |

---

## Architecture Notes

- **Frontend singleton:** `analytics.ts` lazily initializes `AnalyticsBrowser.load()` on first call. Never runs during SSR. Every component imports typed helper functions — no raw `track()` calls.
- **Backend lazy init:** `analytics.py` reads `SEGMENT_WRITE_KEY` from env on first call. Uses the `analytics-python` library's global client pattern.
- **Graceful degradation:** All functions silently no-op when write keys are missing, so local development works without Segment configured.
- **Shutdown flush:** `main.py` calls `flush_analytics()` during FastAPI lifespan shutdown to ensure queued events are sent before the process exits.
- **Duplicate upload tracking:** "Upload Completed" fires from both frontend and backend for reliability. Deduplicate in Amplitude using `upload_id` if needed.
