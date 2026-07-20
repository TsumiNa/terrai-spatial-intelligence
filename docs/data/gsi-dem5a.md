# GSI DEM5A

[中文](gsi-dem5a.md) | [日本語](gsi-dem5a.ja.md) | [English](gsi-dem5a.en.md)

- FL 状态：已接入
- 发布者：日本国土地理院（GSI）
- 原生分辨率：5 m

## 来源

数据来自 GSI 基盘地图信息数值高程模型 DEM5A。下载需要免费注册；官方说明：https://service.gsi.go.jp/kiban/app/help/

## 在本项目中的使用

用于横滨和茂原的高程、坡度、局部起伏、低点代理，以及建筑和道路的地形暴露。确定性坡度/起伏计算仍属于 FL，不等于灾害概率或边坡稳定结论。本地产物包括 `data/yokohama/building_risk.geojson`、`road_priority.geojson` 和光伏网格中的地形字段。

## License

依 GSI 内容利用规则使用，需注明来源和加工；DEM 属基本测量成果。条款：https://maps.gsi.go.jp/help/termsofuse.html

## 商业使用注意

部分复制、地图制作或公开利用方式可能需要依据日本测量法办理手续。生产使用前应确认具体成果、加工表达和发布方式；植被、建筑遮挡和测量误差意味着 DEM 不能替代现场测量或地质工程判断。
