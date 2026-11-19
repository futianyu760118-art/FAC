# FAC Finance Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 FAC OFA 与 Calculation 代码之上交付一个可浏览器操作、可验证版本化和幂等重放的财经计算 Demo。

**Architecture:** 新增受 `FAC_DEMO_ENABLED` 控制的 Demo 路由和 `DemoService`。Demo Service 只负责固定演示数据、演示事件和流程编排，所有成本计算复用现有 `CalculationService`、`OFAEngine`、EDP repository 和结果契约；浏览器页面调用 `/api/v1/demo` API 展示真实返回值。

**Tech Stack:** Python 3.11、FastAPI、Pydantic、SQLAlchemy、SQLite、原生 HTML/CSS/JavaScript、pytest、Ruff。

**Spec:** `docs/superpowers/specs/2026-11-19-fac-demo-design.md`

## Global Constraints

- Demo tenant 固定为 `demo-tenant`，Demo source system 固定为 `demo-edp`。
- 初始计划成本必须为 `46.00 CNY`，价格修正后的 V2 必须为 `52.00 CNY`。
- V1 结果不得被 UPDATE 覆盖，V2 必须通过新的 CalculationRun、Snapshot 和 Result 版本生成。
- 重放相同事件不得新增事件、CalculationRun 或 CalculationResult。
- Demo 不连接真实 M02、M04、M13、EDP 或 ERP。
- 生产环境默认关闭 Demo 路由。
- 现有用户改动和无关 CAD 文件不得被删除、重置或覆盖。

## Review Focus

- Demo reset 只能作用于 `demo-tenant`，不能删除其他租户数据；由 API 隔离测试覆盖。
- 旧 V1 结果必须可在 V2 产生后读取且金额不变；由版本回归测试覆盖。
- 事件已写入但计算失败时不能生成伪造总成本；由缺失价格阻断测试覆盖。
- Replay 使用相同 event_id/idempotency_key 时不能重复落库；由重放测试覆盖。
- Demo 路由关闭时不能暴露页面或 API；由设置门禁测试覆盖。

---

### Task 1: Demo contracts and feature gate

**Files:**
- Create: `src/fac/contracts/demo.py`
- Modify: `src/fac/settings.py`
- Modify: `src/fac/main.py`
- Test: `tests/api/test_demo.py`

**Interfaces:**
- Produces `DemoTriggerRequest`, `DemoTriggerResponse`, `DemoStateResponse` and `DemoResetResponse` Pydantic contracts.
- Adds `Settings.demo_enabled: bool = False` from `FAC_DEMO_ENABLED`.
- `create_app()` includes the Demo router only when `demo_enabled` is true.

- [ ] **Step 1: Write failing tests**

  Add tests that `FAC_DEMO_ENABLED=false` hides `/demo/fac`, while enabled mode exposes it; validate the trigger request and response field names.

- [ ] **Step 2: Run the focused tests and verify the expected failure**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: failure because the Demo contracts, setting, and route do not yet exist.

- [ ] **Step 3: Implement contracts and the feature gate**

  Define strict request/response models with `price_revision >= 1`, non-empty event/audit fields, and include the existing `CalculationResponse` and `PlanCostResponse` fields needed by the UI.

