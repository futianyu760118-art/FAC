# AEOS V7.2 — M09 FAC
# 第一阶段 MVP 开发执行方案 V1.1

> 上位方案：《FAC 财经自治中心完整总体方案与分阶段实施计划 V2.1》  
> 模块：M09 — FAC  
> 阶段：Phase 1 MVP  
> 状态：待确认开发基线  
> 版本：V1.1

---

# 0. V1.1 迭代说明

V1.1 在 V1.0 基础上重点补充：

1. EDP Readiness Gate；
2. Actual Cost 双层口径；
3. Management Revenue 正式定义；
4. 多币种与汇率体系；
5. OFA Rule Baseline；
6. CalculationRun 与重算版本机制；
7. Event Catalog；
8. Result Verify 权责矩阵；
9. MVP Test Acceptance Matrix；
10. 调整 8 周开发顺序。

第一阶段仍然坚持：

**先 EDP 数据准备，再 FAC；  
先规则冻结，再迁移；  
先一单可信，再批量扩展；  
先 Evidence，再 Agent。**

---

# 1. 第一阶段最终目标

第一阶段结束后必须证明：

- FAC 所有跨系统数据统一经 EDP；
- FAC Direct ERP Access = 0；
- 现有 EBMS 订单分析库完成 FAC-OFA 专业化迁移；
- 原有 OFA 算法规则有正式基线；
- Revenue / Cost / Margin 支持多币种；
- 每个正式金额同时保留原币和功能币；
- 每次计算都冻结汇率与输入 Snapshot；
- 计划成本、估算实际成本、最终实际成本口径可区分；
- 重算不覆盖历史 Result；
- AR → Risk → Decision → Action → Collection → Verify 跑通；
- Evidence 覆盖核心 Result 100%；
- EBMS 只消费 FAC Finance Result。

---

# 2. 第一阶段两条 MVP

## MVP-1A — FAC-OFA

目标：

**把现有 EBMS“经营中心—订单分析库”迁移成 FAC 的正式订单财经分析模块。**

主链：

```text
ERP / SPC / Finance
        ↓
       EDP
        ↓
Order / BOM / Price / FX / Cost
        ↓
     FAC Ports
        ↓
     FAC-OFA
        ↓
Revenue / Cost / Margin
        ↓
     Evidence
        ↓
       EDP
        ↓
      EBMS
```

---

## MVP-1B — Order-to-Cash

主链：

```text
MarginResult
     ↓
Receivable
     ↓
Overdue
     ↓
ARRisk
     ↓
DecisionCase
     ↓
Collection Action
     ↓
Payment
     ↓
BankTransaction
     ↓
FX / Bank Match
     ↓
Result Verify
     ↓
FinanceResult
     ↓
EBMS
```

---

# 3. 开发前新增 G-1：EDP Readiness Gate

FAC 不允许假定数据已经存在。

正式开发前必须逐项检查 EDP 是否具备以下能力。

| ID | 能力 | MVP要求 |
|---|---|---|
| EDP-R1 | Order | 必须 |
| EDP-R2 | Order Product | 必须 |
| EDP-R3 | Shipment | MVP-1B 必须 |
| EDP-R4 | BOM/BOMLine | 必须 |
| EDP-R5 | Material Price | 必须 |
| EDP-R6 | Labor / Expense | 必须 |
| EDP-R7 | Invoice / AR | MVP-1B 必须 |
| EDP-R8 | Bank Transaction | MVP-1B 必须 |
| EDP-R9 | FX Rate | 必须 |
| EDP-R10 | Evidence | 必须 |
| EDP-R11 | Event | 必须 |
| EDP-R12 | Audit | 必须 |

状态只有：

```text
READY
PARTIAL
NOT_READY
BLOCKED
```

任何 NOT_READY 项必须：

1. 增加 EDP Adapter；
2. 或使用 EDP Mock / Import Adapter；
3. FAC 不得绕过 EDP 直接连接源系统。

输出文件：

`FAC_MVP_EDP_READINESS_MATRIX_V1`

---

# 4. 管理财经 Revenue 正式定义

第一阶段正式对象命名：

