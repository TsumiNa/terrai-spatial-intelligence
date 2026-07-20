const PATHS = {
  buildings: "data/yokohama/building_risk.geojson",
  buildingSummary: "data/yokohama/building_summary.json",
  roads: "data/yokohama/road_priority.geojson",
  roadSummary: "data/yokohama/road_summary.json",
  solar: "data/mobara/site_cells.geojson",
  solarContext: "data/mobara/context.geojson",
  solarSummary: "data/mobara/solar_summary.json",
  hubs: "data/joint/resilience_hubs.geojson",
  corridors: "data/joint/compound_corridors.geojson",
  delivery: "data/joint/solar_delivery_cells.geojson",
  jointSummary: "data/joint/joint_summary.json",
  gridScreen: "data/mobara/tepco_grid_screen.json",
  facilities: "data/yokohama/official_facility_resilience.geojson",
  embeddingEvidence: "data/google/satellite_embedding/embedding_evidence.geojson",
  embeddingSummary: "data/google/satellite_embedding/summary.json",
  yokohamaZones: "data/evidence/yokohama_zones.geojson",
  mobaraZones: "data/evidence/mobara_zones.geojson",
  multiscaleSummary: "data/evidence/multiscale_summary.json"
};

const REGIONS = {
  yokohama: {
    label: "横滨 · 保土谷区",
    center: [35.4465, 139.5885],
    zoom: 17,
    bounds: [[35.4426, 139.5835], [35.4504, 139.5935]],
    tiles: {
      standard: "data/tiles/yokohama/{z}/{x}-{y}.png",
      photo: "data/tiles/yokohama/photo/{z}/{x}-{y}.jpg",
      hillshade: "data/tiles/yokohama/hillshade/{z}/{x}-{y}.png",
      slope: "data/tiles/yokohama/slope/{z}/{x}-{y}.png"
    }
  },
  mobara: {
    label: "千叶 · 茂原市",
    center: [35.445, 140.2835],
    zoom: 16,
    bounds: [[35.4387, 140.2757], [35.4513, 140.2913]],
    tiles: {
      standard: "data/tiles/mobara/{z}/{x}-{y}.png",
      photo: "data/tiles/mobara/photo/{z}/{x}-{y}.jpg",
      hillshade: "data/tiles/mobara/hillshade/{z}/{x}-{y}.png",
      slope: "data/tiles/mobara/slope/{z}/{x}-{y}.png"
    }
  }
};

const BASEMAPS = {
  standard: { label: "标准", title: "GSI 标准地图", maxNativeZoom: 15 },
  photo: { label: "影像", title: "GSI 全国最新正射影像 / 卫星影像", maxNativeZoom: 17 },
  hillshade: { label: "起伏", title: "DEM5/10m 阴影起伏图", maxNativeZoom: 16 },
  slope: { label: "坡度", title: "DEM5/10m 倾斜量图", maxNativeZoom: 15 }
};

const colors = {
  red: "#d75b4c",
  amber: "#e2a43c",
  green: "#1f7a58",
  lime: "#8fc85a",
  blue: "#397ca3",
  forest: "#164d3b",
  gray: "#a9b5af"
};

const I18N = window.TerrAI_I18N;
const AUDIT = window.TerrAI_AUDIT;
const LANGS = ["zh", "ja", "en"];

const state = {
  module: "overview",
  view: "hubs",
  region: "yokohama",
  basemap: "standard",
  lang: "zh",
  data: {},
  tileLayer: null,
  vectorLayers: [],
  queueLayers: [],
  auditRecords: new Map(),
  auditCounter: 0,
  auditSourceProps: null,
  auditReturnFocus: null,
  auditCloseTimer: null
};

const map = L.map("map", { zoomControl: false, preferCanvas: true, attributionControl: true });
L.control.zoom({ position: "bottomright" }).addTo(map);

function fetchJson(path) {
  return fetch(path).then(response => {
    if (!response.ok) throw new Error(`${path}: ${response.status}`);
    return response.json();
  });
}

function t(value) {
  return I18N.translate(value, state.lang);
}

function auditText(value) {
  return AUDIT.text(value, state.lang);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"]/g, character => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" })[character]);
}

function translateMarkup(markup) {
  const template = document.createElement("template");
  template.innerHTML = markup;
  const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const original = node.textContent;
    if (original.trim()) node.textContent = t(original);
  }
  return template.innerHTML;
}

function translateElementText(element) {
  if (!element) return;
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  const nodes = [];
  let node;
  while ((node = walker.nextNode())) nodes.push(node);
  nodes.forEach(textNode => {
    if (textNode.textContent.trim()) textNode.textContent = t(textNode.textContent);
  });
}

function applyStaticTranslations() {
  document.documentElement.lang = state.lang === "zh" ? "zh-CN" : state.lang;
  document.querySelectorAll("[data-i18n]").forEach(element => {
    element.textContent = t(element.dataset.i18n);
  });
  document.querySelectorAll("[data-i18n-aria]").forEach(element => {
    element.setAttribute("aria-label", t(element.dataset.i18nAria));
  });
  document.querySelectorAll(".language-button").forEach(button => {
    const active = button.dataset.lang === state.lang;
    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });
}

function registerAudit(record) {
  const id = `audit-${++state.auditCounter}`;
  state.auditRecords.set(id, record);
  return id;
}

function auditTrigger(content, record, className = "") {
  const id = registerAudit(record);
  return `<button type="button" class="audit-trigger ${className}" data-audit-id="${id}" aria-label="${escapeHtml(t("打开可审计详情"))}">${content}</button>`;
}

function openAudit(record, returnFocus = document.activeElement) {
  if (!record) return;
  const drawer = document.getElementById("audit-drawer");
  const backdrop = document.getElementById("audit-backdrop");
  if (state.auditCloseTimer) window.clearTimeout(state.auditCloseTimer);
  state.auditReturnFocus = returnFocus instanceof HTMLElement ? returnFocus : null;
  document.getElementById("audit-title").textContent = t(auditText(record.title));
  const type = document.getElementById("audit-type");
  type.className = `audit-type ${record.kind}`;
  type.textContent = auditText(AUDIT.TYPE_LABELS[record.kind]);
  document.getElementById("audit-value").textContent = t(auditText(record.value));
  document.getElementById("audit-sections").innerHTML = record.sections.map(item => {
    const value = escapeHtml(t(auditText(item.value)));
    const rendered = item.url ? `<a href="${escapeHtml(item.url)}" target="_blank" rel="noreferrer">${value}</a>` : value;
    return `<section class="audit-section"><span>${escapeHtml(auditText(item.label))}</span><p>${rendered}</p></section>`;
  }).join("");
  document.getElementById("audit-caveat").textContent = t(auditText(record.caveat));
  backdrop.hidden = false;
  requestAnimationFrame(() => {
    drawer.classList.add("open");
    backdrop.classList.add("open");
    document.getElementById("audit-close").focus({ preventScroll: true });
  });
  drawer.setAttribute("aria-hidden", "false");
  document.body.classList.add("audit-open");
}

