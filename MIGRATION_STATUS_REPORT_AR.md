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
            '$expand': 'ItemPrices,ItemWarehouseInfoCollection,ItemUnitOfMeasurementPackages'
        }
        
        result = connection.get('Items', params)
        
        if result.get('value'):
            item = result['value'][0]
            print(f"\nItem found: {item.get('ItemName', 'N/A')}")
            
            # Check what's available
            has_foreign = 'ForeignName' in item and item['ForeignName']
            has_manufacturer = 'Manufacturer' in item and item['Manufacturer']
            has_dimensions = 'Length1' in item and item['Length1']
            has_prices = 'ItemPrices' in item and len(item.get('ItemPrices', [])) > 0
            has_warehouse = 'ItemWarehouseInfoCollection' in item and len(item.get('ItemWarehouseInfoCollection', [])) > 0
            has_uom_packages = 'ItemUnitOfMeasurementPackages' in item and len(item.get('ItemUnitOfMeasurementPackages', [])) > 0
            
            print(f"\nAvailable Data:")
            print(f"  ForeignName: {'YES' if has_foreign else 'NO'}")
            print(f"  Manufacturer: {'YES' if has_manufacturer else 'NO'}")
            print(f"  Dimensions: {'YES' if has_dimensions else 'NO'}")
            print(f"  ItemPrices: {'YES - ' + str(len(item.get('ItemPrices', []))) + ' prices' if has_prices else 'NO'}")
            print(f"  WarehouseInfo: {'YES - ' + str(len(item.get('ItemWarehouseInfoCollection', []))) + ' warehouses' if has_warehouse else 'NO'}")
            print(f"  UoM Packages: {'YES' if has_uom_packages else 'NO'}")
            
            # Show sample price if available
            if has_prices:
                print(f"\n  Sample Prices:")
                for price in item.get('ItemPrices', [])[:3]:
                    plist = price.get('PriceList', 'N/A')
                    amount = price.get('Price', 0)
                    curr = price.get('Currency', 'N/A')
                    print(f"    List {plist}: {amount} {curr}")
            
            # Show sample warehouse if available
            if has_warehouse:
                print(f"\n  Sample Warehouse:")
                for wh in item.get('ItemWarehouseInfoCollection', [])[:2]:
                    code = wh.get('WarehouseCode', 'N/A')
                    instock = wh.get('InStock', 0)
                    print(f"    {code}: {instock} in stock")
            
            # Show fields list
            print(f"\n  Total fields in SAP Item: {len(item.keys())}")
            print(f"  Field names: {', '.join(list(item.keys())[:20])}...")
        else:
            print("Item not found!")
    
    # Test 2: Check if PriceLists exist separately
    print("\n" + "-" * 80)
    print("Test 2: Checking SAP PriceLists...")
    print("-" * 80)
    
    try:
        pricelists_data = connection.get('PriceLists', {'$top': 5})
        pl_count = len(pricelists_data.get('value', []))
        print(f"SAP PriceLists found: {pl_count}")
        
        if pl_count > 0:
            print("\nAvailable PriceLists:")
            for pl in pricelists_data['value']:
                print(f"  - {pl.get('PriceListNo')}: {pl.get('PriceListName', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Check Warehouses
    print("\n" + "-" * 80)
    print("Test 3: Checking SAP Warehouses...")
    print("-" * 80)
    
    try:
        warehouses_data = connection.get('Warehouses', {'$top': 5})
        wh_count = len(warehouses_data.get('value', []))
        print(f"SAP Warehouses found: {wh_count}")
        
        if wh_count > 0:
            print("\nAvailable Warehouses:")
            for wh in warehouses_data['value']:
                print(f"  - {wh.get('WarehouseCode')}: {wh.get('WarehouseName', 'N/A')}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
    
    connection.close_session()

env.cr.commit()









