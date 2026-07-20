# PR1a Plan: Establish FL → SL → AL Conceptual Boundaries

[中文](01-concept-layers-pr1a.md) | [日本語](01-concept-layers-pr1a.ja.md) | [English](01-concept-layers-pr1a.en.md)

- Status: Completed
- Refactor: `fl-sl-al-platform`
- PR: #1 / part a

## Goal

Define one FL/SL/AL vocabulary covering observed/synthetic/unresolved evidence, multiscale missingness, quality gates, and current maturity, so AL heuristics cannot be presented as model predictions.

## Scope

1. Write the three-layer concept and Mermaid overview.
2. Review `geo_pfn` sparse-context results and limit them to mechanism evidence.
3. Map GSI, OSM, Yokohama, NASA POWER, TEPCO, and Satellite Embedding to FL.
4. State that current Yokohama/Mobara surface SL count is zero.
5. Add concept contract tests.

## Non-goals

No schemas, inter-layer APIs, databases, model registry, customer permissions, or production surface model.

## Acceptance

- Definitions, alternatives, consequences, and non-goals live in `00-overview` and `docs/architecture/FL_SL_AL_CONCEPT.en.md`.
- AL risk, suitability, and capacity proxies are never labeled SL.
- Chinese, Japanese, and English versions pass documentation validation.
