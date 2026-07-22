# 国土交通省五万分之一土地分类基本调查
[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

## 数据内容
按图幅提供地质、土壤等 Shapefile；年代和字段会随图幅变化。TerrAI 裁剪已 GIS 化的关东 15 幅图幅并转为 GeoJSON，保留原字段、图层名和时间戳。上游仅对部分图幅做了 GIS 化，覆盖存在按图幅缺失。
## 来源
[国土调查下载](https://nlftp.mlit.go.jp/kokjo/inspect/landclassification/download.html)
## 在本项目中的使用
用于坡地稳定、施工限制、渗透性及用地尽调。API 键为 `landClassification50k`；更新命令见英文版。
## License
现行默认适用公共数据利用规则1.0，须标注来源和加工。
## 商业使用注意
部分测量成果可能受《测量法》手续约束；不得原样再分发原包，交付前需逐图幅核验。
