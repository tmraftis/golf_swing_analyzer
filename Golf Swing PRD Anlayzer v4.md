# Golf Swing Analyzer App - PRD

### TL;DR

Golf Swing Analyzer is a web app for amateur golfers to upload their own swing videos (both down-the-line and face-on), select their swing type (iron or driver), and instantly compare their mechanics to Tiger Woods’ iconic 2000 swing with the corresponding club. The app overlays pose skeletons, presents clear angle deltas, and delivers the top 3 actionable improvement tips plus curated drill recommendations—making high-level golf coaching accessible to everyone. **V1 launches with iron swing support only. Driver analysis is coming in a future release; users can select which type of swing they're uploading, but only iron is enabled for analysis in V1.**

---

## Goals

### Business Goals

* Achieve 1000+ new user signups within the first 3 months.

* Reach a 60% or higher video upload completion rate among registered users.

* Maintain at least a 30% weekly active user retention rate one month post-launch.

* Establish Golf Swing Analyzer as the #1 destination for Tiger Woods swing comparison within 8 weeks.

* Collect baseline user satisfaction data via in-app feedback for future product refinement.

### User Goals

* Identify and visualize the top 3 differences between their swing and Tiger Woods’ 2000 swing for a selected club type.

* Gain simple, actionable feedback and improvement drills tailored to their primary swing faults.

* Easily access side-by-side video comparisons for immediate, visual self-coaching.

* Experience fast, seamless onboarding and feedback with minimal technical obstacles.

* Build confidence in their practice sessions thanks to personalized, pro-level guidance.

### Non-Goals

* Support for comparisons to any professional golfer other than Tiger Woods (2000) in v1.

* Handling non-iPhone video formats or videos exceeding 30 seconds.

* Offering personalized, real-time coaching or AI-generated voice feedback within v1.

* **Driver swing analysis, fairway woods, hybrids, wedges, and putting are out of scope for v1. Only iron swing analysis will be supported at launch; others to follow in future updates.**

---

## User Stories

**Persona A: Amateur Golfer ("Weekend Warrior")**

* As an amateur golfer, I want to **select whether I’m uploading an iron or driver swing** so that I’m compared to the appropriate Tiger Woods reference swing.

* As an amateur golfer, I want to upload two videos (down-the-line and face-on) of my swing so that the app can analyze my technique accurately.

* As an amateur golfer, I want to directly compare my swing side-by-side to the Tiger Woods 2000 swing with the same club type so that I can visualize my biggest differences.

* As an amateur golfer, I want to see the three most significant aspects of my swing that differ from Tiger so that I know what to focus my practice on.

* As an amateur golfer, I want the app to suggest links to drills for my top faults so that I can work to improve efficiently.

**Persona B: Returning User/Practicing Golfer**

* As a returning user, I want to view my previous swing analyses so that I can track my improvement over time.

**Persona C: Curious New User**

* As a new user, I want a simple Google sign-up process so that I can get started quickly without creating another account.

---

## Functional Requirements

* **Authentication & Onboarding** (Priority: High)

  * *Google OAuth Login*: Users must sign in with Google before accessing swing analysis features.

  * *Onboarding Flow*: Brief tutorial pop-up on first login, highlighting video requirements and process.

* **Video Upload & Validation** (Priority: High)

  * *Swing Type Selection*: **Before upload, user selects swing type (Iron enabled for v1, Driver disabled with "Coming Soon" indicator).**

  * *Dual Video Upload*: Require both down-the-line and face-on swing videos.

  * *Format & Duration Validations*: Accept only iPhone-native file types (e.g., .mov, .mp4), max 30-second clips each.

  * *Upload Error Handling*: Clear user feedback if format, angle, or length requirements aren’t met.

* **Pose Estimation & Processing** (Priority: High)

  * *MediaPipe Pose Pipeline*: Backend model extracts 2D body landmarks from each submitted video.

  * *Frame Sampling*: Analyze key frames throughout each swing to cover address, top, impact, and follow-through.

