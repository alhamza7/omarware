#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test creating a sale order with different UoMs"""

import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 80)
print("TEST: UoM in Sales Order")
print("=" * 80)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected")

# Get a product
product = models.execute_kw(db, uid, password,
    'product.product', 'search_read',
    [[('default_code', '!=', False)]],
    {'fields': ['id', 'default_code', 'name', 'uom_id', 'list_price'], 'limit': 1}
)[0]

print("\nProduct: %s (%s)" % (product['default_code'], product['name']))
print("   Base UoM: %s" % (product['uom_id'][1] if product.get('uom_id') else 'N/A'))
print("   List Price: %.2f" % product.get('list_price', 0))

# Get available UoMs
print("\nAvailable UoMs for this product:")
print("   (In Odoo, you can select from all UoMs in the dropdown)")
print("   The price will adjust automatically based on pricelist rules")

# Show pricelists
pricelists = models.execute_kw(db, uid, password,
    'product.pricelist', 'search_read',
    [[]],
    {'fields': ['name']}
)

print("\nAvailable Pricelists:")
for pl in pricelists:
    print("   - %s" % pl['name'])

print("\n" + "=" * 80)
print("READY TO TEST!")
print("=" * 80)
print("\nGo to Odoo:")
print("   Sales → Quotations → Create")
print("   Add product: %s" % product['default_code'])
print("   Change UoM → Notice price changes!")
print("=" * 80)


