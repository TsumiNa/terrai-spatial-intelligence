# 横滨市地域防灾拠点

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入
- 快照：2026-04-01
- 数据类型：官方设施名称、地址、位置

## 来源

横滨市地域防灾拠点与帰宅困難者一時滞在施設 CSV：https://www.city.yokohama.lg.jp/bousai-kyukyu-bohan/bousai-saigai/data/shiryodata/data/data.files/hinanjo.csv

## 在本项目中的使用

筛出保土谷区研究窗口内两处官方据点，作为公共设施韧性改造的真实行动对象。位置、名称、地址为官方观测；最近建筑屋顶、光伏容量、道路距离和250 m高风险建筑关联均为 TerrAI 代理，产物为 `data/yokohama/official_facility_resilience.geojson`。

## License

横滨市开放数据默认 CC BY 4.0，允许商用；须署名并标明加工。条款：https://data.city.yokohama.lg.jp/terms.html

## 商业使用注意

第三方权利由使用者另行确认。不得把 TerrAI 的屋顶、容量、服务圈或韧性分称为横滨市官方字段、正式改造建议或灾害保证；设施状态和快照日期需定期更新。
