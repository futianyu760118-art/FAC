# FAC-OFA Rule Baseline V1

## 1. 目的

本文件冻结现 EBMS“经营中心—订单分析库”迁移进入 FAC 前的核心业务算法语义。

目标不是永久保留旧算法，而是确保：

> **迁移数据架构时，不同时改变财经算法。**

采用：`Freeze → Characterization Test → Port Migration → Rule Improvement`

## 2. Rule 基线结构

每条规则必须具有：
```text
rule_id
rule_name
version
description
input
formula
output
fallback
exception
owner
effective_from
evidence_required
```

初始版本：`OFA-RULESET-V1`

## 3. R01 — BOM Tree Expansion
按产品对应 BOM 构建多级结构。必须保留层级、父子关系、防循环、最大深度、Revision。

异常：
```text
BOM_NOT_FOUND
BOM_LOOP_DETECTED
BOM_DEPTH_EXCEEDED
```

## 4. R02 — Duplicate BOM Merge
满足唯一性条件的重复物料合并数量，必须保存 source_line_refs[] 与 merged_qty。

## 5. R03 — Self-made Item Rollup
自制/委外父节点：
```text
material_cost = Σ child material cost
```
同时保留 processing fee、labor、expense，禁止父件材料价与子件材料价重复计入。

## 6. R04 — Purchased Material Cost
```text
material_cost
=
effective_unit_price
× bom_quantity
× order_quantity
```
必须处理 price unit、BOM unit、currency、effective date。

## 7. R05 — UOM Conversion
至少支持 t、kg、g、pcs、set、m、mm。仅同量纲可自动换算，无法换算时返回 `UOM_CONVERSION_REQUIRED`，不得默认为 1。

## 8. R06 — Material Price Priority
```text
Historical Approved Material Price Snapshot
        ↓
Approved Fallback Price
        ↓
MaterialPriceMissing
```
删除 Missing → 0 语义。价格缺失时为 `CALCULATION_INCOMPLETE`。

## 9. R07 — Direct Labor
Labor Rate 必须包含 version、effective date、currency、source。

## 10. R08 — Outsource / Processing Fee
outsource_labor 与 processing_fee 分别保存，禁止全部并入材料成本。

## 11. R09 — Expense Allocation
第一阶段支持 variable_overhead、fixed_overhead、logistics_cost、quality_loss、allocated_expense。

## 12. R10 — Product Labor Rate
原成品工价继续保留，但升级为 ProductLaborRate + version + effective_date + evidence。

## 13. R11 — BOM Override
必须保存 original_value、override_value、reason、approved_by、approved_at、effective_from、evidence。

## 14. R12 — Fallback
允许 Primary Source → Approved Secondary Source，禁止 Primary missing → silently use 0。

## 15. R13 — Management Revenue
第一阶段：
```text
ShipmentCompleted
+
CommercialAmountConfirmed
→ ManagementRevenueFact
```
不等同于 Accounting Revenue。

## 16. R14 — Currency Conversion
```text
functional_amount = original_amount × approved_fx_rate
```
必须绑定 fx_rate_id、fx_rate_type、fx_rate_date、rule_version。

## 17. R15 — Plan Margin
```text
PlanMargin = ManagementRevenue - PlanCost
PlanMarginRate = PlanMargin / ManagementRevenue
```
Revenue=0 时状态为 NOT_APPLICABLE。

## 18. R16 — Actual Margin
分别计算 EstimatedActualMargin 与 FinalActualMargin，不可混用。

## 19. R17 — Plan vs Actual Variance
```text
CostVariance = ActualCost - PlanCost
MarginVariance = ActualMargin - PlanMargin
```
必须保存 variance_reason。

## 20. R18 — Calculation Snapshot
冻结 Order Revision、BOM Revision、Price Snapshot、Labor Version、Expense Rule、FX Snapshot、Revenue Revision、RuleSet Version。

## 21. R19 — Recalculation
关键输入变化时必须 New CalculationRun → New Result Version，不覆盖旧结果。

## 22. R20 — Missing Critical Input
BOM、Material Price、Currency、FX Rate、Revenue、quantity 任一缺失，状态为 CALCULATION_INCOMPLETE，不允许 Verified。

## 23. Rule Baseline 验收
至少覆盖：简单BOM、多级BOM、重复BOM、自制件、委外件、单位换算、Missing Price、Historical Price、Labor、Processing Fee、Override、Multi-currency、FX change、Recalculation。

所有旧算法差异必须零差异或有正式 ADR。
