import { NextRequest, NextResponse } from "next/server";
import { getSubdomain } from "./lib/tenant";
import { getApiBase } from "./lib/api";

/**
 * Next.js middleware that detects whether the request is on a tenant subdomain.
 * Validates the tenant exists via the Django API and redirects to a "club not
 * found" page if it doesn't. Sets x-subdomain header for Server Components.
 */
export async function middleware(request: NextRequest) {
  const hostname = request.headers.get("host") ?? "";
  const subdomain = getSubdomain(hostname);

  if (!subdomain) {
    // Platform root — no tenant context needed
    return NextResponse.next();
  }

  // Skip validation for the club-not-found page itself to avoid redirect loops
  if (request.nextUrl.pathname === "/club-not-found") {
    return NextResponse.next();
  }

  // Validate the tenant exists by hitting the Brand Kit endpoint
  try {
    const apiBase = getApiBase(subdomain);
    const res = await fetch(`${apiBase}/api/brand-kit/`, {
      headers: { "Content-Type": "application/json" },
    });

    if (!res.ok) {
      // Tenant doesn't exist — show club not found page
      const url = request.nextUrl.clone();
      url.pathname = "/club-not-found";
      return NextResponse.rewrite(url);
    }
  } catch {
    // Backend unreachable — let the page handle the error
  }

  // Tenant exists — pass subdomain to server components
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-subdomain", subdomain);

  return NextResponse.next({
    request: { headers: requestHeaders },
  });
}

export const config = {
  // Run on all routes except static files and Next.js internals
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
