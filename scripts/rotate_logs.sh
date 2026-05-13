#!/bin/bash
# Rotates odoo.log using the local logrotate config.
# Run manually or via cron: 0 0 * * * /home/lugalai/Lugal-ai/rotate_logs.sh

LOGROTATE_CONF="/home/lugalai/Lugal-ai/logrotate-odoo.conf"
LOGROTATE_STATE="/home/lugalai/Lugal-ai/logrotate.state"

logrotate --state "$LOGROTATE_STATE" "$LOGROTATE_CONF"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Log rotation completed" >> /home/lugalai/Lugal-ai/rotate_logs.log
