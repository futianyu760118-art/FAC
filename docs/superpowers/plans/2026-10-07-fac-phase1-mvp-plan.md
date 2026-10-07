# FAC Phase 1 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 `D:\FAC` 搭建一个可本地运行、可审计、可测试的 FAC Phase 1 模块化单体，先完成 MVP-1A OFA，再完成 MVP-1B Order-to-Cash。

**Architecture:** 使用 FastAPI + SQLAlchemy/Alembic 的模块化单体。FAC 只通过 EDP Mock/Import Adapter 消费带 revision 的对象；Money、CalculationRun、Evidence、Event 和 Verify 作为横切域服务，OFA、AR、Bank 和 Finance 作为独立业务模块。

**Tech Stack:** Python 3.11、FastAPI、Pydantic v2、SQLAlchemy 2.x、Alembic、SQLite（默认）/PostgreSQL、pytest、httpx、Ruff、Docker Compose。

**Spec:** `docs/superpowers/specs/2026-10-07-fac-phase1-mvp-design.md`

## Global Constraints

- 所有跨系统数据必须先进入 EDP；FAC 不得直接访问 ERP、SPC、CRM、HR、Bank 或其他业务数据库。
- 所有正式金额使用 Decimal，并同时保存原币、功能币、汇率、汇率日期、汇率类型和来源/版本。
- Missing Price 必须产生 `MaterialPriceMissing` 和 `CALCULATION_INCOMPLETE`，不得回退为 0。
- Missing FX 必须产生 `FXRateMissing` 和 `CALCULATION_INCOMPLETE`，不得回退为 1 或未记录来源的最近汇率。
- 历史 Result 不得被 UPDATE 覆盖；输入或规则变化必须创建新的 CalculationRun、Snapshot 和 Result version。
- 缺少 Evidence 的正式 Result 不得进入 `VERIFIED`。
- 高风险 Verify 必须由具备权限的人类完成；Agent 不拥有正式财经事实。
- 所有写入型事件必须幂等、可审计且 replay 不产生重复 Result。
- 生产 Secret 只来自环境变量/Secret Manager，不进入源码、fixture 或提交记录。

## Review Focus

- 不同币种和 JPY 零小数精度：每个金额的原币/功能币/汇率元数据必须保持一致。
- 缺失价格或汇率：计算必须阻断并留下异常事件，而不是产生看似完整的毛利。
- BOM 重复节点、自制件、委外件和单位换算：成本 rollup 不得重复计算或丢失节点。
- 同一请求 replay 或价格/BOM/FX 修正：必须复用既有幂等结果或创建新版本，不能重复或覆盖。
- 非 EXACT 银行匹配、跨币种付款和人工 FX：必须转入人工确认并阻止自动 Verify/核销。

---

### Task 1: Bootstrap the runnable service

