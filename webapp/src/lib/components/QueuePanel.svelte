<script lang="ts">
  import AuditTrigger from "./AuditTrigger.svelte";
  import type { ModuleVM } from "../modules";

  let { vm }: { vm: ModuleVM } = $props();
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
      <div class="queue-item">
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
