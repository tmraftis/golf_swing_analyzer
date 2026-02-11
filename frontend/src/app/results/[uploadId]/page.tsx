import { getUserOrRedirect } from "@propelauth/nextjs/server/app-router";
import ResultsPageClient from "./ResultsPageClient";

export default async function ResultsPage() {
  // Require authentication — redirects to PropelAuth login if not signed in
  await getUserOrRedirect();

  return <ResultsPageClient />;
}