**Files:**
- Create: `pyproject.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `src/fac/__init__.py`
- Create: `src/fac/main.py`
- Create: `src/fac/settings.py`
- Create: `src/fac/api/routes/health.py`
- Create: `tests/test_health.py`
- Create: `README.md`

**Interfaces:**
- Produces `fac.main:create_app() -> FastAPI` and `GET /health -> {"status": "ok", "service": "fac"}`.
- Configuration reads `FAC_DATABASE_URL`, `FAC_FUNCTIONAL_CURRENCY`, and `FAC_ENVIRONMENT`; defaults to SQLite, `CNY`, and `development`.

- [ ] **Step 1: Write the failing health test**

  Add `tests/test_health.py` using `httpx.AsyncClient` or `TestClient`; assert `/health` returns HTTP 200 and the exact service/status fields.

- [ ] **Step 2: Run the test to verify it fails**

  Run: `python -m pytest tests/test_health.py -q`

  Expected: FAIL because the package and route do not exist.

- [ ] **Step 3: Add the minimal application and packaging**

  Define the dependencies and pytest configuration in `pyproject.toml`, implement `create_app`, settings, and the health route. Keep application construction import-safe so tests do not require external services.

- [ ] **Step 4: Run the focused and full baseline tests**

  Run: `python -m pytest tests/test_health.py -q` then `python -m pytest -q`.

  Expected: the health test passes and no other tests fail.

- [ ] **Step 5: Commit**

  ```powershell
  git add pyproject.toml .env.example .gitignore src tests README.md
  git commit -m "feat: bootstrap FAC service"
  ```

### Task 2: Implement Money, FX, evidence, event, and error contracts

**Files:**
- Create: `src/fac/contracts/common.py`
- Create: `src/fac/contracts/events.py`
- Create: `src/fac/domain/money.py`
- Create: `src/fac/domain/errors.py`
- Create: `src/fac/domain/evidence.py`
- Create: `src/fac/domain/events.py`
- Create: `tests/domain/test_money.py`
- Create: `tests/domain/test_events.py`
- Create: `tests/domain/test_evidence.py`

**Interfaces:**
- `Money.from_original(amount: Decimal, currency: str, functional_currency: str, fx: FXRate | None) -> Money`.
- `FXRate(base_currency: str, quote_currency: str, rate: Decimal, rate_type: str, effective_at: date, source: str, revision: int, evidence_ref: str)`.
- `Money.to_functional() -> Decimal` raises `FXRateMissing` for non-functional currency without a rate.
- `EventEnvelope` validates the required Event Catalog V1 fields and exposes a deterministic `idempotency_key`.
- `EvidenceRef` carries `evidence_id`, `kind`, `source_ref`, `checksum`, and `created_at`.

- [ ] **Step 1: Write failing money and contract tests**

  Cover CNY→CNY at rate 1, USD→CNY Decimal conversion, JPY zero-decimal quantization, missing FX rejection, invalid currency codes, event required fields, and evidence checksum fields.

- [ ] **Step 2: Run focused tests to verify the expected failures**

  Run: `python -m pytest tests/domain/test_money.py tests/domain/test_events.py tests/domain/test_evidence.py -q`

  Expected: FAIL because the domain types are absent.

- [ ] **Step 3: Implement the smallest contract/domain types**

  Use `Decimal` with explicit quantization from a currency metadata map, preserve both currency representations, and map domain failures to stable error codes (`FX_RATE_MISSING`, `INVALID_MONEY`, `EVIDENCE_REQUIRED`). Do not add fallback rates.

- [ ] **Step 4: Run focused tests and the full suite**

  Run the focused command, then `python -m pytest -q`.

  Expected: all tests pass with no warnings caused by float conversion.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/contracts src/fac/domain tests/domain
  git commit -m "feat: add FAC money and event contracts"
  ```

### Task 3: Add persistence, migrations, and EDP fixture/import boundary

**Files:**
- Create: `src/fac/infrastructure/db.py`
- Create: `src/fac/infrastructure/models.py`
- Create: `src/fac/infrastructure/repositories.py`
- Create: `src/fac/adapters/edp_mock/models.py`
- Create: `src/fac/adapters/edp_mock/adapter.py`
- Create: `src/fac/api/routes/imports.py`
- Create: `alembic.ini`
- Create: `alembic/env.py`
- Create: `alembic/versions/0001_fac_core.py`
- Create: `fixtures/edp/sample_phase1.json`
- Create: `tests/contracts/test_edp_import.py`
- Create: `tests/infrastructure/test_repositories.py`

**Interfaces:**
- `EdpAdapter.import_fixture(payload: EdpFixture) -> ImportReport`.
- `EdpObjectRef(object_type, object_id, source_system, revision)` is the only cross-system reference form.
- Repositories persist and retrieve `CalculationRun`, `CalculationSnapshot`, `Evidence`, `EventRecord`, and EDP source projections by tenant and revision.
- `POST /api/v1/import/edp-fixture` accepts the fixture contract and returns counts plus rejected object reasons.

- [ ] **Step 1: Write failing contract tests**

  Assert a valid fixture imports Order/BOM/Price/Labor/Expense/FX with source and revision; malformed objects are rejected; a second import of the same revision is idempotent; a different tenant cannot read the imported object.

- [ ] **Step 2: Run the tests to verify failure**

  Run: `python -m pytest tests/contracts/test_edp_import.py tests/infrastructure/test_repositories.py -q`

  Expected: FAIL because persistence and adapter interfaces are absent.

- [ ] **Step 3: Implement database and adapter boundary**

  Define SQLAlchemy models with tenant/revision uniqueness constraints, create the initial Alembic migration, implement the fixture adapter and repository methods, and keep imported EDP data behind adapter/repository interfaces. The route must never receive or execute a source-system database connection.

