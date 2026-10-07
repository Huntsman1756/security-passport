import {
  ApiError,
  Passport,
  SearchResult,
  type Passport as TPassport,
} from "./types";

export class ApiRequestError extends Error {
  code: string;
  requestId?: string;

  constructor(code: string, message: string, requestId?: string) {
    super(message);
    this.code = code;
    this.requestId = requestId;
  }
}

async function get<T>(path: string, schema: {
  parse: (v: unknown) => T;
}): Promise<T> {
  const r = await fetch(path, { headers: { Accept: "application/json" } });
  const body: unknown = await r.json().catch(() => null);
  if (!r.ok) {
    const parsed = ApiError.safeParse(body);
    if (parsed.success) {
      const e = parsed.data.error;
      throw new ApiRequestError(e.code, e.message, e.request_id);
    }
    throw new ApiRequestError(
      "INTERNAL_DATA_INTEGRITY_ERROR",
      `HTTP ${r.status} for ${path}`,
    );
  }
  return schema.parse(body);
}

export function fetchPassport(isin: string): Promise<TPassport> {
  return get(`/api/v1/passports/${isin}`, Passport);
}

export function search(q: string) {
  return get(`/api/v1/search?q=${encodeURIComponent(q)}`, SearchResult);
}

export function status() {
  return get("/api/v1/status", {
    parse: (v: unknown) => v as Record<string, unknown>,
  });
}
