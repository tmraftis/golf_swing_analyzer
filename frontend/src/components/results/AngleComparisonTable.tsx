"use client";

import { useState } from "react";
import type {
  AngleData,
  DeltaData,
  SwingPhase,
  TopDifference,
  VideoAngle,
} from "@/types";
import { ANGLE_DISPLAY_NAMES, PHASE_LABELS } from "@/types";

interface AngleComparisonTableProps {
  userAngles: AngleData;
  referenceAngles: AngleData;
  deltas: DeltaData;
  activePhase: SwingPhase;
  topDifferences: TopDifference[];
}

interface AngleRow {
  angleName: string;
  displayName: string;
  view: VideoAngle;
  userVal: number;
  refVal: number | undefined;
  delta: number | undefined;
  isTopDiff: boolean;
  severity?: "major" | "moderate" | "minor";
}

function getDeltaColor(delta: number | undefined): string {
  if (delta === undefined) return "text-cream/40";
  const abs = Math.abs(delta);
  if (abs > 15) return "text-cardinal-red";
  if (abs > 8) return "text-pastel-yellow";
  return "text-cream/60";
}

function formatDelta(delta: number | undefined): string {
  if (delta === undefined) return "—";
  return `${delta > 0 ? "+" : ""}${delta.toFixed(1)}°`;
}

export default function AngleComparisonTable({
  userAngles,
  referenceAngles,
  deltas,
  activePhase,
  topDifferences,
}: AngleComparisonTableProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Build rows for the active phase across both views
  const rows: AngleRow[] = [];
  const availableViews = (["dtl", "fo"] as const).filter(v => userAngles[v]);
  for (const view of availableViews) {
    const phaseData = userAngles[view]?.[activePhase];
    const refData = referenceAngles[view]?.[activePhase];
    if (!phaseData) continue;

    for (const [angleName, userVal] of Object.entries(phaseData.angles)) {
      // Skip geometry metrics that aren't angles
      if (
        angleName.includes("width") ||
        angleName.includes("offset")
      )
        continue;

      const refVal = refData?.angles?.[angleName];
      const delta = deltas[view]?.[activePhase]?.[angleName];

      const topDiff = topDifferences.find(
        (d) =>
          d.angle_name === angleName &&
          d.phase === activePhase &&
          d.view === view
      );

      rows.push({
        angleName,
        displayName: ANGLE_DISPLAY_NAMES[angleName] ?? angleName,
        view,
        userVal,
        refVal,
        delta,
        isTopDiff: !!topDiff,
        severity: topDiff?.severity,
      });
    }
  }

  // Sort: top differences first, then by delta magnitude
  rows.sort((a, b) => {
    if (a.isTopDiff && !b.isTopDiff) return -1;
    if (!a.isTopDiff && b.isTopDiff) return 1;
    return (
      Math.abs(b.delta ?? 0) - Math.abs(a.delta ?? 0)
    );
  });

  const SEVERITY_BORDER: Record<string, string> = {
    major: "border-l-cardinal-red",
    moderate: "border-l-pastel-yellow",
    minor: "border-l-cream/40",
  };

  return (
    <div>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm font-medium text-cream/60 hover:text-cream/80 transition-colors mb-4"
      >
        <svg
          className={`w-4 h-4 transition-transform ${isExpanded ? "rotate-90" : ""}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
            clipRule="evenodd"
          />
        </svg>
        Angle Comparison — {PHASE_LABELS[activePhase]}
        <span className="text-cream/30">({rows.length} angles)</span>
      </button>

      {isExpanded && (
        <>
          {/* Desktop table */}
          <div className="hidden md:block rounded-lg border border-cream/10 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-cream/10 bg-cream/3">
                  <th className="text-left px-4 py-3 font-medium text-cream/50">
                    Angle
                  </th>
                  <th className="text-left px-4 py-3 font-medium text-cream/50">
                    View
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-cream/50">
                    You
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-cream/50">
                    Tiger
                  </th>
                  <th className="text-right px-4 py-3 font-medium text-cream/50">
                    Diff
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row) => (
                  <tr
                    key={`${row.view}-${row.angleName}`}
                    className={`border-b border-cream/5 hover:bg-cream/3 transition-colors ${
                      row.isTopDiff
                        ? `border-l-2 ${SEVERITY_BORDER[row.severity ?? "minor"]}`
                        : ""
                    }`}
                  >
                    <td className="px-4 py-3 font-medium">
                      {row.displayName}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`text-xs px-2 py-0.5 rounded-full ${
                          row.view === "dtl"
                            ? "bg-cream/10 text-cream/60"
                            : "bg-cream/10 text-cream/60"
                        }`}
                      >
                        {row.view === "dtl" ? "DTL" : "FO"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right font-mono">
                      {row.userVal.toFixed(1)}&deg;
                    </td>
                    <td className="px-4 py-3 text-right font-mono text-pastel-yellow">
                      {row.refVal !== undefined
                        ? `${row.refVal.toFixed(1)}°`
                        : "—"}
                    </td>
                    <td
                      className={`px-4 py-3 text-right font-mono font-medium ${getDeltaColor(row.delta)}`}
                    >
                      {formatDelta(row.delta)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile cards */}
          <div className="md:hidden space-y-2">
            {rows.map((row) => (
              <div
                key={`${row.view}-${row.angleName}`}
                className={`rounded-lg bg-cream/3 p-3 ${
                  row.isTopDiff
                    ? `border-l-2 ${SEVERITY_BORDER[row.severity ?? "minor"]}`
                    : ""
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium text-sm">
                    {row.displayName}
                  </span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-cream/10 text-cream/50">
                    {row.view === "dtl" ? "DTL" : "FO"}
                  </span>
                </div>
                <div className="flex items-center gap-4 text-sm">
                  <div>
                    <span className="text-cream/40 text-xs">You </span>
                    <span className="font-mono">
                      {row.userVal.toFixed(1)}&deg;
                    </span>
                  </div>
                  <div>
                    <span className="text-cream/40 text-xs">Tiger </span>
                    <span className="font-mono text-pastel-yellow">
                      {row.refVal !== undefined
                        ? `${row.refVal.toFixed(1)}°`
                        : "—"}
                    </span>
                  </div>
                  <div>
                    <span className="text-cream/40 text-xs">Diff </span>
                    <span
                      className={`font-mono font-medium ${getDeltaColor(row.delta)}`}
                    >
                      {formatDelta(row.delta)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
