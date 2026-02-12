import { getUserOrRedirect } from "@propelauth/nextjs/server/app-router";
import UploadForm from "@/components/UploadForm";

export default async function UploadPage() {
  // Require authentication — redirects to PropelAuth login if not signed in
  await getUserOrRedirect();

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto max-w-2xl">
        <UploadForm />
      </div>
    </div>
  );
}
