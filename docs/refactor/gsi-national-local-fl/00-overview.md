# GSI National-Local Foundation Data Integration

## Objective

Integrate Japan's national designated evacuation dataset from the Geospatial Information Authority of Japan (GSI) into the Foundation Data Layer (FL), while retaining Yokohama City data as an independent local validation and enrichment source.

This refactor establishes two FL contracts:

1. When national and local datasets describe the same domain, the national dataset is the base coverage and the local dataset validates or enriches it.
2. Every FL dataset records source and retrieval timestamps so that changes can be compared and scheduled refreshes can be audited.

## Why this is one refactor

The acquisition script, source registry, evidence fusion, architecture documentation, and data catalog all encode the same source-precedence decision. Landing only part of the change would leave either runtime behavior or audit documentation inconsistent, so they are delivered in one PR with separately reviewable commits.

## Scope

- Status: Completed — merged as PR #2
- Download and normalize GSI designated shelters and designated emergency evacuation places for Yokohama.
- Record source update time and retrieval time in generated FL artifacts.
- Use GSI records as the national base in the facility evidence view.
- Match Yokohama City records as local validation/enrichment and retain unmatched local records as explicitly labelled supplements.
- Document source semantics, licensing, commercial-use cautions, and the FL precedence/timestamp contract in English, Japanese, and Chinese where repository policy requires it.
- Add automated tests for acquisition normalization, source reconciliation, timestamps, and task orchestration.

## Non-goals

- A nationwide user-selectable municipality downloader.
- Database migration or a generic FL schema/API redesign.
- Automated legal interpretation of source licences.
- Treating either GSI or Yokohama data as real-time emergency guidance.

## Architectural decision

GSI is selected as the base because it provides a nationally standardized, script-downloadable distribution for municipality code `14100`. Yokohama City remains valuable because its local categories and descriptions can validate and add operational context. A reconciled record therefore preserves provenance from both sources instead of silently overwriting one with the other.

The accepted trade-off is a small reconciliation step and possible source disagreement. This is preferable to using a local-only dataset with weaker national scalability, or replacing the local dataset and losing a useful independent check.

## Delivery plan

- [01-gsi-evacuation-pr1.md](01-gsi-evacuation-pr1.md): one PR containing acquisition, reconciliation, documentation, and verification.

## Success criteria

- A direct project command can rebuild or refresh the GSI artifact without a paid service or API key.
- A normal data readiness check recognizes the GSI artifact and rebuilds it when permitted and missing.
- Facility evidence distinguishes national-only, nationally based/local-validated, and local-supplement records.
- Generated GSI records and source metadata contain source-update and retrieval timestamps.
- FL architecture documentation states the national-base/local-validation rule and timestamp requirement in all three required languages.
- The full unit-test suite passes.

