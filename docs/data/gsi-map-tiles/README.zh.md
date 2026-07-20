# GSI 地图与视觉瓦片

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入并缓存试点范围
- 图层：标准地图、全国最新照片、阴影起伏图、倾斜量图

## 来源

GSI 地图图层目录：https://maps.gsi.go.jp/development/ichiran.html 。本项目缓存 `seamlessphoto`、`hillshademap`、`slopemap` 等试点瓦片。

## 在本项目中的使用

作为地图背景及屋顶、植被、农田、水体、建设状态、山脊谷地和坡度的视觉核查证据。瓦片通过 `/api/v1/assets/*` 提供，页面运行不访问 GSI 服务器。视觉底图不进入评分。

## License

依 GSI 内容利用规则署名并标明加工。部分瓦片可能包含第三方权利或个别法令限制：https://maps.gsi.go.jp/help/termsofuse.html

## 商业使用注意

“全国最新照片”在高缩放级别主要是正射航空影像，部分覆盖才是卫星影像，不得把全部内容称为卫星地图。公开离线再发布前需逐图层复核许可，不应对官方瓦片服务造成过大负载。
