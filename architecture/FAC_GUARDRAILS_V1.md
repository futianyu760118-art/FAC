# FAC_GUARDRAILS_V1

> 上位框架：AEOS V7.2  
> 模块：M09 — FAC（Finance Autonomous Center）  
> 文档性质：强制架构红线 / 开发门禁  
> 适用范围：FAC 全阶段，Phase 1 MVP 起立即生效  
> 版本：V1

## 1. 目的

本文件定义 FAC 的强制红线。

任何需求、设计、代码、PR、测试或上线方案，只要违反本文件任一 P0 红线，必须阻断合并或上线。

红线优先级高于局部实现便利性。

---

# 2. P0 红线

## GR-01 所有跨系统数据必须先进入 EDP

禁止：

```text
FAC → ERP
FAC → SPC
FAC → CRM
FAC → HR
FAC → Bank
FAC → Other Business DB
```

允许：

```text
Source System
→ EDP Adapter
→ Business Object / Event / Evidence
→ FAC
```

若 EDP 尚未具备真实 Adapter，可使用 EDP Mock / Import Adapter。

不得绕过 EDP。

---

## GR-02 FAC 不得直接读写其他模块数据库

禁止跨域：

- direct SQL；
- direct table join；
- shared private table；
- direct file dependency。

跨模块必须通过：

- Object Contract；
- API；
- Event；
- Result；
- Evidence Reference。

---

## GR-03 FAC 不拥有 EDP 的基础治理对象

以下通用基础对象由 M02 EDP 统一负责：

- Business Object 基础注册；
- Event 基础协议；
- Evidence；
- Audit；
- Provenance；
- Value Ledger。

FAC 只能定义财经专业 Profile / Extension。

---

## GR-04 FAC 不重定义 AEOS 全局 Decision / Action 契约

DecisionCase、Decision、Action、Task、Guard 等全局语义由 M01/AEOS Kernel 负责。

FAC 可以：

- 生成财经 DecisionCase Request；
- 提供财经 Evidence；
- 产生专业 Result；
- 调用标准 Action 能力。

FAC 不得建立第二套全局决策状态机。

---

## GR-05 Missing Price 不得静默使用 0

关键物料价格缺失时：

```text
MaterialPriceMissing
→ CALCULATION_INCOMPLETE
```

禁止：

```text
missing price → 0
```

否则会产生虚假高毛利。

---

## GR-06 Missing FX 不得静默使用 1 或无记录回退

外币金额缺少有效汇率时：

```text
FXRateMissing
→ CALCULATION_INCOMPLETE
```

禁止：

- 默认 rate = 1；
- 静默取最近汇率；
- 使用未记录来源的人工汇率。

---

## GR-07 所有正式金额必须保留原币与功能币

Money 对象至少必须保存：

```text
original_amount
original_currency
functional_amount
functional_currency
fx_rate
fx_rate_date
fx_rate_type
fx_rate_source / fx_rate_id
```

原币不得被功能币覆盖。

---

## GR-08 历史结果不得被 UPDATE 覆盖

BOM、价格、人工、FX、Revenue、Actual Cost、Rule 等关键输入发生变化时：

```text
New CalculationRun
→ New Result Version
```

旧 Result 必须保留。

允许状态：

```text
CURRENT
SUPERSEDED
RESTATED
```

禁止静默改写历史数字。

---

## GR-09 规则必须版本化

所有正式财经 Result 必须能追溯：

```text
rule_id
rule_version
effective_from
input_snapshot
calculation_id
```

禁止代码逻辑变化后无法判断历史结果使用了哪套规则。

---

## GR-10 Agent 不拥有正式财经事实

Agent 可以：

- 查询；
- 解释；
- 发现异常；
- 生成建议；
- 生成 DecisionCase Request。

Agent 不得自行成为 Revenue、Cost、Margin、AR、Cash 等正式事实的 Owner。

---

## GR-11 高风险 Result 不允许 AI 自行 Verify

以下场景必须保留人类 Accountable Owner：

- Manual Adjustment；
- Manual FX；
- Bank Match 非 EXACT；
- Write-off；
- Final Actual Cost；
- 重大 Margin Restatement；
- Collection Result；
- 高风险 FinanceResult。

Agent 不得同时：

```text
Generate
+
Approve
+
Verify
```

---

## GR-12 财经高风险动作必须满足 SoD

至少按：

```text
Maker
→ Checker
→ Approver
→ Executor
→ Verifier
```

进行职责隔离。

适用于：

- Payment；
- Bank Transfer；
- Write-off；
- Manual Adjustment；
- Manual FX；
- Budget Major Change；
- Investment；
- Bank Account Change。

---

## GR-13 EBMS 不重新计算 FAC 专业结果

EBMS 只消费 FAC 发布的标准：

