/**
 * Audit record builders — the provenance behind every dashed value.
 *
 * Port of `frontend/audit.js`. Every displayed value keeps its route back to
 * source, formula and limitation; all three record kinds (`raw`,
 * `calculation`, `model`) and every section survive the port. Records carry
 * trilingual `Localized` content resolved by the drawer at display time, so a
 * language switch re-renders an open record too.
 *
 * Branching that `audit.js` did on Chinese UI labels is now done on typed
 * message keys.
 */

import { CATALOGS, type Language, type MessageKey } from "./i18n/i18n.svelte";
import type { FeatureProperties } from "./api/types";

export interface Localized {
  zh: string;
  ja: string;
  en: string;
}

export type LocalizedText = Localized | string;
export type AuditValue = LocalizedText | number;

export interface AuditSection {
  label: LocalizedText;
  value: LocalizedText;
  url?: string;
}

export type AuditKind = "raw" | "calculation" | "model";

export interface AuditRecord {
  kind: AuditKind;
  title: LocalizedText;
  value: AuditValue;
  sections: AuditSection[];
  caveat: LocalizedText;
}

export const ml = (zh: string, ja: string, en: string): Localized => ({ zh, ja, en });

export function text(value: AuditValue, lang: Language): string {
  return typeof value === "object" ? value[lang] || value.zh : String(value);
}

/** Trilingual text for a message key, so audit titles follow the catalogs. */
export function localized(key: MessageKey): Localized {
  return { zh: CATALOGS.zh[key], ja: CATALOGS.ja[key], en: CATALOGS.en[key] };
}

const section = (label: Localized, value: LocalizedText, url = ""): AuditSection => ({ label, value, url });
const resultText = (value: string | number, unit = "") => `${value}${unit ? ` ${unit}` : ""}`;

export const TYPE_LABELS: Record<AuditKind, Localized> = {
  raw: ml("原始数据", "原データ", "SOURCE DATA"),
  model: ml("预测 / 模型输出", "予測・モデル出力", "PREDICTION / MODEL OUTPUT"),
  calculation: ml("计算数据", "計算データ", "CALCULATION"),
};

function raw(
  title: LocalizedText,
  value: AuditValue,
  source: LocalizedText,
  sourceField: LocalizedText,
  snapshot: LocalizedText,
  localFile: LocalizedText,
  caveat: LocalizedText,
  url = "",
): AuditRecord {
  return {
    kind: "raw",
    title,
    value,
    sections: [
      section(ml("数据来源", "データソース", "Data source"), source, url),
      section(ml("来源字段", "元フィールド", "Source field"), sourceField),
      section(ml("时间/版本", "時点・バージョン", "Date / version"), snapshot),
      section(ml("本地证据", "ローカル証拠", "Local evidence"), localFile),
    ],
    caveat,
  };
}

function calculation(
  title: LocalizedText,
  value: AuditValue,
  formula: LocalizedText,
  inputs: LocalizedText,
  sources: LocalizedText,
  caveat: LocalizedText,
): AuditRecord {
  return {
    kind: "calculation",
    title,
    value,
    sections: [
      section(ml("计算公式", "計算式", "Formula"), formula),
      section(ml("本次代入", "今回の代入値", "Substituted inputs"), inputs),
      section(ml("数据血缘", "データ系譜", "Data lineage"), sources),
    ],
    caveat,
  };
}

function model(
  title: LocalizedText,
  value: AuditValue,
  modelName: LocalizedText,
  features: LocalizedText,
  uncertainty: LocalizedText,
  validation: LocalizedText,
  source: LocalizedText,
  url = "",
): AuditRecord {
  return {
    kind: "model",
    title,
    value,
    sections: [
      section(ml("模型/版本", "モデル・バージョン", "Model / version"), modelName),
      section(ml("输入与输出", "入力と出力", "Inputs and output"), features),
      section(ml("不确定性", "不確実性", "Uncertainty"), uncertainty),
      section(ml("验证状态", "検証状況", "Validation status"), validation),
      section(ml("数据来源", "データソース", "Data source"), source, url),
    ],
    caveat: ml(
      "模型表征不是土地类别或灾害概率；必须结合影像、现场和本地标签验证。",
      "モデル表現は土地分類や災害確率ではありません。画像、現地調査、ローカルラベルでの検証が必要です。",
      "The model representation is neither a land-cover class nor a hazard probability; validate it with imagery, field checks and local labels.",
    ),
  };
}