- [ ] **Step 4: Run contract, migration, and full tests**

  Run: `alembic upgrade head`; `python -m pytest tests/contracts tests/infrastructure -q`; then `python -m pytest -q`.

  Expected: migration succeeds and all tests pass.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/infrastructure src/fac/adapters src/fac/api/routes/imports.py alembic.ini alembic fixtures tests/contracts tests/infrastructure
  git commit -m "feat: add EDP import boundary and persistence"
  ```

### Task 4: Build versioned CalculationRun/Snapshot and OFA plan-cost engine

**Files:**
- Create: `src/fac/modules/calculation/service.py`
- Create: `src/fac/modules/ofa/models.py`
- Create: `src/fac/modules/ofa/ports.py`
- Create: `src/fac/modules/ofa/engine.py`
- Create: `src/fac/modules/ofa/rules.py`
- Create: `src/fac/contracts/ofa.py`
- Create: `tests/modules/test_calculation_versioning.py`
- Create: `tests/modules/test_ofa_engine.py`
- Create: `tests/regression/test_ofa_matrix.py`

**Interfaces:**
- `CalculationService.start(subject_type: str, subject_id: str, input_refs: list[EdpObjectRef], rule_set_version: str, trigger_type: str, reason: str, actor: str) -> CalculationContext`.
- `OFAEngine.calculate_plan_cost(order: OrderInput, ports: OFAPorts, context: CalculationContext) -> PlanCostResult`.
- `PlanCostResult` exposes component Money values, total cost, `calculation_id`, `snapshot_id`, `rule_set_version`, `status`, and evidence refs.
- `OFAEngine.calculate_plan_cost` supports simple/multi-level BOM, duplicate nodes, self-made, outsource, UOM conversion, historical price, override/fallback, and incomplete calculation status.

- [ ] **Step 1: Write failing OFA/version tests**

  Add tests for a simple BOM, multi-level BOM rollup, duplicate-node merge, self-made parent, outsource processing, UOM conversion, missing price, historical price selection, and a same-request replay. Add version tests for BOM/price/FX/rule changes: V1 remains queryable and V2 points to a new CalculationRun/Snapshot.

- [ ] **Step 2: Run the tests to verify the correct failures**

  Run: `python -m pytest tests/modules/test_calculation_versioning.py tests/modules/test_ofa_engine.py tests/regression/test_ofa_matrix.py -q`

  Expected: FAIL because calculation and OFA services are absent.

- [ ] **Step 3: Implement calculation context and minimal OFA engine**

  Freeze all input refs and rule version in a checksumed snapshot; use Decimal-only cost rollup; emit `MaterialPriceMissing` when required prices are absent; return `CALCULATION_INCOMPLETE` without fake totals. Apply Rule Registry version and persist a new Result instead of mutating an older one.

- [ ] **Step 4: Run OFA tests and full suite**

  Run the focused command, then `python -m pytest -q`.

  Expected: all regression and version tests pass.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/modules/calculation src/fac/modules/ofa src/fac/contracts/ofa.py tests/modules tests/regression
  git commit -m "feat: add versioned OFA plan cost engine"
  ```

### Task 5: Add revenue, margin, Evidence, event outbox, and calculation APIs

**Files:**
- Create: `src/fac/modules/revenue/service.py`
- Create: `src/fac/modules/margin/service.py`
- Create: `src/fac/modules/evidence/service.py`
- Create: `src/fac/modules/events/dispatcher.py`
- Create: `src/fac/api/routes/calculations.py`
- Create: `src/fac/api/routes/margins.py`
- Create: `tests/integration/test_ofa_api.py`
- Create: `tests/integration/test_evidence_and_events.py`

**Interfaces:**
- `RevenueService.create_management_revenue_fact(...) -> ManagementRevenueFact` uses shipment-date FX and preserves each shipment snapshot.
- `MarginService.calculate(order_id: str, margin_type: MarginType, revenue: Money, cost: Money, context: CalculationContext) -> MarginResult`.
- `EvidenceService.attach(result_id: str, refs: list[EvidenceRef]) -> None` and `EvidenceService.require_for_verify(result_id: str) -> None`.
- `POST /api/v1/calculations/orders/{order_id}` starts or idempotently returns an OFA calculation.
- `GET /api/v1/calculations/{calculation_id}` and `GET /api/v1/orders/{order_id}/margin` expose versioned results without exposing persistence internals.

- [ ] **Step 1: Write failing integration tests**

  Import the sample EDP fixture, calculate an order, assert ManagementRevenueFact/PlanCostResult/MarginResult are created with Evidence and events, assert missing evidence blocks Verify, and assert replay returns the same calculation/result rather than creating duplicates.

