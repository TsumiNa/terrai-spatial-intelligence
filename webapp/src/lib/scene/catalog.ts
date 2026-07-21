/**
 * The underground scene catalog and box-selection matching.
 *
 * A drawn box matches at most one catalogued scene — the first whose
 * geographic extent it intersects. Scenes are geographically disjoint by
 * construction (that is the data refactor's isolation rule), so a selection
 * can never combine Nihonbashi with Sapporo.
 */

import type { LocalFrame } from "./frame";

export type EvidenceAvailability = "available" | "unresolved" | "not_applicable";

export interface EvidenceSource {
  dataset_id: string;
  resource_ids: string[];
  retrieved_at: string;
  source_updated_at: string | null;
  license: { name: string; url: string };
  audit_index_path: string;
  asset_paths: string[];
  feature_count: number;
}

export interface EvidenceFamily {
  availability: EvidenceAvailability;
  reason?: string;
  evidence_class?: string;
  sources?: EvidenceSource[];
}

export interface SceneHandoff {
  schema_version: string;
  scene_id: string;
  purpose: string;
  owner_dataset_key: string;
  foundation_layer_only: boolean;
  approved_roots: string[];
  local_frame: LocalFrame;
  evidence_families: Record<string, EvidenceFamily>;
}

export interface SceneEntry {
  scene_id: string;
  purpose: string;
  owner_dataset_key: string;
  handoff_path: string;
  /** [west, south, east, north] degrees + [minH, maxH] metres. */
  geographic_extent_degrees_and_metres: number[];
  origin_geographic_degrees_and_metres: number[];
  evidence_availability: Record<string, EvidenceAvailability>;
}

export interface SceneCatalog {
  schema_version: string;
  coordinate_contract: string;
  scenes: SceneEntry[];
}

export interface SceneBundle {
  scene: SceneEntry;
  handoff: SceneHandoff;
}

/** The seven evidence families, in the handoff's published order. */
export const EVIDENCE_FAMILIES = [
  "terrain_buildings_context",
  "utility_networks",
  "underground_structures",
  "access_topology",
  "boreholes",
  "strata",
  "predicted_fields",
] as const;

export function sceneExtent(entry: SceneEntry): [number, number, number, number] {
  const [west, south, east, north] = entry.geographic_extent_degrees_and_metres;
  return [west, south, east, north];
}

/** The first catalogued scene a drawn box intersects, or null. */
export function matchScene(
  box: [number, number, number, number],
  scenes: SceneEntry[],
): SceneEntry | null {
  const [boxWest, boxSouth, boxEast, boxNorth] = box;
  for (const entry of scenes) {
    const [west, south, east, north] = sceneExtent(entry);
    const intersects = boxWest <= east && boxEast >= west && boxSouth <= north && boxNorth >= south;
    if (intersects) return entry;
  }
  return null;
}
