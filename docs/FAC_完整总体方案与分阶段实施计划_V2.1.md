# AEOS V7.2 — M09 FAC（Finance Autonomous Center）

# 财经自治中心完整总体方案与分阶段实施计划 V2.1

## 1. 文档定位

本方案定义 AEOS V7.2 下 M09 — FAC（Finance Autonomous Center，财经自治中心）的完整终局架构、模块体系、数据边界、系统关系、Agent/Skill、自治机制、实施路线及第一阶段 MVP。

本方案坚持：

**先完整规划终局，再按阶段实施；先业务事实，再智能自治；先真实闭环，再规模复制。**

FAC 不定位为传统财务 ERP，也不只是财务 BI。

FAC 的正式定位为：

**企业经营财经事实中心 + 盈利分析中心 + 资金与风险判断中心 + 经营价值自治中心。**

---

# 2. FAC 总体目标

FAC 最终需要回答五类问题。

## 2.1 企业发生了什么

建立可信财经事实：

- 收入；
- 成本；
- 毛利；
- 应收；
- 应付；
- 现金；
- 预算；
- 投资。

## 2.2 为什么发生

分析：

- 哪个客户；
- 哪个产品；
- 哪张订单；
- 哪个项目；
- 哪项材料；
- 哪项人工；
- 哪个品质问题；
- 哪个采购价格变化；

导致利润、现金和风险变化。

## 2.3 未来会怎样

预测：

- 回款；
- 付款；
- 现金；
- 毛利；
- 预算；
- ROI；
- 财经风险。

## 2.4 应该采取什么行动

形成：

`Fact → Event → DecisionCase → Decision → Action`

## 2.5 行动有没有产生价值

最终验证：

`Action → Result → Verify → Evidence → ROI → Value`

---

# 3. FAC 在 AEOS 中的位置

FAC 为 AEOS 一级正式模块：

**M09 — FAC 财经自治中心**

总体关系：

```text
                         AEOS V7.2
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
       M01 Kernel          M02 EDP              M03 EBMS
     权限/目标/行动       数据与证据底座        管理者工作面
          │                   │                    ▲
          │                   │                    │
          └──────────────┐    │    ┌───────────────┘
                         ▼    ▼
                       M09 FAC
                    财经自治中心
```

---

# 4. 三个系统必须明确的边界

## 4.1 EDP 管数据

EDP 是 FAC 的唯一企业级数据进出通道。

负责：

- Source Adapter；
- Business Object；
- Event；
- Evidence；
- Audit；
- Provenance；
- Data Quality；
- Event Replay；
- Outbox；
- API Contract；
- 租户隔离；
- Value Ledger。

原则：

> FAC 不直接连接 ERP、CRM、SPC、HR、MES、银行等外部或业务系统。

所有跨系统数据：

```text
业务系统
   ↓
EDP
   ↓
标准对象 / Event / Evidence
   ↓
FAC
```

---

## 4.2 FAC 管财经专业能力

FAC 负责：

- 财经规则；
- 财经计算；
- 盈利判断；
- 现金判断；
- 风险识别；
- 财经预测；
- 财经专业 Result；
- 财经 Agent / Skill。

---

## 4.3 EBMS 管管理结果

EBMS 负责：

- Result；
- Exception；
- Decision；
- Evidence；

的管理者工作面。

EBMS 不再维护第二套正式：

- Margin；
- Cash；
- AR；
- ROI。

---

# 5. FAC 完整功能架构

FAC 划分九个业务模块。

## 5.1 F01 Revenue — 收入自治

能力：

- 经营收入；
- 客户收入；
- 产品收入；
- 订单收入；
- 项目收入；
- 收入趋势；
- 收入差异；
- 收入对账。

---

# 5.2 F02 Cost & Order Financial Analysis — 成本与订单财经分析

这是本次 V2.1 的重点调整。

现 EBMS：

