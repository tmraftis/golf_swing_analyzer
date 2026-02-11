"use client";

import { useRef, useState, useCallback, useEffect } from "react";
import type {
  VideoAngle,
  VideoUrls,
  AngleData,
  SwingPhase,
} from "@/types";
import { SWING_PHASES, PHASE_LABELS } from "@/types";
import { getVideoUrl } from "@/lib/api";

interface VideoComparisonProps {
  videoUrls: VideoUrls;
  referenceVideoUrls: VideoUrls;
  userAngles: AngleData;
  referenceAngles: AngleData;
  activeView: VideoAngle;
  activePhase: SwingPhase;
  onPhaseChange: (phase: SwingPhase) => void;
}

export default function VideoComparison({
  videoUrls,
  referenceVideoUrls,
  userAngles,
  referenceAngles,
  activeView,
  activePhase,
  onPhaseChange,
}: VideoComparisonProps) {
  const userVideoRef = useRef<HTMLVideoElement>(null);
  const refVideoRef = useRef<HTMLVideoElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [userTime, setUserTime] = useState(0);
  const [userDuration, setUserDuration] = useState(0);
  const [userVideoReady, setUserVideoReady] = useState(false);
  const [refVideoReady, setRefVideoReady] = useState(false);
  const pendingPhaseRef = useRef<SwingPhase>(activePhase);

  const userSrc = getVideoUrl(videoUrls[activeView]);
  const refSrc = getVideoUrl(referenceVideoUrls[activeView]);

  // Reset readiness when video sources change (view toggle)
  useEffect(() => {
    setUserVideoReady(false);
    setRefVideoReady(false);
  }, [userSrc, refSrc]);

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

  // Seek both videos to a specific phase (internal — does not update parent state)
  const seekVideosToPhase = useCallback(
    (phase: SwingPhase) => {
      const userPhaseData = userAngles[activeView]?.[phase];
      const refPhaseData = referenceAngles[activeView]?.[phase];

      if (userVideoRef.current && userPhaseData) {
        seekVideo(userVideoRef.current, userPhaseData.timestamp_sec);
      }
      if (refVideoRef.current && refPhaseData) {
        seekVideo(refVideoRef.current, refPhaseData.timestamp_sec);
      }

      setIsPlaying(false);
      userVideoRef.current?.pause();
      refVideoRef.current?.pause();
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
    if (isPlaying) {
      userVideoRef.current?.pause();
      refVideoRef.current?.pause();
      setIsPlaying(false);
    } else {
      userVideoRef.current?.play();
      refVideoRef.current?.play();
      setIsPlaying(true);
    }
  }, [isPlaying]);

  // Track the desired phase and seek when it changes
  useEffect(() => {
    pendingPhaseRef.current = activePhase;
    seekVideosToPhase(activePhase);
  }, [activeView, activePhase, seekVideosToPhase]);

  // When a video becomes ready, execute any pending seek
  useEffect(() => {
    if (userVideoReady || refVideoReady) {
      seekVideosToPhase(pendingPhaseRef.current);
    }
  }, [userVideoReady, refVideoReady, seekVideosToPhase]);

  // Track user video time for progress bar
  const handleTimeUpdate = useCallback(() => {
    if (userVideoRef.current) {
      setUserTime(userVideoRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (userVideoRef.current) {
      setUserDuration(userVideoRef.current.duration);
      setUserVideoReady(true);
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

  return (
    <div className="space-y-4">
      {/* Side-by-side videos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* User video */}
        <div>
          <h3 className="text-sm font-medium text-cream/50 mb-2">
            Your Swing
          </h3>
          <div className="rounded-xl overflow-hidden bg-black/30 aspect-video">
            <video
              ref={userVideoRef}
              src={userSrc}
              className="w-full h-full object-contain"
              muted
              playsInline
              preload="auto"
              onTimeUpdate={handleTimeUpdate}
              onLoadedMetadata={handleLoadedMetadata}
              onEnded={handleEnded}
            />
          </div>
        </div>

        {/* Tiger video */}
        <div>
          <h3 className="text-sm font-medium text-cream/50 mb-2">
            Tiger Woods 2000
          </h3>
          <div className="rounded-xl overflow-hidden bg-black/30 aspect-video">
            <video
              ref={refVideoRef}
              src={refSrc}
              className="w-full h-full object-contain"
              muted
              playsInline
              preload="auto"
              onLoadedMetadata={() => setRefVideoReady(true)}
              onEnded={handleEnded}
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