function closeAudit() {
  const drawer = document.getElementById("audit-drawer");
  const backdrop = document.getElementById("audit-backdrop");
  if (drawer.contains(document.activeElement)) {
    if (state.auditReturnFocus?.isConnected) state.auditReturnFocus.focus({ preventScroll: true });
    else document.activeElement.blur();
  }
  drawer.classList.remove("open");
  backdrop.classList.remove("open");
  drawer.setAttribute("aria-hidden", "true");
  document.body.classList.remove("audit-open");
  state.auditReturnFocus = null;
  state.auditCloseTimer = window.setTimeout(() => { backdrop.hidden = true; }, 220);
}

function clearMap() {
  state.vectorLayers.forEach(layer => map.removeLayer(layer));
  state.vectorLayers = [];
  state.queueLayers = [];
  state.auditRecords = new Map();
  state.auditCounter = 0;
  closeAudit();
}

function setArchitectureMode(active) {
  document.getElementById("map").hidden = active;
  document.getElementById("architecture-board").hidden = !active;
  document.querySelector(".map-toolbar").hidden = active;
  document.getElementById("map-note").hidden = active;
  document.querySelector(".map-card").classList.toggle("concept-mode", active);
}

function useBasemap(basemapKey, resetView = false) {
  state.basemap = basemapKey;
  const region = REGIONS[state.region];
  if (state.tileLayer) map.removeLayer(state.tileLayer);
  state.tileLayer = L.tileLayer(region.tiles[basemapKey], {
    minZoom: 15,
    maxZoom: 19,
    maxNativeZoom: BASEMAPS[basemapKey].maxNativeZoom,
    bounds: region.bounds,
    noWrap: true,
    attribution: `${t(BASEMAPS[basemapKey].title)} · <a href="https://maps.gsi.go.jp/development/ichiran.html">GSI</a>`
  }).addTo(map);
  state.tileLayer.bringToBack();
  if (resetView) map.setView(region.center, region.zoom, { animate: false });
  renderBasemapSwitcher();
}

function renderBasemapSwitcher() {
  const root = document.getElementById("basemap-switcher");
  root.innerHTML = Object.entries(BASEMAPS).map(([key, item]) =>
    `<button class="basemap-button ${key === state.basemap ? "active" : ""}" data-basemap="${key}" title="${escapeHtml(t(item.title))}">${escapeHtml(t(item.label))}</button>`
  ).join("");
  root.querySelectorAll("button").forEach(button => button.addEventListener("click", () => useBasemap(button.dataset.basemap)));
}

function useRegion(regionKey) {
  state.region = regionKey;
  const region = REGIONS[regionKey];
  useBasemap(state.basemap, true);
  document.getElementById("region-pill").innerHTML = `${escapeHtml(t(region.label))} <span>⌄</span>`;
}

function metric(label, value, unit, note, color, auditContext = {}) {
  const record = AUDIT.metric(label, value, unit, note, auditContext);
  const translatedUnit = t(unit || "");
  const valueMarkup = `${escapeHtml(value)}${state.lang === "en" && translatedUnit ? " " : ""}<small>${escapeHtml(translatedUnit)}</small>`;
  return `<article class="metric" style="--metric-color:${color}">
    <div class="metric-label"><span>${escapeHtml(t(label))}</span><i></i></div>
    <div class="metric-value">${auditTrigger(valueMarkup, record)}</div>
    <div class="metric-note">${auditTrigger(escapeHtml(t(note)), record)}</div>
  </article>`;
}

function setMetrics(items) {
  document.getElementById("metrics").innerHTML = items.join("");
}

function legend(items) {
  document.getElementById("map-legend").innerHTML = items.map(item =>
    `<span class="legend-item"><i class="legend-dot" style="background:${item[1]}"></i>${escapeHtml(t(item[0]))}</span>`
  ).join("");
}

function setEvidenceStatus(items = []) {
  document.getElementById("evidence-status").innerHTML = items.map(item =>
    `<span class="status-chip ${item[0]}"><strong>${escapeHtml(t(item[1]))}</strong>${item[2] ? ` · ${escapeHtml(t(item[2]))}` : ""}</span>`
  ).join("");
}

function setTabs(tabs, current) {
  const root = document.getElementById("view-tabs");
  root.innerHTML = tabs.map(tab =>
    `<button class="view-tab ${tab[0] === current ? "active" : ""}" data-view="${tab[0]}">${escapeHtml(t(tab[1]))}</button>`
  ).join("");
  root.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
    state.view = button.dataset.view;
    renderModule(state.module, true);
  }));
}

function setHeader(eyebrow, title, kicker, heroTitle, description, formula = "") {
  document.getElementById("eyebrow").textContent = t(eyebrow);
  document.getElementById("page-title").textContent = t(title);
  document.getElementById("hero-kicker").textContent = kicker;
  document.getElementById("hero-title").textContent = t(heroTitle);
  document.getElementById("hero-description").textContent = t(description);
  const formulaEl = document.getElementById("hero-formula");
  formulaEl.style.display = formula ? "flex" : "none";
  if (formula) formulaEl.innerHTML = translateMarkup(formula);
  setEvidenceStatus([["observed", "公开观测"], ["proxy", "PoC 推断"]]);
}

function setQueueHeading(eyebrow, title, count) {
  document.getElementById("queue-eyebrow").textContent = eyebrow;
  document.getElementById("queue-title").textContent = t(title);
  document.getElementById("queue-count").textContent = count;
}

function queue(items, formatter) {
  const root = document.getElementById("queue");
  root.innerHTML = items.slice(0, 18).map((feature, index) => {
    const item = formatter(feature.properties, index);
    const scoreRecord = AUDIT.queueScore(state.module, state.view, item.score, feature.properties);
    const scoreId = registerAudit(scoreRecord);
    const detailRecord = AUDIT.field("队列详情", item.detail, feature.properties);
    const detailId = registerAudit(detailRecord);
    return `<div class="queue-item" role="button" tabindex="0" data-index="${index}">
      <span class="rank" style="--rank-color:${item.color}">${index + 1}</span>
      <span class="queue-main"><strong>${escapeHtml(t(item.title))}</strong><span class="queue-detail audit-trigger" role="button" tabindex="0" data-audit-id="${detailId}">${escapeHtml(t(item.detail))}</span></span>
      <span class="score audit-trigger" role="button" tabindex="0" data-audit-id="${scoreId}" style="--score-color:${item.color}">${escapeHtml(item.score)}<small>${escapeHtml(t(item.label || "SCORE"))}</small></span>
    </div>`;
  }).join("");
  const openQueueItem = (button, event) => {
    if (event.target.closest("[data-audit-id]")) return;
    const layer = state.queueLayers[Number(button.dataset.index)];
    if (!layer) return;
    if (layer.getBounds) map.fitBounds(layer.getBounds(), { padding: [80, 80], maxZoom: 19 });
    else if (layer.getLatLng) map.setView(layer.getLatLng(), 19);
    layer.openPopup();
  };
  root.querySelectorAll(".queue-item").forEach(button => {
    button.addEventListener("click", event => openQueueItem(button, event));
    button.addEventListener("keydown", event => {
      if ((event.key === "Enter" || event.key === " ") && !event.target.closest("[data-audit-id]")) {
        event.preventDefault();
        openQueueItem(button, event);
      }
    });
  });
}

