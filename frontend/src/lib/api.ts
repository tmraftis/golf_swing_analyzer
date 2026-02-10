import { API_URL } from "./constants";
import type { SwingType, UploadResponse } from "@/types";

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
