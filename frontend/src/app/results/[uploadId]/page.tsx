"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getAnalysis } from "@/lib/api";
import type { AnalysisResponse } from "@/types";
import ResultsDashboard from "@/components/results/ResultsDashboard";
import LoadingSkeleton from "@/components/results/LoadingSkeleton";
import ErrorState from "@/components/results/ErrorState";

export default function ResultsPage() {
  const params = useParams();
  const uploadId = params.uploadId as string;
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!uploadId) return;

    getAnalysis(uploadId)
      .then(setAnalysis)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [uploadId]);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorState message={error} />;
  if (!analysis) return <ErrorState message="No analysis data found." />;

  return <ResultsDashboard analysis={analysis} />;
}