**经营中心 → 订单分析库**

正式定义为 FAC 的种子专业模块。

建议正式名称：

**FAC-OFA — Order Financial Analysis**  
**订单财经分析库**

其现有能力包括：

- 订单审核；
- BOM 多级展开；
- BOM 成本；
- 物料价格；
- 人工；
- 加工费；
- 费用；
- 成品工价；
- 计划成本；
- 计划毛利；
- 同类订单对比；
- 计划 vs 实际；
- 成本差异分析。

原则：

**不重新开发，采用“迁移 + 解耦 + 标准化 + EDP 化”。**

---

# 6. 5.2 模块必须端口化

FAC-OFA 不允许直接依赖：

- ERP API；
- JSON 文件；
- EBMS 私有表；
- 某一个固定数据库。

内部统一通过 Port。

```text
FAC-OFA
│
├─ OrderDataPort
├─ BOMDataPort
├─ MaterialPricePort
├─ LaborCostPort
├─ ExpensePort
├─ ActualCostPort
├─ RevenuePort
├─ QualityCostPort
└─ EvidencePort
        │
        ▼
       EDP
```

---

# 7. 5.2.1 OrderDataPort

标准输入至少包含：

```text
order_id
order_no
customer_id
product_id
quantity
unit_price
amount
currency
payment_term
order_date
status
revision
```

来源：

`EDP Business Object`

禁止：

`FAC → ERP orders API`

---

# 8. 5.2.2 BOMDataPort

标准输入：

```text
bom_id
bom_no
product_id
material_code
parent_material_code
level
quantity
unit
material_attr
revision
effective_from
effective_to
```

数据链：

`ERP/SPC → EDP → FAC`

---

# 9. 5.2.3 MaterialPricePort

标准字段：

```text
material_code
unit_price
currency
price_unit
effective_at
source_system
revision
evidence_ref
```

关键设计：

FAC 不能只使用“当前价格”。

必须支持：

**历史价格快照。**

否则历史订单重新计算时会改变原有毛利。

---

# 10. 5.2.4 LaborCostPort

输入：

- direct_labor；
- outsource_labor；
- processing_fee；
- product_labor_rate；
- effective_date；
- revision。

---

# 11. 5.2.5 ExpensePort

支持：

- variable_overhead；
- fixed_overhead；
- logistics_cost；
- quality_loss；
- tooling_cost；
- allocated_expense。

---

# 12. 5.2.6 ActualCostPort

计划成本只是 FAC 的第一步。

最终必须形成：

```text
Plan Cost
   ↓
Actual Cost
   ↓
Variance
   ↓
Reason
   ↓
Decision
   ↓
Action
```

Actual Cost 包括：

- actual_material；
- actual_labor；
- actual_expense；
- actual_logistics；
- actual_quality_loss。

---

# 13. 5.2.7 RevenuePort

订单分析模块不再自己创造第二套 Revenue。

统一引用 F01 的：

`RevenueFact`

避免：

**同一订单出现两个正式收入。**

---

# 14. 5.2.8 EvidencePort

订单毛利必须能够穿透：

```text
Margin Result
 ├─ Order
 ├─ Shipment
 ├─ BOM Revision
 ├─ Material Price Snapshot
 ├─ Labor Rate
 ├─ Expense Rule
 ├─ Calculation Rule
 └─ Evidence
```

Evidence 由 M02 EDP 托管。

---

# 15. F03 Margin — 盈利自治

FAC-OFA 是订单级盈利基础能力。

F03 在此基础上继续聚合：

- 订单毛利；
- 产品毛利；
- 客户毛利；
- 项目毛利；
- 月度毛利；
- 企业毛利。

链路：

```text
RevenueFact
      +
CostFact
      ↓
MarginResult
```

EBMS 禁止重新计算 Margin。

---

# 16. F04 AR — 应收自治

主要能力：