function layerForFeatures(features, options, bindPopup = () => "") {
  const layer = L.geoJSON({ type: "FeatureCollection", features }, {
    style: options.style,
    pointToLayer: options.pointToLayer,
    onEachFeature(feature, featureLayer) {
      state.auditSourceProps = feature.properties;
      featureLayer.bindPopup(bindPopup(feature.properties));
      state.auditSourceProps = null;
    }
  }).addTo(map);
  state.vectorLayers.push(layer);
  const byId = new Map();
  layer.eachLayer(featureLayer => byId.set(String(featureLayer.feature.id ?? featureLayer.feature.properties.osm_id ?? featureLayer.feature.properties.cell_id), featureLayer));
  return { layer, byId };
}

function imageOverlay(path, bounds, opacity = .78) {
  const layer = L.imageOverlay(path, bounds, { opacity, interactive: false }).addTo(map);
  state.vectorLayers.push(layer);
  return layer;
}

function popup(title, eyebrow, fields) {
  const props = state.auditSourceProps || {};
  return `<div class="popup-eyebrow">${escapeHtml(t(eyebrow))}</div><div class="popup-title">${escapeHtml(t(title))}</div>
    <div class="popup-grid">${fields.map(field => {
      const record = AUDIT.field(field[0], field[1], props);
      return `<span>${escapeHtml(t(field[0]))}${auditTrigger(escapeHtml(t(field[1])), record)}</span>`;
    }).join("")}</div>`;
}

function riskColor(band) {
  return band === "high" ? colors.red : band === "medium" ? colors.amber : colors.green;
}

function renderArchitecture() {
  document.getElementById("region-pill").innerHTML = "FL <span>→</span> SL <span>→</span> AL";
  setHeader(
    "概念架构", "从数据基础设施到可扩展应用出口", "FACTOR OF CONCEPT · FL → SL → AL",
    "让观测、合成与应用决策各归其位",
    "FL 保留多尺度现实证据和真实缺测；SL 只在验证通过后补值并披露不确定性；AL 把合格证据转成场景行动。",
    "<span>Foundation Data</span><i>→</i><span>Synthetic Data</span><i>→</i><strong>Applications</strong>"
  );
  setEvidenceStatus([
    ["observed", "FL", "当前 Demo 已接入"],
    ["pending", "SL", "地表补值尚未接入"],
    ["proxy", "AL", "启发式应用已接入"]
  ]);
  setMetrics([
    metric("FL 实际来源", 6, "组", "公开 / 官方观测与表征", colors.green),
    metric("地表 SL 补值", 0, "项", "概念已定义，尚未接入", colors.blue),
    metric("AL 核心出口", 3, "类", "坡地 · 道路 · 光伏", colors.amber),
    metric("极稀疏校准证据", 91.0, "%", "geo_pfn N=3 · 地下实验", colors.forest)
  ]);

  setQueueHeading("LAYER READINESS", "当前分层成熟度", 3);
  document.getElementById("queue").innerHTML = `<div class="concept-status-list">
    <article class="concept-status" style="--status-color:${colors.green}"><span>FL · LIVE</span><strong>${escapeHtml(t("开放数据管线已运行"))}</strong><p>${escapeHtml(t("已缓存多尺度观测、来源和许可；客户私有数据尚未进入。"))}</p></article>
    <article class="concept-status" style="--status-color:${colors.blue}"><span>SL · CONCEPT</span><strong>${escapeHtml(t("稀疏预测边界已定义"))}</strong><p>${escapeHtml(t("geo_pfn 提供地下机制证据；当前横滨与茂原没有 synthetic 补值。"))}</p></article>
    <article class="concept-status" style="--status-color:${colors.amber}"><span>AL · DEMO</span><strong>${escapeHtml(t("三个核心应用出口已运行"))}</strong><p>${escapeHtml(t("当前分数是透明规则与代理，不是 SL 模型预测。"))}</p></article>
  </div>`;
  document.getElementById("method-card").innerHTML = `<strong>${escapeHtml(t("本次重构边界"))}</strong><br>${escapeHtml(t("只建立 FL → SL → AL 的概念分层；schema、API、数据库、调度和模型服务留给 Factor of Develop。"))}`;
}

function renderOverview() {
  const view = ["urban", "renewable"].includes(state.view) ? state.view : "urban";
  state.view = view;
  const isUrban = view === "urban";
  useRegion(isUrban ? "yokohama" : "mobara");
  setHeader(
    "双区域总览", "一套空间底座，两类同域决策产品", "TWO REGIONS · ONE FOUNDATION",
    "不再把不同区域的数据假装成一次联合分析",
    "横滨聚焦城市光储韧性，茂原聚焦地面光伏开发；数据管线、地图交互和证据标准保持一致。",
    "<span>横滨城市韧性</span><i>＋</i><span>茂原新能源开发</span><i>→</i><strong>共享空间智能平台</strong>"
  );
  setMetrics([
    metric("横滨建筑资产", state.data.buildingSummary.building_count.toLocaleString(), "栋", "坡地暴露与屋顶光伏代理", colors.red),
    metric("横滨道路网络", state.data.roadSummary.road_count, "段", `${state.data.roadSummary.total_km} km 韧性分析`, colors.amber),
    metric("茂原光伏优选", state.data.solarSummary.counts.preferred, "格", `${state.data.solarSummary.shortlist_area_ha} ha 初筛面积`, colors.green),
    metric("10 m 遥感证据", (state.data.embeddingSummary.regions.yokohama.pixel_count + state.data.embeddingSummary.regions.mobara.pixel_count).toLocaleString(), "像素", "Google AEF · 2023→2024", colors.blue)
  ]);
  setTabs([["urban", "横滨 · 城市韧性"], ["renewable", "茂原 · 新能源开发"]], view);

  if (isUrban) {
    legend([["光储枢纽", colors.lime], ["复合走廊", colors.red], ["高暴露建筑", "#7b342b"]]);
    const highBuildings = state.data.buildings.features.filter(feature => feature.properties.risk_band === "high");
    layerForFeatures(highBuildings, { style: { color: "#7b342b", weight: .4, fillColor: colors.red, fillOpacity: .2 } }, () => "");
    layerForFeatures(state.data.corridors.features, { style: feature => ({ color: feature.properties.joint_band === "priority" ? colors.red : colors.amber, weight: feature.properties.joint_band === "priority" ? 4 : 2.2, opacity: .65 }) }, props => popup(props.name || "未命名道路", "复合干预走廊", [["联合分", props.compound_score], ["高风险建筑", `${props.joint_high_risk_buildings} 栋`]]));
    const ref = layerForFeatures(state.data.hubs.features, { style: { color: "#0c4e34", weight: 1.2, fillColor: colors.lime, fillOpacity: .9 } }, props => popup(props.name, "社区光储韧性枢纽", [["联合分", props.hub_score], ["光伏代理", `${props.pv_kwp_proxy} kWp`], ["服务需求", `${props.served_high_risk_buildings} 栋`]]));
    const items = state.data.hubs.features;
    state.queueLayers = items.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
    setQueueHeading("YOKOHAMA URBAN RESILIENCE", "横滨光储枢纽队列", items.length);
    queue(items, props => ({ color: colors.green, title: props.name, detail: `${props.pv_kwp_proxy} kWp · 服务 ${props.served_high_risk_buildings} 栋`, score: props.hub_score }));
    document.getElementById("method-card").innerHTML = "<strong>横滨 · 真正同域</strong><br>坡地建筑、道路、官方防灾据点和屋顶光伏代理全部来自同一研究范围；Google AEF 变化层作为独立核查证据，不进入评分。";
    document.getElementById("map-note").textContent = "横滨产品不使用茂原地面光伏网格；屋顶容量仍是建筑轮廓面积代理。";
  } else {
    legend([["高交付性", colors.blue], ["候选", colors.green], ["输电线", "#8e5eaa"]]);
    const context = layerForFeatures(state.data.solarContext.features, { style: feature => feature.properties.kind === "power" ? { color: "#8e5eaa", weight: 3.5, dashArray: "5 5" } : feature.properties.kind === "water" ? { color: colors.blue, weight: 1.4 } : { color: "#687b74", weight: .8 } }, () => "");
    context.layer.bringToBack();
    const items = state.data.delivery.features;
    const ref = layerForFeatures(items, { style: feature => ({ color: "#fff", weight: 1, fillColor: feature.properties.delivery_band === "priority" ? colors.blue : colors.green, fillOpacity: .76 }) }, props => popup(props.cell_id, "可交付光伏单元", [["交付分", props.delivery_score], ["坡度", `${props.slope_deg}°`], ["道路", `${props.distance_road_m} m`], ["输电线", `${props.distance_grid_m} m`]]));
    state.queueLayers = items.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
    setQueueHeading("MOBARA SOLAR DEVELOPMENT", "茂原联合踏勘队列", items.length);
    queue(items, props => ({ color: props.delivery_band === "priority" ? colors.blue : colors.green, title: `单元 ${props.cell_id}`, detail: `${props.area_ha} ha · 坡度 ${props.slope_deg}° · 道路 ${props.distance_road_m} m`, score: props.delivery_score }));
    document.getElementById("method-card").innerHTML = "<strong>茂原 · 独立开发产品</strong><br>地面光伏、道路、地形、输电距离和 AEF 年度变化在茂原同域核查；嵌入变化暂不进入适宜分。";
    document.getElementById("map-note").textContent = "影像用于识别当前地表背景；不能替代地权、农地转用、生态和接续検討。";
  }
}

