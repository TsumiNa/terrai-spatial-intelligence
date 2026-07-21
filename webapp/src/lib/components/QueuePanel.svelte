<script lang="ts">
  import AuditTrigger from "./AuditTrigger.svelte";
  import { app } from "../state.svelte";
  import type { ModuleVM, QueueItemVM } from "../modules";

  let { vm }: { vm: ModuleVM } = $props();

  function open(item: QueueItemVM, event: Event) {
    if ((event.target as HTMLElement).closest(".audit-trigger")) return;
    app.selectQueueItem(item.feature);
  }
</script>

<aside class="insight-panel">
  <div class="panel-head">
    <div>
      <span class="eyebrow">{vm.queueEyebrow}</span>
      <h3>{vm.queueTitle}</h3>
      <p>{vm.queueExplanation}</p>
    </div>
    <span class="queue-count">{vm.queueCount}</span>
  </div>
  <div class="queue">
    {#each vm.queueItems as item, index (index)}
      <div
        class="queue-item"
        role="button"
        tabindex="0"
        onclick={(event) => open(item, event)}
        onkeydown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            open(item, event);
          }
        }}
      >
        <span class="rank" style={`--rank-color:${item.color}`}>{index + 1}</span>
        <span class="queue-main">
          <strong>{item.title}</strong>
          <AuditTrigger record={item.detailAudit} class="queue-detail">{item.detail}</AuditTrigger>
        </span>
        <AuditTrigger record={item.scoreAudit} class="score" style={`--score-color:${item.color}`}>
          {item.score}<small>{item.scoreLabel}</small>
        </AuditTrigger>
      </div>
    {/each}
  </div>
  <div class="method-card"><strong>{vm.methodTitle}</strong><br />{vm.methodBody}</div>
</aside>
