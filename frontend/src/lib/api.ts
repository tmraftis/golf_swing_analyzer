import { API_URL } from "./constants";
import type { SwingType, VideoAngle, UploadResponse, AnalysisResponse } from "@/types";

function authHeaders(accessToken?: string): Record<string, string> {
  const headers: Record<string, string> = {};
  if (accessToken) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }
  return headers;
}

export async function uploadVideo(
  swingType: SwingType,
  view: VideoAngle,
  videoFile: File,
  accessToken?: string
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("swing_type", swingType);
  formData.append("view", view);
  formData.append("video", videoFile);

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: formData,
  });

  const data: UploadResponse = await res.json();

  if (!res.ok) {
    throw new Error(data.detail || "Upload failed. Please try again.");
  }

  return data;
}

export async function analyzeSwing(
  uploadId: string,
  swingType: SwingType = "iron",
  view: VideoAngle = "dtl",
  accessToken?: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_URL}/api/analyze/${uploadId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(accessToken),
    },
    body: JSON.stringify({ swing_type: swingType, view }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(data.detail || `Analysis failed (${res.status})`);
  }

  return res.json();
}

export async function getAnalysis(
  uploadId: string,
  view: VideoAngle = "dtl",
  accessToken?: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_URL}/api/analysis/${uploadId}?view=${view}`, {
    headers: authHeaders(accessToken),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Not found" }));
    throw new Error(data.detail || `Analysis not found (${res.status})`);
  }

  return res.json();
}

export function getVideoUrl(relativePath: string): string {
  return `${API_URL}${relativePath}`;
}
