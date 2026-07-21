<script lang="ts">
  import { mount, onMount, unmount } from "svelte";

  import { apiOrigin } from "../api/client";
  import { field, text, undergroundField, FIELD_LABELS, type AuditRecord, type FieldKey } from "../audit";
  import FeaturePopup from "./FeaturePopup.svelte";
  import { i18n } from "../i18n/i18n.svelte";
  import { buildAnalyticalLayers, drawsOwnBuildings, geometryBounds, queuePopup, type PopupSpec } from "../map/layers";
  import { buildUndergroundLayers } from "../map/underground-layers";
  import { createExhibitionMap, type ExhibitionMap } from "../map/map";
  import { RASTER_REGIONS } from "../map/config";
  import { normalizeView, undergroundAuditContext, undergroundClassKey } from "../modules";
  import { familyResources, materialLabel, summarizeAsset, type UndergroundFamily, type UndergroundResource } from "../underground";
  import { matchScene, sceneExtent, type SceneBundle, type SceneCatalog } from "../scene/catalog";
  import { createApiClient } from "../api/client";
  import { app, BASEMAP_KEYS } from "../state.svelte";
  import type { Feature } from "../api/types";
  import type { ModuleVM } from "../modules";
  import type { MessageKey } from "../i18n/i18n.svelte";

  let { vm }: { vm: ModuleVM } = $props();

  const basemapLabel: Record<(typeof BASEMAP_KEYS)[number], { label: MessageKey; title: MessageKey }> = {
    standard: { label: "basemap.standard", title: "basemap.standardTitle" },
    photo: { label: "basemap.photo", title: "basemap.photoTitle" },
    hillshade: { label: "basemap.hillshade", title: "basemap.hillshadeTitle" },
    slope: { label: "basemap.slope", title: "basemap.slopeTitle" },
  };

  const assetBase = `${apiOrigin(typeof window === "undefined" ? "" : window.location.search)}/api/v1/assets`;

  let container: HTMLElement;
  // $state.raw: the handle is stored for effects, never wrapped reactively.
  let mapApi = $state.raw<ExhibitionMap | null>(null);

  // --- catalogued 3D scenes (underground module) -------------------------
  let sceneCatalog = $state.raw<SceneCatalog | null>(null);
  let boxArmed = $state(false);
  let sceneMessage = $state<string | null>(null);

  $effect(() => {
    if (app.module !== "underground" || sceneCatalog) return;
    void createApiClient()
      .GET("/api/v1/scenes")
      .then(({ data }) => {
        if (data) sceneCatalog = data as unknown as SceneCatalog;
      })
      .catch(() => {});
  });

  // Leaving the module disarms a pending box selection.
  $effect(() => {
    if (app.module !== "underground" && boxArmed) {
      boxArmed = false;
      mapApi?.setBoxSelect(null);
    }
  });

  function armBoxSelect() {
    if (!mapApi || !sceneCatalog) return;
    if (boxArmed) {
      boxArmed = false;
      mapApi.setBoxSelect(null);
      return;
    }
    boxArmed = true;
    sceneMessage = null;
    mapApi.setBoxSelect((bounds) => {
      boxArmed = false;
      const match = matchScene(bounds, sceneCatalog?.scenes ?? []);
      if (!match) {
        sceneMessage = i18n.t("scene.noSceneHere");
        window.setTimeout(() => (sceneMessage = null), 4000);
        return;
      }
      void createApiClient()
        .GET("/api/v1/scenes/{scene_id}", { params: { path: { scene_id: match.scene_id } } })
        .then(({ data }) => {
          if (data) app.openScene(data as unknown as SceneBundle);
        })
        .catch(() => {
          sceneMessage = i18n.t("underground.errorBody");
          window.setTimeout(() => (sceneMessage = null), 4000);
        });
    });
  }

  function showPopup(coordinate: [number, number], props: { eyebrow: string; title: string; fields: { label: string; text: string | number; record: AuditRecord }[] }) {
    if (!mapApi) return;
    const host = document.createElement("div");
    const instance = mount(FeaturePopup, { target: host, props });
    mapApi.openPopup(coordinate, host, () => void unmount(instance));
  }

  function openFeaturePopup(spec: PopupSpec, feature: Feature, coordinate: [number, number]) {
    const props = feature.properties;
    const t = i18n.t.bind(i18n);
    const fields = spec.fields.map((item) => {
      const value = item.value(props, t);
      return { label: text(FIELD_LABELS[item.key], i18n.lang), text: value, record: field(item.key, value, props) };
    });
    showPopup(coordinate, { eyebrow: t(spec.eyebrow), title: spec.title(props, t), fields });
  }

  /** A picked underground asset: its audit-index features rolled up, every
   * field resolving to the same source/asset/date provenance. Granularity is
   * the asset (one glTF tile); it is feature-level exactly when the asset
   * holds a single feature. */
  function openUndergroundAssetPopup(resource: UndergroundResource, contentUri: string, coordinate: [number, number]) {
    const state = app.underground;
    if (state.status !== "ready" || !state.manifest || !state.auditIndex) return;
    const features = state.auditIndex.features.filter(
      (item) => item.source_resource_id === resource.resource_id && item.source_asset === contentUri,
    );
    if (!features.length) return;
    const summary = summarizeAsset(features);
    const context = {
      ...undergroundAuditContext(resource, state.manifest.retrieved_at, state.manifest.package_page),
      assetPath: contentUri,
      featureIds: features.map((item) => item.source_feature_id),
      creationDates: [...new Set(features.map((item) => item.attributes["core:creationDate"]).filter(Boolean))] as string[],
    };
    const entry = (key: FieldKey, value: string | number) => ({
      label: text(FIELD_LABELS[key], i18n.lang),
      text: value,
      record: undergroundField(key, value, context),
    });
    const fields = [
      entry("field.featureCount", features.length),
      // Depth and diameter render as published; the source declares no units.
      entry("field.depthRange", summary.depthRange ? `${summary.depthRange[0]} – ${summary.depthRange[1]}` : "—"),
      entry("field.diameter", summary.diameters.join(" · ") || "—"),
      entry("field.materials", summary.materialCodes.map(materialLabel).join(" · ") || "—"),
      entry("field.mesureType", summary.mesureTypes.join(", ") || "—"),
    ];
    const title = summary.names.join(" · ") || contentUri.split("/").pop() || contentUri;
    showPopup(coordinate, { eyebrow: i18n.t(undergroundClassKey(resource.utility_class)), title, fields });
  }

  onMount(() => {
    let disposed = false;
    let api: ExhibitionMap | undefined;
    createExhibitionMap(container, assetBase, { region: vm.region, basemap: app.basemap })
      .then((created) => {
        if (disposed) created.destroy();
        else {
          api = created;
          mapApi = created;
        }
      })
      .catch((cause) => console.error("map initialisation failed", cause));
    return () => {
      disposed = true;
      api?.destroy();
    };
  });

  $effect(() => {
    mapApi?.setRegion(vm.region);
  });
  $effect(() => {
    mapApi?.setBasemap(app.basemap);
  });
  $effect(() => {
    mapApi?.setUndergroundMode(app.module === "underground");
  });

  // Analytical layers rebuild only when module, view or data change — not on
  // a language switch; popup content resolves its language at open time.
  $effect(() => {
    const module = app.module;
    const view = normalizeView(module, app.view);
    const data = app.data;
    if (!mapApi || !data) return;
    mapApi.closePopup();
    if (module === "underground") {
      const underground = app.underground;
      const resources =
        underground.status === "ready" && underground.manifest
          ? familyResources(underground.manifest, view as UndergroundFamily)
          : [];
      mapApi.setAnalyticalLayers(buildUndergroundLayers(resources, assetBase, { onAsset: openUndergroundAssetPopup }));
    } else {
      mapApi.setAnalyticalLayers(buildAnalyticalLayers(module, view, data, assetBase, { onFeature: openFeaturePopup }));
    }
    mapApi.setVectorBuildingsVisible(!drawsOwnBuildings(module, view));
  });

  // Parity with the old shell: a language switch closes any open popup.
  $effect(() => {
    void i18n.lang;
    mapApi?.closePopup();
  });

  // Queue-to-map: frame the selected feature. Analytical queues also open the
  // feature's popup; underground queue rows are asset layers, whose popups
  // belong to real picked geometry, so framing alone is the honest action.
  $effect(() => {
    const selection = app.queueSelection;
    if (!mapApi || !selection) return;
    const bounds = geometryBounds(selection.feature.geometry);
    if (!bounds) return;
    mapApi.frame(bounds);
    if (app.module === "underground") return;
    const center: [number, number] = [(bounds[0] + bounds[2]) / 2, (bounds[1] + bounds[3]) / 2];
    openFeaturePopup(queuePopup(app.module, normalizeView(app.module, app.view)), selection.feature, center);
  });
