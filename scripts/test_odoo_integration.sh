#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ODOO_URL="${ODOO_URL:-http://localhost:8069}"
ODOO_DB="${ODOO_DB:-odoo}"
ODOO_USERNAME="${ODOO_USERNAME:-admin}"
ODOO_PASSWORD="${ODOO_PASSWORD:-admin}"
export ODOO_URL ODOO_DB ODOO_USERNAME ODOO_PASSWORD

echo "[1/6] Starting Odoo + Postgres..."
docker compose up -d db odoo

echo "[2/6] Waiting for Odoo XML-RPC endpoint..."
python - <<'PY2'
import os
import time
import xmlrpc.client

url = os.environ.get("ODOO_URL", "http://localhost:8069")
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)

last_err = None
for _ in range(90):
    try:
        common.version()
        print("OK: Odoo XML-RPC is reachable")
        break
    except Exception as err:
        last_err = err
        time.sleep(2)
else:
    raise SystemExit(f"Odoo did not become ready in time: {last_err}")
PY2

echo "[3/6] Initializing DB + installing video_automation module..."
docker compose exec -T odoo odoo -d "$ODOO_DB" -i base,video_automation --without-demo=all --stop-after-init

echo "[4/6] Verifying XML-RPC auth..."
python - <<'PY3'
import os
import xmlrpc.client

url = os.environ.get("ODOO_URL", "http://localhost:8069")
db = os.environ.get("ODOO_DB", "odoo")
username = os.environ.get("ODOO_USERNAME", "admin")
password = os.environ.get("ODOO_PASSWORD", "admin")

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, username, password, {})
if not uid:
    raise SystemExit(
        "Auth failed. Verify ODOO_DB/ODOO_USERNAME/ODOO_PASSWORD. "
        "For a fresh DB in this setup default is admin/admin."
    )
print(f"OK: auth works, uid={uid}")
PY3

echo "[5/6] Checking model video.job availability..."
python - <<'PY4'
import os
import xmlrpc.client

url = os.environ.get("ODOO_URL", "http://localhost:8069")
db = os.environ.get("ODOO_DB", "odoo")
username = os.environ.get("ODOO_USERNAME", "admin")
password = os.environ.get("ODOO_PASSWORD", "admin")

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
ids = models.execute_kw(db, uid, password, "ir.model", "search", [[("model", "=", "video.job")]], {"limit": 1})
if not ids:
    raise SystemExit("video.job model not found")
print("OK: video.job exists")
PY4

echo "[6/6] Done. Integration stack is ready."
