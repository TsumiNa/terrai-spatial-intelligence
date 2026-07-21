# PR1 Plan: Toolchain and Typed API Client

- Status: Completed
- Refactor: `maplibre-migration`
- PR: #12

## Goal

Stand up Svelte 5 + Vite + TypeScript alongside the existing frontend, and generate TypeScript types from FastAPI's OpenAPI schema, so later stages port UI against a checked contract instead of magic strings.

## Scope

1. Add Vite, Svelte 5, TypeScript and a static adapter. The build emits to a directory `terrai serve` can serve, but the existing `frontend/` stays the default.
2. Generate types from `/openapi.json` (`openapi-typescript`) plus a typed fetch client. Commit the generated file so a schema drift is visible in review.
3. Add a check that fails when the committed types no longer match the live schema.
4. Add Vitest, and Playwright with one smoke test that the built shell loads.
5. Document the Node prerequisite and the new commands in `CONTRIBUTING.md` and `AGENTS.md`.

## Non-goals

No UI is ported. No map library is added. `frontend/` is untouched. `REQUIRED_FILES` and the exhibition contracts in `terrai_spatial/cli.py` are unchanged.

## Implementation notes

- Keep the generated types out of hand-editing: regeneration must be a single command.
- The drift check is the point of this stage. Without it, generated types rot into a second source of truth.
- Decide where built output lives before writing the serve path; changing it later touches `cli.py` twice.

## Acceptance

- The build produces static output and the existing exhibition still serves unchanged.
- Regenerating types against a running API produces no diff.
- The drift check fails when a route or response model changes without regeneration.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
