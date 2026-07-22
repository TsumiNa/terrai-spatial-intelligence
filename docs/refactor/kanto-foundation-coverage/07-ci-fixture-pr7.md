# PR7 Plan: CI Provisions a Committed Fixture

- Status: In progress
- Refactor: `kanto-foundation-coverage`

## Goal

CI never fetches or caches the full Kanto acquisition: it copies a small
committed fixture — the exact windows the test suites query, derived from a
real acquisition — into `data/mlit` and builds the store from that. The
product keeps its one scope; the fixture is test infrastructure.

## Scope

- `scripts/build_mlit_fixture.py` (+ `mlit_fixture` task, opt-in): clips every
  acquired product to the fixture windows (Yokohama for the Playwright suite,
  Tokyo/Koshigaya/Hachioji for the identity matrix) through the streaming
  reader and the atomic streamed writer, provenance intact, with a manifest
  recording the derivation.
- `data/mlit_fixture/` committed (~57 MB, ~25k features).
- The three workflows replace the Actions-cache + fetch-on-miss steps with a
  single `cp -a data/mlit_fixture data/mlit`.
- The identity matrix's Saitama window moves from Omiya to Koshigaya, where
  the A53 multi-stage flood data actually has features — an empty-vs-empty
  comparison proves nothing.
- `AGENTS.md` §8 documents the fixture.

## Non-goals

- No service or acquisition changes; local and exhibition environments keep
  running `fetch mlit` for the full window.
- No second product scope: the fixture never serves outside test provisioning.

## Acceptance

- With the fixture copied into `data/mlit`: store build in seconds, full
  pytest green, Playwright suite green — measured locally before the PR and
  confirmed by CI wall-clock returning to the pre-acquisition baseline.
- `terrai validate` passes; the fixture derivation is unit-tested without
  real data.
