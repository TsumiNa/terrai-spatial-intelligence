/**
 * deck.gl layers for the underground module: one Tile3DLayer per UC24-16
 * resource, coloured by utility class from the style rules.
 *
 * The published tilesets are 3D Tiles 1.1 with *plural* `contents` arrays,
 * which loaders.gl 4.x does not traverse — a tile whose content lives in
 * `contents` renders nothing. `normalizeTileset` rewrites that shape into the
 * equivalent single-`content` children before the tileset reaches the loader,
 * changing structure only: URIs, bounding volumes and geometric errors all
 * come from the source document.
 */

import { Tile3DLayer } from "@deck.gl/geo-layers";
import type { Layer } from "@deck.gl/core";

import { UNDERGROUND_STYLE, type UndergroundResource } from "../underground";
import { rgba } from "./style-rules";

interface TilesetNode {
  boundingVolume?: unknown;
  geometricError?: number;
  refine?: string;
  content?: { uri?: string; url?: string; boundingVolume?: unknown };
  contents?: { uri?: string; url?: string; boundingVolume?: unknown }[];
  children?: TilesetNode[];
  [key: string]: unknown;
}

export interface TilesetDocument {
  asset?: { version?: string };
  root: TilesetNode;
  [key: string]: unknown;
}

/** Rewrite 3D Tiles 1.1 `contents` arrays into single-`content` children. */
export function normalizeTileset(tileset: TilesetDocument): TilesetDocument {
  const normalizeNode = (node: TilesetNode): TilesetNode => {
    const { contents, children, ...rest } = node;
    const normalizedChildren = (children ?? []).map(normalizeNode);
    if (!contents || contents.length === 0) {
      return { ...rest, ...(children ? { children: normalizedChildren } : {}) };
    }
    const contentChildren = contents.map((content) => ({
      boundingVolume: content.boundingVolume ?? node.boundingVolume,
      geometricError: 0,
      content: { uri: content.uri ?? content.url },
    }));
    return {
      ...rest,
      children: [...normalizedChildren, ...contentChildren],
    };
  };
  return { ...tileset, root: normalizeNode(tileset.root) };
}

/**
 * Wrap a JSON glTF in a GLB container (one JSON chunk, buffers stay data
 * URIs). The published tiles are `.gltf` text, but loaders.gl's tile-content
 * parser dispatches on binary magic and has no JSON branch — the `glTF`
 * header routes the identical payload through its glTF path.
 */
export function gltfJsonToGlb(text: string): ArrayBuffer {
  const json = new TextEncoder().encode(text);
  const padded = (json.length + 3) & ~3;
  const buffer = new ArrayBuffer(12 + 8 + padded);
  const view = new DataView(buffer);
  view.setUint32(0, 0x46546c67, true); // "glTF"
  view.setUint32(4, 2, true);
  view.setUint32(8, buffer.byteLength, true);
  view.setUint32(12, padded, true);
  view.setUint32(16, 0x4e4f534a, true); // "JSON"
  const bytes = new Uint8Array(buffer, 20);
  bytes.set(json);
  bytes.fill(0x20, json.length); // pad with spaces, per the GLB spec
  return buffer;
}

/** A Response whose `url` survives synthesis: loaders.gl detects tileset JSON
 * and resolves child URIs from `response.url`, which `new Response` drops. */
function synthesizedResponse(body: BodyInit, url: string, contentType: string): Response {
  const response = new Response(body, { status: 200, headers: { "content-type": contentType } });
  Object.defineProperty(response, "url", { value: url });
  return response;
}

/** A fetch that serves the normalized tileset document for the tileset URL,
 * wraps `.gltf` JSON content as GLB, and passes everything else through. */
export function tilesetNormalizingFetch(tilesetUrl: string): (url: string, options?: unknown) => Promise<Response> {
  return async (url, options) => {
    const response = await fetch(url, options as RequestInit | undefined);
    if (!response.ok) return response;
    if (url.endsWith(".gltf")) {
      return synthesizedResponse(gltfJsonToGlb(await response.text()), url, "model/gltf-binary");
    }
    if (url !== tilesetUrl) return response;
    const normalized = normalizeTileset((await response.json()) as TilesetDocument);
    return synthesizedResponse(JSON.stringify(normalized), url, "application/json");
  };
}

/**
 * Tile3DLayer culls picking draws by distance from the tile's content origin
 * — a sound optimisation for dense photogrammetry, wrong for these tiles,
 * whose sparse network geometry spans ~500 m chunks: zoomed to a street, the
 * chunk origin projects far off screen and the pipe under the cursor is
 * skipped. Keep the selected/viewport gate, drop the origin-distance cull.
 */
class UndergroundTile3DLayer extends Tile3DLayer {
  static layerName = "UndergroundTile3DLayer";

  filterSubLayer(context: Parameters<Tile3DLayer["filterSubLayer"]>[0]): boolean {
    const tile = (context.layer.props as { tile?: { selected?: boolean; viewportIds?: string[] } }).tile;
    if (!tile) return false;
    return Boolean(tile.selected && tile.viewportIds?.includes(context.viewport.id));
  }
}

export interface UndergroundPickHandlers {
  /** A picked tile resolves to its resource and content URI (`data/….gltf`). */
  onAsset(resource: UndergroundResource, contentUri: string, coordinate: [number, number]): void;
}

/** The `data/….gltf` suffix a picked tile shares with the audit index. */
export function contentUriFromTileUrl(tileUrl: string, tilesetUrl: string): string {
  const base = tilesetUrl.slice(0, tilesetUrl.lastIndexOf("/") + 1);
  return tileUrl.startsWith(base) ? tileUrl.slice(base.length) : tileUrl;
}

export function buildUndergroundLayers(
  resources: UndergroundResource[],
  assetBase: string,
  handlers: UndergroundPickHandlers,
): Layer[] {
  const apiOrigin = assetBase.replace(/\/api\/v1\/assets$/, "");
  return resources.map((resource) => {
    const tilesetUrl = `${apiOrigin}${resource.tileset_url}`;
    const color = rgba(UNDERGROUND_STYLE.classColors[resource.utility_class] ?? UNDERGROUND_STYLE.classColors.sewer_manhole);
    return new UndergroundTile3DLayer({
      id: `underground-${resource.slug}`,
      data: tilesetUrl,
      loadOptions: {
        fetch: tilesetNormalizingFetch(tilesetUrl),
        // A near-zero screen-space-error target forces traversal all the way
        // to the leaf contents. This is renderer LOD tuning, not a data edit:
        // the sample tilesets are small enough to load whole, and stopping at
        // an intermediate node would render nothing at all.
        tileset: { maximumScreenSpaceError: 0.01 },
      },
      opacity: UNDERGROUND_STYLE.opacity,
      pickable: true,
      autoHighlight: true,
      onClick: (info: { object?: { contentUrl?: string; content?: { url?: string } }; coordinate?: number[] }) => {
        const tileUrl = info.object?.contentUrl ?? info.object?.content?.url;
        if (!tileUrl || !info.coordinate) return false;
        handlers.onAsset(resource, contentUriFromTileUrl(tileUrl, tilesetUrl), [info.coordinate[0], info.coordinate[1]]);
        return true;
      },
      _subLayerProps: {
        scenegraph: {
          getColor: color,
          // The x-ray reading: the network draws through the translucent
          // surface instead of being occluded by anything the overlay draws.
          parameters: { depthCompare: "always" },
        },
      },
    } as never);
  });
}
