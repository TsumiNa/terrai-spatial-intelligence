<script lang="ts">
  import type { ModuleName } from "../audit";
  import { i18n, type MessageKey } from "../i18n/i18n.svelte";
  import { app } from "../state.svelte";

  interface NavEntry {
    module: ModuleName;
    icon: string;
    labelKey: MessageKey;
    badge?: { kind: "b" | "em"; text: string };
  }

  interface NavGroup {
    labelKey: MessageKey;
    entries: NavEntry[];
  }

  // Badge counts are the same static values the previous exhibition shipped.
  const groups: NavGroup[] = [
    {
      labelKey: "nav.groupDecisions",
      entries: [
        { module: "overview", icon: "⌂", labelKey: "nav.overview" },
        { module: "joint", icon: "✣", labelKey: "nav.joint", badge: { kind: "b", text: "30" } },
        { module: "development", icon: "▧", labelKey: "nav.development", badge: { kind: "b", text: "21" } },
      ],
    },
    {
      labelKey: "nav.groupAnalysis",
      entries: [
        { module: "slope", icon: "△", labelKey: "nav.slope", badge: { kind: "em", text: "2,128" } },
        { module: "roads", icon: "⌁", labelKey: "nav.roads", badge: { kind: "em", text: "272" } },
        { module: "facilities", icon: "⌘", labelKey: "nav.facilities", badge: { kind: "em", text: "2" } },
        { module: "solar", icon: "☼", labelKey: "nav.solar", badge: { kind: "em", text: "70" } },
        { module: "underground", icon: "⏚", labelKey: "nav.underground", badge: { kind: "b", text: "3D" } },
      ],
    },
    {
      labelKey: "nav.groupTrust",
      entries: [{ module: "evidence", icon: "◎", labelKey: "nav.evidence", badge: { kind: "b", text: "API" } }],
    },
  ];
</script>

<aside class="sidebar">
  <div class="brand">
    <div class="brand-mark">T</div>
    <div><strong>TerrAI</strong><span>Spatial Intelligence</span></div>
  </div>

  <nav class="nav" aria-label={i18n.t("nav.aria")}>
    {#each groups as group (group.labelKey)}
      <p class="nav-label">{i18n.t(group.labelKey)}</p>
      {#each group.entries as entry (entry.module)}
        <button
          class="nav-item"
          class:active={app.module === entry.module}
          data-module={entry.module}
          onclick={() => app.selectModule(entry.module)}
        >
          <span class="nav-icon">{entry.icon}</span><span>{i18n.t(entry.labelKey)}</span>
          {#if entry.badge?.kind === "b"}<b>{entry.badge.text}</b>{:else if entry.badge}<em>{entry.badge.text}</em>{/if}
        </button>
      {/each}
    {/each}
  </nav>

  <div class="foundation-card">
    <div class="foundation-title"><span class="pulse"></span><span>{i18n.t("foundation.serviceOk")}</span></div>
    <div class="foundation-row">
      <span>{i18n.t("foundation.datasets")}</span>
      <strong>{app.data ? `${app.data.meta.datasets_ready} / ${app.data.meta.datasets_total}` : "—"}</strong>
    </div>
    <div class="foundation-row">
      <span>{i18n.t("foundation.sources")}</span>
      <strong>{app.data ? i18n.t("foundation.sourceGroups", { n: app.data.meta.source_groups }) : "—"}</strong>
    </div>
    <div class="foundation-row"><span>{i18n.t("foundation.audit")}</span><strong>{i18n.t("foundation.auditValue")}</strong></div>
    <small>{i18n.t("foundation.hint")}</small>
  </div>
</aside>