* **Comparison & Analysis** (Priority: High)

  * *Reference Data Storage*: **Preprocessed Tiger 2000 swing phase/angle JSON is stored and organized by swing type:** `/reference_data/iron/`, with `/reference_data/driver/` planned for the future.

  * *Swing Type Matching*: **Backend loads the appropriate Tiger reference data set (currently iron only) based on user’s swing type selection.**

  * *Angle Calculation*: Compute and compare shoulder turn, hip turn, spine tilt, arm-torso angle, and wrist cock at 4 swing checkpoints.

  * *Textual Feedback*: Rule-based logic generates top 3 difference summaries and assigns feedback categories.

* **Results & Recommendations** (Priority: High)

  * *Side-by-Side Player*: Synchronized playback of user and Tiger’s swing videos with pose skeleton overlays.

  * *Angle Table*: Table of user vs. Tiger angles at each phase, with color-coding for deviation severity.

  * *Drill Linking*: Surface 2–3 curated drill links per identified difference/fault.

---

## User Experience

**Entry Point & First-Time User Experience**

* Users land on a visually appealing landing page introducing the app’s value.

* Clicking “Sign Up with Google” launches OAuth; successful login routes to an upload dashboard.

* For first-time users, a brief step-by-step guide pop-up (with icons or screenshots) details:

  * Required video angles (down-the-line and face-on), format, and maximum length.

  * Tips for filming the swing correctly.

**Core Experience**

* **Step 1: Swing Type Selection**

  * The user is prompted to select their swing type: Iron (active) or Driver (disabled, "Coming Soon").

  * Tooltip: “Iron and driver swings have different mechanics; we’ll compare you to Tiger’s swing with the same club type.”

* **Step 2: Dual Video Upload**

  * Users upload down-the-line and face-on videos separately (with drag-and-drop or file selector).

  * Instant validation of file type and length; clear error messages for noncompliance.

  * On success, “Submit for Analysis” button is enabled.

* **Step 3: Backend Processing**

  * Status indicator shows real-time progress as swings are analyzed (pose extraction, angle computation).

  * Processing takes < 1 minute; progress feedback provided to prevent user drop-off.

* **Step 4: Side-by-Side Comparison View**

  * On completion, user is navigated to a results dashboard.

  * Videos of the user and Tiger 2000 are displayed side-by-side (with the matching swing type), with skeleton overlays on both.

  * Timeline or slider allows users to scrub through major swing phases (address, top, impact, follow-through).

* **Step 5: Presentation of Results**

  * **Header displays swing type:** e.g., “Your Iron Swing vs Tiger Woods 2000 Iron.”

  * Below the video player, a table details angles at key checkpoints for both user and Tiger, highlighting significant deviations.

  * A highlighted “Top 3 Differences” card summarizes coached feedback with supporting graphics/icons (e.g., “Shoulder turn: -18° vs Tiger at Backswing Top”).

  * Each identified fault comes with a set of clickable links to relevant, pre-curated drill videos or articles.

* **Step 6: Next Steps**

  * Optional: Button for the user to save session, revisit past analyses, or start again with new videos.

**Advanced Features & Edge Cases**

* Responsive layout for easy use on mobile, tablet, or desktop.

* Graceful error handling if background processing fails (e.g., fallback message, retry prompt).

* For users uploading duplicate or corrupted files, prompt for re-upload with clear guidance.

**UI/UX Highlights**

* High color contrast and clear typography for maximum legibility on the results page.

* Focus on accessibility: tab navigation, screen-reader compatibility, and descriptive alt text for all visuals.

* Progress indicators and feedback on all multi-step actions to minimize user confusion and drop-off.

* Videos and overlays are synchronized and responsive, ensuring a cohesive visual experience.

* Tooltips or info icons explain golf terms or phases for novices.

---

## Narrative

Michael, a 34-year-old weekend golfer, often films his swing to improve but struggles to identify what actually needs work. He hears about Golf Swing Analyzer, signs in quickly with Google, and **selects “Iron” as his swing type** (he notices “Driver” is marked as coming soon). He’s prompted to upload both a down-the-line and a face-on clip of his 7-iron swing from his iPhone—both under 30 seconds, just as required. Within a minute, the app processes his swings and puts them side-by-side with Tiger Woods’ 2000 iron swing, pose skeletons overlaid for clarity.

