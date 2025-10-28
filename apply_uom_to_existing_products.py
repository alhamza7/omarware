#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply UoM Groups to existing products
Fetches UoMGroupEntry from SAP and links products
"""

import xmlrpc.client
import time

url = 'http://localhost:8069'
db = 'lugal'
username = 'admin'
password = 'admin'

print("=" * 100)
print("APPLY UoM GROUPS TO EXISTING PRODUCTS")
print("=" * 100)
print("\nThis will:")
print("   1. Fetch UoMGroupEntry from SAP for each product")
print("   2. Link product UoMs to proper groups")
print("   3. Import/update prices for each UoM")
print("   4. Apply conversion factors")
print()
print("⏱️ Estimated time: ~30-60 minutes for 10,670 products")
print()

response = input("Continue? (y/n): ")
if response.lower() != 'y':
    print("Cancelled.")
    exit(0)

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\nConnected")

# Get backend
backends = models.execute_kw(db, uid, password,
    'sap.backend', 'search', [[('active', '=', True)]])
backend_id = backends[0]

# Get all products with SAP code
products = models.execute_kw(db, uid, password,
    'product.product', 'search',
    [[('default_code', '!=', False)]]
)

print("\nFound %d products" % len(products))
print("\nProcessing in batches of 100...")
print("-" * 100)

start = time.time()
processed = 0
linked = 0
prices_updated = 0
errors = 0

# Process in batches
batch_size = 100
total_batches = (len(products) + batch_size - 1) // batch_size

for batch_num in range(total_batches):
    batch_start = batch_num * batch_size
    batch_end = min(batch_start + batch_size, len(products))
    batch_ids = products[batch_start:batch_end]
    
    print("\n[Batch %d/%d] Processing products %d-%d..." % (
        batch_num + 1, total_batches, batch_start + 1, batch_end
    ))
    
    # Get product details
    batch_products = models.execute_kw(db, uid, password,
        'product.product', 'read',
        [batch_ids],
        {'fields': ['default_code']}
    )
    
    for prod in batch_products:
        try:
            item_code = prod['default_code']
            
            # Call the linking function
            result = models.execute_kw(db, uid, password,
                'sap.product.pricelist.sync', 'sync_product_prices_for_item',
                [backend_id, item_code]
            )
            
            processed += 1
            
            if result and result.get('created', 0) > 0:
                prices_updated += result['created']
                linked += 1
            
        except Exception as e:
            errors += 1
            error_msg = str(e)
            if 'not found' not in error_msg.lower() and errors <= 10:
                print("   Error on %s: %s" % (item_code, error_msg[:80]))
    
    # Progress
    elapsed = time.time() - start
    progress = batch_end / len(products)
    if progress > 0:
        estimated_total = elapsed / progress
        remaining = estimated_total - elapsed
        
        print("   Progress: %.0f%%, Elapsed: %.1f min, Remaining: %.1f min" % (
            progress * 100, elapsed/60, remaining/60
        ))

duration = time.time() - start

print("\n" + "=" * 100)
print("COMPLETE!")
print("=" * 100)
print("\nTime: %.2f minutes" % (duration/60))
print("Processed: %d products" % processed)
print("Linked/Updated: %d products" % linked)
print("Prices updated: %d" % prices_updated)
print("Errors/Not found: %d" % errors)
print("\n" + "=" * 100)


