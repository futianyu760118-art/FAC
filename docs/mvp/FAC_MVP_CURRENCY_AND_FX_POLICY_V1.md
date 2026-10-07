# FAC MVP Currency & FX Policy V1

## 1. 目的

FAC 从第一阶段开始原生支持多币种。本文件冻结 Money Model、Functional Currency、FX Rate、Recognition、Collection、FX Variance、Recalculation、Evidence。

## 2. Functional Currency

试点企业默认功能币：**CNY**

功能币用于 EBMS 汇总、企业级 Margin、AR 总量、风险、KPI、FinanceResult。FAC 永久保留原币。

## 3. 支持币种

底层使用 ISO 4217。第一阶段至少测试：
```text
CNY
USD
EUR
GBP
JPY
```
系统不硬编码成这五种。

## 4. Money Precision

金额内部禁止使用浮点数，使用 Decimal。精度依据 Currency Metadata。JPY 等零小数币种按标准处理。

## 5. Rounding

第一阶段建议 ROUND_HALF_UP，但必须进入 Rule Registry，不分散硬编码。

## 6. FX Object

```text
FXRate {
  base_currency
  quote_currency
  rate
  rate_type
  effective_at
  source
  revision
  evidence_ref
}
```

## 7. FX Source

FAC 不定义数据供应商：
```text
Approved FX Source
        ↓
EDP Adapter
        ↓
FXRate
        ↓
FAC
```

## 8. Revenue FX

Management Revenue 默认使用 Shipment Date Rate。同一订单多次发货时，每次发货独立 Revenue Fact 和 FX Snapshot。

## 9. Plan Cost FX

每项成本按 Cost Effective Date 取汇率。跨币种成本汇总到 Functional Currency。

## 10. AR Initial Recognition

AR 初始功能币使用 Management Revenue Recognition FX，并保存 recognition_fx_rate、recognition_fx_rate_id、recognition_date。

## 11. Payment FX

回款使用 Payment Date Rate，每笔 Payment 独立保存。

## 12. FX Variance

```text
FXVariance
=
payment_functional_value
-
receivable_functional_value_released
```

FX Variance 单独显示，第一阶段不得静默并入 Product Margin。

## 13. Margin FX Policy

Operating Margin 不含回款阶段汇兑损益。Finance Impact 单独记录 FX Variance。EBMS 可展示 Operating Margin / FX Impact / Net Finance Impact。

## 14. Period End Revaluation

第一阶段数据模型预留 PERIOD_END，但 MVP 不强制完成完整会计外币重估。

## 15. Missing FX

外币正式金额缺 FX 时发布 FXRateMissing，状态 CALCULATION_INCOMPLETE。禁止 rate=1 或静默取最近汇率。

## 16. Manual FX

仅允许 MANUAL_APPROVED，必须有权限、原因、审批、Evidence、Audit。

## 17. FX Correction

历史汇率修正：
```text
FXRateCorrected
→ RecalculationRequired
→ New CalculationRun
→ Result V2
→ Verify
```
原 V1 = SUPERSEDED。

## 18. Cross-Currency Payment

AR=USD、Payment=EUR 时必须保留 EUR Payment，取 EUR/CNY FX，对比 AR 功能币余额，计算差异并人工确认。MVP 禁止自动核销。

## 19. Partial Payment

每次付款独立保存 payment_amount、payment_currency、payment_fx_rate、functional_value。剩余 AR 保留原始币种余额。

## 20. FX Exposure

FAC 首页至少显示 USD/EUR/GBP/JPY/Other 的 AR、expected collection、functional equivalent。

## 21. Evidence

所有 FX 使用必须可回答 rate source、rate date、rate type、snapshot、revision、calculation id。

## 22. ExchangeRatePort

```text
getRate(from_currency,to_currency,rate_date,rate_type)
getRateSnapshot(currency_pairs,effective_at)
```
只连接 EDP。

## 23. 测试规则

必须覆盖 CNY、USD、EUR、JPY、partial payment、FX correction、missing FX、cross-currency、multiple shipment dates。

## 24. MVP 完成条件

任何金额都必须知道：原币、本币、汇率日期、汇率类型、来源与版本；否则不得 VERIFIED。
