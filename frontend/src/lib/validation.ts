import {
  ACCEPTED_VIDEO_TYPES,
  ACCEPTED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  MAX_DURATION_SECONDS,
} from "./constants";

export function validateVideoFile(file: File): string | null {
  // Check file type — some browsers report empty MIME for .mov
  const ext = "." + file.name.split(".").pop()?.toLowerCase();
  const validType = ACCEPTED_VIDEO_TYPES.includes(file.type);
  const validExt = ACCEPTED_EXTENSIONS.includes(ext);

  if (!validType && !validExt) {
    return "Please upload a .mp4 or .mov video file.";
  }

  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `File is too large. Maximum size is ${MAX_FILE_SIZE_BYTES / (1024 * 1024)}MB.`;
  }

  return null;
}

export function getVideoDuration(file: File): Promise<number> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";

    const url = URL.createObjectURL(file);
    video.src = url;

    video.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(video.duration);
    };

    video.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Could not read video metadata."));
    };
  });
}

export function validateDuration(duration: number): string | null {
  if (duration > MAX_DURATION_SECONDS) {
    return `Video must be ${MAX_DURATION_SECONDS} seconds or less. This video is ${Math.round(duration)}s.`;
  }
  return null;
}
