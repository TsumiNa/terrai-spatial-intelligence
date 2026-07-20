# FL → SL → AL Factor of Concept 重构记录

- 日期：2026-07-20
- 分支：`refactor/fl-sl-al-concept`
- 基线：`main` / `4ceb7ba`
- 类型：首阶段为概念重构；同一 PR 的客户展览阶段增加最小前后端分离

## 1. 重构原因

原 Prototype 已经共用地图、数据和审计基础，但产品叙事仍以三个应用 Demo 为中心。它没有清楚解释多尺度数据缺失如何成为跨应用的能力，也容易让原始观测、确定性加工、代理指标、启发式评分与未来模型补值混在一起。

本次重构把 TerrAI 定义为一个可积累的数据基础设施加多个应用出口：

1. **FL** 积累公开、商业及客户授权的真实证据，并如实保留多尺度 missing。
2. **SL** 使用经过本地验证的场景模型群，在适合预测的 missing 上形成带不确定性和拒答能力的非破坏性增强层。
3. **AL** 把合格 FL/SL 证据转成坡地暴露、道路韧性、光伏选址等业务出口。

这样既保留了现有 Demo 的商业可读性，也为 `geo_pfn` 一类稀疏上下文预测能力留下正确位置。

## 2. 复核过的依据

- `TerrAI_Narrative_Product_Strategy_Update_v4.docx` 的 §4、§6–7：稀疏地下预测是入口技术证明；长期资产是可复用 engine/delivery 能力和受控 application。
- `TsumiNa/geo_pfn` 提交 `07c7ee0` 的 `stage-report.html` 与 `sparse-context-results.html`：模型优劣会随上下文密度、特征和训练量变化，区间覆盖与逐样本误差排序也不是同一问题。
- 当前 Prototype 的数据与评分血缘：6 组外部来源已经形成 FL；现有评分属于 AL 透明规则；横滨/茂原尚无经过 held-out、校准和跨区验证的地表 SL。

`geo_pfn` 的最新结论修正了早期“加入真实特征会变差”的过度概括：后续训练表明这主要与训练不足有关。重构因此不绑定某个固定模型或固定特征组合，而是采用按场景与稀疏度选择模型、与强基线比较、输出不确定性并允许拒答的概念。

## 3. 实施步骤与提交意图

### 提交 1：`docs: define FL SL AL conceptual architecture`

- 写入唯一的三层概念定义、missing 的多尺度含义和 observed/synthetic/unresolved 边界。
- 用 ADR 记录选择这一结构的原因、替代方案、后果与非目标。
- 更新既有重构决策，校正 `geo_pfn` 证据表述。

### 提交 2：`feat: add FL SL AL architecture lens`

- 在 Demo 中增加默认架构入口和中/日/英三语说明。
- 展示 FL 已接入、地表 SL 为 0、AL 已接入的真实成熟度。
- 将 FL 来源、SL 空状态、AL 出口和地下校准证据接入现有审计抽屉。
- 保留所有既有应用和地图交互，不改变其计算结果。

### 提交 3：`docs: map prototype maturity and validate concept`

- 在 README 中建立从运行说明到概念架构、ADR 和重构记录的入口。
- 加入概念契约测试与 CLI 验证，防止后续界面把 AL 启发式误标为 SL。
- 记录 PR 复核路径、验收结果与 Factor of Develop 的边界。

### 提交 4：`feat: rebuild exhibition demo with FastAPI backend`

- 客户导航只保留业务入口、结果、可靠性与审计，不再展示内部三层成熟度和模型壳子。
- 将静态页面移动到 `frontend/`，并通过单一 `/api/v1/bootstrap` 契约加载展示数据。
- 新增 FastAPI 文件数据服务，把汇总、条件/空间查询、区域筛选和行动队列排序移到 Python。
- 保留独立 JSON/GeoJSON 作为当前 FL 存储，不引入数据库 schema、ORM 或写入 API。
- 增加 API、客户界面边界和推荐结果的自动化契约测试。

### 提交 5：`docs: record customer exhibition service boundary`

