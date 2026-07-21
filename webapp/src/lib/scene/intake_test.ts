import { describe, expect, it, vi } from "vitest";

import { matchScene, type SceneBundle, type SceneEntry } from "./catalog";
import { SceneIntakeError, assertSingleSceneBundle, loadSceneBundle, loadSceneCatalog } from "./intake";

function bundle(): SceneBundle {
  return {
    scene: {
      scene_id: "nihonbashi-utilities",
      purpose: "Observed underground utility and access-structure scene",
      owner_dataset_key: "uc24_16_nihonbashi",
      handoff_path: "data/plateau/uc24_16_nihonbashi/scene_handoff.json",
      geographic_extent_degrees_and_metres: [139.767, 35.6809, 139.7803, 35.6917, -35, 8],
      origin_geographic_degrees_and_metres: [139.7737, 35.6863, -13.5],
      evidence_availability: { utility_networks: "available" },
    },
    handoff: {
      schema_version: "1.0",
      scene_id: "nihonbashi-utilities",
      purpose: "Observed underground utility and access-structure scene",
      owner_dataset_key: "uc24_16_nihonbashi",
      foundation_layer_only: true,
      approved_roots: ["data/external/plateau_uc24_16", "data/plateau/uc24_16_nihonbashi"],
      local_frame: {} as SceneBundle["handoff"]["local_frame"],
      evidence_families: {
        utility_networks: {
          availability: "available",
          evidence_class: "observed",
          sources: [
            {
              dataset_id: "plateau_uc24_16_nihonbashi",
              resource_ids: ["r1"],
              retrieved_at: "2026-07-21T12:39:12Z",
              source_updated_at: "2025-06-04",
              license: { name: "PLATEAU Site Policy", url: "https://example.test" },
              audit_index_path: "data/plateau/uc24_16_nihonbashi/audit_index.json",
              asset_paths: ["data/external/plateau_uc24_16/assets/water-pipe/tileset.json"],
              feature_count: 810,
            },
          ],
        },
        boreholes: { availability: "unresolved", reason: "No qualified borehole observations are integrated" },
      },
    },
  };
}

describe("assertSingleSceneBundle", () => {
  it("passes a bundle whose assets sit inside its own approved roots", () => {
    expect(assertSingleSceneBundle(bundle()).scene.scene_id).toBe("nihonbashi-utilities");
  });

  it("refuses an asset that escapes the approved roots", () => {
    const tampered = bundle();
    tampered.handoff.evidence_families.utility_networks.sources![0].asset_paths = ["data/elsewhere/tileset.json"];
    expect(() => assertSingleSceneBundle(tampered)).toThrow(SceneIntakeError);
    expect(() => assertSingleSceneBundle(tampered)).toThrow("escapes the scene's approved roots");
  });

  it("refuses a bundle carrying the other canonical scene's roots", () => {
    const tampered = bundle();
    tampered.handoff.approved_roots = [...tampered.handoff.approved_roots, "data/external/plateau_uc24_13"];
    expect(() => assertSingleSceneBundle(tampered)).toThrow("another scene's root");

    const osm = bundle();
    osm.handoff.approved_roots = [...osm.handoff.approved_roots, "data/osm/sapporo_underground_access"];
    expect(() => assertSingleSceneBundle(osm)).toThrow("another scene's root");
  });

  it("refuses unavailable evidence that carries fabricated metadata", () => {
    const counts = bundle();
    (counts.handoff.evidence_families.boreholes as unknown as Record<string, unknown>).sources = [];
    expect(() => assertSingleSceneBundle(counts)).toThrow("fabricated metadata");

    const classed = bundle();
    (classed.handoff.evidence_families.boreholes as unknown as Record<string, unknown>).evidence_class = "observed";
    expect(() => assertSingleSceneBundle(classed)).toThrow("fabricated metadata");
  });
});

describe("the single loading path", () => {
  it("loads and validates a bundle through the shared client shape", async () => {
    const api = { GET: vi.fn(async () => ({ data: bundle() })) };
    const loaded = await loadSceneBundle("nihonbashi-utilities", api);
    expect(loaded.handoff.owner_dataset_key).toBe("uc24_16_nihonbashi");
    expect(api.GET).toHaveBeenCalledWith("/api/v1/scenes/{scene_id}", {
      params: { path: { scene_id: "nihonbashi-utilities" } },
    });
  });

  it("surfaces catalog and bundle failures instead of swallowing them", async () => {
    const failing = { GET: vi.fn(async () => ({ error: { detail: "boom" } })) };
    await expect(loadSceneCatalog(failing)).rejects.toThrow("scene catalog request failed");
    await expect(loadSceneBundle("nihonbashi-utilities", failing)).rejects.toThrow("bundle request failed");
  });
});

describe("box selection isolation", () => {
  it("a box covering both canonical extents resolves exactly one scene", () => {
    const scenes: SceneEntry[] = [
      { ...bundle().scene },
      {
        ...bundle().scene,
        scene_id: "sapporo-station-underground",
        owner_dataset_key: "uc24_13_sapporo",
        geographic_extent_degrees_and_metres: [141.3489, 43.0541, 141.3577, 43.0713, -30, 40],
      },
    ];
    const everywhere: [number, number, number, number] = [130, 30, 150, 50];
    const matched = matchScene(everywhere, scenes);
    expect(matched?.scene_id).toBe("nihonbashi-utilities");
  });
});
