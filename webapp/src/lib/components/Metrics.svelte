<script lang="ts">
  import AuditTrigger from "./AuditTrigger.svelte";
  import { i18n } from "../i18n/i18n.svelte";
  import type { ModuleVM } from "../modules";

  let { vm }: { vm: ModuleVM } = $props();
</script>

<section class="metrics" aria-label={i18n.t("aria.keyMetrics")}>
  {#each vm.metrics as item, index (index)}
    <article class="metric" style={`--metric-color:${item.color}`}>
      <div class="metric-label"><span>{item.label}</span><i></i></div>
      <div class="metric-value">
        <AuditTrigger record={item.audit}>
          {item.value}{i18n.lang === "en" && item.unit ? " " : ""}<small>{item.unit}</small>
        </AuditTrigger>
      </div>
      <div class="metric-note"><AuditTrigger record={item.audit}>{item.note}</AuditTrigger></div>
    </article>
  {/each}
</section>
