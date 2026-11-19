# FAC 正式产品化迭代设计

## 1. 意图

将当前 FAC 仓库从“可运行的联调 Demo”升级为 AEOS V7.2 的正式 M09 FAC 产品迭代基线。产品必须继续使用现有公网入口 `http://150.158.13.110:18000/fac`，在原有代码、领域模型、OFA 计算能力和 AEOS 深色工作台基础上持续演进，不另起项目、不更换地址、不把演示数据冒充生产事实。

本设计承接以下既有基线：

- `docs/FAC_完整总体方案与分阶段实施计划_V2.1.md`
- `docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md`
- `architecture/FAC_GUARDRAILS_V1.md`
- 现有 FAC-OFA、EDP fixture、Finance Result、Evidence、Event Replay 和 M09 工作台代码

正式定位为：

> 企业经营财经事实中心、订单盈利分析中心和财经判断/价值闭环中心；后续逐步扩展为完整财经自治中心。

## 2. 目标

### 2.1 本轮目标

1. 把 `/fac` 从 Demo 工作台升级为正式 FAC 工作台入口。
2. 把订单财经分析（FAC-OFA）从演示能力提升为正式 Phase 1 业务能力。
3. 建立正式的 EDP-first 数据边界：外部和跨域事实只从 EDP Object/Event/Evidence 进入 FAC。
4. 建立正式的结果、规则、期间、证据、审计、版本和回放语义。
5. 保持现有计算结果可回归：同一输入和规则下，计划成本/订单毛利版本结果保持一致。
6. 为 Revenue、Cost、Margin、AR、AP、Cash、Budget、ROI、Risk 和 Agent/Guard/Action 预留稳定接口，但不伪装尚未接入的外部系统。
7. 让腾讯云同一地址成为持续迭代环境，每次发布都通过测试、迁移、灰度和回滚验证。

### 2.2 非目标

- 本轮不一次性声称九大模块全部生产完成。
- 不直接连接 ERP、CRM、SPC、HR、MES、银行或其他业务数据库。
- 不在 FAC 中复制 EDP 的基础治理对象。
- 不在 EBMS 中重新计算 FAC 的 Margin、AR、Cash 或 ROI。
- 不把 M13 Agent、M01 Guard、M10 POMS、EBMS 的沙箱投影写成真实外部联调完成。
- 不删除已有 Demo 测试路由；但 Demo 路由只能用于开发、回归和验收，不能作为正式产品入口或正式数据源。

### 2.3 反目标

- 继续增加硬编码的演示状态、演示金额或假完成状态。
- 使用 `demo` 数据库作为正式业务数据库。
- 用页面展示代替真实的对象、结果、证据和审计模型。
- 为了快速上线覆盖历史结果、删除迁移记录或绕过 EDP 契约。

## 3. 约束

- 正式入口保持 `/fac`，公网地址保持 `http://150.158.13.110:18000/fac`。
- 所有用户可见文案使用中文；AEOS、FAC、M02、M09、M13、M01、M10、EDP、POMS、OFA、API 事件编号等技术标识保留。
- 继续复用现有 Python 3.11、FastAPI、SQLAlchemy、Alembic、Pydantic 和原生 HTML/CSS/JavaScript，不引入不必要的前端构建链。
- 遵守 `FAC_GUARDRAILS_V1.md` 的 P0 红线：EDP-first、无跨域直连、金额/汇率完整、历史结果不可覆盖、规则版本化、Evidence 完整、Replay 幂等、Agent 不拥有正式财经事实、风险动作满足 SoD、源码不保存 Secret。
- 现网发布必须可回滚：旧容器/版本、数据库迁移和新镜像均保留明确标识。

## 4. 现状与问题

当前仓库已有：

- FAC-OFA 的订单、BOM、物料价格、人工、费用和计划成本计算基础。
- 计算版本、快照、规则引用、Result 和 Evidence 的部分模型。
- EDP fixture/adapter、事件台账、幂等回放和中文 M09 工作台。
- M02 EDP、M13 Agent、M01 Guard、M10 POMS、FAC Verify、EBMS 的联调投影。

当前需要纠正：

- 正式页面、接口和 README 仍然以 Demo 语义为主。
- 数据库设置使用 `fac_demo.db` 和演示初始化路径，正式配置边界不清晰。
- M13/M01/M10/EBMS 目前是沙箱投影，不能被当作真实系统完成。
- `/api/v1/demo/*` 是测试接口，不应成为正式模块 API 的唯一入口。
- 现有发布镜像是临时部署产物，后续需要采用正式镜像、正式环境变量和可重复迁移流程。

## 5. 方案选择

### 方案 A：正式产品化迭代（采用）

保留现有仓库、`/fac` 入口和已验证的 OFA 能力，先完成 Phase 1 的正式订单财经闭环，再沿原九个月路线逐步扩展。新增正式命名、正式配置、正式数据表/接口和 Adapter 边界；测试 Demo 仅作为回归夹具保留。

