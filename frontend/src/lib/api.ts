const API_PORT = process.env.NEXT_PUBLIC_API_PORT ?? "8000";
const API_HOST = process.env.NEXT_PUBLIC_API_HOST ?? "lvh.me";

/**
 * Build the API base URL for a given subdomain.
 * When subdomain is provided, targets {subdomain}.lvh.me:8000.
 * When omitted, targets the platform domain (lvh.me:8000).
 */
export function getApiBase(subdomain?: string): string {
  const host = subdomain ? `${subdomain}.${API_HOST}` : API_HOST;
  return `http://${host}:${API_PORT}`;
}

export async function apiGet(path: string, subdomain?: string) {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json" },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export async function apiPost(path: string, body: FormData | Record<string, unknown>, subdomain?: string) {
  const isFormData = body instanceof FormData;
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: isFormData ? {} : { "Content-Type": "application/json" },
    body: isFormData ? body : JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export async function apiAuthGet(path: string, token: string, subdomain?: string) {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}${path}`, {
    method: "GET",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export async function apiAuthPost(path: string, body: Record<string, unknown>, token: string, subdomain?: string) {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export async function apiAuthPatch(path: string, body: Record<string, unknown>, token: string, subdomain?: string) {
  const base = getApiBase(subdomain);
  const res = await fetch(`${base}${path}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new ApiError(res.status, data);
  }
  return res.json();
}

export class ApiError extends Error {
  status: number;
  data: Record<string, unknown>;
  constructor(status: number, data: Record<string, unknown>) {
    super(`API error ${status}`);
    this.status = status;
    this.data = data;
  }
}
