<script lang="ts">
  import { i18n } from "../i18n/i18n.svelte";
  import { app, BASEMAP_KEYS } from "../state.svelte";
  import type { ModuleVM } from "../modules";
  import type { MessageKey } from "../i18n/i18n.svelte";

  let { vm }: { vm: ModuleVM } = $props();

  const basemapLabel: Record<(typeof BASEMAP_KEYS)[number], { label: MessageKey; title: MessageKey }> = {
    standard: { label: "basemap.standard", title: "basemap.standardTitle" },
    photo: { label: "basemap.photo", title: "basemap.photoTitle" },
    hillshade: { label: "basemap.hillshade", title: "basemap.hillshadeTitle" },
    slope: { label: "basemap.slope", title: "basemap.slopeTitle" },
  };
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
  <div id="map" class="map-placeholder" role="img" aria-label={i18n.t("map.aria")}>
    <span>{i18n.t("map.placeholder")}</span>
  </div>
  <div class="map-note">{vm.mapNote}</div>
</div>
