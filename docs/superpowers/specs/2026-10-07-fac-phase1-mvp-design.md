# FAC Phase 1 MVP Design

**日期：** 2026-10-07  
**仓库：** `D:\FAC`  
**依据：** `architecture/FAC_GUARDRAILS_V1.md`、`docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md` 以及 `docs/mvp/` 下的六份冻结附件

## 1. 目标与范围

本设计把 FAC Phase 1 落成一个可本地运行、可测试、可审计的模块化单体，并按两个可独立验收的垂直切片交付：

- **MVP-1A / FAC-OFA：** 从 EDP Order、BOM、Material Price、Labor、Expense、FX 输入生成 PlanCostResult、EstimatedActualCostResult、FinalActualCostResult、MarginResult 和 Evidence。
- **MVP-1B / Order-to-Cash：** 从 MarginResult 生成 Receivable，完成 Aging、ARRiskResult、Collection Action、BankMatchResult、CollectionResult、Verify 和 FinanceResult。

第一阶段的本地版本使用 EDP Mock/Import Adapter 代替尚未接入的真实 EDP。Adapter 的输入输出遵守 EDP/FAC 合同；FAC 不直接访问 ERP、SPC、CRM、HR、Bank 或其他业务数据库。真实 EDP 接入时只替换 Adapter，不改变专业计算核心。

不在本阶段实现完整法定总账、税务、自动跨币种核销、完整期末外币重估或由 Agent 直接写入财经事实。Agent 仅提供查询、解释、异常发现和 DecisionCase 请求能力。

## 2. 技术方案

采用 Python 3.11 模块化单体：

- FastAPI：HTTP API、OpenAPI 和健康检查；
- Pydantic v2：外部契约、输入校验和事件 Envelope；
- SQLAlchemy 2.x + Alembic：持久化和数据库迁移；
- SQLite：本地默认数据库；PostgreSQL：生产兼容目标；
- Decimal：所有金额计算，禁止使用浮点数；
- pytest：UT、CT、RT、IT、E2E、SEC 测试；
- Docker Compose：本地一键启动 API 与 PostgreSQL profile；
- Ruff/格式化与静态检查：统一 Python 质量门禁。

目录按业务边界组织，而不是按数据库表组织：

```text
src/fac/
  api/             HTTP 路由、依赖注入、错误映射
  contracts/       Object/Event/Result/Evidence 外部模型
  domain/
    money/         Money、FX、货币精度和舍入规则
    calculation/   CalculationRun、Snapshot、版本状态
    evidence/      Evidence Reference、审计引用
    events/        Event Envelope、幂等和发布接口
  adapters/
    edp_mock/      本地 JSON fixture/import Adapter
    persistence/   SQLAlchemy repositories
  modules/
    ofa/           BOM rollup、成本和毛利
    ar/            Receivable、Aging、Risk、Collection
    bank/          BankMatch proposal/confirmation
    finance/       Verify、FinanceResult
  bootstrap/       配置、数据库、样例数据
```

数据库表为 FAC 自有专业对象及审计投影；EDP 基础对象仍以 `object_type + object_id + source_system + revision` 引用，禁止通过外部主键做跨库 join。

## 3. 核心数据与不变量

### 3.1 通用字段

所有 FAC 对象和 Result 至少携带 `tenant_id`、`id`、`version`、`source_system`、`created_at`、`updated_at`、`correlation_id`、`trace_id` 和 `evidence_refs`。跨租户查询必须由服务层和数据库查询条件同时约束。

### 3.2 Money 与 FX

`Money` 同时保存：

```text
original_amount
original_currency
functional_amount
functional_currency
fx_rate
fx_rate_date
fx_rate_type
fx_rate_id / fx_rate_source
```

试点功能币为 CNY；支持 ISO 4217，测试覆盖 CNY、USD、EUR、GBP、JPY。金额使用 Decimal；舍入规则进入 Rule Registry，默认 `ROUND_HALF_UP`。CNY→CNY 仍显式保存 `fx_rate=1` 和汇率元数据。

缺失物料价格发布 `MaterialPriceMissing`，计算状态为 `CALCULATION_INCOMPLETE`；缺失汇率发布 `FXRateMissing`，不得使用 0、1 或未记录来源的最近汇率。人工汇率只有 `MANUAL_APPROVED` 并具备权限、原因、审批、Evidence 和 Audit 才能使用。

### 3.3 版本与重算

每次计算先创建 `CalculationSnapshot`，冻结订单、发运、BOM、价格、人工、费用、汇率和规则版本；随后创建 `CalculationRun`。输入或规则发生变化时创建新的 CalculationRun 与 Result version，旧结果仅能变为 `SUPERSEDED` 或 `RESTATED`，不得 UPDATE 覆盖历史数字。

每个正式 Result 保存 `rule_id/rule_version`、`input_snapshot_id/hash`、`calculation_id`、`previous_result_id` 和 Evidence 引用。写入型事件使用稳定幂等键，重放不得生成重复 Result。

### 3.4 Result 状态与 Verify

Result 状态至少包括 `DRAFT`、`CALCULATION_INCOMPLETE`、`PENDING_VERIFY`、`VERIFIED`、`SUPERSEDED`、`RESTATED`。缺少 Evidence 的 ManagementRevenueFact、PlanCostResult、FinalActualCostResult、MarginResult、CollectionResult、FinanceResult 不得进入 `VERIFIED`。

