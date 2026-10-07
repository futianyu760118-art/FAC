# FAC MVP Test Acceptance Matrix V1

## 1. 测试层级

```text
UT   Unit
CT   Contract
RT   Regression
IT   Integration
E2E  End-to-End
SEC  Security
UAT  Business Acceptance
```

## 2. Contract Test

- CT-01 EDP→FAC Order：Schema/Revision/Source/Tenant。
- CT-02 BOM：层级/Revision/UOM。
- CT-03 MaterialPrice：effective_at/currency/revision。
- CT-04 FX：rate/date/type/source。
- CT-05 Evidence：link/checksum/reverse trace。
- CT-06 FAC→EBMS：EBMS 不读取 FAC 内部表即可展示 FinanceResult。

## 3. OFA Regression

- RT-01 Simple BOM：与 Legacy Baseline 一致。
- RT-02 Multi-level BOM：树与成本 Rollup 一致。
- RT-03 Duplicate Node：合并规则正确。
- RT-04 Self-made：父子成本无重复。
- RT-05 Outsource：加工费正确。
- RT-06 UOM：单位换算正确。
- RT-07 Missing Price：CALCULATION_INCOMPLETE。
- RT-08 Historical Price：老订单不使用新价格。
- RT-09 Override：保留 before/after Evidence。

## 4. Multi-Currency

- FX-01 CNY→CNY：rate=1。
- FX-02 USD Order/CNY Cost：原币+功能币正确。
- FX-03 EUR Partial Payment：每笔 Payment 独立汇率。
- FX-04 Rate Change：产生 FX variance。
- FX-05 Missing FX：计算阻断。
- FX-06 FX Correction：创建新 CalculationRun。
- FX-07 Cross Currency Payment：人工确认。
- FX-08 JPY Zero-decimal Handling：金额精度正确。

## 5. Calculation Version

- CV-01 BOM Revision：Result V2。
- CV-02 Price Correction：旧 V1 保留。
- CV-03 Rule Version：不可覆盖旧结果。
- CV-04 Replay Same Request：不得重复 Result。

## 6. AR

- AR-01 Normal：LOW。
- AR-02 1–30 Days：MEDIUM。
- AR-03 31–60：HIGH。
- AR-04 >60：CRITICAL。
- AR-05 Partial Payment：余额正确。
- AR-06 Full Payment：PAID。
- AR-07 Disputed：不得自动催收升级。

## 7. Bank Match

- BM-01 Exact。
- BM-02 Same Amount Multiple AR：不得误匹配。
- BM-03 Reference Match。
- BM-04 Cross Currency：需确认。
- BM-05 Partial：正确拆分。

## 8. Closed Loop

- E2E-01 正常订单→正常回款。
- E2E-02 低毛利→Exception。
- E2E-03 逾期→DecisionCase→Action→Payment→Verify。
- E2E-04 外币逾期→回款汇率差→Verify。

## 9. Evidence

- EV-01 Margin 可穿透 Order→BOM→Price→Rule。
- EV-02 Collection 可穿透 AR→Action→BankTransaction。
- EV-03 Checksum 异常：Verify Fail。

## 10. Security

- SEC-01 FAC 无 ERP Secret。
- SEC-02 FAC 无 Direct ERP Network Call。
- SEC-03 跨租户拒绝。
- SEC-04 Agent 尝试 Verify 高风险 Result：拒绝。
- SEC-05 Manual FX 无权限：拒绝。

## 11. Performance MVP

常规订单财经详情 P95 < 2s。复杂 BOM 首次计算单独建立性能基线，不以性能换正确性。

## 12. UAT 样本

至少：5 orders、3 customers、2 currencies、1 overdue、1 collection、1 complex BOM、1 calculation change。

## 13. Go 阈值

| 指标 | 门槛 |
|---|---:|
| Contract Test | 100% |
| Legacy Regression | 100%或批准差异 |
| FX Coverage | 100% |
| Evidence Coverage | 100% |
| Decision Traceability | 100% |
| Unauthorized Action | 0 |
| Direct ERP Access | 0 |
| P0/P1 Defects | 0 |

## 14. Test Evidence

每个 Gate 保存 test_run_id、commit_sha、environment、dataset_version、passed/failed、report_ref、verifier。
