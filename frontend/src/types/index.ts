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

// --- Analysis types ---

export interface TopDifference {
  rank: number;
  angle_name: string;
  phase: string;
  view: string;
  user_value: number;
  reference_value: number;
  delta: number;
  severity: "major" | "moderate" | "minor";
  title: string;
  description: string;
  coaching_tip: string;
}

export interface AnalysisResponse {
  status: string;
  upload_id: string;
  swing_type: string;
  processing_time_sec: number;
  user_angles: Record<string, unknown>;
  reference_angles: Record<string, unknown>;
  deltas: Record<string, unknown>;
  top_differences: TopDifference[];
  phase_frames: Record<string, unknown>;
}
