"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import type {
  VideoAngle,
  VideoUrls,
  AngleData,
  SwingPhase,
  PhaseLandmarkData,
  AllLandmarkData,
  PhaseImageData,
} from "@/types";
import { SWING_PHASES, PHASE_LABELS } from "@/types";
import { getVideoUrl } from "@/lib/api";
import SkeletonOverlay from "./SkeletonOverlay";

interface VideoComparisonProps {
  videoUrls: VideoUrls;
  referenceVideoUrls: VideoUrls;
  userAngles: AngleData;
  referenceAngles: AngleData;
  activeView: VideoAngle;
  activePhase: SwingPhase;
  onPhaseChange: (phase: SwingPhase) => void;
  userPhaseLandmarks?: PhaseLandmarkData;
  referencePhaseLandmarks?: PhaseLandmarkData;
  userAllLandmarks?: AllLandmarkData;
  userPhaseImages?: PhaseImageData;
  referencePhaseImages?: PhaseImageData;
}

export default function VideoComparison({
  videoUrls,
  referenceVideoUrls,
  userAngles,
  referenceAngles,
  activeView,
  activePhase,
  onPhaseChange,
  userPhaseLandmarks,
  referencePhaseLandmarks,
  userAllLandmarks,
  userPhaseImages,
  referencePhaseImages,
}: VideoComparisonProps) {
  const userVideoRef = useRef<HTMLVideoElement | null>(null);
  const refVideoRef = useRef<HTMLVideoElement | null>(null);

  const [isPlaying, setIsPlaying] = useState(false);
  const [userTime, setUserTime] = useState(0);
  const [userDuration, setUserDuration] = useState(0);

  // Skeleton overlay state
  const [showSkeleton, setShowSkeleton] = useState(false);
  const userLandmarks = userPhaseLandmarks?.[activeView]?.[activePhase];
  const refLandmarks = referencePhaseLandmarks?.[activeView]?.[activePhase];
  const hasLandmarkData = !!(userPhaseLandmarks || referencePhaseLandmarks);
  // Frame-by-frame landmarks for the active view (user video only)
  const userFrameLandmarks = userAllLandmarks?.[activeView];
  // Phase frame images for instant switching
  const userPhaseImage = userPhaseImages?.[activeView]?.[activePhase];
  const refPhaseImage = referencePhaseImages?.[activeView]?.[activePhase];

  // Preload phase images for the active view on mount
  useEffect(() => {
    const sources = [userPhaseImages, referencePhaseImages];
    for (const imageData of sources) {
      if (!imageData) continue;
      const viewImages = imageData[activeView];
      if (!viewImages) continue;
      for (const url of Object.values(viewImages)) {
        if (url) {
          const img = new Image();
          img.src = getVideoUrl(url);
        }
      }
    }
  }, [userPhaseImages, referencePhaseImages, activeView]);

  // Seek a single video, waiting for it to be ready if needed
  const seekVideo = useCallback(
    (video: HTMLVideoElement, targetTime: number) => {
      if (video.readyState >= 1) {
        video.currentTime = targetTime;
      } else {
        const handler = () => {
          video.currentTime = targetTime;
          video.removeEventListener("loadeddata", handler);
        };
        video.addEventListener("loadeddata", handler);
      }
    },
    []
  );

  // Seek both videos to a specific phase
  const seekVideosToPhase = useCallback(
    (phase: SwingPhase) => {
      const userVideo = userVideoRef.current;
      const refVideo = refVideoRef.current;
      const userPhaseData = userAngles[activeView]?.[phase];
      const refPhaseData = referenceAngles[activeView]?.[phase];

      if (userVideo && userPhaseData) {
        seekVideo(userVideo, userPhaseData.timestamp_sec);
      }
      if (refVideo && refPhaseData) {
        seekVideo(refVideo, refPhaseData.timestamp_sec);
      }

      setIsPlaying(false);
      userVideo?.pause();
      refVideo?.pause();
    },
    [activeView, userAngles, referenceAngles, seekVideo]
  );

  // Called by internal phase buttons — updates parent + seeks
  const handlePhaseClick = useCallback(
    (phase: SwingPhase) => {
      onPhaseChange(phase);
      seekVideosToPhase(phase);
    },
    [onPhaseChange, seekVideosToPhase]
  );

  // Sync play/pause
  const togglePlay = useCallback(() => {
    const userVideo = userVideoRef.current;
    const refVideo = refVideoRef.current;
    if (isPlaying) {
      userVideo?.pause();
      refVideo?.pause();
      setIsPlaying(false);
    } else {
      userVideo?.play();
      refVideo?.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  // When active phase changes, seek videos
  useEffect(() => {
    setIsPlaying(false);
    seekVideosToPhase(activePhase);
  }, [activePhase, seekVideosToPhase]);

  // Track user video time for progress bar
  const handleTimeUpdate = useCallback(() => {
    const userVideo = userVideoRef.current;
    if (userVideo) {
      setUserTime(userVideo.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    const video = userVideoRef.current;
    if (video) {
      setUserDuration(video.duration);
    }
  }, []);

  // When both videos end, reset playing state
  const handleEnded = useCallback(() => {
    setIsPlaying(false);
  }, []);

  // Build phase markers for the progress bar
  const phaseMarkers = SWING_PHASES.map((phase) => {
    const phaseData = userAngles[activeView]?.[phase];
    if (!phaseData || !userDuration) return null;
    const pct = (phaseData.timestamp_sec / userDuration) * 100;
    return { phase, pct, label: PHASE_LABELS[phase] };
  }).filter(Boolean) as { phase: SwingPhase; pct: number; label: string }[];

  const progressPct = userDuration ? (userTime / userDuration) * 100 : 0;

  const userVideoUrl = videoUrls[activeView];
  const refVideoUrl = referenceVideoUrls[activeView];

  return (
    <div className="space-y-4">
      {/* Side-by-side videos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* User video */}
        <div>
          <h3 className="text-sm font-medium text-cream/50 mb-2">
            Your Swing
          </h3>
          <div className="rounded-lg overflow-hidden bg-black/30 aspect-video relative">
            {userVideoUrl && (
              <video
                ref={userVideoRef}
                src={getVideoUrl(userVideoUrl)}
                className="w-full h-full object-contain"
                muted
                playsInline
                preload="auto"
                onTimeUpdate={handleTimeUpdate}
                onLoadedMetadata={handleLoadedMetadata}
                onEnded={handleEnded}
              />
            )}
            {/* Phase frame image: instant display when paused, hidden during playback */}
            {userPhaseImage && !isPlaying && (
              <img
                src={getVideoUrl(userPhaseImage)}
                alt=""
                className="absolute inset-0 w-full h-full object-contain"
                style={{ zIndex: 5 }}
              />
            )}
            <SkeletonOverlay
              videoRef={userVideoRef.current}
              landmarks={userLandmarks}
              allFrameLandmarks={userFrameLandmarks}
              visible={showSkeleton}
              isPlaying={isPlaying}
            />
          </div>
        </div>

        {/* Tiger video */}
        <div>
          <h3 className="text-sm font-medium text-cream/50 mb-2">
            Tiger Woods 2000
          </h3>
          <div className="rounded-lg overflow-hidden bg-black/30 aspect-video relative">
            {refVideoUrl && (
              <video
                ref={refVideoRef}
                src={getVideoUrl(refVideoUrl)}
                className="w-full h-full object-contain"
                muted
                playsInline
                preload="auto"
                onEnded={handleEnded}
              />
            )}
            {/* Phase frame image: instant display when paused, hidden during playback */}
            {refPhaseImage && !isPlaying && (
              <img
                src={getVideoUrl(refPhaseImage)}
                alt=""
                className="absolute inset-0 w-full h-full object-contain"
                style={{ zIndex: 5 }}
              />
            )}
            <SkeletonOverlay
              videoRef={refVideoRef.current}
              landmarks={refLandmarks}
              visible={showSkeleton && !isPlaying}
              isPlaying={isPlaying}
            />
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="space-y-3">
        {/* Progress bar with phase markers */}
        <div className="relative h-2 bg-cream/10 rounded-full">
          {/* Progress fill */}
          <div
            className="absolute top-0 left-0 h-full bg-forest-green rounded-full transition-all duration-100"
            style={{ width: `${progressPct}%` }}
          />
          {/* Phase markers */}
          {phaseMarkers.map(({ phase, pct, label }) => (
            <button
              key={phase}
              onClick={() => handlePhaseClick(phase)}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 group"
              style={{ left: `${pct}%` }}
              title={label}
            >
              <div
                className={`w-3.5 h-3.5 rounded-full border-2 transition-all ${
                  phase === activePhase
                    ? "bg-pastel-yellow border-pastel-yellow scale-125"
                    : "bg-blue-charcoal border-cream/40 group-hover:border-cream/70"
                }`}
              />
            </button>
          ))}
        </div>

        {/* Play/pause + phase buttons */}
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlay}
            className="w-10 h-10 rounded-full bg-cream/10 hover:bg-cream/20 flex items-center justify-center transition-colors"
          >
            {isPlaying ? (
              <svg
                className="w-4 h-4 text-cream"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M5.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75A.75.75 0 007.25 3h-1.5zM12.75 3a.75.75 0 00-.75.75v12.5c0 .414.336.75.75.75h1.5a.75.75 0 00.75-.75V3.75a.75.75 0 00-.75-.75h-1.5z" />
              </svg>
            ) : (
              <svg
                className="w-4 h-4 text-cream ml-0.5"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M6.3 2.841A1.5 1.5 0 004 4.11v11.78a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z" />
              </svg>
            )}
          </button>

          {/* Skeleton overlay toggle */}
          {hasLandmarkData && (
            <button
              onClick={() => setShowSkeleton((prev) => !prev)}
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                showSkeleton
                  ? "bg-forest-green text-cream"
                  : "bg-cream/10 hover:bg-cream/20 text-cream/50"
              }`}
              title={showSkeleton ? "Hide skeleton" : "Show skeleton"}
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z"
                />
              </svg>
            </button>
          )}

          <div className="flex items-center gap-1">
            {SWING_PHASES.map((phase) => (
              <button
                key={phase}
                onClick={() => handlePhaseClick(phase)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                  phase === activePhase
                    ? "bg-pastel-yellow/20 text-pastel-yellow"
                    : "text-cream/40 hover:text-cream/70 hover:bg-cream/5"
                }`}
              >
                {PHASE_LABELS[phase]}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
