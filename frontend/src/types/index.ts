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

// --- Swing phases ---

export const SWING_PHASES = [
  "address",
  "top",
  "impact",
  "follow_through",
] as const;
export type SwingPhase = (typeof SWING_PHASES)[number];

export const PHASE_LABELS: Record<SwingPhase, string> = {
  address: "Address",
  top: "Top",
  impact: "Impact",
  follow_through: "Follow-Through",
};

export const ANGLE_DISPLAY_NAMES: Record<string, string> = {
  spine_angle_dtl: "Spine Angle",
  lead_arm_torso: "Lead Arm-Torso",
  trail_arm_torso: "Trail Arm-Torso",
  right_elbow: "Right Elbow",
  left_elbow: "Left Elbow",
  right_knee_flex: "Right Knee Flex",
  left_knee_flex: "Left Knee Flex",
  right_wrist_cock: "Wrist Cock",
  shoulder_line_angle: "Shoulder Turn",
  hip_line_angle: "Hip Rotation",
  x_factor: "X-Factor",
  spine_tilt_fo: "Spine Tilt",
  shoulder_width_apparent: "Shoulder Width",
  hip_width_apparent: "Hip Width",
  shoulder_hip_offset_x: "Shoulder-Hip Offset",
};

// --- Analysis types ---

export interface PhaseAngles {
  frame: number;
  timestamp_sec: number;
  description?: string;
  angles: Record<string, number>;
}

export type ViewAngles = Partial<Record<SwingPhase, PhaseAngles>>;

export interface AngleData {
  dtl: ViewAngles;
  fo: ViewAngles;
}

export type ViewDeltas = Partial<Record<SwingPhase, Record<string, number>>>;

export interface DeltaData {
  dtl: ViewDeltas;
  fo: ViewDeltas;
}

export type PhaseFrames = Record<VideoAngle, Partial<Record<SwingPhase, number>>>;

export interface VideoUrls {
  dtl: string;
  fo: string;
}

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
  user_angles: AngleData;
  reference_angles: AngleData;
  deltas: DeltaData;
  top_differences: TopDifference[];
  phase_frames: PhaseFrames;
  video_urls?: VideoUrls;
  reference_video_urls?: VideoUrls;
}
