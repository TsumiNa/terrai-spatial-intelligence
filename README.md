# TerrAI Spatial Intelligence

TerrAI is a spatial-decision Demo for clean energy and climate resilience. It combines public foundation data, traceable augmented evidence, and scenario analysis to answer “where should we investigate first, why, and can the evidence be trusted?” through maps and action queues.

The current Demo covers slope exposure and road/facility resilience in Yokohama, solar siting in Mobara, and cross-module analysis. Every core value can expose its source, formula, model status, and limitations. The interface switches instantly among Chinese, Japanese, and English.

## Quick start

Install [uv](https://docs.astral.sh/uv/) and Node.js >= 22. No database or paid data service is required.

```bash
cd webapp && npm install && npm run build && cd ..   # build the exhibition frontend once
uv run python -m terrai_spatial serve --port 4176
```

Open:

- Exhibition UI: `http://127.0.0.1:4176/`
- FastAPI docs: `http://127.0.0.1:8000/docs`

The first online startup checks and obtains automatable data, then rebuilds missing or stale derivatives. Add `--offline` for strict offline operation.

The MLIT foundation pack is rebuilt from official archives with `uv run python -m terrai_spatial data update --only mlit`. Its large layers are available through the catalog and dataset/feature APIs on demand, not included in the frontend bootstrap. The legacy W05 river layer is excluded because its official terms prohibit commercial use; its evaluation is retained in `docs/summary/` for a future sourcing decision.

## Documentation

- [Product and runtime state](docs/summary/2026-07-prototype-state/README.md)
- [System architecture](docs/architecture/FRONTEND_BACKEND.md)
- [FL → SL → AL concept](docs/architecture/FL_SL_AL_CONCEPT.md)
- [Integrated data and licenses](docs/data/README.md)
- [Refactor plan](docs/refactor/fl-sl-al-platform/00-overview.md)
- [Development and contribution](CONTRIBUTING.md)

This project is a Prototype for customer discussion and technical validation. Rankings begin screening and due diligence; they do not replace engineering, permitting, grid-connection, or investment decisions.
