import Link from "next/link";
import Button from "@/components/Button";

interface ErrorStateProps {
  message: string;
}

export default function ErrorState({ message }: ErrorStateProps) {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <svg
          className="w-16 h-16 mx-auto text-cardinal-red/60 mb-6"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fillRule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
            clipRule="evenodd"
          />
        </svg>
        <h2 className="text-xl font-semibold mb-2">Analysis Not Found</h2>
        <p className="text-cream/50 mb-8">{message}</p>
        <Link href="/upload">
          <Button variant="primary">Upload New Swing</Button>
        </Link>
      </div>
    </div>
  );
}
