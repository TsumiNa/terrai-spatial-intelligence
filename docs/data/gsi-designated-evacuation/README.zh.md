# GSI 指定紧急避难场所与指定避难所数据

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已作为全国基线接入
- 自治体：横滨市（`14100`）
- 来源更新时间：2026-01-16（GSI 公开履历）
- 获取方式：免费直接下载；不需要账号、API key、Earth Engine 或付费服务

## 数据内容

- **分发方式** — GSI 按自治体提供指定避难所（`14100_1`）与指定紧急避难场所（`14100_2`）的 CSV / GeoJSON，并提供机器可读的公开履历 CSV。
- **数据量** — 当前标准化快照含 459 条指定避难所记录、1,796 条指定紧急避难场所记录。
- **粒度** — 指定避难所通常每个设施一条记录；指定紧急避难场所可能把同一学校的多个校舍和体育馆分别记录，因此未经聚合不能把 1,796 条记录理解为 1,796 个独立地点。
- **灾种字段** — 指定紧急避难场所记录洪水、崩塌/泥石流/滑坡、风暴潮、地震、海啸、大规模火灾、内涝和火山现象的适用指定。
- **时间元数据** — 标准化脚本从 GSI 公开履历读取 `source_updated_at`，并把 UTC `retrieved_at` 写入数据集 metadata 和每个 feature。两者的审计含义不同，不合并为一个模糊的“最新日期”。

## 来源

- [GSI 公开与下载页面](https://hinanmap.gsi.go.jp/hinanjocp/hinanbasho/koukaidate.html)
- [指定避难所 GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_1.geojson)
- [指定紧急避难场所 GeoJSON](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/geoJSON/14100_2.geojson)
- [自治体公开履历](https://hinanmap.gsi.go.jp/hinanjocp/defaultFtpData/publicHistoryCSV/publicHistoryListData.csv)

## 在本项目中的使用

GSI 指定避难所构成设施韧性视图的全国 FL 基线。横滨市地域防灾据点用于校验匹配设施并增加地方说明；未匹配的横滨记录保留为明确标记的地方补充。GSI 指定紧急避难场所的校舍记录按设施名聚合后提供灾种指定证据，但不会被改称为指定避难所。

标准化 FL 产物为 `data/external/gsi_evacuation/yokohama_evacuation.geojson`，metadata 位于同一目录；融合后的 AL 证据为 `data/yokohama/official_facility_resilience.geojson`；后端还通过 `gsiEvacuation` dataset key 提供原始标准化数据。

直接刷新命令：

```bash
uv run python -m terrai_spatial data update --only gsi_evacuation
```

若文件缺失且允许联网，程序启动时也会自动执行该任务。

## License

GSI 说明，除页面另有规定外，适用其[内容使用条款](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html)和公共数据利用规则 1.0。再利用通常需要注明来源；编辑或加工内容应明确标识，第三方权利仍由使用者负责确认。

## 商业使用注意

这些记录由自治体依据《灾害对策基本法》登记，但 GSI 提醒数据可能存在未收录或过期情况。指定紧急避难场所按灾种指定，与指定避难所不是同一概念。在用于紧急指引、客户交付或运营决策前，应向横滨市确认最新指定、开放条件、容量、无障碍情况和详细灾害条件。还应把这些限制传递给下游用户，不得把 TerrAI 的韧性、屋顶、光伏或道路代理指标称为 GSI 字段。
