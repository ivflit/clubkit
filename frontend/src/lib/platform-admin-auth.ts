"use client";

import { getApiBase } from "./api";

const TOKEN_KEY = "clubkit_platform_admin_token";

export function getStoredPlatformAdminToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function storePlatformAdminToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearPlatformAdminToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function platformAdminLogin(email: string, password: string): Promise<string> {
  const base = getApiBase(); // no subdomain → lvh.me
  const res = await fetch(`${base}/api/platform-admin/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new PlatformAdminAuthError(res.status, data);
  }
  const { access } = await res.json();
  storePlatformAdminToken(access);
  return access;
}

export class PlatformAdminAuthError extends Error {
  status: number;
  data: Record<string, unknown>;
  constructor(status: number, data: Record<string, unknown>) {
    super(`Platform admin auth error ${status}`);
    this.status = status;
    this.data = data;
  }
}