function renderEvidence() {
  const allowed = ["yokohama_change", "yokohama_latent", "mobara_change", "mobara_latent"];
  const view = allowed.includes(state.view) ? state.view : "yokohama_change";
  state.view = view;
  const [region, mode] = view.split("_");
  useRegion(region);
  const summary = state.data.embeddingSummary.regions[region];
  const overlay = state.data.embeddingSummary.overlays[region];
  const zones = (region === "yokohama" ? state.data.yokohamaZones : state.data.mobaraZones).features;
  const evidence = state.data.embeddingEvidence.features
    .filter(feature => feature.properties.region === region)
    .sort((a, b) => b.properties.change_score - a.properties.change_score);

  setHeader(
    "统一底座 / 多尺度证据", "从 10 m 地表表征到可行动资产", "MULTI-SCALE EVIDENCE STACK",
    mode === "change" ? "年度变化用于发现异常，不替代原因判断" : "64 维表征用于相似性，不伪装成土地类别",
    "Google Satellite Embedding、对象资产、邻域上下文与区域门槛分层保存；观测、代理和待接入数据在界面上明确区分。",
    "<span>10 m 遥感</span><i>→</i><span>对象资产</span><i>→</i><span>邻域上下文</span><i>→</i><strong>投资队列</strong>"
  );
  setEvidenceStatus([
    ["observed", "Satellite Embedding", "2023→2024 真实裁剪"],
    ["proxy", "决策区", "启发式聚合"]
  ]);
  setMetrics([
    metric("有效 10 m 像素", summary.pixel_count.toLocaleString(), "个", `${summary.valid_pct}% 覆盖`, colors.forest),
    metric("平均余弦变化", summary.mean_cosine_change, "", `P95 ${summary.p95_cosine_change}`, colors.amber),
    metric("多尺度决策区", zones.length, "区", "对象与邻域汇总", colors.green),
    metric("付费数据依赖", 0, "项", "运行时无需 API Key", colors.green)
  ]);
  setTabs([
    ["yokohama_change", "横滨 · 年度变化"], ["yokohama_latent", "横滨 · 相似表征"],
    ["mobara_change", "茂原 · 年度变化"], ["mobara_latent", "茂原 · 相似表征"]
  ], view);

  imageOverlay(mode === "change" ? overlay.change_image : overlay.latent_image, overlay.bounds, mode === "change" ? .82 : .74);
  const zoneLayer = layerForFeatures(zones, {
    style: feature => ({ color: "#ffffff", weight: 1.1, dashArray: "4 4", fillColor: colors.forest, fillOpacity: .04 })
  }, props => popup(props.zone_id, "多尺度决策区", [
    ["行动分", props.action_score], ["上下文", props.context_density],
    ["嵌入变化", props.embedding_change_score ?? "—"], ["未计入评分", props.embedding_used_in_score ? "否" : "是"]
  ]));
  zoneLayer.layer.bringToFront();

  let ref;
  if (mode === "change") {
    legend([["变化较高", colors.red], ["中等", colors.amber], ["稳定", colors.forest]]);
    ref = layerForFeatures(evidence, {
      style: feature => ({ color: "transparent", weight: 0, fillColor: feature.properties.change_score >= 75 ? colors.red : feature.properties.change_score >= 45 ? colors.amber : colors.forest, fillOpacity: .08 })
    }, props => popup(props.cell_id, "Satellite Embedding 年度变化", [
      ["变化分位", props.change_score], ["余弦变化", props.cosine_change],
      ["有效像素", props.valid_pixels], ["证据状态", "观测表征"]
    ]));
  } else {
    legend([["颜色", colors.blue], ["仅表达 64D 相似性", colors.gray]]);
    ref = layerForFeatures(evidence, {
      style: { color: "transparent", weight: 0, fillOpacity: 0 }
    }, props => popup(props.cell_id, "Satellite Embedding 相似表征", [
      ["年度", "2024"], ["支持率", `${props.support_pct}%`],
      ["向量预览", props.embedding_preview.slice(0, 3).join(" · ")], ["语义类别", "不可直接解释"]
    ]));
  }
  state.queueLayers = evidence.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
  setQueueHeading("CHANGE REVIEW", "变化证据核查队列", evidence.length);
  queue(evidence, props => ({
    color: props.change_score >= 75 ? colors.red : props.change_score >= 45 ? colors.amber : colors.green,
    title: `${props.cell_id} · ${props.year_pair}`,
    detail: `${props.valid_pixels} 个 10 m 像素 · 支持率 ${props.support_pct}%`,
    score: props.change_score,
    label: "CHANGE"
  }));
  document.getElementById("method-card").innerHTML = `<strong>当前遥感策略</strong><br>Embedding 只承担年度变化与相似性，不直接解释成土地类别，也不进入业务评分。Demo 使用本地缓存证据，不依赖 Earth Engine 或其他付费分析服务。geo_pfn 的 25–50 个相似整孔优势只作为稀疏迁移机制证据，不外推为本模块精度。`;
  document.getElementById("map-note").textContent = mode === "change"
    ? "暖色表示 2023→2024 的 64 维表征变化较大；原因可能是建设、植被或成像条件，必须结合影像与现场核查。"
    : "RGB 由 64 维向量的前三个主方向生成；颜色接近只代表表征相似，不等同于同一种土地利用。";
}

