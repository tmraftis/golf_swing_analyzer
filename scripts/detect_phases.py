"""
Phase 2: Auto-detect golf swing phases from extracted landmark data.

Identifies the 4 key swing phases from any user video:
  - Address (setup position)
  - Top of backswing (hands at highest point)
  - Impact (club at ball)
  - Follow-through (full extension post-impact)

Algorithm works backwards from the top of backswing (most reliable signal),
then finds address before it, impact after it, and follow-through after impact.

Handles videos that don't start at address (pre-shot routines, waggle, etc.).

Usage:
    python detect_phases.py <landmarks.json> [--view dtl|fo] [--output path]
"""

import argparse
import json
import math
import os
import sys
import numpy as np


# ─── Default algorithm parameters ───

DEFAULT_PARAMS = {
    "smoothing_window": 5,              # frames for rolling average smoothing
    "velocity_window": 10,              # frames for rolling velocity computation
    "still_threshold": 0.001,           # max rolling velocity to consider "still"
    "min_still_duration": 5,            # minimum consecutive still frames for address
    "top_prominence_threshold": 0.05,   # min Y drop from address level to qualify as "top"
    "impact_search_window_sec": 2.0,    # seconds after top to search for impact
    "followthrough_search_window_sec": 3.0,  # seconds after impact to search for follow-through
    "downswing_validation_frames": 20,  # frames after top to check for velocity spike
    "primary_hand": "right_wrist",      # primary landmark for detection
    "fallback_hand": "left_wrist",      # fallback if primary has low visibility
    "min_visibility": 0.4,              # minimum acceptable avg visibility
}


# ─── Signal extraction ───

def extract_hand_signal(frames, landmark_name, min_visibility=0.4):
    """
    Extract Y-position and visibility arrays for a landmark across all frames.

    Frames with visibility below min_visibility are treated as undetected
    (y=NaN) to prevent low-confidence tracking artifacts from corrupting
    the signal — especially common at video start/end and during fast motion.

    Returns:
        (y_array, visibility_array): 1D numpy arrays of length len(frames).
        Frames with no detection or low visibility get y=NaN and visibility=0.
    """
    n = len(frames)
    y_arr = np.full(n, np.nan)
    vis_arr = np.zeros(n)

    for i, f in enumerate(frames):
        if f["detected"] and landmark_name in f["landmarks"]:
            lm = f["landmarks"][landmark_name]
            if lm["visibility"] >= min_visibility:
                y_arr[i] = lm["y"]
                vis_arr[i] = lm["visibility"]

    return y_arr, vis_arr


def smooth_signal(signal, window=5):
    """
    Apply rolling average smoothing using np.convolve.
    Interpolates through NaN gaps before smoothing.
    Pads edges to avoid boundary artifacts.
    """
    nan_mask = np.isnan(signal)
    if nan_mask.all():
        return signal.copy()

    # Interpolate NaN gaps
    if nan_mask.any():
        indices = np.arange(len(signal))
        valid = ~nan_mask
        signal_interp = np.interp(indices, indices[valid], signal[valid])
    else:
        signal_interp = signal.copy()

    # Pad edges with reflected values to avoid boundary artifacts
    pad = window // 2
    padded = np.pad(signal_interp, pad, mode="edge")
    kernel = np.ones(window) / window
    smoothed = np.convolve(padded, kernel, mode="same")
    # Remove padding
    return smoothed[pad:pad + len(signal)]


def compute_velocity(signal, window=10):
    """
    Compute rolling mean of absolute frame-to-frame Y changes.
    Returns array of same length as signal (first element is 0).
    """
    frame_diff = np.abs(np.diff(signal))
    kernel = np.ones(window) / window
    rolling_vel = np.convolve(frame_diff, kernel, mode="same")
    return np.concatenate([[0.0], rolling_vel])


