# FAC 完整联调工作台设计

状态：已确认并完成 Demo

日期：2026-11-19

## 1. 意图

把现有 FAC Demo 从“主链路演示页”扩展为与原 GPT 方案一致的完整中文联调工作台。页面不仅展示 `CRM / PLM → M02 EDP → FAC` 的计算链，还要完整呈现 M13 Agent Registry、M01 Guard / Decision、M10 POMS Action、FAC Verify、EBMS Result / Evidence 的职责边界、数据对象、状态流转和证据回链。

目标使用者是方案评审、产品负责人和开发联调人员。使用者打开 Demo 后，应能看懂 AEOS 财经自治链路“谁产生事实、谁负责财经判断、谁提出建议、谁审批、谁执行、谁验证”，并能运行一条可重放的本地联调样例。

## 2. 依据与当前差距

原 GPT 方案明确的核心闭环为：

```text
业务系统
  ↓
M02 EDP
  ↓
FAC 财经判断
  ↓
M13 Agent
  ↓
M01 Guard / Decision
  ↓
M10 POMS Action
  ↓
执行结果
  ↓
FAC Verify
  ↓
EBMS Result / Evidence
```

M13 的正式边界为：

```text
M13 /internal/aeos/agent-registry
  ↓ 服务间 HMAC 签名
最小 Agent Registry Projection
  ↓
FAC HttpM13RegistryAdapter
  ↓
require_dispatchable()
```

当前 Demo 已有 OFA 真实本地计算、V1/V2 版本、事件重放和主链路视觉框架，但 M13、M01、M10、Verify / EBMS 主要还是静态联调投影，页面也没有把原方案中的对象和职责完整展开。本次工作先补齐“完整方案展示 + 可运行沙箱联调”，不把沙箱状态伪装成生产真实接口。

## 3. 目标

- 以中文呈现原 GPT 方案的完整模块层级和职责边界。
- 把主链路拆成可点击的七个工作区：架构总览、事件总线、财经结果、智能体注册、防护决策、POMS 动作、验证证据。
- 每个工作区至少展示：业务目的、输入、输出、责任模块、状态、关联编号和证据引用。
- 运行一次 Demo 时，页面上的事件、结果、智能体建议、Guard 决策、POMS Action、执行反馈和 Verify 状态同步变化。
- 保留当前 OFA V1 `46.00 CNY`、V2 `52.00 CNY` 的真实本地计算和幂等回放行为。
- 明确标识“真实本地行为”“联调沙箱投影”“未来真实接口”，避免 Demo 误导为生产集成。
- 让评审者可以从任意结果回钻到 `Result → CalculationSnapshot → Rule → Source Object → Evidence`。

## 4. 非目标

- 本次不接入真实 M13、M01、M10 服务，不模拟网页登录，不调用 `/api/harbor` 作为正式服务接口。
- 本次不引入真实 LLM、Agent Runtime、Temporal、LangGraph 或生产级权限服务；开源项目选型作为后续真实联调阶段的扩展点。
- 不修改 OFA 计算规则，不改变现有 Demo API 的 V1/V2 结果契约。
- 不删除、重置或覆盖当前工作区中用户已有的 OFA、Calculation、EDP、数据库迁移和 CAD 文件改动。
- 不把页面做成泛化财务 BI 看板；核心是 AEOS 系统联调和财经结果证据链。

## 5. 方案选择

### 方案 A：单页方案说明书

在现有主控制台中增加更多说明、架构图和状态卡片。实现成本最低，但对象之间的关系和各模块的操作路径仍然不够清晰，适合静态汇报，不适合联调演示。

### 方案 B：完整联调工作台（采用）

保留当前深色 AEOS 风格和 `/fac` 入口，扩展为七个工作区。每个工作区有自己的中文标题、职责说明、对象列表和状态表；主控制台负责串起完整链路，按钮触发同一套本地 Demo API。这样能最大程度呈现原方案，同时不要求本轮接入外部服务。

### 方案 C：直接做真实跨系统集成

同时建设 M13 Registry Adapter、M01 Guard Client、M10 POMS Client、服务间认证和真实回证。它最接近生产目标，但需要其他系统的真实 API 契约、网络地址、认证材料和联调环境，超出当前 FAC Demo 可独立完成的范围。

本次采用方案 B，接口和数据模型按方案 C 的边界预留。

## 6. 工作区设计

### 6.1 架构总览 / 控制台

展示完整链路：

`CRM / PLM → M02 EDP → M09 FAC → M13 Agent → M01 Guard → M10 POMS → Verify → EBMS`

内容包括：

- 顶部运行环境、租户、关联编号、幂等开关和当前阶段。
- 七个节点的职责、输入、输出和状态。
- 四步运行手册：事实进入 EDP、FAC 计算判断、智能体建议与 Guard、防护后的动作执行与验证。
- 当前已完成能力、正在联调能力和未来真实接口的状态分组。
- 一键运行联调、重放最近事件、查看事件台账和验证证据。

### 6.2 事件总线 / M02 EDP

展示 `Object / Event / Evidence / Audit / Outbox` 的关系。

- 事件类型、来源系统、目标模块、关联编号、幂等键、状态。
- `QuoteRecalculationRequired`、`BOMReleased`、`MarginRiskDetected` 示例。
- 事件写入、确认、处理、失败、可回放状态。
- 重放时不重复创建财经事实的结果说明。
- 展示 EDP 是事实标准化和审计入口，不是财经规则 Owner。

### 6.3 财经结果 / M09 FAC

展示 FAC 作为财经专业结果 Owner 的边界。

