# PR4 Plan: Port Components to the Theme

- Status: Planned
- Refactor: `ui-design-system`
- PR: #4

## Goal

Restyle the eight components through the theme and delete the rules they replace, so there is one styling system rather than two.

## Scope

1. Port each component: `Sidebar`, `Topbar`, `Hero`, `Metrics`, `QueuePanel`, `MapCard`, `AuditTrigger`, `FeaturePopup`, `AuditDrawer`, and `App`.
2. Delete each `app.css` rule as its component stops needing it. `app.css` should retain only genuinely global concerns — resets, base typography, and anything the map libraries need.
3. Keep the audit affordance exactly as it renders today. The dashed underline marking an auditable value is product surface.
4. Check the longest English string in every ported component against the fixed sidebar width, and against the narrow breakpoint.

## Non-goals

No visual change. No markup restructuring beyond what styling requires. No accessibility work — stage 05. No new components.

## Implementation notes

- Port one component per commit. A single commit touching all eight makes the screenshot diff unreadable, which defeats the reason the baseline exists.
- Any screenshot diff is a defect in this stage, not an improvement. If a diff looks better, it still fails: this stage is defined as visually neutral, and a better version belongs to a design change that is reviewed as one.
- `MapCard` is the largest at 133 lines and interacts with the map canvas; port it last, once the pattern is settled.

## Acceptance

- Stage 01 screenshots pass unchanged across all three languages and both viewports.
- `app.css` contains only global concerns; every component-specific rule is gone.
- The theme enforcement check from stage 03 passes without new exceptions.
- The dashed audit affordance renders identically.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