function renderFacilities() {
  const view = ["official", "network"].includes(state.view) ? state.view : "official";
  state.view = view;
  useRegion("yokohama");
  const facilities = [...state.data.facilities.features].sort((a, b) => b.properties.resilience_score - a.properties.resilience_score);
  const pv = facilities.reduce((sum, item) => sum + item.properties.pv_kwp_proxy, 0);
  const demandLinks = facilities.reduce((sum, item) => sum + item.properties.served_high_risk_buildings, 0);
  const meanScore = Math.round(facilities.reduce((sum, item) => sum + item.properties.resilience_score, 0) / facilities.length);
  setHeader(
    "横滨 / 官方设施韧性", "从假想枢纽转向真实公共设施", "OFFICIAL FACILITY RESILIENCE",
    "先在真实避难设施上验证“光储＋道路＋社区需求”",
    "采用横滨市 2026 年官方地域防灾拠点位置；屋顶匹配、光伏容量和服务需求仍作为可审计代理。",
    "<span>官方设施</span><i>×</i><span>灾时道路</span><i>×</i><span>周边需求</span><i>→</i><strong>改造项目</strong>"
  );
  setEvidenceStatus([
    ["observed", "设施位置", "横滨市 CC BY · 2026-04"],
    ["proxy", "屋顶 / 容量 / 服务圈", "待现场验证"]
  ]);
  setMetrics([
    metric("官方防灾据点", facilities.length, "处", "当前研究窗口内", colors.blue),
    metric("屋顶容量代理", Math.round(pv), "kWp", "最近建筑轮廓 × 0.12", colors.green),
    metric("高风险服务关联", demandLinks, "栋次", "250 m 服务圈，可重叠", colors.red),
    metric("平均韧性机会分", meanScore, "/100", "用于改造排队", colors.amber)
  ]);
  setTabs([["official", "官方设施"], ["network", "设施—道路—社区网络"]], view);

  if (view === "network") {
    layerForFeatures(state.data.corridors.features, {
      style: feature => ({ color: feature.properties.joint_band === "priority" ? colors.red : colors.amber, weight: 3.2, opacity: .55 })
    }, props => popup(props.name || "未命名道路", "复合干预走廊", [["联合分", props.compound_score], ["高风险建筑", props.joint_high_risk_buildings]]));
    layerForFeatures(state.data.hubs.features, {
      style: { color: colors.green, weight: .7, fillColor: colors.lime, fillOpacity: .35 }
    }, props => popup(props.name, "候选补充节点", [["联合分", props.hub_score], ["容量代理", `${props.pv_kwp_proxy} kWp`]]));
  }
  legend([["官方防灾据点", colors.blue], ["高机会", colors.green], ["周边高暴露", colors.red]]);
  const highBuildings = state.data.buildings.features.filter(feature => feature.properties.risk_band === "high");
  layerForFeatures(highBuildings, { style: { color: colors.red, weight: .25, fillColor: colors.red, fillOpacity: .12 } }, () => "");
  const ref = layerForFeatures(facilities, {
    pointToLayer: (feature, latlng) => L.circleMarker(latlng, {
      radius: 9, color: "#ffffff", weight: 2.2,
      fillColor: feature.properties.resilience_score >= 80 ? colors.green : colors.blue,
      fillOpacity: .95, className: "facility-marker"
    })
  }, props => popup(props.name, "横滨市官方地域防灾拠点", [
    ["机会分", props.resilience_score], ["官方状态", "已观测"],
    ["容量代理", `${props.pv_kwp_proxy} kWp`], ["高风险关联", `${props.served_high_risk_buildings} 栋`],
    ["道路距离", `${props.nearest_road_m} m`], ["屋顶匹配", `${props.matched_roof_m} m`]
  ]));
  state.queueLayers = facilities.map(feature => ref.byId.get(String(feature.id)));
  setQueueHeading("OFFICIAL ASSET QUEUE", "公共设施改造队列", facilities.length);
  queue(facilities, props => ({
    color: props.resilience_score >= 80 ? colors.green : colors.blue,
    title: props.name,
    detail: `${props.pv_kwp_proxy} kWp · 服务关联 ${props.served_high_risk_buildings} 栋 · 道路 ${props.nearest_road_m} m`,
    score: props.resilience_score
  }));
  document.getElementById("method-card").innerHTML = `<strong>可取自 Claude A3，但修正了核心缺陷</strong><br>设施身份与坐标改用横滨官方数据；不再写死高程，不使用“其他设施平均高程”冒充 TPI。评分分开显示官方观测和最近建筑/道路代理。`;
  document.getElementById("map-note").textContent = "两处设施是真实官方据点；容量、屋顶结构、储能可行性和服务人口尚未验证，不能直接作为投资承诺。";
}

function renderSlope() {
  useRegion("yokohama");
  const summary = state.data.buildingSummary;
  setHeader("基础分析 / 坡地暴露", "建筑级坡地暴露筛查", "SLOPE EXPOSURE", "先识别需要现场确认的建筑", "DEM5A 地形与 OSM 建筑轮廓共同生成坡度、局部起伏和低点暴露代理。", "");
  setMetrics([
    metric("分析建筑", summary.building_count.toLocaleString(), "栋", "OSM 建筑轮廓", colors.forest),
    metric("高暴露", summary.counts.high, "栋", "进入优先核验队列", colors.red),
    metric("中暴露", summary.counts.medium, "栋", "建议批量复核", colors.amber),
    metric("平均风险分", summary.mean_score, "/100", "启发式相对评分", colors.green)
  ]);
  setTabs([["all", "全部建筑"], ["high", "仅高暴露"]], ["all", "high"].includes(state.view) ? state.view : "all");
  legend([["高", colors.red], ["中", colors.amber], ["低", colors.green]]);
  const all = [...state.data.buildings.features].sort((a, b) => b.properties.risk_score - a.properties.risk_score);
  const features = state.view === "high" ? all.filter(feature => feature.properties.risk_band === "high") : all;
  const ref = layerForFeatures(features, {
    style: feature => ({ color: riskColor(feature.properties.risk_band), weight: .55, fillColor: riskColor(feature.properties.risk_band), fillOpacity: feature.properties.risk_band === "high" ? .72 : .42 })
  }, props => popup(props.name, "坡地暴露", [["风险分", props.risk_score], ["坡度", `${props.slope_deg}°`], ["局部起伏", `${props.local_relief_m} m`], ["高程", `${props.elevation_m} m`]]));
  const queueItems = all.filter(feature => feature.properties.risk_band === "high");
  state.queueLayers = queueItems.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
  setQueueHeading("EXPOSURE QUEUE", "高暴露建筑队列", summary.counts.high);
  queue(queueItems, props => ({ color: colors.red, title: props.name, detail: `坡度 ${props.slope_deg}° · 起伏 ${props.local_relief_m} m`, score: props.risk_score }));
  document.getElementById("method-card").innerHTML = "<strong>评分构成</strong><br>坡度 55% ＋ 局部起伏 30% ＋ 低点暴露 15%。用于筛查，不替代地质灾害图、结构鉴定或现场踏勘。";
  document.getElementById("map-note").textContent = "建筑风险为 0–100 相对分；红色表示优先核验，并非已确认灾害。";
}

