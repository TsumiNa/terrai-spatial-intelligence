# Full Pipeline Run Report — Borehole Integration

**Run date**: 2026-06-27 (re-run 11:26 → 13:04, adds N-values / water level /
color) · **Pipeline**: [fetch_and_integrate_parquet.py](../fetch_and_integrate_parquet.py)

---

## 1. Summary

The hybrid XML + VLM integration pipeline processed the full kunijiban borehole
set and produced **three** Parquet datasets (boreholes, layers, SPT) plus an
error log. **12,067 of 12,077 boreholes integrated successfully (99.92%)**; 10
failed (6 data-poor records with no usable XML/PDF, 4 malformed VLM JSON
responses). Beyond stratigraphy it now extracts **239,137 SPT N-value tests**,
water levels, and per-layer color/observation/density. Estimated VLM cost ≈ **$5**.
No reliability safeguard stalled the run.

## 2. Run metrics

| Metric                  | Value                                   |
| :---------------------- | :-------------------------------------- |
| Boreholes attempted     | 12,077 (of 12,081; 4 had neither URL)   |
| Successfully integrated | **12,067**                              |
| Failed                  | 10 (6 data-poor + 4 VLM JSON)           |
| Total strata (layers)   | 122,693 (mean 10.2 / borehole, max 104) |
| **SPT N-value tests**   | **239,137**                             |
| Wall-clock              | ~1 h 38 m, 4 worker threads             |

## 3. Data-source breakdown

| `data_source`   | Count | Mean layers | SPT borings | Meaning                                          |
| :-------------- | ----: | ----------: | ----------: | :----------------------------------------------- |
| `raw_xml`       | 6,462 |        12.5 |       5,669 | Native JGS XML (authoritative)                   |
| `pdf_vlm`       | 5,241 |         8.1 |       4,775 | VLM-reconstructed from a 柱状図 PDF              |
| `pdf_vlm_empty` |   364 |         0.0 |           0 | 土性図 / ≤1-layer sheet — no usable stratigraphy |

The 364 zero-layer records correspond **exactly** to `pdf_vlm_empty`, confirming
the validity gate flags non-stratigraphic sheets consistently. To work only with
usable geology, filter `data_source != 'pdf_vlm_empty'`.

## 4. Source DTD versions

| DTD              | Count | Notes                                       |
| :--------------- | ----: | :------------------------------------------ |
| `4.00_Synthetic` | 5,605 | All VLM-derived (5,241 + 364)               |
| `2.10`           | 3,466 | Older format — `土質岩種区分` layers        |
| `4.00`           | 1,899 | `工学的地質区分名現場土質名` layers         |
| `3.00`           | 1,071 | `岩石土区分` rock columns                   |
| `2.01`           |    26 | Additional legacy version, parsed correctly |

Without the multi-version schema table, ~73% of XML boreholes (everything except
`4.00`) would have parsed to zero layers. See report §6.4 of
[Geotechnical_VLM_Evaluation_Report.md](Geotechnical_VLM_Evaluation_Report.md).

## 5. Data quality & field coverage

| Check / field                | Result                                                                            |
| :--------------------------- | :-------------------------------------------------------------------------------- |
| Duplicate ids                | 0 (12,067 unique)                                                                 |
| Missing `total_depth`        | **0** (header tag → CSV `boring_length` → deepest layer)                          |
| Missing latitude / longitude | 0 / 0                                                                             |
| Missing `elevation`          | 86 (~0.7%; absent in both XML and CSV)                                            |
| Boreholes with SPT           | 10,444 / 12,067 (87%) — raw_xml 5,669, pdf_vlm 4,775                              |
| `water_level` populated      | 6,030 (50%) — raw_xml 90%, pdf_vlm only 4% (VLM rarely reads it; CSV often blank) |
| `layer_color` populated      | 71,757 strata (58%) — XML-only                                                    |
| `layer_observation`          | 45,091 (37%) — XML-only, often sparse                                             |
| `layer_density`              | 8,220 (7%) — XML-only, sparse                                                     |

**SPT caveat**: `n_value` ranges 0–794 (mean 18.6). N > 50 is ~1.0% (legitimate
refusal/hard-ground); only 3 tests exceed 100 and a single 794 is an apparent
source-data outlier. Consumers may wish to cap/flag extreme N.

## 6. Failures (10)

- **6** in range `511179`–`511186`: *"No usable data — XML unreachable/empty and
  no PDF."* Data-poor archival records (XML has no layers, no soilmap PDF). Not a
  pipeline fault.
