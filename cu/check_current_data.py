#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import xmlrpc.client

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("=" * 80)
print("Checking Current Data")
print("=" * 80)

# Check sap.uom.sync
sync_count = models.execute_kw(db, uid, password, 'sap.uom.sync', 'search_count', [[]])
print(f"\nsap.uom.sync: {sync_count} records")

# Check sap.product.uom
try:
    product_uom_count = models.execute_kw(db, uid, password, 'sap.product.uom', 'search_count', [[]])
    print(f"sap.product.uom: {product_uom_count} records")
except:
    print("sap.product.uom: Model not accessible or no records")

# Check sap.uom.mapping
try:
    mapping_count = models.execute_kw(db, uid, password, 'sap.uom.mapping', 'search_count', [[]])
    print(f"sap.uom.mapping: {mapping_count} records")
except:
    print("sap.uom.mapping: Model not accessible or no records")

# Check products
product_count = models.execute_kw(db, uid, password, 'product.product', 'search_count', [[]])
print(f"product.product: {product_count} records")

# Check pricelists
pricelist_count = models.execute_kw(db, uid, password, 'product.pricelist', 'search_count', [[]])
print(f"product.pricelist: {pricelist_count} records")

print("\n" + "=" * 80)




