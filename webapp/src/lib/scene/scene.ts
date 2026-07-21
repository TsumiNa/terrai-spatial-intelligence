/**
 * The standalone Three.js site scene — its own canvas, its own WebGL
 * context, nothing shared with MapLibre.
 *
 * The scene renders exactly what the selected handoff makes available:
 * PLATEAU tilesets stream through TilesRenderer into the handoff's ENU local
 * frame (`world_to_local` applied to the ECEF-rooted tile groups — never a
 * hard-coded transform), and the Sapporo OSM access snapshot draws as an
 * independent overlay that supplements but never snaps to PLATEAU geometry.
 * Unresolved and not-applicable families produce no geometry at all.
 *
 * Section cuts are material clipping planes and vertical exaggeration is a
 * scale on the local-frame wrapper: renderer configuration, not coordinate
 * facts. Picking resolves through the handoff's inverse transform back to
 * real coordinates.
 */

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { DRACOLoader } from "three/addons/loaders/DRACOLoader.js";
import { TilesRenderer } from "3d-tiles-renderer";
import { GLTFExtensionsPlugin } from "3d-tiles-renderer/plugins";

import { palette } from "../theme";
import { UNDERGROUND_STYLE, type UndergroundFamily } from "../underground";
import { normalizeTileset, type TilesetDocument } from "../map/underground-layers";
import { geographicToLocal, localToGeographic } from "./frame";
import type { SceneBundle, EvidenceSource } from "./catalog";

export type SectionAxis = "x" | "y" | "z";

export interface PickedElement {
  familyKey: string;
  datasetId: string;
  /** The tile content URI relative to its tileset, e.g. `data/….gltf`. */
  tileUri: string | null;
  /** b3dm batch-table values for the picked feature, where the format has them. */
  batch: Record<string, unknown> | null;
  localPoint: [number, number, number];
  /** Resolved through the handoff's inverse transform. */
  geographic: [number, number, number];
  source: EvidenceSource;
}

export interface SceneHandlers {
  onPick(picked: PickedElement | null): void;
  onFamilyStatus(familyKey: string, status: "loading" | "ready" | "error", detail?: string): void;
}

export interface SiteScene {
  setExaggeration(factor: number): void;
  setSection(axis: SectionAxis | null, position: number): void;
  resize(): void;
  destroy(): void;
}

/** Nihonbashi utility classes keep their map colours; everything else keeps
 * the material its source publishes. */
function utilityColorForAsset(assetPath: string): string | null {
  const slug = assetPath.match(/assets\/([a-z-]+)\/tileset\.json$/)?.[1];
  if (!slug) return null;
  return UNDERGROUND_STYLE.classColors[slug.replaceAll("-", "_")] ?? null;
}