- **4** VLM JSON errors (`118635, 130581, 131189, 131556`): truncated / empty VLM
  responses — the longer output (now incl. the SPT array) occasionally exceeds a
  clean JSON envelope. 0.08% of VLM borings. **This run predated the JSON-retry**;
  the retry-once + `max_tokens=8000` guard was added afterward (now in the code),
  and should reclaim most of these on the next re-run.

Logged in
[../notebooks/processed/batch_integration_errors.csv](../notebooks/processed/batch_integration_errors.csv).

## 7. Output artifacts

### `notebooks/processed/integrated_boreholes.parquet` (nested, 12,067 rows)

One row per borehole. Columns: `id, location, data_source, dtd_version,
boring_id, boring_id_old, survey_name, client_name, approval_code, project_name,
investigation_name, boring_name, latitude, longitude, elevation,
elevation_source, total_depth, water_level, layers, spt, xml_url, raw_xml`.
`layers` is a list of `{base_depth, name, symbol, color, observation, density,
category}`; `spt` is a list of `{depth, n_value, category, soil_name}`; `raw_xml`
retains the original (or synthetic) XML for auditing.

### `notebooks/processed/integrated_borehole_layers.parquet` (flat, 122,693 rows)

One row per stratum (exploded), without `raw_xml` — ideal for SQL/analytics.
Columns: `id, location, data_source, dtd_version, boring_id, project_name,
boring_name, latitude, longitude, elevation, elevation_source, layer_index,
base_depth, layer_name, layer_symbol, layer_category, layer_color,
layer_observation, layer_density, xml_url`.

### `notebooks/processed/integrated_borehole_spt.parquet` (flat, 239,137 rows)

One row per SPT test (depths differ from layer boundaries). Columns:
`id, location, data_source, boring_id, boring_name, latitude, longitude,
elevation, depth, n_value, layer_category, layer_name`. Each test is depth-matched
to its containing soil layer, so the soil type travels with the N-value.

### Derived fields

- **`category` / `layer_category`** — unified soil class mapped from the
  Japanese `layer_name` (name-based; dominant = rightmost noun). One of:
  `fill, topsoil, clay, silt, sand, gravel, cobble_boulder, organic, volcanic,
  rock, asphalt_concrete, improved, waste, other, unknown`. **~99% map to a
  real class**; for the ~1% `other`/`unknown`, fall back to `layer_name`. Raw
  `layer_name` / `layer_symbol` are never modified.
- **`elevation_source`** — provenance of the elevation, the handle for
  user-side datum normalisation (the JGS XML carries **no** geodetic datum tag,
  and VLM-read harbour elevations may use a local datum e.g. Y.P.):
  `xml` (6,376) · `vlm` (5,601) · `csv` (4) · `none` (86). True datum
  reconciliation (T.P./Y.P.) is intentionally left to the consumer.

Usage examples: [../notebooks/usage_demo.ipynb](../notebooks/usage_demo.ipynb).

## 8. Recommendations / follow-ups

1. **Filter `pdf_vlm_empty`** (364) out of geological analysis; they carry valid
   metadata/coordinates but no stratigraphy.
2. **Optional physical-property pass**: the 364 土性図 sheets are the only source
   of ρt/ρs/WL/Wp/Wn (absent from XML). If needed, run an incremental
   `gemini-3.5-flash` pass over them (~$85 for the wider set), treating marker
   readings as approximate (see eval report §6.6–6.7).
3. **10 failed ids**: 6 have no recoverable source (leave/drop). The 4 VLM-JSON
   failures occurred before the retry guard existed; the code now retries once
   with `max_tokens=8000`, so a targeted re-run of just those 4 (or the next full
   run) should reclaim most. If any persist, escalate to more retries or a
   chunked-output strategy.

---

## Appendix A — Parquet field reference

### A.1 `integrated_boreholes.parquet` (nested · one row per borehole)

