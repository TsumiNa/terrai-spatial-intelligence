# AGENTS.md

Operating rules for AI coding agents working in this repository. Read this before making any change.

This file is the single source of agent guidance for this repository. `CLAUDE.md` only points here — do not duplicate content into it.

## 1. Always check `.github/instructions/` first

Before editing or creating any file, check `.github/instructions/` for instruction files whose `applyTo` glob pattern matches the file(s) you are about to touch, and follow their rules. This directory is the source of truth for repo-specific conventions and takes precedence over general habits or assumptions.

- Re-read the directory each time — instruction files are added/updated independently of this document, so do not rely solely on the summary below.
- If an instruction's `applyTo` pattern matches your target file, its rules are mandatory, not optional guidance.
- If two instructions conflict, prefer the more specific `applyTo` pattern and ask the user if the conflict is not resolvable.
- **When writing or editing an instruction file, keep it free of project-specific commands, module paths, and code symbols.** Instructions state what must be true; they must not name the CLI command, script, or constant that currently enforces it — those drift with every refactor and turn the instruction into a source of wrong information. Put the concrete commands here in `AGENTS.md` or in `CONTRIBUTING.md` instead.

Current instruction files (may be incomplete — always verify against the directory):

| File                                               | Applies to                               | Covers                                                                      |
| -------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------- |
| `branch-and-pr-workflow.instructions.md`           | `**`                                     | Branching, PR timing, and splitting a refactor into verifiable PR sequences |
| `in-branch-api-compat.instructions.md`             | (all)                                    | No compatibility wrappers/aliases for in-progress API changes               |
| `minimal-implementation-and-tests.instructions.md` | `**`                                     | Minimal abstraction/scope, required test coverage for new logic             |
| `repository-doc-boundaries.instructions.md`        | `**/{README,CONTRIBUTING}.md`, `docs/**` | Root entrypoints, `docs/` structure, language policy                        |
| `docs-data-cards.instructions.md`                  | `docs/data/**`                           | Dataset card sections, including `## Data description`                      |
| `color-palette.instructions.md`                    | `webapp/**`                              | Where color may be declared, and what to do when adding or changing one     |

## 2. Python environment: this project uses `uv`