Michael sees a table showing that his shoulder turn at the top is 22° less than Tiger’s, his hips don’t rotate enough at impact, and he’s losing spine angle in the follow-through. The app distills this to “Top 3 Differences” with plain language and attaches three high-quality YouTube drill links for each fault. Motivated by this focused insight, Michael saves the session, heads to the range with the recommended drills, and returns weekly to track his improvement. For the business, Michael’s engagement and success story drive further word-of-mouth, fueling organic growth and engagement.

---

## Success Metrics

### User-Centric Metrics

* **Signup Conversion Rate:** % of landing page visitors who sign up via Google OAuth.

* **Swing Type Selection:** Track rate of iron vs. attempted driver selection.

* **Video Upload Completion:** % of signed-in users who successfully upload both required swing videos.

* **Results Engagement:** % of users who spend >1 minute on the results page or interact with drill links.

* **User Satisfaction:** Average session rating collected post-analysis via a single-click feedback prompt.

### Business Metrics

* **Weekly Active Users (WAU):** Number of unique users interacting with the app per week.

* **User Retention:** % of users returning to analyze a new swing within 30 days.

* **Session Growth:** Month-over-month increase in completed analyses.

### Technical Metrics

* **Pose Estimation Accuracy:** % of swings where pose skeleton is properly overlayed (automated error logging).

* **Video Processing Speed:** Median time from upload to results page (<60 seconds target).

* **System Uptime:** 99% or higher service availability.

### Tracking Plan

* Google OAuth sign-ins

* **Swing type selection tracking (iron vs driver attempt)**

* Successful/failed video uploads (both views)

* Analysis start/completion events by swing type

* Drill link clicks per feedback/fault type

* Feedback/rating prompt submissions

---

## Technical Validation Checklist

This checklist must be completed before building any UI or user-facing features. The pose estimation pipeline and Tiger reference data are the critical path—without these working correctly, the entire product fails.

### Phase 0: Tiger Reference Data Preparation (Complete First)

* Find and download down-the-line and face-on footage of iron shots from tournaments (preferably mid-iron like 6- or 7-iron).

* Verify clear body visibility throughout entire swing, minimal camera movement, good lighting.

* Save as `tiger_2000_iron_dtl_source.mp4` and `tiger_2000_iron_face_on_source.mp4`.

* **Note: Driver swing videos can be sourced later (Phase 5+) for expanded swing type support.**


* Set up Python environment with MediaPipe Pose installed.

* Create script that processes video frame-by-frame and extracts all 33 body landmarks.

* Output raw landmark coordinates to CSV or JSON for inspection.


* Inspect processed frames visually (or use a simple viewer script).

* Manually note frame numbers for: Address, Top of Backswing, Impact, Follow-Through.

* Document the visual criteria used (e.g., "Impact = frame where club is lowest and nearest to ball position").


* Compute shoulder turn, hip turn, spine tilt, lead arm-torso angle, wrist cock, knee flex at each phase.

* Print angle values and sanity-check against golf instruction norms.

  * Top of backswing: shoulder turn \~90-110°, hip turn \~45-50°

  * Impact: hip rotation \~40-45° open, spine tilt maintained from address

* If angles seem off, debug landmark detection or angle calculation formulas.


* Structure: `{ "swing_type": "iron", "phase": "top", "frame": 45, "shoulder_turn": 105.3, "hip_turn": 47.8, ... }`

* **Include a** `"swing_type"` **field in every reference object.**

* Create `tiger_2000_iron_dtl_reference.json` and `tiger_2000_iron_face_on_reference.json`.

* **Organize reference data files in** `/reference_data/iron/`**. Reserve** `/reference_data/driver/` **for future swing types.**

### Phase 0.5: Pipeline Validation (Complete Before Building Upload UI)

* Record 3–5 test swings on iPhone (down-the-line and face-on).

* Run through same MediaPipe pipeline.

* Verify landmarks are detected consistently, especially at impact (watch for motion blur issues).


* Compute angles for test swings at the 4 key phases.

* Manually inspect: Do the numbers make sense? (e.g., shoulder turn should be positive, hip turn less than shoulder).

* If landmarks are jittery or missing, consider frame sampling strategy or confidence thresholds.


* Compare test swing angles to Tiger iron reference data.

* Calculate deltas (user_angle - tiger_angle).

* Verify feedback rules trigger correctly (e.g., "shoulder turn 20° less" produces expected fault message).


* Time full pipeline from video input to results output.

