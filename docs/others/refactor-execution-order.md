# Refactor Execution Order (temporary)

This is a working checklist for executing three planned refactors in sequence, written to be
picked up by a fresh session. It is **not** a plan document: every decision lives in the plan it
points to. Delete this file in the final PR of the sequence — that deletion is the last step
below.

Process: per `.github/instructions/branch-and-pr-workflow.instructions.md`, one PR at a time —
review, address feedback, squash merge, fetch main, then begin the next. Do not start a later
step while the current PR is open.

## Precondition (other session)

`maplibre-migration` stages 06 and 07 land first. Two pieces of doc housekeeping belong to that
work, both already owed:

- `docs/refactor/maplibre-migration/06-underground-networks-pr6.md` still says
  `Blocked — the dataset this stage renders is not integrated yet`; the dataset landed in PR #31,
  and the status flip its handoff promised was never made.
- `docs/refactor/underground-observation-foundation/00-overview.md` still says `In progress`
  although all three of its stages are `Completed`.

## Sequence

Each step is one PR. Statuses in the plan documents flip `Planned` → `In progress` → `Completed`
as each starts and merges.

1. **`data-pipeline-and-store` PR1** — shared pipeline library
   ([plan](../refactor/data-pipeline-and-store/01-shared-pipeline-library-pr1.md)).
   First because it is pure consolidation with byte-identical outputs, and every later step
   builds on the library. The underground scripts' de-facto sharing gets promoted here.
2. **`projected-crs-measurement` PR1** — projected measurement
   ([plan](../refactor/projected-crs-measurement/01-projected-measurement-pr1.md)).
   Second so its measurement module lands inside the library and every diff in this PR is a
   semantic change, none of it relocation. Regenerates `joint` and `evidence` outputs; the PR
   description must carry the before/after comparison and band-change count.
3. **`data-pipeline-and-store` PR2** — spatially indexed store
   ([plan](../refactor/data-pipeline-and-store/02-spatial-store-pr2.md)).
   Built on the library, against outputs already corrected by step 2.
4. **`data-pipeline-and-store` PR3** — store-backed service
   ([plan](../refactor/data-pipeline-and-store/03-store-backed-service-pr3.md)).
   Contract frozen, responses byte-identical, latency measured. The measurements also update
   `rust-api-backend`'s entry conditions.
5. **`on-demand-fl-delivery` PR1** — viewport-driven feature client
   ([plan](../refactor/on-demand-fl-delivery/01-windowed-feature-client-pr1.md)).
   Deliberately after step 4 so the windowed client's first consumer hits indexed queries, not
   linear scans. Includes API response compression.
6. **`on-demand-fl-delivery` PR2** — foundation layers as auditable overlays
   ([plan](../refactor/on-demand-fl-delivery/02-foundation-overlay-ui-pr2.md)).
7. **`on-demand-fl-delivery` PR3** — underground scene intake
   ([plan](../refactor/on-demand-fl-delivery/03-underground-scene-intake-pr3.md)).
   Last, and currently `Blocked`: finalize it against what `maplibre-migration` 06/07 actually
   built — especially the site-bundle endpoint PR7 owns — before implementing.

Final step, in the same PR as step 7 or a trailing docs PR: **delete this file** and flip any
remaining plan statuses.

## Deliberately not in this sequence

Gated stages whose triggers have not fired: `data-pipeline-and-store` PR4 (large layers out of
git; size/churn trigger), PR5 (Postgres cloud tier; cloud deployment scheduled or first
authoritative table), and `rust-api-backend` (requires step 4's measurement plus a settled
business scope).