function countAudit(
  title: LocalizedText,
  value: string,
  file: string,
  filter: string,
  source: string,
): AuditRecord {
  return calculation(
    title,
    value,
    "count(records satisfying filter)",
    `${filter} → ${value}`,
    `${source} → ${file}`,
    ml(
      "数量是当前研究范围和快照的记录数，不代表全市或全县总量。",
      "現在の調査範囲・スナップショット内の件数であり、市・県全体の総数ではありません。",
      "This is a record count for the current study window and snapshot, not a city- or prefecture-wide total.",
    ),
  );
}

export interface MetricAuditContext {
  snapshot?: string | null;
}

/** [file, filter, source] for count-style metrics, keyed by metric message key. */
const COUNT_FILES: Partial<Record<MessageKey, [string, string, string]>> = {
  "metric.yokohamaBuildings": ["data/yokohama/building_risk.geojson", "all building features", "OpenStreetMap + GSI DEM5A"],
  "metric.buildingsAnalyzed": ["data/yokohama/building_risk.geojson", "all building features", "OpenStreetMap + GSI DEM5A"],
  "metric.yokohamaRoads": ["data/yokohama/road_priority.geojson", "all road segments", "OpenStreetMap + TerrAI segmentation"],
  "metric.roadsAnalyzed": ["data/yokohama/road_priority.geojson", "all road segments", "OpenStreetMap + TerrAI segmentation"],
  "metric.mobaraSolar": ["data/mobara/site_cells.geojson", "status = preferred", "GSI DEM5A + OpenStreetMap"],
  "metric.preferredCells": ["data/mobara/site_cells.geojson", "status = preferred", "GSI DEM5A + OpenStreetMap"],
  "metric.candidateCells": ["data/mobara/site_cells.geojson", "all generated grid cells", "TerrAI grid + GSI DEM5A + OpenStreetMap"],
  "metric.conditionalCells": ["data/mobara/site_cells.geojson", "status = conditional", "TerrAI suitability rules"],
  "metric.highExposure": ["data/yokohama/building_risk.geojson", "risk_band = high", "TerrAI slope exposure rules"],
  "metric.mediumExposure": ["data/yokohama/building_risk.geojson", "risk_band = medium", "TerrAI slope exposure rules"],
  "metric.highPriorityQueue": ["data/yokohama/road_priority.geojson", "priority_score ≥ 70", "TerrAI road priority rules"],
  "metric.deliveryCells": ["data/joint/solar_delivery_cells.geojson", "delivery_score ≥ 68", "TerrAI joint delivery rules"],
  "metric.ruleExclusions": ["data/mobara/site_cells.geojson", "status = reject", "TerrAI setback and slope rules"],
  "metric.resilienceHubs": ["data/joint/resilience_hubs.geojson", "hub_score ≥ 45 and candidate gates", "TerrAI joint hub rules"],
  "metric.compoundCorridors": ["data/joint/compound_corridors.geojson", "compound_score ≥ 62", "TerrAI compound corridor rules"],
  "metric.officialBases": ["data/yokohama/official_facility_resilience.geojson", "inside study bounds", "Yokohama City open data"],
};

