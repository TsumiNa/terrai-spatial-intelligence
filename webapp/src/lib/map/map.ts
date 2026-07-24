/**
 * The one module that owns the MapLibre instance and its deck.gl overlay.
 *
 * Svelte components call the narrow interface returned by
 * `createExhibitionMap` from effects; nothing else touches map internals and
 * no map object enters reactive state. Basemap switches are visibility
 * toggles on prebuilt layers, region switches are camera jumps and
 * analytical layers arrive as prebuilt deck.gl layer arrays, so the map is
 * never rebuilt after construction.
 */

import { MapboxOverlay } from "@deck.gl/mapbox";
import type { Layer } from "@deck.gl/core";
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// v6 ships an ESM worker. Its filename is chosen by a dev/prod ternary, which
// defeats Vite's static `new URL(...)` worker analysis, so the worker is never
// emitted and its request hangs (main-thread fallback, no vector tiles, and
// `networkidle` never settles). Route it through Vite's worker pipeline with
// `?worker&url` (not plain `?url`, which drops the shared sibling chunk) and
// register it. See MapLibre `setWorkerUrl` docs.
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

maplibregl.setWorkerUrl(workerUrl);

import type { RegionKey } from "../modules";
import type { BasemapKey } from "../state.svelte";
import { Protocol } from "pmtiles";

import { registerGsiDemProtocol } from "./dem";
import { type CoverageIndex, loadCoverage, viewportInCoverage } from "./coverage";
import {
  MAX_PITCH,
  MAX_ZOOM,
  MIN_ZOOM,
  FALLBACK_RASTER_LAYER_ID,
  RELIEF_TINT_LAYER_ID,
  RASTER_KINDS,
  REGION_CAMERAS,
  LOCAL_STYLE_URL,
  LOCAL_SPRITE_URL,
  BUILDING_TILES_LAYER_ID,
  BUILDING_EXTRUSION_LAYER_ID,
  BUILDING_TILES_MIN_ZOOM,
  BUILDING_CLICK_MIN_ZOOM,
  COVERAGE_URL,
  buildingTilesUrl,
  composeStyle,
  rasterId,
  TERRAIN_EXAGGERATION,
  TERRAIN_PITCH,
  TERRAIN_SOURCE_ID,
} from "./config";

/** The PMTiles protocol backs the merged building tiles; register it once. */
let pmtilesRegistered = false;
function registerPmtilesProtocol(lib: typeof maplibregl): void {
  if (pmtilesRegistered) return;
  lib.addProtocol("pmtiles", new Protocol().tile);
  pmtilesRegistered = true;
}

/** Camera pitch of the lowered underground view, within the raised MAX_PITCH. */
export const UNDERGROUND_PITCH = 70;
/** Basemap canvas opacity while the surface is read through. */
export const UNDERGROUND_SURFACE_OPACITY = 0.45;

export interface ExhibitionMap {
  setRegion(region: RegionKey): void;
  setBasemap(basemap: BasemapKey): void;
  /**
   * Toggle the 2.5D view: perspective (camera pitch) on any basemap, plus the
   * 3D DEM surface on imagery and relief. Decoupled from the basemap choice.
   */
  set2point5D(on: boolean): void;
  setAnalyticalLayers(layers: Layer[]): void;
  /**
   * Lower the camera and make the surface translucent so content drawn by the
   * deck overlay reads through it. The camera never goes below ground; the
   * translucency is the MapLibre canvas's, so the overlay stays opaque.
   */
  setUndergroundMode(on: boolean): void;
  /**
   * One-shot box selection: while armed, a drag draws a rectangle instead of
   * panning; on release the geographic bounds go to the handler and the mode
   * disarms. `null` cancels.
   */
  setBoxSelect(onBox: ((bounds: [number, number, number, number]) => void) | null): void;
  openPopup(lngLat: [number, number], content: HTMLElement, onClose?: () => void): void;
  closePopup(): void;
  /** Frame a feature the way the queue always has: fit its bounds, capped. */
  frame(bounds: [number, number, number, number]): void;
  /**
   * Report settled viewports — bounds and zoom, plain data only. Fetch
   * decisions belong to the caller; the map only says where it is looking.
   * Fires once for the initial view and on every `moveend`; returns an
   * unsubscribe function.
   */
  onViewChange(listener: (view: { bounds: [number, number, number, number]; zoom: number }) => void): () => void;
  /**
   * Report whether the merged building tiles are out of service — the viewport,
   * at building zoom, lies wholly outside the coverage footprint, so the map has
   * fallen back to GSI's own building texture. Fires with the current value on
   * subscribe and whenever it changes; returns an unsubscribe function.
   */
  onBuildingsOutOfService(listener: (outOfService: boolean) => void): () => void;
  /**
   * A building in the merged tiles was clicked (only at/above the click zoom, and
   * only when no deck overlay feature was picked — analysis wins contested
   * clicks). Delivers the clicked feature's baked properties + the click point;
   * returns an unsubscribe.
   */
  onBuildingClick(listener: (properties: Record<string, unknown>, lngLat: [number, number]) => void): () => void;
  destroy(): void;
}

