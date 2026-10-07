# AEOS V7.2 — M09 FAC（Finance Autonomous Center）财经自治中心行动计划 V1.0

> 状态：INITIAL BASELINE  
> 模块：M09 — FAC（Finance Autonomous Center）  
> 上位框架：AEOS V7.2  
> 版本：V1.0  
> 日期：2026-10-07  
> 执行原则：先边界、后功能；先闭环、后扩展；先 A0/A1、后 A2/A3；代码完成不等于业务完成。

---

## 1. 目的

本行动计划用于将 FAC 从“总体方案”推进到“可开发、可测试、可验收、可审计、可复制”的 AEOS 正式模块。

FAC 的核心职责是把经营事实转化为可验证的财经事实、经营判断与价值结果，围绕以下正式财经域建立自治能力：

- Revenue（收入）
- Cost（成本）
- Margin（毛利）
- Cash（资金）
- AR（应收）
- AP（应付）
- Budget（预算）
- ROI（投资回报）
- Value（价值）

所有关键流程必须遵循 AEOS 标准闭环：

`Fact → Event → DecisionCase → Decision → Action → Result → Verify → Evidence`

FAC 不重复建设销售、采购、生产、库存、人事等业务主数据系统；跨域数据通过标准 Object / API / Event / Result / Evidence Contract 获取，不直接跨域写库。

---

## 2. 项目成功定义

FAC 项目“完成”不是页面上线或代码合并，而是满足以下条件：

1. M09 Domain Boundary 与 Data Ownership 已冻结；
2. 核心 Object / Event / Result / Evidence / Decision / Action Contract 通过 Contract Test；
3. Revenue / Cost / Margin / AR 至少形成一个端到端可验收 MVP；
4. 至少一个真实闭环完成 `Event → Decision → Action → Result → Verify → Evidence`；
5. Finance Result 可被 M03 EBMS 直接消费，不重复计算；
6. 关键 Result Evidence 覆盖率达到 100%；
7. 重大资金、税务、预算、付款操作不可绕过 Guard 与人类责任人；
8. Development Ledger 中存在完整 Gate、Owner、Evidence 和 Verify 记录。

---

## 3. 分阶段执行模型

### P0 — 治理与边界冻结（第 0–2 周）

目标：先建立 FAC 的受控仓库与不可越界的架构基线。

必须完成：

- README 与仓库治理规则
- FAC_BOUNDARY_V1
- DATA_OWNERSHIP_V1
- MODULE_MAP_V1
- Object / Event / Result / Evidence / Decision / Action Contract 初版
- Agent / Skill 注册规范
- Development Ledger
- ADR 机制
- CI / Contract Test 基础门禁
- M01/M02/M03/M05/M06/M08/M10/M11/M12 接口责任矩阵

退出条件：

- G0：Boundary 评审通过
- G1：所有正式财经对象 Owner 明确
- G2-pre：Contract Schema 可校验
- 无未登记的跨域直连和影子财务事实

### P1 — MVP 闭环（第 3–8 周）

目标：只做 Revenue / Cost / Margin / AR 四个优先域，形成第一个完整财经自治闭环。

建设顺序：

1. Revenue
2. Cost
3. Margin
4. AR
5. Finance Result
6. CFO Agent / AR Agent / Cost Agent / Margin Agent
7. EBMS 财经结果卡片
8. 应收催收闭环

退出条件：

- Revenue 自动识别率 ≥95%
- 订单毛利可计算率 ≥95%
- AR 自动匹配率 ≥95%
- 至少 1 个应收闭环完成 Result Verify
- Result Evidence 覆盖率 100%
- Decision 可追溯率 100%

### P2 — 轻量自治（第 9–14 周）

目标：扩展 Cash / AP / Budget / ROI / Value，并把 Agent 从“分析”推进到“受控执行”。

建设顺序：

1. Cash
2. AP
3. Budget
4. ROI
5. Value Ledger
6. Cash Agent
7. Budget Agent
8. ROI Agent
9. Finance Risk Agent
10. A2 低风险自动化

退出条件：