- 更新启动、独立前后端运行、API 接口和客户入口说明。
- 记录静态前端、FastAPI、数据管线的责任边界及未来 SQLite 触发条件。
- 修正 PR 复核步骤，使客户展示与内部概念文档各自服务正确受众。

精确提交哈希和每个提交的 diff 由本分支 Git 历史与 PR `Commits` 页面保留；本文记录每一步的产品意图，避免只看到最终文件而失去决策过程。

## 4. 当前资产映射

| 当前资产 | 概念位置 | 理由 |
|---|---|---|
| GSI、OSM、横滨开放数据、NASA POWER、东京电力 CSV | FL | 真实发布/观测证据及其本地快照 |
| Google Satellite Embedding | FL | Google 生产的外部表征，不是 TerrAI 对 missing 的补值 |
| DEM 派生坡度、坐标转换、空间聚合 | FL | 保持来源观测语义的确定性加工 |
| 风险分、适宜分、联合分、容量代理 | AL | 透明业务规则与代理，不是训练模型生成的补值 |
| `geo_pfn` 羽田实验 | SL 机制证据 | 证明特定稀疏上下文下的候选机制，不证明地表应用精度 |
| 横滨/茂原地表 sparse imputation | 尚不存在 | 缺少本地目标标签、held-out、校准和跨区验证 |

## 5. PR 复核顺序

1. 启动 Demo，确认首屏一眼说明横滨城市韧性与茂原新能源两个客户场景。
2. 依次进入项目组合和专项分析，确认地图、行动队列和一句话结果解释完整。
3. 点击指标、队列分数和地图弹窗中的虚线值，确认来源、公式、不确定性与限制可追溯。
4. 切换中文、日文、英文，并在窄屏下确认主功能仍可读、可操作。
5. 打开 FastAPI `/docs`，确认健康、目录、数据、GeoJSON 查询和推荐队列接口。
6. 内部架构复核再阅读 `FL_SL_AL_CONCEPT.md` 与 ADR，确认运行时结果没有把 AL 规则误标成 SL。
7. 运行自动化校验，确认概念契约、API、数据任务和静态资源完整。

## 6. 明确留给 Factor of Develop

- FL/SL/AL 的数据对象、字段、表和文件 schema；
- 层间 API、任务编排、模型注册、版本与回滚协议；
- 客户数据导入、权限、多租户隔离和跨客户学习规则；
- 第一个地表目标变量、标签获取、缺测机制与模型组合；
- SL 的 held-out、校准、跨时间/跨区验证和 AL 准入阈值；
- 数据库、特征库、对象存储、在线推理和部署拓扑。

这些决策必须由首个客户 PoC 的目标变量、风险承受度和数据授权来约束。本次概念重构不以虚构接口或占位 schema 提前锁定答案。

## 7. 验收命令

```bash
node --check frontend/app.js
node --check frontend/audit.js
node --check frontend/i18n.js
uv run python -m unittest discover -s tests -v
uvx ruff check .
uv run python -m terrai_spatial validate
git diff --check
```

## 8. 客户展览与 FastAPI 后续重构

概念重构的首版把 FL/SL/AL 直接作为默认页面，适合内部对齐，但不适合客户展览。客户主要需要理解“有什么功能、结果意味着什么、是否可靠、如何追溯”，不需要在主流程中阅读内部成熟度或实验边界。因此同一 PR 继续完成第二阶段：

1. 将 FL/SL/AL 定义保留在架构文档和 ADR，不再放进客户导航。
2. 客户首屏改为项目机会、四个业务指标、地图、推荐队列和一句话结果解释。
3. 将内部实验、Claude 对比和模型壳子说明移出运行时主界面。
4. 静态文件移动到 `frontend/`；前端只通过 FastAPI 加载数据与推荐结果。
5. 新增 Python 数据服务，承担 JSON/GeoJSON 缓存、查询、汇总和队列排序。
6. 当前继续使用文件存储，以稳定 dataset key 隔离未来 SQLite 迁移。

详细职责与最小 API 见 `docs/architecture/FRONTEND_BACKEND_SPLIT.md`。