def select_primary_landmark(frames, params):
    """
    Choose the best landmark for phase detection based on average visibility.
    Returns the landmark name string.
    """
    primary = params["primary_hand"]
    fallback = params["fallback_hand"]
    min_vis = params["min_visibility"]

    def avg_vis(name):
        visibilities = []
        for f in frames:
            if f["detected"] and name in f["landmarks"]:
                visibilities.append(f["landmarks"][name]["visibility"])
        return np.mean(visibilities) if visibilities else 0.0

    primary_vis = avg_vis(primary)
    fallback_vis = avg_vis(fallback)

    if primary_vis >= min_vis:
        return primary
    elif fallback_vis >= min_vis:
        print(f"  NOTE: {primary} avg visibility too low ({primary_vis:.2f}), using {fallback} ({fallback_vis:.2f})")
        return fallback
    else:
        # Use whichever is higher
        chosen = primary if primary_vis >= fallback_vis else fallback
        print(f"  WARNING: Both landmarks have low visibility ({primary}: {primary_vis:.2f}, {fallback}: {fallback_vis:.2f})")
        print(f"  Using {chosen} (best available)")
        return chosen


# ─── Phase detection functions ───

def _has_preceding_address(local_min_idx, velocity, y_smooth, rough_address_y, fps, params):
    """
    Check whether there's a still period (address) with hands low within
    5 seconds before a candidate top-of-backswing frame.

    The real top of backswing is always preceded by the address position:
    the golfer standing still with hands near the ball (high Y). Post-swing
    Y minima (follow-through peak, walking away) are NOT preceded by a
    still period — they're preceded by active swing motion.

    Uses a relaxed velocity threshold (3x the still_threshold) to account
    for tracking noise during the address, and a shorter minimum still
    duration (3 frames) since the velocity window smoothing can shorten
    apparent still periods.

    Returns True if a qualifying still period is found before local_min_idx.
    """
    still_thresh = params["still_threshold"] * 3  # relaxed threshold for address detection
    min_still = 3  # shorter than address detection (which uses min_still_duration=5)
    search_start = max(0, local_min_idx - int(fps * 5))

    # Search for any still run in the window before this candidate
    vel_region = velocity[search_start:local_min_idx]
    run_start = None
    for i in range(len(vel_region)):
        if vel_region[i] < still_thresh:
            if run_start is None:
                run_start = i
        else:
            if run_start is not None and (i - run_start) >= min_still:
                # Found a still run — check that hands were LOW (high Y)
                abs_start = search_start + run_start
                abs_end = search_start + i - 1
                avg_y = float(np.mean(y_smooth[abs_start:abs_end + 1]))
                # Hands should be in the lower 60% of Y range (near ball)
                if avg_y > rough_address_y * 0.5:
                    return True
            run_start = None

    # Check if a still run extends to end of region
    if run_start is not None and (len(vel_region) - run_start) >= min_still:
        abs_start = search_start + run_start
        abs_end = search_start + len(vel_region) - 1
        avg_y = float(np.mean(y_smooth[abs_start:abs_end + 1]))
        if avg_y > rough_address_y * 0.5:
            return True

    return False