- 应收余额；
- 到期；
- 逾期；
- 账龄；
- 客户风险；
- 催收优先级；
- 回款预测；
- 回款闭环。

标准链：

```text
Receivable
→ Due
→ Overdue
→ Risk Event
→ DecisionCase
→ Collection Action
→ Payment
→ Evidence
→ Verify
```

---

# 17. F05 AP — 应付自治

能力：

- 应付余额；
- 到期计划；
- 付款优先级；
- 供应商付款；
- 资金压力；
- Payment Forecast。

FAC 可以建议付款。

FAC Agent 不直接执行高风险付款。

---

# 18. F06 Cash — 资金自治

包括两层。

## Cash Position

回答：

**现在有多少钱。**

## Cash Forecast

回答：

**未来有多少钱。**

模型：

```text
Opening Cash
+ Collection Forecast
- AP Forecast
- Payroll
- Tax
- Capex
- Other Commitments
= Future Cash
```

周期：

- 7D；
- 30D；
- 90D。

---

# 19. F07 Budget — 预算自治

预算必须绑定企业目标：

```text
Goal
 ↓
Budget
 ↓
Actual
 ↓
Variance
 ↓
Decision
 ↓
Action
 ↓
Result
```

---

# 20. F08 ROI — 投资回报自治

重点覆盖：

- 研发项目；
- 自动化设备；
- AI 项目；
- 产品开发；
- 市场投入；
- 改造项目。

输出：

- ROI；
- Payback；
- NPV；
- Investment Result。

---

# 21. F09 Financial Risk & Value

综合判断：

- Margin Risk；
- AR Risk；
- Cash Risk；
- Cost Risk；
- Budget Risk；
- Investment Risk。

最终输出：

`FinanceHealthResult`

及：

`ValueResult`

Value Result 写入 M02 Value Ledger。

---

# 22. FAC 三层逻辑架构

完整 FAC 内部再分三层。

```text
F1 财经事实层
│
├ Revenue
├ Cost
├ AR
├ AP
├ Cash
├ Budget Actual
└ Investment
        │
        ▼
F2 财经判断层
│
├ Margin
├ Variance
├ Forecast
├ ROI
├ Risk
└ Finance Health
        │
        ▼
F3 自治执行层
│
├ Agent
├ Skill
├ DecisionCase
├ Guard
├ Action
├ Result
└ Verify
```

---

# 23. 财经事实与法定会计边界

FAC 第一阶段以：

**Management Finance**

为主。

FAC 不直接替代：

- 总账；
- 法定凭证；
- 税务申报；
- 法定财报。

必须区分：

```text
Management Finance
Accounting Finance
Tax Finance
```

FAC 可以进行三口径对账。

不能混成一个数字。

---

# 24. Rule Engine

FAC 必须建设 Finance Rule Registry。

每个正式规则至少包含：

```text
rule_id
rule_name
rule_type
version
formula
effective_from
effective_to
owner
approval_status
source_fields
evidence_required
```

每一个 Result 必须记录：

`rule_id + rule_version`

---

# 25. Finance Period

期间状态：

```text
OPEN
→ CALCULATED
→ REVIEWED
→ VERIFIED
→ CLOSED
```

异常：

```text
REOPENED
RESTATED
```

历史结果不得静默修改。

---

# 26. Reconciliation

FAC 建设五类核心对账。

## Revenue

Management Revenue  
vs Accounting Revenue  
vs Invoice。

## Cost

Management Cost  
vs Accounting Cost。

## AR

FAC AR  
vs Finance AR  
vs Bank Collection。

## AP

FAC AP  
vs Purchase AP  
vs Finance AP。

## Cash

FAC Cash  
vs Bank Balance。

---

# 27. EDP 数据架构原则

FAC 所需任何外部数据均经过：

```text
Source System
      ↓
EDP Adapter
      ↓
Business Object
      ↓
Event
      ↓
Evidence
      ↓
FAC
```