优点：最大化复用已有成果，能立即修正产品定位，同时不阻断后续真实系统接入。代价是需要做兼容迁移和命名收敛，不能一轮完成所有九大模块。

### 方案 B：一次性搭建九大模块骨架

先生成全部模块菜单、表、接口和权限，再逐步填充业务。优点是覆盖面大；代价是大量空壳和待接入状态，容易再次形成“看起来完整但没有正式业务闭环”的问题，不符合当前优先级。

### 方案 C：直接全面对接真实 AEOS 系统

同时实现 M02、M01、M10、M13、EBMS 的真实客户端和认证。优点是终局形态最接近生产；代价是依赖外部 API 契约、认证、网络和测试数据，目前信息不足，不能作为本轮唯一实施路径。

采用方案 A。方案 C 的接口边界作为未来 Adapter 设计要求，方案 B 的模块目录和导航按路线逐步增加，而不是一次性制造空壳。

## 6. 目标架构

```text
业务系统 / 微系统
        ↓ 可靠事件或已登记 API
M02 EDP Adapter
        ↓
Business Object / Event / Evidence / Audit / Provenance
        ↓
FAC Ports
        ↓
FAC-OFA / Revenue / Cost / Margin / AR / AP / Cash / Budget / ROI / Risk
        ↓
Finance Result / DecisionCase Request / Evidence Reference
        ↓
M01 Guard → M10 POMS → Verify → M02 Value Ledger / M03 EBMS
```

FAC 专业能力只能通过 Port 消费 EDP 数据。第一阶段至少固定以下端口名称和责任：

- `OrderDataPort`
- `BOMDataPort`
- `MaterialPricePort`
- `LaborCostPort`
- `ExpensePort`
- `ActualCostPort`
- `RevenuePort`
- `ExchangeRatePort`
- `QualityCostPort`
- `EvidencePort`

正式结果必须能够回钻：

```text
FinanceResult / OrderMarginResult
→ CalculationRun
→ CalculationSnapshot
→ Rule + RuleVersion
→ Order / BOM / Price / Labor / Expense
→ EDP Evidence / Audit
```

## 7. 产品与接口设计

### 7.1 正式工作台

`/fac` 作为正式 M09 FAC 工作台，保留当前 AEOS 深色布局和主链导航，但改用正式产品文案：

- 总览：财经事实、计算、结果、证据和动作状态。
- 订单财经分析：订单、BOM、价格快照、成本构成、计划成本和计划毛利。
- 规则与期间：Finance Rule Registry、Finance Period、版本状态和关闭/重开。
- 结果与证据：FinanceResult、OrderMarginResult、Evidence、审计和回钻。
- 事件与同步：EDP Object/Event/Evidence、同步状态、重试、幂等和回放。
- 决策与动作：只展示 FAC 产生的 DecisionCase Request 和标准 Action 引用，明确 M01/M10 待接入状态。
- 对账与扩展：为 Revenue/AR/AP/Cash/Budget/ROI/Risk 提供正式模块入口和接入状态。

页面不得显示“运行联调演示”作为正式业务按钮；正式页面应使用“计算订单”“生成财经结果”“查看证据”“提交复核”等业务动作。开发环境可以保留测试入口和测试标识。

### 7.2 正式 API 与兼容 API

正式 API 使用业务语义命名，至少包含：

- `GET /api/v1/fac/overview`
- `GET /api/v1/fac/orders`
- `GET /api/v1/fac/orders/{order_id}/financial-result`
- `POST /api/v1/fac/orders/{order_id}/calculations`
- `GET /api/v1/fac/calculations/{calculation_id}`
- `GET /api/v1/fac/results/{result_id}/evidence`
- `GET /api/v1/fac/rules`
- `GET /api/v1/fac/periods`
- `GET /api/v1/fac/events`

现有 `/api/v1/demo/*` 接口保留一段迁移期，仅用于测试夹具和回归，返回体中不得作为正式生产数据源；正式工作台改用 `/api/v1/fac/*`。

### 7.3 配置与数据

- 正式运行使用 `FAC_DATABASE_URL` 指向正式数据库，默认值不再命名为 `fac_demo.db`。
- `FAC_DEMO_ENABLED` 仅控制测试路由是否加载，不控制正式 `/fac` 页面是否可用。
- 数据库迁移必须从现有 Alembic 链连续演进，不删除历史迁移、不重写已发布版本。
- 正式初始化不自动写入固定演示订单；开发/验收夹具通过显式命令或测试 fixture 注入。
- 正式数据需要 tenant、source system、object revision、calculation revision、rule version、evidence reference 和 audit trace。

### 7.4 外部系统 Adapter

本轮先完成接口和 Contract Test：

- EDP：使用现有 fixture/import adapter 作为可替换实现。
- M13：保留 Registry/Capability 查询 Port，未配置真实地址时显示“待接入”。
- M01：保留 DecisionCase/Guard Policy Port，任何高风险动作默认人工复核。
- M10：保留 Action/Todo/Feedback Port，未配置真实客户端时不声称执行完成。
- EBMS/M02 Value Ledger：只发布已验证 FinanceResult/Evidence Reference，不复制计算。

