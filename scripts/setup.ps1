param(
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

# Create venv
if (!(Test-Path -Path ".venv")) {
  python -m venv .venv
}

# Activate venv
$venvActivate = Join-Path ".venv" "Scripts\Activate.ps1"
. $venvActivate

# Install deps
pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example if missing
if (!(Test-Path -Path ".env") -or $Force) {
  if (Test-Path -Path ".env.example") {
    Copy-Item ".env.example" ".env" -Force
    Write-Host "Copied .env.example to .env (edit your secrets)."
  }
}

Write-Host "Setup complete. Edit .env, then run scripts/run_cli.ps1 or scripts/run_server.ps1"