| Column               | Type               | Description                                                                                                                |
| :------------------- | :----------------- | :------------------------------------------------------------------------------------------------------------------------- |
| `id`                 | int64              | Kunijiban borehole id (unique key)                                                                                         |
| `location`           | str                | Area label (e.g. Yokohama, Kawasaki)                                                                                       |
| `data_source`        | str (enum)         | Provenance — see A.4                                                                                                       |
| `dtd_version`        | str                | Source JGS DTD (`2.10`/`3.00`/`4.00`/`2.01`) or `4.00_Synthetic` (VLM)                                                     |
| `boring_id`          | str                | JGS boring id (new schema)                                                                                                 |
| `boring_id_old`      | str                | Legacy boring id                                                                                                           |
| `survey_name`        | str                | Survey/investigation name (CSV)                                                                                            |
| `client_name`        | str                | Commissioning client (CSV)                                                                                                 |
| `approval_code`      | str                | Approval code (CSV)                                                                                                        |
| `project_name`       | str                | Project name (from XML, or synthetic label for VLM)                                                                        |
| `investigation_name` | str                | Investigation name                                                                                                         |
| `boring_name`        | str                | Borehole name (may be a default for unnamed records)                                                                       |
| `latitude`           | float              | WGS84 latitude (decimal)                                                                                                   |
| `longitude`          | float              | WGS84 longitude (decimal)                                                                                                  |
| `elevation`          | float              | Ground-surface elevation (m); datum **not** normalized                                                                     |
| `elevation_source`   | str (enum)         | Elevation provenance — see A.5                                                                                             |
| `total_depth`        | float              | Total drilled length (m); header tag → CSV → deepest layer                                                                 |
| `water_level`        | float              | Borehole water level (m); `孔内水位` → CSV `boring_waterlevel`                                                             |
| `layers`             | list&lt;struct&gt; | Stratigraphy: `{base_depth, name, symbol, color, observation, density, category}`                                          |
| `spt`                | list&lt;struct&gt; | SPT N-values: `{depth: float, n_value: int, category: str, soil_name: str}` — each test carries the soil layer it falls in |
| `xml_url`            | str                | Source XML URL (empty for PDF-only)                                                                                        |
| `raw_xml`            | str                | Original (or synthetic) XML, retained for audit                                                                            |

Layer struct fields: `color` (色調), `observation` (観察記事), `density`
(相対密度稠度) are **XML-only** (empty on VLM layers); `category` — see A.3.

### A.2 `integrated_borehole_layers.parquet` (flat · one row per stratum)

| Column              | Type       | Description                                               |
| :------------------ | :--------- | :-------------------------------------------------------- |
| `id`                | int64      | Borehole id (foreign key to nested)                       |
| `location`          | str        | Area label                                                |
| `data_source`       | str (enum) | Provenance — see A.4                                      |
| `dtd_version`       | str        | Source DTD version                                        |
| `boring_id`         | str        | JGS boring id                                             |
| `project_name`      | str        | Project name                                              |
| `boring_name`       | str        | Borehole name                                             |
| `latitude`          | float      | Latitude (decimal)                                        |
| `longitude`         | float      | Longitude (decimal)                                       |
| `elevation`         | float      | Borehole ground elevation (m)                             |
| `elevation_source`  | str (enum) | Elevation provenance — see A.5                            |
| `layer_index`       | int        | 1-based layer order within the borehole                   |
| `base_depth`        | float      | Bottom depth of the layer (m below collar)                |
| `layer_name`        | str        | Raw Japanese soil/rock name (authoritative)               |
| `layer_symbol`      | str        | Raw JGS symbol (only ~35% populated)                      |
| `layer_category`    | str (enum) | Unified soil class — see A.3                              |
| `layer_color`       | str        | 色調 colour (XML-only, ~58%)                              |
| `layer_observation` | str        | 観察記事 observation note (XML-only, ~37%)                |
| `layer_density`     | str        | 相対密度稠度 relative density/consistency (XML-only, ~7%) |
| `xml_url`           | str        | Source XML URL                                            |

### A.2b `integrated_borehole_spt.parquet` (flat · one row per SPT test)

| Column                   | Type       | Description                                                         |
| :----------------------- | :--------- | :------------------------------------------------------------------ |
| `id`                     | int64      | Borehole id (foreign key)                                           |
| `location`               | str        | Area label                                                          |
| `data_source`            | str (enum) | Provenance — see A.4                                                |
| `boring_id`              | str        | JGS boring id                                                       |
| `boring_name`            | str        | Borehole name                                                       |
| `latitude` / `longitude` | float      | Coordinates                                                         |
| `elevation`              | float      | Borehole ground elevation (m)                                       |
| `depth`                  | float      | Test start depth (m below collar)                                   |
| `n_value`                | int        | SPT N (合計打撃回数); see §5 SPT caveat on extremes                 |
| `layer_category`         | str        | Unified soil class of the layer containing the test (100% assigned) |
| `layer_name`             | str        | Raw Japanese name of the containing layer                           |

239,137 tests · raw_xml exact integers · pdf_vlm read from the N値 chart
(approximate). `layer_category` / `layer_name` are derived by depth-matching each
test to its soil layer, so N-values stay associated with the soil without a join.

### A.3 Soil `category` / `layer_category` mapping

Mapped from `layer_name` (names ~100% populated vs symbols ~35%). **Genetic/PRIMARY
types are matched first** (override); for natural soils the **dominant material is
the rightmost keyword** in the name (砂質シルト → silt; 礫混じり砂 → sand).
~99% of strata map to a real class; `other`/`unknown` (~1%) → fall back to `layer_name`.