FAC Result 回流：

```text
FAC
 ↓
Finance Result
 ↓
EDP
 ↓
EBMS / POMS / AEOS
```

---

# 28. FAC 不得再出现的架构

禁止：

```text
FAC → ERP
FAC → SPC Database
FAC → CRM Database
FAC → HR Database
FAC → Bank Database
```

同时逐步取消：

```text
EBMS Order Analysis
      ↓
Direct ERP
```

---

# 29. 现有订单分析代码迁移原则

现有 EBMS 订单分析库不直接删除。

采用四阶段迁移。

## Step 1 — Freeze

冻结当前算法和结果。

形成：

`OFA_LEGACY_BASELINE`

---

## Step 2 — Characterization Test

给当前计算建立测试。

固定：

- 输入；
- 输出；
- 毛利；
- 成本；
- BOM；
- 示例订单。

确保迁移前后结果一致。

---

## Step 3 — Replace Data Source

把：

`ERP / JSON`

替换为：

`EDP Port`

但算法暂时不变。

---

## Step 4 — Move Professional Ownership

算法归：

**FAC**

EBMS 只通过 Result Contract 使用。

---

# 30. 安全整改

现有订单分析代码存在直接 ERP 连接和连接凭据进入源码的问题。

FAC P0 必须执行：

- 凭据轮换；
- Secret 外置；
- 禁止源码存 Key；
- FAC 禁止直接连接 ERP；
- 数据经 EDP Adapter；
- 加入 CI Secret Scan。

该项定义为：

**P0 Blocking Issue**

未整改不得进入生产 FAC。

---

# 31. Agent 体系

完整 Agent：

- CFO Agent
- Revenue Agent
- Cost Agent
- Margin Agent
- AR Agent
- AP Agent
- Cash Agent
- Budget Agent
- ROI Agent
- Finance Risk Agent

第一阶段不全部开发。

---

# 32. Skill 体系

首批专业 Skill：

## OFA

- calculate_plan_cost
- build_bom_cost
- calculate_actual_cost
- compare_plan_actual
- calculate_order_margin

## AR

- calculate_ar_aging
- detect_ar_risk
- predict_collection

## Cash

- get_cash_position
- forecast_cash

## ROI

- calculate_roi
- calculate_payback

## Evidence

- generate_finance_result
- attach_evidence
- verify_finance_result

---

# 33. Guard 与 SoD

重大财经动作：

```text
Maker
→ Checker
→ Approver
→ Executor
→ Verifier
```

适用：

- Payment；
- Bank Transfer；
- Budget Major Change；
- Tax；
- Investment；
- Bank Account Change。

---

# 34. 自治等级

## A0

查询、解释、发现异常。

## A1

生成建议和 DecisionCase。

## A2

自动执行低风险动作：

- 催收提醒；
- 报表；
- 重算；
- 通知；
- 任务。

## A3

受限白名单自治。

高风险财经操作始终保留人类责任。

---

# 35. 完整项目阶段规划

FAC 按九个月完整规划。

## Phase -1 — Current State

现状调查。

## Phase 0 — Architecture Baseline

边界与契约。

## Phase 1 — MVP

订单财经 + Order-to-Cash 闭环。

## Phase 2 — Lightweight Finance

Revenue / Cost / Margin / AR / AP / Cash。

## Phase 3 — Forecast & Budget

预测与预算。

## Phase 4 — ROI / Value

投资与价值。

## Phase 5 — Autonomous Finance

Agent / Guard / Risk。

## Phase 6 — Productization

复制和行业模板。

---

# 36. 九个月路线图

## Month 1

- 财经现状调查；
- EDP 数据地图；
- FAC Boundary；
- Data Ownership；
- OFA Legacy Baseline。

## Month 2

- OFA 端口化；
- EDP Order/BOM/Material Price 接口；
- Revenue / Cost / Margin MVP。

## Month 3

