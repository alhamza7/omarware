#!/usr/bin/env python3
"""
fix_sap_sales_flags.py
======================
Fetches all SAP items where SalesItem=tYES and Frozen=tNO,
then enables sale_ok, available_in_pos, purchase_ok in Odoo
for matching products (matched by default_code = ItemCode).

Only touches products that are:
  - active = true  in Odoo
  - sale_ok = false OR available_in_pos = false OR purchase_ok = false

Usage:
    cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
    ./venv/bin/python fix_sap_sales_flags.py
"""

import sys
import json
import logging
import requests
import psycopg2
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
_logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
SAP_BASE_URL   = 'https://192.168.15.50:50000/b1s/v1'
SAP_USER       = 'manager'
SAP_PASSWORD   = 'na54321'
SAP_COMPANY_DB = 'NBS_TEST_27_03_2026'
DB_NAME        = 'lugal_local'
DB_USER        = 'capo7amzah'
BATCH_SIZE     = 500
# ──────────────────────────────────────────────────────────────────────────────


def sap_login(session):
    """Login to SAP Service Layer and return session cookie."""
    resp = session.post(
        f'{SAP_BASE_URL}/Login',
        json={'UserName': SAP_USER, 'Password': SAP_PASSWORD, 'CompanyDB': SAP_COMPANY_DB},
        verify=False, timeout=30,
    )
    resp.raise_for_status()
    _logger.info('SAP login OK — session established')


def fetch_sap_sales_items(session):
    """
    Fetch ALL SAP items where SalesItem=tYES and Frozen=tNO.
    Returns a dict: {ItemCode: {'sales': bool, 'purchase': bool}}
    """
    result = {}
    skip = 0
    page = 1

    while True:
        params = {
            '$select': 'ItemCode,SalesItem,PurchaseItem,Frozen',
            '$filter': "SalesItem eq 'tYES' and Frozen eq 'tNO'",
            '$top': BATCH_SIZE,
            '$skip': skip,
            '$orderby': 'ItemCode',
        }
        resp = session.get(f'{SAP_BASE_URL}/Items', params=params, verify=False, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        batch = data.get('value', [])

        if not batch:
            break

        for item in batch:
            code = (item.get('ItemCode') or '').strip()
            if code:
                result[code] = {
                    'sales':    (item.get('SalesItem', 'tNO') == 'tYES'),
                    'purchase': (item.get('PurchaseItem', 'tNO') == 'tYES'),
                }

        _logger.info('Page %d: fetched %d items (total so far: %d)', page, len(batch), len(result))

        if len(batch) < BATCH_SIZE:
            break

        skip += BATCH_SIZE
        page += 1

    _logger.info('SAP: total items with SalesItem=tYES → %d', len(result))
    return result


def update_odoo_products(sap_items):
    """
    For each SAP item that has SalesItem=tYES, find the matching Odoo product
    by default_code and enable sale_ok / available_in_pos / purchase_ok.
    Only updates products that actually need changing.
    """
    conn = psycopg2.connect(f'dbname={DB_NAME} user={DB_USER}')
    conn.autocommit = False
    cur = conn.cursor()

    # Fetch all Odoo products that need fixing (active but any flag disabled)
    cur.execute("""
        SELECT id, default_code, sale_ok, available_in_pos, purchase_ok
        FROM product_template
        WHERE active = true
          AND default_code IS NOT NULL
          AND default_code != ''
          AND (sale_ok = false OR available_in_pos = false OR purchase_ok = false)
        ORDER BY default_code
    """)
    odoo_products = cur.fetchall()
    _logger.info('Odoo: %d active products with at least one flag disabled', len(odoo_products))

    updated = 0
    skipped_not_in_sap = 0
    skipped_sap_no_sales = 0

    for row in odoo_products:
        tmpl_id, code, sale_ok, pos_ok, purchase_ok = row
        code = (code or '').strip()

        if code not in sap_items:
            skipped_not_in_sap += 1
            continue

        sap = sap_items[code]
        new_sale     = sap['sales']
        new_pos      = sap['sales']      # POS follows SalesItem
        new_purchase = sap['purchase']

        # Nothing to change
        if sale_ok == new_sale and pos_ok == new_pos and purchase_ok == new_purchase:
            continue

        if not new_sale:
            # SAP itself says SalesItem=tNO for this product — skip
            skipped_sap_no_sales += 1
            continue

        cur.execute("""
            UPDATE product_template
            SET sale_ok = %s,
                available_in_pos = %s,
                purchase_ok = %s,
                write_date = NOW()
            WHERE id = %s
        """, (new_sale, new_pos, new_purchase, tmpl_id))

        updated += 1
        if updated % 500 == 0:
            conn.commit()
            _logger.info('  ... committed %d updates so far', updated)

    conn.commit()
    cur.close()
    conn.close()

    _logger.info('─' * 60)
    _logger.info('Done.')
    _logger.info('  Updated (enabled):         %d products', updated)
    _logger.info('  Not in SAP item list:      %d products', skipped_not_in_sap)
    _logger.info('  SAP SalesItem=tNO (kept):  %d products', skipped_sap_no_sales)
    return updated


def main():
    session = requests.Session()
    session.headers.update({'Content-Type': 'application/json', 'Accept': 'application/json'})

    _logger.info('Step 1: Logging in to SAP...')
    sap_login(session)

    _logger.info('Step 2: Fetching SAP sales items...')
    sap_items = fetch_sap_sales_items(session)

    _logger.info('Step 3: Updating Odoo products...')
    update_odoo_products(sap_items)


if __name__ == '__main__':
    main()
