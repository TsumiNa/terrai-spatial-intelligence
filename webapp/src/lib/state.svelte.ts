import type { AuditRecord, ModuleName } from "./audit";
import type { Bootstrap, Feature } from "./api/types";
import type { UndergroundAuditIndex, UndergroundManifest, UndergroundState } from "./underground";
import type { SceneBundle } from "./scene/catalog";
import { MODULES, normalizeView } from "./modules";
import { i18n } from "./i18n/i18n.svelte";

export type BasemapKey = "standard" | "photo" | "hillshade";
export const BASEMAP_KEYS: BasemapKey[] = ["standard", "photo", "hillshade"];

function isModule(value: unknown): value is ModuleName {
  return typeof value === "string" && (MODULES as string[]).includes(value);
}

function isBasemap(value: unknown): value is BasemapKey {
  return typeof value === "string" && (BASEMAP_KEYS as string[]).includes(value);
}

function initialParams() {
  if (typeof window === "undefined") return { module: "overview" as ModuleName, view: null, basemap: "standard" as BasemapKey, twoAndHalfD: false };
  const params = new URLSearchParams(window.location.search);
  const module = isModule(params.get("module")) ? (params.get("module") as ModuleName) : "overview";
  const view = params.get("view");
  const basemap = isBasemap(params.get("basemap")) ? (params.get("basemap") as BasemapKey) : "standard";
  const twoAndHalfD = params.get("tilt") === "1";
  return { module, view, basemap, twoAndHalfD };
}

const initial = initialParams();

let module = $state<ModuleName>(initial.module);
let view = $state<string | null>(initial.view);
let basemap = $state<BasemapKey>(initial.basemap);
// The 2.5D view toggle: perspective on any basemap, plus the 3D DEM surface on
// imagery/relief. Decoupled from the basemap (basemap-view-modes).
let twoAndHalfD = $state<boolean>(initial.twoAndHalfD);
let data = $state<Bootstrap | null>(null);
let loadError = $state<string | null>(null);
// The merged building tiles cover only mainland Kanto; true when the viewport
// (at building zoom) lies wholly outside that footprint and the map has fallen
// back to GSI's building texture. Drives the on-map "out of service" badge.
let buildingsOutOfService = $state<boolean>(false);
let auditRecord = $state<AuditRecord | null>(null);
let queueSelection = $state.raw<{ feature: Feature; tick: number } | null>(null);

let underground = $state.raw<UndergroundState>({ status: "unknown", manifest: null, auditIndex: null });
// Foundation overlay visibility is explicit application state: it survives
// module, view, region and language switches, deliberately.
let foundationLayers = $state<string[]>([]);
let sceneBundle = $state.raw<SceneBundle | null>(null);

export type { UndergroundState } from "./underground";

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
  get twoAndHalfD() {
    return twoAndHalfD;
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
  get underground() {
    return underground;
  },
  get sceneBundle() {
    return sceneBundle;
  },
  get foundationLayers() {
    return foundationLayers;
  },
  get buildingsOutOfService() {
    return buildingsOutOfService;
  },
  setBuildingsOutOfService(next: boolean) {
    buildingsOutOfService = next;
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
  toggle25D() {
    twoAndHalfD = !twoAndHalfD;
    // Keep the `?tilt=1` deep link in sync with the toggle, since initialParams
    // reads it back on load.
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    if (twoAndHalfD) url.searchParams.set("tilt", "1");
    else url.searchParams.delete("tilt");
    window.history.replaceState({}, "", url);
  },
  toggleFoundationLayer(key: string) {
    foundationLayers = foundationLayers.includes(key)
      ? foundationLayers.filter((item) => item !== key)
      : [...foundationLayers, key];
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
  openScene(bundle: SceneBundle) {
    sceneBundle = bundle;
    this.closeAudit();
  },
  closeScene() {
    sceneBundle = null;
  },
  setUndergroundLoading() {
    underground = { status: "loading", manifest: null, auditIndex: null };
  },
  setUndergroundReady(manifest: UndergroundManifest, auditIndex: UndergroundAuditIndex) {
    underground = { status: "ready", manifest, auditIndex };
  },
  setUndergroundUnavailable(status: "unavailable" | "error" = "unavailable") {
    underground = { status, manifest: null, auditIndex: null };
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
