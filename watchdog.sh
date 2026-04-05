#!/bin/bash
# Odoo watchdog — restarts Odoo automatically if it crashes.
# Usage: nohup bash watchdog.sh > /tmp/watchdog.log 2>&1 &

ODOO_DIR="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai"
ODOO_CONF="$ODOO_DIR/odoo_local.conf"
PYTHON="$ODOO_DIR/venv/bin/python"
HEALTH_URL="http://127.0.0.1:8070/web/health"
CHECK_INTERVAL=15   # seconds between health checks
RESTART_DELAY=5     # seconds to wait before restarting after crash

echo "[watchdog] Started at $(date)"

while true; do
  # Check if Odoo is responding
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HEALTH_URL" 2>/dev/null)

  if [ "$HTTP" != "200" ]; then
    echo "[watchdog] $(date) — Odoo DOWN (HTTP=$HTTP). Restarting..."

    # Kill any stale odoo-bin processes
    pkill -f "odoo-bin" 2>/dev/null
    sleep "$RESTART_DELAY"

    # Start Odoo
    cd "$ODOO_DIR" && nohup "$PYTHON" odoo-bin -c "$ODOO_CONF" >> /tmp/odoo.log 2>&1 &
    echo "[watchdog] $(date) — Odoo started with PID $!"

    # Wait for it to come up (up to 60s)
    for i in $(seq 1 12); do
      sleep 5
      HTTP2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HEALTH_URL" 2>/dev/null)
      if [ "$HTTP2" = "200" ]; then
        echo "[watchdog] $(date) — Odoo is UP after restart ✓"
        break
      fi
    done
  fi

  sleep "$CHECK_INTERVAL"
done
