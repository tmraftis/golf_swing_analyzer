import { authMiddleware } from "@propelauth/nextjs/server/app-router";

export const middleware = authMiddleware;

export const config = {
  matcher: [
    // Match all routes except static files and Next.js internals
    "/((?!_next/static|_next/image|favicon.ico|pure-logo.jpeg).*)",
  ],
};