高风险场景（Final Actual Cost、Manual FX、非 EXACT Bank Match、Write-off、CollectionResult、重大 Margin Restatement）必须由具备权限的人类 Verifier 完成；Agent 不得代替 Verify。

## 4. 业务数据流

### 4.1 MVP-1A

```text
EDP Mock/Import
  -> Order/BOM/Price/Labor/Expense/FX snapshot
  -> CalculationRun
  -> PlanCostResult
  -> Estimated/Final Actual Cost
  -> ManagementRevenueFact
  -> MarginResult
  -> Evidence + Event outbox
```

OFA 至少支持简单 BOM、多级 BOM、重复节点、自制件、委外件、单位换算、历史价格、Override/Fallback 和成本缺失阻断。计划成本、估算实际成本、最终实际成本必须使用不同 `margin_type/cost_status`，不得在 API 或页面中混称为“实际成本”。

### 4.2 MVP-1B

```text
MarginResult
  -> Receivable
  -> Aging / ARRiskResult
  -> DecisionCase Request / Collection Action reference
  -> Payment + BankTransaction reference
  -> BankMatchResult
  -> CollectionResult
  -> human Verify
  -> FinanceResult
```

每笔 Payment 独立保存金额、币种、付款日汇率和功能币价值。部分回款保留原币余额；跨币种付款只提出匹配建议并要求人工确认，不自动核销。FX Variance 单独记录，不并入 Product Margin。

## 5. 接口与事件

HTTP API 首批接口：

- `GET /health`：健康状态；
- `POST /api/v1/import/edp-fixture`：导入带 schema/revision/source 的 EDP fixture；
- `POST /api/v1/calculations/orders/{order_id}`：创建订单计算；
- `GET /api/v1/calculations/{calculation_id}`：查询 CalculationRun、Snapshot 和结果；
- `GET /api/v1/orders/{order_id}/margin`：查询版本化 MarginResult；
- `GET /api/v1/ar/{ar_id}`：查询 Receivable、Aging 和 Risk；
- `POST /api/v1/collections/{ar_id}/match-proposals`：生成 BankMatch proposal；
- `POST /api/v1/collections/{collection_id}/verify`：人类 Verify；
- `GET /api/v1/finance/results`：查询 EBMS 可消费的 FinanceResult；
- `GET /api/v1/evidence/{evidence_id}`：反向穿透 Evidence。

事件统一使用 Event Catalog V1 的 Envelope：`event_id`、`event_type`、`version`、`object_ref`、`source_system`、`occurred_at`、`actor_id`、`correlation_id`、`causation_id`、`trace_id`、`payload_version`、`payload`、`evidence_refs`、`idempotency_key`。事件先写入可审计的 outbox，再由本地 dispatcher 发布；同一幂等键重复消费返回既有结果。

## 6. 失败处理与安全

- 输入 schema、tenant、revision、currency 和权限不通过时拒绝请求，不进入计算；
- 缺价格/缺汇率返回可解释的 `CALCULATION_INCOMPLETE`，并保存对应异常事件；
- 计算失败不写入半成品 VERIFIED Result；CalculationRun 标记 `FAILED` 并保留 trace；
- Verify 失败只改变 Verify 状态，不修改原始计算数字；
- 所有写操作需要 actor、correlation、causation 和 Audit；
- Secret 只来自环境变量/Secret Manager，仓库不保存生产 Secret；
- 对象查询按 tenant 隔离；禁止 FAC direct ERP network call；
- API 只返回合同字段，不暴露内部表结构；EBMS 只能消费 FinanceResult。

## 7. 测试与验收

测试从第一批生产代码前开始：每个域行为先写失败测试，再写最小实现。最低覆盖：

- Contract：Order/BOM/Price/FX/Evidence/FinanceResult schema、revision、source、tenant；
- OFA Regression：RT-01 至 RT-09；
- FX：FX-01 至 FX-08，包括缺汇率、修正、跨币种、部分付款、JPY 精度；
- Calculation Version：CV-01 至 CV-04；
- AR/Bank：AR-01 至 AR-07、BM-01 至 BM-05；
- E2E：正常订单、低毛利、逾期催收、外币回款；
- Evidence：正向穿透和 checksum 异常；
- Security：无 ERP Secret、无 direct ERP call、跨租户拒绝、Agent Verify 拒绝、无权限 Manual FX 拒绝。

Phase 1 本地 Go/No-Go 需要记录 `test_run_id`、`commit_sha`、`environment`、`dataset_version`、`passed/failed`、`report_ref` 和 `verifier`，并达到 Contract 100%、FX 100%、Evidence 100%、Decision Traceability 100%、Unauthorized Action 0、Direct ERP Access 0、P0/P1 Defects 0。

## 8. 交付顺序

1. **Foundation：** 配置、数据库、通用字段、Money/FX、Evidence、Event、错误模型、健康检查和测试工具。
2. **MVP-1A：** EDP fixture、OFA ports、snapshot/run、Plan Cost、Actual Cost、Revenue、Margin、Evidence、回归矩阵。
3. **MVP-1B：** Receivable、Aging、Risk、Collection、Bank Match、Verify、FinanceResult、闭环 E2E。
4. **Operator surface：** OpenAPI、种子数据、最小查询界面/示例脚本、Docker Compose、开发与验收文档。

每个交付单元都必须能独立运行和测试；真实 EDP、M01 DecisionCase、EBMS 连接保留为合同兼容的 Adapter，不把外部系统不可用伪装成 FAC 已完成。

