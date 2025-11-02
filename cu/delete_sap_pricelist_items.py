#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
سكريبت لحذف pricelist items من SAP Price Lists
استخدمه من Developer Mode في Odoo:
Settings → Technical → Automation → Scheduled Actions → Create → Python Code
"""

# حذف جميع pricelist items من SAP pricelists
pricelists = env['product.pricelist'].search([('name', 'like', 'SAP Price List%')])
total_items = 0

for pricelist in pricelists:
    items_count = len(pricelist.item_ids)
    total_items += items_count
    log(f"Deleting {items_count} items from {pricelist.name}")
    pricelist.item_ids.unlink()

# حذف sync records
sync_records = env['sap.product.pricelist.sync'].search([])
log(f"Deleting {len(sync_records)} sync records")
sync_records.unlink()

log(f"Done! Deleted {total_items} pricelist items and {len(sync_records)} sync records")


