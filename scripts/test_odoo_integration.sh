#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[1/5] Starting Odoo + Postgres..."
docker compose up -d db odoo

echo "[2/5] Waiting for Odoo HTTP health..."
for i in {1..60}; do
  if curl -fsS http://localhost:8069/web/health >/dev/null 2>&1; then
    break
  fi
  sleep 2
  if [[ "$i" == "60" ]]; then
    echo "Odoo did not become ready in time" >&2
    exit 1
  fi
done

echo "[3/5] Installing video_automation module..."
docker compose exec -T odoo odoo -d odoo -i video_automation --stop-after-init

echo "[4/5] Checking XML-RPC auth + model availability..."
python - <<'PY'
import xmlrpc.client
url = "http://localhost:8069"
db = "odoo"
username = "admin"
password = "admin"
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, username, password, {})
if not uid:
    raise SystemExit("Auth failed for admin/admin. Set admin password in Odoo UI and update script/env.")
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
ids = models.execute_kw(db, uid, password, "ir.model", "search", [[("model", "=", "video.job")]], {"limit": 1})
if not ids:
    raise SystemExit("video.job model not found")
print("OK: XML-RPC auth works and video.job exists")
PY

echo "[5/5] Done. You can run bot with ODOO_ENABLED=true and ODOO_* env vars."
