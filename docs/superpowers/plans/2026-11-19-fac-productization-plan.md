# FAC 正式产品化迭代实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 FAC-OFA、EDP-first 和 M09 工作台基础上，把 `/fac` 及其后端升级为可持续迭代的正式 FAC Phase 1 产品，同时保留 `/demo/fac` 作为开发测试入口。

**Architecture:** 新增正式 `fac` API、契约和服务层，复用现有 EDP Port、OFA Engine、CalculationRun/Snapshot/Result/Evidence 和幂等事件能力。正式系统将规则、期间、外部请求状态和正式配置纳入持久化模型；M02/M01/M10/M13/EBMS 通过 Adapter/Contract 预留，未接入时只产生可审计的待外部处理状态。

**Tech Stack:** Python 3.11, FastAPI, Pydantic, SQLAlchemy 2, Alembic, SQLite（本地/首期云端持久化）和现有原生 HTML/CSS/JavaScript。

**Spec:** `docs/superpowers/specs/2026-11-19-fac-productization-design.md`

## Global Constraints

- 正式入口必须保持 `/fac` 和 `http://150.158.13.110:18000/fac`。
- `/demo/fac` 与 `/api/v1/demo/*` 只能用于开发测试和兼容回归，不作为正式页面数据源。
- 外部及跨域事实必须经过 EDP Object/Event/Evidence；FAC 不得直连 ERP、CRM、SPC、HR、MES、银行或其他业务数据库。
- 正式 Result 必须保留原币/功能币、规则版本、计算快照、来源对象和 Evidence 引用。
- 价格、汇率、证据缺失不得静默通过；历史 Result 不得 UPDATE 覆盖；Replay/Retry 不得生成重复财经事实。
- M13/M01/M10/EBMS 未接入时，不得把沙箱投影显示为生产执行完成。
- 所有用户可见文案使用中文；AEOS/FAC/EDP/OFA 等技术标识保留。
- 发布必须具备数据库迁移、灰度验证、同端口切换和旧版本回滚路径。

## Review Focus

- 旧 Demo 数据库误进入正式数据：在迁移/启动测试中验证正式库不自动导入演示订单。
- `/api/v1/fac/*` 与 `/api/v1/demo/*` 数据源混用：正式页面测试必须只调用正式 API。
- 缺失价格、汇率、Evidence：验证结果为 `CALCULATION_INCOMPLETE` 或不可验证，而不是伪造金额。
- 结果版本被覆盖：验证每次输入/规则变化都生成新的 CalculationRun、Snapshot 和 Result。
- 外部系统不可用时误报完成：验证 M13/M01/M10/EBMS 只产生 `WAITING_EXTERNAL`/待接入状态和审计记录。

---

### Task 1: 正式配置、运行边界与产品入口

**Files:**
- Modify: `src/fac/settings.py`
- Modify: `src/fac/main.py`
- Create: `src/fac/api/routes/fac.py`
- Modify: `src/fac/api/routes/demo.py`
- Modify: `tests/api/test_demo.py`
- Create: `tests/api/test_fac_api.py`

**Interfaces:**
- Produces `FAC_DATABASE_URL`, `FAC_DEMO_ENABLED`, `FAC_ENVIRONMENT` 的正式配置语义。
- Produces always-on `GET /fac` and `/api/v1/fac/*` router。
- Keeps existing `/demo/fac` and `/api/v1/demo/*` behind `FAC_DEMO_ENABLED`。

- [ ] **Step 1: Write failing tests** for `/fac` being available when demo is disabled, `/demo/fac` being hidden, and formal API returning a structured empty/ready state without invoking Demo routes.
- [ ] **Step 2: Run** `python -m pytest tests/api/test_fac_api.py tests/api/test_demo.py -q` and verify the new formal-route assertions fail.
- [ ] **Step 3: Implement** settings aliases/defaults, include a formal router unconditionally in `create_app`, and move formal route handlers out of the Demo router without duplicating business logic.
- [ ] **Step 4: Run** the focused tests and verify formal routes pass while Demo route gating remains intact.
- [ ] **Step 5: Commit** `feat: establish formal fac api boundary`.

### Task 2: 正式财经契约、规则与期间模型

**Files:**
- Create: `src/fac/contracts/fac.py`
- Modify: `src/fac/infrastructure/models.py`
- Modify: `src/fac/infrastructure/repositories.py`
- Create: `alembic/versions/0004_fac_product_baseline.py`
- Create: `tests/contracts/test_fac_contracts.py`
- Create: `tests/infrastructure/test_fac_persistence.py`