def find_top_of_backswing(y_smooth, velocity, rough_address_y, fps, params,
                          visibility=None):
    """
    Find the top of backswing: the local minimum of hand Y immediately
    before the fastest downswing.

    Strategy:
      1. Find ALL significant downswing velocity peaks, not just the global max.
         The post-swing hand drop (walking away) can have velocity as large as
         the actual downswing, so using the global max can pick the wrong event.
      2. For each velocity peak (earliest first), search backwards for the
         preceding Y-minimum. Validate:
         a) The minimum is followed by a return to near-address Y level (the
            characteristic backswing-impact "V" shape).
         b) There is a still period (address) with hands low within 5 seconds
            BEFORE the candidate. This rejects post-swing Y dips which have
            no preceding address.
      3. Fall back to prominence-based search if velocity approach fails.

    Using visibility data when available to discount low-confidence frames
    that may contain tracking artifacts during fast motion.

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    n = len(y_smooth)
    prominence = params["top_prominence_threshold"]

    # Compute directional velocity (positive = Y increasing = hands going down)
    y_diff = np.diff(y_smooth)

    # Weight by visibility if available — low-visibility frames are unreliable
    if visibility is not None:
        vis_smooth = smooth_signal(visibility, params["smoothing_window"])
        # Frames with visibility below 0.6 are likely tracking artifacts
        vis_weight = np.clip(vis_smooth[:-1], 0.3, 1.0)
        weighted_diff = y_diff * vis_weight
    else:
        weighted_diff = y_diff

    # Apply rolling average to directional velocity for robustness
    dir_vel_window = max(3, params["smoothing_window"])
    padded = np.pad(weighted_diff, dir_vel_window // 2, mode="edge")
    kernel = np.ones(dir_vel_window) / dir_vel_window
    dir_vel_smooth = np.convolve(padded, kernel, mode="same")
    dir_vel_smooth = dir_vel_smooth[dir_vel_window//2:dir_vel_window//2+len(weighted_diff)]

    diag = {}

    # Strategy 1: Find ALL significant velocity peaks, try each (earliest first)
    # A golf downswing creates a large positive dY/dt (hands coming down fast).
    # But post-swing motion (walking away, lowering hands) can also create a
    # similar velocity spike. Using only the global max picks the wrong one
    # if the post-swing spike is larger.
    global_peak = int(np.argmax(dir_vel_smooth))
    global_peak_vel = float(dir_vel_smooth[global_peak])
    diag["peak_downswing_frame"] = global_peak
    diag["peak_downswing_vel"] = global_peak_vel

    if global_peak_vel > params["still_threshold"] * 5:
        # Find all velocity peaks above 40% of the global max
        peak_threshold = global_peak_vel * 0.4
        vel_peaks = []
        for i in range(2, len(dir_vel_smooth) - 2):
            if (dir_vel_smooth[i] >= dir_vel_smooth[i - 1] and
                    dir_vel_smooth[i] >= dir_vel_smooth[i + 1] and
                    dir_vel_smooth[i] > peak_threshold):
                # Avoid duplicates within 0.5s of each other (keep the stronger one)
                if vel_peaks and (i - vel_peaks[-1]) < int(fps * 0.5):
                    if dir_vel_smooth[i] > dir_vel_smooth[vel_peaks[-1]]:
                        vel_peaks[-1] = i
                else:
                    vel_peaks.append(i)

        diag["velocity_peaks"] = vel_peaks

        # Try each velocity peak in chronological order (earliest first).
        # The first valid backswing→impact "V" shape wins.
        for peak_frame in sorted(vel_peaks):
            search_start = max(0, peak_frame - int(fps * 3))
            search_region = y_smooth[search_start:peak_frame + 1]

            if len(search_region) <= 2:
                continue

            local_min_idx = int(np.argmin(search_region)) + search_start
            top_prominence = rough_address_y - y_smooth[local_min_idx]

            if top_prominence <= prominence:
                continue

            # Validate "V" shape: after the top, Y must return to within 60%
            # of address level within 1.5s. This distinguishes the real
            # backswing→impact from follow-through→walking-away.
            validation_end = min(local_min_idx + int(fps * 1.5), n)
            post_top_y = y_smooth[local_min_idx:validation_end]
            if len(post_top_y) > 0:
                max_return_y = float(np.nanmax(post_top_y))
                # Check that hands come back down to at least 60% of address level
                return_ratio = max_return_y / rough_address_y if rough_address_y > 0 else 0
                if return_ratio < 0.6:
                    # Hands never returned to near-address level — likely
                    # this is the follow-through, not the top of backswing
                    diag.setdefault("rejected_peaks", []).append({
                        "frame": peak_frame,
                        "min_idx": local_min_idx,
                        "return_ratio": round(return_ratio, 3),
                        "reason": "no_v_shape_return",
                    })
                    continue

            # Validate preceding address: there must be a still period with
            # hands low within 5s before this candidate. Post-swing Y dips
            # (follow-through, walking away) have no preceding address.
            if not _has_preceding_address(local_min_idx, velocity, y_smooth,
                                          rough_address_y, fps, params):
                diag.setdefault("rejected_peaks", []).append({
                    "frame": peak_frame,
                    "min_idx": local_min_idx,
                    "reason": "no_preceding_address",
                })
                continue

            diag["chosen"] = local_min_idx
            diag["method"] = "velocity_peak_backtrack"
            diag["top_prominence"] = float(top_prominence)
            diag["used_peak"] = peak_frame
            return local_min_idx, diag

    # Strategy 2: Fallback — prominence-based with velocity and V-shape validation
    minima = []
    for i in range(2, n - 2):
        if (y_smooth[i] <= y_smooth[i - 1] and y_smooth[i] <= y_smooth[i + 1] and
                y_smooth[i] <= y_smooth[i - 2] and y_smooth[i] <= y_smooth[i + 2]):
            minima.append(i)

    qualified = [m for m in minima if (rough_address_y - y_smooth[m]) > prominence]
    diag["all_minima_count"] = len(minima)
    diag["qualified_count"] = len(qualified)

    val_frames = params["downswing_validation_frames"]
    validated = []
    for candidate in qualified:
        window_end = min(candidate + val_frames, n)
        post_vel = velocity[candidate:window_end]
        if len(post_vel) > 0 and np.max(post_vel) > params["still_threshold"] * 3:
            # Also validate V-shape: hands must return toward address level
            v_end = min(candidate + int(fps * 1.5), n)
            post_y = y_smooth[candidate:v_end]
            max_return = float(np.nanmax(post_y)) if len(post_y) > 0 else 0
            return_ratio = max_return / rough_address_y if rough_address_y > 0 else 0
            if return_ratio >= 0.6:
                # Must have a preceding address (still period with hands low)
                if _has_preceding_address(candidate, velocity, y_smooth,
                                          rough_address_y, fps, params):
                    validated.append(candidate)

    if validated:
        # Prefer the FIRST valid minimum (chronologically), not the deepest.
        # The follow-through often has lower Y (hands higher) than the backswing.
        best = validated[0]
        diag["chosen"] = best
        diag["method"] = "prominence_fallback"
        diag["candidates_count"] = len(validated)
        return best, diag

    if qualified:
        # Without V-shape validation, still prefer chronologically first
        best = qualified[0]
        diag["chosen"] = best
        diag["method"] = "prominence_only"
        return best, diag

    # Last resort: global minimum
    if len(y_smooth) > 0:
        gmin = int(np.argmin(y_smooth))
        diag["chosen"] = gmin
        diag["method"] = "global_min"
        return gmin, diag

    return -1, {**diag, "error": "no_valid_top"}


def find_address(y_smooth, velocity, top_frame, params):
    """
    Find the address frame: last moment of stillness before takeaway
    where hands are LOW (near ball level, high Y value).
    Searches only before top_frame.

    Returns (frame_index, diagnostics_dict).
    """
    still_thresh = params["still_threshold"]
    min_dur = params["min_still_duration"]

    search_region = velocity[:top_frame]
    still_mask = search_region < still_thresh

    # Find contiguous runs of still frames
    runs = []
    run_start = None
    for i in range(len(still_mask)):
        if still_mask[i] and run_start is None:
            run_start = i
        elif not still_mask[i] and run_start is not None:
            if (i - run_start) >= min_dur:
                runs.append((run_start, i - 1))
            run_start = None
    # Handle run that extends to end of search region
    if run_start is not None and (len(still_mask) - run_start) >= min_dur:
        runs.append((run_start, len(still_mask) - 1))

    diag = {"total_still_runs": len(runs)}

    if not runs:
        # No still period found - fallback to frame 0
        diag["fallback"] = True
        diag["reason"] = "no_still_period_found"
        return 0, diag

    # Filter runs to those where hands are LOW (high Y = near ball level).
    # The top of backswing has low Y (hands high), so we want runs where
    # the average Y is closer to the max Y (hands low) than to the min Y (hands high).
    top_y = y_smooth[top_frame]
    max_y = float(np.nanmax(y_smooth[:top_frame]))
    y_midpoint = (top_y + max_y) / 2  # midpoint between highest and lowest hand positions

    hands_low_runs = []
    for run_start_f, run_end_f in runs:
        avg_y = float(np.mean(y_smooth[run_start_f:run_end_f + 1]))
        if avg_y > y_midpoint:  # hands are in the lower half (near ball)
            hands_low_runs.append((run_start_f, run_end_f))

    diag["hands_low_runs"] = len(hands_low_runs)

    if hands_low_runs:
        # Pick the last qualifying run (closest to takeaway)
        last_run = hands_low_runs[-1]
        # Within the run, pick the frame with highest Y (hands at their lowest
        # = most settled at ball level). This gives a more natural "address"
        # position rather than the very last still frame before takeaway.
        run_slice = y_smooth[last_run[0]:last_run[1] + 1]
        address_frame = last_run[0] + int(np.argmax(run_slice))
        diag["chosen_run"] = last_run
        diag["address_frame"] = address_frame
        return address_frame, diag

    # Fallback: use the last run with the highest average Y (hands lowest)
    best_run = max(runs, key=lambda r: np.mean(y_smooth[r[0]:r[1] + 1]))
    run_slice = y_smooth[best_run[0]:best_run[1] + 1]
    address_frame = best_run[0] + int(np.argmax(run_slice))
    diag["fallback"] = True
    diag["chosen_run"] = best_run
    diag["address_frame"] = address_frame
    return address_frame, diag


def find_impact(y_smooth, velocity, top_frame, address_y, fps, params):
    """
    Find impact: the moment hands reach maximum downswing speed and decelerate.

    Uses two strategies:
      1. Velocity-based: Find the peak downswing velocity after top, then
         find where the velocity drops below a threshold — this is impact.
         A golf downswing takes 0.2-0.5s, so impact is close after the top.
      2. Y-crossing fallback: If velocity method fails, find where Y returns
         to near address level.

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    # Limit search to a reasonable window after top
    max_downswing_sec = 1.0  # real downswing is 0.2-0.5s, allow margin
    window_frames = int(max_downswing_sec * fps)
    search_end = min(top_frame + window_frames, len(y_smooth))
    search_region = y_smooth[top_frame:search_end]

    if len(search_region) == 0:
        return -1, {"error": "no_frames_after_top"}

    # Strategy 1: Velocity-based impact detection
    # Compute directional velocity in search region (positive = Y increasing = hands down)
    if len(search_region) > 1:
        dir_vel = np.diff(search_region)
        # Smooth directional velocity
        if len(dir_vel) > 3:
            kernel = np.ones(3) / 3
            dir_vel_smooth = np.convolve(dir_vel, kernel, mode="same")
        else:
            dir_vel_smooth = dir_vel

        # Find peak downswing velocity (max positive dY)
        peak_idx = int(np.argmax(dir_vel_smooth))
        peak_vel = dir_vel_smooth[peak_idx]

        if peak_vel > params["still_threshold"] * 2:
            # Impact is where velocity drops back to near-zero after the peak
            # Search from peak forward for velocity settling
            settle_threshold = peak_vel * 0.15  # velocity drops to 15% of peak
            for i in range(peak_idx + 1, len(dir_vel_smooth)):
                if dir_vel_smooth[i] < settle_threshold:
                    impact_frame = top_frame + i
                    diag = {
                        "search_range": (top_frame, search_end),
                        "impact_frame": impact_frame,
                        "peak_downswing_vel": float(peak_vel),
                        "method": "velocity_settle",
                    }
                    return impact_frame, diag

            # If velocity never fully settles, use the point of max deceleration
            # (largest drop in velocity after peak)
            if peak_idx + 2 < len(dir_vel_smooth):
                decel = -np.diff(dir_vel_smooth[peak_idx:])
                max_decel_offset = int(np.argmax(decel))
                impact_frame = top_frame + peak_idx + max_decel_offset + 1
                diag = {
                    "search_range": (top_frame, search_end),
                    "impact_frame": impact_frame,
                    "method": "max_deceleration",
                }
                return impact_frame, diag

    # Strategy 2: Y-crossing fallback
    threshold_y = address_y * 0.85
    crossings = np.where(search_region >= threshold_y)[0]

    if len(crossings) > 0:
        first_crossing = crossings[0]
        refine_end = min(first_crossing + 5, len(search_region))
        refine_region = search_region[first_crossing:refine_end]
        refine_dist = np.abs(refine_region - address_y)
        best_offset = int(np.argmin(refine_dist))
        best_idx = first_crossing + best_offset
        impact_frame = top_frame + int(best_idx)
        diag = {
            "search_range": (top_frame, search_end),
            "distance_to_address": float(np.abs(search_region[best_idx] - address_y)),
            "impact_frame": impact_frame,
            "method": "y_crossing_fallback",
        }
        return impact_frame, diag

    # Last fallback: closest approach to address Y
    distance_to_address = np.abs(search_region - address_y)
    best_idx = int(np.argmin(distance_to_address))
    impact_frame = top_frame + int(best_idx)
    diag = {
        "search_range": (top_frame, search_end),
        "distance_to_address": float(distance_to_address[best_idx]),
        "impact_frame": impact_frame,
        "method": "closest_approach_fallback",
    }
    return impact_frame, diag


