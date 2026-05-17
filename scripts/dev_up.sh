#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export ODOO_URL="${ODOO_URL:-http://localhost:8069}"
export ODOO_DB="${ODOO_DB:-odoo}"
export ODOO_USERNAME="${ODOO_USERNAME:-admin}"
export ODOO_PASSWORD="${ODOO_PASSWORD:-admin}"

# 1) Infra + Odoo module ready
./scripts/test_odoo_integration.sh

# 2) Optionally run backend and bot in foreground from this shell
if [[ "${RUN_BACKEND:-0}" == "1" ]]; then
  echo "Starting backend on http://0.0.0.0:8000 ..."
  uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
  BACKEND_PID=$!
fi

if [[ "${RUN_BOT:-0}" == "1" ]]; then
  if [[ -z "${BOT_TOKEN:-}" ]]; then
    echo "BOT_TOKEN is required when RUN_BOT=1" >&2
    exit 1
  fi
  export ODOO_ENABLED="${ODOO_ENABLED:-true}"
  echo "Starting Telegram bot ..."
  python -m bot.main &
  BOT_PID=$!
fi

if [[ -n "${BACKEND_PID:-}" || -n "${BOT_PID:-}" ]]; then
  echo "Services started. Press Ctrl+C to stop."
  trap '[[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID"; [[ -n "${BOT_PID:-}" ]] && kill "$BOT_PID"' INT TERM
  wait
else
  echo "Odoo stack is ready."
  echo "To start everything in one command: RUN_BACKEND=1 RUN_BOT=1 BOT_TOKEN=... ./scripts/dev_up.sh"
fi