export function createSiteScene(
  canvas: HTMLCanvasElement,
  bundle: SceneBundle,
  apiOrigin: string,
  handlers: SceneHandlers,
): SiteScene {
  const frame = bundle.handoff.local_frame;
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.localClippingEnabled = true;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(palette.ink);
  scene.add(new THREE.AmbientLight(palette.white, 1.4));
  const sun = new THREE.DirectionalLight(palette.white, 2.2);
  sun.position.set(400, -300, 600);
  scene.add(sun);

  const extent = frame.geographic_extent_degrees_and_metres;
  const spanMetres = Math.max(
    Math.abs(geographicToLocal(frame, [extent[2], extent[3], extent[5]])[0] -
      geographicToLocal(frame, [extent[0], extent[1], extent[4]])[0]),
    200,
  );

  const camera = new THREE.PerspectiveCamera(55, 1, 0.1, spanMetres * 20);
  camera.up.set(0, 0, 1); // ENU: z is up
  camera.position.set(spanMetres * 0.4, -spanMetres * 0.5, spanMetres * 0.35);
  const controls = new OrbitControls(camera, canvas);
  controls.target.set(0, 0, 0);

  /** Everything in the local frame hangs off this wrapper; vertical
   * exaggeration is its z-scale. */
  const localFrameGroup = new THREE.Group();
  scene.add(localFrameGroup);

  const worldToLocal = new THREE.Matrix4();
  const m = frame.world_to_local_matrix_row_major;
  // Matrix4.set takes row-major arguments, matching the handoff layout.
  worldToLocal.set(m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12], m[13], m[14], m[15]);

  const sectionPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), spanMetres);
  let sectionEnabled = false;
  const clippableMaterials = new Set<THREE.Material>();

  const applyClipping = (material: THREE.Material) => {
    material.clippingPlanes = sectionEnabled ? [sectionPlane] : [];
    material.clipShadows = true;
    material.needsUpdate = true;
    clippableMaterials.add(material);
  };

  const tilesRenderers: TilesRenderer[] = [];
  const pickRoots: THREE.Object3D[] = [];

  // One plugin instance per TilesRenderer: the renderer binds a plugin to a
  // single tileset and rejects sharing.
  const makeNormalizePlugin = () => ({
    name: "terrai-normalize-tileset",
    async fetchData(url: string, options?: RequestInit): Promise<Response> {
      const response = await fetch(url, options);
      if (!response.ok || !url.split("?")[0].endsWith("tileset.json")) return response;
      const normalized = normalizeTileset((await response.json()) as TilesetDocument);
      const synthesized = new Response(JSON.stringify(normalized), {
        status: 200,
        headers: { "content-type": "application/json" },
      });
      Object.defineProperty(synthesized, "url", { value: url });
      return synthesized;
    },
  });

  for (const [familyKey, family] of Object.entries(bundle.handoff.evidence_families)) {
    if (family.availability !== "available" || !family.sources) continue; // no geometry for the unresolved
    for (const source of family.sources) {
      const tilesetPaths = source.asset_paths.filter((path) => path.endsWith("tileset.json"));
      const geojsonPaths = source.asset_paths.filter((path) => path.endsWith(".geojson"));

      for (const assetPath of tilesetPaths) {
        handlers.onFamilyStatus(familyKey, "loading");
        let modelsLoaded = 0;
        const url = `${apiOrigin}/api/v1/assets/${assetPath.replace(/^data\//, "")}`;
        const tiles = new TilesRenderer(url);
        tiles.registerPlugin(makeNormalizePlugin() as never);
        // PLATEAU b3dm carries Draco-compressed glTF that *requires*
        // CESIUM_RTC; the library's extensions plugin wires both. The Draco
        // decoder is vendored under /draco so the scene stays offline-capable.
        const dracoLoader = new DRACOLoader();
        dracoLoader.setDecoderPath("/draco/");
        tiles.registerPlugin(new GLTFExtensionsPlugin({ rtc: true, dracoLoader }) as never);
        // Leaf geometric errors in the utility sample are 0; a small error
        // target reaches them. Renderer LOD tuning, not a data statement.
        tiles.errorTarget = 0.5;
        // Plain per-tile raycasting (not the accelerated bounds traversal)
        // respects the external local-frame matrix we render with.
        (tiles as unknown as { accelerateRaycast: boolean }).accelerateRaycast = false;
        tiles.setCamera(camera);
        tiles.setResolutionFromRenderer(camera, renderer);

        const utilityColor = utilityColorForAsset(assetPath);
        tiles.addEventListener("load-model", (event) => {
          modelsLoaded += 1;
          const model = (event as unknown as { scene: THREE.Object3D; tile: { content?: { uri?: string } } }).scene;
          const tile = (event as unknown as { tile: { content?: { uri?: string } } }).tile;
          model.traverse((object) => {
            object.userData.terrai = { familyKey, source, tileUri: tile?.content?.uri ?? null };
            const mesh = object as THREE.Mesh;
            if (!mesh.isMesh) return;
            if (utilityColor) {
              // The sample glTF publishes no materials; colour by class.
              const material = new THREE.MeshStandardMaterial({
                color: new THREE.Color(utilityColor),
                side: THREE.DoubleSide,
                metalness: 0.1,
                roughness: 0.8,
              });
              mesh.material = material;
              applyClipping(material);
            } else {
              for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
                (material as THREE.MeshStandardMaterial).side = THREE.DoubleSide;
                applyClipping(material);
              }
            }
          });
        });
        // 'tiles-load-end' fires when the load queues drain — the whole
        // visible tileset is in.
        tiles.addEventListener("tiles-load-end", () => handlers.onFamilyStatus(familyKey, "ready"));
        tiles.addEventListener("load-error", (event) => {
          // A handful of failed tiles in an otherwise-rendered set is worth a
          // console trace, not an "unavailable" verdict; error state is for a
          // family that produced nothing (e.g. the cache is absent).
          if (modelsLoaded === 0) {
            handlers.onFamilyStatus(familyKey, "error", String((event as unknown as { error?: unknown }).error ?? ""));
          }
        });

        // The tiles group arrives in ECEF; the handoff transform puts it in
        // the local frame. Never derived here, always taken from the bundle.
        tiles.group.matrixAutoUpdate = false;
        tiles.group.matrix.copy(worldToLocal);
        localFrameGroup.add(tiles.group);
        tilesRenderers.push(tiles);
        pickRoots.push(tiles.group);
      }

      for (const assetPath of geojsonPaths) {
        handlers.onFamilyStatus(familyKey, "loading");
        const url = `${apiOrigin}/api/v1/assets/${assetPath.replace(/^data\//, "")}`;
        void fetch(url)
          .then(async (response) => {
            if (!response.ok) throw new Error(`${response.status}`);
            const collection = (await response.json()) as {
              features: { geometry: { type: string; coordinates: unknown }; properties: Record<string, unknown> }[];
            };
            const group = buildAccessOverlay(collection.features, frame, familyKey, source);
            localFrameGroup.add(group);
            pickRoots.push(group);
            handlers.onFamilyStatus(familyKey, "ready");
          })
          .catch((cause) => handlers.onFamilyStatus(familyKey, "error", String(cause)));
      }
    }
  }

  // Picking: raycast → nearest tagged object → inverse transform to reality.
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  const onClick = (event: MouseEvent) => {
    const bounds = canvas.getBoundingClientRect();
    pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
    pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(pickRoots, true);
    const hit = hits.find((item) => (item.object as THREE.Mesh).isMesh || item.object.type === "Line" || item.object.type === "Points");
    if (!hit) {
      handlers.onPick(null);
      return;
    }
    let tagged: THREE.Object3D | null = hit.object;
    while (tagged && !tagged.userData.terrai) tagged = tagged.parent;
    if (!tagged) {
      handlers.onPick(null);
      return;
    }
    const tag = tagged.userData.terrai as { familyKey: string; source: EvidenceSource; tileUri: string | null };

    // b3dm feature identity: _BATCHID at the hit vertex → batch-table values.
    let batch: Record<string, unknown> | null = null;
    const mesh = hit.object as THREE.Mesh;
    if (mesh.isMesh && hit.face) {
      const attribute = mesh.geometry.getAttribute("_batchid") ?? mesh.geometry.getAttribute("_BATCHID");
      let root: THREE.Object3D | null = mesh;
      while (root && !(root as unknown as { batchTable?: unknown }).batchTable) root = root.parent;
      const table = (root as unknown as { batchTable?: { getDataFromId(id: number, target?: object): Record<string, unknown> } })?.batchTable;
      if (attribute && table) {
        batch = table.getDataFromId(attribute.getX(hit.face.a));
      }
    }

    // The exaggeration scale must not distort resolved coordinates.
    const local: [number, number, number] = [hit.point.x, hit.point.y, hit.point.z / localFrameGroup.scale.z];
    handlers.onPick({
      familyKey: tag.familyKey,
      datasetId: tag.source.dataset_id,
      tileUri: tag.tileUri,
      batch,
      localPoint: local,
      geographic: localToGeographic(frame, local),
      source: tag.source,
    });
  };
  canvas.addEventListener("click", onClick);

  let disposed = false;
  const renderLoop = () => {
    if (disposed) return;
    requestAnimationFrame(renderLoop);
    controls.update();
    camera.updateMatrixWorld();
    for (const tiles of tilesRenderers) {
      try {
        tiles.update();
      } catch {
        // One tileset must not kill the whole scene's frame loop.
      }
    }
    renderer.render(scene, camera);
  };

  const resize = () => {
    const width = canvas.clientWidth || canvas.parentElement?.clientWidth || 800;
    const height = canvas.clientHeight || canvas.parentElement?.clientHeight || 600;
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    for (const tiles of tilesRenderers) tiles.setResolutionFromRenderer(camera, renderer);
  };
  resize();
  renderLoop();

  let requestedAxis: SectionAxis | null = null;
  let requestedPosition = 0;
  const applySection = () => {
    sectionEnabled = requestedAxis !== null;
    if (requestedAxis) {
      sectionPlane.normal.set(requestedAxis === "x" ? -1 : 0, requestedAxis === "y" ? -1 : 0, requestedAxis === "z" ? -1 : 0);
      sectionPlane.constant = sectionPlaneConstant(requestedAxis, requestedPosition, localFrameGroup.scale.z);
    }
    for (const material of clippableMaterials) {
      material.clippingPlanes = sectionEnabled ? [sectionPlane] : [];
      material.needsUpdate = true;
    }
  };

  return {
    setExaggeration(factor) {
      localFrameGroup.scale.z = factor;
      applySection();
    },
    setSection(axis, position) {
      requestedAxis = axis;
      requestedPosition = position;
      applySection();
    },
    resize,
    destroy() {
      disposed = true;
      canvas.removeEventListener("click", onClick);
      controls.dispose();
      for (const tiles of tilesRenderers) tiles.dispose();
      renderer.dispose();
    },
  };
}