| category           | matched keywords (substring)                               | precedence           |
| :----------------- | :--------------------------------------------------------- | :------------------- |
| `asphalt_concrete` | アスファルト, ｱｽﾌｧﾙﾄ, コンクリート, 舗装                   | primary              |
| `waste`            | 廃棄物                                                     | primary              |
| `fill`             | 埋土, 盛土, 客土, 埋立, 盛り土, 覆土                       | primary              |
| `improved`         | 改良土, 改良                                               | primary              |
| `topsoil`          | 表土, 表層                                                 | primary              |
| `organic`          | 腐植, 腐食, 泥炭, 有機, 黒ぼく, 黒ボク, ヘドロ, 黒泥, 浮泥 | primary              |
| `volcanic`         | 火山灰, スコリア, 軽石, 浮石, ローム                       | primary              |
| `rock`             | 岩, チャート, マサ, まさ, 頁, 片麻, 花崗                   | primary              |
| `cobble_boulder`   | 玉石, 転石, コブル, ボルダー, 巨礫                         | material (rightmost) |
| `gravel`           | 礫, れき, 砂利, 砕石, ガラ                                 | material (rightmost) |
| `sand`             | 砂                                                         | material (rightmost) |
| `silt`             | シルト, 沈泥, ｼﾙﾄ                                          | material (rightmost) |
| `clay`             | 粘土, 粘性土, 粘                                           | material (rightmost) |
| `other`            | (name present but no keyword matched)                      | —                    |
| `unknown`          | (blank name)                                               | —                    |

Distribution (122,693 strata): sand 48,119 · silt 31,650 · fill 13,487 · clay 10,891 ·
gravel 7,635 · rock 3,247 · organic 2,640 · topsoil 1,263 · volcanic 1,121 ·
asphalt_concrete 906 · other 704 · unknown 468 · improved 278 · cobble_boulder 211 · waste 73.

### A.4 `data_source` values

| value           | count | meaning                                          |
| :-------------- | ----: | :----------------------------------------------- |
| `raw_xml`       | 6,462 | Native JGS XML (authoritative)                   |
| `pdf_vlm`       | 5,241 | VLM-reconstructed from a 柱状図 PDF              |
| `pdf_vlm_empty` |   364 | 土性図 / ≤1-layer sheet — no usable stratigraphy |

### A.5 `elevation_source` values

| value  | count | meaning                                                          |
| :----- | ----: | :--------------------------------------------------------------- |
| `xml`  | 6,376 | From XML `孔口標高`                                              |
| `vlm`  | 5,601 | Read from PDF by the VLM (harbour records may use a local datum) |
| `csv`  |     4 | Back-filled from CSV `boring_elevation`                          |
| `none` |    86 | No elevation available                                           |

---

## Appendix B — JGS XML tag mapping by DTD version

Tag names differ across DTD versions; the parser tries each schema in order
(source of truth: `JGS_HEADER_TAGS` / `JGS_LAYER_SCHEMAS` in
[fetch_and_integrate_parquet.py](../fetch_and_integrate_parquet.py)).

### B.1 Stratigraphy (repeating layer container + sub-fields)

| Field           | DTD 2.10                     | DTD 3.00                | DTD 4.00                                                |
| :-------------- | :--------------------------- | :---------------------- | :------------------------------------------------------ |
| layer container | `土質岩種区分`               | `岩石土区分`            | `工学的地質区分名現場土質名`                            |
| base depth      | `土質岩種区分_下端深度`      | `岩石土区分_下端深度`   | `工学的地質区分名現場土質名_下端深度`                   |
| name            | `土質岩種区分_土質岩種区分1` | `岩石土区分_岩石土名`   | `工学的地質区分名現場土質名_工学的地質区分名現場土質名` |
| symbol          | `土質岩種区分_土質岩種記号1` | `岩石土区分_岩石土記号` | `工学的地質区分名現場土質名_…記号`                      |

(DTD `2.01` reuses the 2.10 schema.)

### B.2 Header fields (first non-empty tag wins)

| Logical field      | Tag(s) — by version where they differ        |
| :----------------- | :------------------------------------------- |
| project_name       | `事業工事名` (all)                           |
| investigation_name | `調査名` (all)                               |
| boring_name        | `ボーリング名` (all)                         |
| elevation          | `孔口標高` (all)                             |
| latitude           | `緯度_度` / `緯度_分` / `緯度_秒` (all)      |
| longitude          | `経度_度` / `経度_分` / `経度_秒` (all)      |
| total_depth        | `総削孔長` (4.00) · `総掘進長` (2.10 / 3.00) |

> No geodetic datum tag exists in any version — hence `elevation_source` (A.5)
> rather than a normalized datum. CSV fallbacks: `elevation ← boring_elevation`,
> `total_depth ← boring_length`.
