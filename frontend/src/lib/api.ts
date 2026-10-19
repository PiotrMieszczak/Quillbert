import { supabase } from "./supabase";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

/** fetch against the backend as the signed-in user. Throws ApiError carrying the
 *  server's `detail` (docs/api-contract.md error envelope). */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<{ status: number; data: T }> {
  const { data } = await supabase.auth.getSession();
  const headers = new Headers(init.headers);
  if (data.session) headers.set("Authorization", `Bearer ${data.session.access_token}`);

  const response = await fetch(`/api/v1${path}`, { ...init, headers });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return { status: response.status, data: body as T };
}
