import { createClient } from "@/lib/supabase/client";

// Same-origin proxy path (see next.config.mjs rewrites). Keeps API calls on the
// browser's warm connection to the Next server, avoiding Docker Desktop's
// per-connection published-port latency to :8000.
const BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/backend";

/** Fetch wrapper that attaches the Supabase access token to FastAPI requests. */
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  let token: string | undefined;
  try {
    const supabase = createClient();
    const { data } = await supabase.auth.getSession();
    token = data.session?.access_token;
  } catch {
    // No session (dev mode) — backend allows anonymous dev principal.
  }

  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}
