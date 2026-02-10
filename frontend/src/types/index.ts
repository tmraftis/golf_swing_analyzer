export type SwingType = "iron" | "driver";
export type VideoAngle = "dtl" | "fo";

export interface VideoFile {
  file: File;
  angle: VideoAngle;
  duration?: number;
  validated: boolean;
  error?: string;
}

export interface FileInfo {
  filename: string;
  size_bytes: number;
  content_type: string;
}

export interface UploadResponse {
  status: "success" | "error";
  upload_id?: string;
  swing_type?: string;
  files?: {
    dtl: FileInfo;
    fo: FileInfo;
  };
  message?: string;
  detail?: string;
}
