/**
 * The one loading path for underground scene discovery and bundles.
 *
 * The scene catalog and per-scene handoffs are whole documents behind the
 * bundle endpoint the renderer stage defined (`GET /api/v1/scenes`,
 * `GET /api/v1/scenes/{scene_id}`); they are not feature collections, so the
 * windowed bbox client is the wrong shape for them. What "one path" means
 * here: every scene request goes through this module and the shared typed
 * client — no component-level fetch, no silent failure, and every bundle is
 * checked before it becomes application state.
 *
 * The frontend is a consumer of coordinate and availability facts, never a
 * source of them. The checks below restate nothing: they verify the bundle's
 * own isolation invariants — assets inside the scene's approved roots, roots
 * belonging to exactly the bundle's owner, unavailable families carrying no
 * fabricated metadata — and refuse the bundle otherwise.
 */

import { createApiClient } from "../api/client";
import type { SceneBundle, SceneCatalog } from "./catalog";

export class SceneIntakeError extends Error {}

interface ApiLike {
  GET(
    path: "/api/v1/scenes" | "/api/v1/scenes/{scene_id}",
    init?: unknown,
  ): Promise<{ data?: unknown; error?: unknown }>;
}

/** Path markers that identify each canonical scene's data roots. The two
 *  scenes are never resolved together: a bundle whose approved roots carry
 *  the other owner's marker is refused before it can reach the viewer. */
const OWNER_ROOT_MARKERS: Record<string, string[]> = {
  uc24_16_nihonbashi: ["plateau_uc24_16", "uc24_16_nihonbashi"],
  uc24_13_sapporo: ["plateau_uc24_13", "uc24_13_sapporo", "osm/sapporo_underground_access"],
};

function insideRoots(path: string, roots: string[]): boolean {
  // A non-canonical path (absolute, traversal or empty segments) could pass
  // a prefix check while resolving outside the root; reject it outright.
  const segments = path.split("/");
  if (path.startsWith("/") || segments.some((segment) => segment === ".." || segment === "." || segment === "")) {
    return false;
  }
  return roots.some((root) => path === root || path.startsWith(`${root}/`));
}

/** Refuse a bundle that violates its own isolation or honesty invariants. */
export function assertSingleSceneBundle(bundle: SceneBundle): SceneBundle {
  const owner = bundle.handoff.owner_dataset_key;
  if (bundle.scene.owner_dataset_key !== owner || bundle.scene.scene_id !== bundle.handoff.scene_id) {
    throw new SceneIntakeError(
      `bundle identity mismatch: catalog says ${bundle.scene.scene_id}/${bundle.scene.owner_dataset_key}, ` +
        `handoff says ${bundle.handoff.scene_id}/${owner}`,
    );
  }
  const ownMarkers = OWNER_ROOT_MARKERS[owner];
  if (!ownMarkers) throw new SceneIntakeError(`unknown scene owner: ${owner}`);
  const foreignMarkers = Object.entries(OWNER_ROOT_MARKERS)
    .filter(([key]) => key !== owner)
    .flatMap(([, markers]) => markers);

  const roots = bundle.handoff.approved_roots;
  if (!roots?.length) throw new SceneIntakeError(`${bundle.scene.scene_id} has no approved roots`);
  for (const root of roots) {
    if (foreignMarkers.some((marker) => root.includes(marker))) {
      throw new SceneIntakeError(`${bundle.scene.scene_id} carries another scene's root: ${root}`);
    }
    if (!ownMarkers.some((marker) => root.includes(marker))) {
      throw new SceneIntakeError(`${bundle.scene.scene_id} carries a root outside its owner's data: ${root}`);
    }
  }

  for (const [name, family] of Object.entries(bundle.handoff.evidence_families)) {
    if (family.availability !== "available") {
      // A stated absence carries no geometry, no counts and no model
      // identity — collapsing that distinction is refused, not repaired.
      if (family.sources || family.evidence_class) {
        throw new SceneIntakeError(`unavailable ${name} evidence carries fabricated metadata`);
      }
      continue;
    }
    for (const source of family.sources ?? []) {
      for (const path of [source.audit_index_path, ...source.asset_paths]) {
        if (!insideRoots(path, roots)) {
          throw new SceneIntakeError(`${name} evidence escapes the scene's approved roots: ${path}`);
        }
      }
    }
  }
  return bundle;
}

export async function loadSceneCatalog(api: ApiLike = createApiClient()): Promise<SceneCatalog> {
  const { data, error } = await api.GET("/api/v1/scenes");
  if (error || !data) throw new SceneIntakeError("the scene catalog request failed");
  return data as SceneCatalog;
}

export async function loadSceneBundle(sceneId: string, api: ApiLike = createApiClient()): Promise<SceneBundle> {
  const { data, error } = await api.GET("/api/v1/scenes/{scene_id}", {
    params: { path: { scene_id: sceneId } },
  });
  if (error || !data) throw new SceneIntakeError(`the scene bundle request failed: ${sceneId}`);
  return assertSingleSceneBundle(data as SceneBundle);
}
