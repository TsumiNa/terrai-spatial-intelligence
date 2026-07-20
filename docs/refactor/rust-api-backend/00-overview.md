# Rust API Backend

- Date recorded: 2026-07-20
- Status: **direction only — not started, no PR stages planned**
- Precondition: the business scope is settled

## Why this is recorded now

This is a stated direction, not an active refactor. It is written down so the decisions being made today do not accidentally foreclose it, and so the trigger for starting it is explicit rather than a feeling that things have got slow.

## The direction

As the Foundation Data Layer grows, the FastAPI service is expected to stop meeting response requirements for querying and combining data. The intended answer is to rewrite the API backend in Rust, move as much Python data processing as possible into preprocessing, and call Python from Rust only where it remains necessary.

At that point the technology stack is considered settled. Frontend migration questions become ordinary product and performance work rather than platform decisions.

## Why the current architecture leaves room for it

The seam already exists, and it is narrow.

- `terrai_spatial/data_service.py` is the only component that knows where datasets live on disk. The browser sees stable public keys, never paths.
- The API is read-only. There is no write path, no ORM and no session state to port.
- The web layer is roughly 380 lines against roughly 1,951 lines of pipeline and geospatial code. A rewrite replaces the small half.
- `terrai_spatial/data_tasks.py` is already an offline pipeline registry that produces files. "Move Python work into preprocessing" is a continuation of how the project already runs, not a new idea.
- The planned frontend migration generates its client from the OpenAPI schema, so the browser does not care which language serves the contract, provided the contract does not change.

Keeping that seam narrow is the cheapest thing that can be done today to preserve this option. Anything that lets dataset paths, ad-hoc query logic or response shaping leak outside `data_service.py` makes the eventual rewrite larger.

## Alternatives that should be measured first

A language rewrite is one answer to slow queries. It should not be the first thing tried, because the likely first bottleneck is not the language.

Today every request loads whole JSON and GeoJSON files, caches them by modification time, and filters and sorts in memory with no spatial index. Long before Python itself is the constraint, the following will be:

- full-file parsing where a query touches a handful of features;
- linear scans where a spatial index would answer in logarithmic time;
- keeping entire collections resident to serve a bounding-box query.

These are addressed by changing the storage and query layer, not the language — a columnar or spatial store, an on-disk format that supports partial reads, or a real spatial index. Any of those may remove the pressure entirely, and each is far cheaper than a rewrite.

The honest sequence is: measure, fix the data layer, measure again, and only then decide whether Rust is answering a question that still exists.

## Design question to settle before starting

"Call Python from Rust when necessary" has two very different implementations.

**Embedded** (PyO3 in the server process) keeps a single deployable but inherits the GIL, Python's memory profile, and a build that must ship a CPython runtime. Concurrency characteristics become hard to reason about precisely where the rewrite was supposed to help.

**Separated** (Python stays an offline pipeline, or an online model service behind its own boundary) keeps the Rust service simple and preserves the existing pipeline design. It costs a network hop for the rare online case.

Given the reason for the rewrite is throughput under concurrent queries, embedding the runtime that motivated the rewrite deserves scrutiny. Separation is the safer default unless a specific case proves otherwise.

## What must survive the rewrite

- **Auditability.** Every displayed value keeps its route back to source, formula and limitation. This is the product's core claim and it is expressed today in the API responses, not only in the browser.
- **Stable dataset keys.** The public contract is the thing the frontend and any future field client depend on. A rewrite that changes it is two migrations, not one.
- **Offline operation.** The demo runs with no network. Whatever replaces the current file-backed service keeps that property.
- **The observed / synthetic / unresolved distinction.** It is a data-model commitment from the FL → SL → AL architecture, not a presentation detail.

## Non-goals

Nothing here is scheduled. No PR stages are planned, no language evaluation has been run, and no performance measurement exists yet to justify starting. When it starts, this folder gains numbered plan files like any other refactor.