function renderRoads() {
  useRegion("yokohama");
  const summary = state.data.roadSummary;
  setHeader("基础分析 / 道路韧性", "道路连续性与巡检优先级", "ROAD RESILIENCE", "从道路本身的脆弱性，看到受影响的社区", "道路坡度、低点、关键等级与邻近高暴露建筑共同决定巡检优先级。", "");
  setMetrics([
    metric("分析道路", summary.road_count, "段", `${summary.total_km} km 路网`, colors.forest),
    metric("高优先队列", summary.high_queue, "段", "优先现场巡检", colors.red),
    metric("邻近暴露建筑", summary.exposed_buildings.toLocaleString(), "栋", "道路 55m 影响带", colors.amber),
    metric("平均优先分", summary.mean_score, "/100", "综合情景基线", colors.blue)
  ]);
  setTabs([["all", "完整路网"], ["high", "高优先道路"]], ["all", "high"].includes(state.view) ? state.view : "all");
  legend([["≥70 高优先", colors.red], ["45–69 关注", colors.amber], ["低", colors.green]]);
  const all = [...state.data.roads.features].sort((a, b) => b.properties.priority_score - a.properties.priority_score);
  const features = state.view === "high" ? all.filter(feature => feature.properties.priority_score >= 70) : all;
  const ref = layerForFeatures(features, {
    style: feature => {
      const score = feature.properties.priority_score;
      return { color: score >= 70 ? colors.red : score >= 45 ? colors.amber : colors.green, weight: score >= 70 ? 4 : 2.2, opacity: .85 };
    }
  }, props => popup(props.name || "未命名道路", "道路韧性", [["优先分", props.priority_score], ["最大坡度", `${props.max_slope_deg}°`], ["暴露建筑", `${props.nearby_exposed_buildings} 栋`], ["长度", `${props.length_m} m`]]));
  const queueItems = all.filter(feature => feature.properties.priority_score >= 70);
  state.queueLayers = queueItems.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
  setQueueHeading("ROAD QUEUE", "道路巡检队列", queueItems.length);
  queue(queueItems, props => ({ color: colors.red, title: props.name || "未命名道路", detail: `${props.highway} · 邻近高风险 ${props.nearby_high_buildings} 栋`, score: props.priority_score }));
  document.getElementById("method-card").innerHTML = "<strong>基线权重</strong><br>地形 45% ＋ 建筑暴露 25% ＋ 道路关键性 20% ＋ 低点 10%。生产版应加入交通量、封路记录与排水设施。";
  document.getElementById("map-note").textContent = "道路分数是巡检排队代理，不是通行中断概率。";
}

function renderSolar() {
  useRegion("mobara");
  const summary = state.data.solarSummary;
  setHeader("基础分析 / 光伏选址", "地面光伏候选地快速筛查", "SOLAR SITING", "先排除明显冲突，再把踏勘资源放在高价值单元", "坡度、道路、输电线、建筑与水体退距构成透明的开源数据初筛。", "");
  setMetrics([
    metric("候选网格", summary.cell_count, "格", "约 2.24 ha / 格", colors.forest),
    metric("优选单元", summary.counts.preferred, "格", `${summary.shortlist_area_ha} ha`, colors.green),
    metric("条件可选", summary.counts.conditional, "格", "需进一步核验", colors.amber),
    metric("年均 GHI", summary.annual_ghi_kwh_m2.toLocaleString(), "kWh/m²", "NASA POWER 2001–2020", colors.blue)
  ]);
  setTabs([["all", "全部网格"], ["preferred", "仅优选"]], ["all", "preferred"].includes(state.view) ? state.view : "all");
  legend([["优选", colors.green], ["条件", colors.amber], ["排除", colors.gray]]);
  const context = layerForFeatures(state.data.solarContext.features, {
    style: feature => {
      const kind = feature.properties.kind;
      if (kind === "power") return { color: "#8e5eaa", weight: 3.5, opacity: .8, dashArray: "5 5" };
      if (kind === "water") return { color: colors.blue, weight: 2, opacity: .75 };
      if (kind === "building") return { color: "#6e7e78", weight: .5, fillColor: "#8b9994", fillOpacity: .45 };
      return { color: "#687b74", weight: 1.2, opacity: .7 };
    }
  }, props => popup(props.name || props.kind, "场地背景", [["类型", props.kind], ["等级", props.class || "—"]]));
  context.layer.bringToBack();
  const all = [...state.data.solar.features].sort((a, b) => b.properties.score - a.properties.score);
  const features = state.view === "preferred" ? all.filter(feature => feature.properties.status === "preferred") : all;
  const ref = layerForFeatures(features, {
    style: feature => {
      const status = feature.properties.status;
      const color = status === "preferred" ? colors.green : status === "conditional" ? colors.amber : colors.gray;
      return { color: "#fff", weight: .65, fillColor: color, fillOpacity: status === "reject" ? .34 : .72 };
    }
  }, props => popup(props.cell_id, "光伏选址单元", [["适宜分", props.score], ["坡度", `${props.slope_deg}°`], ["距输电线", `${props.distance_grid_m} m`], ["距道路", `${props.distance_road_m} m`]]));
  const queueItems = all.filter(feature => feature.properties.status === "preferred");
  state.queueLayers = queueItems.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
  setQueueHeading("SITE SHORTLIST", "优选场地队列", queueItems.length);
  queue(queueItems, props => ({ color: colors.green, title: `单元 ${props.cell_id}`, detail: `${props.area_ha} ha · 坡度 ${props.slope_deg}° · 道路 ${props.distance_road_m} m`, score: props.score }));
  document.getElementById("method-card").innerHTML = "<strong>筛查权重</strong><br>坡度 35% ＋ 输电线 25% ＋ 道路 20% ＋ 退距 10% ＋ 土地背景 10%。尚未覆盖地权、容量、环评和生态红线。";
  document.getElementById("map-note").textContent = "GHI 为区域气候平均值；网格结论只用于项目发现，不构成发电量或并网承诺。";
}

