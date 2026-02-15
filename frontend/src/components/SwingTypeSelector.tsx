"use client";

import type { SwingType } from "@/types";

interface SwingTypeSelectorProps {
  selected: SwingType;
  onSelect: (type: SwingType) => void;
}

export default function SwingTypeSelector({
  selected,
  onSelect,
}: SwingTypeSelectorProps) {
  return (
    <div className="grid grid-cols-2 gap-3">
      {/* Iron — active */}
      <button
        onClick={() => onSelect("iron")}
        className={`relative rounded-lg border-2 p-4 text-left transition-colors ${
          selected === "iron"
            ? "border-forest-green bg-forest-green/10"
            : "border-cream/15 hover:border-cream/30"
        }`}
      >
        <h3 className="font-semibold mb-0.5">Iron</h3>
        <p className="text-xs text-cream/50">
          Compare to Tiger&apos;s 2000 form
        </p>
        {selected === "iron" && (
          <div className="absolute top-3 right-3">
            <svg className="w-4 h-4 text-forest-green" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
            </svg>
          </div>
        )}
      </button>

      {/* Driver — coming soon */}
      <div className="relative rounded-lg border-2 border-cream/10 p-4 text-left opacity-50 cursor-not-allowed">
        <div className="absolute top-3 right-3">
          <span className="bg-pastel-yellow text-blue-charcoal text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap">
            Soon
          </span>
        </div>
        <h3 className="font-semibold mb-0.5">Driver</h3>
        <p className="text-xs text-cream/50">
          Coming soon
        </p>
      </div>
    </div>
  );
}