- 30 天现金预测准确率 ≥90%
- AP 付款计划与证据完整
- Budget Variance 可追溯
- ROI/Value 可关联目标、投入、行动和结果
- A2 自动动作均可审计、可撤销或可升级

### P3 — 正式版与受限自治（第 15–20 周）

目标：完成风险闭环、Guard、性能、安全、可观测性和受限 A3。

建设内容：

- Finance Risk Engine
- Guard Policy Engine
- 高风险双人/多角色审批
- Event Replay
- Idempotency
- Audit completeness
- 结果对账与异常冲销机制
- 性能/SLO/告警
- A3 白名单场景
- 正式 UAT 与发布门禁

退出条件：

- G0–G7 全部通过
- 核心财经数据准确率 ≥99.5%
- Evidence 覆盖率 100%
- Decision 可追溯率 100%
- 高风险操作 0 个未授权自动执行
- 正式上线前 UAT 与 Owner Verify 完成

---

## 4. 20 周路线图

| 周期 | 核心任务 | 主要交付物 | Gate |
|---|---|---|---|
| W1 | 仓库治理、Boundary、Ownership | README、Boundary、Ownership | G0 |
| W2 | Contract Pack、接口矩阵、Ledger | Contract V1、Ledger、ADR | G1/G2-pre |
| W3 | Revenue Object/Event/Result | Revenue Engine 骨架 | G2 |
| W4 | Revenue 规则与 Evidence | Revenue Result | G3 |
| W5 | Cost Engine | Cost Result | G3 |
| W6 | Margin Engine | Margin Result | G3 |
| W7 | AR Engine + AR Agent | AR Aging / Overdue | G4 |
| W8 | 应收闭环 + EBMS Result | 首个完整闭环 | G5/G6/G7 |
| W9 | Cash Engine | Cash Position | G3 |
| W10 | 7/30/90 天现金预测 | Cash Forecast | G4 |
| W11 | AP Engine | AP Plan | G3 |
| W12 | Budget Engine | Budget Variance | G3 |
| W13 | ROI Engine | ROI Result | G3/G4 |
| W14 | Value Ledger | Value Result | G6/G7 |
| W15 | Finance Risk Engine | Risk Event / Result | G4 |
| W16 | Guard A0/A1/A2 | Guard Policy | G5 |
| W17 | 受限 A3 白名单 | A3 Policy | G5 |
| W18 | Event Replay / Idempotency / Audit | Contract Test 完整集 | G2/G7 |
| W19 | UAT / 性能 / 安全 | UAT Evidence | G6/G7 |
| W20 | 发布、培训、基线冻结 | Release Baseline | 全 Gate |

---

## 5. WBS 工作分解

### WBS-01 仓库治理

Owner 类型：System Lead / Architecture Owner  
输入：AEOS V7.2 受控基线  
输出：

- README.md
- docs/BASELINE_MANIFEST.md
- ledger/DEVELOPMENT_LEDGER.md
- adr/README.md
- .github/Issue / PR 模板
- CI 基础工作流

验收：

- 目录结构受控
- 每个正式交付物有 Owner / Version / Status
- PR 不可替代 Gate Verify

Evidence：

- Commit SHA
- PR Review
- Gate 记录

### WBS-02 Domain Boundary

Owner 类型：Business Owner + Architecture Owner  
输入：SYSTEM_REGISTRY / DATA_OWNERSHIP / DEH Boundary  
输出：

- architecture/FAC_BOUNDARY_V1.md
- architecture/DATA_OWNERSHIP_V1.md
- architecture/MODULE_MAP_V1.md

验收：

- M09 只拥有财经事实
- 无重复客户/订单/采购/生产/库存主数据
- EBMS 不维护第二套正式财经事实

### WBS-03 Contract Pack

Owner 类型：Data Architect / Backend Lead  
输出：

- OBJECT_CONTRACT_V1
- EVENT_CONTRACT_V1
- RESULT_CONTRACT_V1
- EVIDENCE_CONTRACT_V1
- DECISION_ACTION_CONTRACT_V1
- API_CONTRACT_V1