- `FinanceResult / OrderMarginResult`。
- 计划成本 V1、V2 和版本差异。
- `CalculationRun`、`CalculationSnapshot`、规则版本、价格版本。
- 订单、BOM、MaterialPrice、Labor、Expense 的冻结输入。
- 结果状态、功能币种、证据覆盖率和前序结果引用。
- 链接到 `/demo/fac` 查看 OFA 详细计算过程。

### 6.4 智能体注册 / M13 Agent Registry

展示最小 Registry Projection，而不是模拟聊天机器人。

- Agent 名称、职责、能力、风险等级、运行级别（A0 观察 / A1 建议 / A2 执行）。
- `dispatchable` 条件：已注册、能力匹配、策略允许、服务认证有效、健康检查通过。
- CFO、成本、毛利、应收、付款智能体示例。
- Harbor 主数据与 FAC 最小投影的关系。
- 明确显示：当前为本地 Registry 沙箱；真实版本将通过 HMAC 服务接口和 `HttpM13RegistryAdapter` 获取。

### 6.5 防护与决策 / M01 Guard

展示“智能体建议”和“高风险动作执行”之间的隔离。

- DecisionCase 编号、来源结果、风险等级、建议内容、Maker、Checker、Approver、Accountable Owner。
- 策略命中、职责分离、审批状态、允许 / 拒绝 / 待复核结果。
- 高风险付款、价格修改、信用政策、催收动作的示例。
- 明确显示 Agent 不能自行 Verify、不能绕过 Guard、不能直接产生执行结果。

### 6.6 POMS 动作 / M10 POMS

展示从财经建议到业务执行的落地过程。

- Action / Todo 编号、来源 DecisionCase、责任人、截止日期、优先级。
- 待办、已接收、进行中、已完成、失败状态。
- 执行反馈、反馈时间、反馈证据和回流 FAC 的结果。
- 当前为 Action 下发沙箱；真实版本预留 POMS Action Client。

### 6.7 验证与证据 / FAC Verify / EBMS

展示完整证据链和价值验证。

- `Result → Snapshot → Rule → Source Object → Evidence → Audit`。
- Verify 结论、证据完整率、执行结果、ROI / Value Ledger。
- 结果是否可消费、是否可回钻、是否需要人工复核。
- EBMS 仅消费已验证的 Result / Evidence，不直接重新计算 FAC 财经结果。

## 7. Demo 状态模型

一次“运行联调演示”统一使用 `FAC-DEMO-2025-01` 作为关联编号，按照以下顺序推进：

1. CRM / PLM 产生订单、报价、BOM 事实。
2. M02 EDP 接收并标准化 Object / Event / Evidence。
3. FAC 调用真实本地 OFA，生成 V1 `46.00 CNY` 和 V2 `52.00 CNY`。
4. M13 沙箱返回可调度 Cost / Margin Agent 建议。
5. M01 沙箱生成 DecisionCase，应用职责分离和高风险审批规则。
6. M10 沙箱生成 POMS Action，并返回执行反馈。
7. FAC Verify 绑定 FinanceResult、Evidence 和执行反馈，形成已验证结果。
8. EBMS 投影消费已验证结果；重复回放只更新可回放状态，不新增财经事实。

页面状态必须由同一条 Demo 状态来源驱动，避免主控制台与子页面显示互相矛盾。

## 8. 数据与接口边界

### 真实本地行为

- `/api/v1/demo/reset`
- `/api/v1/demo/state`
- `/api/v1/demo/events/quote-recalculation`
- `/api/v1/demo/replay`
- FAC Calculation / OFA / CalculationSnapshot / Result / Event Ledger

### 联调沙箱投影

- M13 Registry、Agent 建议和 dispatchable 结果
- M01 DecisionCase、策略判断和审批状态
- M10 Action、Todo、执行反馈
- FAC Verify、EBMS Result / Evidence 投影

### 未来真实接口预留

- `HttpM13RegistryAdapter`
- M13 `/internal/aeos/agent-registry`
- 服务间 HMAC 签名和密钥轮换
- M01 Guard Policy / Decision Client
- M10 POMS Action Client
- Verify / Evidence 回证接口

## 9. 视觉与交互约束

- 所有用户可见文案使用中文；AEOS、FAC、M02、M13、M01、M10、EDP、POMS、OFA 和接口事件编号保留为技术标识。
- 延续原 GPT 设计要求的深色 AEOS 控制台风格，但增加清晰的模块分层、状态色和证据关系。
- 不使用泛化 KPI 大屏替代系统对象和链路。
- 每个沙箱状态都必须有“沙箱 / 待真实接入”标识。
- 桌面端展示完整关系，窄屏端采用纵向卡片和横向流程滚动。

## 10. 验收标准

- `/fac` 首屏能完整看懂从业务事实到 EBMS 的闭环。
- 七个工作区均可通过导航访问，且页面标题、职责、对象和状态不使用英文说明性文案。
- 运行联调后，七个阶段状态均更新，V1 / V2、DecisionCase、Action、Verify、Evidence 互相有引用关系。
- 重放最近事件后显示幂等成功，不能新增 Result、Run 或 Event。
- `/demo/fac` 仍能运行 reset → V1 → V2 → replay，且显示中文动态结果。
- 测试、Ruff、编译检查和浏览器交互验证全部通过。
- 真实外部系统未接入时，页面不能声称 M13、M01、M10 或 EBMS 已完成生产联调。

## 11. 留给实现阶段的决定

- 复用现有原生 HTML/CSS/JavaScript，不新增前端框架和构建链。
- 复用现有 Demo API 和 OFA 结果，不在页面中硬编码财经金额。
- 新增一个聚合的 `DemoIntegrationState` 投影，供主控制台和七个工作区共用。
- 先用本地内存 / 数据库沙箱补齐 M13/M01/M10/Verify 的对象状态，再为真实 Adapter 留接口。
