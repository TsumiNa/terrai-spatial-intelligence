<script lang="ts">
  import { Dialog } from "bits-ui";
  import { text, TYPE_LABELS } from "../audit";
  import { i18n } from "../i18n/i18n.svelte";
  import { app } from "../state.svelte";

  const record = $derived(app.auditRecord);

  // Bits UI owns the focus trap, the return of focus to whatever opened the
  // drawer, the escape and click-outside handling, the scroll lock, and the
  // dialog semantics. The hand-rolled versions of all of that are gone: they
  // were where the four accessibility defects lived.
  function onOpenChange(open: boolean) {
    if (!open) app.closeAudit();
  }
</script>

<Dialog.Root open={!!record} {onOpenChange}>
  <Dialog.Portal>
    <Dialog.Overlay class="audit-backdrop open" />
    <Dialog.Content class="audit-drawer open">
      <div class="audit-head">
        <div>
          <span class="eyebrow">{i18n.t("audit.eyebrow")}</span>
          <!-- Rendered as a real <h2>: the default is a div with role="heading",
               which the stylesheet's `.audit-head h2` rule does not match, and the
               title silently dropped from 20px to 16px. -->
          <Dialog.Title id="audit-title">
            {#snippet child({ props })}
              <h2 {...props}>{record ? text(record.title, i18n.lang) : "—"}</h2>
            {/snippet}
          </Dialog.Title>
        </div>
        <Dialog.Close class="audit-close" aria-label={i18n.t("audit.close")}>×</Dialog.Close>
      </div>
      <div class="audit-body">
        <span class="audit-type {record?.kind ?? ''}">
          {record ? text(TYPE_LABELS[record.kind], i18n.lang) : "—"}
        </span>
        <div class="audit-value">{record ? text(record.value, i18n.lang) : "—"}</div>
        <div class="audit-sections">
          {#if record}
            {#each record.sections as item, index (index)}
              <section class="audit-section">
                <span>{text(item.label, i18n.lang)}</span>
                <p>
                  {#if item.url}
                    <a href={item.url} target="_blank" rel="noopener noreferrer">
                      {text(item.value, i18n.lang)}
                    </a>
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
    </Dialog.Content>
  </Dialog.Portal>
</Dialog.Root>
