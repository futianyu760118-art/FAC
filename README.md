# FAC

FAC is being built in phases. This repository currently contains the initial
service bootstrap and health endpoint; the full Phase 1 MVP is not yet implemented.

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
