#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check UoM-Specific Prices"""

print("=" * 80)
print("CHECK UoM-SPECIFIC PRICES")
print("=" * 80)
print()

cr = env.cr

# 1. Check if sap_product_pricelist_sync has uom_id field
print("1. Checking sap_product_pricelist_sync structure...")
cr.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'sap_product_pricelist_sync'
    AND column_name IN ('uom_id', 'uom_code')
""")

uom_columns = [row[0] for row in cr.fetchall()]
print(f"   UoM-related columns: {uom_columns}")
print()

# 2. Check if we have products with multiple prices (different UoMs)
print("2. Checking for products with UoM-specific prices...")
cr.execute("""
    SELECT 
        product_code,
        COUNT(*) as price_count,
        COUNT(DISTINCT uom_id) as uom_count
    FROM sap_product_pricelist_sync
    WHERE uom_id IS NOT NULL
    GROUP BY product_code
    HAVING COUNT(*) > 2
    ORDER BY COUNT(*) DESC
    LIMIT 10
""")

multi_uom_products = cr.fetchall()
if multi_uom_products:
    print(f"   Found {len(multi_uom_products)} products with UoM-specific prices:")
    for code, price_count, uom_count in multi_uom_products:
        print(f"     {code}: {price_count} prices, {uom_count} different UoMs")
    print()
else:
    print("   NO products with UoM-specific prices found")
    print()

# 3. Check a specific product example
print("3. Checking sample product with multiple UoMs...")
cr.execute("""
    SELECT 
        product_code,
        sap_pricelist_num,
        price,
        uom_id,
        uom_code
    FROM sap_product_pricelist_sync
    WHERE product_code IN (
        SELECT product_code 
        FROM sap_product_pricelist_sync
        GROUP BY product_code
        HAVING COUNT(DISTINCT uom_id) > 1
        LIMIT 1
    )
    ORDER BY product_code, sap_pricelist_num, uom_id
    LIMIT 10
""")

sample_prices = cr.fetchall()
if sample_prices:
    print("   Sample UoM-specific prices:")
    for code, plist, price, uom_id, uom_code in sample_prices:
        uom_name = "Default" if not uom_id else f"UoM {uom_id}"
        print(f"     {code} | Pricelist {plist} | {uom_name} | Price: {price}")
    print()
else:
    print("   NO UoM-specific prices in data")
    print()

# 4. Check total prices with/without UoM
cr.execute("""
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN uom_id IS NOT NULL THEN 1 END) as with_uom,
        COUNT(CASE WHEN uom_id IS NULL THEN 1 END) as without_uom
    FROM sap_product_pricelist_sync
""")

total, with_uom, without_uom = cr.fetchone()

print("=" * 80)
print("SUMMARY:")
print("=" * 80)
print(f"  Total price records: {total}")
print(f"  With UoM specified: {with_uom}")
print(f"  Without UoM (default): {without_uom}")
print()

if with_uom > 0:
    percentage = (with_uom / total) * 100
    print(f"  UoM-specific prices: {percentage:.1f}% of total")
    print()
    print("  YES - UoM-specific prices were imported!")
else:
    print("  NO - All prices use default UoM")
    print()
    print("  This could mean:")
    print("    - SAP doesn't have UoM-specific prices")
    print("    - OR they weren't imported properly")

print("=" * 80)

exit()





