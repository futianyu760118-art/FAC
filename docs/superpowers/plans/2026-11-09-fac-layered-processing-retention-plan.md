# FAC Layered Processing and Retention Standard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已确认的“微系统可独立处理业务、微系统保留 1 周、中心系统保留 3 个月、EDP 长期存储”同步到 FAC 的受控架构、实施和验收文档。

**Architecture:** 采用文档基线更新，不改变当前运行时代码。微系统是本域业务动作的第一处理点，中心系统承接中心级协同和中期查询，EDP 负责跨系统标准化、审计和长期归档；各层通过标准 API、事件或可靠消息同步，并保持重试、幂等和可追踪。

**Tech Stack:** Markdown 文档；PowerShell `rg`；Git diff 检查。

**Spec:** `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

## Global Constraints

- 每个微系统页面必须支持本域业务的录入、提交、处理、状态跟踪和结果反馈。
- 微系统数据保留不少于 7 天。
- 各中心系统数据保留不少于 3 个月。
- EDP 对跨系统共享、审计或长期追溯数据进行标准化、版本化、证据化和长期存储。
- 数据同步必须可重试、幂等、可追踪；不得因短暂的上层不可用而静默丢失业务事实。
- 下层数据清理必须以目标层已确认接收并通过完整性校验为前提。
- 近期查询优先访问微系统；三个月内运营查询优先访问中心系统；更早或审计查询访问 EDP。
- 微系统不得绕过既定数据契约直接读写其他系统数据库。

## Review Focus

- 上层系统暂时不可用时，微系统本地业务是否仍可完成并留下待同步状态；由 Task 3 的同步失败验收检查覆盖。
- 重复投递或重放事件时，中心系统和 EDP 是否幂等且不重复生成业务结果；由 Task 4 的重复投递测试覆盖。
- 同步尚未确认时是否发生本地清理；由 Task 4 的清理前置条件测试覆盖。
- 7 天和 3 个月边界查询是否无数据空洞；由 Task 4 的边界路由测试覆盖。
- 是否出现微系统到其他系统的直接数据库访问或未登记接口；由 Task 1 和 Task 5 的红线检查覆盖。

---

### Task 1: 更新 FAC 强制架构红线

**Files:**
- Modify: `architecture/FAC_GUARDRAILS_V1.md`
- Reference: `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

**Interfaces:**
- Consumes: approved layered processing and retention rules from the spec.
- Produces: a P0 guardrail covering micro-system business completeness, retention floors, reliable propagation, and safe cleanup.

- [ ] **Step 1: Add the layered processing and retention guardrail**

  Add a new P0 rule after the existing data-boundary rules. State that each micro-system page is the first processing point for its own domain, micro-system retention is at least 7 days, center-system retention is at least 3 months, and EDP is the long-term archive.

- [ ] **Step 2: Clarify the EDP boundary without removing the direct-access prohibition**

  Update the EDP and cross-system wording so local micro-system processing is allowed, but cross-system propagation still uses registered API/event/message contracts and never direct database reads or writes.

- [ ] **Step 3: Add Go/No-Go checks for retention and propagation**

  Add No-Go conditions for a micro-system page that cannot complete its own domain workflow, retention below 7 days or 3 months, cleanup before receipt/integrity confirmation, missing retry/idempotency, or untraceable propagation.

- [ ] **Step 4: Verify the guardrail text**

  Run: `rg -n "7 天|3 个月|长期|幂等|重试|清理|微系统|中心系统" architecture/FAC_GUARDRAILS_V1.md`

  Expected: all approved constraints appear in the controlled guardrail document and the existing `Direct ERP Access = 0` rule remains present.

- [ ] **Step 5: Commit**

  ```bash
  git add architecture/FAC_GUARDRAILS_V1.md
  git commit -m "docs: add layered processing retention guardrails"
  ```

### Task 2: Update the overall architecture and data-flow standard

**Files:**
- Modify: `docs/FAC_完整总体方案与分阶段实施计划_V2.1.md`
- Reference: `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

**Interfaces:**
- Consumes: Task 1 guardrail terminology and the approved layer responsibilities.
- Produces: a consistent overall architecture section, data-flow description, query routing rule, and retention table.

- [ ] **Step 1: Add the layered responsibility subsection**

  Extend the system-boundary section with a table for micro-system, center-system, and EDP responsibilities, including the exact retention floors of 7 days, 3 months, and long-term.

- [ ] **Step 2: Update the data-flow principle**

  Replace the implication that every local business action must wait for centralized processing with the approved flow: micro-system local business action first, reliable propagation to center system and EDP, and EDP remains the standardized long-term cross-system data and audit base.

- [ ] **Step 3: Define query routing and purge prerequisites**

  State that recent operational queries use micro-system data, three-month operational queries use center-system data, historical/audit queries use EDP, and local cleanup requires target-layer receipt plus integrity confirmation.

- [ ] **Step 4: Verify architecture consistency**

  Run: `rg -n "微系统|中心系统|7 天|3 个月|长期|清理|幂等|重试|查询" docs/FAC_完整总体方案与分阶段实施计划_V2.1.md`

  Expected: the new layer rules are present and no nearby section still claims that micro-systems are query-only or that they cannot process local business.

- [ ] **Step 5: Commit**

  ```bash
  git add docs/FAC_完整总体方案与分阶段实施计划_V2.1.md
  git commit -m "docs: define layered FAC data architecture"
  ```

### Task 3: Update the Phase 1 implementation baseline

**Files:**
- Modify: `docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md`
- Modify: `docs/mvp/README.md`
- Reference: `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