**ManagementRevenueFact**

避免与法定会计收入混淆。

第一阶段支持三个参考金额：

```text
Order Amount
Shipment Amount
Accounting Revenue
```

但只有：

`ManagementRevenueFact`

进入 FAC 经营毛利计算。

---

# 5. Management Revenue 触发规则

第一阶段建议支持配置化 Revenue Trigger。

例如：

```text
RULE-MR-001
ShipmentCompleted
+
CommercialAmountConfirmed
=
ManagementRevenueRecognized
```

以后企业可以配置：

- 发货确认；
- 客户验收；
- 特定业务完成节点。

不得把“订单创建”直接等同收入确认。

---

# 6. 多币种总体设计

第一阶段必须原生支持多币种。

每个正式金额至少同时保存：

```text
transaction_currency
transaction_amount

functional_currency
functional_amount

fx_rate
fx_rate_type
fx_rate_date
fx_rate_source
fx_rate_snapshot_ref
```

---

# 7. 三类币种

FAC 定义三层货币概念。

## 7.1 Transaction Currency

原始业务交易币种。

例如：

```text
USD
EUR
GBP
JPY
CNY
```

订单是 USD，则原币永久保存 USD。

---

## 7.2 Functional Currency

企业经营管理功能币种。

宁波恒剑当前 FAC 首个试点建议：

`CNY`

所有跨订单、跨客户、跨月份经营比较统一转换为功能币种。

---

## 7.3 Reporting Currency

未来可选。

例如企业集团需要：

`USD Reporting`

第一阶段预留字段，但不强制实现集团多报表币种。

---

# 8. 金额对象标准

不允许只设计：

```text
amount: 100000
```

正式结构至少：

```text
Money {
    original_amount
    original_currency

    functional_amount
    functional_currency

    fx_rate
    fx_rate_date
    fx_rate_type
    fx_rate_source
    fx_snapshot_id
}
```

---

# 9. ExchangeRatePort

新增 FAC 强制 Port：

```text
ExchangeRatePort
```

接口：

```text
getRate(
    from_currency,
    to_currency,
    rate_date,
    rate_type
)

getRateSnapshot(
    currency_pairs,
    effective_at
)
```

FAC 不直接访问外部汇率网站或银行。

路径：

```text
Exchange Rate Source
        ↓
EDP Adapter
        ↓
FXRate Business Object
        ↓
ExchangeRatePort
        ↓
FAC
```

---

# 10. FXRate 对象

至少包含：

```text
fx_rate_id
base_currency
quote_currency
rate
rate_type
effective_at
source_system
revision
evidence_ref
```

---

# 11. 汇率类型

第一阶段预留：

```text
SPOT
ORDER_DATE
SHIPMENT_DATE
INVOICE_DATE
PAYMENT_DATE
PERIOD_AVERAGE
PERIOD_END
MANUAL_APPROVED
```

第一阶段 FAC 不把某一种汇率写死到代码。

使用：

`FinanceRule`

确定。

---

# 12. 第一阶段推荐汇率规则

建议默认：

### Management Revenue

使用：

`Shipment Date Rate`

### Plan Cost

如果采购/成本本身是外币：

采用：

`Cost Snapshot Effective Rate`

### AR

初始确认：

`Revenue Recognition Rate`

### Collection

实际回款：

`Payment Date Rate`

因此可能产生：

`FXVarianceResult`

---

# 13. 汇兑差异

例如：

订单收入：

USD 100,000

发货日：

```text
USD/CNY = 7.10
```

Management Revenue：

```text
USD 100,000
CNY 710,000
```

实际收款日：

```text
USD/CNY = 7.18
```

实际收到功能币价值：

```text
CNY 718,000
```

形成：

```text
FX Variance = +8,000 CNY
```

第一阶段至少记录差异。

是否进入经营毛利，由 Finance Rule 决定。

---

# 14. 多币种核心原则

必须遵守：

**原币不覆盖。**

**汇率不覆盖。**

**历史 Snapshot 不覆盖。**

因此半年以后重算订单，也能够知道当时使用的是：

