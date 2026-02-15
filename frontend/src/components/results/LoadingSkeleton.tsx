export default function LoadingSkeleton() {
  return (
    <div className="min-h-screen px-6 py-6">
      <div className="mx-auto max-w-6xl animate-pulse space-y-6">
        {/* Header */}
        <div className="text-center space-y-3">
          <div className="h-8 w-64 bg-cream/5 rounded mx-auto" />
          <div className="h-4 w-48 bg-cream/5 rounded mx-auto" />
        </div>

        {/* View toggle */}
        <div className="flex justify-center">
          <div className="h-10 w-56 bg-cream/5 rounded-lg" />
        </div>

        {/* Videos */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="h-4 w-24 bg-cream/5 rounded" />
            <div className="aspect-video bg-cream/5 rounded-lg" />
          </div>
          <div className="space-y-2">
            <div className="h-4 w-32 bg-cream/5 rounded" />
            <div className="aspect-video bg-cream/5 rounded-lg" />
          </div>
        </div>

        {/* Phase timeline */}
        <div className="flex items-center justify-between px-8">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex flex-col items-center gap-2">
              <div className="w-10 h-10 rounded-full bg-cream/5" />
              <div className="h-3 w-16 bg-cream/5 rounded" />
            </div>
          ))}
        </div>

        {/* Difference cards */}
        <div className="space-y-3">
          <div className="h-5 w-48 bg-cream/5 rounded" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-48 bg-cream/5 rounded-lg" />
            ))}
          </div>
        </div>

        {/* Angle table */}
        <div className="space-y-3">
          <div className="h-5 w-40 bg-cream/5 rounded" />
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-10 bg-cream/5 rounded" />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
