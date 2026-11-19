# FAC

FAC is being built in phases. This repository contains the service bootstrap,
EDP fixture boundary, OFA calculation core, and a local finance calculation Demo;
the full Phase 1 MVP is not yet implemented.

## Local setup

Requires Python 3.11. From the repository root, create and activate a virtual
environment, then install the development dependencies:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

The default configuration uses SQLite, `CNY` as the functional currency, and
the `development` environment. Override these values with `FAC_DATABASE_URL`,
`FAC_FUNCTIONAL_CURRENCY`, and `FAC_ENVIRONMENT` in `.env` or the process
environment. Do not put secrets in the example file or source control.

## Run the service

```powershell
uvicorn fac.main:create_app --factory --reload
```

Check the health endpoint at `http://127.0.0.1:8000/health`:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

It returns `{"status":"ok","service":"fac"}`. Run the tests with
`python -m pytest -q`.

## Run the local finance Demo

The Demo uses a separate `fac_demo.db`, seeds a fixed `demo-tenant` order, and
shows real OFA calculation versions, snapshots, results, and replay behavior.
It does not connect to production EDP, M02, M04, M13, or ERP systems.

```powershell
.\scripts\run_fac_demo.ps1
```

Open `http://127.0.0.1:8000/demo/fac`, then run the workflow in order:

1. 初始化 Demo 数据
2. 运行初次计算 — V1 total `46.00 CNY`
3. 价格修正并重算 — V2 total `52.00 CNY`
4. 重放最近事件 — no duplicate result

The Demo is disabled by default through `FAC_DEMO_ENABLED=false`.

## Run the AEOS FAC integration workbench

Open `http://127.0.0.1:8000/fac` for the AEOS-style M09 FAC integration console.
It presents the main cross-system chain from `CRM / PLM → M02 EDP → FAC → M13
Agent → M01 Guard → M10 POMS → Verify → EBMS`, including the Event Ledger,
runtime trace, result/evidence views, and a replay-safe demo action.

The `运行联调演示` button executes the local EDP/OFA workflow and renders the
Agent, Guard, POMS, and Verify stages as explicit integration projections. The
OFA calculation segment is real local demo behavior; external service calls are
represented as clearly labeled sandbox states until those services are connected.
The detailed OFA workbench remains available at `http://127.0.0.1:8000/demo/fac`.

The complete projection is also available from `GET /api/v1/demo/integration`
after initialization. It exposes the correlation ID, idempotency setting, seven
integration stages, the M13 Registry projection, M01 DecisionCase queue, M10
POMS Action queue, FAC Verify evidence coverage, Value Ledger, EBMS consumption
status, and the event ledger. Before initialization it returns `404` so the UI
does not show a false completed state.
