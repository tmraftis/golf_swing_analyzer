import Link from "next/link";
import Image from "next/image";

export default function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-blue-charcoal/90 backdrop-blur-md border-b border-cream/10">
      <div className="mx-auto max-w-6xl flex items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center gap-3">
          <Image
            src="/pure-logo.jpeg"
            alt="Pure logo"
            width={36}
            height={36}
            className="rounded-sm invert"
          />
          <span className="text-cream font-semibold tracking-widest text-lg">
            PURE
          </span>
        </Link>
        <Link
          href="/upload"
          className="bg-cardinal-red text-cream px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-cardinal-red/90 transition-colors"
        >
          Analyze Your Swing
        </Link>
      </div>
    </header>
  );
}
