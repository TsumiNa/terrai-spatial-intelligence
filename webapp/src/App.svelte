<script lang="ts">
  import { onMount } from "svelte";

  import { apiOrigin, createApiClient } from "./lib/api/client";
  import type { Bootstrap } from "./lib/api/types";
  import type { UndergroundAuditIndex, UndergroundManifest } from "./lib/underground";
  import AuditDrawer from "./lib/components/AuditDrawer.svelte";
  import SceneViewer from "./lib/components/SceneViewer.svelte";
  import Hero from "./lib/components/Hero.svelte";
  import MapCard from "./lib/components/MapCard.svelte";
  import Metrics from "./lib/components/Metrics.svelte";
  import QueuePanel from "./lib/components/QueuePanel.svelte";
  import Sidebar from "./lib/components/Sidebar.svelte";
  import Topbar from "./lib/components/Topbar.svelte";
  import { i18n } from "./lib/i18n/i18n.svelte";
  import { buildModuleVM } from "./lib/modules";
  import { app } from "./lib/state.svelte";

  const vm = $derived(app.data ? buildModuleVM(app.module, app.view, app.data, app.underground) : null);

  $effect(() => {
    document.documentElement.lang = i18n.lang === "zh" ? "zh-CN" : i18n.lang;
  });

  $effect(() => {
    if (vm) app.syncUrl(vm.activeView);
  });

  // The underground module's data is on demand: first entry checks /catalog
  // readiness, then loads the manifest and audit index. Nothing is fetched
  // until the module is opened, and an absent cache is an honest state.
  $effect(() => {
    if (app.module !== "underground" || app.underground.status !== "unknown") return;
    app.setUndergroundLoading();
    void (async () => {
      try {
        const client = createApiClient();
        const catalog = await client.GET("/api/v1/catalog");
        // An unreachable or failing API is an error, not "cache absent".
        if (catalog.error || !catalog.data) throw new Error("catalog request failed");
        const rows = (catalog.data as { datasets?: { key: string; ready: boolean }[] }).datasets ?? [];
        if (!rows.length) throw new Error("catalog returned no datasets");
        if (!rows.find((row) => row.key === "uc24_16_nihonbashi")?.ready) {
          app.setUndergroundUnavailable();
          return;
        }
        const origin = apiOrigin(window.location.search);
        const [manifest, auditIndex] = await Promise.all([
          client.GET("/api/v1/datasets/{key}", { params: { path: { key: "uc24_16_nihonbashi" } } }),
          fetch(`${origin}/api/v1/assets/plateau/uc24_16_nihonbashi/audit_index.json`),
        ]);
        if (manifest.error || !manifest.data || !auditIndex.ok) throw new Error("underground manifest fetch failed");
        app.setUndergroundReady(
          manifest.data as unknown as UndergroundManifest,
          (await auditIndex.json()) as UndergroundAuditIndex,
        );
      } catch (cause) {
        console.error("underground data load failed", cause);
        app.setUndergroundUnavailable("error");
      }
    })();
  });

  onMount(async () => {
    try {
      const client = createApiClient();
      const { data, error } = await client.GET("/api/v1/bootstrap");
      if (error || !data) throw new Error(`bootstrap: ${error ? JSON.stringify(error) : "empty response"}`);
      // The endpoint returns an open object in the OpenAPI schema; the shape
      // itself is maintained by hand in lib/api/types.ts.
      app.setData(data as unknown as Bootstrap);
    } catch (cause) {
      app.setLoadError(cause instanceof Error ? cause.message : String(cause));
    }
  });
</script>

<div class="app-shell">
  <Sidebar />
  <main class="workspace">
    <Topbar {vm} />
    {#if vm}
      <Hero {vm} />
      <Metrics {vm} />
      <section class="analysis-grid">
        <MapCard {vm} />
        <QueuePanel {vm} />
      </section>
    {/if}
  </main>
</div>

<AuditDrawer />
<SceneViewer />

<div class="loading" class:done={app.data !== null}>
  {#if app.loadError}
    <strong>{i18n.t("loading.failed")}</strong><span>{app.loadError}</span>
  {:else}
    <div class="loader"></div>
    <span>{i18n.t("loading.connecting")}</span>
  {/if}
</div>
