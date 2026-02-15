"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useUser } from "@propelauth/nextjs/client";
import { createShare, getShareImageUrl } from "@/lib/api";
import { API_URL } from "@/lib/constants";
import type { ShareResponse, VideoAngle } from "@/types";
import Button from "@/components/Button";

interface ShareModalProps {
  uploadId: string;
  view: VideoAngle;
  isOpen: boolean;
  onClose: () => void;
}

export default function ShareModal({
  uploadId,
  view,
  isOpen,
  onClose,
}: ShareModalProps) {
  const { accessToken } = useUser();
  const [share, setShare] = useState<ShareResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const backdropRef = useRef<HTMLDivElement>(null);

  // Create share token on mount
  useEffect(() => {
    if (!isOpen || share || loading) return;

    setLoading(true);
    setError(null);

    createShare(uploadId, view, accessToken ?? undefined)
      .then(setShare)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [isOpen, uploadId, view, accessToken, share, loading]);

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setCopied(false);
      setError(null);
    }
  }, [isOpen]);

  // Close on Escape key
  useEffect(() => {
    function handleEscape(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [isOpen, onClose]);

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === backdropRef.current) onClose();
    },
    [onClose]
  );

  const handleCopyLink = useCallback(async () => {
    if (!share) return;
    try {
      await navigator.clipboard.writeText(share.share_url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Fallback for non-HTTPS contexts
      const input = document.createElement("input");
      input.value = share.share_url;
      document.body.appendChild(input);
      input.select();
      document.execCommand("copy");
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    }
  }, [share]);

  const handleDownloadImage = useCallback(async () => {
    if (!share) return;
    setDownloading(true);
    try {
      const url = getShareImageUrl(share.share_token);
      const res = await fetch(url);
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `pure-swing-${share.share_token.slice(0, 8)}.png`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(a.href);
    } catch {
      setError("Failed to download image. Please try again.");
    } finally {
      setDownloading(false);
    }
  }, [share]);

  const shareUrl = share?.share_url ?? "";

  const twitterUrl = share
    ? `https://twitter.com/intent/tweet?text=${encodeURIComponent(
        "Check out my golf swing analysis vs Tiger Woods! \u26f3"
      )}&url=${encodeURIComponent(shareUrl)}`
    : "#";

  const facebookUrl = share
    ? `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(
        shareUrl
      )}`
    : "#";

  if (!isOpen) return null;

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-lg mx-4 rounded-xl border border-cream/10 bg-blue-charcoal p-6 shadow-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-cream/40 hover:text-cream transition-colors"
          aria-label="Close share modal"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        <h2 className="text-xl font-bold mb-2">Share Your Results</h2>
        <p className="text-cream/50 text-sm mb-5">
          Show off your swing analysis and challenge friends to beat your score.
        </p>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <svg className="animate-spin h-8 w-8 text-cream/40" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        )}

        {error && (
          <div className="rounded-lg bg-cardinal-red/10 border border-cardinal-red/30 p-4 mb-4">
            <p className="text-sm text-cardinal-red">{error}</p>
          </div>
        )}

        {share && !loading && (
          <div className="space-y-4">
            {/* Download Image */}
            <button
              onClick={handleDownloadImage}
              disabled={downloading}
              className="w-full flex items-center gap-4 rounded-lg border border-cream/10 bg-cream/5 p-4 hover:bg-cream/10 transition-colors text-left"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-forest-green/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-forest-green" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-sm">
                  {downloading ? "Generating..." : "Download Image"}
                </h3>
                <p className="text-xs text-cream/40">
                  1080x1080 branded PNG — perfect for Instagram
                </p>
              </div>
            </button>

            {/* Copy Link */}
            <button
              onClick={handleCopyLink}
              className="w-full flex items-center gap-4 rounded-lg border border-cream/10 bg-cream/5 p-4 hover:bg-cream/10 transition-colors text-left"
            >
              <div className="flex-shrink-0 w-12 h-12 rounded-lg bg-pastel-yellow/20 flex items-center justify-center">
                <svg className="w-6 h-6 text-pastel-yellow" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-sm">
                  {copied ? "Copied!" : "Copy Link"}
                </h3>
                <p className="text-xs text-cream/40">
                  Share a public results page with anyone
                </p>
              </div>
            </button>

            {/* Social Share Buttons */}
            <div className="flex gap-3 pt-2">
              <a
                href={twitterUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-cream/10 bg-cream/5 py-3 text-sm font-medium hover:bg-cream/10 transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                </svg>
                Post on X
              </a>
              <a
                href={facebookUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-cream/10 bg-cream/5 py-3 text-sm font-medium hover:bg-cream/10 transition-colors"
              >
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
                Share
              </a>
            </div>

            {/* Share URL (copyable) */}
            <div className="mt-2 rounded-lg bg-cream/5 border border-cream/10 p-3">
              <p className="text-xs text-cream/30 mb-1">Share URL</p>
              <p className="text-xs text-cream/60 font-mono break-all select-all">
                {share.share_url}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
