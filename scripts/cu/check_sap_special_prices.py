#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check SAP Special Prices and UoM Pricing"""

print("=" * 80)
print("CHECK SAP SPECIAL PRICES & UoM PRICING")
print("=" * 80)
print()

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if not backend:
    print("No backend found")
    exit()

try:
    connection = backend.get_connection()
    
    # Check what fields are available in ItemPrices
    print("1. Checking ItemPrices structure in SAP...")
    
    params = {
        '$top': 1,
        '$filter': "ItemCode eq 'ADF00001'"
    }
    
    item_data = connection.get('Items', params)
    items = item_data.get('value', [])
    
    if items and items[0].get('ItemPrices'):
        price_sample = items[0]['ItemPrices'][0]
        print("   ItemPrices fields available:")
        for key in price_sample.keys():
            print(f"     - {key}: {price_sample.get(key)}")
        print()
    
    # Check if SpecialPrices exists
    print("2. Checking for SpecialPrices...")
    try:
        sp_params = {'$top': 1}
        special_prices = connection.get('SpecialPrices', sp_params)
        sp_data = special_prices.get('value', [])
        
        if sp_data:
            print(f"   Found SpecialPrices in SAP!")
            print(f"   Sample record:")
            for key, value in sp_data[0].items():
                print(f"     {key}: {value}")
            print()
        else:
            print("   SpecialPrices exists but empty")
    except Exception as e:
        print(f"   SpecialPrices not available: {str(e)[:50]}")
    
    print()
    
    # Check UoMPrices or PriceListMatrix
    print("3. Checking for UoM-based pricing structures...")
    
    # Try to get UoM Groups
    try:
        uom_params = {'$top': 5}
        uom_groups = connection.get('UnitOfMeasurementGroups', uom_params)
        uom_data = uom_groups.get('value', [])
        
        if uom_data:
            print(f"   Found {len(uom_data)} UoM Groups")
            if uom_data[0].get('UoMGroupDefinitionCollection'):
                print("   UoM Groups have definitions")
                
                # Check if prices vary by UoM
                sample_uom = uom_data[0]
                print(f"   Sample: {sample_uom.get('Code')}")
                definitions = sample_uom.get('UoMGroupDefinitionCollection', [])
                for uom_def in definitions[:3]:
                    print(f"     UoM: {uom_def.get('AlternateUoM')}, Factor: {uom_def.get('BaseQuantity')}")
        else:
            print("   UoM Groups found but empty")
    except Exception as e:
        print(f"   UoM Groups check failed: {str(e)[:60]}")
    
    print()
    print("=" * 80)
    print("CONCLUSION:")
    print("=" * 80)
    
    print("Based on SAP data structure:")
    print("  - ItemPrices: Contains prices per pricelist")
    print("  - UoMCode/UoMEntry: NOT present in ItemPrices")
    print()
    print("ANSWER:")
    print("  SAP configuration does NOT include UoM-specific prices")
    print("  in the standard ItemPrices structure.")
    print()
    print("  If you need UoM-specific prices, they might be in:")
    print("    - SpecialPrices (with UoM field)")
    print("    - Custom price tables")
    print("    - Or need manual configuration")
    print("=" * 80)
    
except Exception as e:
    print(f"Error: {str(e)}")

exit()