- AR；
- Collection；
- Bank Evidence；
- 第一条完整闭环。

## Month 4

- AP；
- Cash Position；
- 全订单推广。

## Month 5

- 7/30/90D Cash Forecast；
- Budget。

## Month 6

- ROI；
- Value Result；
- Financial Risk。

## Month 7

- Agent；
- Skill；
- Guard；
- SoD。

## Month 8

- Accuracy；
- Reconciliation；
- Audit；
- Performance；
- Security；
- UAT。

## Month 9

- 正式上线；
- 模板化；
- 行业复制包。

---

# 37. 第一阶段 MVP 总体拆分

Phase 1 拆成两个 MVP。

# MVP-1A — FAC-OFA 迁移验证

目的：

把现 EBMS 订单分析库真正变成 FAC 专业模块。

链路：

```text
ERP / SPC
    ↓
   EDP
    ↓
Order / BOM / Price
    ↓
FAC-OFA
    ↓
Plan Cost
    ↓
Margin Result
    ↓
Evidence
    ↓
EBMS
```

---

# 38. MVP-1A 目标

必须证明：

1. FAC 不再直接取 ERP 数据；
2. OFA 通过标准 Port 运行；
3. 迁移前后同订单计算结果一致；
4. 每个毛利可回钻 Evidence；
5. EBMS 通过 Finance Result 消费结果。

---

# 39. MVP-1A 开发工作包

## A01 Legacy Baseline

选择至少三类订单：

- 正常订单；
- 低毛利订单；
- BOM 较复杂订单。

固化当前：

- Revenue；
- Material Cost；
- Labor；
- Expense；
- Total Cost；
- Margin。

---

## A02 EDP Order Object

建立：

`Order Business Object`

---

## A03 EDP BOM Object

建立：

`BOM / BOMLine Object`

---

## A04 Material Price Snapshot

建立历史价格对象。

---

## A05 OFA Port

实现：

- OrderDataPort；
- BOMDataPort；
- MaterialPricePort；
- LaborCostPort；
- ExpensePort。

---

## A06 Cost Engine Adapter

保留当前验证通过的核心成本算法。

取消其直接数据访问能力。

---

## A07 Margin Result

生成：

`OrderMarginResult`

---

## A08 Evidence

绑定：

- Order；
- BOM；
- Price；
- Rule；
- Calculation Snapshot。

---

## A09 EBMS Integration

EBMS 只消费：

`OrderFinanceResult`

---

# 40. MVP-1A 验收

迁移前后：

### 成本结果差异

在规则和源数据相同前提下：

`0 或可解释差异`

### Evidence

100%。

### Direct ERP Access

FAC：

`0`

### Contract

100% 通过。

### Result Traceability

100%。

---

# 41. MVP-1B — Order-to-Cash

在 OFA 完成以后继续。

链路：

```text
Order
 ↓
Shipment
 ↓
Revenue Fact
 ↓
Cost Fact
 ↓
Margin Result
 ↓
AR
 ↓
Overdue
 ↓
DecisionCase
 ↓
Collection Action
 ↓
Payment
 ↓
Bank Evidence
 ↓
Verify
 ↓
EBMS
```

---

# 42. MVP-1B 输入

EDP 提供：

- Order；
- Shipment；
- Customer；
- Invoice；
- AR；
- Bank Transaction。

---

# 43. MVP-1B Agent

只启用：

## CFO Agent — A0

读取、分析、解释。

## AR Agent — A1

负责：

- Aging；
- Risk；
- Collection Advice；
- DecisionCase。

---

# 44. MVP-1B Skill

第一阶段严格控制数量：

```text
calculate_order_margin
calculate_ar_aging
detect_ar_risk
create_collection_decision_case
match_bank_collection
verify_collection_result
generate_finance_result
```

---

# 45. 第一阶段页面

只建设必要工作面。

## Page 1 — 财经健康首页

