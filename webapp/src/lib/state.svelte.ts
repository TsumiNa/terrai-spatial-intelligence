import type { AuditRecord, ModuleName } from "./audit";
import type { Bootstrap, Feature } from "./api/types";
import { MODULES, normalizeView } from "./modules";
import { i18n } from "./i18n/i18n.svelte";

export type BasemapKey = "standard" | "photo" | "hillshade" | "slope";
export const BASEMAP_KEYS: BasemapKey[] = ["standard", "photo", "hillshade", "slope"];

function isModule(value: unknown): value is ModuleName {
  return typeof value === "string" && (MODULES as string[]).includes(value);
}

function isBasemap(value: unknown): value is BasemapKey {
  return typeof value === "string" && (BASEMAP_KEYS as string[]).includes(value);
}

function initialParams() {
  if (typeof window === "undefined") return { module: "overview" as ModuleName, view: null, basemap: "standard" as BasemapKey };
  const params = new URLSearchParams(window.location.search);
  const module = isModule(params.get("module")) ? (params.get("module") as ModuleName) : "overview";
  const view = params.get("view");
  const basemap = isBasemap(params.get("basemap")) ? (params.get("basemap") as BasemapKey) : "standard";
  return { module, view, basemap };
}

const initial = initialParams();

let module = $state<ModuleName>(initial.module);
let view = $state<string | null>(initial.view);
let basemap = $state<BasemapKey>(initial.basemap);
let data = $state<Bootstrap | null>(null);
let loadError = $state<string | null>(null);
let auditRecord = $state<AuditRecord | null>(null);
let queueSelection = $state.raw<{ feature: Feature; tick: number } | null>(null);

export const app = {
  get module() {
    return module;
  },
  get view() {
    return view;
  },
  get basemap() {
    return basemap;
  },
  get data() {
    return data;
  },
  get loadError() {
    return loadError;
  },
  get auditRecord() {
    return auditRecord;
  },
  get queueSelection() {
    return queueSelection;
  },

  selectModule(next: ModuleName) {
    module = next;
    view = null; // the module decides its default view, as the old shell did
    queueSelection = null;
    this.closeAudit();
  },
  selectView(next: string) {
    view = normalizeView(module, next);
    queueSelection = null;
    this.closeAudit();
  },
  selectQueueItem(feature: Feature) {
    queueSelection = { feature, tick: (queueSelection?.tick ?? 0) + 1 };
  },
  selectBasemap(next: BasemapKey) {
    basemap = next;
  },
  selectLanguage(lang: typeof i18n.lang) {
    if (lang === i18n.lang) return;
    i18n.lang = lang;
    // Parity with the old shell: switching language re-rendered the module
    // and closed the audit drawer.
    this.closeAudit();
  },
  setData(payload: Bootstrap) {
    data = payload;
    loadError = null;
  },
  setLoadError(message: string) {
    loadError = message;
  },
  openAudit(record: AuditRecord) {
    auditRecord = record;
  },
  closeAudit() {
    auditRecord = null;
  },

  /** Keep module/view/lang shareable, as the old `syncUrl` did. */
  syncUrl(activeView: string) {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    url.searchParams.set("module", module);
    url.searchParams.set("view", activeView);
    url.searchParams.set("lang", i18n.lang);
    window.history.replaceState({}, "", url);
  },
};