function renderJoint() {
  const view = ["hubs", "corridors"].includes(state.view) ? state.view : "hubs";
  state.view = view;
  useRegion("yokohama");
  const summary = state.data.jointSummary;
  setHeader("横滨 / 光储韧性枢纽", "城市风险与分布式能源的同域联合决策", "YOKOHAMA URBAN RESILIENCE", "把屋顶能源潜力放到真正需要韧性服务的地方", "全部输入均位于横滨同一研究范围：建筑坡地暴露、道路可达性与屋顶光伏容量代理。", "<span>坡地需求</span><i>×</i><span>道路可达</span><i>×</i><span>屋顶光伏</span><i>→</i><strong>韧性枢纽</strong>");
  setEvidenceStatus([
    ["observed", "官方设施 / DEM / OSM"],
    ["proxy", "风险 / 容量 / 服务圈"],
    ["observed", "AEF 变化", "独立核查，不计分"]
  ]);
  setMetrics([
    metric("韧性枢纽", summary.resilience_hubs.count, "处", `${summary.resilience_hubs.priority_count} 处高优先`, colors.lime),
    metric("屋顶容量代理", summary.resilience_hubs.pv_capacity_proxy_kwp.toLocaleString(), "kWp", "面积 × 0.12 kWp/m²", colors.green),
    metric("复合干预走廊", summary.compound_corridors.count, "段", `${summary.compound_corridors.road_length_km} km`, colors.red),
    metric("地形证据层", 3, "类", "DEM · 起伏 · 坡度", colors.blue)
  ]);
  setTabs([["hubs", "社区韧性枢纽"], ["corridors", "复合干预走廊"]], view);

  let features, ref;
  if (view === "hubs") {
    legend([["高优先枢纽", colors.lime], ["候选", colors.green], ["高暴露需求", colors.red]]);
    const high = state.data.buildings.features.filter(feature => feature.properties.risk_band === "high");
    layerForFeatures(high, { style: { color: colors.red, weight: .35, fillColor: colors.red, fillOpacity: .18 } }, () => "");
    layerForFeatures(state.data.facilities.features, {
      pointToLayer: (feature, latlng) => L.circleMarker(latlng, { radius: 8, color: "#fff", weight: 2, fillColor: colors.blue, fillOpacity: .95 })
    }, props => popup(props.name, "官方防灾据点", [["机会分", props.resilience_score], ["容量代理", `${props.pv_kwp_proxy} kWp`]]));
    features = state.data.hubs.features;
    ref = layerForFeatures(features, { style: feature => ({ color: "#104b35", weight: 1.1, fillColor: feature.properties.hub_band === "priority" ? colors.lime : colors.green, fillOpacity: .9 }) }, props => popup(props.name, "社区光储韧性枢纽", [["联合分", props.hub_score], ["光伏代理", `${props.pv_kwp_proxy} kWp`], ["服务需求", `${props.served_high_risk_buildings} 栋`], ["道路优先度", props.nearest_road_priority]]));
    setQueueHeading("RESILIENCE HUBS", "枢纽投资队列", features.length);
    queue(features, props => ({ color: colors.green, title: props.name, detail: `${props.pv_kwp_proxy} kWp · 服务 ${props.served_high_risk_buildings} 栋`, score: props.hub_score }));
    document.getElementById("method-card").innerHTML = "<strong>联合评分</strong><br>屋顶光伏代理 30% ＋ 道路可达 25% ＋ 周边高风险需求 35% ＋ 场址安全 10%。建议下一步核查公共属性、屋顶结构和避难功能。";
    document.getElementById("map-note").textContent = "优先寻找自身坡度较低、道路可达且能服务高风险建筑群的大型屋顶。";
  } else if (view === "corridors") {
    legend([["高优先", colors.red], ["关注", colors.amber]]);
    features = state.data.corridors.features;
    ref = layerForFeatures(features, { style: feature => ({ color: feature.properties.joint_band === "priority" ? colors.red : colors.amber, weight: feature.properties.joint_band === "priority" ? 4.5 : 2.5, opacity: .85 }) }, props => popup(props.name || "未命名道路", "复合干预走廊", [["联合分", props.compound_score], ["高风险建筑", `${props.joint_high_risk_buildings} 栋`], ["平均建筑风险", props.joint_average_building_risk], ["长度", `${props.length_m} m`]]));
    setQueueHeading("COMPOUND CORRIDORS", "联合巡检队列", features.length);
    queue(features, props => ({ color: props.joint_band === "priority" ? colors.red : colors.amber, title: props.name || "未命名道路", detail: `${props.joint_high_risk_buildings} 栋高风险建筑 · ${props.length_m} m`, score: props.compound_score }));
    document.getElementById("method-card").innerHTML = "<strong>联合评分</strong><br>道路韧性 45% ＋ 高风险建筑密度 35% ＋ 邻近建筑平均风险 20%。把分散的道路和建筑巡检打包为走廊项目。";
    document.getElementById("map-note").textContent = "同一高风险建筑可能邻近多条道路，因此关联数量不可直接相加为独立受益人口。";
  }
  state.queueLayers = features.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
}