export function metric(
  labelKey: MessageKey,
  value: string | number,
  unit: string,
  note: string,
  context: MetricAuditContext = {},
): AuditRecord {
  const title = localized(labelKey);
  const shown = resultText(value, unit);

  const countFile = COUNT_FILES[labelKey];
  if (countFile) return countAudit(title, shown, countFile[0], countFile[1], countFile[2]);

  if (labelKey === "metric.embedding10m" || labelKey === "metric.validPixels" || labelKey === "metric.meanCosine") {
    return model(
      title,
      shown,
      "AlphaEarth Foundations v2.1 / Satellite Embedding V1",
      ml(
        "多源地球观测 → 每个10 m像素64维单位向量；本页比较2023与2024年度向量。",
        "複数の地球観測データ → 10 m画素ごとの64次元単位ベクトル。本画面では2023年と2024年を比較。",
        "Multi-source Earth observations → a 64D unit vector per 10 m pixel; this view compares 2023 and 2024.",
      ),
      ml(
        "产品不提供逐像素预测区间；界面披露有效像素覆盖率、P95变化，并将其排除在业务评分之外。",
        "画素別の予測区間は提供されません。有効画素率とP95変化を表示し、業務スコアには使用しません。",
        "No per-pixel predictive interval is provided. The UI reports valid-pixel coverage and P95 change, and excludes it from business scores.",
      ),
      ml(
        "尚未用横滨/茂原本地标签完成hold-out校准。",
        "横浜・茂原のローカルラベルによるhold-out校正は未実施です。",
        "No hold-out calibration with Yokohama/Mobara local labels has been completed.",
      ),
      "Google Satellite Embedding V1 via Source Cooperative public COG mirror",
      "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL",
    );
  }

  if (labelKey === "metric.annualGhi") {
    return raw(
      title,
      shown,
      "NASA POWER Climatology API",
      "ALLSKY_SFC_SW_DWN",
      "2001–2020 climatology / API v2.9.7",
      "data/mobara/solar_summary.json",
      ml(
        "区域长期气候平均值，不是场址级发电量或逐年预测。",
        "地域の長期気候平均であり、地点別発電量や年次予測ではありません。",
        "Regional long-term climatology, not site-level yield or an annual forecast.",
      ),
      "https://power.larc.nasa.gov/docs/services/api/temporal/climatology/",
    );
  }

  if (labelKey === "metric.spareCapacity") {
    const snapshot = context.snapshot ? `source ZIP Last-Modified ${context.snapshot}` : "source date unavailable";
    return raw(
      title,
      shown,
      "TEPCO Power Grid 系統の予想潮流等（千葉県CSV）",
      "茂原配電用変電所 / 上位系統考慮後空容量",
      snapshot,
      "data/mobara/tepco_grid_screen.json",
      ml(
        "公开值为暂定简化筛查信息，不保证接入；正式结论需要接续検討。原资料并非开放许可数据。",
        "公開値は暫定的な簡略スクリーニング情報で、接続を保証しません。正式判断には接続検討が必要で、原資料はオープンライセンスではありません。",
        "The public value is provisional screening information and does not guarantee connection. A formal connection study is required; the source is not openly licensed.",
      ),
      "https://www.tepco.co.jp/pg/consignment/system/index-j.html",
    );
  }

  if (labelKey === "metric.roofCapacityProxy") {
    return calculation(
      title,
      shown,
      "Σ(roof footprint m² × 0.60 usable share × 0.20 kWp/m²) = Σ(footprint × 0.12)",
      `${note} → ${shown}`,
      "OpenStreetMap building footprint → TerrAI proxy",
      ml(
        "不含屋顶朝向、遮挡、结构承载、设备间距和消防通道。",
        "屋根方位、日影、構造耐力、機器間隔、消防動線は未考慮です。",
        "Roof orientation, shading, structural capacity, equipment spacing and fire access are not included.",
      ),
    );
  }

  if (labelKey === "metric.meanRiskScore" || labelKey === "metric.meanPriorityScore" || labelKey === "metric.meanResilienceScore") {
    return calculation(
      title,
      shown,
      "Σ(object score) / object count",
      `${note} → ${shown}`,
      "Object-level TerrAI heuristic scores",
      ml(
        "平均值用于组合概览，不代表单个对象风险或概率。",
        "平均値はポートフォリオ概要用で、個別対象のリスクや確率ではありません。",
        "The mean is a portfolio summary, not an individual-object risk or probability.",
      ),
    );
  }

  if (labelKey === "metric.highRiskLinks" || labelKey === "metric.nearbyExposedBuildings") {
    return calculation(
      title,
      shown,
      labelKey === "metric.highRiskLinks"
        ? "Σ count(high-risk buildings within 250 m)"
        : "count(buildings within 55 m road buffer)",
      `${note} → ${shown}`,
      "TerrAI spatial join over building and facility/road layers",
      ml(
        "空间关联可能重复计算同一建筑，不能直接解释为独立受益人口。",
        "同一建物が重複集計される場合があり、独立した受益人口とは解釈できません。",
        "Spatial links can count the same building more than once and cannot be read as unique beneficiaries.",
      ),
    );
  }

  if (
    labelKey === "metric.zones" ||
    labelKey === "metric.paidDeps" ||
    labelKey === "metric.terrainLayers" ||
    labelKey === "metric.cachedVisualLayers"
  ) {
    return calculation(
      title,
      shown,
      "count(configured records or layers)",
      `${note} → ${shown}`,
      "TerrAI local configuration and cached assets",
      ml(
        "这是工程清单数量，不是模型输出。",
        "これは構成・資産の件数であり、モデル出力ではありません。",
        "This is an engineering inventory count, not a model output.",
      ),
    );
  }

  return calculation(
    title,
    shown,
    "aggregate(current filtered records)",
    `${note} → ${shown}`,
    "TerrAI local GeoJSON/JSON",
    ml(
      "点击具体对象的字段可查看对象级公式和代入值。",
      "個別対象のフィールドをクリックすると、対象別の式と代入値を確認できます。",
      "Click an individual object field to inspect its object-level formula and substituted values.",
    ),
  );
}

