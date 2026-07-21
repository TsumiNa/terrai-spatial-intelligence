import { expect, it, vi } from "vitest";

import { buildUndergroundLayers, contentUriFromTileUrl, gltfJsonToGlb, normalizeTileset, type TilesetDocument } from "./underground-layers";
import type { UndergroundResource } from "../underground";

const multiContents: TilesetDocument = {
  asset: { version: "1.1" },
  root: {
    boundingVolume: { region: [1, 2, 3, 4, 0, 10] },
    geometricError: 100,
    refine: "ADD",
    children: [
      {
        boundingVolume: { region: [1, 2, 3, 4, 0, 10] },
        geometricError: 10,
        contents: [
          { boundingVolume: { region: [1, 2, 2, 3, 0, 5] }, uri: "data/a.gltf" },
          { uri: "data/b.gltf" },
        ],
      },
    ],
  },
};

it("rewrites 1.1 plural contents into single-content children", () => {
  const normalized = normalizeTileset(multiContents);
  const child = normalized.root.children![0];
  expect(child.contents).toBeUndefined();
  expect(child.children).toHaveLength(2);
  expect(child.children![0].content).toEqual({ uri: "data/a.gltf" });
  // A content without its own bounding volume inherits the node's.
  expect(child.children![1].boundingVolume).toEqual({ region: [1, 2, 3, 4, 0, 10] });
  expect(child.children![0].boundingVolume).toEqual({ region: [1, 2, 2, 3, 0, 5] });
});

it("leaves single-content tilesets structurally unchanged", () => {
  const single: TilesetDocument = {
    root: { geometricError: 1, content: { uri: "data/x.gltf" }, children: [] },
  };
  expect(normalizeTileset(single).root.content).toEqual({ uri: "data/x.gltf" });
});

it("does not mutate the source document", () => {
  const before = JSON.stringify(multiContents);
  normalizeTileset(multiContents);
  expect(JSON.stringify(multiContents)).toBe(before);
});

it("recovers the audit-index asset path from a picked tile URL", () => {
  const tileset = "http://127.0.0.1:8000/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/tileset.json";
  expect(
    contentUriFromTileUrl("http://127.0.0.1:8000/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/data/WaterPipe_coordinates_-14_-115.gltf", tileset),
  ).toBe("data/WaterPipe_coordinates_-14_-115.gltf");
});

it("builds one pickable tile layer per resource", () => {
  const resources = [
    { resource_id: "a", slug: "water-pipe", utility_class: "water_pipe", tileset_url: "/api/v1/assets/external/plateau_uc24_16/assets/water-pipe/tileset.json" },
    { resource_id: "b", slug: "sewer-manhole", utility_class: "sewer_manhole", tileset_url: "/api/v1/assets/external/plateau_uc24_16/assets/sewer-manhole/tileset.json" },
  ] as unknown as UndergroundResource[];
  const layers = buildUndergroundLayers(resources, "http://x/api/v1/assets", { onAsset: vi.fn() });
  expect(layers.map((layer) => layer.id)).toEqual(["underground-water-pipe", "underground-sewer-manhole"]);
  for (const layer of layers) {
    expect((layer as unknown as { props: { pickable: boolean; data: string } }).props.pickable).toBe(true);
    expect((layer as unknown as { props: { data: string } }).props.data).toContain("http://x/api/v1/assets/external/");
  }
});

it("wraps JSON glTF into a spec-conformant GLB container", () => {
  const source = JSON.stringify({ asset: { version: "2.0" }, meshes: [] });
  const glb = gltfJsonToGlb(source);
  const view = new DataView(glb);
  expect(view.getUint32(0, true)).toBe(0x46546c67); // "glTF"
  expect(view.getUint32(4, true)).toBe(2);
  expect(view.getUint32(8, true)).toBe(glb.byteLength);
  expect(glb.byteLength % 4).toBe(0);
  const chunkLength = view.getUint32(12, true);
  expect(view.getUint32(16, true)).toBe(0x4e4f534a); // "JSON"
  const text = new TextDecoder().decode(new Uint8Array(glb, 20, chunkLength));
  expect(JSON.parse(text)).toEqual(JSON.parse(source)); // space padding is valid JSON whitespace
});
