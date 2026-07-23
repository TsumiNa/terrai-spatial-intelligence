# PR3 Plan: Subsurface and Analysis Overlays

- Status: Planned
- Refactor: `local-3d-work-mode`

## Goal

The local scene becomes a full above-and-below-ground workspace: the observed
subsurface renders beneath the PLATEAU buildings, and the SL overlays and AL
simulation results for the selected area are composed into the same scene, each
carrying its provenance and its observed / synthetic / unresolved standing.

## Scope

- Compose the already-integrated observed subsurface (the UC24 underground
  scenes) below ground for the selected footprint, aligned to the same terrain
  and coordinate frame as the PLATEAU buildings above — reusing the
  renderer-neutral scene handoff so above- and below-ground share one scene.
- Bring the SL overlays and AL simulation results scoped to the selection into
  the scene as toggleable layers, keyed to the same mesh/bbox.
- Preserve the FL → SL → AL distinction in presentation: observed (FL/subsurface,
  PLATEAU measured), synthetic (SL/AL model output), and unresolved are visually
  and in-provenance distinct — a simulated value never reads as measured.
- Per-layer provenance and legend, so any displayed value routes back to source,
  formula, and limitation, consistent with the product's auditability claim.

## Non-goals

- No new subsurface data acquisition — this composes what is already integrated.
- No change to the SL model stack or AL simulation math — this presents their
  outputs in the local scene, it does not alter them.
- No localisation/telemetry (PR4).

## Implementation steps

1. Place the observed subsurface under the buildings in the local scene, aligned
   to the shared terrain/coordinate frame.
2. Add the SL overlay and AL simulation layers scoped to the selection, as
   toggles with a legend.
3. Enforce the observed/synthetic/unresolved visual + provenance distinction
   across all local-scene layers.
4. e2e: a selection over an area with subsurface + SL/AL shows all tiers,
   correctly attributed and distinguished.

## Acceptance

- A selection over an area with integrated subsurface renders buildings above and
  the observed subsurface below in one aligned scene, with SL/AL overlays
  toggleable.
- Observed vs synthetic vs unresolved is distinct visually and in each layer's
  provenance; every value routes back to source.
- `cd webapp && npm run build && npm run test`, the Playwright suites, and
  `uv run python -m terrai_spatial validate` pass.
