<script lang="ts">
  import { text, TYPE_LABELS } from "../audit";
  import { i18n } from "../i18n/i18n.svelte";
  import { app } from "../state.svelte";

  const record = $derived(app.auditRecord);
  let closeButton = $state<HTMLButtonElement | null>(null);
  let returnFocus: HTMLElement | null = null;

  $effect(() => {
    if (record) {
      const active = document.activeElement;
      if (active instanceof HTMLElement && !closeButton?.contains(active)) returnFocus = active;
      closeButton?.focus({ preventScroll: true });
      document.body.classList.add("audit-open");
    } else {
      document.body.classList.remove("audit-open");
      if (returnFocus?.isConnected) returnFocus.focus({ preventScroll: true });
      returnFocus = null;
    }
  });
</script>

<svelte:window
  onkeydown={(event) => {
    if (event.key === "Escape" && record) app.closeAudit();
  }}
/>

<div
  class="audit-backdrop"
  class:open={record}
  onclick={() => app.closeAudit()}
  role="presentation"
></div>
<aside class="audit-drawer" class:open={record} aria-hidden={!record} aria-labelledby="audit-title">
  <div class="audit-head">
    <div>
      <span class="eyebrow">{i18n.t("audit.eyebrow")}</span>
      <h2 id="audit-title">{record ? text(record.title, i18n.lang) : "—"}</h2>
    </div>
    <button
      class="audit-close"
      type="button"
      aria-label={i18n.t("audit.close")}
      bind:this={closeButton}
      onclick={() => app.closeAudit()}
    >
      ×
    </button>
  </div>
  <div class="audit-body">
    <span class="audit-type {record?.kind ?? ''}">{record ? text(TYPE_LABELS[record.kind], i18n.lang) : "—"}</span>
    <div class="audit-value">{record ? text(record.value, i18n.lang) : "—"}</div>
    <div class="audit-sections">
      {#if record}
        {#each record.sections as item, index (index)}
          <section class="audit-section">
            <span>{text(item.label, i18n.lang)}</span>
            <p>
              {#if item.url}
                <a href={item.url} target="_blank" rel="noopener noreferrer">{text(item.value, i18n.lang)}</a>
              {:else}
                {text(item.value, i18n.lang)}
              {/if}
            </p>
          </section>
        {/each}
      {/if}
    </div>
    <div class="audit-caveat">
      <strong>{i18n.t("audit.howToRead")}</strong>
      <p>{record ? text(record.caveat, i18n.lang) : ""}</p>
    </div>
  </div>
</aside>
