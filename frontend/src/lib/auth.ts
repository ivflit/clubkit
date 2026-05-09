"use client";

import { getApiBase } from "./api";

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: "admin" | "member";
  date_joined: string;
}

const TOKEN_KEY = "clubkit_tokens";

export function getStoredTokens(): AuthTokens | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(TOKEN_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function storeTokens(tokens: AuthTokens): void {
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
}

export function clearTokens(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function login(
  subdomain: string,
  username: string,
  password: string,
): Promise<AuthTokens> {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}/api/auth/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new AuthError(res.status, data);
  }
  const tokens: AuthTokens = await res.json();
  storeTokens(tokens);
  return tokens;
}

export async function register(
  subdomain: string,
  data: { email: string; password: string; first_name?: string; last_name?: string },
): Promise<User> {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}/api/auth/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new AuthError(res.status, body);
  }
  return res.json();
}

export async function fetchMe(subdomain: string): Promise<User> {
  const tokens = getStoredTokens();
  if (!tokens) throw new AuthError(401, { detail: "Not authenticated" });

  const base = getApiBase(subdomain);
  const res = await fetch(`${base}/api/auth/me/`, {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${tokens.access}`,
    },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new AuthError(res.status, data);
  }
  return res.json();
}

export function logout(): void {
  clearTokens();
}

export class AuthError extends Error {
  status: number;
  data: Record<string, unknown>;
  constructor(status: number, data: Record<string, unknown>) {
    super(`Auth error ${status}`);
    this.status = status;
    this.data = data;
  }
}
