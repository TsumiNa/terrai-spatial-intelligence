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
  vectorBuildingLayerIds,
} from "./config";

export interface ExhibitionMap {
  setRegion(region: RegionKey): void;
  setBasemap(basemap: BasemapKey): void;
  setAnalyticalLayers(layers: Layer[]): void;
  /** Hide the basemap's own buildings while an analysis colors buildings. */
  setVectorBuildingsVisible(visible: boolean): void;
  openPopup(lngLat: [number, number], content: HTMLElement, onClose?: () => void): void;
  closePopup(): void;
  /** Frame a feature the way the queue always has: fit its bounds, capped. */
  frame(bounds: [number, number, number, number]): void;
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
  const buildingLayers = vectorBuildingLayerIds(style);

  let region = initial.region;
  let basemap = initial.basemap;
  let vectorBuildingsVisible = true;

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

  const overlay = new MapboxOverlay({ interleaved: false, layers: [], pickingRadius: 8 });
  map.addControl(overlay);

  const popup = new maplibregl.Popup({ closeButton: true, maxWidth: "300px" });
  let popupCleanup: (() => void) | null = null;
  popup.on("close", () => {
    popupCleanup?.();
    popupCleanup = null;
  });

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
    for (const id of buildingLayers) {
      map.setLayoutProperty(id, "visibility", vectorBuildingsVisible ? "visible" : "none");
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
    setAnalyticalLayers(layers) {
      overlay.setProps({ layers });
    },
    setVectorBuildingsVisible(visible) {
      if (visible === vectorBuildingsVisible) return;
      vectorBuildingsVisible = visible;
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
      popup.remove();
      map.remove();
    },
  };
}
