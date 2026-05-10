#!/usr/bin/env bash
# Restart Odoo using odoo_ws.conf (WS / sandbox instance).
# Safe to run repeatedly; waits until old workers exit, then waits for HTTP health.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON="${ROOT}/venv/bin/python"
CONF="${ROOT}/odoo_ws.conf"
LOG="${ROOT}/odoo_ws.log"

if [[ ! -x "$PYTHON" ]]; then
  echo "restart_odoo_ws.sh: missing executable $PYTHON" >&2
  exit 1
fi
if [[ ! -f "$CONF" ]]; then
  echo "restart_odoo_ws.sh: missing $CONF" >&2
  exit 1
fi

HTTP_PORT="$(grep -E '^[[:space:]]*http_port[[:space:]]*=' "$CONF" 2>/dev/null | head -1 | sed 's/.*=[[:space:]]*//' | tr -d '[:space:]')"
HTTP_PORT="${HTTP_PORT:-8075}"
HEALTH_URL="http://127.0.0.1:${HTTP_PORT}/web/health"

echo "restart_odoo_ws.sh: stopping odoo-bin (odoo_ws.conf)..."
# Match both `-c odoo_ws.conf` and `-c /abs/path/odoo_ws.conf`
pkill -f "odoo-bin.*odoo_ws\.conf" 2>/dev/null || true

for _ in $(seq 1 30); do
  if ! pgrep -f "odoo-bin.*odoo_ws\.conf" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "restart_odoo_ws.sh: starting Odoo..."
nohup "$PYTHON" odoo-bin -c "$CONF" --logfile="$LOG" >/dev/null 2>&1 &

for _ in $(seq 1 90); do
  code="$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" 2>/dev/null || echo 000)"
  if [[ "$code" == "200" ]]; then
    echo "restart_odoo_ws.sh: OK (HTTP $code on port $HTTP_PORT)"
    exit 0
  fi
  sleep 1
done

echo "restart_odoo_ws.sh: timed out waiting for $HEALTH_URL" >&2
exit 1