```text
USD 100,000
Rate 7.10
Rate Date 2026-xx-xx
Source XXX
Rule Version V1
```

---

# 15. OFA Port 完整版

FAC-OFA 第一阶段 Ports 调整为：

```text
OrderDataPort
BOMDataPort
MaterialPricePort
LaborCostPort
ExpensePort
ActualCostPort
RevenuePort
ExchangeRatePort
QualityCostPort
EvidencePort
```

新增：

**ExchangeRatePort**

---

# 16. OFA Rule Baseline

迁移前不能只冻结订单结果。

必须冻结：

`FAC_OFA_RULE_BASELINE_V1`

至少包括：

| Rule | 内容 |
|---|---|
| R01 | BOM 展开 |
| R02 | BOM 重复行合并 |
| R03 | 自制件成本 Rollup |
| R04 | 外购物料成本 |
| R05 | UOM 换算 |
| R06 | Material Price Priority |
| R07 | Labor Rate |
| R08 | Processing Fee |
| R09 | Expense Allocation |
| R10 | Product Labor Rate |
| R11 | BOM Override |
| R12 | Fallback |
| R13 | Revenue |
| R14 | Currency Conversion |
| R15 | Plan Margin |
| R16 | Actual Margin |

每条规则必须有：

```text
rule_id
rule_version
description
formula
input
output
example
owner
effective_from
```

---

# 17. 物料价格规则

当前系统存在类似：

```text
Material Current Price
→ BOM Price
→ 0
```

V1.1 必须修改成：

```text
Material Price Snapshot at effective_at
      ↓
Approved Fallback Price
      ↓
Missing Price Exception
```

不得静默：

`Missing → 0`

因为 0 会直接产生虚假高毛利。

---

# 18. Missing Price

任何必要物料没有价格：

发布：

```text
MaterialPriceMissing
```

订单状态：

```text
CALCULATION_INCOMPLETE
```

不能把订单标为 Verified。

---

# 19. Actual Cost 双层设计

第一阶段正式拆为：

## EstimatedActualCost

经营过程中实时估算。

数据可能来自：

- 当前领料；
- 当前人工；
- 暂估物流；
- 当前品质损失。

状态：

```text
ESTIMATED
```

---

## FinalActualCost

月结或订单结算完成后形成。

要求：

- 数据完整；
- 对账完成；
- Finance Period 达到规定状态。

状态：

```text
FINAL
VERIFIED
```

---

# 20. Margin 相应拆分

形成：

```text
PlanMarginResult
EstimatedActualMarginResult
FinalActualMarginResult
```

管理页面明确显示三个概念。

不得都叫：

“毛利”。

---

# 21. CalculationRun

新增核心治理对象：

```text
CalculationRun
```

至少：

```text
calculation_id
calculation_type
subject_type
subject_id

input_snapshot_id
input_snapshot_hash

rule_set_id
rule_set_version

previous_calculation_id
previous_result_id

reason
trigger_type

started_at
completed_at

status
actor
```

---

# 22. 计算状态

```text
PENDING
RUNNING
SUCCESS
FAILED
SUPERSEDED
CANCELLED
```

---

# 23. Result 版本机制

正式 Result：

```text
V1
V2
V3
```

状态：

```text
CURRENT
SUPERSEDED
RESTATED
```

禁止：

数据库 UPDATE 直接把 V1 数值覆盖成 V2。

---

# 24. 允许触发重算的场景

包括：

- BOM Revision；
- Material Price Correction；
- Labor Rate Correction；
- FX Rate Correction；
- Actual Cost Update；
- Revenue Adjustment；
- Rule Version Change；
- Manual Approved Recalculation。

---

# 25. 重算流程

```text
Change Detected
      ↓
RecalculationRequired
      ↓
Decision / Policy
      ↓
New CalculationRun
      ↓
Result V2
      ↓
Compare V1 vs V2
      ↓
Verify
      ↓
V1 SUPERSEDED
V2 CURRENT
```

---

# 26. Event Catalog

每个事件必须定义：

```text
Event Name
Publisher
Consumer
Trigger
Object Ref
Payload
Idempotency
Evidence
Retry Policy
```

