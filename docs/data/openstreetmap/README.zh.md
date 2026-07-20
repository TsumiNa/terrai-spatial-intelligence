# OpenStreetMap

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已接入并转为本地 GeoJSON
- 数据类型：建筑、道路、水体、土地利用、输电线

## 来源

OpenStreetMap 社区数据库：https://www.openstreetmap.org/copyright 。当前 Demo 使用已下载和标准化的本地数据，不依赖公共 API 或瓦片服务器。

## 在本项目中的使用

建筑轮廓用于坡地暴露和屋顶容量代理；道路用于连续性、可达性和光伏物流；水体/土地利用用于退距和场景；输电线用于茂原候选地距离代理。主要产物位于 `data/yokohama/`、`data/mobara/` 和 `data/joint/`。

## License

Open Database License（ODbL），使用时必须署名 OpenStreetMap contributors；公开衍生数据库可能触发共享相同方式要求。

## 商业使用注意

ODbL 对数据库与生成作品的义务不同，商业发布前应判断交付物是否构成衍生数据库。众包数据的完整性、精度和更新不保证；不能把缺失对象解释为现实中不存在，也不能滥用 OSM 公共生产 API/瓦片服务。
