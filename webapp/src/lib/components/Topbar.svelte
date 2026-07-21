<script lang="ts">
  import { i18n, LANGUAGES, type Language } from "../i18n/i18n.svelte";
  import { app } from "../state.svelte";
  import type { ModuleVM } from "../modules";

  let { vm }: { vm: ModuleVM | null } = $props();

  const languageLabels: Record<Language, string> = { zh: "中", ja: "日", en: "EN" };
</script>

<header class="topbar">
  <div>
    <span class="eyebrow">{vm?.eyebrow ?? ""}</span>
    <h1>{vm?.title ?? ""}</h1>
  </div>
  <div class="top-actions">
    <div class="language-switcher" role="group" aria-label="Language">
      {#each LANGUAGES as lang (lang)}
        <button
          class="language-button"
          class:active={i18n.lang === lang}
          aria-pressed={i18n.lang === lang}
          {lang}
          onclick={() => app.selectLanguage(lang)}
        >
          {languageLabels[lang]}
        </button>
      {/each}
    </div>
    <span class="data-date">{i18n.t("topbar.snapshot")}</span>
    <div class="region-pill">{vm?.region === "mobara" ? i18n.t("region.mobara") : i18n.t("region.yokohama")}</div>
  </div>
</header>
