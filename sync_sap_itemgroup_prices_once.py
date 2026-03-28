#!/usr/bin/env python3
"""
One-off: لكل منتج موجود في أودو (له default_code / رمز ساب)، جلب ItemPrices من ساب
وتحديث قوائم الأسعار عبر sap.product.pricelist.sync.

لا يُنشئ منتجات جديدة ولا يعتمد على فلتر ItemsGroupName في API ساب (غير مدعوم عندكم).

Usage:
    ./venv/bin/python3 sync_sap_itemgroup_prices_once.py
    ./venv/bin/python3 sync_sap_itemgroup_prices_once.py --limit 200
    ./venv/bin/python3 sync_sap_itemgroup_prices_once.py --group-prefix ALC   # فرعي: فقط من مجموعة أودو
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from odoo.tools import config as odoo_config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger('sync_odoo_prices_from_sap')

DEFAULT_DB = 'nbs_lugalai'
PROGRESS_EVERY = 50


def odata_escape(val):
    return str(val).replace("'", "''")


def matches_group_prefix(env, product, prefix: str) -> bool:
    """prefix مطابقة في اسم مجموعة أودو (قالب أو sap.product.extended)."""
    p = prefix.strip().lower()
    if not p:
        return True
    tmpl = product.product_tmpl_id
    g = (tmpl.sap_items_group_name or '').strip().lower()
    if g.startswith(p):
        return True
    ext = env['sap.product.extended'].search([('product_id', '=', product.id)], limit=1)
    if ext:
        g2 = (ext.items_group_name or '').strip().lower()
        if g2.startswith(p):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(
        description='Sync SAP ItemPrices for Odoo products only (by default_code)',
    )
    parser.add_argument('--db', default=DEFAULT_DB, help='Odoo database name')
    parser.add_argument(
        '--group-prefix',
        default='',
        help='Optional: only variants whose SAP item group name in Odoo contains/starts with this (e.g. ALC)',
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=0,
        help='If > 0, stop after this many distinct item codes synced or attempted',
    )
    args = parser.parse_args()

    odoo_config.parse_config([
        '--config', os.path.join(ROOT, 'odoo.conf'),
        '--no-http',
    ])

    from odoo.modules.registry import Registry
    from odoo import api, SUPERUSER_ID

    db = args.db
    gprefix = (args.group_prefix or '').strip()

    log.info('=' * 60)
    log.info('Sync SAP prices for Odoo products | db=%s', db)
    if gprefix:
        log.info('Filter: item group in Odoo ~= %r', gprefix)
    if args.limit > 0:
        log.info('Limit: %s distinct codes', args.limit)
    log.info('=' * 60)

    registry = Registry(db)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        backend = env['sap.backend'].search([('active', '=', True)], limit=1)
        if not backend:
            log.error('No active sap.backend')
            return 1

        connection = backend.get_connection()
        if not connection:
            log.error('Could not connect to SAP')
            return 1

        Product = env['product.product']
        PlSync = env['sap.product.pricelist.sync']

        # كل المتغيرات ذات رمز — نعالج كل ItemCode مرة واحدة
        candidates = Product.search([('default_code', '!=', False)], order='id')
        seen_codes: set[str] = set()
        to_process: list = []
        for product in candidates:
            code = (product.default_code or '').strip()
            if not code or code in seen_codes:
                continue
            if gprefix and not matches_group_prefix(env, product, gprefix):
                continue
            seen_codes.add(code)
            to_process.append(product)
            if args.limit > 0 and len(to_process) >= args.limit:
                break

        log.info('Odoo products to sync (distinct codes): %s', len(to_process))

        synced = skipped_nopr = 0
        errors: list[str] = []
        n = 0

        for product in to_process:
            item_code = (product.default_code or '').strip()
            esc = odata_escape(item_code)
            n += 1
            if n % PROGRESS_EVERY == 0:
                log.info('Progress: %s / %s …', n, len(to_process))
            try:
                item_with_prices = connection.get(
                    'Items', {'$filter': f"ItemCode eq '{esc}'"}
                )
                if item_with_prices.get('status_code', 200) >= 400:
                    errors.append(f'{item_code}: SAP HTTP error')
                    continue
                items_value = item_with_prices.get('value') or []
                if not items_value:
                    errors.append(f'{item_code}: not in SAP')
                    continue
                full_item = items_value[0]
                item_prices = full_item.get('ItemPrices') or []
                if not item_prices:
                    skipped_nopr += 1
                    continue
                PlSync._sync_extended_info_from_item_data(product, backend, full_item)
                PlSync.sync_product_prices_from_sap(product, backend, item_prices)
                synced += 1
                cr.commit()
            except Exception as exc:
                errors.append(f'{item_code}: {exc}')
                log.warning('%s', errors[-1])
                cr.rollback()

        log.info(
            'Done: synced=%s skipped_no_sap_prices=%s errors=%s',
            synced,
            skipped_nopr,
            len(errors),
        )
        if errors[:25]:
            for e in errors[:25]:
                log.info('  err: %s', e)
            if len(errors) > 25:
                log.info('  ... +%s more', len(errors) - 25)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