## 8. 分阶段实施

### 阶段 0：基线纠偏

- 标记当前公网版本为临时迁移基线。
- 正式入口、正式配置、正式文案和 Demo 测试边界分离。
- 完成仓库中的 Secret 扫描、部署配置和回滚记录。

### 阶段 1：FAC-OFA 正式订单财经闭环

- 订单、BOM、物料价格快照、人工、费用从 EDP Port 进入。
- 建立 PlanCost、PlanMargin、CalculationRun、CalculationSnapshot、FinanceResult。
- 建立规则版本、期间状态、Evidence、Audit 和 Result 回钻。
- 保留 V1/V2 历史结果，禁止覆盖。
- 完成正式 `/api/v1/fac/*` API 与 `/fac` 页面。

### 阶段 2：轻量财经事实与判断

- Revenue、Cost、Margin、AR、AP、Cash 的正式对象、结果和对账接口。
- 计划/估算实际/最终实际严格区分。
- 形成 Order-to-Cash 闭环。

### 阶段 3：预测与预算

- 7/30/90 日现金预测。
- Budget → Actual → Variance → DecisionCase → Action。

### 阶段 4：ROI、价值与风险

- ROI、Payback、NPV、FinanceHealthResult、ValueResult。
- 对接 M02 Value Ledger。

### 阶段 5：Agent、Skill、Guard 与自治执行

- M13 Agent Registry、专业 Skill、M01 Guard、SoD、M10 Action、Verify。
- 高风险动作默认 Maker → Checker → Approver → Executor → Verifier。

## 9. 验收标准

### 本轮产品化验收

- 公网入口仍为 `http://150.158.13.110:18000/fac`。
- `/fac` 页面不再以 Demo 作为正式定位，所有主流程文案为中文业务语义。
- 正式页面使用 `/api/v1/fac/*`，不依赖 `/api/v1/demo/*` 才能运行。
- 订单财经分析能显示订单、BOM、价格快照、人工、费用、计划成本、计划毛利和证据引用。
- 重新计算生成新 CalculationRun/Result 版本，历史结果仍可查询。
- 缺失价格、缺失汇率、缺失证据不能静默通过。
- EDP-first、幂等、回放、租户隔离、规则版本和审计链有自动化测试。
- 未接入的 M13/M01/M10/EBMS 能力清晰标记为待接入，不能显示虚假的生产完成。
- 本地测试、迁移测试、接口测试、浏览器验证和公网健康检查全部通过。

### 后续阶段验收

后续每个阶段必须按同样格式增加：正式对象、正式 API、页面业务闭环、数据保留、证据、权限、回放、对账和部署回滚验收，不以静态菜单或占位卡片作为完成标准。

## 10. 发布策略

每次发布遵循：

1. 本地测试和数据库迁移检查。
2. 构建带版本号的正式镜像。
3. 使用独立灰度端口启动并验证健康、迁移、核心 API 和页面。
4. 备份当前公网容器和配置。
5. 切换同一 `18000` 端口。
6. 从公网验证 `/health`、`/fac`、正式 API 和关键业务流程。
7. 保留旧版本用于回滚，不在验证前删除。

本轮不重新创建公网地址，也不把 Demo 镜像继续作为长期正式镜像名称。

## 11. 由实现者决定的事项

- 在不改变上述接口语义的前提下，正式 API 的内部模块拆分和 SQLAlchemy 查询实现由实现者选择。
- 前端继续使用现有原生 HTML/CSS/JavaScript；当页面规模明显超过单文件可维护范围时，可按工作区拆分模板，但不引入非必要构建链。
- 开发环境可以继续使用 SQLite；腾讯云正式环境优先使用可持久化数据库，具体数据库类型在部署前依据现有服务器资源和备份能力确定。
- 真实 M02/M01/M10/M13/EBMS 地址和认证材料未提供前，Adapter 只实现接口、契约和安全的不可用状态，不虚构调用成功。

## 12. 已确认的实施决策

本轮先完成 FAC 系统内部可以独立交付的正式能力，不等待外部系统接口：

- 当前部署按单租户内部正式系统推进；租户、角色、权限和审计字段进入正式模型，统一登录通过后续 Auth Adapter 接入。
- Phase 1 先交付订单财经分析闭环：订单/BOM/价格/人工/费用 → 计划成本 → 计划毛利 → Finance Result → Evidence → Replay/审计。
- M02 EDP、M01 Guard、M10 POMS、M13 Agent、EBMS 先提供标准 Port、Contract、状态和待接入记录；外部接口资料提供后再替换 Adapter。
- 现有 Demo 数据只作为测试夹具和回归基线，不作为正式业务历史迁移来源。
- 正式系统使用同一 `/fac` 入口和腾讯云公网地址持续迭代，`/demo/fac` 仅保留开发测试用途。
