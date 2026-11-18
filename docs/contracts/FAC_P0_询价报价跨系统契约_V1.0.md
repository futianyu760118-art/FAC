# FAC P0 询价报价跨系统契约 V1.0

## 主链

M05 InquiryCreated
→ M04 ProductConfigurationConfirmed
→ M04 SpecificationConfirmed
→ M04 BOMReleased
→ M09 QuoteFinanceCalculated
→ M01 FinanceGuardEvaluated
→ M05 QuoteApprovedForCustomer
→ M05 SalesOrderConfirmed
→ M09 OrderFinanceStarted

## 核心对象

### Inquiry
- inquiry_id
- customer_id
- product_request
- quantity
- currency
- payment_terms
- incoterms
- target_delivery_date
- special_requirements

### ProductConfigurationRef
- product_id
- configuration_id
- specification_id
- specification_version
- bom_id
- bom_revision

### QuoteFinanceResult
- inquiry_id
- quote_version
- revenue_cny
- total_cost_cny
- gross_profit_cny
- gross_margin_rate
- floor_unit_price_original
- target_unit_price_original
- recommended_unit_price_original
- risk_level
- rule_id
- rule_version
- calculation_method

## 三化融合要求

已知事实必须通过EDP自动带出，不得重复录入。
不能自动确定的字段优先使用标准选择。
自由文本只允许用于无法结构化的业务说明。

## 财务红线

正式成本、毛利、价格底线、现金、ROI等数值必须由确定性Skill/规则产生。
LLM只能解释与建议，不得直接写正式财务数值。