/** Field labels: score keys plus the geospatial/property keys used by popups. */
export type FieldKey =
  | "score.risk"
  | "score.priority"
  | "score.suitability"
  | "score.joint"
  | "score.delivery"
  | "score.opportunity"
  | "score.action"
  | "score.changePercentile"
  | "score.conflicts"
  | "field.queueDetail"
  | "field.cosineChange"
  | "field.embeddingChange"
  | "field.vectorPreview"
  | "field.pvProxy"
  | "field.capacityProxy"
  | "field.roadPriority"
  | "field.slope"
  | "field.maxSlope"
  | "field.localRelief"
  | "field.elevation"
  | "field.road"
  | "field.transmission"
  | "field.distRoad"
  | "field.distTransmission"
  | "field.distWater"
  | "field.length"
  | "field.highRiskBuildings"
  | "field.serviceDemand"
  | "field.officialStatus"
  | "field.highRiskLinks"
  | "field.roadDistance"
  | "field.roofMatch"
  | "field.exposedBuildings"
  | "field.evidenceStatus"
  | "field.year"
  | "field.support"
  | "field.validPixels"
  | "field.semanticClass"
  | "field.notScored"
  | "field.context"
  | "field.kind"
  | "field.class"
  | "field.reasons"
  | "field.meanBuildingRisk"
  | "field.property";

