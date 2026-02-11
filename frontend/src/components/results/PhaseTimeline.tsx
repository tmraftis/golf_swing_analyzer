import { SWING_PHASES, PHASE_LABELS, type SwingPhase } from "@/types";

interface PhaseTimelineProps {
  activePhase: SwingPhase;
  onPhaseChange: (phase: SwingPhase) => void;
}

export default function PhaseTimeline({
  activePhase,
  onPhaseChange,
}: PhaseTimelineProps) {
  const activeIdx = SWING_PHASES.indexOf(activePhase);

  return (
    <div className="flex items-center justify-between w-full">
      {SWING_PHASES.map((phase, idx) => {
        const isActive = phase === activePhase;
        const isPast = idx < activeIdx;

        return (
          <div key={phase} className="flex items-center flex-1 last:flex-none">
            {/* Node */}
            <button
              onClick={() => onPhaseChange(phase)}
              className="flex flex-col items-center gap-2 group"
            >
              <div
                className={`w-10 h-10 rounded-full border-2 flex items-center justify-center text-sm font-semibold transition-all ${
                  isActive
                    ? "border-pastel-yellow bg-pastel-yellow/20 text-pastel-yellow"
                    : isPast
                      ? "border-forest-green bg-forest-green/20 text-forest-green"
                      : "border-cream/20 text-cream/30 group-hover:border-cream/40 group-hover:text-cream/50"
                }`}
              >
                {idx + 1}
              </div>
              <span
                className={`text-xs font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? "text-pastel-yellow"
                    : isPast
                      ? "text-forest-green"
                      : "text-cream/40 group-hover:text-cream/60"
                }`}
              >
                {PHASE_LABELS[phase]}
              </span>
            </button>

            {/* Connector line */}
            {idx < SWING_PHASES.length - 1 && (
              <div className="flex-1 mx-3 mt-[-1.5rem]">
                <div
                  className={`h-0.5 rounded ${
                    idx < activeIdx ? "bg-forest-green" : "bg-cream/15"
                  }`}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
