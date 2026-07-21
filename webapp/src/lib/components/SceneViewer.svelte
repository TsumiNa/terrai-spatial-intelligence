<script lang="ts">
  import { untrack } from "svelte";
  import { Dialog } from "bits-ui";

  import AuditTrigger from "./AuditTrigger.svelte";
  import { sceneElement, type SceneAuditContext } from "../audit";
  import { apiOrigin } from "../api/client";
  import { i18n, type MessageKey } from "../i18n/i18n.svelte";
  import { EVIDENCE_FAMILIES } from "../scene/catalog";
  import { createSiteScene, type PickedElement, type SectionAxis, type SiteScene } from "../scene/scene";
  import { app } from "../state.svelte";

  const bundle = $derived(app.sceneBundle);

  let canvas = $state.raw<HTMLCanvasElement | null>(null);
  let site = $state.raw<SiteScene | null>(null);
  let picked = $state.raw<PickedElement | null>(null);
  let familyStatus = $state<Record<string, "loading" | "ready" | "error">>({});
  let exaggeration = $state(1);
  let sectionAxis = $state<SectionAxis | null>(null);
  let sectionPosition = $state(0);

  const origin = apiOrigin(typeof window === "undefined" ? "" : window.location.search);

  // The scene is created when the dialog content (and its canvas) mounts and
  // destroyed when it leaves; the map underneath is never touched.
  $effect(() => {
    if (!bundle || !canvas) return;
    picked = null;
    familyStatus = {};
    exaggeration = 1;
    sectionAxis = null;
    sectionPosition = 0;
    // untrack: the synchronous onFamilyStatus calls during creation read
    // familyStatus; tracked, they would make this effect depend on the very
    // state its callbacks write and recreate the scene forever.
    const created = untrack(() =>
      createSiteScene(canvas!, bundle, origin, {
        onPick: (element) => (picked = element),
        onFamilyStatus: (familyKey, status) => {
          familyStatus = { ...familyStatus, [familyKey]: status };
        },
      }),
    );
    site = created;
    const observer = new ResizeObserver(() => created.resize());
    observer.observe(canvas);
    return () => {
      observer.disconnect();
      created.destroy();
      site = null;
    };
  });

  $effect(() => {
    site?.setExaggeration(exaggeration);
  });
  $effect(() => {
    site?.setSection(sectionAxis, sectionPosition);
  });

  const familyKey = (name: string) => `family.${name}` as MessageKey;

  function pickedAudit(element: PickedElement) {
    const batchLabel = element.batch
      ? String(element.batch["gml_id"] ?? element.batch["gml:id"] ?? Object.values(element.batch)[0] ?? "")
      : "";
    const context: SceneAuditContext = {
      datasetId: element.datasetId,
      licenseName: element.source.license.name,
      licenseUrl: element.source.license.url,
      elementLabel: batchLabel || element.tileUri || element.familyKey,
      coordinates: element.geographic,
      sourceUpdatedAt: element.source.source_updated_at,
      retrievedAt: element.source.retrieved_at,
      auditIndexPath: element.source.audit_index_path,
    };
    return sceneElement(context);
  }
</script>

