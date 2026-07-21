"""FastAPI application for the TerrAI exhibition demo."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from .data_service import DatasetNotFoundError, ROOT, service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Refuse to serve from a missing or drifted store: a broken pipeline must
    # surface as a startup failure naming the fix, never as stale responses.
    service.require_store()
    yield


app = FastAPI(
    title="TerrAI Spatial Intelligence API",
    version="1.0.0",
    description="Read-only APIs for the TerrAI commercial exhibition prototype, served from the spatial store derived from the committed datasets.",
    lifespan=lifespan,
)

RASTER_SUFFIXES = (".png", ".jpg")


class SkipRasterCompression:
    """Strip Accept-Encoding for raster tiles so the gzip layer passes them
    through untouched: PNG and JPEG are already compressed, and wrapping them
    again spends cycles for negative gain. Everything else on the asset mount
    (GeoJSON, glTF, audit indexes) compresses like the JSON routes."""

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http" and scope["path"].lower().endswith(RASTER_SUFFIXES):
            scope = {**scope, "headers": [item for item in scope["headers"] if item[0] != b"accept-encoding"]}
        await self.app(scope, receive, send)


# Compression wraps the whole application, the static asset mount included.
# Middleware added later runs earlier, so the raster exclusion above sees the
# request before gzip negotiates.
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(SkipRasterCompression)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_origin_regex=r"^https?://(127\.0\.0\.1|localhost)(:\d+)?$",
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/v1/health", tags=["reliability"])
def health() -> dict:
    """Return API and packaged-dataset readiness."""

    return service.health()


@app.get("/api/v1/catalog", tags=["reliability"])
def catalog() -> dict:
    """Return the auditable file-backed dataset catalog."""

    return {"datasets": service.catalog()}


@app.get("/api/v1/bootstrap", tags=["exhibition"])
def bootstrap() -> dict:
    """Return the complete local exhibition payload through one stable contract."""

    return service.bootstrap()


@app.get("/api/v1/datasets/{key}", tags=["data"])
def dataset(key: str) -> dict:
    """Return one JSON or GeoJSON dataset by stable public key."""

    try:
        value = service.load(key)
    except (DatasetNotFoundError, FileNotFoundError) as error:
        raise HTTPException(status_code=404, detail=f"unknown or unavailable dataset: {key}") from error
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail=f"dataset {key} is not an object")
    return value


@app.get("/api/v1/features/{key}", tags=["query"])
def features(
    key: str,
    where: str | None = None,
    equals: str | None = None,
    minimum: float | None = None,
    maximum: float | None = None,
    sort: str | None = None,
    descending: bool = True,
    limit: Annotated[int, Query(ge=1, le=5000)] = 5000,
    bbox: Annotated[list[float] | None, Query(min_length=4, max_length=4)] = None,
) -> dict:
    """Filter, sort and spatially window a GeoJSON FeatureCollection."""

    try:
        return service.query_features(
            key,
            where=where,
            equals=equals,
            minimum=minimum,
            maximum=maximum,
            sort=sort,
            descending=descending,
            limit=limit,
            bbox=tuple(bbox) if bbox else None,
        )
    except (DatasetNotFoundError, FileNotFoundError) as error:
        raise HTTPException(status_code=404, detail=f"unknown or unavailable dataset: {key}") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/api/v1/recommendations/{analysis}", tags=["analysis"])
def recommendations(analysis: str) -> dict:
    """Return a server-ranked action queue for one exhibition analysis."""

    try:
        return service.recommendation(analysis)
    except DatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"unknown analysis: {analysis}") from error


@app.get("/api/v1/scenes", tags=["scenes"])
def scenes() -> dict:
    """Return the renderer-neutral underground scene catalog."""

    return service.scene_catalog()


@app.get("/api/v1/scenes/{scene_id}", tags=["scenes"])
def scene_bundle(scene_id: str) -> dict:
    """Return one catalogued scene with its local-frame handoff."""

    try:
        return service.scene_bundle(scene_id)
    except DatasetNotFoundError as error:
        raise HTTPException(status_code=404, detail=f"unknown scene: {scene_id}") from error


app.mount("/api/v1/assets", StaticFiles(directory=ROOT / "data"), name="data-assets")
