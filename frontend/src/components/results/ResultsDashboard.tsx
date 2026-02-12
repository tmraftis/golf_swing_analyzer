"use client";

import { useState } from "react";
import Link from "next/link";
import type { AnalysisResponse, VideoAngle, SwingPhase } from "@/types";
import VideoComparison from "./VideoComparison";
import PhaseTimeline from "./PhaseTimeline";
import DifferenceCard from "./DifferenceCard";
import AngleComparisonTable from "./AngleComparisonTable";
import Button from "@/components/Button";

interface ResultsDashboardProps {
  analysis: AnalysisResponse;
}

export default function ResultsDashboard({ analysis }: ResultsDashboardProps) {
  const [activePhase, setActivePhase] = useState<SwingPhase>("address");

  // Determine the single view from the data (whichever key exists)
  const activeView: VideoAngle = analysis.user_angles.dtl ? "dtl" : "fo";
  const viewLabel = activeView === "dtl" ? "Down the Line" : "Face On";

  const hasVideos = analysis.video_urls && analysis.reference_video_urls;

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto max-w-6xl space-y-10">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold mb-2">Swing Analysis</h1>
          <p className="text-cream/50 text-sm">
            {analysis.swing_type.charAt(0).toUpperCase() +
              analysis.swing_type.slice(1)}{" "}
            swing · {viewLabel} · Processed in {analysis.processing_time_sec}s ·
            Compared to Tiger Woods&apos; 2000 {analysis.swing_type}
          </p>
        </div>

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
          <h2 className="text-lg font-semibold mb-4">
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
