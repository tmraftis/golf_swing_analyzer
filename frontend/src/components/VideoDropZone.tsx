"use client";

import { useCallback } from "react";
import { useDropzone } from "react-dropzone";
import type { VideoAngle, VideoFile } from "@/types";
import { ACCEPTED_EXTENSIONS } from "@/lib/constants";
import { validateVideoFile, getVideoDuration, validateDuration } from "@/lib/validation";

interface VideoDropZoneProps {
  angle: VideoAngle;
  label: string;
  hint: string;
  file: VideoFile | null;
  onFileValidated: (video: VideoFile) => void;
  onRemove: () => void;
}

export default function VideoDropZone({
  angle,
  label,
  hint,
  file,
  onFileValidated,
  onRemove,
}: VideoDropZoneProps) {
  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const f = acceptedFiles[0];
      if (!f) return;

      // Validate file type and size
      const fileError = validateVideoFile(f);
      if (fileError) {
        onFileValidated({ file: f, angle, validated: false, error: fileError });
        return;
      }

      // Validate duration
      try {
        const duration = await getVideoDuration(f);
        const durationError = validateDuration(duration);
        if (durationError) {
          onFileValidated({
            file: f,
            angle,
            duration,
            validated: false,
            error: durationError,
          });
          return;
        }
        onFileValidated({ file: f, angle, duration, validated: true });
      } catch {
        // If we can't read metadata, allow upload — backend can re-validate
        onFileValidated({
          file: f,
          angle,
          validated: true,
          error: undefined,
        });
      }
    },
    [angle, onFileValidated]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "video/mp4": [".mp4"],
      "video/quicktime": [".mov"],
    },
    maxFiles: 1,
    multiple: false,
  });

  // File loaded state
  if (file) {
    const sizeMB = (file.file.size / (1024 * 1024)).toFixed(1);
    return (
      <div
        className={`rounded-lg border-2 p-5 ${
          file.validated
            ? "border-forest-green/50 bg-forest-green/5"
            : "border-cardinal-red/50 bg-cardinal-red/5"
        }`}
      >
        <div className="flex items-start justify-between mb-3">
          <h3 className="font-semibold text-sm uppercase tracking-wide text-cream/60">
            {label}
          </h3>
          <button
            onClick={onRemove}
            className="text-cream/40 hover:text-cream text-sm transition-colors"
          >
            Remove
          </button>
        </div>

        <div className="flex items-center gap-3">
          {file.validated ? (
            <svg className="w-5 h-5 text-forest-green shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-cardinal-red shrink-0" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
            </svg>
          )}
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{file.file.name}</p>
            <p className="text-xs text-cream/40">
              {sizeMB} MB
              {file.duration != null && ` · ${Math.round(file.duration)}s`}
            </p>
          </div>
        </div>

        {file.error && (
          <p className="mt-3 text-sm text-cardinal-red">{file.error}</p>
        )}
      </div>
    );
  }

  // Empty state / drop zone
  return (
    <div
      {...getRootProps()}
      className={`rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
        isDragActive
          ? "border-forest-green bg-forest-green/5"
          : "border-cream/20 hover:border-cream/40"
      }`}
    >
      <input {...getInputProps()} />
      <div className="text-cream/30 mb-2">
        <svg className="w-8 h-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
      </div>
      <p className="text-sm text-cream/40 mb-1">
        Drag &amp; drop or click to select
      </p>
      <p className="text-xs text-cream/30">
        {ACCEPTED_EXTENSIONS.join(", ")} · Max 30s
      </p>
    </div>
  );
}