* Target: <60 seconds for both videos combined.

* If too slow, optimize frame sampling rate or consider async processing.

### Go/No-Go Decision Point

Only proceed to Phase 1 (building auth and upload UI) if:

* Tiger iron reference data angles match expected golf instruction values.

* Test swings produce consistent landmark detection (>90% of frames usable).

* Angle deltas between test swings and Tiger are interpretable and produce sensible feedback.

* Processing completes within 60 seconds per analysis.

If any of these fail, debug the pose estimation pipeline before writing any user-facing code.

---

## Technical Considerations

### Technical Needs

* **Frontend:** SPA using React/Next.js for seamless upload, playback, and results presentation.

* **Backend:** FastAPI service handling authentication integration, receiving video uploads (including swing_type parameter), triggering MediaPipe Pose estimation, performing angle calculations, and returning results.

* **Tiger Reference Data:** Static JSON containing processed angles and landmarks from a reference Tiger Woods 2000 swing (identified swing phases), **organized by swing_type.**

* **Comparison Engine:** Logic to compare user vs. Tiger angles, generate deltas, and interpret these into coaching feedback, loading appropriate reference JSON by swing type.

### Integration Points

* **Google OAuth:** Secure authentication and basic profile retrieval.

* **YouTube (Optional):** Embedded Tiger Woods swing for comparison.

* Drill resource links (curated, not generated in-app for v1).

### Data Storage & Privacy

* **Video Storage:** Temporary, private storage of user-uploaded videos and pose extraction data; automatic deletion after analysis or within 24 hours.

* **User Data:** Minimal—OAuth ID, session metadata, swing_type, and aggregate swing metrics only.

* **Compliance:** Adhere to applicable privacy regulations (e.g., GDPR), especially around video uploads and storage.

### Scalability & Performance

* Expectation of initial user base (100-1000 DAU); backend must process concurrent analyses without timeouts.

* Frontend designed to be responsive and lightweight for fast loading and playback.

### Potential Challenges

* Handling iPhone high-resolution files efficiently without long load times.

* Ensuring pose estimation quality in suboptimal home-recorded video.

* Prioritizing fast video processing and clear user feedback on failures.

* **Ensuring future driver and other club support can be added modularly without major data or UI refactoring.**

---

## Milestones & Sequencing

### Project Estimate

* **Medium:** 3–4 weeks

### Team Size & Composition

* **Small Team:** 2–3 multipurpose members (Full-stack Engineer, Product Designer/PM, part-time content/drill curator).

### Suggested Phases

**Phase 0: Tiger Reference Data & Pipeline Validation (Days 1–3)**

* **Key Deliverables:**

  * Engineer: Source and download Tiger 2000 iron swing videos (down-the-line and face-on)

  * Engineer: Build preprocessing script with MediaPipe Pose to extract landmarks frame-by-frame

  * Engineer: Manually identify and document frame numbers for 4 swing phases (address, top, impact, follow-through)

  * Engineer: Calculate angles (shoulder turn, hip turn, spine tilt, arm-torso, wrist cock, knee flex) for each phase

  * Engineer: Validate angles against golf instruction norms and sanity-check values

  * Engineer: Save validated reference data as `tiger_2000_iron_dtl_reference.json` and `tiger_2000_iron_face_on_reference.json` with `"swing_type"` field, organized under `/reference_data/iron/`

  * Engineer: Test pipeline on 3–5 amateur test swings to verify landmark detection quality and angle calculation accuracy

* **Dependencies:** Python environment with MediaPipe installed, high-quality Tiger 2000 iron source videos

* **Success Criteria:** Tiger angles match expected values, test swings produce consistent landmarks (>90% frame success rate), processing completes in <60 seconds

* **Go/No-Go Gate:** Do not proceed to Phase 1 until validation checklist is complete and passing

**Phase 1: Core Auth & Upload Infrastructure (Days 4–7)**

* **Key Deliverables:**

  * Engineer: Set up Next.js/React frontend with landing page

  * Engineer: Implement Google OAuth login flow and session management

  * Engineer: Build dual video upload UI with drag-and-drop or file selector

  * **Engineer: Add swing type selection UI (Iron enabled for v1, Driver present but disabled with “Coming Soon”)**

  * Engineer: Add client-side validation for file type (.mov, .mp4), duration (max 30s), and both angles required

  * Engineer: Display clear error messages for validation failures

  * Engineer: Set up FastAPI backend skeleton with video upload endpoint (**accepts swing_type parameter, but only “iron” analysis processed in v1**)

  * Engineer: Configure temporary video storage (local or cloud bucket with 24-hour auto-delete)

