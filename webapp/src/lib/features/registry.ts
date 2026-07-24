/**
 * The foundation-layer registry: every on-demand foundation feature layer the
 * product can show as an overlay, described as data.
 *
 * Adding a layer is a registry entry plus a data card — never a code change
 * in the layer builder. A foundation layer is evidence shown, never evidence
 * scored: nothing here may enter a score, queue or recommendation, and the
 * registry test pins the key set to the on-demand feature collections so an
 * analytical dataset cannot drift in.
 *
 * Attribution is not optional: several MLIT sources require attribution or
 * carry Survey Act considerations, and OSM is ODbL. An entry without
 * attribution must not render — `renderableFoundationLayers` enforces that,
 * and a test fails on a registry entry that lacks one.
 *
 * The 3D asset manifests (`uc24_16_nihonbashi`, `uc24_13_sapporo`,
 * `kunijibanBoreholes`) are deliberately absent: they are manifests over 3D
 * Tiles and Parquet, not feature collections, and belong to the underground
 * stages.
 */

import { ml, type Localized } from "../audit";
import type { MessageKey } from "../i18n/i18n.svelte";
import type { Bounds } from "./windowed";

/** The MLIT acquisition window — mainland Kanto (Tokyo, Kanagawa, Chiba,
 *  Saitama) — from the pipeline region registry's `MLIT_ACQUISITION_BOUNDS`
 *  (`terrai_spatial/pipeline/regions.py`). Sheet-based sources (the 1:50k
 *  land classification, the 2011 land history) have sheet-shaped gaps inside
 *  it; a window there truthfully reports zero features. */
const MLIT_EXTENTS: Bounds[] = [[138.65, 34.85, 140.95, 36.3]];
const SAPPORO_EXTENT: Bounds[] = [[141.349592632, 43.054916388, 141.356913521, 43.070980841]];

const MLIT_KSJ_ATTRIBUTION = "「国土数値情報」（国土交通省）を加工して作成";
const MLIT_KOKJO_ATTRIBUTION = "国土交通省 国土調査（土地分類調査・水害統計調査）を加工して作成";

const NOT_FOR_SCORING = ml(
  "基础图层仅作证据展示，不进入任何评分、排序或推荐。",
  "基盤レイヤは証拠の表示のみで、スコア・ランキング・推奨には入りません。",
  "Foundation layers are evidence shown, never scored, ranked or recommended.",
);

function limitations(zh: string, ja: string, en: string): Localized {
  return ml(`${zh} ${NOT_FOR_SCORING.zh}`, `${ja} ${NOT_FOR_SCORING.ja}`, `${en} ${NOT_FOR_SCORING.en}`);
}

export interface FoundationLayerEntry {
  key: string;
  name: MessageKey;
  geometry: "polygon" | "line" | "point" | "mixed";
  minZoom: number;
  extents: Bounds[];
  /** Source-stated attribution; an entry without one must not render. */
  attribution: string;
  /** The licence as the source states it, shown verbatim. */
  license: string;
  /** The source's own timestamp, verbatim — a 2021 mesh over a 2024 basemap
   *  must say 2021 on screen. Per-feature values are shown at click time. */
  sourceUpdatedAt: string;
  limitations: Localized;
  /** Per-layer window budget for denser-but-simpler features. */
  windowLimit?: number;
}

