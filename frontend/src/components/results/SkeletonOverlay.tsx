"use client";

import { useRef, useEffect, useCallback } from "react";
import type { PhaseLandmarks, LandmarkPoint, FrameLandmark } from "@/types";

interface SkeletonOverlayProps {
  videoRef: HTMLVideoElement | null;
  /** Static landmarks for a single phase (used when paused or no frame data) */
  landmarks: PhaseLandmarks | undefined;
  /** All frame landmarks for continuous playback sync */
  allFrameLandmarks?: FrameLandmark[];
  visible: boolean;
  /** Whether the video is currently playing */
  isPlaying: boolean;
}

// Body connections for the skeleton (12 lines)
const SKELETON_CONNECTIONS: [string, string][] = [
  // Shoulder line
  ["left_shoulder", "right_shoulder"],
  // Hip line
  ["left_hip", "right_hip"],
  // Left torso
  ["left_shoulder", "left_hip"],
  // Right torso
  ["right_shoulder", "right_hip"],
  // Left arm
  ["left_shoulder", "left_elbow"],
  ["left_elbow", "left_wrist"],
  // Right arm
  ["right_shoulder", "right_elbow"],
  ["right_elbow", "right_wrist"],
  // Left leg
  ["left_hip", "left_knee"],
  ["left_knee", "left_ankle"],
  // Right leg
  ["right_hip", "right_knee"],
  ["right_knee", "right_ankle"],
];

// Colors from the Pure design system
const LINE_COLOR = "#2E5B3B"; // Forest Green
const DOT_COLOR = "#F6F1E5"; // Cream
const LINE_WIDTH = 2.5;
const DOT_RADIUS = 4;

/**
 * Calculate the actual rendered region of a video inside its container
 * when using `object-fit: contain`. The video may be letterboxed
 * (bars on sides) or pillarboxed (bars on top/bottom).
 */
function getVideoRenderRect(video: HTMLVideoElement) {
  const cW = video.clientWidth;
  const cH = video.clientHeight;
  const vW = video.videoWidth;
  const vH = video.videoHeight;

  if (!vW || !vH) {
    return { offsetX: 0, offsetY: 0, renderWidth: cW, renderHeight: cH };
  }

  const videoAspect = vW / vH;
  const containerAspect = cW / cH;

  if (videoAspect > containerAspect) {
    // Video is wider than container → bars on top/bottom
    const renderWidth = cW;
    const renderHeight = cW / videoAspect;
    return {
      offsetX: 0,
      offsetY: (cH - renderHeight) / 2,
      renderWidth,
      renderHeight,
    };
  } else {
    // Video is taller than container → bars on left/right
    const renderHeight = cH;
    const renderWidth = cH * videoAspect;
    return {
      offsetX: (cW - renderWidth) / 2,
      offsetY: 0,
      renderWidth,
      renderHeight,
    };
  }
}

/**
 * Convert a normalized landmark (0-1) to pixel coordinates on the canvas,
 * accounting for the object-contain offset.
 */
function landmarkToPixel(
  lm: LandmarkPoint,
  rect: { offsetX: number; offsetY: number; renderWidth: number; renderHeight: number }
): { px: number; py: number } {
  return {
    px: rect.offsetX + lm.x * rect.renderWidth,
    py: rect.offsetY + lm.y * rect.renderHeight,
  };
}

/**
 * Draw the skeleton (lines + dots) onto the canvas.
 */
