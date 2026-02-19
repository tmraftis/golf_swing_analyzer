import type { TopDifference } from "@/types";
import { PHASE_LABELS, type SwingPhase } from "@/types";

export const SEVERITY_COLORS = {
  major: {
    border: "border-cardinal-red/50",
    bg: "bg-cardinal-red/5",
    badge: "bg-cardinal-red/20 text-cardinal-red",
  },
  moderate: {
    border: "border-pastel-yellow/50",
    bg: "bg-pastel-yellow/5",
    badge: "bg-pastel-yellow/20 text-pastel-yellow",
  },
  minor: {
    border: "border-cream/30",
    bg: "bg-cream/5",
    badge: "bg-cream/20 text-cream/70",
  },
};

interface DifferenceCardProps {
  diff: TopDifference;
  onClick?: () => void;
}

export default function DifferenceCard({ diff, onClick }: DifferenceCardProps) {
  const colors = SEVERITY_COLORS[diff.severity];
  const phaseLabel =
    PHASE_LABELS[diff.phase as SwingPhase] ?? diff.phase;

  return (
    <div
      className={`rounded-lg border ${colors.border} ${colors.bg} p-5 ${
        onClick ? "cursor-pointer hover:bg-cream/5 transition-colors" : ""
      }`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-cream/30">
            #{diff.rank}
          </span>
          <div>
            <h4 className="font-semibold leading-tight">
              {diff.title}
            </h4>
            <div className="flex items-center gap-2 mt-1">
              <span className="text-xs text-cream/40 uppercase tracking-wide">
                {phaseLabel}
              </span>
              <span className="text-xs text-cream/20">·</span>
              <span className="text-xs text-cream/40 uppercase tracking-wide">
                {diff.view === "dtl" ? "Down the Line" : "Face On"}
              </span>
            </div>
          </div>
        </div>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full uppercase tracking-wide ${colors.badge}`}
        >
          {diff.severity}
        </span>
      </div>

      <p className="text-sm text-cream/70 mb-4 leading-relaxed">
        {diff.description}
      </p>

      <div className="rounded-lg bg-forest-green/10 border border-forest-green/20 p-4">
        <div className="flex items-start gap-2">
          <svg
            className="w-4 h-4 text-forest-green mt-0.5 shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a.75.75 0 000 1.5h.253a.25.25 0 01.244.304l-.459 2.066A1.75 1.75 0 0010.747 15H11a.75.75 0 000-1.5h-.253a.25.25 0 01-.244-.304l.459-2.066A1.75 1.75 0 009.253 9H9z" />
          </svg>
          <p className="text-sm text-cream/80">{diff.coaching_tip}</p>
        </div>
      </div>
    </div>
  );
}
