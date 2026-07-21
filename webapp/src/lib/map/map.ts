/**
 * The one module that owns the MapLibre instance.
 *
 * Svelte components call the narrow interface returned by
 * `createExhibitionMap` from effects; nothing else touches map internals and
 * no map object enters reactive state. Basemap switches are visibility
 * toggles on prebuilt layers and region switches are camera jumps, so the
 * map is never rebuilt after construction.
 */

import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

import type { RegionKey } from "../modules";
import type { BasemapKey } from "../state.svelte";
import {
  MAX_PITCH,
  MAX_ZOOM,
  MIN_ZOOM,
  RASTER_KINDS,
  REGION_CAMERAS,
  REGION_KEYS,
  VECTOR_STYLE_URL,
  composeStyle,
  rasterId,
} from "./config";

export interface ExhibitionMap {
  setRegion(region: RegionKey): void;
  setBasemap(basemap: BasemapKey): void;
  destroy(): void;
}

export async function createExhibitionMap(
  container: HTMLElement,
  assetBase: string,
  initial: { region: RegionKey; basemap: BasemapKey },
): Promise<ExhibitionMap> {
  const response = await fetch(VECTOR_STYLE_URL);
  if (!response.ok) throw new Error(`vector style request failed: ${response.status}`);
  const style = composeStyle(await response.json(), assetBase);

  let region = initial.region;
  let basemap = initial.basemap;

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
  map.addControl(new maplibregl.NavigationControl({ visualizePitch: true }), "bottom-right");

  const observer = new ResizeObserver(() => map.resize());
  observer.observe(container);

  const loaded = new Promise<void>((resolve) => map.once("load", () => resolve()));

  const applyVisibility = () => {
    for (const r of REGION_KEYS) {
      for (const kind of RASTER_KINDS) {
        const visible = r === region && kind === basemap;
        map.setLayoutProperty(rasterId(r, kind), "visibility", visible ? "visible" : "none");
      }
    }
  };
  void loaded.then(applyVisibility);

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
    destroy() {
      observer.disconnect();
      map.remove();
    },
  };
}
