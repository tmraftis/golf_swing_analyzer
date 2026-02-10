import Link from "next/link";

export default function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-charcoal via-blue-charcoal to-blue-charcoal/95" />
      <div className="relative z-10 text-center max-w-3xl mx-auto">
        <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-6">
          Swing{" "}
          <span className="text-pastel-yellow">pure</span>
        </h1>
        <p className="text-cream/70 text-lg md:text-xl leading-relaxed mb-10 max-w-xl mx-auto">
          Compare your swing to Tiger Woods&apos; iconic 2000 form. See exactly
          where to improve with AI-powered pose analysis.
        </p>
        <Link
          href="/upload"
          className="inline-block bg-cardinal-red text-cream px-8 py-4 rounded-lg text-lg font-semibold hover:bg-cardinal-red/90 transition-colors"
        >
          Start Your Analysis
        </Link>
      </div>
    </section>
  );
}
