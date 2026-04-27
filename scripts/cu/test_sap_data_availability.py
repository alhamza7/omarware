#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test SAP Data Availability"""

print("\n" + "=" * 80)
print("TESTING SAP DATA AVAILABILITY")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if backend:
    print(f"Backend: {backend.name}\n")
    
    connection = backend.get_connection()
    
    # Test 1: Get single item with all expansions
    print("-" * 80)
    print("Test 1: Fetching single item with expansions...")
    print("-" * 80)
    
    products = env['product.product'].search([('default_code', '!=', False)], limit=1)
    if products:
        item_code = products[0].default_code
        print(f"Testing with item: {item_code}")
        
        # Try with full expansion
        params = {
            '$filter': f"ItemCode eq '{item_code}'",
            '$expand': 'ItemPrices,ItemWarehouseInfoCollection'
        }
        
        result = connection.get('Items', params)
        
        if result.get('value'):
            item = result['value'][0]
            
            # Check what's available
            has_foreign = 'ForeignName' in item and item['ForeignName']
            has_prices = 'ItemPrices' in item and len(item.get('ItemPrices', [])) > 0
            has_warehouse = 'ItemWarehouseInfoCollection' in item and len(item.get('ItemWarehouseInfoCollection', [])) > 0
            
            print(f"\nAvailable Data:")
            print(f"  ForeignName: {'YES' if has_foreign else 'NO'}")
            if has_foreign:
                print(f"    Value: {item.get('ForeignName', 'N/A')}")
            
            print(f"  ItemPrices: {'YES - ' + str(len(item.get('ItemPrices', []))) + ' prices' if has_prices else 'NO'}")
            if has_prices:
                for price in item.get('ItemPrices', [])[:2]:
                    print(f"    List {price.get('PriceList')}: {price.get('Price')} {price.get('Currency')}")
            
            print(f"  WarehouseInfo: {'YES - ' + str(len(item.get('ItemWarehouseInfoCollection', []))) + ' wh' if has_warehouse else 'NO'}")
            if has_warehouse:
                for wh in item.get('ItemWarehouseInfoCollection', [])[:2]:
                    print(f"    {wh.get('WarehouseCode')}: {wh.get('InStock')} in stock")
            
            print(f"\n  Total SAP fields: {len(item.keys())}")
    
    connection.close_session()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)

env.cr.commit()











