param(
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $repoRoot

# 正式本地运行：只升级数据库并显式导入 Phase 1 EDP 夹具，不启用 Demo。
$dataDirectory = Join-Path $repoRoot "data"
New-Item -ItemType Directory -Force -Path $dataDirectory | Out-Null
$env:FAC_DATABASE_URL = "sqlite:///./data/fac.db"
$env:FAC_TENANT_ID = "tenant-a"
$env:FAC_DEMO_ENABLED = "false"
$env:FAC_ENVIRONMENT = "development"
$env:PYTHONPATH = Join-Path $repoRoot "src"

python -m alembic upgrade head

python -c "import json; from pathlib import Path; from fac.adapters.edp_mock.adapter import EdpAdapter; from fac.adapters.edp_mock.models import EdpFixture; from fac.infrastructure.db import make_session_factory; payload=EdpFixture.model_validate(json.loads(Path('fixtures/edp/sample_phase1.json').read_text(encoding='utf-8'))); session=make_session_factory()(); report=EdpAdapter(session).import_fixture(payload); print('EDP fixture:', report.model_dump_json()); session.close()"

python -m uvicorn fac.main:create_app --factory --reload --port $Port
