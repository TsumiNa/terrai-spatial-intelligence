import { expect, it } from "vitest";

import { apiOrigin } from "./client";

it("defaults to the local API origin", () => {
  expect(apiOrigin("")).toBe("http://127.0.0.1:8000");
});

it("honours the ?api= override", () => {
  expect(apiOrigin("?api=http://192.168.10.5:8000")).toBe("http://192.168.10.5:8000");
});

it("strips a trailing slash from the override", () => {
  expect(apiOrigin("?api=http://192.168.10.5:8000/")).toBe("http://192.168.10.5:8000");
});

it("falls back when the override value is empty", () => {
  expect(apiOrigin("?api=")).toBe("http://127.0.0.1:8000");
});
