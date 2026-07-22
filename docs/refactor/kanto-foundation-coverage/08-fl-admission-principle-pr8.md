# PR8 Plan: FL Spatial-alignment Admission Principle

- Status: Planned
- Refactor: `kanto-foundation-coverage`

## Goal

Record the owner's standing admission principle for foundation data: a source that
has no GIS data and cannot be aligned spatially — through coordinates, elevation or a
defined projection — is never integrated as FL.

## Scope

- `docs/architecture/FL_SL_AL_CONCEPT.md` + `.ja.md` + `.zh.md`: an admission bullet
  in the FL section — spatial alignment is a requirement for integration; a source
  with no alignment path is recorded in `data/external/source_registry.json` as
  `confirmed_not_integrated` with the reason, never drawn through invented
  georeference.
- `scripts/fetch_mlit_foundation.py`: the module docstring cites the principle as a
  constraint on adding datasets to the acquisition table.

## Non-goals

- No mechanical validation of the principle (the registry has no per-source geometry
  schema to check against); it binds evaluation, and the registry records outcomes.
- No change to any integrated dataset — all current FL sources satisfy the principle
  (the KuniJiban boreholes align through coordinates and elevation; the PLATEAU
  scenes are georeferenced 3D Tiles).

## Acceptance

- `terrai validate` passes (trilingual partners intact); the three language versions
  state the same principle.
