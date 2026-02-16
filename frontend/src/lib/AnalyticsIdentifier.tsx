"use client";

/**
 * Invisible component that calls Segment identify() when PropelAuth
 * resolves the current user.  Renders nothing (null).
 *
 * Place inside <AuthProvider> so it has access to useUser().
 */

import { useEffect, useRef } from "react";
import { useUser } from "@propelauth/nextjs/client";
import { identifyUser, resetIdentity } from "@/lib/analytics";

export default function AnalyticsIdentifier() {
  const { loading, user } = useUser();
  const identifiedRef = useRef<string | null>(null);

  useEffect(() => {
    if (loading) return;

    if (user && user.userId !== identifiedRef.current) {
      identifyUser(user.userId, { email: user.email });
      identifiedRef.current = user.userId;
    } else if (!user && identifiedRef.current) {
      resetIdentity();
      identifiedRef.current = null;
    }
  }, [loading, user]);

  return null;
}
