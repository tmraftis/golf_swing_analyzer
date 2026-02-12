"use client";

import { useReducer } from "react";
import { useRouter } from "next/navigation";
import { useUser } from "@propelauth/nextjs/client";
import type { SwingType, VideoAngle, VideoFile, UploadResponse } from "@/types";
import SwingTypeSelector from "./SwingTypeSelector";
import VideoDropZone from "./VideoDropZone";
import Button from "./Button";
import { uploadVideo, analyzeSwing } from "@/lib/api";

interface UploadState {
  swingType: SwingType;
  view: VideoAngle;
  videoFile: VideoFile | null;
  isUploading: boolean;
  isAnalyzing: boolean;
  uploadResult: UploadResponse | null;
  uploadError: string | null;
  analysisError: string | null;
}

type UploadAction =
  | { type: "SET_SWING_TYPE"; payload: SwingType }
  | { type: "SET_VIEW"; payload: VideoAngle }
  | { type: "SET_VIDEO"; payload: VideoFile }
  | { type: "REMOVE_VIDEO" }
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_SUCCESS"; payload: UploadResponse }
  | { type: "UPLOAD_ERROR"; payload: string }
  | { type: "ANALYSIS_START" }
  | { type: "ANALYSIS_ERROR"; payload: string };

const initialState: UploadState = {
  swingType: "iron",
  view: "dtl",
  videoFile: null,
  isUploading: false,
  isAnalyzing: false,
  uploadResult: null,
  uploadError: null,
  analysisError: null,
};

function reducer(state: UploadState, action: UploadAction): UploadState {
  switch (action.type) {
    case "SET_SWING_TYPE":
      return { ...state, swingType: action.payload };
    case "SET_VIEW":
      return {
        ...state,
        view: action.payload,
        videoFile: null,
        uploadResult: null,
        uploadError: null,
      };
    case "SET_VIDEO":
      return {
        ...state,
        videoFile: action.payload,
        uploadResult: null,
        uploadError: null,
      };
    case "REMOVE_VIDEO":
      return {
        ...state,
        videoFile: null,
        uploadResult: null,
        uploadError: null,
      };
    case "UPLOAD_START":
      return {
        ...state,
        isUploading: true,
        uploadResult: null,
        uploadError: null,
      };
    case "UPLOAD_SUCCESS":
      return { ...state, isUploading: false, uploadResult: action.payload };
    case "UPLOAD_ERROR":
      return { ...state, isUploading: false, uploadError: action.payload };
    case "ANALYSIS_START":
      return { ...state, isAnalyzing: true, analysisError: null };
    case "ANALYSIS_ERROR":
      return { ...state, isAnalyzing: false, analysisError: action.payload };
    default:
      return state;
  }
}

