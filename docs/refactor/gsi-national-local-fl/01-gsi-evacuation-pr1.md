# PR1 — GSI Evacuation Foundation Data

## Goal

Make GSI designated evacuation data a reproducible national FL base for the Yokohama demo and reconcile it with Yokohama City's local disaster-base dataset.

## Implementation steps

1. Add a deterministic downloader/normalizer for GSI designated shelters, designated emergency evacuation places, and municipality publication history.
2. Register the generated artifact as an automatic, network-aware data task and add it to downstream evidence dependencies.
3. Rework facility evidence generation so GSI is the base, Yokohama data validates/enriches matched facilities, and unmatched local facilities remain explicit supplements.
4. Propagate source-update and retrieval timestamps into source metadata and reconciled evidence.
5. Add the GSI source card and update the Yokohama card and data catalog in English, Japanese, and Chinese.
6. Add the FL precedence and timestamp contract to the trilingual architecture documentation.
7. Rebuild generated evidence and run the complete unit-test and data-validation checks.

## Commit plan

1. `docs: plan GSI national-local FL integration`
2. `feat: add timestamped GSI evacuation foundation data`
3. `feat: reconcile national and local facility evidence`
4. `docs: document FL source precedence and GSI data`
5. `test: verify GSI acquisition and reconciliation` (may be combined with the implementation commits when tests are tightly coupled)

## Review focus

- National/local precedence is explicit in both code and documentation.
- No local record is silently dropped; unmatched records are labelled as supplements.
- GSI emergency-place hazard designations are not confused with designated-shelter status.
- Timestamp names distinguish the source's publication/update time from TerrAI's retrieval time.
- The downloader uses only stable public endpoints and standard project dependencies.

## Rollback

Revert this PR. Existing Yokohama source data remains in the repository, so reverting restores the previous local-only evidence build without a data migration.