**Interfaces:**
- `FacOverviewResponse`, `FacOrderSummary`, `FacCalculationRequest`, `FacResultResponse`, `FacEvidenceResponse`, `FinanceRuleResponse`, `FinancePeriodResponse`, `ExternalRequestResponse`。
- `FinanceRule`: tenant, rule id/version, status, effective dates, formula metadata and evidence requirement。
- `FinancePeriod`: tenant, period id, currency, status (`OPEN`, `CALCULATED`, `REVIEWED`, `VERIFIED`, `CLOSED`, `REOPENED`, `RESTATED`)。
- `ExternalRequest`: correlation id, target system, request type, idempotency key, status, payload, retry/audit fields。

- [ ] **Step 1: Write failing contract tests** for required identifiers, status enums, money/result version fields, and rejection of missing evidence/FX metadata.
- [ ] **Step 2: Run** `python -m pytest tests/contracts/test_fac_contracts.py -q` and verify failure.
- [ ] **Step 3: Implement** Pydantic contracts and SQLAlchemy models using existing revision/tenant conventions; add the Alembic migration without altering existing migration files.
- [ ] **Step 4: Add persistence tests** for tenant scope, rule version uniqueness, period state values, external-request idempotency and historical immutability.
- [ ] **Step 5: Run** `python -m pytest tests/contracts/test_fac_contracts.py tests/infrastructure/test_fac_persistence.py -q` and `python -m alembic check`.
- [ ] **Step 6: Commit** `feat: add formal fac finance contracts and period model`.

### Task 3: 从 Demo 服务抽取正式 FAC 服务

**Files:**
- Create: `src/fac/modules/fac/service.py`
- Modify: `src/fac/modules/demo/service.py`
- Modify: `src/fac/modules/calculation/service.py`
- Modify: `src/fac/modules/ofa/ports.py`
- Modify: `src/fac/modules/ofa/engine.py`
- Create: `tests/modules/test_fac_service.py`
- Modify: `tests/modules/test_calculation_versioning.py`

**Interfaces:**
- `FacService.overview(session, tenant_id) -> FacOverviewResponse`
- `FacService.list_orders(session, tenant_id, filters) -> tuple[FacOrderSummary, ...]`
- `FacService.calculate_order(request: FacCalculationRequest) -> FacResultResponse`
- `FacService.result_evidence(result_id, tenant_id) -> FacEvidenceResponse`
- `FacService.replay(request) -> FacResultResponse`
- `DemoService` becomes a compatibility facade that calls the formal service with test-only tenant/configuration.

- [ ] **Step 1: Add failing tests** for formal calculation using EDP-backed refs, new result version on price/rule revision, replay returning the existing result id, and no mutation of previous results.
- [ ] **Step 2: Run** focused module tests and verify they fail because the formal service does not exist.
- [ ] **Step 3: Extract** shared orchestration from `DemoService` into `FacService`; keep the OFA engine as the calculation owner and keep EDP repository access behind ports.
- [ ] **Step 4: Add missing-price, missing-FX and incomplete-evidence paths with explicit statuses and error contracts.
- [ ] **Step 5: Make the existing Demo service delegate to `FacService` and preserve all existing Demo tests.
- [ ] **Step 6: Run** `python -m pytest tests/modules tests/regression -q` and verify both formal and compatibility paths pass.
- [ ] **Step 7: Commit** `refactor: promote demo orchestration to formal fac service`.

### Task 4: 正式 `/api/v1/fac` API

**Files:**
- Modify: `src/fac/api/routes/fac.py`
- Modify: `src/fac/main.py`
- Create: `tests/api/test_fac_api.py` (extend Task 1 file)

**Interfaces:**
- `GET /api/v1/fac/overview`
- `GET /api/v1/fac/orders`
- `GET /api/v1/fac/orders/{order_id}/financial-result`
- `POST /api/v1/fac/orders/{order_id}/calculations`
- `GET /api/v1/fac/calculations/{calculation_id}`
- `GET /api/v1/fac/results/{result_id}/evidence`
- `GET /api/v1/fac/rules`
- `GET /api/v1/fac/periods`
- `GET /api/v1/fac/events`
- `GET /api/v1/fac/external-requests`

- [ ] **Step 1: Write failing API contract tests** for status codes, tenant scoping, pagination/filter parameters, validation errors, incomplete calculations, and `WAITING_EXTERNAL` responses.
- [ ] **Step 2: Run** `python -m pytest tests/api/test_fac_api.py -q` and verify failure.
- [ ] **Step 3: Implement** route handlers with Pydantic request/response models and shared `get_session`; formal routes must never call `/api/v1/demo/*` handlers.
- [ ] **Step 4: Add same-origin protection to state-changing browser calls and deterministic error payloads for missing source refs, missing evidence and replay conflicts.
- [ ] **Step 5: Run** focused API tests and OpenAPI schema inspection; verify all listed paths exist.
- [ ] **Step 6: Commit** `feat: expose formal fac finance api`.

