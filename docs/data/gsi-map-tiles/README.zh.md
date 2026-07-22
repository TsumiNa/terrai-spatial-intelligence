# GSI 地图与视觉瓦片

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：全国在线流式获取
- 图层：标准矢量地图、全国最新照片、阴影起伏图、倾斜量图

## 数据内容

- **格式** — 标准底图为 GSI 矢量瓦片样式（`experimental_bvmap`，z4–16）；栅格底图为 XYZ 瓦片（256 × 256 px）：`seamlessphoto`（JPEG，z2–18）、`hillshademap`（PNG，z2–16）、`slopemap`（PNG，z3–15）。全部从 `https://cyberjapandata.gsi.go.jp/xyz` 在线获取。
- **坐标系** — Web 墨卡托（EPSG:3857），标准 XYZ 瓦片方案。
- **覆盖范围** — 全国；超过各来源的最大缩放级别时，界面直接放大显示，不请求会返回 404 的瓦片。
- **时点** — 即 GSI 当前发布的内容，无本地快照；上游图层由发布方独立更新。
- **已知缺失与限制** — 晕渲与坡度图是**已渲染的图像**而非数值栅格，无法从中读取高程或度数；本项目所有数值地形量均来自 DEM 产品。

## 来源

GSI 地图图层目录：https://maps.gsi.go.jp/development/ichiran.html 。本项目流式使用 `std.json`（矢量）、`seamlessphoto`、`hillshademap`、`slopemap`。

## 在本项目中的使用

作为地图背景及屋顶、植被、农田、水体、建设状态、山脊谷地和坡度的视觉核查证据，可在覆盖范围内任意地点使用。瓦片在渲染时从 GSI 获取，不落盘、不再分发。视觉底图不进入评分。

## License

依 GSI 内容利用规则署名并标明加工。部分瓦片可能包含第三方权利或个别法令限制：https://maps.gsi.go.jp/help/termsofuse.html

## 商业使用注意

“全国最新照片”在高缩放级别主要是正射航空影像，部分覆盖才是卫星影像，不得把全部内容称为卫星地图。公开离线再发布前需逐图层复核许可，不应对官方瓦片服务造成过大负载。