<Dialog.Root open={!!bundle} onOpenChange={(open) => !open && app.closeScene()}>
  <Dialog.Portal>
    <Dialog.Overlay class="fixed inset-0 z-[3000] bg-ink/80" />
    <Dialog.Content class="fixed inset-3 z-[3010] grid grid-cols-[minmax(0,1fr)_340px] grid-rows-1 overflow-hidden rounded-panel border border-line bg-paper shadow-card">
      {#if bundle}
        <div class="relative min-h-0 min-w-0 overflow-hidden">
          <!-- Absolute positioning decouples the canvas layout from its drawing-buffer
               attributes; sized in flow, the attribute growth feeds back into the
               grid row and the canvas balloons past the dialog. -->
          <canvas bind:this={canvas} class="absolute inset-0 block h-full w-full"></canvas>
          <div class="absolute left-3 top-3 rounded-card bg-ink/80 px-3 py-2 text-xs text-paper">
            {bundle.handoff.local_frame.local_unit} · ENU · {bundle.handoff.local_frame.vertical_datum}
            · {i18n.t("scene.orthometric")}: {bundle.handoff.local_frame.orthometric_vertical_datum}
          </div>
          <!-- Demonstration-grade provenance stays at the point of use, not
               buried in a drawer the user may never open. -->
          <div class="absolute bottom-3 left-3 right-3 rounded-card bg-ink/80 px-3 py-2 text-[11px] leading-snug text-paper" role="note">
            {i18n.t("scene.demoNotice")}
          </div>
        </div>
        <aside class="flex min-h-0 min-w-0 flex-col gap-4 overflow-y-auto border-l border-line p-5">
          <div>
            <span class="eyebrow">{i18n.t("scene.title")}</span>
            <Dialog.Title class="mt-1 text-lg font-bold text-ink">{bundle.scene.scene_id}</Dialog.Title>
            <p class="mt-1 text-xs leading-relaxed text-muted">{bundle.scene.purpose}</p>
          </div>

          <section>
            <h3 class="text-xs font-bold uppercase tracking-wide text-muted">{i18n.t("scene.evidence")}</h3>
            <ul class="mt-2 space-y-1">
              {#each EVIDENCE_FAMILIES as name (name)}
                {@const family = bundle.handoff.evidence_families[name]}
                <li class="flex items-baseline justify-between gap-2 text-xs">
                  <span class="text-ink">{i18n.t(familyKey(name))}</span>
                  <span class="text-muted">
                    {#if family?.availability === "available"}
                      {i18n.t("availability.available")}
                      {#if familyStatus[name]}
                        · {i18n.t(`sceneStatus.${familyStatus[name]}` as MessageKey)}
                      {/if}
                    {:else if family?.availability === "not_applicable"}
                      <span title={family.reason}>{i18n.t("availability.not_applicable")}</span>
                    {:else}
                      <span title={family?.reason}>{i18n.t("availability.unresolved")}</span>
                    {/if}
                  </span>
                </li>
              {/each}
            </ul>
            {#if bundle.scene.scene_id === "sapporo-station-underground"}
              <p class="mt-2 text-[11px] leading-relaxed text-muted">{i18n.t("scene.osmReferencePlane")}</p>
            {/if}
          </section>

          <section>
            <h3 class="text-xs font-bold uppercase tracking-wide text-muted">{i18n.t("scene.exaggeration")}</h3>
            <div class="mt-1 flex items-center gap-2 text-xs text-ink">
              <input type="range" min="1" max="3" step="0.1" bind:value={exaggeration} class="w-full accent-forest" />
              <span class="w-9 text-right">{exaggeration.toFixed(1)}×</span>
            </div>
          </section>

          <section>
            <h3 class="text-xs font-bold uppercase tracking-wide text-muted">{i18n.t("scene.section")}</h3>
            <div class="mt-1 flex items-center gap-1">
              <button
                class="rounded-control border border-line px-2 py-1 text-xs"
                class:bg-forest={sectionAxis === null}
                class:text-paper={sectionAxis === null}
                onclick={() => (sectionAxis = null)}
              >
                {i18n.t("scene.sectionOff")}
              </button>
              {#each ["x", "y", "z"] as const as axis (axis)}
                <button
                  class="rounded-control border border-line px-2 py-1 text-xs uppercase"
                  class:bg-forest={sectionAxis === axis}
                  class:text-paper={sectionAxis === axis}
                  onclick={() => (sectionAxis = axis)}
                >
                  {axis}
                </button>
              {/each}
            </div>
            {#if sectionAxis}
              <input
                type="range"
                min="-400"
                max="400"
                step="1"
                bind:value={sectionPosition}
                class="mt-2 w-full accent-forest"
              />
            {/if}
          </section>

          <section class="min-h-24">
            <h3 class="text-xs font-bold uppercase tracking-wide text-muted">{i18n.t("scene.pickedElement")}</h3>
            {#if picked}
              <div class="mt-2 rounded-card border border-line bg-white p-3 text-xs">
                <div class="font-bold text-ink">{i18n.t(familyKey(picked.familyKey))}</div>
                <div class="mt-1 break-all text-muted">
                  {picked.batch ? String(picked.batch["gml_id"] ?? picked.batch["gml:id"] ?? "") : picked.tileUri}
                </div>
                <div class="mt-2">
                  <AuditTrigger record={pickedAudit(picked)}>
                    {picked.geographic[0].toFixed(6)}°, {picked.geographic[1].toFixed(6)}°, {picked.geographic[2].toFixed(1)} m
                  </AuditTrigger>
                </div>
              </div>
            {:else}
              <p class="mt-2 text-xs text-muted">{i18n.t("scene.pickHint")}</p>
            {/if}
          </section>

          <Dialog.Close class="mt-auto rounded-control border border-line bg-white px-3 py-2 text-sm font-bold text-ink">
            {i18n.t("scene.leave")}
          </Dialog.Close>
        </aside>
      {/if}
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