### Task 5: 将 `/fac` 工作台改为正式产品界面

**Files:**
- Modify: `src/fac/api/fac_page.py`
- Modify: `src/fac/api/demo_page.py` only for explicit test labeling
- Create: `tests/api/test_fac_page_copy.py`
- Modify: `tests/api/test_demo.py`

**Interfaces:**
- Page JavaScript consumes only `/api/v1/fac/*` for formal panes.
- Formal panes: 总览、订单财经分析、规则与期间、财经结果、事件与同步、决策/动作、证据与验证。

- [ ] **Step 1: Write failing page tests** asserting no formal-page copy contains “Demo/演示/本地沙箱/租户：demo-tenant/运行联调演示”, and asserting formal business labels and API hooks exist.
- [ ] **Step 2: Run** `python -m pytest tests/api/test_fac_page_copy.py -q` and verify failure against the current page.
- [ ] **Step 3: Replace** Demo labels/actions with formal business actions: 计算订单、生成财经结果、查看证据、提交复核、查看待外部处理；keep technical AEOS/M09/EDP/OFA identifiers.
- [ ] **Step 4: Bind overview, order list, result/evidence and external-request panes to formal endpoints; show explicit `待接入`/`待外部处理` states for unavailable adapters.
- [ ] **Step 5: Run** browser verification with Playwright: open `/fac`, calculate one order, inspect result/evidence, refresh, and verify no false completion appears.
- [ ] **Step 6: Commit** `feat: convert fac workbench from demo to product ui`.

### Task 6: 正式数据库启动、测试夹具与兼容迁移

**Files:**
- Modify: `alembic.ini`
- Modify: `Dockerfile`
- Modify: `README.md`
- Modify: `scripts/run_fac_demo.ps1`
- Create: `scripts/run_fac.ps1`
- Create: `tests/infrastructure/test_formal_migration.py`

**Interfaces:**
- Formal runtime uses `FAC_DATABASE_URL` and does not seed fixed Demo data on startup.
- Development command `scripts/run_fac.ps1` explicitly applies migrations and imports the Phase 1 fixture.
- Demo command remains isolated and documented as test-only.

- [ ] **Step 1: Write failing migration tests** for an empty formal database, repeatable `alembic upgrade head`, and no automatic insertion of `ORD-1001`.
- [ ] **Step 2: Run** migration tests and verify current startup behavior fails the formal expectations.
- [ ] **Step 3: Update** Docker/runtime defaults to `/app/data/fac.db`, add a persistent data directory, remove automatic Demo reset, and keep demo fixture loading explicit.
- [ ] **Step 4: Add formal local run script and document environment variables, fixture import, backup, restore and rollback.
- [ ] **Step 5: Run** `python -m pytest tests/infrastructure/test_formal_migration.py -q` and a clean-container smoke test.
- [ ] **Step 6: Commit** `chore: make fac runtime migration and data lifecycle explicit`.

### Task 7: 全量验证、腾讯云同地址发布与回滚证据

**Files:**
- Modify: `Dockerfile`
- Create: `docs/FAC_正式产品化发布记录.md`
- Create: `tests/regression/test_formal_product_boundary.py`

- [ ] **Step 1: Add regression tests** covering EDP-first imports, tenant isolation, no direct-source dependency, immutable result history, missing price/FX behavior, replay idempotency and unavailable external adapters.
- [ ] **Step 2: Run** `python -m pytest -q`, `ruff check src tests`, and `python -m compileall src tests`; resolve all failures.
- [ ] **Step 3: Build** a versioned image from the repository Dockerfile, run Alembic upgrade in an isolated container, and verify `/health`, `/fac`, formal API OpenAPI paths and one complete Phase 1 calculation.
- [ ] **Step 4: Upload and run** the new image on a temporary cloud port with persistent data path; verify migration, database persistence across restart, formal page copy and rollback container.
- [ ] **Step 5: Switch** the existing `18000` service only after smoke checks; keep the previous container/image and record exact rollback commands.
- [ ] **Step 6: Verify externally** `http://150.158.13.110:18000/health`, `/fac`, `/api/v1/fac/overview` and the formal calculation/evidence path.
- [ ] **Step 7: Commit** `release: deploy formal fac phase one baseline`.

## Definition of Done

- `/fac` remains the same public entry and is a formal FAC workbench rather than a Demo page.
- A fresh formal database can migrate, import EDP fixture explicitly, calculate an order and query a versioned Finance Result with Evidence.
- Demo routes remain isolated and do not power the formal page.
- Tests and static checks pass; the public deployment has a persistent data path, a recorded rollback target and externally verified formal API/page behavior.
