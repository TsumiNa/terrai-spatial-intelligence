<script lang="ts">
  import AuditTrigger from "./AuditTrigger.svelte";
  import type { AuditRecord } from "../audit";

  let {
    eyebrow,
    title,
    fields,
  }: {
    eyebrow: string;
    title: string;
    fields: { label: string; text: string | number; record: AuditRecord }[];
  } = $props();
</script>

<div class="popup-eyebrow">{eyebrow}</div>
<div class="popup-title">{title}</div>
<div class="popup-grid">
  {#each fields as item, index (index)}
    <span>{item.label}<AuditTrigger record={item.record}>{item.text}</AuditTrigger></span>
  {/each}
</div>
