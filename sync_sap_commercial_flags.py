#!/usr/bin/env python3
"""
One-off: update Odoo product.template flags from SAP Items.

Uses Valid + Frozen for active; SalesItem / PurchaseItem for sale_ok, POS, purchase_ok
(same rules as sap.product.complete.migration).

Usage:
    cd /home/lugalai/Lugal-ai
    ./venv/bin/python3 sync_sap_commercial_flags.py [-c odoo_simple.conf] [--db DATABASE]
"""

import argparse
import configparser
import logging
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from odoo.tools import config as odoo_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
_logger = logging.getLogger("sync_sap_commercial_flags")


def _resolve_config_path(explicit):
    if explicit:
        p = explicit if os.path.isabs(explicit) else os.path.join(ROOT, explicit)
        return p if os.path.isfile(p) else None
    for name in ("odoo.conf", "odoo_simple.conf", "odoo_local.conf"):
        p = os.path.join(ROOT, name)
        if os.path.isfile(p):
            return p
    return None


def _db_name_from_config(config_path):
    try:
        cp = configparser.ConfigParser()
        cp.read(config_path)
        if cp.has_option("options", "db_name"):
            return cp.get("options", "db_name").strip() or None
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        default=None,
        help="Odoo config file (default: first of odoo.conf, odoo_simple.conf, odoo_local.conf)",
    )
    parser.add_argument(
        "--db",
        default=os.environ.get("ODOO_DB") or None,
        help="Odoo database name (default: db_name from config or nbs_lugalai)",
    )
    parser.add_argument(
        "--force-enable-sales-pos",
        action="store_true",
        help="Ignore SAP SalesItem; enable sale_ok/POS for all non-frozen items",
    )
    args = parser.parse_args()

    cfg = _resolve_config_path(args.config)
    if not cfg:
        _logger.error(
            "No readable Odoo config. Pass -c path/to/odoo.conf or add odoo_simple.conf in %s",
            ROOT,
        )
        return 1

    db = args.db or _db_name_from_config(cfg) or "nbs_lugalai"
    _logger.info("Using config=%s database=%s", cfg, db)

    odoo_config.parse_config(["--config", cfg, "--no-http", "-d", db])

    from odoo.modules.registry import Registry
    from odoo import api, SUPERUSER_ID

    registry = Registry(db)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        backend = env["sap.backend"].search([("active", "=", True)], limit=1)
        if not backend:
            _logger.error("No active sap.backend found.")
            return 1
        wiz = env["sap.product.complete.migration"].create(
            {
                "backend_id": backend.id,
                "batch_size": 100,
                "product_limit": 0,
                "force_enable_sales_pos": args.force_enable_sales_pos,
            }
        )
        res = wiz.sync_commercial_flags_from_sap()
        cr.commit()
        _logger.info(
            "Done: updated=%s not_in_odoo=%s errors=%s",
            res.get("updated"),
            res.get("not_in_odoo"),
            res.get("errors"),
        )
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