- [ ] **Step 4: Run the focused tests and verify they pass**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: PASS for gate and contract tests.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/contracts/demo.py src/fac/settings.py src/fac/main.py tests/api/test_demo.py
  git commit -m "feat: add FAC demo contracts and feature gate"
  ```

### Task 2: Demo seed and calculation orchestration

**Files:**
- Create: `src/fac/modules/demo/__init__.py`
- Create: `src/fac/modules/demo/service.py`
- Modify: `src/fac/infrastructure/models.py` only if a query needs an existing model export
- Test: `tests/modules/test_demo_service.py`

**Interfaces:**
- `DemoService(session: Session)` owns the `demo-tenant` scenario.
- `DemoService.reset() -> DemoResetResponse` clears only the Demo tenant and seeds Order, BOM, MaterialPrice V1/V2, Labor, and Expense projections.
- `DemoService.trigger(request: DemoTriggerRequest) -> DemoTriggerResponse` records `QuoteRecalculationRequired`, starts a calculation version, calls OFA, and returns replay status plus result.
- `DemoService.state() -> DemoStateResponse` returns Demo events, input refs, runs, snapshots, and results.

- [ ] **Step 1: Write failing service tests**

  Add tests for reset isolation, initial calculation total `46.00`, price revision 2 total `52.00`, V1 preservation, `previous_result_id`, and replay returning the existing V2 without duplicate rows.

- [ ] **Step 2: Run service tests to verify the expected failure**

  Run: `python -m pytest tests/modules/test_demo_service.py -q`

  Expected: failure because `DemoService` is missing.

- [ ] **Step 3: Implement reset and seed behavior**

  Delete only rows where `tenant_id == "demo-tenant"` from the known FAC tables, commit, then insert the fixed EDP projections through `EdpRepository` so the normal EDP boundary is used.

- [ ] **Step 4: Implement trigger orchestration**

  Build the frozen refs for the selected price revision, construct an immutable `EventEnvelope` with `event_type="QuoteRecalculationRequired"`, persist it through `CoreRepository.add_event`, and call `CalculationService.start()` plus `OFAEngine(session).calculate_plan_cost()`.

  If `add_event()` reports an existing event, load the existing calculation/result instead of creating a duplicate. Preserve the event’s trigger type, reason, actor, and idempotency key in the returned audit data.

- [ ] **Step 5: Implement state projection**

  Query only Demo tenant rows and map persisted payloads into the response contract, including short display checksums while retaining the full checksum in API data.

- [ ] **Step 6: Run service tests to verify they pass**

  Run: `python -m pytest tests/modules/test_demo_service.py -q`

  Expected: PASS.

- [ ] **Step 7: Commit**

  ```powershell
  git add src/fac/modules/demo tests/modules/test_demo_service.py
  git commit -m "feat: add FAC demo calculation flow"
  ```

### Task 3: Demo API routes

**Files:**
- Create: `src/fac/api/routes/demo.py`
- Modify: `src/fac/main.py`
- Test: `tests/api/test_demo.py`

**Interfaces:**
- `GET /demo/fac` returns the Demo HTML page.
- `POST /api/v1/demo/reset` calls `DemoService.reset()`.
- `GET /api/v1/demo/state` calls `DemoService.state()`.
- `POST /api/v1/demo/events/quote-recalculation` calls `DemoService.trigger()`.
- `POST /api/v1/demo/replay` reuses the supplied event identity and calls `DemoService.trigger()`.

- [ ] **Step 1: Add failing route tests**

  Use `TestClient` with a temporary SQLite session factory. Assert reset, trigger, state, replay status codes and response fields; assert Demo routes are unavailable when disabled.

- [ ] **Step 2: Run route tests to verify failure**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: failure because the Demo router is not implemented.

- [ ] **Step 3: Implement the routes**

  Use `Annotated[Session, Depends(get_session)]`, return the existing Pydantic contracts, translate missing Demo state into HTTP 404, and keep all business orchestration in `DemoService`.

- [ ] **Step 4: Run route tests to verify they pass**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: PASS.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/api/routes/demo.py src/fac/main.py tests/api/test_demo.py
  git commit -m "feat: expose FAC demo API"
  ```

### Task 4: Browser Demo workbench

**Files:**
- Create: `src/fac/api/demo_page.py`
- Modify: `src/fac/api/routes/demo.py`
- Test: `tests/api/test_demo.py`

**Interfaces:**
- `render_demo_page() -> str` returns the browser page.
- The page calls the four Demo endpoints and renders result cards, version timeline, event status, input refs, checksum, and replay state.

- [ ] **Step 1: Add failing page tests**

  Assert the page contains the FAC Demo title, order `ORD-1001`, buttons for reset/initial calculation/price recalculation/replay, and placeholders for V1/V2 and audit information.

- [ ] **Step 2: Run page tests to verify failure**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: failure because the page renderer is missing.

- [ ] **Step 3: Implement the page**

  Use semantic HTML, inline CSS and native JavaScript so no frontend dependency or build step is introduced. Keep the visual hierarchy compact: workflow rail, result summary, version timeline, and audit details. Render all money values from API responses rather than hardcoding displayed results.

- [ ] **Step 4: Run page tests to verify they pass**

  Run: `python -m pytest tests/api/test_demo.py -q`

  Expected: PASS.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/api/demo_page.py src/fac/api/routes/demo.py tests/api/test_demo.py
  git commit -m "feat: add FAC browser demo workbench"
  ```

### Task 5: Demo runner, documentation, and full verification

**Files:**
- Create: `scripts/run_fac_demo.ps1`
- Modify: `README.md`
- Modify: `.env.example`
- Test: `tests/test_health.py` only if app startup behavior changes

**Interfaces:**
- The runner sets a demo SQLite URL, enables Demo, upgrades Alembic to head, and starts Uvicorn.
- README documents the exact local startup command and `/demo/fac` URL without claiming production readiness.

- [ ] **Step 1: Add the runner and documentation**

  Keep the Demo database path explicit and local; do not use or overwrite the default `fac.db`.

- [ ] **Step 2: Run the full verification suite**

  Run:

  ```powershell
  python -m pytest -q
  python -m ruff check src tests
  python -m compileall -q src tests
  git diff --check
  ```

  Expected: all tests pass, Ruff passes for FAC source/tests, compilation succeeds, and no whitespace errors appear.

- [ ] **Step 3: Start the Demo and verify the browser flow**

  Run `.\scripts\run_fac_demo.ps1`, open `http://127.0.0.1:8000/demo/fac`, then execute reset → initial calculation → price recalculation → replay. Confirm V1=46.00, V2=52.00, V1 remains queryable, and replay reports no duplicate.

- [ ] **Step 4: Review the final diff**

  Confirm the diff contains only Demo files plus the intended README/env documentation; preserve pre-existing OFA/Calculation and CAD changes.

- [ ] **Step 5: Commit**

  ```powershell
  git add scripts/run_fac_demo.ps1 README.md .env.example
  git commit -m "docs: add FAC demo runner and usage"
  ```
