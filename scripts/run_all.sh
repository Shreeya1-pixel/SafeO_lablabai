#!/usr/bin/env bash
# SafeO — start the FastAPI decision engine (required for Odoo + demos).
# Odoo itself is not bundled here; run your Odoo 19 instance separately (see README).

set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend"

if [[ ! -d .venv ]]; then
  echo "No .venv found. Create one and install deps:"
  echo "  cd SafeO/backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

export PYTHONPATH="${ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
echo "Starting SafeO API on http://127.0.0.1:8001 (Swagger: /docs)"
echo "In another terminal: start Odoo with addons-path including SafeO/odoo_module"
exec .venv/bin/python -m uvicorn safeo_backend.main:app --host 127.0.0.1 --port 8001 --reload
