# GSI 地图与视觉瓦片

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入并缓存试点范围
- 图层：标准地图、全国最新照片、阴影起伏图、倾斜量图

## 数据内容

- **格式** — 从 `https://cyberjapandata.gsi.go.jp/xyz` 获取的 XYZ 栅格瓦片，256 × 256 px。标准图、晕渲、坡度图为 PNG，正射影像为 JPEG。
- **已缓存图层与缩放级别** — `std`（标准地图）z15；`seamlessphoto`（全国最新正射影像／卫星镶嵌）z15–17；`hillshademap`（DEM 派生晕渲）z15–16；`slopemap`（DEM 派生坡度渲染）z15。
- **坐标系** — Web 墨卡托（EPSG:3857），标准 XYZ 瓦片方案。
- **本地缓存范围** — 仅两个演示矩形，不含更大范围。
- **数据量与目录结构** — 141 个瓦片文件，全部登记在 `data/tiles/manifest.json`，按 `data/tiles/<region>/[layer]/<z>/<x>-<y>.<ext>` 存放；标准图层省略图层目录层级。
- **时点** — 建立缓存时的固定快照，无自动刷新；上游图层由发布方独立更新。
- **已知缺失与限制** — 晕渲与坡度图是**已渲染的图像**而非数值栅格，无法从中读取高程或度数；本项目所有数值地形量均来自 DEM 产品。缓存的缩放上限即可见细节上限，在界面中请求更深缩放只会放大现有瓦片而不会获取新瓦片。

## 来源

GSI 地图图层目录：https://maps.gsi.go.jp/development/ichiran.html 。本项目缓存 `seamlessphoto`、`hillshademap`、`slopemap` 等试点瓦片。

## 在本项目中的使用

作为地图背景及屋顶、植被、农田、水体、建设状态、山脊谷地和坡度的视觉核查证据。瓦片通过 `/api/v1/assets/*` 提供，页面运行不访问 GSI 服务器。视觉底图不进入评分。

## License

依 GSI 内容利用规则署名并标明加工。部分瓦片可能包含第三方权利或个别法令限制：https://maps.gsi.go.jp/help/termsofuse.html

## 商业使用注意

“全国最新照片”在高缩放级别主要是正射航空影像，部分覆盖才是卫星影像，不得把全部内容称为卫星地图。公开离线再发布前需逐图层复核许可，不应对官方瓦片服务造成过大负载。
