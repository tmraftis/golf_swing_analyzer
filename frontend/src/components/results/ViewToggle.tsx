import type { VideoAngle } from "@/types";

interface ViewToggleProps {
  activeView: VideoAngle;
  onViewChange: (view: VideoAngle) => void;
}

const VIEWS: { value: VideoAngle; label: string }[] = [
  { value: "dtl", label: "Down the Line" },
  { value: "fo", label: "Face On" },
];

export default function ViewToggle({
  activeView,
  onViewChange,
}: ViewToggleProps) {
  return (
    <div className="inline-flex rounded-lg bg-cream/5 p-1">
      {VIEWS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onViewChange(value)}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
            activeView === value
              ? "bg-forest-green text-cream"
              : "text-cream/50 hover:text-cream/80"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