function renderDevelopment() {
  const view = ["delivery", "constraints"].includes(state.view) ? state.view : "delivery";
  state.view = view;
  useRegion("mobara");
  const summary = state.data.jointSummary;
  const grid = state.data.gridScreen.mobara_screen;
  setHeader("茂原 / 开发约束", "从“光照适宜”走向“土地与并网可开发”", "MOBARA DEVELOPMENT READINESS", "把场地筛查升级成可交付性尽调队列", "地形、道路、输电背景和东京电力公开容量快照已接入；地籍、农地、保护区与地价仍处于数据管线阶段。", "<span>土地合规</span><i>×</i><span>工程可达</span><i>×</i><span>电网约束</span><i>→</i><strong>开发准备度</strong>");
  setMetrics([
    metric("可交付单元", summary.solar_delivery_cells.count, "格", `${summary.solar_delivery_cells.area_ha} ha`, colors.blue),
    metric("规则排除", state.data.solarSummary.counts.reject, "格", "现有退距与坡度规则", colors.red),
    metric("已缓存视觉层", 4, "类", "标准 · 影像 · 起伏 · 坡度", colors.green),
    metric("上位约束后空容量", grid.spare_with_upstream_mw, "MW", `自身 ${grid.spare_own_mw} MW · 仅公开筛查`, colors.red, { snapshot: state.data.gridScreen.source_file_last_modified_at })
  ]);
  setTabs([["delivery", "可交付候选"], ["constraints", "现有排除项"]], view);
  const context = layerForFeatures(state.data.solarContext.features, {
    style: feature => feature.properties.kind === "power" ? { color: "#8e5eaa", weight: 3.5, opacity: .85, dashArray: "5 5" } : feature.properties.kind === "water" ? { color: colors.blue, weight: 1.5, opacity: .75 } : { color: "#687b74", weight: 1, opacity: .55 }
  }, () => "");
  context.layer.bringToBack();

  let features, ref;
  if (view === "delivery") {
    legend([["高交付性", colors.blue], ["候选", colors.green], ["输电线", "#8e5eaa"]]);
    features = state.data.delivery.features;
    ref = layerForFeatures(features, { style: feature => ({ color: "#fff", weight: 1, fillColor: feature.properties.delivery_band === "priority" ? colors.blue : colors.green, fillOpacity: .78 }) }, props => popup(props.cell_id, "可交付光伏单元", [["交付分", props.delivery_score], ["坡度", `${props.slope_deg}°`], ["道路", `${props.distance_road_m} m`], ["输电线", `${props.distance_grid_m} m`]]));
    setQueueHeading("DELIVERY-READY SOLAR", "联合踏勘队列", features.length);
    queue(features, props => ({ color: props.delivery_band === "priority" ? colors.blue : colors.green, title: `单元 ${props.cell_id}`, detail: `${props.area_ha} ha · 坡度 ${props.slope_deg}° · 输电线 ${props.distance_grid_m} m`, score: props.delivery_score }));
    const gridSnapshot = state.data.gridScreen.source_file_last_modified_at || "—";
    const gridMethod = state.lang === "ja"
      ? `東京電力ソースZIPの最終更新 ${gridSnapshot}：茂原変電所の当該設備空容量代理は ${grid.spare_own_mw} MW、上位系統考慮後は ${grid.spare_with_upstream_mw} MW。平常時出力制御の可能性があるため、候補地調査前に系統接続の事前相談を推奨します。`
      : state.lang === "en"
        ? `TEPCO source ZIP last modified ${gridSnapshot}: Mobara substation own spare-capacity proxy is ${grid.spare_own_mw} MW and ${grid.spare_with_upstream_mw} MW after upstream constraints. Normal-operation curtailment may occur; request a grid pre-consultation before surveying candidate sites.`
        : `东京电力源 ZIP 最后修改于 ${gridSnapshot}：茂原变电所自身空容量代理 ${grid.spare_own_mw} MW；考虑上位系统后 ${grid.spare_with_upstream_mw} MW；存在平常时出力控制可能。建议候选地踏勘前先做并网预咨询。`;
    document.getElementById("method-card").innerHTML = `<strong>${escapeHtml(t("并网先决信号"))}</strong><br>${escapeHtml(gridMethod)}`;
    document.getElementById("map-note").textContent = "容量CSV没有设备几何，当前作为茂原区域级门槛证据，不分配到单个网格，也不等同正式接续検討。";
  } else {
    legend([["多重冲突", colors.red], ["单项冲突", colors.amber], ["水体", colors.blue]]);
    features = state.data.solar.features.filter(feature => feature.properties.status === "reject").sort((a, b) => b.properties.reject_reasons.length - a.properties.reject_reasons.length || b.properties.slope_deg - a.properties.slope_deg);
    ref = layerForFeatures(features, { style: feature => ({ color: "#fff", weight: .7, fillColor: feature.properties.reject_reasons.length > 1 ? colors.red : colors.amber, fillOpacity: .72 }) }, props => popup(props.cell_id, "现有规则排除", [["冲突数", props.reject_reasons.length], ["原因", props.reject_reasons.join("、") || "—"], ["坡度", `${props.slope_deg}°`], ["距水体", `${props.distance_water_m} m`]]));
    setQueueHeading("CURRENT EXCLUSIONS", "规则排除队列", features.length);
    queue(features, props => ({ color: props.reject_reasons.length > 1 ? colors.red : colors.amber, title: `单元 ${props.cell_id}`, detail: props.reject_reasons.join(" · ") || "规则冲突", score: props.reject_reasons.length, label: "RULES" }));
    document.getElementById("method-card").innerHTML = `<strong>排除项边界</strong><br>空间规则包含坡度、道路、输电线、建筑和水体退距；电网快照已提示上位约束。地籍权属、农地转用、保护区和地价尚未进入逐格判定。`;
    document.getElementById("map-note").textContent = "红色是多项现有空间规则冲突，不代表法律上绝对不可开发；电网信号目前是区域级证据。";
  }
  state.queueLayers = features.slice(0, 18).map(feature => ref.byId.get(String(feature.id)));
}

function renderModule(module, preserveView = false) {
  clearMap();
  state.module = module;
  setArchitectureMode(module === "architecture");
  if (!preserveView) {
    const defaults = { architecture: "layers", overview: "urban", evidence: "yokohama_change", slope: "all", roads: "all", facilities: "official", solar: "all", joint: "hubs", development: "delivery" };
    state.view = defaults[module] || "all";
  }
  document.querySelectorAll(".nav-item").forEach(button => button.classList.toggle("active", button.dataset.module === module));
  if (module === "architecture") renderArchitecture();
  if (module === "overview") renderOverview();
  if (module === "evidence") renderEvidence();
  if (module === "slope") renderSlope();
  if (module === "roads") renderRoads();
  if (module === "facilities") renderFacilities();
  if (module === "solar") renderSolar();
  if (module === "joint") renderJoint();
  if (module === "development") renderDevelopment();
  translateElementText(document.getElementById("method-card"));
  translateElementText(document.getElementById("map-note"));
  applyStaticTranslations();
  if (module !== "architecture") window.setTimeout(() => map.invalidateSize(), 50);
}

document.addEventListener("click", event => {
  const trigger = event.target.closest("[data-audit-id]");
  if (!trigger) return;
  event.preventDefault();
  event.stopPropagation();
  openAudit(state.auditRecords.get(trigger.dataset.auditId), trigger);
});

document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeAudit();
  if ((event.key === "Enter" || event.key === " ") && event.target.matches("[data-audit-id]")) {
    event.preventDefault();
    openAudit(state.auditRecords.get(event.target.dataset.auditId), event.target);
  }
});

document.getElementById("audit-close").addEventListener("click", closeAudit);
document.getElementById("audit-backdrop").addEventListener("click", closeAudit);
document.querySelectorAll(".language-button").forEach(button => button.addEventListener("click", () => {
  const lang = button.dataset.lang;
  if (!LANGS.includes(lang) || lang === state.lang) return;
  state.lang = lang;
  localStorage.setItem("terrai-language", lang);
  if (Object.keys(state.data).length) renderModule(state.module, true);
  else applyStaticTranslations();
}));

Promise.all(Object.entries(PATHS).map(([key, path]) => fetchJson(path).then(data => [key, data])))
  .then(entries => {
    state.data = Object.fromEntries(entries);
    document.querySelectorAll(".nav-item").forEach(button => button.addEventListener("click", () => renderModule(button.dataset.module)));
    const params = new URLSearchParams(window.location.search);
    const requestedLanguage = params.get("lang") || localStorage.getItem("terrai-language") || "zh";
    state.lang = LANGS.includes(requestedLanguage) ? requestedLanguage : "zh";
    const initialModule = ["architecture", "overview", "evidence", "slope", "roads", "facilities", "solar", "joint", "development"].includes(params.get("module")) ? params.get("module") : "architecture";
    const initialView = params.get("view");
    if (Object.hasOwn(BASEMAPS, params.get("basemap"))) state.basemap = params.get("basemap");
    renderModule(initialModule);
    if (initialView) {
      state.view = initialView;
      renderModule(initialModule, true);
    }
    document.getElementById("loading").classList.add("done");
  })
  .catch(error => {
    document.getElementById("loading").innerHTML = `<strong>${escapeHtml(t("数据装载失败"))}</strong><span>${escapeHtml(error.message)}</span>`;
    console.error(error);
  });
