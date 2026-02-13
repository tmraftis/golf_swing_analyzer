import type { Metadata } from "next";
import SharedResultsClient from "./SharedResultsClient";

interface Props {
  params: Promise<{ shareToken: string }>;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { shareToken } = await params;

  // Try to fetch share data for OG tags
  try {
    const res = await fetch(`${API_URL}/api/share/${shareToken}`, {
      next: { revalidate: 300 },
    });

    if (res.ok) {
      const data = await res.json();
      const score = data.similarity_score ?? 0;
      return {
        title: `${score}% Similarity to Tiger Woods — Pure Swing Analysis`,
        description: `See how this swing compares to Tiger Woods! ${score}% similarity score. Analyze your own swing with Pure.`,
        openGraph: {
          title: `${score}% Similar to Tiger Woods`,
          description: `Swing analysis powered by Pure. See the breakdown and compare your own swing!`,
          images: [`${API_URL}/api/share/${shareToken}/image`],
          type: "website",
        },
        twitter: {
          card: "summary_large_image",
          title: `${score}% Similar to Tiger Woods — Pure`,
          description: `Swing analysis powered by Pure. Compare your own swing!`,
          images: [`${API_URL}/api/share/${shareToken}/image`],
        },
      };
    }
  } catch {
    // Fall through to defaults
  }

  return {
    title: "Swing Analysis — Pure",
    description: "Compare your golf swing to Tiger Woods with Pure.",
  };
}

export default async function SharedResultsPage({ params }: Props) {
  const { shareToken } = await params;
  return <SharedResultsClient shareToken={shareToken} />;
}