展示：

- Revenue；
- Margin；
- AR；
- Cash；
- Risk。

---

## Page 2 — 订单财经分析库

复用并升级现订单分析库：

- Order；
- Plan Cost；
- Actual Cost；
- Margin；
- Variance；
- Evidence。

---

## Page 3 — AR 工作台

过去：

- Outstanding；
- Overdue；
- Collection。

未来：

- 今日催收；
- 高风险；
- 待升级。

---

## Page 4 — Evidence

支持：

Result → Evidence → Source。

---

## Page 5 — EBMS Result Card

管理层看到：

```text
Result
Target
Variance
Exception
Decision
Evidence
```

---

# 46. 第一阶段详细 Gate

## G-1

Current State 完成。

## G0

FAC Boundary 冻结。

## G1

Data Ownership 冻结。

## G2

EDP/FAC Contract 通过。

## G3

OFA 迁移前后计算一致。

## G4

Order Margin Result 正确。

## G5

AR 风险判断可用。

## G6

Collection 闭环完成。

## G7

Result Verified。

## G8

Evidence 100%。

## G9

EBMS 消费成功。

---

# 47. 第一阶段明确不做

MVP 阶段不做：

- 替代财务 ERP；
- 总账；
- 自动凭证；
- 税务申报；
- 自动大额支付；
- 全量 Agent；
- 复杂预算；
- 完整 ROI；
- A3 财务自治；
- 过度复杂的成本分摊。

---

# 48. P0 优先级

在任何新增功能开发前必须先完成：

**P0-01**  
现有 OFA 算法基线冻结。

**P0-02**  
ERP Secret 安全整改。

**P0-03**  
FAC ↔ EDP Boundary。

**P0-04**  
OFA Port Definition。

**P0-05**  
Order/BOM/Price Contract。

**P0-06**  
Finance Rule Version。

**P0-07**  
Evidence Contract Profile。

**P0-08**  
Regression Test。

---

# 49. 数据主原则

以后所有 FAC 开发统一遵守：

> **数据源不属于 FAC。数据进入 FAC 以前，必须由 EDP 完成接入、标准化、版本化、证据化和审计。**

FAC 只关注：

> **这个财经数据怎么算、怎么算对、意味着什么、下一步应该怎么做。**

---

# 50. 最终系统分工

最终形成：

```text
EDP
=
Data Plane
数据总线 + 对象 + Event + Evidence + Audit

FAC
=
Finance Intelligence Plane
财经事实 + 财经计算 + 判断 + 预测 + 风险 + 自治

EBMS
=
Management Plane
结果 + 异常 + 决策 + Evidence
```

---

# 51. FAC 完成定义

FAC 不能以“页面数量”或“代码完成”判断完成。

完整 FAC 至少达到：

- 数据全部经 EDP；
- 无跨域直接写库；
- 核心财经规则版本化；
- 订单财经分析完成 FAC 化；
- Revenue / Cost / Margin 可追溯；
- AR / AP / Cash 闭环；
- Forecast 可验证；
- ROI / Value 可追溯；
- Agent 不持有正式事实；
- Guard / SoD 生效；
- Evidence 100%；
- EBMS 不重复专业计算；
- 可独立部署；
- 可配置复制。

---

# 52. 最终建设原则

**先完整规划，再分阶段。**

**先复用现有能力，再重新开发。**

**先数据端口，再业务算法。**

**所有跨系统数据先过 EDP。**

**FAC 做财经专业能力，EBMS 只做管理结果面。**

**先规则，再 Agent。**

**先一单跑通，再批量订单。**

**先 Evidence，再自治。**

**先 A0/A1，再 A2/A3。**

FAC 最终不是一个“AI 财务软件”。

FAC 的最终目标是：

> **让企业每一笔经营活动都能形成可信的财经结果，让每一个经营决策都能看到财经影响，让每一个行动最终都能验证价值。**