export default function UploadForm() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const router = useRouter();
  const { accessToken } = useUser();

  const canSubmit =
    state.swingType === "iron" &&
    state.videoFile?.validated &&
    !state.isUploading &&
    !state.isAnalyzing;

  async function handleSubmit() {
    if (!state.videoFile) return;

    // Step 1: Upload
    dispatch({ type: "UPLOAD_START" });
    let uploadResult: UploadResponse;
    try {
      uploadResult = await uploadVideo(
        state.swingType,
        state.view,
        state.videoFile.file,
        accessToken || undefined
      );
      dispatch({ type: "UPLOAD_SUCCESS", payload: uploadResult });
    } catch (err) {
      dispatch({
        type: "UPLOAD_ERROR",
        payload: err instanceof Error ? err.message : "Upload failed.",
      });
      return;
    }

    // Step 2: Auto-trigger analysis, redirect on success
    if (uploadResult.upload_id) {
      dispatch({ type: "ANALYSIS_START" });
      try {
        await analyzeSwing(
          uploadResult.upload_id,
          state.swingType,
          state.view,
          accessToken || undefined
        );
        router.push(`/results/${uploadResult.upload_id}?view=${state.view}`);
      } catch (err) {
        dispatch({
          type: "ANALYSIS_ERROR",
          payload: err instanceof Error ? err.message : "Analysis failed.",
        });
      }
    }
  }

  // Analyzing state — show progress
  if (state.isAnalyzing) {
    return (
      <div className="rounded-xl border-2 border-pastel-yellow/30 bg-pastel-yellow/5 p-8 text-center">
        <div className="relative w-16 h-16 mx-auto mb-6">
          <div className="absolute inset-0 rounded-full border-4 border-cream/10" />
          <div className="absolute inset-0 rounded-full border-4 border-t-pastel-yellow animate-spin" />
        </div>
        <h3 className="text-xl font-semibold mb-2">Analyzing Your Swing</h3>
        <p className="text-cream/50 mb-6">
          Extracting landmarks, detecting phases, and comparing angles...
        </p>
        <div className="space-y-3 text-sm text-cream/40 max-w-sm mx-auto">
          <div className="flex items-center gap-3">
            <svg
              className="w-4 h-4 text-forest-green shrink-0"
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                clipRule="evenodd"
              />
            </svg>
            <span>Video uploaded successfully</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full border-2 border-t-pastel-yellow border-cream/10 animate-spin shrink-0" />
            <span className="text-cream/60">
              Running AI analysis (~15-25 seconds)
            </span>
          </div>
        </div>

        {state.analysisError && (
          <div className="mt-6 rounded-lg border border-cardinal-red/50 bg-cardinal-red/5 p-4">
            <p className="text-sm text-cardinal-red">{state.analysisError}</p>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Step 1: Swing type */}
      <div>
        <h2 className="text-lg font-semibold mb-1">Swing Type</h2>
        <p className="text-sm text-cream/50 mb-4">
          Select the type of swing you&apos;re uploading.
        </p>
        <SwingTypeSelector
          selected={state.swingType}
          onSelect={(t) => dispatch({ type: "SET_SWING_TYPE", payload: t })}
        />
      </div>

      {/* Step 2: Camera angle */}
      <div>
        <h2 className="text-lg font-semibold mb-1">Camera Angle</h2>
        <p className="text-sm text-cream/50 mb-4">
          Choose which angle you filmed your swing from.
        </p>
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={() => dispatch({ type: "SET_VIEW", payload: "dtl" })}
            className={`relative rounded-xl border-2 p-6 text-left transition-colors ${
              state.view === "dtl"
                ? "border-forest-green bg-forest-green/10"
                : "border-cream/15 hover:border-cream/30"
            }`}
          >
            <h3 className="text-lg font-semibold mb-1">Down the Line</h3>
            <p className="text-sm text-cream/50">
              Camera behind the golfer, looking at the target line
            </p>
            {state.view === "dtl" && (
              <div className="absolute top-4 right-4">
                <svg
                  className="w-5 h-5 text-forest-green"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
          </button>

          <button
            onClick={() => dispatch({ type: "SET_VIEW", payload: "fo" })}
            className={`relative rounded-xl border-2 p-6 text-left transition-colors ${
              state.view === "fo"
                ? "border-forest-green bg-forest-green/10"
                : "border-cream/15 hover:border-cream/30"
            }`}
          >
            <h3 className="text-lg font-semibold mb-1">Face On</h3>
            <p className="text-sm text-cream/50">
              Camera facing the golfer from the target side
            </p>
            {state.view === "fo" && (
              <div className="absolute top-4 right-4">
                <svg
                  className="w-5 h-5 text-forest-green"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
            )}
          </button>
        </div>
      </div>

      {/* Step 3: Video upload */}
      <div>
        <h2 className="text-lg font-semibold mb-1">Upload Video</h2>
        <p className="text-sm text-cream/50 mb-4">
          Upload your {state.view === "dtl" ? "down-the-line" : "face-on"} swing
          video.
        </p>
        <VideoDropZone
          angle={state.view}
          label={state.view === "dtl" ? "Down the Line" : "Face On"}
          hint={
            state.view === "dtl"
              ? "Film from behind the golfer"
              : "Film facing the golfer"
          }
          file={state.videoFile}
          onFileValidated={(v) =>
            dispatch({ type: "SET_VIDEO", payload: v })
          }
          onRemove={() => dispatch({ type: "REMOVE_VIDEO" })}
        />
      </div>

      {/* Error messages */}
      {(state.uploadError || state.analysisError) && (
        <div className="rounded-lg border border-cardinal-red/50 bg-cardinal-red/5 p-4">
          <p className="text-sm text-cardinal-red">
            {state.uploadError || state.analysisError}
          </p>
        </div>
      )}

      {/* Submit */}
      <Button
        variant="primary"
        disabled={!canSubmit}
        loading={state.isUploading}
        onClick={handleSubmit}
        className="w-full py-4 text-base"
      >
        Submit for Analysis
      </Button>
    </div>
  );
}
