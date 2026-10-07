# FAC MVP — EDP Readiness Matrix V1

## 1. 目的

本文件定义 FAC Phase 1 MVP 对 EDP 的数据与平台能力依赖，并作为 **G1 — EDP Readiness Gate** 的正式验收依据。

核心原则：

> FAC 不允许因为 EDP 某个领域对象尚未完成，就直接连接 ERP、SPC、财务软件、银行或其他源系统。

缺失能力应在 EDP 侧通过 Source Adapter、Import Adapter、Mock Adapter、Business Object、Event、Evidence 进行补齐。

## 2. 当前平台基础能力

根据当前 EDP 仓库实际结构，以下平台能力可认定已经具有实现基础：

| 能力 | 状态 | FAC判断 |
|---|---|---|
| Business Object Registry | READY | 可作为 FAC 领域对象登记底座 |
| Event API | READY | 已有事件模块、Schema、Service、集成测试 |
| Event Idempotency | READY | 已有 UUIDv5 / Idempotency 设计 |
| Outbox | READY | 可用于事件分发 |
| Evidence | READY | 已有 Evidence 模块及集成测试 |
| Audit | READY | 已有 Audit 模块及测试 |
| Authentication | READY | JWT/API Key |
| RBAC | READY | 可用于 FAC 服务主体授权 |
| Tenant/RLS | READY | 已具备隔离基线 |
| OpenAPI Contract Gate | READY | 可用于 FAC/EDP Contract 冻结 |
| Source Adapter Framework | PARTIAL | 框架存在，FAC 领域 Adapter 仍需补充 |

## 3. FAC MVP 数据 Readiness

### EDP-R1 Order
状态：**PARTIAL**

最低字段：
```text
order_id
order_no
customer_id
order_date
currency
amount
payment_term
status
revision
source_system
```

退出条件：EDP 可按 ID 查询；支持 revision；source 可追踪；FAC 不直接读 ERP。

### EDP-R2 Order Product
状态：**NOT_READY / 待领域实现确认**

最低字段：
```text
order_id
line_id
product_id
product_code
bom_no
quantity
unit_price
currency
revision
```

### EDP-R3 Shipment
状态：**NOT_READY / MVP-1B 阻塞项**

最低字段：
```text
shipment_id
order_id
product_id
shipment_date
shipped_qty
status
revision
```

### EDP-R4 BOM / BOMLine
状态：**NOT_READY / MVP-1A 阻塞项**

最低能力：BOM Header、BOM Revision、BOM Tree、effective date、material attribute、UOM、hierarchy。

### EDP-R5 Material Price
状态：**NOT_READY / MVP-1A 阻塞项**

禁止只存 current_price，必须提供：
```text
material_code
unit_price
currency
price_unit
effective_from
effective_to
source
revision
```

### EDP-R6 Labor / Expense
状态：**NOT_READY**

Labor 至少包含：direct_labor、outsource_labor、processing_fee、product_labor_rate。  
Expense 至少包含：variable_overhead、fixed_overhead、logistics_cost、quality_loss、allocated_expense。

### EDP-R7 Invoice / AR
状态：**NOT_READY / MVP-1B 阻塞项**

### EDP-R8 BankTransaction
状态：**NOT_READY / MVP-1B 阻塞项**

### EDP-R9 FX Rate
状态：**NOT_READY / MVP-1A 阻塞项**

必须支持多币种、Effective Date、Rate Type、Source、Revision、Evidence。

### EDP-R10 Evidence
状态：**READY**

### EDP-R11 Event
状态：**READY**

### EDP-R12 Audit
状态：**READY**

## 4. Readiness 总表

| ID | 能力 | 当前判断 | Phase |
|---|---|---|---|
| R1 | Order | PARTIAL | 1A |
| R2 | Order Product | NOT_READY | 1A |
| R3 | Shipment | NOT_READY | 1B |
| R4 | BOM/BOMLine | NOT_READY | 1A |
| R5 | Material Price | NOT_READY | 1A |
| R6 | Labor/Expense | NOT_READY | 1A |
| R7 | Invoice/AR | NOT_READY | 1B |
| R8 | Bank Transaction | NOT_READY | 1B |
| R9 | FX Rate | NOT_READY | 1A |
| R10 | Evidence | READY | 1A |
| R11 | Event | READY | 1A |
| R12 | Audit | READY | 1A |

## 5. MVP-1A 最低 EDP 出口

```text
Order
OrderProduct
BOM
BOMLine
MaterialPrice
LaborCost
Expense
FXRate
```

## 6. MVP-1B 最低 EDP 出口

```text
Shipment
Invoice
ReceivableSource
BankTransaction
```

## 7. 临时 Adapter 原则

允许：
```text
CSV / Excel / JSON
        ↓
EDP Import Adapter
        ↓
Business Object
        ↓
FAC
```

禁止：
```text
CSV / ERP
   ↓
FAC directly
```

## 8. G1 退出条件

只有同时满足以下条件才能通过：

- R1/R2/R4/R5/R6/R9 对 MVP-1A 达到 READY；
- Evidence READY；
- Event READY；
- Audit READY；
- FAC 无 Direct ERP；
- Contract 测试通过；
- 数据对象存在 owner/revision/source/evidence；
- Mock 与真实 Adapter 使用同一 Contract。

**当前结论：EDP 平台底座 READY，但 FAC 专业数据域尚未 READY，因此当前 G1 = NOT PASSED。**
