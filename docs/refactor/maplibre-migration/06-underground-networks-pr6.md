# PR6 Plan: Underground Utility Networks on the Map

- Status: Blocked — the dataset this stage renders is not integrated yet
- Refactor: `maplibre-migration`
- PR: #6

## Goal

Let a user see buried pipes, cables and facilities in regional context by lowering the camera and making the surface translucent, without the camera ever going below ground.

## Scope

1. An underground view mode: camera pitch lowered toward the ceiling raised in stage 03, buildings and basemap translucency increased, 3D terrain off.
2. Network layers at negative elevation, drawn with depth testing relaxed so they read through the surface rather than being occluded by it.
3. Depth and diameter carried as data; audit records for each network element covering source, survey date and positional accuracy.
4. A legend that distinguishes surveyed position from inferred position. Buried-utility records routinely carry both, and conflating them would misrepresent certainty.

## Non-goals

No soil, strata or predicted properties. Those are unreadable at regional scale and belong to stage 07. No camera descent below the surface.

## Blocking dependency

No underground network dataset is integrated. This stage cannot start until one exists and has a data card under `docs/data/`.

## Implementation notes

- `depthTest: false` produces the x-ray reading users expect from utility mapping. Verify it does not also let network lines draw over UI panels or the audit drawer.
- Positional accuracy for buried utilities is often metres, not centimetres. The audit record must say so; a crisp line implies a precision the data does not have.

## Acceptance

- Entering the underground view is a single action and leaves the analytical layers legible.
- Network elements are visible through the surface at the lowered camera angle.
- Clicking an element opens an audit record naming its source, survey date and positional accuracy.
- Surveyed and inferred positions are visually distinct.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