export const FIELD_LABELS: Record<FieldKey, Localized> = {
  "score.risk": ml("风险分", "リスクスコア", "Risk score"),
  "score.priority": ml("优先分", "優先スコア", "Priority score"),
  "score.suitability": ml("适宜分", "適合性スコア", "Suitability score"),
  "score.joint": ml("联合分", "統合スコア", "Joint score"),
  "score.delivery": ml("交付分", "デリバリースコア", "Delivery score"),
  "score.opportunity": ml("机会分", "機会スコア", "Opportunity score"),
  "score.action": ml("行动分", "アクションスコア", "Action score"),
  "score.changePercentile": ml("变化分位", "変化パーセンタイル", "Change percentile"),
  "score.conflicts": ml("冲突数", "競合数", "Conflict count"),
  "field.queueDetail": ml("队列详情", "キュー詳細", "Queue details"),
  "field.cosineChange": ml("余弦变化", "コサイン変化", "Cosine change"),
  "field.embeddingChange": ml("嵌入变化", "埋め込み変化", "Embedding change"),
  "field.vectorPreview": ml("向量预览", "ベクトルプレビュー", "Vector preview"),
  "field.pvProxy": ml("光伏代理", "太陽光代理", "PV proxy"),
  "field.capacityProxy": ml("容量代理", "容量代理", "Capacity proxy"),
  "field.roadPriority": ml("道路优先度", "道路優先度", "Road priority"),
  "field.slope": ml("坡度", "傾斜", "Slope"),
  "field.maxSlope": ml("最大坡度", "最大傾斜", "Maximum slope"),
  "field.localRelief": ml("局部起伏", "局所起伏", "Local relief"),
  "field.elevation": ml("高程", "標高", "Elevation"),
  "field.road": ml("道路", "道路", "Road"),
  "field.transmission": ml("输电线", "送電線", "Transmission line"),
  "field.distRoad": ml("距道路", "道路距離", "Distance to road"),
  "field.distTransmission": ml("距输电线", "送電線距離", "Distance to line"),
  "field.distWater": ml("距水体", "水域距離", "Distance to water"),
  "field.length": ml("长度", "延長", "Length"),
  "field.highRiskBuildings": ml("高风险建筑", "高リスク建物", "High-risk buildings"),
  "field.serviceDemand": ml("服务需求", "サービス需要", "Service demand"),
  "field.officialStatus": ml("官方状态", "公式状態", "Official status"),
  "field.highRiskLinks": ml("高风险关联", "高リスク関連", "High-risk links"),
  "field.roadDistance": ml("道路距离", "道路距離", "Road distance"),
  "field.roofMatch": ml("屋顶匹配", "屋根マッチング", "Roof match"),
  "field.exposedBuildings": ml("暴露建筑", "曝露建物", "Exposed buildings"),
  "field.evidenceStatus": ml("证据状态", "証拠状態", "Evidence status"),
  "field.year": ml("年度", "年度", "Year"),
  "field.support": ml("支持率", "支持率", "Support"),
  "field.validPixels": ml("有效像素", "有効画素", "Valid pixels"),
  "field.semanticClass": ml("语义类别", "意味クラス", "Semantic class"),
  "field.notScored": ml("未计入评分", "スコア未使用", "Not scored"),
  "field.context": ml("上下文", "コンテキスト", "Context"),
  "field.kind": ml("类型", "種類", "Type"),
  "field.class": ml("等级", "区分", "Class"),
  "field.reasons": ml("原因", "理由", "Reasons"),
  "field.meanBuildingRisk": ml("平均建筑风险", "平均建物リスク", "Mean building risk"),
  "field.property": ml("属性值", "属性値", "Property value"),
};

/** Fields audit.js routed to the "cached GeoJSON property" record, whose
 * meaning varies by object type and whose licensing lives in docs/data. */
const PROPERTY_FIELDS: FieldKey[] = [
  "field.evidenceStatus",
  "field.year",
  "field.kind",
  "field.class",
  "field.support",
  "field.notScored",
  "field.validPixels",
  "field.semanticClass",
  "field.reasons",
  "field.highRiskBuildings",
  "field.exposedBuildings",
  "field.serviceDemand",
  "field.meanBuildingRisk",
];

const GEOSPATIAL_FIELDS: FieldKey[] = [
  "field.slope",
  "field.maxSlope",
  "field.localRelief",
  "field.elevation",
  "field.road",
  "field.transmission",
  "field.distRoad",
  "field.distTransmission",
  "field.distWater",
  "field.length",
];

