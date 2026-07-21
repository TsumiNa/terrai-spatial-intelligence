# PR4 Plan: Port Components to the Theme

- Status: Planned
- Refactor: `ui-design-system`
- PR: #4

## Goal

Restyle all ten components through the theme and delete the rules they replace, so there is one styling system rather than two.

## Scope

1. Port all ten: the nine under `webapp/src/lib/components/` — `Sidebar`, `Topbar`, `Hero`, `Metrics`, `QueuePanel`, `MapCard`, `AuditTrigger`, `FeaturePopup`, `AuditDrawer` — plus `webapp/src/App.svelte`.
2. Delete each `app.css` rule as its component stops needing it. `app.css` should retain only genuinely global concerns — resets, base typography, and anything the map libraries need.
3. Keep the audit affordance exactly as it renders today. The dashed underline marking an auditable value is product surface.
4. Check the longest English string in every ported component against the fixed sidebar width, and against the narrow breakpoint.

## Non-goals

No redesign. No markup restructuring beyond what styling requires. No accessibility work — stage 05. No new components.

## Implementation notes

- Port one component per commit. A single commit touching all ten makes the screenshot diff unreadable, which defeats the reason the baseline exists.
- **Small visual diffs are acceptable here, and are reviewed rather than forbidden.** The earlier rule demanded pixel neutrality; that was dropped deliberately. The applications are exploratory and about to be rewritten, so preserving spacing that was set by eye costs more than it is worth. What must not happen is a diff nobody looked at: regenerate baselines as part of the review, with the images in the pull request, not to turn a red build green.
- The screenshots still earn their place — they turn "did anything move" from an opinion into an artefact. Their purpose in this stage is disclosure, not prohibition.
- `MapCard` is the largest at 133 lines and interacts with the map canvas; port it last, once the pattern is settled.

## Acceptance

- Any screenshot diff is small, deliberate, and shown in the pull request with regenerated baselines.
- `app.css` contains only global concerns; every component-specific rule is gone.
- The theme enforcement check from stage 03 passes without new exceptions.
- The dashed audit affordance renders identically. This one is not negotiable: it is the product's signal that a value is auditable.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
