/**
 * Centralized Segment analytics module.
 *
 * Every component imports typed track functions from here — no raw
 * analytics.track() calls are scattered across the codebase.
 *
 * Lazy-loaded: AnalyticsBrowser.load() is called on first use, never
 * during SSR. No-ops gracefully when NEXT_PUBLIC_SEGMENT_WRITE_KEY is
 * missing (local dev without Segment configured).
 */

import { AnalyticsBrowser } from "@segment/analytics-next";

// ─── Singleton ───────────────────────────────────────────────────

let analyticsInstance: AnalyticsBrowser | null = null;

function getAnalytics(): AnalyticsBrowser | null {
  if (analyticsInstance) return analyticsInstance;

  const writeKey = process.env.NEXT_PUBLIC_SEGMENT_WRITE_KEY;
  if (!writeKey) return null;

  analyticsInstance = AnalyticsBrowser.load({ writeKey });
  return analyticsInstance;
}

// ─── Identity ────────────────────────────────────────────────────

export function identifyUser(userId: string, traits?: Record<string, unknown>) {
  getAnalytics()?.identify(userId, traits);
}

export function resetIdentity() {
  getAnalytics()?.reset();
}

// ─── Page Views ──────────────────────────────────────────────────

export function trackPageView(pageName: string) {
  getAnalytics()?.page(pageName, { page_name: pageName });
}

// ─── Typed Event Functions ───────────────────────────────────────

export function trackCTAClicked(props: {
  cta_text: string;
  cta_location: "hero" | "header";
  destination: string;
}) {
  getAnalytics()?.track("CTA Clicked", props);
}

export function trackAuthInitiated(props: {
  auth_type: "sign_up" | "sign_in";
  source: "header" | "hero";
}) {
  getAnalytics()?.track("Auth Initiated", props);
}

export function trackViewSelected(props: {
  view: "dtl" | "fo";
  previous_view: "dtl" | "fo";
}) {
  getAnalytics()?.track("View Selected", props);
}

export function trackVideoDropped(props: {
  file_size_bytes: number;
  file_type: string;
  duration_seconds: number | null;
  view: "dtl" | "fo";
  valid: boolean;
  error?: string;
}) {
  getAnalytics()?.track("Video Dropped", props);
}

export function trackUploadStarted(props: {
  swing_type: string;
  view: "dtl" | "fo";
  file_size_bytes: number;
}) {
  getAnalytics()?.track("Upload Started", props);
}

export function trackUploadCompleted(props: {
  swing_type: string;
  view: "dtl" | "fo";
  file_size_bytes: number;
  upload_id: string;
}) {
  getAnalytics()?.track("Upload Completed", props);
}

export function trackUploadFailed(props: {
  swing_type: string;
  view: "dtl" | "fo";
  error_message: string;
}) {
  getAnalytics()?.track("Upload Failed", props);
}

export function trackAnalysisStarted(props: {
  upload_id: string;
  swing_type: string;
  view: "dtl" | "fo";
}) {
  getAnalytics()?.track("Analysis Started", props);
}

export function trackResultsViewed(props: {
  upload_id: string;
  similarity_score: number;
  swing_type: string;
  view: "dtl" | "fo";
  processing_time_sec: number;
}) {
  getAnalytics()?.track("Results Viewed", props);
}

export function trackPhaseTabSwitched(props: {
  phase: string;
  previous_phase: string;
  upload_id: string;
}) {
  getAnalytics()?.track("Phase Tab Switched", props);
}

export function trackShareButtonClicked(props: {
  upload_id: string;
  view: "dtl" | "fo";
}) {
  getAnalytics()?.track("Share Button Clicked", props);
}

export function trackShareLinkCopied(props: {
  upload_id: string;
  share_token: string;
}) {
  getAnalytics()?.track("Share Link Copied", props);
}

export function trackShareImageDownloaded(props: {
  upload_id: string;
  share_token: string;
}) {
  getAnalytics()?.track("Share Image Downloaded", props);
}

export function trackSocialShareClicked(props: {
  platform: "twitter" | "facebook";
  upload_id: string;
  share_token: string;
}) {
  getAnalytics()?.track("Social Share Clicked", props);
}

export function trackAnalyzeAnotherClicked(props: {
  from_upload_id: string;
}) {
  getAnalytics()?.track("Analyze Another Clicked", props);
}
