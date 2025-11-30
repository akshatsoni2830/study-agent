#!/usr/bin/env bash
set -euo pipefail

# Create venv
if [ ! -d ".venv" ]; then
  python -m venv .venv
fi

# Activate venv
# shellcheck disable=SC1091
source .venv/bin/activate

# Install deps
python -m pip install --upgrade pip
pip install -r requirements.txt

# Create .env from example if missing
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    cp .env.example .env
    echo "Copied .env.example to .env (edit your secrets)."
  fi
fi

echo "Setup complete. Edit .env, then run scripts/run_cli.sh or scripts/run_server.sh"
