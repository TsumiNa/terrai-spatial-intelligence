# ADR-0001: Adopt FL → SL → AL as the TerrAI Conceptual Architecture

[中文](0001-fl-sl-al-conceptual-layers.md) | [日本語](0001-fl-sl-al-conceptual-layers.ja.md) | [English](0001-fl-sl-al-conceptual-layers.en.md)

- Status: Accepted (Factor of Concept)
- Date: 2026-07-20
- Decision maker: TerrAI
- Scope: product narrative, Demo information architecture, and later-development boundaries

## Context

The current TerrAI Prototype combines several open spatial datasets and three application directions, but the former “unified data foundation” language did not clearly distinguish observations, deterministic transformations, future sparse predictions, and what application scores should consume.

Strategy v4 calls for a reusable engine core, standard delivery layer, and limited application layer. The Cyber Port/Haneda work demonstrates an entry capability—predicting subsurface parameters under sparse observation—not a complete application. The user further expressed this strategy as a Foundation Data Layer, Synthetic Data Layer, and Application Layer.

`geo_pfn` also shows that performance varies with context density, feature groups, and model size. This does not support a single “train once, fill everywhere” model; it supports scenario-specific model portfolios with applicability, calibration, and abstention.

## Decision

Adopt a three-layer conceptual architecture:

1. **FL** stores public, commercial, and customer-authorized observations plus deterministic transformations that preserve observational meaning; multiscale missingness is allowed.
2. **SL** non-destructively creates validated sparse imputations or augmentations over FL. Observed, synthetic, and unresolved must remain distinguishable and carry uncertainty and applicability boundaries.
3. **AL** converts qualified FL/SL evidence into scenario rules, rankings, and action outputs; it must not hide synthetic values as facts.

The decision also establishes that:

- Not all missing data should be imputed. Legal rights, ownership, and formal engineering conclusions remain unknown and trigger authoritative processes.
- The current spatial Demo has no validated surface SL. Risk, suitability, capacity proxies, and joint scores are AL heuristics.
- Google Satellite Embedding is an externally produced FL representation, not TerrAI-generated SL.
- `geo_pfn` is mechanism evidence for sparse transfer, model selection, and uncertainty; it is not evidence of accuracy for slope, road, or solar applications.

## Alternatives considered

### A. Continue “unified data foundation + multiple applications”

Simple, but continues to mix facts, proxies, and model imputations and cannot explain sparse prediction as a cross-application asset. Rejected.

### B. Each application maintains its own imputation model

Fast for short-term delivery, but customer learning and validation remain trapped in individual projects, violating the scaling test that each deployment should require less customization. Rejected as the overall architecture.

### C. FL → SL → AL

Allows open/customer data accumulation, sparse-prediction capability, and application revenue outputs to evolve separately, while placing uncertainty and audit boundaries before applications. Accepted.

## Consequences

Benefits:

- Reusable assets expand from shared map code to accumulated FL evidence and SL model capability.
- New applications can reuse SL instead of hiding missing-data logic in business scores.
- Observed/synthetic separation makes audit, uncertainty, and human review part of the product structure.
- Model portfolios and abstention have an explicit place across customers and sparsity levels.

Costs and risks:

- The product must accept that some regions remain unknown; a completely filled map cannot be the only definition of completion.
- Cross-scenario SL reuse requires strict validation; subsurface evidence cannot be transferred directly to surface tasks.
- Later development must handle versions, permissions, model selection, and lineage, but this ADR does not prescribe implementations.

## Non-goals

This ADR does not define data structures, APIs, databases, model registries, orchestration, deployment, or customer-permission mechanisms. Those require later Factor of Develop ADRs.

## Validation

- Engineering documentation contains one explicit FL/SL/AL definition and its non-goals.
- Internal architecture documents state current maturity truthfully; the customer Demo does not use internal concepts as primary navigation.
- Existing applications continue to run without relabeling heuristics as SL.
- The trilingual UI remains consistent.
- The PR records rationale, steps, evidence changes, and later-development questions.