必须覆盖：

- tenant_id
- object_ref
- version
- source_system
- correlation_id
- trace_id
- idempotency_key
- evidence_refs
- actor / permission / audit fields

验收：

- Schema Validation
- Idempotency
- Event Replay
- Permission Enforcement
- Evidence Traceability
- Audit Completeness

### WBS-04 Revenue

Owner 类型：Finance Business Owner + Backend Lead  
输入：M05 Order、M06 Shipment、Invoice、Collection  
输出：Revenue / AR 基础事实、RevenueRecognized Event、Finance Result  
验收：自动识别率 ≥95%，差异可解释、可追溯。

### WBS-05 Cost

Owner 类型：Cost Owner + Backend Lead  
输入：采购、材料、生产、物流、人工、品质损失  
输出：Cost Result / CostAdjusted Event  
验收：核心订单成本可计算率 ≥95%，成本来源可回钻。

### WBS-06 Margin

Owner 类型：Finance Business Owner  
依赖：Revenue + Cost  
输出：Order/Product/Customer Margin  
验收：毛利计算覆盖率 ≥95%，异常低毛利可触发 Event。

### WBS-07 AR

Owner 类型：AR Owner  
输入：Invoice / Payment / Customer / Order  
输出：Aging、Overdue、Collection Priority  
验收：自动匹配率 ≥95%，至少完成 1 个真实催收闭环。

### WBS-08 Cash

Owner 类型：Treasury Owner  
依赖：AR / AP / Bank / Payroll / Tax  
输出：Current Cash、7/30/90D Forecast  
验收：30 天预测准确率 ≥90%。

### WBS-09 AP

Owner 类型：AP Owner  
输出：Payable、Due、Payment Priority、Payment Plan  
验收：付款建议不得直接执行高风险资金动作；必须进入 Guard。

### WBS-10 Budget

Owner 类型：Budget Owner  
输入：Goal + Revenue/Cost/Cash  
输出：Budget、BudgetExecution、Variance  
验收：每项预算偏差可关联目标、责任人与 Evidence。

### WBS-11 ROI / Value

Owner 类型：CFO / Investment Owner  
输出：Investment、ROI、Payback、Value Result  
验收：投资→行动→结果→财经结果→ROI→Value 可串联。

### WBS-12 Agent / Skill

Owner 类型：AI Lead  
Agent 顺序：

1. CFO Agent
2. AR Agent
3. Cost Agent
4. Margin Agent
5. Cash Agent
6. Budget Agent
7. ROI Agent
8. Finance Risk Agent

首批 Skill：

- calculate_revenue
- calculate_cost
- calculate_order_margin
- calculate_customer_margin
- calculate_product_margin
- calculate_ar_aging
- predict_collection
- calculate_ap
- generate_payment_priority
- forecast_cash_7d
- forecast_cash_30d
- forecast_cash_90d
- calculate_budget_variance
- calculate_roi
- calculate_payback_period
- detect_margin_anomaly
- detect_cash_risk
- detect_ar_risk
- detect_cost_anomaly
- generate_finance_result
- attach_evidence

验收：

- 每个 Skill 有输入/输出 Schema
- Agent 不绕过 Contract 和 Guard
- 建议与执行分离
- 所有正式输出可追溯到 Evidence

---

## 6. 系统责任分工

| AEOS 模块 | 与 FAC 的关系 |
|---|---|
| M01 Kernel | Goal、Permission、Guard、Decision/Action、Agent/Skill 公共能力 |
| M02 Data & Evidence | Object/Event/Evidence/Audit/Result/Value Ledger 底座 |
| M03 EBMS | 消费 Finance Result / Exception / Decision / Evidence |
| M04 R&D | 提供研发项目、BOM、ECO、Release 等经营事实 |
| M05 Sales | 提供 Customer / Lead / Quote / Order / Collection 相关业务事实 |
| M06 Delivery | 提供 Material / PO / Plan / Production / Shipment 等事实 |
| M07 HR/Logistics | 提供人工、薪酬及行政成本事实 |
| M08 Quality | 提供质量损失、返工、投诉、CAPA 等事实 |
| M10 POMS | 向财务岗位展示 Todo / Action / Evidence |
| M11 Integration | API Gateway / Connector / Event Bus |
| M12 DevSecOps | Contract Test、CI/CD、Observability、Security、Release Gate |

