"use client";

import Link from "next/link";
import Image from "next/image";
import { useUser, useLogoutFunction } from "@propelauth/nextjs/client";

export default function Header() {
  const { loading, user } = useUser();
  const logout = useLogoutFunction();

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

        <div className="flex items-center gap-4">
          {!loading && user ? (
            <>
              <span className="text-cream/60 text-sm hidden sm:inline">
                {user.email}
              </span>
              <button
                onClick={() => logout()}
                className="text-cream/50 hover:text-cream text-sm font-medium transition-colors cursor-pointer"
              >
                Sign Out
              </button>
            </>
          ) : !loading ? (
            <>
              <Link
                href="/api/auth/login"
                className="text-cream/70 hover:text-cream text-sm font-medium transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/api/auth/signup"
                className="bg-cardinal-red text-cream px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-cardinal-red/90 transition-colors"
              >
                Get Started
              </Link>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
