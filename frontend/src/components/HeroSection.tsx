"use client";

import { useEffect } from "react";
import Link from "next/link";
import { useUser } from "@propelauth/nextjs/client";
import { trackPageView, trackCTAClicked, trackAuthInitiated } from "@/lib/analytics";

export default function HeroSection() {
  const { loading, user } = useUser();

  useEffect(() => {
    trackPageView("Home");
  }, []);

  return (
    <section className="relative min-h-screen flex items-center justify-center px-6">
      <div className="absolute inset-0 bg-gradient-to-b from-blue-charcoal via-blue-charcoal to-blue-charcoal/95" />
      <div className="relative z-10 text-center max-w-3xl mx-auto">
        <h1 className="text-6xl md:text-8xl font-bold tracking-tight mb-6">
          <span className="text-pastel-yellow">Swing</span>{" "}
          <span className="text-white">pure</span>
        </h1>
        <p className="text-cream/70 text-lg md:text-xl leading-relaxed mb-8 max-w-xl mx-auto">
          Compare your swing to Tiger Woods&apos; iconic 2000 form. See exactly
          where to improve with AI-powered analysis.
        </p>
        <Link
          href={loading ? "#" : user ? "/upload" : "/api/auth/signup"}
          className="inline-block bg-cardinal-red text-cream px-8 py-3 rounded-lg text-base font-semibold hover:bg-cardinal-red/90 transition-colors"
          aria-disabled={loading}
          onClick={() => {
            const dest = user ? "/upload" : "/api/auth/signup";
            trackCTAClicked({
              cta_text: user ? "Start Your Analysis" : "Get Started",
              cta_location: "hero",
              destination: dest,
            });
            if (!user) {
              trackAuthInitiated({ auth_type: "sign_up", source: "hero" });
            }
          }}
        >
          {loading ? "Get Started" : user ? "Start Your Analysis" : "Get Started"}
        </Link>
      </div>
    </section>
  );
}
