export const BRAND = {
  name: "Pure",
  tagline: "Swing pure",
} as const;

export const ACCEPTED_VIDEO_TYPES = ["video/mp4", "video/quicktime"];
export const ACCEPTED_EXTENSIONS = [".mp4", ".mov"];
export const MAX_DURATION_SECONDS = 30;
export const MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024; // 100MB
export const SWING_TYPES = ["iron", "driver"] as const;

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