function scoreFormula(key: FieldKey, props: FeatureProperties, value: string | number): AuditRecord | null {
  const title = FIELD_LABELS[key];
  if (key === "score.risk") {
    return calculation(
      title,
      value,
      "round(0.55×slope + 0.30×relief + 0.15×low-point)",
      `0.55×${props.slope_component} + 0.30×${props.relief_component} + 0.15×${props.low_point_component} = ${value}`,
      "GSI DEM5A → slope/relief/low-point components",
      ml("启发式相对分，不是灾害发生概率。", "ヒューリスティックな相対スコアで、災害発生確率ではありません。", "A heuristic relative score, not a hazard probability."),
    );
  }
  if (key === "score.priority") {
    return calculation(
      title,
      value,
      "round(0.45×terrain + 0.25×exposure + 0.20×criticality + 0.10×low-point)",
      `0.45×${props.terrain_component} + 0.25×${props.exposure_component} + 0.20×${props.criticality_component} + 0.10×${props.lowpoint_component} = ${value}`,
      "GSI DEM5A + OSM roads/buildings → TerrAI components",
      ml("用于巡检排序，不是道路中断概率。", "点検順位付け用で、道路寸断確率ではありません。", "Used to prioritize inspections, not to predict road failure probability."),
    );
  }
  if (key === "score.suitability") {
    return calculation(
      title,
      value,
      "round(0.35×slope + 0.25×grid + 0.20×access + 0.10×setback + 0.10×land)",
      `0.35×${props.slope_component} + 0.25×${props.grid_component} + 0.20×${props.access_component} + 0.10×${props.setback_component} + 0.10×${props.land_component} = ${value}`,
      "GSI DEM5A + OSM context → TerrAI components",
      ml(
        "未包含地权、农地转用、生态许可和正式并网。",
        "所有権、農地転用、環境許可、正式な系統接続は含みません。",
        "Ownership, farmland conversion, environmental permitting and formal grid connection are not included.",
      ),
    );
  }
  if (key === "score.joint" && props.hub_score !== undefined) {
    return calculation(
      title,
      value,
      "round(0.30×PV + 0.25×access + 0.35×community need + 0.10×site safety)",
      `0.30×${props.pv_component} + 0.25×${props.access_component} + 0.35×${props.community_need_component} + 0.10×${props.site_safety_component} = ${value}`,
      "Building footprint + road priority + 150 m demand + building risk",
      ml(
        "候选建筑不一定是公共设施，屋顶与服务能力需现场确认。",
        "候補建物が公共施設とは限らず、屋根とサービス能力は現地確認が必要です。",
        "A candidate building is not necessarily a public facility; roof and service capacity require field verification.",
      ),
    );
  }
  if (key === "score.joint" && props.compound_score !== undefined) {
    const demand = Math.min(100, (Number(props.joint_high_risk_buildings) / 8) * 100);
    return calculation(
      title,
      value,
      "round(0.45×road priority + 0.35×high-risk demand + 0.20×mean building risk)",
      `0.45×${props.priority_score} + 0.35×${demand.toFixed(1)} + 0.20×${props.joint_average_building_risk} = ${value}`,
      "Road priority + buildings within 55 m",
      ml(
        "同一建筑可能关联多条道路，不能把关联数当作独立人口。",
        "同一建物が複数道路に紐づく場合があり、関連件数を独立人口とは扱えません。",
        "A building may link to multiple roads; link counts are not unique people.",
      ),
    );
  }
  if (key === "score.delivery") {
    return calculation(
      title,
      value,
      "round(0.45×suitability + 0.20×slope + 0.20×access + 0.15×grid)",
      `0.45×${props.score} + 0.20×${props.slope_component} + 0.20×${props.access_component} + 0.15×${props.grid_component} = ${value}`,
      "Solar suitability + engineering access components",
      ml(
        "公开电网信号是区域门槛，不在本分数中按宗地分配。",
        "公開系統情報は地域ゲートであり、このスコアでは筆単位に配分していません。",
        "The public grid signal is a regional gate and is not allocated parcel-by-parcel in this score.",
      ),
    );
  }
  if (key === "score.opportunity") {
    return calculation(
      title,
      value,
      "round(0.30×site safety + 0.25×access + 0.30×community need + 0.15×energy)",
      `0.30×${props.site_safety_component} + 0.25×${props.access_component} + 0.30×${props.community_need_component} + 0.15×${props.energy_component} = ${value}`,
      "Official facility + matched roof + road + 250 m demand",
      ml(
        "设施位置是官方数据；屋顶匹配、容量和机会分是PoC代理。",
        "施設位置は公式データですが、屋根マッチング、容量、機会スコアはPoC代理です。",
        "Facility location is official; roof matching, capacity and opportunity score are PoC proxies.",
      ),
    );
  }
  if (key === "score.action") {
    if (props.building_count !== undefined) {
      return calculation(
        title,
        value,
        "round(0.45×high-risk share×3 + 0.35×max road priority + 0.20×facility gap)",
        `high share ${props.high_risk_share_pct}% · road ${props.max_road_priority} · facilities ${props.official_facilities} → ${value}`,
        "100–300 m zone aggregation",
        ml(
          "决策区为启发式邻域，不是行政区或法定服务区。",
          "意思決定ゾーンはヒューリスティックな近傍で、行政区や法定サービス圏ではありません。",
          "The decision zone is a heuristic neighborhood, not an administrative or statutory service area.",
        ),
      );
    }
    return calculation(
      title,
      value,
      "round(0.65×mean solar score + 0.35×preferred-cell share)",
      `mean ${props.mean_solar_score} · preferred ${props.preferred_cells}/${props.solar_cells} → ${value}`,
      "100–300 m solar zone aggregation",
      ml(
        "区域聚合用于排队，不替代宗地尽调。",
        "ゾーン集計は順位付け用で、筆単位のデューデリジェンスを代替しません。",
        "Zone aggregation supports prioritization and does not replace parcel due diligence.",
      ),
    );
  }
  return null;
}

