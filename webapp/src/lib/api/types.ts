/**
 * Shape of the `/api/v1/bootstrap` payload.
 *
 * The FastAPI endpoint returns an untyped `dict`, so the generated OpenAPI
 * schema cannot carry these fields; this interface mirrors
 * `terrai_spatial/data_service.py` (`DATASETS` + `bootstrap()`) by hand.
 * Property access in the app goes through this contract instead of magic
 * strings.
 */

export interface FeatureProperties {
  [name: string]: unknown;
}

export interface Feature {
  type: "Feature";
  id?: string | number;
  properties: FeatureProperties;
  geometry: unknown;
}

export interface FeatureCollection {
  type: "FeatureCollection";
  features: Feature[];
}

export interface BuildingSummary {
  building_count: number;
  counts: { high: number; medium: number; low: number };
  mean_score: number;
}

export interface RoadSummary {
  road_count: number;
  total_km: number;
  high_queue: number;
  exposed_buildings: number;
  mean_score: number;
}

export interface SolarSummary {
  cell_count: number;
  counts: { preferred: number; conditional: number; reject: number };
  shortlist_area_ha: number;
  annual_ghi_kwh_m2: number;
}

export interface JointSummary {
  resilience_hubs: { count: number; priority_count: number; pv_capacity_proxy_kwp: number };
  compound_corridors: { count: number; road_length_km: number };
  solar_delivery_cells: { count: number; area_ha: number };
}

export interface GridScreen {
  mobara_screen: { spare_own_mw: number; spare_with_upstream_mw: number };
  source_file_last_modified_at: string | null;
}

export interface EmbeddingRegionSummary {
  pixel_count: number;
  valid_pct: number;
  mean_cosine_change: number;
  p95_cosine_change: number;
}

export interface EmbeddingOverlay {
  change_image: string;
  latent_image: string;
  bounds: [[number, number], [number, number]];
}

export interface EmbeddingSummary {
  regions: { yokohama: EmbeddingRegionSummary; mobara: EmbeddingRegionSummary };
  overlays: { yokohama: EmbeddingOverlay; mobara: EmbeddingOverlay };
}

export interface FacilitySummary {
  count: number;
  pv_kwp_proxy: number;
  served_high_risk_buildings: number;
  mean_resilience_score: number;
}

export interface BootstrapMeta {
  status: string;
  datasets_ready: number;
  datasets_total: number;
  source_groups: number;
  traceability: string;
  checked_at: string;
  source_catalog: unknown[];
  data_model: string;
  api_version: string;
}

export interface Recommendations {
  slope: FeatureCollection;
  roads: FeatureCollection;
  solar: FeatureCollection;
  facilities: FeatureCollection;
  hubs: FeatureCollection;
  corridors: FeatureCollection;
  delivery: FeatureCollection;
  constraints: FeatureCollection;
  embedding: FeatureCollection;
  embeddingYokohama: FeatureCollection;
  embeddingMobara: FeatureCollection;
}

export interface Bootstrap {
  buildings: FeatureCollection;
  buildingSummary: BuildingSummary;
  roads: FeatureCollection;
  roadSummary: RoadSummary;
  solar: FeatureCollection;
  solarContext: FeatureCollection;
  solarSummary: SolarSummary;
  hubs: FeatureCollection;
  corridors: FeatureCollection;
  delivery: FeatureCollection;
  jointSummary: JointSummary;
  gridScreen: GridScreen;
  gsiEvacuation: FeatureCollection;
  facilities: FeatureCollection;
  embeddingEvidence: FeatureCollection;
  embeddingSummary: EmbeddingSummary;
  yokohamaZones: FeatureCollection;
  mobaraZones: FeatureCollection;
  multiscaleSummary: Record<string, unknown>;
  facilitySummary: FacilitySummary;
  recommendations: Recommendations;
  meta: BootstrapMeta;
}
