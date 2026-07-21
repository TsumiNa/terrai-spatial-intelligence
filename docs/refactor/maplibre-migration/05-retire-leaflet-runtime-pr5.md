# PR5 Plan: Retire the Leaflet Runtime

- Status: Completed
- Refactor: `maplibre-migration`
- PR: #17

## Goal

Make the Svelte application the served exhibition, delete the hand-written frontend, and replace the literal-string contracts that guarded it.

## Scope

1. `terrai serve` and `terrai frontend` serve the built output.
2. Delete `frontend/app.js`, `audit.js`, `i18n.js`, `index.html`, `styles.css` and `vendor/leaflet.*`.
3. Update `REQUIRED_FILES` and remove the `exhibition_contract` string checks in `terrai_spatial/cli.py` that grep the deleted files. Keep the checks that still describe something real; delete the ones the type system or Playwright now covers.
4. Update `docs/architecture/FRONTEND_BACKEND.*` — all three languages — to describe the new call structure.
5. Update `README.md`, `CONTRIBUTING.md` and `AGENTS.md` for the build step.

## Non-goals

No new capability. This stage removes and rewires only.

## Implementation notes

- This is the one stage where a move and its reference updates must land together. Deleting the files in one PR and fixing `cli.py` in another leaves the default branch red.
- Do not keep the old frontend behind a flag. Per `.github/instructions/in-branch-api-compat.instructions.md`, if a stage cannot be green without a compatibility shim, the sequence is ordered wrong.

## Acceptance

- A clean checkout builds and serves the exhibition with no reference to Leaflet.
- No file under `frontend/` is referenced by `cli.py`, tests or documentation.
- The call-structure document matches the running application in all three languages.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
