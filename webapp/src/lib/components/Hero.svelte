<script lang="ts">
  import type { ModuleVM } from "../modules";

  let { vm }: { vm: ModuleVM } = $props();
</script>

<section class="hero-strip">
  <div class="hero-copy">
    <span class="hero-kicker">{vm.kicker}</span>
    <h2>{vm.heroTitle}</h2>
    <p>{vm.description}</p>
    <div class="evidence-status">
      {#each vm.chips as chip, index (index)}
        <span class="status-chip {chip.kind}"><strong>{chip.label}</strong>{#if chip.detail}{` · ${chip.detail}`}{/if}</span>
      {/each}
    </div>
  </div>
  {#if vm.formula}
    <div class="hero-formula">
      {#each vm.formula.parts as part, index (index)}
        {#if index > 0}<i>{vm.formula.ops[index - 1]}</i>{/if}
        {#if part.strong}<strong>{part.label}</strong>{:else}<span>{part.label}</span>{/if}
      {/each}
    </div>
  {/if}
</section>