---

## 7. 自治等级放开条件

### A0 — 观察

允许：

- 查询
- 分析
- 异常发现
- 报告生成

禁止：

- 自动修改正式财经事实
- 自动付款
- 自动预算变更

进入条件：P0 完成。

### A1 — 人工确认

允许：

- 自动生成 DecisionCase
- 自动生成催收建议
- 自动生成预算/风险建议

必须：Accountable Owner 人工确认。

进入条件：G2/G3 通过。

### A2 — 低风险自动执行

允许：

- 催款提醒
- 报告生成
- 指标重算
- 低风险任务创建
- 自动升级通知

必须：

- 全量审计
- 幂等
- Evidence
- 可撤销/可升级

进入条件：至少连续两个迭代无重大审计缺陷。

### A3 — 受限自治

仅允许白名单动作。

禁止 Agent 自动最终执行：

- 大额付款
- 税务申报
- 预算重大变更
- 资金调拨
- 银行账户变更
- 重大投资审批
- 正式会计政策变更

这些操作始终需要明确的人类责任人和 Guard。

---

## 8. Gate 体系

| Gate | 核心验收 |
|---|---|
| G0 | Domain Boundary 冻结 |
| G1 | Data Owner / Accountable Owner 明确 |
| G2 | Contract Test 通过 |
| G3 | Finance Result 正确 |
| G4 | Agent 建议可用 |
| G5 | Action 闭环完成 |
| G6 | Result Verify 完成 |
| G7 | Evidence / Audit 完整 |

任何 Gate 未通过，不得用“代码已完成”替代业务完成。

---

## 9. KPI

- 财经核心数据准确率 ≥99.5%
- Revenue 自动识别率 ≥95%
- Order Margin 可计算率 ≥95%
- AR 自动匹配率 ≥95%
- 30 天 Cash Forecast 准确率 ≥90%
- 异常自动识别率 ≥90%
- Finance Result Evidence 覆盖率 = 100%
- Decision 可追溯率 = 100%
- 高风险动作未授权执行数 = 0
- Contract Test 通过率 = 100%
- 关键 Event Replay 成功率 = 100%

---

## 10. 未来 7 天立即行动清单

### Day 1

- 初始化 FAC 仓库正式目录
- 固化 README
- 建立 BASELINE_MANIFEST
- 建立 Development Ledger

### Day 2

- 完成 FAC_BOUNDARY_V1
- 完成 DATA_OWNERSHIP_V1
- 建立跨模块责任矩阵

### Day 3

- 完成核心 Object Contract
- 冻结 Revenue / Cost / Margin / AR 字段集

### Day 4

- 完成 Event / Result / Evidence Contract
- 定义 correlation_id / idempotency_key / evidence_refs

### Day 5

- 建立 Contract Test 最小框架
- 建立 Issue / PR 模板
- 定义 Gate 字段

### Day 6

- 建立 Revenue MVP 模拟数据
- 跑通 Order → Revenue → Result → Evidence

### Day 7

- 召开 P0 Gate Review
- 确认 Owner
- 冻结 V1 基线
- 开始 Revenue MVP 开发

---

## 11. 第一个 30 天必须完成

1. FAC 仓库治理结构完整；
2. Boundary / Ownership / Module Map 冻结；
3. Object / Event / Result / Evidence Contract V1 冻结；
4. Revenue Engine 可运行；
5. Cost Engine 可运行；
6. Margin Engine 可运行；
7. AR Aging / Overdue 可运行；
8. 至少一套模拟数据端到端闭环；
9. CFO Agent A0 可生成财经摘要；
10. AR Agent A1 可生成催收 DecisionCase；
11. EBMS 可消费至少一个 Finance Result；
12. Development Ledger 能记录 Gate、Owner、Evidence 和 Verify。

