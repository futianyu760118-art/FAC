# FAC MVP Object Dictionary V1

## 1. 原则

对象分三类：EDP Source Object、FAC Finance Object、FAC Result Object。

通用字段继承 AEOS：
```text
tenant_id
id
version
source_system
created_at
updated_at
correlation_id
trace_id
evidence_refs
```

## 2. Money
```text
original_amount: decimal
original_currency: ISO4217
functional_amount: decimal
functional_currency: ISO4217
fx_rate: decimal?
fx_rate_id: string?
fx_rate_type: enum?
fx_rate_date: date?
```
CNY→CNY 时 fx_rate=1，但仍保存 currency。

## 3. ManagementRevenueFact
Owner：FAC F01
```text
revenue_fact_id
order_id
shipment_id
customer_id
product_id
recognized_qty
amount: Money
recognition_date
recognition_rule_id
recognition_rule_version
accounting_revenue_ref?
invoice_ref?
status
evidence_refs
```

## 4. PlanCostResult
Owner：FAC-OFA
```text
result_id
order_id
material_cost: Money
labor_cost: Money
processing_cost: Money
expense_cost: Money
logistics_cost: Money
quality_cost: Money
total_cost: Money
calculation_id
snapshot_id
rule_set_version
status
evidence_refs
```

## 5. EstimatedActualCostResult
包含 material、labor、expense、logistics、quality、total、completeness_ratio、calculation_id、evidence_refs，cost_status=ESTIMATED。

## 6. FinalActualCostResult
增加 finance_period_id、reconciled、verified_at、verified_by，cost_status=FINAL。

## 7. MarginResult
```text
result_id
order_id
margin_type: PLAN | ESTIMATED_ACTUAL | FINAL_ACTUAL
revenue: Money
cost: Money
margin: Money
margin_rate
target_margin_rate
variance_amount
variance_rate
calculation_id
rule_version
risk_level
status
evidence_refs
```

## 8. Receivable
Owner：FAC F04
```text
ar_id
customer_id
order_id
invoice_id?
original_amount
original_currency
functional_amount
functional_currency
recognition_fx_rate
recognition_fx_rate_id
due_date
paid_original_amount
paid_functional_amount
outstanding_original_amount
outstanding_functional_amount
aging_days
status
risk_level
evidence_refs
```

## 9. ARRiskResult
包含 risk_result_id、ar_id、customer_id、aging_days、outstanding_amount、risk_level、risk_rule_id、risk_reason[]、suggested_action[]、decision_case_ref、status、evidence_refs。

## 10. FXRate
EDP Owner / FAC Consumer。
```text
fx_rate_id
base_currency
quote_currency
rate
rate_type
effective_at
source_system
source_record_ref
revision
status
evidence_ref
```

## 11. BankTransaction
EDP Owner。FAC 不修改原始 BankTransaction。

## 12. BankMatchResult
包含 match_result_id、bank_transaction_id、ar_id、collection_action_id、match_level、match_score、matched_original_amount、matched_functional_amount、fx_rate_id、fx_variance、status、manual_confirmation_required、evidence_refs。

## 13. CollectionResult
包含 result_id、ar_id、action_id、bank_match_result_id、expected_amount、actual_amount、remaining_amount、payment_date、status、submitted_by、verified_by、verified_at、evidence_refs。

## 14. FinanceResult
供 EBMS 消费：
```text
result_id
period
management_revenue
plan_cost
estimated_actual_cost
final_actual_cost?
plan_margin
estimated_actual_margin
final_actual_margin?
ar_total
overdue_ar
collected_amount
fx_impact
risk_count
critical_risk_count
status
verified_at
evidence_refs
```

## 15. CalculationRun
包含 calculation_id、calculation_type、subject_type、subject_id、input_snapshot_id/hash、rule_set_id/version、previous_calculation_id/result_id、trigger_type、reason、status、started_at、completed_at、actor、trace_id。

## 16. CalculationSnapshot
冻结 order_revision、shipment_revision、bom_revisions[]、price_snapshot_refs[]、labor_rule_refs[]、expense_rule_refs[]、fx_rate_refs[]、revenue_fact_ref、rule_set_version、checksum、created_at。

## 17. 对象引用规则
跨模块只能用 object_type + object_id + source_system + revision，禁止 FAC 保存外部表 PK 并直接 join 外部数据库。

## 18. 必填质量规则
ManagementRevenueFact、PlanCostResult、FinalActualCostResult、MarginResult、CollectionResult、FinanceResult 缺 Evidence 时不得进入 VERIFIED。
