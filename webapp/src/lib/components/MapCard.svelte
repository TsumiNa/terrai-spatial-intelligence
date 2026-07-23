<script lang="ts">
  import { mount, onDestroy, onMount, unmount, untrack } from "svelte";

  import { Popover } from "bits-ui";

  import { apiOrigin } from "../api/client";
  import { field, foundationField, localized, text, undergroundField, FIELD_LABELS, type AuditRecord, type FieldKey } from "../audit";
  import FeaturePopup from "./FeaturePopup.svelte";
  import { foundationLayer, renderableFoundationLayers } from "../features/registry";
  import { createWindowedFeatureClient, type WindowedState } from "../features/windowed";
  import { i18n } from "../i18n/i18n.svelte";
  import { buildAnalyticalLayers, buildWindowedFeatureLayer, geometryBounds, queuePopup, type PopupSpec } from "../map/layers";
  import { buildUndergroundLayers } from "../map/underground-layers";
  import { createExhibitionMap, type ExhibitionMap } from "../map/map";
  import { normalizeView, undergroundAuditContext, undergroundClassKey } from "../modules";
  import { familyResources, materialLabel, summarizeAsset, type UndergroundFamily, type UndergroundResource } from "../underground";
  import { matchScene, sceneExtent, type SceneCatalog } from "../scene/catalog";
  import { loadSceneBundle, loadSceneCatalog } from "../scene/intake";
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

  // --- foundation overlays -----------------------------------------------
  // One windowed client per visible registry layer; the clients own every
  // fetch decision and this component only relays the map's settled
  // viewports in and plain state snapshots out. Visibility itself lives in
  // app state, so it survives module, view, region and language switches.
  const renderableLayers = renderableFoundationLayers();
  // The basemap-detail layer joins the windowed machinery automatically on
  // the standard basemap in every module — the building experience belongs
  // to the basemap, uniformly: GSI texture below the handover, OSM data
  // objects above it, and analysis buildings simply draw on top (they are
  // the same OSM footprints, so the analysis color covers its own outline).
  function activeDetailKeys(): string[] {
    const wanted = app.basemap === "standard" && app.module !== "underground";
    return wanted ? renderableLayers.filter((entry) => entry.basemapDetail).map((entry) => entry.key) : [];
  }
  let foundationStates = $state.raw<Record<string, WindowedState>>({});
  // Non-reactive by design: clients are synced incrementally, so toggling
  // one layer never recreates the others or drops their window caches.
  const foundationClients = new Map<string, ReturnType<typeof createWindowedFeatureClient>>();
  let lastView: { bounds: [number, number, number, number]; zoom: number } | null = null;

  $effect(() => {
    if (!mapApi) return;
    const unsubscribe = mapApi.onViewChange((view) => {
      lastView = view;
      for (const client of foundationClients.values()) client.viewChanged(view);
    });
    return unsubscribe;
  });

  $effect(() => {
    const wanted = new Set([
      ...app.foundationLayers.filter((key) => renderableLayers.some((entry) => entry.key === key)),
      ...activeDetailKeys(),
    ]);
    untrack(() => {
      for (const [key, client] of [...foundationClients]) {
        if (wanted.has(key)) continue;
        client.destroy();
        foundationClients.delete(key);
        const next = { ...foundationStates };
        delete next[key];
        foundationStates = next;
      }
      for (const key of wanted) {
        if (foundationClients.has(key)) continue;
        const entry = renderableLayers.find((item) => item.key === key);
        if (!entry) continue;
        const client = createWindowedFeatureClient({
          api: createApiClient(),
          datasetKey: entry.key,
          extents: entry.extents,
          minZoom: entry.minZoom,
          windowLimit: entry.windowLimit,
          onState: (state) => (foundationStates = { ...foundationStates, [entry.key]: state }),
        });
        foundationClients.set(key, client);
        if (lastView) client.viewChanged(lastView);
      }
    });
  });

  onDestroy(() => {
    for (const client of foundationClients.values()) client.destroy();
    foundationClients.clear();
  });

  const activeAttributions = $derived(
    [...activeDetailKeys(), ...app.foundationLayers]
      .map((key) => foundationLayer(key))
      .filter((entry) => entry !== undefined)
      .map((entry) => `${i18n.t(entry.name)} — ${entry.attribution} · ${entry.license}`),
  );

  function openFoundationPopup(key: string, feature: Feature, coordinate: [number, number]) {
    const entry = foundationLayer(key);
    if (!entry) return;
    const props = feature.properties as Record<string, unknown>;
    // The audit "source field" names where the shown value actually came
    // from — the feature property that supplied it, or the registry.
    const pick = (candidates: string[], fallback: string): { value: string; field: string } => {
      for (const name of candidates) {
        if (props[name] != null) return { value: String(props[name]), field: name };
      }
      return { value: fallback, field: "registry" };
    };
    const retrieved = pick(["terrai_retrieved_at", "osm_timestamp"], "—");
    const sourceUpdated = pick(["terrai_source_updated_at"], entry.sourceUpdatedAt);
    const sourceLayer = pick(["terrai_source_layer", "feature_class"], "—");
    const rawUrl = props.terrai_source_url ?? props.source_url;
    const sourceUrl = typeof rawUrl === "string" ? rawUrl : undefined;
    const context = (sourceField: string) => ({
      attribution: entry.attribution,
      license: entry.license,
      sourceUpdatedAt: sourceUpdated.value,
      retrievedAt: retrieved.value,
      sourceField,
      datasetKey: key,
      sourceUrl,
      limitations: entry.limitations,
    });
    const t = i18n.t.bind(i18n);
    const fields = [
      { label: t("fl.sourceLayer"), text: sourceLayer.value, record: foundationField(localized("fl.sourceLayer"), sourceLayer.value, context(sourceLayer.field)) },
      { label: t("fl.sourceUpdatedAt"), text: sourceUpdated.value, record: foundationField(localized("fl.sourceUpdatedAt"), sourceUpdated.value, context(sourceUpdated.field)) },
      { label: t("fl.retrievedAt"), text: retrieved.value, record: foundationField(localized("fl.retrievedAt"), retrieved.value, context(retrieved.field)) },
      { label: t("fl.license"), text: entry.license, record: foundationField(localized("fl.license"), entry.license, context("registry")) },
    ];
    showPopup(coordinate, { eyebrow: t("fl.eyebrow"), title: t(entry.name), fields });
  }

  $effect(() => {
    if (app.module !== "underground" || sceneCatalog) return;
    loadSceneCatalog()
      .then((catalog) => (sceneCatalog = catalog))
      .catch(() => {
        // A failed catalog is a visible state, not a silently missing control.
        sceneMessage = i18n.t("underground.errorBody");
        window.setTimeout(() => (sceneMessage = null), 4000);
      });
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
      loadSceneBundle(match.scene_id)
        .then((validated) => app.openScene(validated))
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
    createExhibitionMap(container, { region: vm.region, basemap: app.basemap })
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

  // A popup belongs to the module/view/data it was opened in; leaving any of
  // them closes it. Deliberately NOT part of the layer-rebuild effect below:
  // that one also re-runs on every windowed-overlay state change, and a
  // detail-layer window arriving must never close an open popup.
  $effect(() => {
    void app.module;
    void app.view;
    void app.data;
    mapApi?.closePopup();
  });

  // Layers rebuild when module, view, data or an overlay window change — not
  // on a language switch; popup content resolves its language at open time.
  $effect(() => {
    const module = app.module;
    const view = normalizeView(module, app.view);
    const data = app.data;
    if (!mapApi || !data) return;
    if (module === "underground") {
      const underground = app.underground;
      const resources =
        underground.status === "ready" && underground.manifest
          ? familyResources(underground.manifest, view as UndergroundFamily)
          : [];
      mapApi.setAnalyticalLayers(buildUndergroundLayers(resources, assetBase, { onAsset: openUndergroundAssetPopup }));
    } else {
      // Foundation overlays are context: they render beneath the analysis,
      // and deck's topmost-first picking means an analytical feature wins
      // any contested click.
      const overlays = [...activeDetailKeys(), ...app.foundationLayers]
        .map((key) => ({ key, state: foundationStates[key] }))
        .filter((item) => item.state?.status === "ready")
        .map(({ key, state }) =>
          buildWindowedFeatureLayer(key, state.features, {
            onFeature: (feature, coordinate) => openFoundationPopup(key, feature, coordinate),
          }),
        );
      mapApi.setAnalyticalLayers([
        ...overlays,
        ...buildAnalyticalLayers(module, view, data, assetBase, { onFeature: openFeaturePopup }),
      ]);
    }
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
            onclick={() => app.selectBasemap(key)}
          >
            {i18n.t(basemapLabel[key].label)}
          </button>
        {/each}
      </div>
      {#if app.module !== "underground"}
        <Popover.Root>
          <Popover.Trigger
            class="basemap-button foundation-toggle"
            aria-pressed={app.foundationLayers.length > 0}
            title={i18n.t("layers.title")}
          >
            {i18n.t("layers.toggle")}{app.foundationLayers.length ? ` · ${app.foundationLayers.length}` : ""}
          </Popover.Trigger>
          <Popover.Portal>
            <Popover.Content
              class="foundation-panel z-30 flex min-w-64 flex-col gap-1 rounded-card border border-line bg-paper p-2 shadow-card"
              sideOffset={6}
              aria-label={i18n.t("layers.aria")}
            >
              {#each renderableLayers.filter((entry) => !entry.basemapDetail) as entry (entry.key)}
                {@const on = app.foundationLayers.includes(entry.key)}
                {@const status = on ? (foundationStates[entry.key]?.status ?? "loading") : "off"}
                <button
                  class="foundation-item flex items-center justify-between gap-3 rounded-card px-2 py-1 text-left text-xs text-ink hover:bg-line/40"
                  class:active={on}
                  aria-pressed={on}
                  data-layer={entry.key}
                  onclick={() => app.toggleFoundationLayer(entry.key)}
                >
                  <span>{i18n.t(entry.name)}</span>
                  <span class="foundation-status text-[10px] text-muted" data-layer-status={status}>
                    {#if status === "off"}
                      —
                    {:else if status === "ready"}
                      {i18n.t("windowed.ready", { n: foundationStates[entry.key]?.matched ?? 0 })}
                    {:else if status === "loading" || status === "idle"}
                      {i18n.t("windowed.loading")}
                    {:else if status === "belowZoom"}
                      {i18n.t("windowed.belowZoom")}
                    {:else if status === "outside"}
                      {i18n.t("windowed.outside")}
                    {:else if status === "empty"}
                      {i18n.t("windowed.empty")}
                    {:else if status === "oversized"}
                      {i18n.t("windowed.oversized")}
                    {:else}
                      {i18n.t("windowed.error")}
                    {/if}
                  </span>
                </button>
              {/each}
            </Popover.Content>
          </Popover.Portal>
        </Popover.Root>
      {/if}
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
  {#if activeAttributions.length}
    <!-- Attribution is registry-driven and not optional: it stays on screen
         for as long as any foundation overlay is visible. -->
    <div
      class="map-attribution pointer-events-none absolute bottom-8 left-2 z-10 max-w-2xl rounded-card border border-line bg-paper/90 px-2 py-1 text-[10px] leading-snug text-muted"
      role="note"
    >
      {#each activeAttributions as line (line)}
        <span class="block">{line}</span>
      {/each}
    </div>
  {/if}
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