**Interfaces:**
- Consumes: Task 1 guardrails and Task 2 architecture vocabulary.
- Produces: Phase 1 development gates and MVP work order that explicitly validate micro-system business completeness and layered retention.

- [ ] **Step 1: Add layered processing to Phase 1 goals and boundaries**

  Update the Phase 1 goal list and relevant data-flow diagrams to require that each participating micro-system can complete its own domain workflow while FAC/EDP contracts continue to govern cross-system data.

- [ ] **Step 2: Add retention and reliable-sync work to the execution gates**

  Add a gate or work item covering 7-day micro-system retention, 3-month center-system retention, EDP long-term archive, retry/idempotency/traceability, and cleanup only after upper-layer confirmation.

- [ ] **Step 3: Extend Go/No-Go criteria**

  Add the layered retention floors, query routing, and cleanup safety to the Phase 1 Go criteria; add missing workflow capability, data-loss risk, unverified purge, and non-idempotent replay to No-Go.

- [ ] **Step 4: Refresh the MVP controlled-document index and redline summary**

  Update `docs/mvp/README.md` so the controlled summary reflects that EDP remains the long-term governance layer while micro-systems are allowed and required to process their own business domain locally.

- [ ] **Step 5: Verify Phase 1 references**

  Run: `rg -n "微系统|中心系统|7 天|3 个月|长期|重试|幂等|清理|No-Go|NO-GO" docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md docs/mvp/README.md`

  Expected: the implementation baseline, the Go/No-Go section, and the MVP summary use the same retention and processing rules.

- [ ] **Step 6: Commit**

  ```bash
  git add docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md docs/mvp/README.md
  git commit -m "docs: align MVP plan with layered retention"
  ```

### Task 4: Extend the MVP acceptance matrix

**Files:**
- Modify: `docs/mvp/FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md`
- Reference: `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

**Interfaces:**
- Consumes: the retention and synchronization rules from Tasks 1–3.
- Produces: named acceptance cases and Go thresholds for workflow completeness, retention, routing, replay, and purge safety.

- [ ] **Step 1: Add layered-processing contract cases**

  Add acceptance cases for: complete micro-system workflow; micro-system retention of at least 7 days; center-system retention of at least 3 months; EDP long-term retrieval with source/version/audit metadata; query routing by age; and no direct database cross-access.

- [ ] **Step 2: Add failure and replay cases**

  Add cases for upper-layer outage with local retry state, duplicate delivery/replay without duplicate business results, and cleanup blocked until receipt and integrity confirmation.

- [ ] **Step 3: Add UAT samples and Go thresholds**

  Extend the UAT sample set with one complete micro-system workflow, one sync outage/retry, one duplicate event, one seven-day boundary query, one three-month boundary query, and one historical EDP query. Add 100% pass thresholds for the new mandatory cases and zero data-loss/duplicate-result/premature-purge defects.

- [ ] **Step 4: Verify the acceptance matrix**

  Run: `rg -n "微系统|中心系统|7 天|3 个月|长期|重试|重复|清理|数据丢失|Go 阈值" docs/mvp/FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md`

  Expected: every requirement in the approved spec maps to a named test or Go/No-Go threshold.

- [ ] **Step 5: Commit**

  ```bash
  git add docs/mvp/FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md
  git commit -m "test: add layered retention acceptance cases"
  ```

### Task 5: Run final controlled-document consistency checks

**Files:**
- Verify: `architecture/FAC_GUARDRAILS_V1.md`
- Verify: `docs/FAC_完整总体方案与分阶段实施计划_V2.1.md`
- Verify: `docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md`
- Verify: `docs/mvp/README.md`
- Verify: `docs/mvp/FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md`
- Verify: `docs/superpowers/specs/2026-11-09-fac-layered-processing-retention-design.md`

**Interfaces:**
- Consumes: all updated controlled documents.
- Produces: evidence that terminology, thresholds, query routing, and safety rules are consistent across the document set.

- [ ] **Step 1: Check required values and terms globally**

  Run: `rg -n "微系统|中心系统|7 天|3 个月|长期|幂等|重试|清理|EDP" architecture docs`

  Expected: the approved terms occur in the design, architecture, implementation baseline, and acceptance matrix without contradictory retention values.

- [ ] **Step 2: Check Markdown and whitespace cleanliness**

  Run: `git diff --check`

  Expected: no whitespace errors.

- [ ] **Step 3: Review the final diff against the approved spec**

  Confirm that the final diff changes only controlled documentation, preserves the historical action plan, does not alter runtime code, and covers all goals, non-goals, synchronization rules, and acceptance criteria in the spec.

- [ ] **Step 4: Commit the consistency review**

  ```bash
  git add architecture/FAC_GUARDRAILS_V1.md docs/FAC_完整总体方案与分阶段实施计划_V2.1.md docs/FAC_第一阶段_MVP_开发执行方案_V1.1.md docs/mvp/README.md docs/mvp/FAC_MVP_TEST_ACCEPTANCE_MATRIX_V1.md
  git commit -m "docs: finalize layered processing standard"
  ```