- [ ] **Step 2: Run integration tests to verify failure**

  Run: `python -m pytest tests/integration/test_ofa_api.py tests/integration/test_evidence_and_events.py -q`

  Expected: FAIL because revenue/margin services and routes are absent.

- [ ] **Step 3: Implement services, outbox, and routes**

  Publish `OrderFinanceCalculationRequested`, `PlanCostCalculated`, `MarginCalculated`, `MaterialPriceMissing`, `FXRateMissing`, and `ResultSuperseded` through an outbox record. Require Evidence before `VERIFIED` and keep the API response stable across replay.

- [ ] **Step 4: Run integration and full tests**

  Run the focused command, then `python -m pytest -q`.

  Expected: all tests pass and the sample order can be calculated end to end.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/modules/revenue src/fac/modules/margin src/fac/modules/evidence src/fac/modules/events src/fac/api/routes/calculations.py src/fac/api/routes/margins.py tests/integration
  git commit -m "feat: expose OFA margin and evidence flow"
  ```

### Task 6: Implement AR risk, collection, bank match, and human Verify

**Files:**
- Create: `src/fac/modules/ar/models.py`
- Create: `src/fac/modules/ar/service.py`
- Create: `src/fac/modules/bank/matcher.py`
- Create: `src/fac/modules/finance/verify.py`
- Create: `src/fac/contracts/ar.py`
- Create: `src/fac/api/routes/ar.py`
- Create: `src/fac/api/routes/collections.py`
- Create: `tests/modules/test_ar_risk.py`
- Create: `tests/modules/test_bank_matching.py`
- Create: `tests/integration/test_order_to_cash.py`

**Interfaces:**
- `ARService.create_receivable(revenue_fact: ManagementRevenueFact) -> Receivable`.
- `ARService.assess_risk(ar: Receivable, as_of: date) -> ARRiskResult` with LOW, MEDIUM, HIGH, CRITICAL aging thresholds.
- `BankMatcher.propose(transaction: BankTransaction, candidates: list[Receivable]) -> BankMatchResult` with `EXACT`, `REFERENCE`, `PARTIAL`, `AMBIGUOUS`, `CROSS_CURRENCY` levels.
- `VerifyService.verify_collection(collection_id: str, actor: ActorContext) -> CollectionResult` rejects unauthorized/high-risk automatic verification and requires Evidence/Audit.
- APIs expose AR details, risk, match proposals and human verification without allowing FAC to mutate the original BankTransaction.

- [ ] **Step 1: Write failing AR/bank/Verify tests**

  Cover normal, 1–30, 31–60, and over-60 day risk; partial/full/disputed payments; exact/reference/ambiguous/partial/cross-currency matches; manual FX permission; Agent Verify denial; and Evidence/Audit requirements.

- [ ] **Step 2: Run focused tests to verify failure**

  Run: `python -m pytest tests/modules/test_ar_risk.py tests/modules/test_bank_matching.py tests/integration/test_order_to_cash.py -q`

  Expected: FAIL because the AR, bank, and Verify services are absent.

- [ ] **Step 3: Implement the O2C services**

  Store each payment with its own FX snapshot and functional value; calculate remaining original/functional balances and FX variance separately; require manual confirmation for non-EXACT or cross-currency matches; emit the catalog events from Receivable creation through CollectionResult verification.

- [ ] **Step 4: Run O2C and full tests**

  Run the focused command, then `python -m pytest -q`.

  Expected: all AR, bank, security, and E2E tests pass.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/modules/ar src/fac/modules/bank src/fac/modules/finance src/fac/contracts/ar.py src/fac/api/routes/ar.py src/fac/api/routes/collections.py tests/modules tests/integration
  git commit -m "feat: add order to cash verification flow"
  ```

### Task 7: Produce FinanceResult and operator-facing sample flow

**Files:**
- Create: `src/fac/modules/finance/aggregate.py`
- Create: `src/fac/api/routes/finance.py`
- Create: `src/fac/bootstrap/seed.py`
- Create: `scripts/seed_phase1.py`
- Create: `tests/e2e/test_phase1_flow.py`
- Create: `tests/contracts/test_finance_result.py`
- Modify: `README.md`

