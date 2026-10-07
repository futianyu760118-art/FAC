# FAC Phase 1 MVP 受控文档索引

> 上位框架：AEOS V7.2  
> 模块：M09 — FAC（Finance Autonomous Center）  
> 当前阶段：Phase 1 MVP  
> 状态：PRE-DEVELOPMENT / G1 NOT PASSED  
> 更新日期：2026-10-07

## 1. 上位文档

0. `../../architecture/FAC_GUARDRAILS_V1.md` — **FAC 强制架构红线与 PR/Go-No-Go 门禁，优先级高于下位实现文档。**
1. `../FAC_完整总体方案与分阶段实施计划_V2.1.md` — FAC 完整终局方案与九个月实施路线。
2. `../FAC_第一阶段_MVP_开发执行方案_V1.1.md` — 第一阶段 MVP 开发执行基线。
3. `../FAC_行动计划_V1.0.md` — 历史行动计划，保留用于版本追溯。

## 2. Phase 1 前置附件

01. `FAC_MVP_EDP_READINESS_MATRIX_V1.md`  
用于判定 EDP 是否具备 FAC MVP 所需的 Order/BOM/Price/Labor/AR/Bank/FX 等数据能力。

02. `FAC_OFA_RULE_BASELINE_V1.md`  
冻结 EBMS 订单分析库迁移前的 BOM、物料价格、人工、费用、毛利、多币种、重算等规则语义。

03. `FAC_MVP_OBJECT_DICTIONARY_V1.md`  
冻结 ManagementRevenueFact、PlanCostResult、MarginResult、Receivable、FXRate、CalculationRun 等对象字段。

04. `FAC_MVP_EVENT_CATALOG_V1.md`  
冻结 Publisher/Consumer/Trigger/Idempotency/Evidence/Replay 等事件契约。

05. `FAC_MVP_RESULT_VERIFY_MATRIX_V1.md`  
冻结每个财经 Result 的 Producer、Submitter、Verifier、SoD 与 Verify 条件。

06. `FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md`  
定义 Contract/Regression/Integration/E2E/Security/UAT 测试与 Go/No-Go 门槛。

07. `FAC_MVP_CURRENCY_AND_FX_POLICY_V1.md`  
冻结多币种 Money Model、功能币、汇率、部分回款、汇兑差异与历史重算政策。

## 3. 当前 Gate 状态

当前判断：

- EDP 平台底座：READY
- Event：READY
- Evidence：READY
- Audit：READY
- FAC 专业数据对象：部分未 READY
- G1 EDP Readiness：**NOT PASSED**

因此当前工程顺序固定为：

```text
W1 Current State + Legacy Freeze + Security
↓
W2 EDP Readiness + Contract + Port
↓
W3 EDP Adapter + FAC Port Integration
↓
W4 FAC-OFA Plan Cost + Regression
↓
W5 Actual Cost + Margin + Evidence
↓
W6 AR + Risk + Agent
↓
W7 Collection + Bank + Verify + EBMS
↓
W8 UAT + Go/No-Go
```

## 4. 开发红线

> 完整强制条款见 `../../architecture/FAC_GUARDRAILS_V1.md`。以下仅为摘要；发生冲突时以 Guardrails 文件为准。

- FAC 不得直接连接 ERP/SPC/CRM/HR/Bank。
- 所有跨系统数据必须先进入 EDP。
- Missing Price / Missing FX 不允许静默使用 0 或 1。
- 旧 Result 不允许被 UPDATE 覆盖，必须通过 CalculationRun 产生新版本。
- Agent 不拥有正式财经事实。
- 高风险 Result 不允许 AI 自行 Verify。
- EBMS 只消费 FAC FinanceResult，不重新计算专业财经结果。

## 5. Phase 1 开工条件

正式进入 FAC-OFA 开发前至少满足：

- MVP-1A 必需的 EDP-R1/R2/R4/R5/R6/R9 = READY；
- Event / Evidence / Audit = READY；
- OFA Rule Baseline 已冻结；
- EDP/FAC Contract Test 通过；
- ERP Secret 已轮换；
- FAC Direct ERP Access = 0。
