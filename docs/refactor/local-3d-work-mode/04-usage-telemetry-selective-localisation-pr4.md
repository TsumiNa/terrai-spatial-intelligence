# PR4 Plan: Usage Telemetry and Selective Localisation

- Status: Planned
- Refactor: `local-3d-work-mode`

## Goal

The project learns which areas are actually inspected and mirrors only those into
project storage — so hot areas load fast and work offline, without pre-caching a
region most sessions never open.

## Scope

- Lightweight telemetry recording which meshes are opened in local mode and how
  often, written where the project already keeps operational records (privacy-safe:
  mesh codes and counts, no user identity, no personal data).
- A `data status`-style report ranking meshes by open frequency, so localisation
  is a decision on evidence, not a guess.
- A localisation task (`automatic=False`, gitignored product, committed manifest —
  the same pattern as the acquisitions) that mirrors the PLATEAU models for a
  chosen set of hot meshes into project storage, pinned and provenance-tagged.
- The on-demand loader (`02`) prefers a localised mesh when present and falls back
  to the live PLATEAU fetch otherwise — transparent to the scene, faster and
  offline-capable where localised.

## Non-goals

- No automatic localisation — mirroring is an explicit, owner-triggered task on
  the telemetry evidence, not a background cache that grows on its own.
- No change to the rendering (PR2/PR3); this only changes where a mesh's models
  come from.
- No personal data in telemetry.

## Implementation steps

1. Add mesh-open telemetry (mesh code + count), privacy-safe, in the existing
   operational-record location.
2. Add the frequency report to the CLI/status surface.
3. Add the localisation task mirroring chosen meshes into pinned project storage
   with a manifest.
4. Make the loader prefer localised meshes; e2e that a localised mesh renders
   with the PLATEAU host blocked (offline), and an unlocalised one still falls
   back to live fetch.

## Acceptance

- Opening local scenes records mesh-open counts; the report ranks them.
- Running the localisation task on a chosen mesh mirrors its models; that mesh
  then renders offline (PLATEAU host blocked), while an unlocalised mesh still
  fetches live.
- Telemetry carries no personal data; `uv run python -m terrai_spatial validate`,
  `cd webapp && npm run build && npm run test`, and the Playwright suites pass.
