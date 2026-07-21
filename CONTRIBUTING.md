# TerrAI Development and Contribution

## Local development

```bash
uv sync
cd webapp && npm install && npm run build && cd ..
uv run python -m terrai_spatial validate
uv run pytest
uv run python -m terrai_spatial serve --port 4176
```

The exhibition frontend lives in `webapp/`; FastAPI and data services in `terrai_spatial/`; directly executable data tasks in `scripts/`; and file-backed foundation data and caches in `data/`.

## Frontend toolchain (`webapp/`)

The exhibition frontend is a Svelte 5 + Vite + TypeScript application in `webapp/`, rendering the map with MapLibre GL and deck.gl. `terrai serve` and `terrai frontend` serve the built output from `webapp/dist` and refuse to start until it exists (see the [MapLibre migration](docs/refactor/maplibre-migration/00-overview.md)).

Requires Node.js >= 22 alongside `uv`.

```bash
cd webapp
npm install                  # once
npm run dev                  # dev server on http://127.0.0.1:4310 (e2e uses the preview build on 4300)
npm run build                # static output in webapp/dist/
npm run check                # svelte-check over the TypeScript sources
npm test                     # Vitest unit tests (colocated *_test.ts)
npm run test:e2e             # Playwright smoke test (npx playwright install chromium once)
npm run generate:api         # regenerate webapp/openapi.json and src/lib/api/schema.d.ts
```

`webapp/openapi.json` and `webapp/src/lib/api/schema.d.ts` are generated from the FastAPI application and committed. Never hand-edit them: after any API route or response change, run `npm run generate:api` — `terrai_spatial/api_test.py` fails while the committed schema drifts from the live application.

## Documentation convention

Project documentation belongs in the five `docs/` categories: `architecture`, `refactor`, `data`, `summary`, and `others`. Documents in `architecture`, `data`, and `summary` require an English `.md`, Japanese `.ja.md`, and Chinese `.zh.md` version. English is always the unsuffixed default. Every data or summary group lives in its own subfolder with `README.*` filenames. All other locations use English-only `.md` documents by default. See [repository-doc-boundaries.instructions.md](.github/instructions/repository-doc-boundaries.instructions.md) for detailed boundaries and naming.

Run `uv run python -m terrai_spatial validate` after adding or changing documentation. The validator discovers documents under the three multilingual directories automatically and checks their language partners and navigation. It also enforces directory boundaries, refactor naming, and required data-card sections.

## Visual baselines

`webapp/e2e/visual_test.ts` compares the exhibition chrome against committed screenshots. They are platform specific — fonts and rasterisation differ between macOS and the Linux runner — so both suffixes are committed and Playwright picks the right one.

Regenerate deliberately, never to turn a red build green:

- **Locally**, for the platform you are on: `cd webapp && npx playwright test e2e/visual_test.ts --update-snapshots`
- **For Linux**, run the `Visual baselines` workflow from the Actions tab, download the `visual-baselines-linux` artifact, review every changed image, and commit the ones you intend to keep.

A diff during a refactor is a defect. A diff during an intended redesign is the thing being reviewed.

## Branches and PRs

Follow [branch-and-pr-workflow.instructions.md](.github/instructions/branch-and-pr-workflow.instructions.md): use one branch/PR per objective; continue on an existing branch when its PR has the same objective; and record reviewable stages in the relevant `docs/refactor/<refactor>/` plan.