All Python execution, dependency management, and environment setup goes through [`uv`](https://docs.astral.sh/uv/). Do not use bare `pip install`, `python -m venv`, `python3`, or a global/system interpreter.

- **Run everything through `uv run`**, e.g. `uv run python -m terrai_spatial serve --port 4176`. This guarantees the correct interpreter and dependencies from the project's managed environment.
- **Add/remove dependencies with `uv add <package>` / `uv remove <package>`.** Do not hand-edit the `dependencies` array in `pyproject.toml` without also updating `uv.lock` — let `uv` regenerate the lockfile instead of editing it manually.
- **Requires Python >= 3.11** (`requires-python` in `pyproject.toml`).
- **The geospatial stack is a base dependency** (`fiona`, `numpy`, `pillow`, `pyproj`, `rasterio`). There is no optional extra: `uv sync` installs everything the pipelines need, so no code path installs dependencies at runtime.
- **`[tool.uv] package = false`**: this repository is not built or installed as an importable package, and there is no `[build-system]` section. Do not add build-backend config or attempt `pip install -e .`.
- **Tests use `pytest`** (dev dependency group, installed by default via `default-groups = ["dev"]`). Write plain test functions with bare `assert`, not `unittest.TestCase` classes. Use the `tmp_path` and `monkeypatch` fixtures rather than `tempfile` and `unittest.mock.patch`.

  Tests are **colocated** next to the source file they exercise and named `<source>_test.py`, per `minimal-implementation-and-tests.instructions.md`. There is no `tests/` tree. `[tool.pytest.ini_options]` in `pyproject.toml` sets `testpaths` and `python_files = ["*_test.py"]`.

  ```bash
  uv run pytest                                   # whole suite
  uv run pytest terrai_spatial/cli_test.py        # one file
  uv run pytest -k feature_query                  # by name
  uv run pytest terrai_spatial/data_service_test.py::test_health_reports_all_file_backed_datasets_ready
  ```

  `scripts/__init__.py` makes `scripts` a package so `from scripts.<module> import ...` resolves from the repository root; do not remove it.

  | Source                           | Test                                  |
  | -------------------------------- | ------------------------------------- |
  | `terrai_spatial/api.py`          | `terrai_spatial/api_test.py`          |
  | `terrai_spatial/cli.py`          | `terrai_spatial/cli_test.py`          |
  | `terrai_spatial/data_service.py` | `terrai_spatial/data_service_test.py` |
  | `terrai_spatial/data_tasks.py`   | `terrai_spatial/data_tasks_test.py`   |
  | `scripts/fetch_tepco_grid.py`    | `scripts/fetch_tepco_grid_test.py`    |

## 3. CLI commands

The repo is not installable, so invoke the CLI as a module:

```bash
uv run python -m terrai_spatial serve            # API thread (:8000) + built frontend (:4176)
uv run python -m terrai_spatial api              # FastAPI only; docs at /docs
uv run python -m terrai_spatial frontend         # built webapp/dist only; expects API on :8000
uv run python -m terrai_spatial data status      # per-task readiness table
uv run python -m terrai_spatial data ensure      # repair missing/stale derived data
uv run python -m terrai_spatial build --only joint
uv run python -m terrai_spatial fetch grid       # any task that downloads; see --help
uv run python -m terrai_spatial validate         # asset + JSON + contract checks
```

`serve`/`api` run `ensure_data` at startup; `--offline` skips downloads, `--no-ensure-data` skips the check entirely.

The exhibition frontend in `webapp/` (Svelte 5 + Vite + TypeScript, MapLibre GL + deck.gl) has its own npm toolchain — commands in `CONTRIBUTING.md`; its tests are colocated `*_test.ts` files run by Vitest, plus Playwright under `webapp/e2e/`. `serve`/`frontend` serve the built `webapp/dist` and refuse to start until `npm run build` has produced it. `webapp/openapi.json` and `webapp/src/lib/api/schema.d.ts` are generated by `npm run generate:api`, never hand-edited; `terrai_spatial/api_test.py` fails when they drift from the FastAPI application.

## 4. Color is locked to the palette

`color-palette.instructions.md` holds the rules. This section is the concrete form they take today.

**The two declarations.** `webapp/src/lib/theme.ts` is the only TypeScript file that may write a color literal; the `@theme` block in `webapp/src/app.css` declares the same set as `--color-*` tokens. Names correspond as kebab ↔ camelCase: `--color-exposure-outline` ↔ `exposureOutline`. A test compares them by name *and* value, so they cannot drift — which they already had, `lime` meaning `#a9d96e` in the stylesheet and `#8fc85a` on the map.

**How it is enforced.** `--color-*: initial` clears the default palette, so `bg-blue-500` is not generated at all. `webapp/src/lib/palette_guard.ts` then rejects arbitrary color utilities in class attributes, and color literals in `.svelte` files, in `.ts` files other than `theme.ts`, and in any `.css` file outside its `@theme` block. `app.css` is the single exception: it predates the rule and is held to an exact inventory instead, so a new literal there fails too, through a different assertion. Failures name the file and the value:

```
{ "file": "src/lib/components/Hero.svelte",
  "reason": "arbitrary color utility",
  "value": "bg-[#ff6600]" }
```

**Changing a value** — edit both declarations in the same commit, then regenerate the screenshot baselines and show the images in the pull request:

```bash
cd webapp && npx playwright test e2e/visual_test.ts --update-snapshots
```

**Adding a color** — add to both, with corresponding names. This is normal; do not use an arbitrary value to avoid it.

```css
/* webapp/src/app.css, inside @theme */
--color-flood-risk: #2f6f9f;
```
```ts
// webapp/src/lib/theme.ts
floodRisk: "#2f6f9f",
```

**Using a color** — `class="bg-forest text-paper"`, `var(--color-forest)` in a stylesheet, or `palette.transmission` in TypeScript.

**The lock is on color, not geometry.** `p-[13px]`, `rounded-[7px]` and `w-[238px]` are legitimate, and so are arbitrary variants such as `data-[state=open]:`. A check that rejects those is broken.

**Two known items.** `lime` (`#a9d96e`, interface accent) and `hub` (`#8fc85a`, map fill) are deliberately separate; merging them changes what the map renders and belongs to the redesign. `app.css` also carries 59 colors picked by eye before this rule, asserted as an exact set in `palette_guard_test.ts` — adding one fails, and so does removing one without updating the list.

## 5. Architecture

Three tiers, each with one chokepoint file:

**1. Data pipelines — `terrai_spatial/data_tasks.py`.** A declarative `TASKS` registry of `DataTask` records (script, inputs, outputs, dependencies, network/remote-extra flags). `ensure_data()` topologically orders tasks, decides missing/stale/blocked from file existence + mtime + JSON validity, and shells out to the matching `scripts/*.py`. The pipeline scripts themselves are standalone and know nothing about the registry. Adding a pipeline = write the script *and* register its `DataTask`; nothing else discovers it.

**2. Read-only API — `terrai_spatial/data_service.py` + `api.py`.** `DATASETS` is the only place that maps a stable public key (`buildings`, `solar`, `hubs`, …) to a file path under `data/`. The browser only ever sees keys. `DataService` mtime-caches loads, and `recommendations()` computes every server-ranked action queue (filter + sort per analysis) — ranking logic lives here, not in the frontend. `api.py` is a thin FastAPI wrapper: `/api/v1/{health,catalog,bootstrap,datasets/{key},features/{key},recommendations/{analysis}}`, plus `data/` mounted at `/api/v1/assets` (map tiles are served from there). CORS is locked to localhost origins.

**3. Frontend — `webapp/`.** The Svelte app fetches `/bootstrap` once through the typed OpenAPI client (`src/lib/api/client.ts`, API origin overridable via `?api=`) and renders everything from that payload. `src/lib/audit.ts` builds the per-value provenance records (`raw` / `calculation` / `model` kinds) behind every dashed number — the "auditable" claim is this module. `src/lib/i18n/messages.ts` holds the compile-checked trilingual catalogs: **the English catalog defines the typed key set**, and a missing `zh`/`ja` entry fails `npm run build`. One imperative module (`src/lib/map/map.ts`) owns the MapLibre instance and its deck.gl overlay; layer colors and thresholds are data in `src/lib/map/style-rules.ts`; panels are view models in `src/lib/modules.ts`. Do not wrap map internals in reactive state.

The FL → SL → AL conceptual language (Foundation / Synthetic / Application layer) that documentation and UI copy use is defined in [docs/architecture/FL_SL_AL_CONCEPT.md](docs/architecture/FL_SL_AL_CONCEPT.md). Today's scores are transparent AL heuristics, not SL model predictions — do not blur that distinction in code or copy.

## 6. String-level contracts

`terrai validate` (`command_validate` in [terrai_spatial/cli.py](terrai_spatial/cli.py)) asserts on *literal substrings* in `terrai_spatial/api.py` and several docs — route paths, mermaid `sequenceDiagram` counts, trilingual cross-links — plus the module registry in `webapp/src/lib/modules.ts`. The old frontend string checks were retired with the Leaflet runtime: UI flows are covered by Playwright (`webapp/e2e/`), payload fields by the typed client, and translations by the compile-checked catalogs. Renaming a route still breaks validation far from the edit.

`cli.py` is the single definition of these contracts: [terrai_spatial/cli_test.py](terrai_spatial/cli_test.py) asserts that `command_validate` passes rather than re-implementing the checks, and `multilingual_documents()` is the only place that decides which documents need language partners. Do not copy either into a test.

## 7. Documentation rules

`repository-doc-boundaries.instructions.md` is authoritative; `terrai validate` and `terrai_spatial/cli_test.py` enforce it mechanically.

- **Three languages only under `docs/architecture/`, `docs/data/`, and `docs/summary/`.** English is the unsuffixed canonical `name.md`, with `name.ja.md` and `name.zh.md` partners; each links to the other two. `multilingual_documents()` in `cli.py` is the single definition of that scope.
- **Dataset cards and summary groups use one subfolder per group.** Each direct child contains `README.md`, `README.ja.md`, and `README.zh.md`. The data catalog is the sole exception and lives directly at `docs/data/README.*`; no Markdown files sit directly under `docs/summary/`.
- **Everything else is English-only** — root `README.md`, `CONTRIBUTING.md`, `docs/README.md`, and everything under `docs/refactor/` and `docs/others/`. Do not add language-suffixed partners there unless explicitly requested.
- No loose files directly under `docs/` except `docs/README.md`. Everything else goes in `architecture/`, `refactor/`, `summary/`, `data/`, or `others/`.
- Refactor plans are named `NN-slug-prN[a].md` inside a folder that has a `00-overview.md` (`REFACTOR_PLAN_PATTERN`).
- `README.md` stays user-facing; developer-facing structure/workflow content belongs in `CONTRIBUTING.md`.

## 8. Data and licensing

Small analysis products and manifests under `data/` (~31 MB) are committed; the large acquisitions are gitignored reproducible pipelines:

- The MLIT foundation data `data/mlit/` — one acquisition scope, the mainland-Kanto window (~2.3 GB of GeoJSON, ~2.7M features), produced by `fetch mlit` and provisioned automatically by `data ensure`. CI restores it from the Actions cache keyed on the acquisition table and fetches only when that table changes. There is no separate demo subset: every environment holds the same data world.
- TEPCO source CSVs/ZIPs and `*.local.json` (publicly readable but redistribution-prohibited). Only the derived `data/mobara/tepco_grid_screen.json` is committed; the `grid` task re-downloads the cache on demand.
- PLATEAU source archives and expanded 3D Tiles (reproducible on-demand caches; the selection, retrieval manifests and audit indexes are committed).

## 9. Working style

- Branch/PR: check the current branch's PR state *before* editing (see `branch-and-pr-workflow.instructions.md`). Don't commit non-trivial work to `main`.
- No compatibility wrappers, aliases, or adapter layers for in-progress API changes within a branch — update call sites directly.
- Minimal abstraction and minimal scope: no options, flags, or refactors the request didn't ask for.
- Commit subjects follow `type: imperative summary` (`feat:`, `docs:`, `style:`).
