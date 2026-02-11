import { getRouteHandlers } from "@propelauth/nextjs/server/app-router";
import { NextRequest, NextResponse } from "next/server";

const routeHandlers = getRouteHandlers({
  postLoginRedirectPathFn: (_req: NextRequest) => "/upload",
  getDefaultActiveOrgId: () => undefined,
});

// Wrap handlers for Next.js 16 compatibility (params are now Promises)
export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
): Promise<Response> {
  const resolvedParams = await params;
  return routeHandlers.getRouteHandler(req, {
    params: resolvedParams,
  }) as Promise<Response>;
}

export async function POST(
  req: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
): Promise<Response> {
  const resolvedParams = await params;
  return routeHandlers.postRouteHandler(req, {
    params: resolvedParams,
  }) as Promise<Response>;
}