---

# 27. 第一阶段核心 Event Catalog

## OrderFinanceCalculationRequested

Publisher：

FAC / Human / System

Consumer：

FAC-OFA

---

## PlanCostCalculated

Publisher：

FAC-OFA

Consumer：

- EDP
- Margin Engine
- CFO Agent

---

## ActualCostUpdated

Publisher：

FAC Cost

Consumer：

- Margin Engine
- EDP

---

## MarginCalculated

Publisher：

FAC Margin

Consumer：

- EDP
- EBMS
- CFO Agent
- Risk Engine

Idempotency：

```text
order_id
+
calculation_id
+
rule_version
```

---

## ReceivableOverdue

Publisher：

FAC AR

Consumer：

- AR Agent
- EDP
- EBMS Exception

---

## ARRiskRaised

Publisher：

FAC AR

Consumer：

- AR Agent
- CFO Agent

---

## PaymentReceived

建议原始事实：

EDP 发布。

FAC 消费。

---

## CollectionResultVerified

FAC / M01 Verify 后发布。

EBMS 消费。

---

# 28. Result Verify Matrix

第一阶段明确责任。

| Result | Producer | Submitter | Verifier |
|---|---|---|---|
| ManagementRevenueFact | System | FAC | Finance Owner |
| PlanCostResult | FAC-OFA | System | Cost/Finance Owner |
| EstimatedActualCost | FAC | System | Finance Owner |
| FinalActualCost | FAC | System | Finance Owner |
| MarginResult | FAC | System | Finance Owner |
| Receivable | FAC | System | AR/Finance Owner |
| ARRiskResult | FAC | System | AR Owner |
| BankMatchResult | Skill/Agent | System | Finance Owner |
| CollectionResult | Action Owner | Human/System | Finance Owner |
| FinanceResult | FAC | System | Accountable Finance Owner |

原则：

**Producer ≠ 必然等于 Verifier。**

---

# 29. SoD

高风险财经场景执行：

```text
Maker
→ Checker
→ Approver
→ Executor
→ Verifier
```

第一阶段付款本身不进入 FAC 自动执行范围。

但 Bank Match / Write-off / Manual Adjustment 等同样需要权限隔离。

---

# 30. AR 多币种设计

Receivable 必须保存：

```text
original_amount
original_currency

functional_amount
functional_currency

recognition_fx_rate
recognition_fx_date

paid_original_amount
paid_functional_amount

outstanding_original_amount
outstanding_functional_amount

fx_variance
```

---

# 31. 部分回款

例如：

```text
AR = USD 100,000
Payment 1 = USD 30,000
Payment 2 = USD 50,000
Remaining = USD 20,000
```

每笔 Payment 保存自己的：

`payment_fx_rate`

不得把最后一次汇率应用到全部历史收款。

---

# 32. Bank Match 多币种

第一阶段匹配规则调整为：

### L1 Exact

```text
currency
+
amount
+
customer
+
reference
```

### L2 Strong Candidate

```text
currency
+
amount
+
customer
+
date window
```

### L3 Cross-Currency Candidate

例如客户使用其他币种支付。

必须：

- 找到 FX Evidence；
- 计算功能币差异；
- 人工确认。

不得自动直接核销。

---

# 33. CFO Agent 多币种要求

CFO Agent 在回答：

“这个月收入多少？”

默认使用：

**Functional Currency**

例如：

`CNY 12.58M`

但必须可以展开：

```text
USD 620k
EUR 180k
CNY 6.92M
```

以及：

`FX Impact`

---

# 34. 财经健康首页

第一阶段增加：

### Revenue

原币 + 功能币汇总。

### Margin

统一使用功能币。

### AR

同时展示：

- Functional AR；
- Currency Exposure。

### FX Exposure

新增：

```text
USD Exposure
EUR Exposure
Other Exposure
```

---

# 35. 第一阶段 Object Dictionary

必须生成：

`FAC_MVP_OBJECT_DICTIONARY_V1`

至少包含：