function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  landmarks: PhaseLandmarks,
  rect: ReturnType<typeof getVideoRenderRect>
) {
  // Draw connection lines
  ctx.strokeStyle = LINE_COLOR;
  ctx.lineWidth = LINE_WIDTH;
  ctx.lineCap = "round";

  for (const [jointA, jointB] of SKELETON_CONNECTIONS) {
    const a = landmarks[jointA];
    const b = landmarks[jointB];
    if (!a || !b) continue;

    const pxA = landmarkToPixel(a, rect);
    const pxB = landmarkToPixel(b, rect);

    ctx.beginPath();
    ctx.moveTo(pxA.px, pxA.py);
    ctx.lineTo(pxB.px, pxB.py);
    ctx.stroke();
  }

  // Draw joint dots on top of lines
  ctx.fillStyle = DOT_COLOR;

  for (const joint of Object.values(landmarks)) {
    const px = landmarkToPixel(joint, rect);
    ctx.beginPath();
    ctx.arc(px.px, px.py, DOT_RADIUS, 0, Math.PI * 2);
    ctx.fill();
  }
}

/**
 * Binary search for the nearest frame landmark by timestamp.
 * Returns the landmark data for the frame closest to `time`.
 */
function findNearestFrame(
  frames: FrameLandmark[],
  time: number
): PhaseLandmarks | null {
  if (frames.length === 0) return null;

  let lo = 0;
  let hi = frames.length - 1;

  // Binary search for closest timestamp
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (frames[mid].t < time) {
      lo = mid + 1;
    } else {
      hi = mid;
    }
  }

  // Check if the previous frame is actually closer
  if (lo > 0 && Math.abs(frames[lo - 1].t - time) < Math.abs(frames[lo].t - time)) {
    lo = lo - 1;
  }

  return frames[lo].lm;
}

export default function SkeletonOverlay({
  videoRef,
  landmarks,
  allFrameLandmarks,
  visible,
  isPlaying,
}: SkeletonOverlayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafIdRef = useRef<number>(0);

  // Core draw function that renders a given set of landmarks
  const drawFrame = useCallback(
    (currentLandmarks: PhaseLandmarks | null | undefined) => {
      const canvas = canvasRef.current;
      if (!canvas || !videoRef) return;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const displayWidth = videoRef.clientWidth;
      const displayHeight = videoRef.clientHeight;

      canvas.width = displayWidth * dpr;
      canvas.height = displayHeight * dpr;
      ctx.scale(dpr, dpr);

      ctx.clearRect(0, 0, displayWidth, displayHeight);

      if (
        visible &&
        currentLandmarks &&
        Object.keys(currentLandmarks).length > 0
      ) {
        const rect = getVideoRenderRect(videoRef);
        drawSkeleton(ctx, currentLandmarks, rect);
      }
    },
    [videoRef, visible]
  );

  // Continuous playback mode: sync skeleton to video currentTime via rAF
  useEffect(() => {
    if (
      !visible ||
      !isPlaying ||
      !allFrameLandmarks ||
      allFrameLandmarks.length === 0 ||
      !videoRef
    ) {
      return;
    }

    const tick = () => {
      const currentTime = videoRef.currentTime;
      const frameLandmarks = findNearestFrame(allFrameLandmarks, currentTime);
      drawFrame(frameLandmarks);
      rafIdRef.current = requestAnimationFrame(tick);
    };

    rafIdRef.current = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(rafIdRef.current);
    };
  }, [visible, isPlaying, allFrameLandmarks, videoRef, drawFrame]);

  // Static mode: draw phase landmarks when paused or no frame data available
  useEffect(() => {
    // Only draw static landmarks when NOT in continuous playback mode
    if (isPlaying && allFrameLandmarks && allFrameLandmarks.length > 0) {
      return; // rAF loop handles this
    }

    const canvas = canvasRef.current;
    if (!canvas || !videoRef) return;

    const draw = () => {
      drawFrame(landmarks);
    };

    draw();

    // Redraw on container resize (responsive layout, window resize)
    const resizeObserver = new ResizeObserver(draw);
    resizeObserver.observe(videoRef);

    return () => {
      resizeObserver.disconnect();
    };
  }, [videoRef, landmarks, visible, isPlaying, allFrameLandmarks, drawFrame]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none"
      style={{ zIndex: 10 }}
    />
  );
}
