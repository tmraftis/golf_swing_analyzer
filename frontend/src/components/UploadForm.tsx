"use client";

import { useReducer } from "react";
import type {
  SwingType,
  VideoFile,
  UploadResponse,
  AnalysisResponse,
  TopDifference,
} from "@/types";
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
  analysisResult: AnalysisResponse | null;
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
  | { type: "ANALYSIS_SUCCESS"; payload: AnalysisResponse }
  | { type: "ANALYSIS_ERROR"; payload: string }
  | { type: "RESET" };

const initialState: UploadState = {
  swingType: "iron",
  dtlFile: null,
  foFile: null,
  isUploading: false,
  isAnalyzing: false,
  uploadResult: null,
  analysisResult: null,
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
    case "ANALYSIS_SUCCESS":
      return {
        ...state,
        isAnalyzing: false,
        analysisResult: action.payload,
      };
    case "ANALYSIS_ERROR":
      return { ...state, isAnalyzing: false, analysisError: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const SEVERITY_COLORS = {
  major: {
    border: "border-cardinal-red/50",
    bg: "bg-cardinal-red/5",
    badge: "bg-cardinal-red/20 text-cardinal-red",
  },
  moderate: {
    border: "border-pastel-yellow/50",
    bg: "bg-pastel-yellow/5",
    badge: "bg-pastel-yellow/20 text-pastel-yellow",
  },
  minor: {
    border: "border-cream/30",
    bg: "bg-cream/5",
    badge: "bg-cream/20 text-cream/70",
  },
};

function DifferenceCard({ diff }: { diff: TopDifference }) {
  const colors = SEVERITY_COLORS[diff.severity];

  return (
    <div className={`rounded-xl border ${colors.border} ${colors.bg} p-6`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold text-cream/30">
            #{diff.rank}
          </span>
          <h4 className="text-lg font-semibold">{diff.title}</h4>
        </div>
        <span
          className={`text-xs font-medium px-2.5 py-1 rounded-full uppercase tracking-wide ${colors.badge}`}
        >
          {diff.severity}
        </span>
      </div>

      <p className="text-sm text-cream/70 mb-4 leading-relaxed">
        {diff.description}
      </p>

      <div className="flex items-center gap-4 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <span className="text-cream/40">You:</span>
          <span className="font-mono font-medium">
            {diff.user_value.toFixed(1)}°
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-cream/40">Tiger:</span>
          <span className="font-mono font-medium text-pastel-yellow">
            {diff.reference_value.toFixed(1)}°
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-cream/40">Diff:</span>
          <span
            className={`font-mono font-medium ${
              Math.abs(diff.delta) > 15 ? "text-cardinal-red" : "text-cream/80"
            }`}
          >
            {diff.delta > 0 ? "+" : ""}
            {diff.delta.toFixed(1)}°
          </span>
        </div>
      </div>

      <div className="rounded-lg bg-forest-green/10 border border-forest-green/20 p-4">
        <div className="flex items-start gap-2">
          <svg
            className="w-4 h-4 text-forest-green mt-0.5 shrink-0"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M10 2a8 8 0 100 16 8 8 0 000-16zM8.94 6.94a.75.75 0 11-1.061-1.061 .75.75 0 011.061 1.061zM10 15a.75.75 0 01-.75-.75v-4.5a.75.75 0 011.5 0v4.5A.75.75 0 0110 15z" />
          </svg>
          <p className="text-sm text-cream/80">{diff.coaching_tip}</p>
        </div>
      </div>
    </div>
  );
}

export default function UploadForm() {
  const [state, dispatch] = useReducer(reducer, initialState);

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

    // Step 2: Auto-trigger analysis
    if (uploadResult.upload_id) {
      dispatch({ type: "ANALYSIS_START" });
      try {
        const analysisResult = await analyzeSwing(
          uploadResult.upload_id,
          state.swingType
        );
        dispatch({ type: "ANALYSIS_SUCCESS", payload: analysisResult });
      } catch (err) {
        dispatch({
          type: "ANALYSIS_ERROR",
          payload: err instanceof Error ? err.message : "Analysis failed.",
        });
      }
    }
  }

  // Analysis complete — show results
  if (state.analysisResult) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="text-center mb-8">
          <svg
            className="w-12 h-12 mx-auto text-forest-green mb-4"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
              clipRule="evenodd"
            />
          </svg>
          <h3 className="text-2xl font-semibold mb-2">Swing Analysis</h3>
          <p className="text-cream/50 text-sm">
            Processed in {state.analysisResult.processing_time_sec}s • Compared
            to Tiger Woods&apos; 2000 {state.analysisResult.swing_type} swing
          </p>
        </div>

        {/* Top differences */}
        <div>
          <h3 className="text-lg font-semibold mb-4">
            Top Areas for Improvement
          </h3>
          <div className="space-y-4">
            {state.analysisResult.top_differences.map((diff) => (
              <DifferenceCard key={diff.rank} diff={diff} />
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="pt-4">
          <Button
            variant="secondary"
            onClick={() => dispatch({ type: "RESET" })}
            className="w-full py-3"
          >
            Analyze Another Swing
          </Button>
        </div>
      </div>
    );
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

  // Upload success but no analysis yet (shouldn't normally happen with auto-trigger)
  if (state.uploadResult?.status === "success" && !state.isAnalyzing) {
    return (
      <div className="rounded-xl border-2 border-forest-green/50 bg-forest-green/5 p-8 text-center">
        <svg
          className="w-12 h-12 mx-auto text-forest-green mb-4"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z"
            clipRule="evenodd"
          />
        </svg>
        <h3 className="text-xl font-semibold mb-2">Videos Uploaded</h3>
        <p className="text-cream/60 mb-4">
          Your {state.swingType} swing videos have been uploaded successfully.
        </p>
        <p className="text-sm text-cream/40">
          Upload ID:{" "}
          <code className="text-pastel-yellow">
            {state.uploadResult.upload_id}
          </code>
        </p>
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
