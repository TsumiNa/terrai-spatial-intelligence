# MLIT Foundation Data Expansion

## Context

TerrAI currently demonstrates terrain, roads, facilities, solar context, satellite embeddings, and grid screening, but several authoritative MLIT layers that directly affect hazard, infrastructure, land-use, and valuation decisions are absent from the Foundation Data Layer (FL).

The requested sources span two distribution families with different constraints:

- National Land Numerical Information datasets, mostly current CC BY 4.0 / PDL-compatible releases.
- National Land Survey datasets, which require attribution, prohibit unchanged redistribution, and may trigger Survey Act procedures when background-map survey成果 are reproduced or used.

The legacy W05 river dataset is explicitly marked non-commercial and must not silently enter a customer-facing commercial demo.

## Decision

Add one MLIT source-pack pipeline that downloads official archives, normalizes and clips redistributable layers to practical Yokohama/Mobara context windows, records source and retrieval timestamps, and exposes the resulting FL files through on-demand API keys.

Keep the W05 river pipeline separate, opt-in, local-only, Git-ignored, and absent from customer bootstrap/API output because its source page explicitly marks commercial use as prohibited.

Do not add the new layers to the existing frontend bootstrap payload. The API will distinguish application/bootstrap datasets from larger on-demand FL datasets, preventing every exhibition page load from transferring all source layers.

## Alternatives considered

### Load all new datasets in bootstrap

Rejected because large hazard and mesh layers would slow every page load even when no application module uses them.

### Catalog the sources without downloading or normalizing them

Rejected because documentation-only entries would not be operational FL integrations and could not support API queries or later AL modules.

### Commit every downloaded archive

Rejected because it would bloat Git, redistribute unnecessary originals, and violate or complicate source-specific redistribution terms. Only normalized, clipped, redistributable outputs are committed; raw archives remain temporary.

### Treat the legacy river dataset like the open datasets

Rejected because the individual W05 page explicitly says non-commercial. The local-only task preserves technical accessibility without misrepresenting commercial rights.

## Scope

- MLIT river data (W05), local-only and non-commercial.
- 1:50,000 land classification basic survey.
- All-period flood-history GIS.
- Land-history survey GIS.
- Landslide warning zones (A33, 2025).
- Multi-stage flood assumptions (A53, 2025).
- Published land prices (L01, 2026).
- Residential land development / special embankment regulation zones (A56, 2025).
- Railway data (N02, 2025).
- Fine land-use mesh (L03-b, 2021).
- Prefectural land-price survey (L02, 2025).
- Data tasks, source registry, on-demand API catalog, tests, and trilingual data cards.

## Non-goals

- New customer-facing analysis screens or changing existing AL scores.
- Nationwide preloading into Git or the browser.
- Replacing authoritative legal, cadastral, valuation, flood-control, or engineering decisions.
- Claiming commercial rights for W05 river data.
- Automating Survey Act legal determinations.

## Consequences

- FL gains authoritative inputs relevant to all three current application domains.
- Initial rebuilds require substantial network transfer and optional geospatial dependencies; committed normalized clips keep normal demo startup offline.
- New source layers are queryable on demand but remain outside business scores until an AL-specific validation and audit design is added.
- Restricted-source behavior is enforced by task/API boundaries rather than documentation alone.

## Delivery plan

- [01-mlit-source-pack-pr1.md](01-mlit-source-pack-pr1.md): integrate and document the complete MLIT source pack in one independently verifiable PR.

