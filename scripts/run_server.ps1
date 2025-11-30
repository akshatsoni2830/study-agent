$ErrorActionPreference = 'Stop'

if (!(Test-Path -Path ".venv")) {
  Write-Host "Virtualenv not found. Run scripts/setup.ps1 first." -ForegroundColor Yellow
  exit 1
}

. ".venv/Scripts/Activate.ps1"

python -m src.server