</script>

<div class="map-card">
  <div class="map-toolbar">
    <div class="view-tabs">
      {#each vm.tabs as tab (tab.view)}
        <button class="view-tab" class:active={tab.view === vm.activeView} onclick={() => app.selectView(tab.view)}>
          {tab.label}
        </button>
      {/each}
    </div>
    <div class="map-tools">
      <div class="basemap-switcher" aria-label={i18n.t("basemap.aria")}>
        {#each BASEMAP_KEYS as key (key)}
          <button
            class="basemap-button"
            class:active={key === app.basemap}
            title={i18n.t(basemapLabel[key].title)}
            disabled={key !== "standard" && !RASTER_REGIONS.includes(vm.region)}
            onclick={() => app.selectBasemap(key)}
          >
            {i18n.t(basemapLabel[key].label)}
          </button>
        {/each}
      </div>
      {#if app.module === "underground" && sceneCatalog}
        <div class="basemap-switcher" aria-label={i18n.t("scene.catalogScenes")}>
          {#each sceneCatalog.scenes as entry (entry.scene_id)}
            <button class="basemap-button" title={entry.purpose} onclick={() => mapApi?.frame(sceneExtent(entry))}>
              {entry.scene_id === "nihonbashi-utilities" ? i18n.t("region.nihonbashi") : entry.scene_id}
            </button>
          {/each}
          <button
            class="basemap-button"
            class:active={boxArmed}
            title={i18n.t("scene.boxSelectHint")}
            onclick={armBoxSelect}
          >
            {i18n.t("scene.boxSelect")}
          </button>
        </div>
      {/if}
      <div class="map-legend">
        {#each vm.legend as item, index (index)}
          <span class="legend-item"><i class="legend-dot" style={`background:${item.color}`}></i>{item.label}</span>
        {/each}
      </div>
    </div>
  </div>
  <div id="map" bind:this={container} aria-label={i18n.t("map.aria")}></div>
  {#if sceneMessage}
    <div class="absolute left-1/2 top-16 z-20 -translate-x-1/2 rounded-card border border-line bg-paper/95 px-4 py-2 text-xs text-ink shadow-card" role="status">
      {sceneMessage}
    </div>
  {/if}
  {#if vm.notice}
    <!-- The notice is a pure status display and the whole overlay is
         click-through: box selection works from the committed catalog even
         when the tile cache is absent, and the card sits centred exactly
         where a box would be dragged. -->
    <div class="pointer-events-none absolute inset-0 z-10 grid place-items-center p-6" role="status">
      <div class="max-w-md rounded-panel border border-line bg-paper/95 p-6 text-center shadow-card">
        <strong class="text-ink">{vm.notice.title}</strong>
        <p class="mt-2 text-sm leading-relaxed text-muted">{vm.notice.body}</p>
      </div>
    </div>
  {/if}
  <div class="map-note">{vm.mapNote}</div>
</div>
