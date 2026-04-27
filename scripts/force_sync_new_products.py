#!/usr/bin/env python3
"""
Force full product sync from SAP for the past week.

Resets the last_sync_at to 7 days ago on all active realtime sync configs,
then triggers delta sync immediately so new SAP products added in the last
week are imported into Odoo without waiting for the cron scheduler.

Usage:
    cd /home/lugalai/Lugal-ai
    ./venv/bin/python3 force_sync_new_products.py
"""

import sys
import os
import logging
from datetime import datetime, timedelta

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from odoo.tools import config as odoo_config
odoo_config.parse_config([
    '--config', os.path.join(ROOT, 'odoo.conf'),
    '--no-http',
])

from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%H:%M:%S',
)
_logger = logging.getLogger('force_sync_products')

def log(msg):
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"{ts}  {msg}", flush=True)

DB = 'nbs_lugalai'


def main():
    log("=" * 70)
    log(f"SAP Force Full-Product Sync  —  DB: {DB}")
    log("=" * 70)

    registry = Registry(DB)

    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        SyncModel = env['sap.realtime.sync']
        configs = SyncModel.search([('active', '=', True)])

        if not configs:
            log("WARNING: No active sap.realtime.sync configs found!")
            return

        log(f"Found {len(configs)} active realtime sync config(s):")
        for c in configs:
            log(f"  • [{c.id}] {c.name or '(no name)'}  |  last_sync_at: {c.last_sync_at or 'never'}  |  auto_create_products: {c.auto_create_products}")

        seven_days_ago = datetime.now() - timedelta(days=7)
        log("")
        log(f"Resetting last_sync_at → {seven_days_ago.strftime('%Y-%m-%d %H:%M:%S')}  (7 days back)")

        configs.write({
            'last_sync_at': seven_days_ago,
            'auto_create_products': True,
        })
        cr.commit()

        log("")
        log("Starting delta sync (fetching all SAP items changed in last 7 days)…")

        total_created = 0
        total_updated = 0

        for config in configs:
            log("")
            log(f"▶ Syncing: {config.name or f'config #{config.id}'}")
            try:
                config._run_delta_sync()
                cr.commit()
                log_text = config.last_sync_log or ''
                log(f"  Status  : {config.last_sync_status}")
                log(f"  Changed : {config.last_items_changed} items")

                for line in log_text.splitlines():
                    if line.strip():
                        log(f"  {line.strip()}")
                    if 'Products created' in line:
                        try:
                            total_created += int(line.split(':')[-1].strip())
                        except Exception:
                            pass
                    if 'Products updated' in line:
                        try:
                            total_updated += int(line.split(':')[-1].strip())
                        except Exception:
                            pass

            except Exception as exc:
                import traceback
                log(f"  ERROR for config [{config.id}]: {exc}")
                traceback.print_exc()

        log("")
        log("=" * 70)
        log("SUMMARY")
        log(f"  New products created : {total_created}")
        log(f"  Existing updated     : {total_updated}")
        log("=" * 70)


if __name__ == '__main__':
    main()