export const FOUNDATION_LAYERS: FoundationLayerEntry[] = [
  {
    key: "landClassification50k",
    name: "fl.landClassification50k",
    geometry: "polygon",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KOKJO_ATTRIBUTION,
    license: "Public Data License 1.0; Survey Act and redistribution cautions apply",
    sourceUpdatedAt: "current download; map-sheet vintage varies",
    limitations: limitations(
      "5万分の1土地分类图幅年代不一，不适用于工程判断。",
      "5万分の1土地分類は図幅により年代が異なり、工学的判断には使えません。",
      "The 1:50k land classification's map-sheet vintages vary; not for engineering judgement.",
    ),
  },
  {
    key: "floodHistory",
    name: "fl.floodHistory",
    geometry: "polygon",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KOKJO_ATTRIBUTION,
    license: "Public Data License 1.0; attribution/edit notice and redistribution cautions apply",
    sourceUpdatedAt: "2025-03",
    limitations: limitations(
      "历史浸水范围不等于未来风险边界。",
      "過去の浸水実績は将来のリスク境界ではありません。",
      "Historic inundation extents are not future risk boundaries.",
    ),
  },
  {
    key: "landHistory",
    name: "fl.landHistory",
    geometry: "mixed",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KOKJO_ATTRIBUTION,
    license: "Public Data License 1.0; Survey Act and redistribution cautions apply",
    sourceUpdatedAt: "2011 survey package",
    limitations: limitations(
      "2011年调查包；地形改变可能早于或晚于图示。",
      "2011年調査パッケージ。地形改変は図示より前後する可能性があります。",
      "A 2011 survey package; land modification may pre- or post-date what is drawn.",
    ),
  },
  {
    key: "landslideWarning",
    name: "fl.landslideWarning",
    geometry: "polygon",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0 with provider-specific partial restrictions",
    sourceUpdatedAt: "2025-08-01",
    limitations: limitations(
      "警戒区域边界以主管机关公示为准。",
      "警戒区域の境界は所管機関の公示が正です。",
      "Warning-zone boundaries defer to the issuing authority's publication.",
    ),
  },
  {
    key: "multistageFlood",
    name: "fl.multistageFlood",
    geometry: "polygon",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0",
    sourceUpdatedAt: "2025 release",
    limitations: limitations(
      "多段浸水想定为模型假设下的产物，不是实测。",
      "多段浸水想定はモデル前提下の産物で、実測ではありません。",
      "Multi-stage flood assumptions are model products, not observations.",
    ),
  },
  {
    key: "publishedLandPrice",
    name: "fl.publishedLandPrice",
    geometry: "point",
    minZoom: 15,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0",
    sourceUpdatedAt: "2026-01-01",
    limitations: limitations(
      "公示地价为标准地评估值，非成交价。",
      "公示地価は標準地の評価額で、取引価格ではありません。",
      "Published land prices are appraisal values for standard lots, not transactions.",
    ),
  },
  {
    key: "embankmentRegulation",
    name: "fl.embankmentRegulation",
    geometry: "polygon",
    minZoom: 15,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0; regulatory boundaries must not be modified",
    sourceUpdatedAt: "2025-07-18",
    limitations: limitations(
      "规制区域边界禁止修改；以行政公示为准。",
      "規制区域の境界は改変禁止で、行政の公示が正です。",
      "Regulatory boundaries must not be modified; the authority's publication governs.",
    ),
  },
  {
    key: "railway",
    name: "fl.railway",
    geometry: "line",
    minZoom: 14,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0",
    sourceUpdatedAt: "2025-12-31",
    limitations: limitations(
      "铁路数据为年度整备快照。",
      "鉄道データは年次整備のスナップショットです。",
      "Railway data is an annually maintained snapshot.",
    ),
  },
  {
    key: "landUseMesh",
    name: "fl.landUseMesh",
    geometry: "polygon",
    minZoom: 16,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "Public Data License 1.0",
    sourceUpdatedAt: "2021",
    limitations: limitations(
      "2021年土地利用细分网格；叠于新底图时年代差即在此。",
      "2021年の土地利用細分メッシュ。新しい基図に重ねる際の年差はここにあります。",
      "A 2021 land-use mesh; the vintage gap over a newer basemap lives here.",
    ),
  },
  {
    key: "prefecturalLandPrice",
    name: "fl.prefecturalLandPrice",
    geometry: "point",
    minZoom: 15,
    extents: MLIT_EXTENTS,
    attribution: MLIT_KSJ_ATTRIBUTION,
    license: "CC BY 4.0",
    sourceUpdatedAt: "2025-07-01",
    limitations: limitations(
      "都道府县地价调查为标准地评估值。",
      "都道府県地価調査は基準地の評価額です。",
      "Prefectural land-price survey values are appraisals for standard lots.",
    ),
  },
  // osmBuildings retired (osm-basemap-tiles PR5): the Kanto OSM footprints render
  // as part of the merged self-hosted building PMTiles (a MapLibre layer,
  // clickable at inspection zoom, BUILDING_CLICK_MIN_ZOOM), not a windowed
  // store collection.
  {
    key: "osmSapporoUndergroundAccess",
    name: "fl.osmSapporoUndergroundAccess",
    geometry: "mixed",
    minZoom: 14,
    extents: SAPPORO_EXTENT,
    attribution: "© OpenStreetMap contributors",
    license: "Open Database License (ODbL) 1.0",
    sourceUpdatedAt: "community database; per-feature timestamps",
    limitations: limitations(
      "社区数据的完整性与现势性无保证；无通行限制标注不等于可通行。",
      "コミュニティデータの完全性・現勢性は保証されません。制限タグが無いことは通行可の証明ではありません。",
      "Community completeness and freshness are not guaranteed; an absent access tag is not proof of access.",
    ),
  },
];

export function foundationLayer(key: string): FoundationLayerEntry | undefined {
  return FOUNDATION_LAYERS.find((entry) => entry.key === key);
}

/** A layer whose registry entry lacks attribution must not render. */
export function renderableFoundationLayers(entries: FoundationLayerEntry[] = FOUNDATION_LAYERS): FoundationLayerEntry[] {
  return entries.filter((entry) => entry.attribution.trim().length > 0);
}
