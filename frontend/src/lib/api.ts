import { API_URL } from "./constants";
import type { SwingType, UploadResponse, AnalysisResponse } from "@/types";

export async function uploadVideos(
  swingType: SwingType,
  dtlFile: File,
  foFile: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("swing_type", swingType);
  formData.append("video_dtl", dtlFile);
  formData.append("video_fo", foFile);

  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
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
  swingType: SwingType = "iron"
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_URL}/api/analyze/${uploadId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ swing_type: swingType }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Analysis failed" }));
    throw new Error(data.detail || `Analysis failed (${res.status})`);
  }

  return res.json();
}

export async function getAnalysis(
  uploadId: string
): Promise<AnalysisResponse> {
  const res = await fetch(`${API_URL}/api/analysis/${uploadId}`);

  if (!res.ok) {
    const data = await res.json().catch(() => ({ detail: "Not found" }));
    throw new Error(data.detail || `Analysis not found (${res.status})`);
  }

  return res.json();
}

export function getVideoUrl(relativePath: string): string {
  return `${API_URL}${relativePath}`;
}
