#!/usr/bin/env bash
# Run once with sudo:  sudo bash /home/lugalai/Lugal-ai/deploy/install_odoo_systemd.sh
set -euo pipefail
ROOT="/home/lugalai/Lugal-ai"
UNIT_SRC="${ROOT}/deploy/odoo-nbs.service"
UNIT_DST="/etc/systemd/system/odoo-nbs.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

# Stop manual / nohup Odoo if any
pkill -f "${ROOT}/venv/bin/python3.*odoo-bin" 2>/dev/null || true
sleep 2

cp -a "${UNIT_SRC}" "${UNIT_DST}"
systemctl daemon-reload
systemctl enable odoo-nbs.service
systemctl restart odoo-nbs.service
sleep 5
systemctl --no-pager status odoo-nbs.service
echo ""
echo "Active: $(systemctl is-active odoo-nbs.service)"
echo "Logs:   journalctl -u odoo-nbs.service -f"
echo "URL:    http://127.0.0.1:8069"
