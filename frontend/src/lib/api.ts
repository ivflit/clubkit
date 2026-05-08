const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://lvh.me:8000";

export async function apiPost(path: string, body: FormData | Record<string, unknown>) {
  const isFormData = body instanceof FormData;
  const res = await fetch(`${API_BASE}${path}`, {
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

export class ApiError extends Error {
  status: number;
  data: Record<string, unknown>;
  constructor(status: number, data: Record<string, unknown>) {
    super(`API error ${status}`);
    this.status = status;
    this.data = data;
  }
}
