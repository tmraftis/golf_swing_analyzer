"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useUser } from "@propelauth/nextjs/client";
import { getAnalysis } from "@/lib/api";
import type { AnalysisResponse } from "@/types";
import ResultsDashboard from "@/components/results/ResultsDashboard";
import LoadingSkeleton from "@/components/results/LoadingSkeleton";
import ErrorState from "@/components/results/ErrorState";

export default function ResultsPageClient() {
  const params = useParams();
  const uploadId = params.uploadId as string;
  const { loading: authLoading, accessToken } = useUser();
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!uploadId || authLoading || !accessToken) return;

    getAnalysis(uploadId, accessToken)
      .then(setAnalysis)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [uploadId, authLoading, accessToken]);

  if (authLoading || loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} />;
  if (!analysis) return <ErrorState message="No analysis data found." />;

  return <ResultsDashboard analysis={analysis} />;
}