```text
ManagementRevenueFact
PlanCostResult
EstimatedActualCostResult
FinalActualCostResult
MarginResult
Receivable
ARRiskResult
BankMatchResult
CollectionResult
FinanceResult
FXRate
CalculationRun
CalculationSnapshot
```

每个字段定义：

```text
Name
Type
Required
Owner
Source
Meaning
Unit
Currency
Example
Validation
Evidence
```

---

# 36. Test Acceptance Matrix

建立：

`FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1`

不得只有零散 Test Case。

---

# 37. 多币种必测场景

至少加入：

## FX-01

CNY Order → CNY Cost → CNY Payment。

## FX-02

USD Order → CNY Cost → USD Payment。

## FX-03

EUR Order → CNY Cost → EUR Partial Payment。

## FX-04

订单日汇率与回款日汇率不同。

## FX-05

汇率缺失。

应产生：

`FXRateMissing`

而非自动使用 1。

## FX-06

历史汇率被修正。

必须产生新 CalculationRun，不覆盖旧结果。

## FX-07

跨币种付款。

必须人工确认。

---

# 38. OFA 回归测试矩阵

至少：

```text
简单BOM
多级BOM
重复BOM
自制件
委外件
单位换算
价格缺失
价格历史版本
人工费
加工费
费用
Override
Fallback
多币种
汇率变化
Actual Cost变化
```

---

# 39. 第一阶段 Gate 重新定义

## G-1 — Current State

企业现状已调查。

## G0 — Boundary

边界冻结。

## G1 — EDP Readiness

EDP 数据准备通过。

## G2 — Contract

Object/Event/API Contract 通过。

## G3 — Rule Baseline

OFA 规则冻结。

## G4 — Regression

Legacy → FAC 迁移回归通过。

## G5 — Finance Result

Revenue/Cost/Margin 正确。

## G6 — AR Closed Loop

应收闭环完成。

## G7 — Verify

Result 已 Verify。

## G8 — Evidence

核心 Evidence = 100%。

## G9 — EBMS

EBMS 正确消费。

---

# 40. 8 周开发计划 V1.1

## W1 — Current State + Legacy Freeze + Security

完成：

- Current State；
- Legacy Orders；
- OFA Rule Baseline；
- ERP Secret 轮换；
- Direct ERP 依赖盘点；
- Multi-Currency Rule Draft。

退出：

G-1。

---

## W2 — EDP Readiness + Contract + Port

完成：

- EDP Readiness Matrix；
- Object Dictionary；
- EDP/FAC Contract；
- FAC Port；
- ExchangeRatePort；
- Event Catalog V1。

退出：

G0/G1/G2。

---

## W3 — EDP Adapter + FAC Port Integration

完成：

- Order；
- BOM；
- Material Price；
- Labor；
- Expense；
- FX Rate；

从 EDP 进入 FAC。

退出：

FAC Direct ERP Access = 0。

---

## W4 — FAC-OFA Plan Cost + Regression

完成：

- CalculationSnapshot；
- CalculationRun；
- Plan Cost；
- Multi-Currency Conversion；
- Regression Test。

退出：

G3/G4。

---

## W5 — Actual Cost + Margin + Evidence

完成：

- Estimated Actual；
- Plan Margin；
- Estimated Actual Margin；
- FX Variance；
- Evidence；
- Result Version。

退出：

G5/G8。

---

## W6 — AR + Risk + Agent

完成：

- Receivable；
- Aging；
- Multi-Currency AR；
- AR Risk；
- CFO Agent A0；
- AR Agent A1。

---

## W7 — Collection + Bank + Verify + EBMS

完成：

- DecisionCase；
- Collection Action；
- BankTransaction；
- Bank Match；
- Partial Payment；
- FX Variance；
- Verify；
- Finance Result；
- EBMS Card。

退出：

G6/G7/G9。

---

## W8 — UAT + Fix + Go/No-Go

完成：

- Regression；
- Contract；
- Integration；
- E2E；
- Multi-Currency Test；
- Audit；
- Security；
- Business UAT。

最终：

`GO / NO-GO`

---

# 41. MVP Test Data

模拟数据必须至少包含：