---

## 12. 并行与串行关系

可并行：

- 仓库治理 与 Domain Boundary
- Revenue Contract 与 Cost Contract
- UI 原型 与后端 Contract
- Agent Prompt/Policy 与 Skill Schema
- Contract Test 与模拟数据准备

必须串行：

1. Boundary → Ownership
2. Ownership → Contract Freeze
3. Contract Freeze → 正式接口开发
4. Revenue + Cost → Margin
5. AR + AP → Cash Forecast
6. Goal/Budget + Actual → Budget Variance
7. Investment + Result → ROI/Value
8. Event → Decision → Action → Result → Verify → Evidence
9. G2 → G3 → G5 → G6 → G7

关键路径：

`Boundary → Ownership → Contract → Revenue/Cost → Margin/AR → 首个闭环 → Cash/AP → Budget/ROI/Value → Risk/Guard → UAT → Release`

---

## 13. GitHub Issue / Milestone 建议

Issue 粒度控制为 0.5–3 天可完成，每个 Issue 必须包含：

- Objective
- Owner
- Input
- Output
- Dependency
- Acceptance Criteria
- Evidence
- Gate
- Risk

命名示例：

- `P0-ARCH-001 Freeze FAC Domain Boundary`
- `P0-DATA-002 Freeze Finance Data Ownership`
- `P0-CONTRACT-003 Define Revenue Object Contract`
- `P1-REV-001 Implement Revenue Recognition Engine`
- `P1-COST-001 Implement Cost Allocation Engine`
- `P1-MARGIN-001 Implement Order Margin Result`
- `P1-AR-001 Implement AR Aging`
- `P1-LOOP-001 Close First AR Collection Loop`
- `P2-CASH-001 Implement 30D Cash Forecast`
- `P2-ROI-001 Implement ROI Result`
- `P3-GUARD-001 Enforce Payment Guard`
- `P3-AUDIT-001 Verify Evidence Traceability`

Milestone：

- M0 — FAC P0 Baseline
- M1 — FAC Simulation
- M2 — FAC MVP
- M3 — FAC Lightweight
- M4 — FAC Full / Guarded Autonomy
- M5 — FAC Production Release

---

## 14. 风险与升级机制

核心风险：

- 上游数据质量不足
- 重复建设财务主数据
- 跨域直接写库
- 财经计算规则未冻结
- Agent 绕过 Guard
- Evidence 不完整
- Forecast 偏差持续过大
- 付款/税务/预算自动化越权
- EBMS 再次计算 FAC 结果
- 代码上线但业务未 Verify

升级规则：

- P0 边界冲突：升级至 Architecture Owner
- 数据 Owner 冲突：升级至 AEOS Kernel / 项目负责人
- 财经规则争议：升级至 Finance Business Owner
- 高风险权限问题：立即阻断并升级
- Evidence 缺失：Result 不得 Verified
- Contract 不兼容：不得进入 G2
- KPI 连续两个周期不达标：进入专项整改 ADR

---

## 15. 项目启动会执行摘要

FAC 的第一目标不是“做一套财务软件”，而是在 AEOS 中建立唯一正式的财经事实与价值判断中心。

第一阶段只抓四件事：

1. 冻结边界；
2. 冻结数据所有权；
3. 冻结 Contract；
4. 打通 Revenue / Cost / Margin / AR 第一个完整闭环。

项目优先级遵循：

`准确性 > 可追溯性 > 闭环 > 自动化程度 > 功能数量`

FAC 所有后续自动化必须建立在可验证的财经事实之上。任何没有 Evidence、Owner、Verify 或 Guard 的“自动化”都不视为 AEOS 自治能力。

---

## 16. 当前基线说明

本计划以 AEOS V7.2 当前可读取的受控架构原则、FAC 总体方案以及已确认的 M09 模块定位为依据。

若 AEOS 总仓后续恢复或更新更高优先级的正式基线文件，应执行差异核对，并通过 ADR / Baseline Manifest 管理变更，不允许静默偏离上位框架。