/**
 * The Sapporo OSM access snapshot as an independent overlay: subway tracks
 * and underground walkways as lines, entrances and stations as points.
 * Features publishing no level render at the local reference plane (z = 0,
 * the scene origin height) — stated in the viewer copy, never invented as a
 * measured depth. OSM geometry is never snapped to PLATEAU structures.
 */
/** Clipping planes live in world space while the requested section position is
 * in local metres; only the z axis rides the vertical-exaggeration scale. */
export function sectionPlaneConstant(axis: SectionAxis, position: number, zScale: number): number {
  return axis === "z" ? position * zScale : position;
}

export function buildAccessOverlay(
  features: { geometry: { type: string; coordinates: unknown }; properties: Record<string, unknown> }[],
  frame: SceneBundle["handoff"]["local_frame"],
  familyKey: string,
  source: EvidenceSource,
): THREE.Group {
  const group = new THREE.Group();
  group.userData.terrai = { familyKey, source, tileUri: null };
  const lineMaterial = new THREE.LineBasicMaterial({ color: new THREE.Color(palette.comms) });
  const pointMaterial = new THREE.PointsMaterial({ color: new THREE.Color(palette.lime), size: 6, sizeAttenuation: false });

  const toLocal = (position: number[]): [number, number, number] => {
    const height = Number.isFinite(Number(position[2])) && position.length > 2 ? Number(position[2]) : frame.origin_geographic_degrees_and_metres[2];
    return geographicToLocal(frame, [Number(position[0]), Number(position[1]), height]);
  };

  const points: number[] = [];
  for (const feature of features) {
    const { type, coordinates } = feature.geometry;
    if (type === "LineString") {
      const path = (coordinates as number[][]).map(toLocal);
      const geometry = new THREE.BufferGeometry().setFromPoints(path.map(([x, y, z]) => new THREE.Vector3(x, y, z)));
      const line = new THREE.Line(geometry, lineMaterial);
      line.userData.terrai = { familyKey, source, tileUri: null };
      group.add(line);
    } else if (type === "Point") {
      const [x, y, z] = toLocal(coordinates as number[]);
      points.push(x, y, z);
    }
  }
  if (points.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(points, 3));
    const cloud = new THREE.Points(geometry, pointMaterial);
    cloud.userData.terrai = { familyKey, source, tileUri: null };
    group.add(cloud);
  }
  return group;
}

export type { UndergroundFamily };
