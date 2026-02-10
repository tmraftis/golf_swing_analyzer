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

def extract_hand_signal(frames, landmark_name):
    """
    Extract Y-position and visibility arrays for a landmark across all frames.

    Returns:
        (y_array, visibility_array): 1D numpy arrays of length len(frames).
        Frames with no detection get y=NaN and visibility=0.
    """
    n = len(frames)
    y_arr = np.full(n, np.nan)
    vis_arr = np.zeros(n)

    for i, f in enumerate(frames):
        if f["detected"] and landmark_name in f["landmarks"]:
            lm = f["landmarks"][landmark_name]
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

def find_top_of_backswing(y_smooth, velocity, rough_address_y, fps, params):
    """
    Find the top of backswing: first significant local minimum of hand Y
    where a fast downswing follows.

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    n = len(y_smooth)
    prominence = params["top_prominence_threshold"]
    val_frames = params["downswing_validation_frames"]

    # Find all local minima (check 2 frames on each side for robustness)
    minima = []
    for i in range(2, n - 2):
        if (y_smooth[i] <= y_smooth[i - 1] and y_smooth[i] <= y_smooth[i + 1] and
                y_smooth[i] <= y_smooth[i - 2] and y_smooth[i] <= y_smooth[i + 2]):
            minima.append(i)

    # Filter by prominence: must be significantly higher than address level
    # (lower Y value = higher position in image)
    qualified = [m for m in minima if (rough_address_y - y_smooth[m]) > prominence]

    diag = {"all_minima_count": len(minima), "qualified_count": len(qualified)}

    # Validate with downswing check: velocity should spike after top
    for candidate in qualified:
        window_end = min(candidate + val_frames, n)
        post_vel = velocity[candidate:window_end]
        if len(post_vel) > 0 and np.max(post_vel) > params["still_threshold"] * 3:
            diag["chosen"] = candidate
            diag["validated"] = True
            return candidate, diag

    # Fallback: use the first qualified minimum
    if qualified:
        best = qualified[0]
        diag["chosen"] = best
        diag["fallback"] = True
        return best, diag

    # Last resort: global minimum of Y in the signal
    if len(y_smooth) > 0:
        gmin = int(np.argmin(y_smooth))
        diag["chosen"] = gmin
        diag["global_min_fallback"] = True
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
        address_frame = last_run[1]
        diag["chosen_run"] = last_run
        diag["address_frame"] = address_frame
        return address_frame, diag

    # Fallback: use the last run with the highest average Y (hands lowest)
    best_run = max(runs, key=lambda r: np.mean(y_smooth[r[0]:r[1] + 1]))
    address_frame = best_run[1]
    diag["fallback"] = True
    diag["chosen_run"] = best_run
    diag["address_frame"] = address_frame
    return address_frame, diag


def find_impact(y_smooth, velocity, top_frame, address_y, fps, params):
    """
    Find impact: FIRST frame where hand Y returns to near address Y after top.

    The key insight: during the downswing, Y increases (hands come down).
    Impact is the FIRST time Y gets close to address level. We don't want
    to search too far and accidentally find a second swing.

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    window_frames = int(params["impact_search_window_sec"] * fps)
    search_end = min(top_frame + window_frames, len(y_smooth))
    search_region = y_smooth[top_frame:search_end]

    if len(search_region) == 0:
        return -1, {"error": "no_frames_after_top"}

    # Strategy: find the FIRST frame where Y crosses a threshold near address level.
    # Use 85% of address_y as threshold (hands don't always return to exact address height)
    threshold_y = address_y * 0.85

    # Find first frame where Y rises above threshold (hands coming down to ball)
    crossings = np.where(search_region >= threshold_y)[0]

    if len(crossings) > 0:
        # Take the first crossing - this is impact
        first_crossing = crossings[0]
        # Refine: among the first few crossing frames, pick the one closest to address_y
        # (look at a small window around the first crossing)
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
            "method": "first_crossing",
        }
        return impact_frame, diag

    # Fallback: no crossing found - find closest approach to address_y
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


def find_follow_through(y_smooth, velocity, impact_frame, top_frame, fps, params):
    """
    Find follow-through: next local minimum of hand Y after impact
    (hands go high again in finish position).

    Uses the backswing duration as a guide for how far to search
    (follow-through typically takes similar time to the backswing).

    Returns (frame_index, diagnostics_dict). Returns (-1, diag) if not found.
    """
    window_frames = int(params["followthrough_search_window_sec"] * fps)
    search_start = impact_frame + 1
    search_end = min(impact_frame + window_frames, len(y_smooth))

    if search_start >= search_end:
        return -1, {"error": "no_frames_after_impact"}

    search_region = y_smooth[search_start:search_end]

    # After impact, hands rise (Y decreases), then stop at finish.
    # The follow-through is the first significant local min after impact
    # where Y has dropped meaningfully below impact level.
    impact_y = y_smooth[impact_frame]
    top_y = y_smooth[top_frame]
    # The follow-through hands should be at least partway between impact and top height
    ft_threshold = impact_y - (impact_y - top_y) * 0.3  # at least 30% of the way up

    # Find local minima in the search region
    minima = []
    for i in range(2, len(search_region) - 2):
        if (search_region[i] <= search_region[i - 1] and
                search_region[i] <= search_region[i + 1]):
            minima.append(i)

    # Filter minima to those where hands are significantly above impact level
    qualified = [m for m in minima if search_region[m] < ft_threshold]

    if qualified:
        # Return the FIRST qualified minimum (earliest follow-through peak)
        best = qualified[0]
        ft_frame = search_start + best
        diag = {
            "minima_count": len(minima),
            "qualified_count": len(qualified),
            "chosen": ft_frame,
        }
        return ft_frame, diag

    # If no qualified minima, take deepest minimum in search region
    if minima:
        best = min(minima, key=lambda m: search_region[m])
        ft_frame = search_start + best
        return ft_frame, {"fallback": "deepest_minimum", "chosen": ft_frame}

    # Last resort: global minimum in the search window
    ft_idx = int(np.argmin(search_region))
    ft_frame = search_start + ft_idx
    return ft_frame, {"fallback": "global_min", "chosen": ft_frame}


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

    # Step 2: Rough address Y estimate (max Y in first quarter = hands low)
    first_quarter = y_smooth[:max(total_frames // 4, 30)]
    rough_address_y = float(np.nanmax(first_quarter))

    # Step 3: Find top of backswing (the anchor)
    top_frame, top_diag = find_top_of_backswing(
        y_smooth, velocity, rough_address_y, fps, effective_params
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
        print(f"                     distance to address Y: {impact_diag['distance_to_address']:.4f}")
    else:
        print(f"  IMPACT:            NOT DETECTED")

    # Step 6: Find follow-through (after impact)
    if impact_frame >= 0:
        ft_frame, ft_diag = find_follow_through(
            y_smooth, velocity, impact_frame, top_frame, fps, effective_params
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
