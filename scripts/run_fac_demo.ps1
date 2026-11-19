$ErrorActionPreference = "Stop"

Write-Host "FAC Demo 仅用于本地测试，不代表正式运行环境。"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $scriptRoot "..")).Path
Set-Location $repoRoot

# Keep Demo data in a separate local database; the formal data directory is untouched.
$env:FAC_DATABASE_URL = "sqlite:///./fac_demo.db"
$env:FAC_DEMO_ENABLED = "true"
$env:PYTHONPATH = Join-Path $repoRoot "src"

python -m alembic upgrade head
python -m uvicorn fac.main:create_app --factory --reload
