# TerrAI Spatial Intelligence

TerrAI is a spatial-decision Demo for clean energy and climate resilience. It combines public foundation data, traceable augmented evidence, and scenario analysis to answer “where should we investigate first, why, and can the evidence be trusted?” through maps and action queues.

The current Demo covers slope exposure and road/facility resilience in Yokohama, solar siting in Mobara, and cross-module analysis. Every core value can expose its source, formula, model status, and limitations. The interface switches instantly among Chinese, Japanese, and English.

## Quick start

Install [uv](https://docs.astral.sh/uv/). No database or paid data service is required.

```bash
uv run python -m terrai_spatial serve --port 4176
```

Open:

- Exhibition UI: `http://127.0.0.1:4176/`
- FastAPI docs: `http://127.0.0.1:8000/docs`

The first online startup checks and obtains automatable data, then rebuilds missing or stale derivatives. Add `--offline` for strict offline operation.

## Documentation

- [Product and runtime state](docs/summary/2026-07-prototype-state/README.md)
- [System architecture](docs/architecture/FRONTEND_BACKEND.md)
- [FL → SL → AL concept](docs/architecture/FL_SL_AL_CONCEPT.md)
- [Integrated data and licenses](docs/data/catalog/README.md)
- [Refactor plan](docs/refactor/fl-sl-al-platform/00-overview.md)
- [Development and contribution](CONTRIBUTING.md)

This project is a Prototype for customer discussion and technical validation. Rankings begin screening and due diligence; they do not replace engineering, permitting, grid-connection, or investment decisions.