- CNY 正常订单；
- USD 正常订单；
- EUR 部分回款；
- 低毛利；
- 多级 BOM；
- 价格缺失；
- 汇率缺失；
- 实际成本超支；
- AR 逾期；
- 银行匹配失败；
- 重算；
- Result Restatement。

真实数据至少：

- 5 个真实订单；
- 至少包含 2 种币种；
- 3 个真实客户；
- 1 个真实逾期；
- 1 个真实部分回款或完整回款。

---

# 42. KPI Definition

所有 KPI 必须进入：

`FAC_MVP_KPI_DICTIONARY_V1`

例如：

## Margin Calculation Coverage

```text
成功形成可信 MarginResult 的订单数
/
应计算订单总数
```

## FX Coverage

```text
拥有有效汇率 Snapshot 的外币财经事实数
/
全部外币财经事实数
```

建议：

`FX Coverage = 100%`

汇率缺失不得进入 Verified。

---

# 43. 第一阶段关键 KPI

```text
Order completeness ≥95%
BOM coverage ≥95%
Material price coverage ≥95%
FX coverage =100%
Margin calculable ≥90%
AR auto matching ≥95%
Evidence coverage =100%
Decision traceability =100%
Direct ERP access =0
Unauthorized high-risk action =0
```

---

# 44. 开发前必须冻结的六个附件

第一阶段正式开发前必须有：

### 01

`FAC_MVP_EDP_READINESS_MATRIX_V1`

### 02

`FAC_OFA_RULE_BASELINE_V1`

### 03

`FAC_MVP_OBJECT_DICTIONARY_V1`

### 04

`FAC_MVP_EVENT_CATALOG_V1`

### 05

`FAC_MVP_RESULT_VERIFY_MATRIX_V1`

### 06

`FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1`

另增加多币种专项：

### 07

`FAC_MVP_CURRENCY_AND_FX_POLICY_V1`

---

# 45. Currency & FX Policy 必须回答

该文件至少冻结：

1. 企业 Functional Currency；
2. 支持币种；
3. Exchange Rate Source；
4. Revenue 使用哪个日期汇率；
5. Cost 使用哪个日期汇率；
6. AR 初始汇率；
7. Payment 汇率；
8. Period End 汇率；
9. FX Variance 处理；
10. 汇率缺失处理；
11. Manual Override 权限；
12. 历史汇率修正机制；
13. Evidence；
14. Recalculation Policy。

---

# 46. Go / No-Go V1.1

## GO

必须同时：

- EDP Readiness 满足 MVP；
- FAC 不直连 ERP；
- ERP Secret 已轮换；
- OFA Rule Baseline 已冻结；
- 多币种 Contract 正确；
- FX Coverage 100%；
- Migration Regression 通过；
- Margin 可解释；
- AR 闭环；
- Bank Match 已 Verify；
- Evidence 100%；
- EBMS 消费成功；
- 无 P0/P1 缺陷。

---

## NO-GO

任一发生：

- 汇率缺失但系统继续计算；
- Missing Price 被当成 0；
- 旧 Result 被直接覆盖；
- 实际成本口径无法区分；
- FAC 绕过 EDP；
- Agent 越权；
- Result 无 Evidence；
- 财经数字无法解释。

立即 NO-GO。

---

# 47. 第一阶段真正的完成定义

最终验收必须能够选一张真实外币或人民币订单，完整演示：

```text
EDP取得订单
→ FAC取得BOM
→ 锁定历史价格
→ 锁定FX Rate
→ Management Revenue
→ Plan Cost
→ Estimated Actual Cost
→ Margin
→ Evidence
→ AR
→ Overdue
→ Agent判断
→ DecisionCase
→ Collection Action
→ Payment
→ Payment FX
→ Bank Match
→ FX Variance
→ Result Verify
→ EBMS
```

并且任何一个金额都可以回答：

**来自哪里？**

**什么币种？**

**用了什么汇率？**

**用了什么规则？**

**什么版本？**

**谁计算？**

**谁验证？**

**Evidence 在哪里？**

只有全部回答清楚，才定义：

# FAC PHASE 1 MVP — PASSED
