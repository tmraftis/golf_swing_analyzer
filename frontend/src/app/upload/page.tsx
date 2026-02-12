import { getUserOrRedirect } from "@propelauth/nextjs/server/app-router";
import UploadForm from "@/components/UploadForm";

export default async function UploadPage() {
  // Require authentication — redirects to PropelAuth login if not signed in
  await getUserOrRedirect();

  return (
    <div className="min-h-screen px-6 py-12">
      <div className="mx-auto max-w-2xl">
        <h1 className="text-3xl font-bold mb-2">Upload Your Swing</h1>
        <p className="text-cream/50 mb-10">
          Select your swing type and camera angle, then upload a video of your
          swing.
        </p>
        <UploadForm />
      </div>
    </div>
  );
}
