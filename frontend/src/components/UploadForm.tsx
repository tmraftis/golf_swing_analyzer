"use client";

import { useReducer } from "react";
import { useRouter } from "next/navigation";
import type { SwingType, VideoFile, UploadResponse } from "@/types";
import SwingTypeSelector from "./SwingTypeSelector";
import VideoDropZone from "./VideoDropZone";
import Button from "./Button";
import { uploadVideos, analyzeSwing } from "@/lib/api";

interface UploadState {
  swingType: SwingType;
  dtlFile: VideoFile | null;
  foFile: VideoFile | null;
  isUploading: boolean;
  isAnalyzing: boolean;
  uploadResult: UploadResponse | null;
  uploadError: string | null;
  analysisError: string | null;
}

type UploadAction =
  | { type: "SET_SWING_TYPE"; payload: SwingType }
  | { type: "SET_DTL_FILE"; payload: VideoFile }
  | { type: "SET_FO_FILE"; payload: VideoFile }
  | { type: "REMOVE_DTL" }
  | { type: "REMOVE_FO" }
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_SUCCESS"; payload: UploadResponse }
  | { type: "UPLOAD_ERROR"; payload: string }
  | { type: "ANALYSIS_START" }
  | { type: "ANALYSIS_ERROR"; payload: string };

const initialState: UploadState = {
  swingType: "iron",
  dtlFile: null,
  foFile: null,
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
    case "SET_DTL_FILE":
      return {
        ...state,
        dtlFile: action.payload,
        uploadResult: null,
        uploadError: null,
      };
    case "SET_FO_FILE":
      return {
        ...state,
        foFile: action.payload,
        uploadResult: null,
        uploadError: null,
      };
    case "REMOVE_DTL":
      return {
        ...state,
        dtlFile: null,
        uploadResult: null,
        uploadError: null,
      };
    case "REMOVE_FO":
      return {
        ...state,
        foFile: null,
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

  const canSubmit =
    state.swingType === "iron" &&
    state.dtlFile?.validated &&
    state.foFile?.validated &&
    !state.isUploading &&
    !state.isAnalyzing;

  async function handleSubmit() {
    if (!state.dtlFile || !state.foFile) return;

    // Step 1: Upload
    dispatch({ type: "UPLOAD_START" });
    let uploadResult: UploadResponse;
    try {
      uploadResult = await uploadVideos(
        state.swingType,
        state.dtlFile.file,
        state.foFile.file
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
        await analyzeSwing(uploadResult.upload_id, state.swingType);
        router.push(`/results/${uploadResult.upload_id}`);
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
            <span>Videos uploaded successfully</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="w-4 h-4 rounded-full border-2 border-t-pastel-yellow border-cream/10 animate-spin shrink-0" />
            <span className="text-cream/60">
              Running AI analysis (~30-50 seconds)
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

      {/* Step 2: Video uploads */}
      <div>
        <h2 className="text-lg font-semibold mb-1">Upload Videos</h2>
        <p className="text-sm text-cream/50 mb-4">
          We need two angles of your swing for a complete analysis.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <VideoDropZone
            angle="dtl"
            label="Down the Line"
            hint="Film from behind the golfer"
            file={state.dtlFile}
            onFileValidated={(v) =>
              dispatch({ type: "SET_DTL_FILE", payload: v })
            }
            onRemove={() => dispatch({ type: "REMOVE_DTL" })}
          />
          <VideoDropZone
            angle="fo"
            label="Face On"
            hint="Film facing the golfer"
            file={state.foFile}
            onFileValidated={(v) =>
              dispatch({ type: "SET_FO_FILE", payload: v })
            }
            onRemove={() => dispatch({ type: "REMOVE_FO" })}
          />
        </div>
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