**Interfaces:**
- `FinanceAggregator.build(period: str, tenant_id: str) -> FinanceResult` containing management revenue, plan/estimated/final actual cost, margins, AR totals, overdue AR, collected amount, FX impact, risk counts, Verify state, and Evidence refs.
- `GET /api/v1/finance/results?period=YYYY-MM` returns only verified/eligible FinanceResult fields for EBMS consumption.
- `seed_phase1.py` loads at least 5 orders, 3 customers, CNY/USD/EUR data, one overdue AR, one collection, one complex BOM, one missing FX case, and one calculation change.

- [ ] **Step 1: Write failing E2E and FinanceResult contract tests**

  Exercise normal order→margin, low-margin exception, overdue→risk→collection→payment→verify, foreign-currency payment variance, and FinanceResult output; assert an unverified result is excluded from the EBMS response.

- [ ] **Step 2: Run E2E tests to verify failure**

  Run: `python -m pytest tests/e2e/test_phase1_flow.py tests/contracts/test_finance_result.py -q`

  Expected: FAIL because aggregation and seed flow are absent.

- [ ] **Step 3: Implement aggregation and seed data**

  Aggregate only verified/eligible Result versions, preserve FX impact separately from operating margin, and make the seed script idempotent by tenant and dataset version.

- [ ] **Step 4: Run E2E and full tests**

  Run the focused command, then `python -m pytest -q`.

  Expected: the complete local Phase 1 flow passes and FinanceResult is consumable without FAC table access.

- [ ] **Step 5: Commit**

  ```powershell
  git add src/fac/modules/finance src/fac/api/routes/finance.py src/fac/bootstrap scripts tests/e2e tests/contracts/test_finance_result.py README.md
  git commit -m "feat: add verified finance result and phase one seed"
  ```

### Task 8: Add Docker, quality gates, security checks, and delivery documentation

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `Makefile`
- Create: `.github/workflows/ci.yml`
- Create: `tests/security/test_guardrails.py`
- Create: `docs/development.md`
- Create: `docs/acceptance/phase1-runbook.md`
- Modify: `README.md`

**Interfaces:**
- `docker compose up --build` starts the API and optional PostgreSQL profile.
- `make test`, `make lint`, `make migrate`, and `make seed` provide repeatable local commands; equivalent PowerShell commands are documented for Windows.
- CI runs migrations, all tests, Ruff, and a direct-ERP-access/source-secret guard.

- [ ] **Step 1: Write failing guardrail and container smoke tests**

  Assert no source file contains direct ERP/Bank connection code or production-secret patterns, cross-tenant access is rejected, unauthorized Agent Verify is rejected, and the container health endpoint responds.

- [ ] **Step 2: Run the tests to verify failure**

  Run: `python -m pytest tests/security/test_guardrails.py -q` and `docker build -t fac-phase1:test .`.

  Expected: the guardrail fixtures/configuration and container files are absent.

- [ ] **Step 3: Implement container and quality tooling**

  Add a non-root runtime image, healthcheck, Postgres profile, Ruff configuration, CI workflow, and a Phase 1 runbook mapping commands/results to G-1 through G-9 and the test acceptance matrix.

- [ ] **Step 4: Run the full verification gate**

  Run:

  ```powershell
  python -m pytest -q
  ruff check .
  alembic upgrade head
  python scripts/seed_phase1.py
  docker build -t fac-phase1:test .
  docker run --rm -d --name fac-phase1-smoke -p 8000:8000 fac-phase1:test
  Invoke-WebRequest http://localhost:8000/health
  docker stop fac-phase1-smoke
  ```

  Expected: all tests pass, lint is clean, migration and seed are idempotent, image builds, and the health endpoint returns HTTP 200. If Docker is unavailable, record the limitation and run the equivalent local Uvicorn smoke test.

- [ ] **Step 5: Commit**

  ```powershell
  git add Dockerfile docker-compose.yml Makefile .github tests/security docs/development.md docs/acceptance README.md
  git commit -m "build: add phase one delivery and acceptance gates"
  ```

## Final Verification

After all tasks, run the complete acceptance set from a clean database:

```powershell
alembic downgrade base
alembic upgrade head
python -m pytest -q
ruff check .
python scripts/seed_phase1.py
python scripts/seed_phase1.py
```

Confirm:

- all tests pass with 0 failures;
- the seed is idempotent;
- every verified Result has Evidence;
- missing price/FX cases are incomplete, never fake-complete;
- historical Result versions remain queryable after recalculation;
- replay creates no duplicate finance facts;
- cross-tenant, Agent Verify, manual FX, and direct-system access guardrails pass;
- `git status --short` contains only intentional, reviewed changes.

