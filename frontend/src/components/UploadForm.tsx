"use client";

import { useReducer } from "react";
import type { SwingType, VideoFile, UploadResponse } from "@/types";
import SwingTypeSelector from "./SwingTypeSelector";
import VideoDropZone from "./VideoDropZone";
import Button from "./Button";
import { uploadVideos } from "@/lib/api";

interface UploadState {
  swingType: SwingType;
  dtlFile: VideoFile | null;
  foFile: VideoFile | null;
  isUploading: boolean;
  uploadResult: UploadResponse | null;
  uploadError: string | null;
}

type UploadAction =
  | { type: "SET_SWING_TYPE"; payload: SwingType }
  | { type: "SET_DTL_FILE"; payload: VideoFile }
  | { type: "SET_FO_FILE"; payload: VideoFile }
  | { type: "REMOVE_DTL" }
  | { type: "REMOVE_FO" }
  | { type: "UPLOAD_START" }
  | { type: "UPLOAD_SUCCESS"; payload: UploadResponse }
  | { type: "UPLOAD_ERROR"; payload: string };

const initialState: UploadState = {
  swingType: "iron",
  dtlFile: null,
  foFile: null,
  isUploading: false,
  uploadResult: null,
  uploadError: null,
};

function reducer(state: UploadState, action: UploadAction): UploadState {
  switch (action.type) {
    case "SET_SWING_TYPE":
      return { ...state, swingType: action.payload };
    case "SET_DTL_FILE":
      return { ...state, dtlFile: action.payload, uploadResult: null, uploadError: null };
    case "SET_FO_FILE":
      return { ...state, foFile: action.payload, uploadResult: null, uploadError: null };
    case "REMOVE_DTL":
      return { ...state, dtlFile: null, uploadResult: null, uploadError: null };
    case "REMOVE_FO":
      return { ...state, foFile: null, uploadResult: null, uploadError: null };
    case "UPLOAD_START":
      return { ...state, isUploading: true, uploadResult: null, uploadError: null };
    case "UPLOAD_SUCCESS":
      return { ...state, isUploading: false, uploadResult: action.payload };
    case "UPLOAD_ERROR":
      return { ...state, isUploading: false, uploadError: action.payload };
    default:
      return state;
  }
}

export default function UploadForm() {
  const [state, dispatch] = useReducer(reducer, initialState);

  const canSubmit =
    state.swingType === "iron" &&
    state.dtlFile?.validated &&
    state.foFile?.validated &&
    !state.isUploading;

  async function handleSubmit() {
    if (!state.dtlFile || !state.foFile) return;

    dispatch({ type: "UPLOAD_START" });
    try {
      const result = await uploadVideos(
        state.swingType,
        state.dtlFile.file,
        state.foFile.file
      );
      dispatch({ type: "UPLOAD_SUCCESS", payload: result });
    } catch (err) {
      dispatch({
        type: "UPLOAD_ERROR",
        payload: err instanceof Error ? err.message : "Upload failed.",
      });
    }
  }

  // Success state
  if (state.uploadResult?.status === "success") {
    return (
      <div className="rounded-xl border-2 border-forest-green/50 bg-forest-green/5 p-8 text-center">
        <svg className="w-12 h-12 mx-auto text-forest-green mb-4" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.857-9.809a.75.75 0 00-1.214-.882l-3.483 4.79-1.88-1.88a.75.75 0 10-1.06 1.061l2.5 2.5a.75.75 0 001.137-.089l4-5.5z" clipRule="evenodd" />
        </svg>
        <h3 className="text-xl font-semibold mb-2">Videos Uploaded</h3>
        <p className="text-cream/60 mb-4">
          Your {state.swingType} swing videos have been uploaded successfully.
        </p>
        <p className="text-sm text-cream/40">
          Analysis will be available in the next release. Upload ID:{" "}
          <code className="text-pastel-yellow">{state.uploadResult.upload_id}</code>
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
            onFileValidated={(v) => dispatch({ type: "SET_DTL_FILE", payload: v })}
            onRemove={() => dispatch({ type: "REMOVE_DTL" })}
          />
          <VideoDropZone
            angle="fo"
            label="Face On"
            hint="Film facing the golfer"
            file={state.foFile}
            onFileValidated={(v) => dispatch({ type: "SET_FO_FILE", payload: v })}
            onRemove={() => dispatch({ type: "REMOVE_FO" })}
          />
        </div>
      </div>

      {/* Error message */}
      {state.uploadError && (
        <div className="rounded-lg border border-cardinal-red/50 bg-cardinal-red/5 p-4">
          <p className="text-sm text-cardinal-red">{state.uploadError}</p>
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