export function field(key: FieldKey, value: string | number, props: FeatureProperties = {}): AuditRecord {
  const scored = scoreFormula(key, props, value);
  if (scored) return scored;
  const title = FIELD_LABELS[key];

  if (key === "field.queueDetail") {
    return calculation(
      title,
      value,
      "format(selected object fields for the active analysis queue)",
      String(value),
      ml(
        "当前对象的本地 GeoJSON 属性 → 排序队列摘要",
        "現在対象のローカル GeoJSON 属性 → 優先順位キュー要約",
        "Current object's local GeoJSON properties → ranked-queue summary",
      ),
      ml(
        "摘要会随分析模块改变；其中的派生分数可通过右侧分数单独查看完整公式。",
        "要約は分析モジュールにより変わります。派生スコアの完全な式は右側のスコアから個別に確認できます。",
        "The summary changes with the analysis module. Open the score at right to inspect the full formula for a derived score.",
      ),
    );
  }

  if (
    key === "score.changePercentile" ||
    key === "field.cosineChange" ||
    key === "field.embeddingChange" ||
    key === "field.vectorPreview"
  ) {
    return model(
      title,
      value,
      "AlphaEarth Foundations v2.1 / Satellite Embedding V1",
      `2023/2024 64D vectors → ${text(title, "en")}`,
      ml(
        "无逐像素置信区间；支持率为数据覆盖，不是预测置信度。",
        "画素別信頼区間はありません。支持率はデータ被覆率で、予測信頼度ではありません。",
        "No per-pixel confidence interval is available. Support percentage is data coverage, not predictive confidence.",
      ),
      ml(
        "不进入业务评分；需要本地标签hold-out验证。",
        "業務スコアには未使用。ローカルラベルでのhold-out検証が必要です。",
        "Excluded from business scores; local-label hold-out validation is required.",
      ),
      "Google Satellite Embedding V1 via Source Cooperative",
      "https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL",
    );
  }

  if (key === "field.pvProxy" || key === "field.capacityProxy") {
    return calculation(
      title,
      value,
      "roof footprint × 0.60 × 0.20 kWp/m² = footprint × 0.12",
      `${props.footprint_m2 ?? props.matched_roof_area_m2 ?? "—"} m² × 0.12 = ${value}`,
      "OpenStreetMap building footprint → TerrAI proxy",
      ml("未验证屋顶结构、朝向和遮挡。", "屋根構造、方位、日影は未検証です。", "Roof structure, orientation and shading are unverified."),
    );
  }

  if (key === "score.conflicts") {
    const reasons = Array.isArray(props.reject_reasons) ? props.reject_reasons : [];
    return calculation(
      title,
      value,
      "count(triggered exclusion rules)",
      `${reasons.join(" + ") || "no triggered rule"} → ${value}`,
      "Slope, road, transmission, building and water-setback rules",
      ml(
        "规则冲突不等于法律上绝对不可开发；仍需主管机关和项目级尽调。",
        "ルール競合は法的な絶対開発不可を意味しません。行政確認と案件別デューデリジェンスが必要です。",
        "A rule conflict is not absolute legal infeasibility; authority checks and project-level due diligence remain necessary.",
      ),
    );
  }

  if (key === "field.roadPriority") {
    return raw(
      title,
      value,
      "Nearest linked road in data/yokohama/road_priority.geojson",
      "priority_score",
      "current Demo snapshot",
      "data/joint/resilience_hubs.geojson",
      ml(
        "这是最近道路已计算的巡检优先分；在本对象中作为输入，不重复计算。",
        "最近接道路で既に計算された点検優先スコアを入力として使用し、ここでは再計算しません。",
        "This is the already-computed inspection priority of the nearest road, reused as an input rather than recomputed here.",
      ),
    );
  }

  if (GEOSPATIAL_FIELDS.includes(key)) {
    return calculation(
      title,
      value,
      "geospatial measurement(source geometry / raster)",
      `${text(title, "en")} = ${value}`,
      "GSI DEM5A and/or OpenStreetMap geometry",
      ml(
        "PoC采用局部平面距离近似；生产版应使用适当投影并记录误差。",
        "PoCは局所平面距離近似を使用。製品版では適切な投影と誤差記録が必要です。",
        "The PoC uses a local planar approximation; production should use a suitable projection and record error.",
      ),
    );
  }

  if (PROPERTY_FIELDS.includes(key)) {
    return raw(
      title,
      value,
      "Local cached GeoJSON property",
      text(title, "en"),
      "current Demo snapshot",
      "data/**/*.geojson",
      ml(
        "字段含义和来源随对象类型而异；完整许可见 docs/data/README.zh.md。",
        "フィールドの意味と出典は対象種別で異なります。ライセンス詳細は docs/data/README.ja.md を参照してください。",
        "Field meaning and lineage vary by object type; see docs/data/README.md for licensing.",
      ),
    );
  }

  return raw(
    title,
    value,
    "Local cached GeoJSON property",
    text(title, "en"),
    "current Demo snapshot",
    "data/**/*.geojson",
    ml(
      "该值用于筛查展示，不构成工程、法律或投资承诺。",
      "スクリーニング表示用で、工学・法務・投資上の保証ではありません。",
      "This value supports screening and is not an engineering, legal or investment commitment.",
    ),
  );
}

export type ModuleName =
  | "overview"
  | "evidence"
  | "slope"
  | "roads"
  | "facilities"
  | "solar"
  | "joint"
  | "development";

export function queueScore(
  moduleName: ModuleName,
  view: string,
  score: string | number,
  props: FeatureProperties,
): AuditRecord {
  const key: FieldKey =
    moduleName === "slope" ? "score.risk"
    : moduleName === "roads" ? "score.priority"
    : moduleName === "solar" ? "score.suitability"
    : moduleName === "facilities" ? "score.opportunity"
    : moduleName === "evidence" ? "score.changePercentile"
    : moduleName === "joint" ? "score.joint"
    : moduleName === "development" ? (view === "constraints" ? "score.conflicts" : "score.delivery")
    : view === "urban" ? "score.joint"
    : "score.delivery";
  return field(key, score, props);
}
