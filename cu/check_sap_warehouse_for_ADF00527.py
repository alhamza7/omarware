#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check SAP Warehouse Info for ADF00527"""

cr = env.cr

print("=" * 80)
print("SAP WAREHOUSE INFO - ADF00527")
print("=" * 80)
print()

# Check in sap_product_warehouse_info
cr.execute("""
    SELECT 
        id,
        sap_warehouse_code,
        sap_warehouse_name,
        last_in_stock,
        last_committed,
        last_ordered,
        last_available,
        minimum_stock,
        maximum_stock,
        sync_status
    FROM sap_product_warehouse_info
    WHERE product_code = 'ADF00527'
    ORDER BY id
""")

results = cr.fetchall()

if results:
    print(f"Found {len(results)} warehouse records for ADF00527")
    print("=" * 80)
    print()
    
    total_stock = 0
    total_available = 0
    
    for row in results:
        (wh_id, code, name, in_stock, committed, ordered, available, 
         min_stock, max_stock, status) = row
        
        print(f"Warehouse ID: {wh_id}")
        print(f"  SAP Code: {code}")
        print(f"  SAP Name: {name}")
        print(f"  In Stock: {in_stock}")
        print(f"  Committed: {committed}")
        print(f"  Ordered: {ordered}")
        print(f"  Available: {available}")
        print(f"  Min Stock: {min_stock}")
        print(f"  Max Stock: {max_stock}")
        print(f"  Status: {status}")
        print()
        
        total_stock += float(in_stock or 0)
        total_available += float(available or 0)
    
    print("=" * 80)
    print("SUMMARY:")
    print(f"  Total In Stock: {total_stock}")
    print(f"  Total Available: {total_available}")
    print(f"  Warehouses: {len(results)}")
    print("=" * 80)
    
else:
    print("NO warehouse info found for ADF00527 in SAP data")
    print()
    print("This could mean:")
    print("  1. Product was not imported from SAP")
    print("  2. Product has no warehouse data in SAP")
    print("  3. Import failed for this product")

print()
print("To view in Odoo UI:")
print("  SAP Integration > Warehouse > Product Warehouse Info")
print("  Search: ADF00527")

exit()






