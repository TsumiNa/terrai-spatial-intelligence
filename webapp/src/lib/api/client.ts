import createClient from "openapi-fetch";

import type { paths } from "./schema";

/** Resolve the API origin the way the exhibition always has: `?api=` overrides. */
export function apiOrigin(search: string): string {
  const override = new URLSearchParams(search).get("api");
  return (override || "http://127.0.0.1:8000").replace(/\/$/, "");
}

/** Typed client over the generated OpenAPI schema; paths carry `/api/v1/…` in full. */
export function createApiClient(search: string = window.location.search) {
  return createClient<paths>({ baseUrl: apiOrigin(search) });
}
