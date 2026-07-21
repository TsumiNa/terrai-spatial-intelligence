<script lang="ts">
  import { mount, onMount, unmount } from "svelte";

  import { apiOrigin } from "../api/client";
  import { field, text, FIELD_LABELS } from "../audit";
  import FeaturePopup from "./FeaturePopup.svelte";
  import { i18n } from "../i18n/i18n.svelte";
  import { buildAnalyticalLayers, drawsOwnBuildings, geometryBounds, queuePopup, type PopupSpec } from "../map/layers";
  import { createExhibitionMap, type ExhibitionMap } from "../map/map";
  import { normalizeView } from "../modules";
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

  function openFeaturePopup(spec: PopupSpec, feature: Feature, coordinate: [number, number]) {
    if (!mapApi) return;
    const props = feature.properties;
    const t = i18n.t.bind(i18n);
    const fields = spec.fields.map((item) => {
      const value = item.value(props, t);
      return { label: text(FIELD_LABELS[item.key], i18n.lang), text: value, record: field(item.key, value, props) };
    });
    const host = document.createElement("div");
    const instance = mount(FeaturePopup, {
      target: host,
      props: { eyebrow: t(spec.eyebrow), title: spec.title(props, t), fields },
    });
    mapApi.openPopup(coordinate, host, () => void unmount(instance));
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

  // Analytical layers rebuild only when module, view or data change — not on
  // a language switch; popup content resolves its language at open time.
  $effect(() => {
    const module = app.module;
    const view = normalizeView(module, app.view);
    const data = app.data;
    if (!mapApi || !data) return;
    mapApi.closePopup();
    mapApi.setAnalyticalLayers(buildAnalyticalLayers(module, view, data, assetBase, { onFeature: openFeaturePopup }));
    mapApi.setVectorBuildingsVisible(!drawsOwnBuildings(module, view));
  });

  // Parity with the old shell: a language switch closes any open popup.
  $effect(() => {
    void i18n.lang;
    mapApi?.closePopup();
  });

  // Queue-to-map: frame the selected feature and open its popup.
  $effect(() => {
    const selection = app.queueSelection;
    if (!mapApi || !selection) return;
    const bounds = geometryBounds(selection.feature.geometry);
    if (!bounds) return;
    mapApi.frame(bounds);
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
      <div class="map-legend">
        {#each vm.legend as item, index (index)}
          <span class="legend-item"><i class="legend-dot" style={`background:${item.color}`}></i>{item.label}</span>
        {/each}
      </div>
    </div>
  </div>
  <div id="map" bind:this={container} aria-label={i18n.t("map.aria")}></div>
  <div class="map-note">{vm.mapNote}</div>
</div>
