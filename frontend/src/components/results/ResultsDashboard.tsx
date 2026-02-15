"use client";

import { useState } from "react";
import Link from "next/link";
import type { AnalysisResponse, VideoAngle, SwingPhase } from "@/types";
import VideoComparison from "./VideoComparison";
import PhaseTimeline from "./PhaseTimeline";
import DifferenceCard from "./DifferenceCard";
import AngleComparisonTable from "./AngleComparisonTable";
import ShareModal from "./ShareModal";
import Button from "@/components/Button";

interface ResultsDashboardProps {
  analysis: AnalysisResponse;
}

function ScoreRing({ score }: { score: number }) {
  const radius = 58;
  const stroke = 6;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;

  return (
    <div className="relative w-36 h-36">
      <svg className="w-36 h-36 -rotate-90" viewBox="0 0 128 128">
        {/* Track */}
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          className="text-cream/10"
        />
        {/* Progress */}
        <circle
          cx="64"
          cy="64"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          className="text-forest-green"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-4xl font-bold tracking-tight">{score}</span>
        <span className="text-lg font-semibold text-cream/50 mt-1">%</span>
      </div>
    </div>
  );
}

export default function ResultsDashboard({ analysis }: ResultsDashboardProps) {
  const [activePhase, setActivePhase] = useState<SwingPhase>("address");
  const [shareOpen, setShareOpen] = useState(false);

  // Determine the single view from the data (whichever key exists)
  const activeView: VideoAngle = analysis.user_angles.dtl ? "dtl" : "fo";
  const viewLabel = activeView === "dtl" ? "Down the Line" : "Face On";

  const hasVideos = analysis.video_urls && analysis.reference_video_urls;
  const score = analysis.similarity_score ?? 0;

  return (
    <div className="min-h-screen px-6 py-6">
      <div className="mx-auto max-w-6xl space-y-6">
        {/* Hero header */}
        <div className="relative overflow-hidden rounded-xl border border-cream/8 bg-gradient-to-b from-cream/[0.04] to-transparent p-6 md:p-8">
          {/* Subtle background glow */}
          <div className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 w-96 h-96 rounded-full bg-forest-green/8 blur-3xl" />

          <div className="relative flex flex-col md:flex-row items-center gap-8">
            {/* Score ring */}
            <ScoreRing score={score} />

            {/* Text content */}
            <div className="flex-1 text-center md:text-left">
              <h1 className="text-2xl md:text-3xl font-bold mb-1">
                Swing Analysis
              </h1>
              <p className="text-forest-green font-semibold text-sm mb-3">
                {score}% similarity to Tiger Woods
              </p>
              <div className="flex flex-wrap justify-center md:justify-start gap-x-3 gap-y-1 text-xs text-cream/40">
                <span>
                  {analysis.swing_type.charAt(0).toUpperCase() +
                    analysis.swing_type.slice(1)}{" "}
                  swing
                </span>
                <span className="text-cream/15">·</span>
                <span>{viewLabel}</span>
                <span className="text-cream/15">·</span>
                <span>vs Tiger Woods 2000</span>
                <span className="text-cream/15">·</span>
                <span>{analysis.processing_time_sec}s</span>
              </div>
            </div>

            {/* Share button */}
            <div className="shrink-0">
              <button
                onClick={() => setShareOpen(true)}
                className="group flex items-center gap-2.5 rounded-lg border border-cream/10 bg-cream/5 px-5 py-3 text-sm font-medium transition-all hover:bg-cardinal-red hover:border-cardinal-red hover:text-cream"
              >
                <svg
                  className="w-4 h-4 text-cream/50 group-hover:text-cream transition-colors"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                  />
                </svg>
                Share Results
              </button>
            </div>
          </div>
        </div>

        {/* Share Modal */}
        <ShareModal
          uploadId={analysis.upload_id}
          view={activeView}
          isOpen={shareOpen}
          onClose={() => setShareOpen(false)}
        />

        {/* Side-by-side video comparison */}
        {hasVideos && (
          <VideoComparison
            videoUrls={analysis.video_urls!}
            referenceVideoUrls={analysis.reference_video_urls!}
            userAngles={analysis.user_angles}
            referenceAngles={analysis.reference_angles}
            activeView={activeView}
            activePhase={activePhase}
            onPhaseChange={setActivePhase}
            userPhaseLandmarks={analysis.user_phase_landmarks}
            referencePhaseLandmarks={analysis.reference_phase_landmarks}
            userAllLandmarks={analysis.user_all_landmarks}
            userPhaseImages={analysis.user_phase_images}
            referencePhaseImages={analysis.reference_phase_images}
          />
        )}

        {/* Phase timeline */}
        <div className="px-4">
          <PhaseTimeline
            activePhase={activePhase}
            onPhaseChange={(phase) => {
              setActivePhase(phase);
            }}
          />
        </div>

        {/* Top 3 differences */}
        <div>
          <h2 className="text-sm font-semibold mb-3 text-cream/60 uppercase tracking-wide">
            Top Areas for Improvement
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {analysis.top_differences.map((diff) => (
              <DifferenceCard key={diff.rank} diff={diff} />
            ))}
          </div>
        </div>

        {/* Angle comparison table */}
        <AngleComparisonTable
          userAngles={analysis.user_angles}
          referenceAngles={analysis.reference_angles}
          deltas={analysis.deltas}
          activePhase={activePhase}
          topDifferences={analysis.top_differences}
        />

        {/* Actions */}
        <div className="flex justify-center pt-4">
          <Link href="/upload">
            <Button variant="secondary" className="px-8 py-3">
              Analyze Another Swing
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
