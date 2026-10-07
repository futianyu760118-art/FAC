# FAC MVP Result Verify Matrix V1

## 1. 原则

**计算成功 ≠ Result Verified。**

生命周期：
```text
CALCULATED → SUBMITTED → VERIFIED
```
异常：
```text
REJECTED / SUPERSEDED / RESTATED
```

## 2. Verify Matrix

| Result | Producer | Submitter | Verifier | 核心条件 |
|---|---|---|---|---|
| ManagementRevenueFact | FAC F01 | FAC | Finance Owner | Order/Shipment/金额/币种/FX/Rule/Evidence 完整 |
| PlanCostResult | FAC-OFA | System | Cost/Finance Owner | BOM/Price/UOM/Labor/Expense/FX/Snapshot 完整 |
| EstimatedActualCost | FAC | System | Finance Owner | 必须显式 ESTIMATED |
| FinalActualCost | FAC | System | Finance Owner | 对账完成、Period允许、Evidence完整 |
| MarginResult | FAC Margin | System | Finance Owner | Verified Revenue + Eligible Cost + Rule + Snapshot |
| Receivable | FAC AR | System | AR/Finance Owner | Customer/Order/Amount/Currency/Due/Source/Evidence |
| ARRiskResult | FAC Risk | System | AR Owner | HIGH/CRITICAL 必须人类 Review |
| BankMatchResult | Skill/Agent | System | Finance Owner | STRONG/CROSS_CURRENCY 必须人工确认 |
| CollectionResult | Action Owner | Human/System | Finance Owner | Bank Match/金额/FX/AR/Evidence |
| FinanceResult | FAC | System | Accountable Finance Owner | 所有内部引用均 CURRENT + VERIFIED |

## 3. RACI

| 对象 | Responsible | Accountable | Consulted |
|---|---|---|---|
| Revenue | System | Finance Owner | Sales |
| Plan Cost | FAC-OFA | Finance Owner | Delivery/Procurement |
| Actual Cost | FAC | Finance Owner | Delivery/HR/Quality |
| Margin | FAC | Finance Owner | Sales |
| AR | FAC | Finance Owner | Sales |
| Bank Match | FAC Skill | Finance Owner | — |
| Collection | Sales/AR Executor | Finance Owner | Sales Owner |
| FinanceResult | FAC | Finance Accountable Owner | GM |

## 4. SoD

禁止同一主体同时完成：
```text
Manual Adjustment + Approval + Verification
```

Agent 不允许作为高风险 Result 的最终 Verifier。

## 5. Verify Evidence

每次 Verify 记录：
```text
verification_id
result_ref
verifier
verified_at
verification_rule
decision
comment
evidence_refs
```

Reject 时原 Result 保留，写原因并创建修正/重算流程。

## 6. G7 条件

- Verify Matrix 全部实现；
- 关键 Result 100% 有 verifier；
- HIGH risk 无 AI 自验；
- Audit 完整。
