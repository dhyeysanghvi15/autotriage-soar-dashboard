export type ApiResult<T> = { ok: true; data: T } | { ok: false; error: string };

async function readJsonOrThrow(resp: Response) {
  const text = await resp.text();
  try {
    return text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Invalid JSON from server (${resp.status})`);
  }
}

export async function apiGet<T>(path: string): Promise<ApiResult<T>> {
  try {
    const resp = await fetch(path, { headers: { Accept: "application/json" } });
    const json = await readJsonOrThrow(resp);
    if (!resp.ok) return { ok: false, error: json?.detail ?? `HTTP ${resp.status}` };
    return { ok: true, data: json as T };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Request failed" };
  }
}

export async function apiPost<T>(path: string, body: unknown): Promise<ApiResult<T>> {
  try {
    const resp = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body)
    });
    const json = await readJsonOrThrow(resp);
    if (!resp.ok) return { ok: false, error: json?.detail ?? `HTTP ${resp.status}` };
    return { ok: true, data: json as T };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : "Request failed" };
  }
}