def find_follow_through(y_smooth, velocity, impact_frame, top_frame, fps, params,
                        visibility=None):
    """
    Find follow-through: the finish position where hands settle after
    the post-impact rise.

    Strategy:
      1. Skip past the immediate post-impact zone (fast motion with
         potentially unreliable tracking).
      2. Look for where velocity settles to near-zero after impact —
         this is the stable finish position.
      3. Fall back to local minimum search if velocity method fails.

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    window_frames = int(params["followthrough_search_window_sec"] * fps)
    # Skip at least 0.3s after impact to avoid tracking artifacts during fast motion
    min_gap = int(0.3 * fps)
    search_start = impact_frame + min_gap
    search_end = min(impact_frame + window_frames, len(y_smooth))

    if search_start >= search_end:
        # If the gap pushes past the end, search from right after impact
        search_start = impact_frame + 1
        if search_start >= search_end:
            return -1, {"error": "no_frames_after_impact"}

    search_region = y_smooth[search_start:search_end]
    vel_region = velocity[search_start:search_end]

    diag = {"search_range": (search_start, search_end)}

    # Strategy 1: Find where velocity settles to near-zero after impact
    # The follow-through is where the golfer reaches the stable finish position.
    # Find the first long still run and pick its midpoint — the golfer
    # holds the finish, so the middle of the settled period is most natural.
    still_thresh = params["still_threshold"]
    min_still = 3  # need at least 3 consecutive still frames
    settle_start = None

    for i in range(len(vel_region)):
        if vel_region[i] < still_thresh:
            if settle_start is None:
                settle_start = i
        else:
            if settle_start is not None and (i - settle_start) >= min_still:
                # Found a qualifying still run — use its midpoint
                mid = settle_start + (i - settle_start) // 2
                ft_frame = search_start + mid
                diag["chosen"] = ft_frame
                diag["method"] = "velocity_settle"
                diag["settle_run"] = (search_start + settle_start, search_start + i - 1)
                return ft_frame, diag
            settle_start = None

    # Check if the still run extends to end of search window
    if settle_start is not None and (len(vel_region) - settle_start) >= min_still:
        mid = settle_start + (len(vel_region) - settle_start) // 2
        ft_frame = search_start + mid
        diag["chosen"] = ft_frame
        diag["method"] = "velocity_settle"
        diag["settle_run"] = (search_start + settle_start, search_start + len(vel_region) - 1)
        return ft_frame, diag

    # Strategy 2: Find local minimum of Y in search region
    # (hands at highest point in finish position)
    minima = []
    for i in range(2, len(search_region) - 2):
        if (search_region[i] <= search_region[i - 1] and
                search_region[i] <= search_region[i + 1]):
            minima.append(i)

    if minima:
        # Use the first local minimum (earliest stable finish)
        best = minima[0]
        ft_frame = search_start + best
        diag["chosen"] = ft_frame
        diag["method"] = "local_minimum"
        return ft_frame, diag

    # Last resort: global minimum in the search window
    ft_idx = int(np.argmin(search_region))
    ft_frame = search_start + ft_idx
    diag["chosen"] = ft_frame
    diag["method"] = "global_min"
    return ft_frame, diag


# ─── Main orchestrator ───

def detect_phases(landmarks_data, view="dtl", params=None):
    """
    Auto-detect the 4 golf swing phases from landmark data.

    Args:
        landmarks_data: Full JSON dict from extract_landmarks.py
                        (with "summary" and "frames" keys).
        view: "dtl" or "fo" - affects landmark selection.
        params: Optional override dict for algorithm parameters.

    Returns:
        Dict matching DTL_PHASES/FO_PHASES format in calculate_angles.py:
        {
            "address":        {"frame": N, "description": "..."},
            "top":            {"frame": N, "description": "..."},
            "impact":         {"frame": N, "description": "..."},
            "follow_through": {"frame": N, "description": "..."},
            "_diagnostics":   { ... }
        }
    """
    effective_params = {**DEFAULT_PARAMS}
    if params:
        effective_params.update(params)

    frames = landmarks_data["frames"]
    fps = landmarks_data["summary"]["fps"]
    total_frames = len(frames)

    print(f"\n{'='*60}")
    print(f"  PHASE DETECTION ({view.upper()} view)")
    print(f"{'='*60}")
    print(f"  Frames: {total_frames}  |  FPS: {fps:.1f}  |  Duration: {total_frames/fps:.2f}s")

    # Step 0: Select best landmark
    landmark_name = select_primary_landmark(frames, effective_params)
    print(f"  Tracking: {landmark_name}")

    # Step 1: Extract and smooth signal
    y_raw, visibility = extract_hand_signal(frames, landmark_name)
    y_smooth = smooth_signal(y_raw, effective_params["smoothing_window"])
    velocity = compute_velocity(y_smooth, effective_params["velocity_window"])

    # Debug: velocity statistics to calibrate thresholds
    valid_vel = velocity[velocity > 0]
    if len(valid_vel) > 0:
        print(f"  Velocity stats: min={np.min(valid_vel):.6f}, "
              f"p25={np.percentile(valid_vel, 25):.6f}, "
              f"median={np.median(valid_vel):.6f}, "
              f"p75={np.percentile(valid_vel, 75):.6f}, "
              f"max={np.max(valid_vel):.6f}")
        still_count = np.sum(velocity < effective_params["still_threshold"])
        print(f"  Frames below still_threshold ({effective_params['still_threshold']}): "
              f"{still_count}/{len(velocity)} ({still_count/len(velocity)*100:.1f}%)")

    # Step 2: Rough address Y estimate (max Y where hands are low)
    # Use the global max of valid (non-NaN) smoothed Y values.
    # This is the position where hands are lowest (near ball level).
    valid_y = y_smooth[~np.isnan(y_smooth)]
    if len(valid_y) == 0:
        print("  ERROR: No valid landmark data found.")
        print("  Check that the video shows the golfer clearly.")
        sys.exit(1)
    rough_address_y = float(np.nanmax(valid_y))

    # Step 3: Find top of backswing (the anchor)
    top_frame, top_diag = find_top_of_backswing(
        y_smooth, velocity, rough_address_y, fps, effective_params,
        visibility=visibility
    )
    if top_frame < 0:
        print("  ERROR: Could not detect top of backswing.")
        print("  Check that the video contains a golf swing.")
        sys.exit(1)

    print(f"\n  TOP of backswing:  frame {top_frame}  (t={top_frame/fps:.2f}s, Y={y_smooth[top_frame]:.4f})")

    # Step 4: Find address (before top)
    address_frame, addr_diag = find_address(
        y_smooth, velocity, top_frame, effective_params
    )
    address_y = float(y_smooth[address_frame])

    print(f"  ADDRESS:           frame {address_frame}  (t={address_frame/fps:.2f}s, Y={address_y:.4f})")

    # Step 5: Find impact (after top)
    impact_frame, impact_diag = find_impact(
        y_smooth, velocity, top_frame, address_y, fps, effective_params
    )
    if impact_frame >= 0:
        print(f"  IMPACT:            frame {impact_frame}  (t={impact_frame/fps:.2f}s, Y={y_smooth[impact_frame]:.4f})")
        print(f"                     method: {impact_diag.get('method', 'unknown')}")
    else:
        print(f"  IMPACT:            NOT DETECTED")

    # Step 6: Find follow-through (after impact)
    if impact_frame >= 0:
        ft_frame, ft_diag = find_follow_through(
            y_smooth, velocity, impact_frame, top_frame, fps, effective_params,
            visibility=visibility
        )
    else:
        ft_frame = -1
        ft_diag = {"error": "no_impact_detected"}

    if ft_frame >= 0:
        print(f"  FOLLOW-THROUGH:    frame {ft_frame}  (t={ft_frame/fps:.2f}s, Y={y_smooth[ft_frame]:.4f})")
    else:
        print(f"  FOLLOW-THROUGH:    NOT DETECTED")

    # Build result
    phases = {
        "address": {
            "frame": int(address_frame),
            "description": "Setup position, club grounded behind ball",
        },
        "top": {
            "frame": int(top_frame),
            "description": "Top of backswing, hands at highest point",
        },
        "impact": {
            "frame": int(impact_frame) if impact_frame >= 0 else 0,
            "description": "Club at ball, hands returning to address height",
        },
        "follow_through": {
            "frame": int(ft_frame) if ft_frame >= 0 else 0,
            "description": "Full extension post-impact, arms high",
        },
    }

    # Timing summary
    if impact_frame >= 0:
        backswing_frames = top_frame - address_frame
        downswing_frames = impact_frame - top_frame
        print(f"\n  Backswing: {backswing_frames} frames ({backswing_frames/fps:.2f}s)")
        print(f"  Downswing: {downswing_frames} frames ({downswing_frames/fps:.2f}s)")
        print(f"  Tempo ratio (back/down): {backswing_frames/max(downswing_frames,1):.1f}:1")

    diagnostics = {
        "landmark_used": landmark_name,
        "fps": fps,
        "total_frames": total_frames,
        "address_y": address_y,
        "top_y": float(y_smooth[top_frame]),
        "params_used": effective_params,
        "top_diagnostics": top_diag,
        "address_diagnostics": addr_diag,
        "impact_diagnostics": impact_diag,
        "followthrough_diagnostics": ft_diag,
    }

    phases["_diagnostics"] = diagnostics
    return phases


# ─── CLI ───

def main():
    parser = argparse.ArgumentParser(
        description="Auto-detect golf swing phases from landmark data"
    )
    parser.add_argument("landmarks_json", help="Path to landmarks JSON file")
    parser.add_argument("--view", choices=["dtl", "fo"], default="dtl",
                        help="Camera view type (default: dtl)")
    parser.add_argument("--output", help="Output JSON path (default: auto-named)")
    parser.add_argument("--smoothing-window", type=int, default=None)
    parser.add_argument("--velocity-window", type=int, default=None)
    parser.add_argument("--still-threshold", type=float, default=None)
    args = parser.parse_args()

    if not os.path.exists(args.landmarks_json):
        print(f"ERROR: File not found: {args.landmarks_json}")
        sys.exit(1)

    with open(args.landmarks_json) as f:
        landmarks_data = json.load(f)

    # Build param overrides from CLI args
    param_overrides = {}
    if args.smoothing_window is not None:
        param_overrides["smoothing_window"] = args.smoothing_window
    if args.velocity_window is not None:
        param_overrides["velocity_window"] = args.velocity_window
    if args.still_threshold is not None:
        param_overrides["still_threshold"] = args.still_threshold

    phases = detect_phases(landmarks_data, view=args.view,
                           params=param_overrides if param_overrides else None)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(args.landmarks_json)[0]
        output_path = base.replace("_landmarks", "_phases") + ".json"

    # Save phases (without internal diagnostics)
    output_data = {
        "phases": {k: v for k, v in phases.items() if k != "_diagnostics"},
        "metadata": {
            "source_file": os.path.basename(args.landmarks_json),
            "view": args.view,
            "landmark_used": phases["_diagnostics"]["landmark_used"],
            "fps": phases["_diagnostics"]["fps"],
            "total_frames": phases["_diagnostics"]["total_frames"],
        },
    }

    with open(output_path, "w") as f:
        json.dump(output_data, f, indent=2)

    print(f"\n  Phases saved to: {output_path}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
