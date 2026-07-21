# KuniJiban 钻孔数据

[English](README.md) | [日本語](README.ja.md) | [中文](README.zh.md)

- FL 状态：已作为用户提供的区域数据接入，按需加载
- 发布者/来源系统：日本国土交通省、土木研究所、港湾空港技术研究所 / KuniJiban
- Dataset/API key：`kunijiban_borehole` / `kunijibanBoreholes`

## 数据内容

- **格式与结构：**3 个 Apache Parquet 文件，分别为每个钻孔一行的嵌套表、每个地层区间一行的扁平表、每个 SPT 试验一行的扁平表。`data/external/kunijiban_borehole/manifest.json` 记录资产、字节数、SHA-256、时间戳、数量和 provenance 分类。
- **覆盖范围与 CRS：**这是用户从 KuniJiban 获取的区域性选择，并非全国完整覆盖。水平坐标为 WGS 84 经纬度（`EPSG:4326`）。高程单位是米，但垂直基准取决于来源且尚未统一；港口或河川记录可能采用地方基准。当前数据包没有定义权威 bounding box。
- **粒度与规模：**11,703 个钻孔、122,693 个地层区间和 239,137 条 SPT 观测。3 个 Parquet 资产合计 11,993,633 bytes。364 个 `pdf_vlm_empty` 钻孔没有可用地层，也没有关联的 layer 或 SPT 行，已从 FL 快照中删除。
- **时间：**整合任务于 2026-06-27 完成，记录为 `retrieved_at=2026-06-27T13:04:00+09:00`。发布方没有提供统一的数据快照日期，各钻孔的调查时间也不相同。KuniJiban 可能在不预先通知的情况下修正记录。
- **主要字段与单位：**钻孔 ID、地区、来源类别、十进制度经纬度、地面高程（m）、总钻深与地下水深度（m）、地层底深度（m）、原始日文地层名称/符号、标准化地层类别、SPT 深度（m）及作为击数的 SPT N 值。嵌套表还保留用于审计的源 XML 或 synthetic XML。
- **Provenance：**6,462 个钻孔来自源 JGS XML，5,241 个由 VLM 从柱状图 PDF 重建。每条记录必须保留 `data_source`；VLM 提取字段不能作为源观测展示。处理报告中的 12,067 行是过滤前的运行结果，不是当前 FL 数量。
- **已知缺口：**86 个钻孔缺少高程，6,030 个具有地下水位。调查目的、精度、旧试验单位、高程基准和时效性不一致。SPT N > 100 的记录需要复核；报告中的最大值 794 是明显的来源异常值。

## 来源

- [KuniJiban](https://www.kunijiban.pwri.go.jp/)
- [官方使用条款](https://www.kunijiban.pwri.go.jp/jp/terms.html)
- [官方使用注意事项](https://www.kunijiban.pwri.go.jp/jp/attention.html)

该数据包由项目所有者从交互式 KuniJiban 服务定向获取后提供。KuniJiban 于 2019 年移除批量下载功能。`Full_Pipeline_Run_Report.md` 记录了整合任务、字段映射、缺失情况和 VLM 来源子集。提取脚本及上游 PDF/XML 不在本仓库中，因此当前快照不能自动从源端重建。

## 在本项目中的使用

该数据作为地下 Foundation Data Layer evidence 使用。`GET /api/v1/catalog` 展示其 readiness 和钻孔数量；`GET /api/v1/datasets/kunijibanBoreholes` 返回审计 manifest。3 个 Parquet 文件通过 `/api/v1/assets/external/kunijiban_borehole/` 按需提供，不进入 exhibition bootstrap。

当前 FastAPI 服务只登记和提供资产，不查询 Parquet 行。未来 SL 模型可以基于带来源限定的地层和 SPT 记录估算缺失岩土参数。AL 必须保留 `data_source`、调查时点限制和未解决的垂直基准，不能把该数据包当作当前项目现场勘察。

## License

KuniJiban 使用条款允许在规定条件下搜索、下载、查看、复制、修改、分发、出借和销售地盘信息。向第三方提供时必须注明信息来自 KuniJiban，且不得对源地盘信息主张著作权。

## 商业使用注意

必须保留清晰可见的 KuniJiban 来源标注和条款链接。应明确区分源 XML 记录和 VLM 提取的 PDF 重建记录；在重要用途上使用前，必须将模型提取值与原始资料核对。KuniJiban 提醒：地下水位及试验值反映调查时点条件，不同调查的精度不同，数据未必与原件核对，旧数据可能存在非 SI 单位，且记录可能随时修正。不得仅依赖该区域数据进行设计、施工、开挖、安全或监管决策。还应复核提取时所用 VLM 的相关条款。本数据卡是数据治理摘要，不构成法律意见。
