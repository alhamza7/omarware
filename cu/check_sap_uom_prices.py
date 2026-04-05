#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check SAP for UoM-Specific Prices"""

print("=" * 80)
print("CHECK SAP FOR UoM PRICES")
print("=" * 80)
print()

# Get backend
backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if not backend:
    print("No SAP backend found!")
    exit()

print(f"Backend: {backend.name}")
print()

try:
    connection = backend.get_connection()
    
    # Get a sample product with its prices
    print("Fetching sample product from SAP...")
    
    params = {
        '$top': 1,
        '$filter': "ItemCode eq 'ADF00001'",
        '$select': 'ItemCode,ItemName,ItemPrices'
    }
    
    items_data = connection.get('Items', params)
    items = items_data.get('value', [])
    
    if items:
        item = items[0]
        item_code = item.get('ItemCode')
        item_prices = item.get('ItemPrices', [])
        
        print(f"Product: {item_code}")
        print(f"Number of prices: {len(item_prices)}")
        print()
        
        if item_prices:
            print("Price details from SAP:")
            print("-" * 80)
            for price_data in item_prices[:5]:  # First 5 prices
                print(f"  PriceList: {price_data.get('PriceList')}")
                print(f"    Price: {price_data.get('Price')}")
                print(f"    Currency: {price_data.get('Currency')}")
                print(f"    UoMCode: {price_data.get('UoMCode', 'NOT PRESENT')}")
                print(f"    UoMEntry: {price_data.get('UoMEntry', 'NOT PRESENT')}")
                print()
            
            # Check if any price has UoM info
            has_uom = any(p.get('UoMCode') or p.get('UoMEntry') for p in item_prices)
            
            print("=" * 80)
            if has_uom:
                print("RESULT: SAP HAS UoM-specific prices!")
                print("  Problem: They were not imported correctly")
                print("  Solution: Need to fix import code")
            else:
                print("RESULT: SAP does NOT have UoM-specific prices")
                print("  All prices use default UoM")
                print("  This is normal for many SAP configurations")
            print("=" * 80)
        else:
            print("No prices found in SAP for this product")
    else:
        print("Product not found in SAP")
        
except Exception as e:
    print(f"Error connecting to SAP: {str(e)}")

exit()





