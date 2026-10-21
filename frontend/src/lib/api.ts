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
  const response = await authorizedFetch(`/api/v1${path}`, init);
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = typeof body?.detail === "string" ? body.detail : `Request failed (${response.status})`;
    throw new ApiError(response.status, detail);
  }
  return { status: response.status, data: body as T };
}

/** A binary resource the API serves at `url` (a full path, e.g. a campaign's `imageUrl`). An <img>
 *  cannot send the bearer token, so images are fetched here and shown from a blob. */
export async function apiBlob(url: string): Promise<Blob> {
  const response = await authorizedFetch(url);
  if (!response.ok) throw new ApiError(response.status, `Request failed (${response.status})`);
  return response.blob();
}

/** The signed-in user's current access token; supabase-js refreshes it when it is close to expiry. */
export async function accessToken() {
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token;
}

async function authorizedFetch(url: string, init: RequestInit = {}) {
  const token = await accessToken();
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return fetch(url, { ...init, headers });
}