```text
FinanceResult
MarginResult
Exception
Evidence
Decision Reference
```

禁止 EBMS 再从底层订单、成本、AR 表重新计算第二套：

- Margin；
- AR；
- Cash；
- ROI。

---

## GR-14 FAC-OFA 不得重新复制一套源系统数据层

FAC-OFA 通过 Port 消费 EDP 数据。

必须采用：

- OrderDataPort；
- BOMDataPort；
- MaterialPricePort；
- LaborCostPort；
- ExpensePort；
- ActualCostPort；
- RevenuePort；
- ExchangeRatePort；
- QualityCostPort；
- EvidencePort。

禁止把 ERP/EBMS 旧数据访问代码原样搬入 FAC。

---

## GR-15 计划成本、估算实际成本、最终实际成本不得混用

必须区分：

```text
PlanCost
EstimatedActualCost
FinalActualCost
```

对应 Margin 同样区分：

```text
PlanMargin
EstimatedActualMargin
FinalActualMargin
```

页面和 API 不得统一含糊显示为“实际成本”或“毛利”。

---

## GR-16 正式 Result 必须有 Evidence

至少以下对象进入 VERIFIED 前必须 Evidence 完整：

- ManagementRevenueFact；
- PlanCostResult；
- FinalActualCostResult；
- MarginResult；
- CollectionResult；
- FinanceResult。

必须支持：

```text
Result
→ Calculation Snapshot
→ Rule
→ Source Object
→ Evidence
```

---

## GR-17 Replay / Retry 不得产生重复财经事实

所有写入型事件消费者必须：

- idempotent；
- auditable；
- traceable。

EDP Event Replay 不得产生重复：

- Revenue；
- AR；
- MarginResult；
- Collection；
- FinanceResult。

---

## GR-18 FAC 不替代法定总账和税务系统

Phase 1 以 Management Finance 为主。

必须区分：

```text
Management Finance
Accounting Finance
Tax Finance
```

禁止将经营口径直接当成法定会计/税务结果。

---

## GR-19 源码不得保存生产 Secret

禁止提交：

- ERP Key；
- ERP Secret；
- Bank Credential；
- API Token；
- Production Password。

必须使用 Secret Management / Environment。

发现历史泄露必须执行：

- Rotate；
- Revoke；
- Secret Scan；
- Audit。

---

## GR-20 G1 未通过不得进入正式 FAC-OFA 业务开发

MVP-1A 开工前至少要求：

- EDP-R1 Order = READY；
- EDP-R2 Order Product = READY；
- EDP-R4 BOM/BOMLine = READY；
- EDP-R5 Material Price = READY；
- EDP-R6 Labor/Expense = READY；
- EDP-R9 FX Rate = READY；
- Evidence/Event/Audit = READY；
- Contract Test 通过。

若未通过，只允许：

- EDP Readiness 补齐；
- Contract；
- Port Skeleton；
- Mock；
- Test Fixture；
- Legacy Baseline。

---

# 3. PR 强制检查

每个 FAC PR 必须回答：

1. 是否新增任何 Direct ERP/DB dependency？
2. 是否绕过 EDP？
3. 是否新增/修改 Money 或 FX 逻辑？
4. 是否修改财经 Rule？
5. 是否可能覆盖历史 Result？
6. 是否新增高风险 Action？
7. 是否需要 Verify / SoD？
8. 是否具备 Evidence？
9. 是否具备 Idempotency？
10. 是否影响 EBMS Contract？
11. 是否新增 Secret？
12. 是否需要 Regression Test？

任意 P0 红线命中且未解决：

```text
PR = BLOCKED
```

---

# 4. Go / No-Go 强制门禁

以下任一发生：

- Direct ERP Access > 0；
- Missing Price 被当 0；
- Missing FX 被当 1；
- Result 被静默覆盖；
- Agent 越权 Verify；
- Finance Result 无 Evidence；
- EBMS 重算 FAC 财经结果；
- Production Secret 进入仓库；
- 高风险 Action 无 SoD；
- Replay 产生重复财经事实；

结论：

```text
NO-GO
```

---

# 5. 违反红线的处理

发现红线问题时：

```text
Issue Raised
→ Severity = P0
→ Stop Merge / Stop Release
→ Corrective Action
→ Regression Test
→ Evidence
→ Re-review
```

不得以“临时上线后再改”为理由豁免。

---

# 6. 生效规则

本文件自合并 main 起生效。

若与下位开发文档冲突：

```text
AEOS V7.2 Controlled Baseline
> FAC_GUARDRAILS_V1
> FAC 总体方案
> FAC MVP 方案
> Attachment
> Implementation
```

任何红线变更必须：

- 明确版本；
- PR；
- 架构评审；
- 影响分析；
- 测试更新；
- 保留历史版本。
