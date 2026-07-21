<script lang="ts">
  import type { Snippet } from "svelte";

  import type { AuditRecord } from "../audit";
  import { i18n } from "../i18n/i18n.svelte";
  import { app } from "../state.svelte";

  let props: { record: AuditRecord; class?: string; style?: string; children: Snippet } = $props();
</script>

<button
  type="button"
  class={`audit-trigger ${props.class ?? ""}`}
  style={props.style}
  aria-label={i18n.t("audit.openLabel")}
  onclick={(event) => {
    event.stopPropagation();
    app.openAudit(props.record);
  }}
>
  {@render props.children()}
</button>
