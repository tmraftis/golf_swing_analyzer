// Mock API response factories for Playwright route interception.
//
// Usage:
//   await page.route("**/api/analyze/**", (route) =>
//     route.fulfill({ json: mockAnalysisResponse() })
//   );

export const MOCK_UPLOAD_ID = "e2e-test-upload-1234";
export const MOCK_SHARE_TOKEN = "e2e-share-abc123";

/** Successful analysis response matching AnalysisResponse schema */
export function mockAnalysisResponse(overrides: Record<string, unknown> = {}) {
  return {
    status: "success",
    upload_id: MOCK_UPLOAD_ID,
    swing_type: "iron",
    similarity_score: 78,
    view: "dtl",
    processing_time_sec: 18.5,
    user_angles: {
      dtl: {
        address: { spine_angle: -32.5, knee_flex: 28.1, hip_angle: 45.2 },
        top: { spine_angle: -30.1, knee_flex: 30.5, hip_angle: 40.8 },
        impact: { spine_angle: -35.2, knee_flex: 26.3, hip_angle: 42.1 },
        follow_through: { spine_angle: -15.4, knee_flex: 18.7, hip_angle: 55.3 },
      },
    },
    reference_angles: {
      dtl: {
        address: { spine_angle: -34.0, knee_flex: 27.0, hip_angle: 44.0 },
        top: { spine_angle: -31.5, knee_flex: 29.0, hip_angle: 39.0 },
        impact: { spine_angle: -36.0, knee_flex: 25.0, hip_angle: 41.0 },
        follow_through: { spine_angle: -14.0, knee_flex: 17.0, hip_angle: 54.0 },
      },
    },
    deltas: {
      dtl: {
        address: { spine_angle: 1.5, knee_flex: -1.1, hip_angle: -1.2 },
        top: { spine_angle: 1.4, knee_flex: -1.5, hip_angle: -1.8 },
        impact: { spine_angle: 0.8, knee_flex: -1.3, hip_angle: -1.1 },
        follow_through: { spine_angle: -1.4, knee_flex: -1.7, hip_angle: -1.3 },
      },
    },
    top_differences: [
      {
        angle_name: "knee_flex",
        phase: "top",
        view: "dtl",
        user_value: 30.5,
        reference_value: 29.0,
        delta: -1.5,
        rank: 1,
        severity: "moderate",
        title: "Knee Flex at Top of Backswing",
        description: "Your right knee flex at the top is 30.5° compared to Tiger's 29.0°.",
        coaching_tip: "Focus on maintaining knee flex throughout the backswing.",
      },
      {
        angle_name: "hip_angle",
        phase: "top",
        view: "dtl",
        user_value: 40.8,
        reference_value: 39.0,
        delta: -1.8,
        rank: 2,
        severity: "minor",
        title: "Hip Angle at Top",
        description: "Your hip angle at the top is 40.8° compared to Tiger's 39.0°.",
        coaching_tip: "Work on hip rotation drills to improve your turn.",
      },
      {
        angle_name: "spine_angle",
        phase: "address",
        view: "dtl",
        user_value: -32.5,
        reference_value: -34.0,
        delta: 1.5,
        rank: 3,
        severity: "minor",
        title: "Spine Angle at Address",
        description: "Your spine angle at address is -32.5° compared to Tiger's -34.0°.",
        coaching_tip: "Try to tilt forward slightly more at address for a better spine angle.",
      },
    ],
    top_similarities: [
      {
        angle_name: "spine_angle",
        phase: "impact",
        view: "dtl",
        user_value: -35.2,
        reference_value: -36.0,
        delta: 0.8,
        rank: 1,
        title: "Spine Angle at Impact",
      },
    ],
    video_urls: {
      dtl: `/uploads/${MOCK_UPLOAD_ID}_dtl.mp4`,
    },
    reference_video_urls: {
      dtl: "/reference/iron/tiger_2000_iron_dtl.mov",
    },
    user_phase_images: null,
    reference_phase_images: null,
    ...overrides,
  };
}

/** Successful upload response */
export function mockUploadResponse(overrides: Record<string, unknown> = {}) {
  return {
    upload_id: MOCK_UPLOAD_ID,
    filename: `${MOCK_UPLOAD_ID}_dtl.mp4`,
    view: "dtl",
    swing_type: "iron",
    ...overrides,
  };
}

/** Successful share creation response */
export function mockShareResponse(overrides: Record<string, unknown> = {}) {
  return {
    share_token: MOCK_SHARE_TOKEN,
    share_url: `http://localhost:3000/shared/${MOCK_SHARE_TOKEN}`,
    expires_at: null,
    ...overrides,
  };
}

/** Shared analysis data (public view — no video URLs) */
export function mockSharedAnalysis(overrides: Record<string, unknown> = {}) {
  const full = mockAnalysisResponse();
  return {
    status: full.status,
    upload_id: full.upload_id,
    swing_type: full.swing_type,
    similarity_score: full.similarity_score,
    view: full.view,
    user_angles: full.user_angles,
    reference_angles: full.reference_angles,
    deltas: full.deltas,
    top_differences: full.top_differences,
    top_similarities: full.top_similarities,
    user_phase_images: null,
    reference_phase_images: null,
    ...overrides,
  };
}
