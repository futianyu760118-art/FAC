$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

# Keep Demo data in a separate local database; the default fac.db is untouched.
$env:FAC_DATABASE_URL = "sqlite:///./fac_demo.db"
$env:FAC_DEMO_ENABLED = "true"
$env:PYTHONPATH = Join-Path $repoRoot "src"

python -m alembic upgrade head
python -m uvicorn fac.main:create_app --factory --reload
