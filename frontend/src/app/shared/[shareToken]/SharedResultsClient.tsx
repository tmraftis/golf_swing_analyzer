"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { getSharedAnalysis, getVideoUrl } from "@/lib/api";
import type { SharedAnalysis, SwingPhase } from "@/types";
import { PHASE_LABELS } from "@/types";
import DifferenceCard from "@/components/results/DifferenceCard";
import Button from "@/components/Button";
import { trackPageView } from "@/lib/analytics";

interface SharedResultsClientProps {
  shareToken: string;
}

export default function SharedResultsClient({
  shareToken,
}: SharedResultsClientProps) {
  const [data, setData] = useState<SharedAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activePhase, setActivePhase] = useState<SwingPhase>("impact");

  useEffect(() => {
    trackPageView("Shared Results");
    getSharedAnalysis(shareToken)
      .then(setData)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [shareToken]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <svg
            className="animate-spin h-10 w-10 text-cream/30 mx-auto mb-4"
            viewBox="0 0 24 24"
            fill="none"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
          <p className="text-cream/50">Loading swing analysis...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center max-w-md mx-auto px-6">
          <div className="w-16 h-16 rounded-full bg-cream/5 flex items-center justify-center mx-auto mb-6">
            <svg
              className="w-8 h-8 text-cream/30"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
              />
            </svg>
          </div>
          <h2 className="text-xl font-bold mb-2">Analysis Unavailable</h2>
          <p className="text-cream/50 text-sm mb-8">
            {error ||
              "This swing analysis has expired or been made private."}
          </p>
          <Link href="/">
            <Button variant="primary" className="px-8">
              Analyze Your Own Swing
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  const viewLabel = data.view === "dtl" ? "Down the Line" : "Face On";

  // Get phase images for the active phase
  const userPhaseImages = data.user_phase_images?.[data.view as "dtl" | "fo"];
  const refPhaseImages =
    data.reference_phase_images?.[data.view as "dtl" | "fo"];

  const userImgUrl = userPhaseImages?.[activePhase]
    ? getVideoUrl(userPhaseImages[activePhase]!)
    : null;
  const refImgUrl = refPhaseImages?.[activePhase]
    ? getVideoUrl(refPhaseImages[activePhase]!)
    : null;

  return (
    <div className="min-h-screen px-6 py-6">
      <div className="mx-auto max-w-4xl space-y-6">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-2">Swing Analysis</h1>
          <p className="text-5xl font-bold text-forest-green mb-2">
            {data.similarity_score}%
          </p>
          <p className="text-cream/50 text-sm">
            Similarity to Tiger Woods · {viewLabel} ·{" "}
            {data.swing_type.charAt(0).toUpperCase() +
              data.swing_type.slice(1)}{" "}
            swing
          </p>
        </div>

        {/* Phase selector */}
        <div className="flex justify-center gap-2">
          {(
            ["address", "top", "impact", "follow_through"] as SwingPhase[]
          ).map((phase) => (
            <button
              key={phase}
              onClick={() => setActivePhase(phase)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors ${
                activePhase === phase
                  ? "bg-forest-green text-cream"
                  : "bg-cream/5 text-cream/50 hover:bg-cream/10"
              }`}
            >
              {PHASE_LABELS[phase]}
            </button>
          ))}
        </div>

        {/* Side-by-side phase images */}
        {(userImgUrl || refImgUrl) && (
          <div className="grid grid-cols-2 gap-4">
            <div className="relative rounded-lg overflow-hidden bg-cream/5 aspect-[3/4]">
              {userImgUrl ? (
                <img
                  src={userImgUrl}
                  alt={`User swing at ${PHASE_LABELS[activePhase]}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-cream/30">
                  No image
                </div>
              )}
              <span className="absolute bottom-3 left-3 px-3 py-1 rounded-md bg-blue-charcoal/80 text-xs font-medium">
                User
              </span>
            </div>
            <div className="relative rounded-lg overflow-hidden bg-cream/5 aspect-[3/4]">
              {refImgUrl ? (
                <img
                  src={refImgUrl}
                  alt={`Tiger Woods at ${PHASE_LABELS[activePhase]}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-cream/30">
                  No image
                </div>
              )}
              <span className="absolute bottom-3 left-3 px-3 py-1 rounded-md bg-blue-charcoal/80 text-xs font-medium">
                Tiger Woods
              </span>
            </div>
          </div>
        )}

        {/* Top differences */}
        {data.top_differences.length > 0 && (
          <div>
            <h2 className="text-sm font-semibold mb-3 text-cream/60 uppercase tracking-wide">
              Top Areas for Improvement
            </h2>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {data.top_differences.map((diff) => (
                <DifferenceCard key={diff.rank} diff={diff} />
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div className="rounded-xl border border-forest-green/30 bg-forest-green/5 p-6 text-center">
          <h3 className="text-lg font-bold mb-2">
            Think you can beat this score?
          </h3>
          <p className="text-cream/60 text-sm mb-5">
            Upload your own swing and see how you compare to Tiger Woods.
          </p>
          <Link href="/">
            <Button variant="primary" className="px-10 py-3 text-base">
              Analyze Your Swing — Free
            </Button>
          </Link>
        </div>

        {/* Branding footer */}
        <div className="text-center text-cream/30 text-xs">
          Powered by{" "}
          <Link href="/" className="text-cream/50 hover:text-cream underline">
            Pure
          </Link>{" "}
          — Swing pure.
        </div>
      </div>
    </div>
  );
}
