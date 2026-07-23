# 政府建筑数据源评估

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

面向自建 basemap 与局部 3D 工作模式的两个政府建筑数据源评估。二者均尚未接入;本文
把各源提供的内容、许可、覆盖以及在两种模式下的用法作为确定事实记录下来,使
`osm-basemap-tiles` 与 `local-3d-work-mode` 两个 refactor 能建立在确凿依据之上。

## 为什么是这两个源

OpenStreetMap 的建筑轮廓在密集城市很丰富(稳定 `osm_id`、建筑类型、偶有高度),但在
日本郊区与农村稀疏。只用 OSM 绘制时,OSM 薄的地方即便地面有建筑也会显得空。以下两个
政府源填补这一缺口,并各以不同方式补充真实高度。

## 基盤地図情報(国土地理院)

- **内容:** 国土地理院的国家测量基础数据。基本项目含建筑物(建築物外周线),为 2D 多边形。
- **覆盖:** 在都市计划区域及有人区网罗完整——郊区/农村远比 OSM 完整——仅在极端山间稀薄。
  全国范围。
- **格式 / 获取:** JPGIS GML(可导出 Shapefile),经基盤地図情報下载服务(需注册)。
- **属性:** 建筑外周线;**无高度**(2D),也无 OSM 式稳定社区 ID(自带 FGD 标识符)。
- **许可——决定性结论:** 基盤地図情報虽属基本測量成果,但国土地理院承認申請 Q&A
  **明确将其排除**在测量法申请要求之外(与地理院タイル一同)。下载它、加工成派生矢量
  瓦片并分发(含商用、离线)**无需测量法承認申请**,仅需出典表示 + 加工表示。与项目
  已在流式使用的地理院瓦片同一档。出典见文末。

## PLATEAU 建筑模型(国土交通省 Project PLATEAU)

- **内容:** 政府 3D 城市模型。建筑模型有 LOD1(带每栋实测高 `bldg:measuredHeight` 的
  体块)与 LOD2(屋顶形状),偶有 LOD4(BIM)。
- **覆盖:** **按市町村**发布。东京 23 区已全建模;从 2021 年 56 城扩展至 2025 年度末
  约 300 城。**不均匀**,存在未建模的市町村。
- **格式 / 获取:** CityGML(权威源)、3D Tiles(Cesium 渲染的格式)、FlatGeobuf/GeoJSON
  衍生,经 G空間情報センター(CKAN)——与项目 UC24 地下场景已用的同一通道。
- **属性:** `measuredHeight`(实高)、`usage`、`storeysAboveGround`,有记录时的
  `yearOfConstruction`(稀疏)。**无建筑重量**(只能推导,如面积×高度×层数×密度系数,
  那是估算而非源数据),**无施工商/开发商**(非开放数据)。
- **许可:** PLATEAU 站点政策 §3(`license_id: plateau`)——署名、允许商用——与已整合的
  UC24 接受的条件相同。

## 两种显示模式下的用法

- **地图模式(2D / 2.5D),出自 `osm-basemap-tiles`。** 由**离线合并**构建的一套瓦片源:
  OSM 为主(标识 + 属性),基盤地図情報填补 OSM 空缺(全国完整性),在已建模市町村用
  PLATEAU 的 `measuredHeight` 作为高度属性连接。含"仅在 OSM 缺失处用政府数据"这一判断
  的合并,在空间连接可负担的**构建时一次完成**,产出每栋带 `footprint_source` 与
  `height_source` 标签的一致单层。由此解决空图问题(政府补全)、重影问题(单层),保留
  离线能力,并对实测 vs 估算保持诚实。2.5D 挤出在起伏地表上读取烘焙的高度。
- **局部 3D 工作模式,出自 `local-3d-work-mode`。** 框选区域,按网格(mesh)按需加载
  高保真 PLATEAU 3D 模型,地上地下并显,叠加 SL 层与 AL 模拟结果。PLATEAU 的轮廓与 ID
  与 OSM 不同,故此模式直接用 PLATEAU 而非合并瓦片;未建模市町村则回落到挤出合并瓦片的
  建筑。再用使用遥测决定把哪些热区本地化,而非预先缓存整个关东。

## 结论

两个源对于一个自建、可离线、可商用分发的产品,在许可上均通行,按署名条件即可使用。
商用正式上线前的最终法务确认是任何依赖许可之决策的稳妥之举——不是因为结论存疑,而是
决策本身值得。合并瓦片的混合许可(OSM ODbL + 地理院条款)需并列署名;若日后公开合并
**数据库本身**(而非仅提供瓦片),ODbL 的 share-alike 将适用。

## 出典

- 承認申請Q&A | 国土地理院 — <https://www.gsi.go.jp/LAW/2930-qa.html>
- 国土地理院コンテンツ利用規約 — <https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html>
- 国土地理院の測量成果の利用手続 — <https://www.gsi.go.jp/LAW/2930-index.html>
- 出典の記載 | 国土地理院 — <https://www.gsi.go.jp/LAW/2930-meizi.html>
- 基盤地図情報ダウンロードサービス — <https://fgd.gsi.go.jp/download/>
- Project PLATEAU open data — <https://www.mlit.go.jp/plateau/open-data/>
- PLATEAU 站点政策 — <https://www.mlit.go.jp/plateau/site-policy/>
