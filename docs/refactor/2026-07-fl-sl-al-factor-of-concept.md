# FL → SL → AL Factor of Concept 重构记录

- 日期：2026-07-20
- 分支：`refactor/fl-sl-al-concept`
- 基线：`main` / `4ceb7ba`
- 类型：概念重构，不是开发架构重构

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

1. 先读 `docs/architecture/FL_SL_AL_CONCEPT.md`，确认定义、成熟度和不可补值边界。
2. 再读 `docs/adr/0001-fl-sl-al-conceptual-layers.md`，确认替代方案和本次非目标。
3. 启动 Demo，默认进入“FL → SL → AL 架构”，逐一点击指标审计来源。
4. 切换中文、日文、英文，确认三层语义一致。
5. 进入坡地、道路、光伏模块，确认原有地图与评分未变，也没有被标为 SL。
6. 运行自动化校验，确认概念契约、数据任务和静态资源完整。

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
node --check app.js
node --check audit.js
node --check i18n.js
uv run python -m unittest discover -s tests -v
uvx ruff check .
uv run python -m terrai_spatial validate
git diff --check
```

