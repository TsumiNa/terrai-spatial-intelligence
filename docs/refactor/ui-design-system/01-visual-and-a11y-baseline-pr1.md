# PR1 Plan: Visual and Accessibility Baseline

- Status: Planned
- Refactor: `ui-design-system`
- PR: #1

## Goal

Record what the UI looks like and how it behaves today, so every later stage can prove it changed nothing it did not intend to. Nothing in production changes.

## Scope

1. Playwright screenshot coverage of every module the exhibition can show, in all three languages, at a wide and a narrow viewport. Cover the audit drawer open as well as closed — it is the component most likely to regress.
2. axe-core assertions on the same states, recording current violations rather than failing on them. The four known audit-drawer defects are expected to appear; they are fixed in stage 05, and the baseline is what proves it.
3. Pin the Playwright browser version so baselines are reproducible.
4. Decide and document where baselines are generated — CI or a developer machine — and write the regeneration command into `CONTRIBUTING.md`.

## Non-goals

No styling change. No accessibility fix. No Tailwind. Existing violations are recorded, not resolved.

## Implementation notes

- Screenshots must be deterministic: disable animations, wait for the map to settle or mask the map canvas entirely. A tile that loads a frame later will otherwise fail every run.
- Masking the map canvas is recommended. This stage protects the chrome; map rendering is covered by its own tests and would make every baseline flaky.
- Three languages times several modules is a large number of images. Prefer a few dense pages over exhaustive permutations, and name them so a failure says what broke.

## Acceptance

- `npx playwright test` passes on a clean checkout and regenerates identical images.
- Deliberately changing a colour in `app.css` produces a failing screenshot diff, confirming the net has holes in it nowhere it matters.
- The axe baseline lists the four audit-drawer defects, so stage 05 has something to prove against.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