export async function createExhibitionMap(
  container: HTMLElement,
  initial: { region: RegionKey; basemap: BasemapKey; twoAndHalfD: boolean },
): Promise<ExhibitionMap> {
  registerGsiDemProtocol(maplibregl);
  registerPmtilesProtocol(maplibregl);
  // The style is a repo-owned snapshot served from our own origin, not the
  // experimental GitHub Pages host — so its dying can no longer stop the map
  // from constructing. A failure here is a deployment error (our own asset
  // missing), not an upstream outage.
  const response = await fetch(LOCAL_STYLE_URL);
  if (!response.ok) throw new Error(`local vector style unavailable: ${LOCAL_STYLE_URL} ${response.status} ${response.statusText}`);
  const search = typeof window !== "undefined" ? window.location.search : "";
  const style = composeStyle(await response.json(), buildingTilesUrl(search));
  // MapLibre v6 requires an absolute sprite URL: the style is passed as an
  // object (no style URL to resolve against), so the repointed root-relative
  // sprite must be resolved to our own origin here or v6 rejects it and no
  // icons load.
  style.sprite = new URL(LOCAL_SPRITE_URL, window.location.origin).href;

  // Ops switch: `?fallback=raster` starts the map on the production-raster
  // fallback (the operational answer if GSI announces a bvmap change). Baked
  // into the style before construction so it is visible from the first frame,
  // with no dependence on load timing.
  const opsFallback = typeof window !== "undefined" && new URLSearchParams(window.location.search).get("fallback") === "raster";
  if (opsFallback) {
    const fallbackLayer = style.layers.find((layer) => layer.id === FALLBACK_RASTER_LAYER_ID);
    if (fallbackLayer) fallbackLayer.layout = { ...fallbackLayer.layout, visibility: "visible" };
  }

  let region = initial.region;
  let basemap = initial.basemap;
  let twoAndHalfD = initial.twoAndHalfD;
  let undergroundMode = false;
  // Merged building-tile coverage: the footprint the fabric is built for, the
  // ids of GSI's own building layers (hidden where our tiles show), and the
  // current out-of-service condition + its listener.
  let coverageIndex: CoverageIndex | null = null;
  let gsiBuildingLayerIds: string[] = [];
  let buildingsOutOfService = false;
  const outOfServiceListeners = new Set<(outOfService: boolean) => void>();
  let buildingClickListener: ((properties: Record<string, unknown>, lngLat: [number, number]) => void) | null = null;

  const map = new maplibregl.Map({
    container,
    style,
    center: REGION_CAMERAS[region].center,
    zoom: REGION_CAMERAS[region].zoom,
    minZoom: MIN_ZOOM,
    maxZoom: MAX_ZOOM,
    maxPitch: MAX_PITCH, // above MapLibre's default 60, for the later lowered-camera stage
    attributionControl: { compact: false },
  });
  // Optional 2× DPR (basemap-view-modes PR3): supersample the render — including
  // the GPU-computed hillshade — for crisper shading, behind ?hidpi=1 given the
  // GPU/fill-rate (and handheld-power) cost. This anti-aliases the shading; it
  // does not fabricate DEM detail.
  if (typeof window !== "undefined" && new URLSearchParams(window.location.search).get("hidpi") === "1") {
    // Supersample to 2×, capped at 2 to bound the fill-rate/power cost (the same
    // ceiling scene.ts uses); crisp on standard displays without over-rendering.
    map.setPixelRatio(Math.min(2, window.devicePixelRatio * 2));
  }
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");

  const overlay = new MapboxOverlay({ interleaved: false, layers: [], pickingRadius: 8 });
  map.addControl(overlay);

  // Building clicks resolve from the baked tile properties (no API call), only at
  // inspection zoom, and only when deck picked nothing at the point — deck's own
  // layer onClick handles an analytical/foundation feature, so analysis wins
  // contested clicks. deck (non-interleaved) consumes the map's own click event,
  // so detect a click from a pointerdown/up pair (the same window pointerup the
  // box-select uses) and read the tile layer with queryRenderedFeatures.
  let clickDown: { x: number; y: number } | null = null;
  const onClickDown = (event: PointerEvent) => {
    clickDown = { x: event.clientX, y: event.clientY };
  };
  const onClickUp = (event: PointerEvent) => {
    const down = clickDown;
    clickDown = null;
    if (!down || boxHandler || !buildingClickListener || map.getZoom() < BUILDING_CLICK_MIN_ZOOM) return;
    if (Math.hypot(event.clientX - down.x, event.clientY - down.y) > 5) return; // a drag, not a click
    const rect = map.getCanvas().getBoundingClientRect();
    const point: [number, number] = [event.clientX - rect.left, event.clientY - rect.top];
    if (overlay.pickObject({ x: point[0], y: point[1], radius: 8 })) return;
    const layers = [BUILDING_TILES_LAYER_ID, BUILDING_EXTRUSION_LAYER_ID].filter((id) => map.getLayer(id));
    if (!layers.length) return;
    // Query a small box, not a bare point, so a click near a footprint still lands
    // it (footprints are only a few pixels across at the click floor).
    const [px, py] = point;
    const region: [[number, number], [number, number]] = [
      [px - 5, py - 5],
      [px + 5, py + 5],
    ];
    const hit = map.queryRenderedFeatures(region, { layers })[0];
    if (hit) {
      const lngLat = map.unproject(point);
      buildingClickListener(hit.properties ?? {}, [lngLat.lng, lngLat.lat]);
    }
  };
  container.addEventListener("pointerdown", onClickDown);
  window.addEventListener("pointerup", onClickUp);

  const popup = new maplibregl.Popup({ closeButton: true, maxWidth: "300px" });
  let popupCleanup: (() => void) | null = null;
  popup.on("close", () => {
    popupCleanup?.();
    popupCleanup = null;
  });

  const observer = new ResizeObserver(() => map.resize());
  observer.observe(container);

  // --- one-shot box selection -------------------------------------------
  let boxHandler: ((bounds: [number, number, number, number]) => void) | null = null;
  let boxStart: { x: number; y: number } | null = null;
  let boxElement: HTMLDivElement | null = null;

  const clearBox = () => {
    boxStart = null;
    boxElement?.remove();
    boxElement = null;
  };
  const disarmBoxSelect = () => {
    boxHandler = null;
    clearBox();
    map.dragPan.enable();
    map.getCanvas().style.cursor = "";
  };
  const canvasPoint = (event: MouseEvent) => {
    const bounds = map.getCanvas().getBoundingClientRect();
    return { x: event.clientX - bounds.left, y: event.clientY - bounds.top };
  };
  const onBoxDown = (event: MouseEvent) => {
    if (!boxHandler) return;
    event.preventDefault();
    boxStart = canvasPoint(event);
    boxElement = document.createElement("div");
    boxElement.className = "map-box-select";
    container.appendChild(boxElement);
  };
  const onBoxMove = (event: MouseEvent) => {
    if (!boxHandler || !boxStart || !boxElement) return;
    const current = canvasPoint(event);
    const left = Math.min(boxStart.x, current.x);
    const top = Math.min(boxStart.y, current.y);
    boxElement.style.left = `${left}px`;
    boxElement.style.top = `${top}px`;
    boxElement.style.width = `${Math.abs(current.x - boxStart.x)}px`;
    boxElement.style.height = `${Math.abs(current.y - boxStart.y)}px`;
  };
  const onBoxUp = (event: MouseEvent) => {
    if (!boxHandler || !boxStart) return;
    const start = boxStart;
    const end = canvasPoint(event);
    const handler = boxHandler;
    const a = map.unproject([start.x, start.y]);
    const b = map.unproject([end.x, end.y]);
    disarmBoxSelect();
    handler([Math.min(a.lng, b.lng), Math.min(a.lat, b.lat), Math.max(a.lng, b.lng), Math.max(a.lat, b.lat)]);
  };
  // Pointer events, not mouse events: MapLibre may preventDefault on
  // pointerdown, which suppresses synthetic mouse events. The move/up pair
  // listens on the window — the standard drag pattern — so pointer capture
  // or leaving the container cannot strand an armed selection.
  container.addEventListener("pointerdown", onBoxDown);
  window.addEventListener("pointermove", onBoxMove);
  window.addEventListener("pointerup", onBoxUp);

  const loaded = new Promise<void>((resolve) => map.once("load", () => resolve()));

  // Toggle only the building layers — cheap, safe to run on every moveend as the
  // coverage condition changes. Kept out of applyVisibility so the moveend path
  // never re-enters the pitch easeTo below (which breaks MapLibre's ease frame).
  const applyBuildingVisibility = () => {
    // moveend can fire before the style finishes loading; setLayoutProperty would
    // throw then, so wait for the style (the post-load applyVisibility re-applies).
    if (!map.isStyleLoaded()) return;
    // The merged building tiles replace GSI's building texture only on the
    // standard basemap, above ground, inside coverage, and **only once the
    // coverage footprint has loaded** — until then (or if it fails to load) GSI's
    // own buildings render everywhere, so a missing coverage.json never empties the
    // map. Out of service (wholly outside coverage) or underground, our tiles hide
    // and GSI's buildings render. Same gray on both sides, so the swap is invisible.
    const showBuildings = basemap === "standard" && !undergroundMode && coverageIndex !== null && !buildingsOutOfService;
    // The flat fill carries the 2D view; the extrusion carries 2.5D. One or the
    // other, so the extrusion's base never z-fights the flat fill.
    if (map.getLayer(BUILDING_TILES_LAYER_ID)) {
      map.setLayoutProperty(BUILDING_TILES_LAYER_ID, "visibility", showBuildings && !twoAndHalfD ? "visible" : "none");
    }
    if (map.getLayer(BUILDING_EXTRUSION_LAYER_ID)) {
      map.setLayoutProperty(BUILDING_EXTRUSION_LAYER_ID, "visibility", showBuildings && twoAndHalfD ? "visible" : "none");
    }
    for (const id of gsiBuildingLayerIds) {
      map.setLayoutProperty(id, "visibility", showBuildings ? "none" : "visible");
    }
  };

  const applyVisibility = () => {
    applyBuildingVisibility();
    for (const kind of RASTER_KINDS) {
      map.setLayoutProperty(rasterId(kind), "visibility", kind === basemap ? "visible" : "none");
    }
    // The colour-by-height tint shows only in hillshade mode (its zoom-fade
    // decides where it is meaningful); underground reads through the surface.
    map.setLayoutProperty(RELIEF_TINT_LAYER_ID, "visibility", basemap === "hillshade" && !undergroundMode ? "visible" : "none");
    const hasTerrain = map.getTerrain() !== null;
    // The underground stage reads through the surface and owns the camera: drop
    // the terrain and let it set its own pitch.
    if (undergroundMode) {
      if (hasTerrain) map.setTerrain(null);
      return;
    }
    // 2.5D is a toggle decoupled from the basemap. Perspective (pitch) applies
    // to any basemap; the 3D DEM surface only to imagery and relief, where real
    // terrain adds meaning — a warped standard cartographic map reads as noise.
    const wantsTerrain = twoAndHalfD && (basemap === "photo" || basemap === "hillshade");
    if (wantsTerrain && !hasTerrain) map.setTerrain({ source: TERRAIN_SOURCE_ID, exaggeration: TERRAIN_EXAGGERATION });
    else if (!wantsTerrain && hasTerrain) map.setTerrain(null);
    const targetPitch = twoAndHalfD ? TERRAIN_PITCH : 0;
    if (Math.abs(map.getPitch() - targetPitch) > 0.5) map.easeTo({ pitch: targetPitch });
  };

  // Recompute the out-of-service condition for the current viewport and re-apply.
  // Out of service only when at building zoom AND the viewport lies wholly outside
  // coverage; with no coverage loaded we degrade to "in coverage" (tiles shown).
  const updateBuildingCoverage = () => {
    const bounds = map.getBounds();
    const view: [number, number, number, number] = [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()];
    const atBuildingZoom = map.getZoom() >= BUILDING_TILES_MIN_ZOOM;
    // Only meaningful once coverage is loaded: with none loaded we show GSI (not
    // our partial tiles), so a failed coverage fetch degrades to GSI, not an empty
    // map, and the "out of service" badge never fires on a coverage we don't know.
    const next = coverageIndex !== null && atBuildingZoom && !viewportInCoverage(view, coverageIndex);
    if (next !== buildingsOutOfService) {
      buildingsOutOfService = next;
      for (const listener of outOfServiceListeners) listener(next);
    }
    // Only re-toggle the building layers here — never the terrain/pitch, which
    // moveend must not re-enter.
    applyBuildingVisibility();
  };

  void loaded.then(() => {
    // Collect GSI's own building layer ids once the style is live, so the toggle
    // above can hand the fabric over to our tiles inside coverage.
    gsiBuildingLayerIds = map
      .getStyle()
      .layers.filter(
        (layer) =>
          "source-layer" in layer &&
          (layer as { "source-layer"?: string })["source-layer"] === "building" &&
          layer.id !== BUILDING_TILES_LAYER_ID,
      )
      .map((layer) => layer.id);
    applyVisibility();
    updateBuildingCoverage();
  });
  map.on("moveend", updateBuildingCoverage);
  void loadCoverage(COVERAGE_URL).then((index) => {
    coverageIndex = index;
    void loaded.then(updateBuildingCoverage);
  });

  // --- production-raster availability fallback (basemap-resilience) --------
  // The experimental vector tiles carry no SLA. When they fail, promote the
  // hidden GSI production-raster layer once (one-way per session) so the wide
  // view degrades to raster streets rather than a blank map. The OSM detail
  // layer, foundation overlays and analyses are unaffected — they are our data.
  // Identify the source by the experimental tiles this fallback specifically
  // guards — not merely "the first vector source" — so an added vector source
  // cannot misdirect the error counting.
  const vectorSourceId = Object.entries(style.sources).find(
    ([, source]) => source.type === "vector" && (source.tiles ?? []).some((tile) => tile.includes("experimental_bvmap")),
  )?.[0];
  // Already active if the ops switch baked it into the style above.
  let fallbackActive = opsFallback;
  const activateFallback = (reason: string): void => {
    if (fallbackActive) return;
    fallbackActive = true;
    // Gate on the *style* being loaded, not the map "load" event: when the
    // vector tiles are dead, "load" (first complete render) may never fire, but
    // the style — and this layer — are present, so showing it must not wait on
    // tiles that will never arrive. Re-check on each styledata until the style
    // is ready (tile errors can fire before the style finishes loading).
    const show = (): void => {
      if (!map.isStyleLoaded()) {
        map.once("styledata", show);
        return;
      }
      if (map.getLayer(FALLBACK_RASTER_LAYER_ID)) map.setLayoutProperty(FALLBACK_RASTER_LAYER_ID, "visibility", "visible");
    };
    show();
    console.warn(`[basemap] vector tiles unavailable — GSI production-raster fallback active (${reason}).`);
  };
  // Auto-promotion: a measured threshold within a window, so a stray tile 404
  // never flaps the basemap, but a dead source promotes and stays. The window is
  // generous: a genuinely dead source fails every requested tile (dozens), so it
  // crosses the threshold easily even when rendering is slow, while four real
  // failures within it in a healthy session stays very unlikely.
  const FALLBACK_WINDOW_MS = 20000;
  const FALLBACK_THRESHOLD = 4;
  const vectorErrorTimes: number[] = [];
  map.on("error", (event) => {
    if (fallbackActive) return; // one-way: stop counting once promoted
    const detail = event as { sourceId?: string; error?: { message?: string } };
    const fromVector = detail.sourceId === vectorSourceId || (detail.error?.message ?? "").includes("experimental_bvmap");
    if (!fromVector) return;
    const now = performance.now();
    vectorErrorTimes.push(now);
    // Keep only the most recent timestamps within the window, bounded by the
    // threshold, so a rapidly-failing source cannot grow this without limit.
    while (vectorErrorTimes.length > FALLBACK_THRESHOLD || (vectorErrorTimes.length > 0 && now - vectorErrorTimes[0] > FALLBACK_WINDOW_MS)) {
      vectorErrorTimes.shift();
    }
    if (vectorErrorTimes.length >= FALLBACK_THRESHOLD) activateFallback("repeated tile failures");
  });

  return {
    setRegion(next) {
      if (next === region) return;
      region = next;
      map.jumpTo({ center: REGION_CAMERAS[next].center, zoom: REGION_CAMERAS[next].zoom });
      void loaded.then(applyVisibility);
    },
    setBasemap(next) {
      if (next === basemap) return;
      basemap = next;
      void loaded.then(applyVisibility);
    },
    set2point5D(next) {
      if (next === twoAndHalfD) return;
      twoAndHalfD = next;
      void loaded.then(applyVisibility);
    },
    setAnalyticalLayers(layers) {
      overlay.setProps({ layers });
    },
    setBoxSelect(onBox) {
      if (!onBox) {
        disarmBoxSelect();
        return;
      }
      boxHandler = onBox;
      map.dragPan.disable();
      map.getCanvas().style.cursor = "crosshair";
    },
    setUndergroundMode(on) {
      if (on === undergroundMode) return;
      undergroundMode = on;
      map.getCanvas().style.opacity = on ? String(UNDERGROUND_SURFACE_OPACITY) : "";
      map.easeTo({ pitch: on ? UNDERGROUND_PITCH : 0 });
      void loaded.then(applyVisibility);
    },
    openPopup(lngLat, content, onClose) {
      popup.remove(); // fires close → previous cleanup
      popupCleanup = onClose ?? null;
      popup.setLngLat(lngLat).setDOMContent(content).addTo(map);
    },
    closePopup() {
      popup.remove();
    },
    onViewChange(listener) {
      let active = true;
      const report = () => {
        if (!active) return; // the initial loaded-report can outlive unsubscribe
        const bounds = map.getBounds();
        listener({
          bounds: [bounds.getWest(), bounds.getSouth(), bounds.getEast(), bounds.getNorth()],
          zoom: map.getZoom(),
        });
      };
      map.on("moveend", report);
      void loaded.then(report);
      return () => {
        active = false;
        map.off("moveend", report);
      };
    },
    onBuildingsOutOfService(listener) {
      outOfServiceListeners.add(listener);
      listener(buildingsOutOfService);
      return () => {
        outOfServiceListeners.delete(listener);
      };
    },
    onBuildingClick(listener) {
      buildingClickListener = listener;
      return () => {
        if (buildingClickListener === listener) buildingClickListener = null;
      };
    },
    frame([west, south, east, north]) {
      if (west === east && south === north) {
        map.easeTo({ center: [west, south], zoom: MAX_ZOOM });
      } else {
        map.fitBounds(
          [
            [west, south],
            [east, north],
          ],
          { padding: 80, maxZoom: MAX_ZOOM },
        );
      }
    },
    destroy() {
      observer.disconnect();
      container.removeEventListener("pointerdown", onBoxDown);
      window.removeEventListener("pointermove", onBoxMove);
      window.removeEventListener("pointerup", onBoxUp);
      popup.remove();
      map.remove();
    },
  };
}
