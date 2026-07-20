# Google Satellite Embedding V1 / AlphaEarth Foundations

[中文](google-satellite-embedding.md) | [日本語](google-satellite-embedding.ja.md) | [English](google-satellite-embedding.en.md)

- FL 状态：已接入
- 分辨率：10 m，年度64维表征
- 当前年份：2023、2024

## 来源

数据由 Google 与 Google DeepMind 生产，本项目从 Source Cooperative 的公开 COG 镜像读取必要窗口；该镜像不由 Google 官方支持。目录：https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_SATELLITE_EMBEDDING_V1_ANNUAL ，镜像：https://registry.opendata.aws/aef-source/

## 在本项目中的使用

横滨 7,820、茂原 19,877 个有效像素，用于年度余弦变化、相似区域核查和未来少量客户标签迁移。生成变化图、相似表征图和100 m证据单元。当前不进入适宜性或韧性评分；外部生产的表征属于 FL，不是 TerrAI SL。

## License

CC BY 4.0。指定署名：`The AlphaEarth Foundations Satellite Embedding dataset is produced by Google and Google DeepMind.`

## 商业使用注意

64维轴不能直接解释为土地类别；年度变化也可能来自成像条件，必须结合影像和现场核查。公开镜像目前无需 Google 账号或 Earth Engine，但 TerrAI 承担自身网络、存储和计算；若改用官方 provider-pays 路径需重新评估费用。