* **Dependencies:** Google OAuth credentials, hosting/deployment environment, Phase 0 complete

* **Success Criteria:** User can sign in with Google, select swing type (iron only active), and upload two videos that pass validation

**Phase 2: Pose Estimation & Angle Comparison Backend (Days 8–14)**

* **Key Deliverables:**

  * Engineer: Build FastAPI endpoint `/analyze-swing` that accepts two video files **and swing_type param**

  * Engineer: Integrate MediaPipe Pose processing pipeline from Phase 0 into API

  * Engineer: Implement frame sampling logic (every 2–3 frames) for performance

  * Engineer: Build auto-detection heuristics to identify 4 swing phases from user videos

  * Engineer: Calculate user angles at each phase using same formulas validated in Phase 0

  * **Engineer: Load Tiger reference JSON using swing_type param (currently only iron enabled)**

  * Engineer: Implement rule-based feedback engine that maps deltas to fault categories and coaching text (iron-specific rules for v1)

  * Engineer: Return JSON response with swing_type, angles, deltas, top 3 differences, and fault tags

* **Dependencies:** Phase 0 reference data, Phase 1 upload infrastructure, MediaPipe Python environment

* **Success Criteria:** API returns accurate angle comparisons and sensible top 3 feedback for test iron swings in <60 seconds

**Phase 3: Results UI & Side-by-Side Comparison (Days 15–21)**

* **Key Deliverables:**

  * Engineer: Build results dashboard page that receives API response

  * **Engineer: Display header with swing type (e.g., “Your Iron Swing vs Tiger Woods 2000 Iron”)**

  * Engineer: Implement side-by-side video player for user and Tiger swings with synchronized playback

  * **Engineer: Display Tiger iron swing for v1 (driver support added later)**

  * Engineer: Add HTML5 canvas overlay to draw pose skeletons on both videos using landmark coordinates

  * Engineer: Create timeline scrubber to navigate to each swing phase (address, top, impact, follow-through)

  * Engineer/Designer: Design and build angle comparison table showing user vs Tiger at each phase

  * Engineer/Designer: Create "Top 3 Differences" card with color-coded severity indicators

  * Designer: Polish visual design, typography, and responsive layout

  * **Engineer: Pass swing_type param from frontend to backend and carry through entire flow**

  * Engineer: Wire up frontend to backend API and handle loading states

* **Dependencies:** Phase 2 backend API complete, Tiger reference video files for playback, sample analysis data

* **Success Criteria:** User can view side-by-side comparison with skeleton overlays, scrub through phases, see top 3 differences clearly, and confirm analysis type is “iron”

**Phase 4: Drill Content & Final Polish (Days 18–24, overlaps Phase 3)**

* **Key Deliverables:**

  * Content Curator: Research and curate 3–5 high-quality drill videos/articles for each identified iron swing fault category

  * Content Curator: Create `drills.json` mapping fault tags to drill URLs, titles, and descriptions

  * Engineer: Integrate drill recommendations into results page based on fault tags from API

  * Engineer: Add drill link tracking to analytics

  * Designer: Add onboarding tutorial pop-up for first-time users explaining video requirements

  * Designer: Implement tooltips for golf terminology and phase names

  * Engineer: Add simple feedback prompt ("Was this helpful?") on results page

  * Engineer/Designer: QA end-to-end flow on multiple devices and browsers

  * Engineer: Performance optimization and error handling polish

* **Dependencies:** Phase 3 UI complete, finalized fault categories from Phase 2

* **Success Criteria:** Drill links display correctly for each identified fault, onboarding flow guides new users, end-to-end flow tested and working

---

**Future work:**

* **Phase 5+:** Source and preprocess Tiger 2000 driver swing videos; implement driver reference JSON; extend backend and UI to enable driver workflow.

* Extend to additional swing types (fairway woods, hybrids, wedges, putter), more pro references, or AI-generated coaching as needed.

---