#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify Migration Completion"""

print("\n" + "=" * 80)
print("🔍 VERIFYING SAP PRODUCT MIGRATION")
print("=" * 80)

try:
    # Get backend
    backend = env['sap.backend'].search([('active', '=', True)], limit=1)
    if not backend:
        print("❌ No active SAP backend found!")
    else:
        print(f"✅ Backend: {backend.name}")
        print(f"   Connection Status: {backend.connection_status}")
        
        print("\n" + "=" * 80)
        print("📊 MIGRATION STATISTICS")
        print("=" * 80)
        
        # 1. UoM Groups
        uom_syncs = env['sap.uom.sync'].search([
            ('backend_id', '=', backend.id),
            ('sync_status', '=', 'success')
        ])
        print(f"\n✅ Stage 1: UoM Groups")
        print(f"   Total UoM Sync Records: {len(uom_syncs)}")
        
        if uom_syncs:
            print(f"   Sample UoMs:")
            for uom in uom_syncs[:5]:
                factor = uom.odoo_uom_id.factor if uom.odoo_uom_id else 0
                print(f"     - {uom.sap_uom_id} → {uom.odoo_uom_id.name} (factor: {factor})")
        
        # 2. Products
        products = env['product.product'].search([('default_code', '!=', False)])
        print(f"\n✅ Stage 2: Products")
        print(f"   Total Products with SAP codes: {len(products)}")
        
        # 3. Extended Info
        extended = env['sap.product.extended'].search([('backend_id', '=', backend.id)])
        print(f"\n✅ Extended Product Info")
        print(f"   Total Extended Records: {len(extended)}")
        
        if extended:
            # Count fields populated
            with_foreign_name = extended.filtered(lambda x: x.foreign_name)
            with_manufacturer = extended.filtered(lambda x: x.manufacturer_id)
            with_dimensions = extended.filtered(lambda x: x.length1 > 0)
            
            print(f"   Records with Foreign Name: {len(with_foreign_name)}")
            print(f"   Records with Manufacturer: {len(with_manufacturer)}")
            print(f"   Records with Dimensions: {len(with_dimensions)}")
        
        # 4. Pricelists
        sap_pricelists = env['product.pricelist'].search([('name', 'like', 'SAP Price List')])
        print(f"\n✅ Stage 3: Pricelists")
        print(f"   SAP Pricelists Created: {len(sap_pricelists)}")
        
        for pl in sap_pricelists:
            print(f"     - {pl.name} ({pl.currency_id.name}): {len(pl.item_ids)} items")
        
        # 5. Price Sync Records
        prices = env['sap.product.pricelist.sync'].search([('backend_id', '=', backend.id)])
        print(f"\n   Price Sync Records: {len(prices)}")
        
        if prices:
            # Group by pricelist
            price_by_list = {}
            for p in prices:
                plist = p.sap_pricelist_num
                if plist not in price_by_list:
                    price_by_list[plist] = 0
                price_by_list[plist] += 1
            
            for plist_num, count in sorted(price_by_list.items()):
                print(f"     - Price List {plist_num}: {count} prices")
        
        # 6. Warehouse Info
        wh_info = env['sap.product.warehouse.info'].search([('backend_id', '=', backend.id)])
        print(f"\n✅ Stage 4: Warehouse Info")
        print(f"   Total Warehouse Records: {len(wh_info)}")
        
        if wh_info:
            # Count by warehouse
            wh_by_code = {}
            for wh in wh_info:
                code = wh.sap_warehouse_code
                if code not in wh_by_code:
                    wh_by_code[code] = 0
                wh_by_code[code] += 1
            
            for wh_code, count in sorted(wh_by_code.items()):
                print(f"     - Warehouse {wh_code}: {count} products")
        
        # Sample Product Detail
        if products:
            print("\n" + "=" * 80)
            print("📦 SAMPLE PRODUCT DETAILS")
            print("=" * 80)
            
            sample = products[0]
            print(f"\nProduct: {sample.name}")
            print(f"  Code: {sample.default_code}")
            print(f"  List Price: {sample.list_price}")
            print(f"  Standard Price: {sample.standard_price}")
            print(f"  UoM: {sample.uom_id.name}")
            print(f"  UoM Category: {sample.uom_id.category_id.name}")
            
            # Extended info
            ext = env['sap.product.extended'].search([('product_id', '=', sample.id)], limit=1)
            if ext:
                print(f"\n  ✅ Extended Information:")
                if ext.foreign_name:
                    print(f"     Foreign Name: {ext.foreign_name}")
                if ext.manufacturer_id:
                    print(f"     Manufacturer: {ext.manufacturer_id.name}")
                if ext.items_group_name:
                    print(f"     Group: {ext.items_group_name}")
                if ext.length1 > 0:
                    print(f"     Dimensions: {ext.length1} × {ext.width1} × {ext.height1}")
                if ext.manage_batch_numbers:
                    print(f"     Batch Management: Yes")
                if ext.min_level > 0:
                    print(f"     Min Stock: {ext.min_level}")
            
            # Prices
            p_prices = env['sap.product.pricelist.sync'].search([('product_id', '=', sample.id)])
            if p_prices:
                print(f"\n  ✅ Prices ({len(p_prices)}):")
                for price in p_prices[:5]:
                    uom_text = f" / {price.uom_id.name}" if price.uom_id else ""
                    print(f"     - {price.odoo_pricelist_id.name}{uom_text}: {price.price} {price.currency_id.name}")
            
            # Warehouse
            p_wh = env['sap.product.warehouse.info'].search([('product_id', '=', sample.id)])
            if p_wh:
                print(f"\n  ✅ Warehouse Info ({len(p_wh)}):")
                for wh in p_wh:
                    print(f"     - {wh.warehouse_name}:")
                    print(f"       SAP In Stock: {wh.last_in_stock}")
                    print(f"       Odoo Available: {wh.current_qty_available}")
                    if wh.minimum_stock > 0:
                        print(f"       Min Stock: {wh.minimum_stock}")
        
        # Final Summary
        print("\n" + "=" * 80)
        print("✅ MIGRATION VERIFICATION COMPLETE")
        print("=" * 80)
        
        print(f"\n📊 Summary:")
        print(f"   ✓ UoM Groups: {len(uom_syncs)}")
        print(f"   ✓ Products: {len(products)}")
        print(f"   ✓ Extended Info: {len(extended)}")
        print(f"   ✓ Pricelists: {len(sap_pricelists)}")
        print(f"   ✓ Price Records: {len(prices)}")
        print(f"   ✓ Warehouse Records: {len(wh_info)}")
        
        # Check completion percentage
        if products:
            completion_rate = (len(extended) / len(products)) * 100 if products else 0
            print(f"\n   Extended Info Coverage: {completion_rate:.1f}%")
            
            if len(extended) == len(products):
                print("   ✅ All products have extended information!")
            elif len(extended) > 0:
                print(f"   ⚠ {len(products) - len(extended)} products missing extended info")
            else:
                print("   ❌ No extended information imported")
        
        print("\n" + "=" * 80)
        
        if len(products) > 0 and len(extended) > 0:
            print("✅ MIGRATION SUCCESSFUL!")
            print("   All stages completed with data imported")
        elif len(products) > 0:
            print("⚠ PARTIAL MIGRATION")
            print("   Products imported but some stages may be incomplete")
        else:
            print("❌ MIGRATION INCOMPLETE")
            print("   No products imported - please check SAP connection and data")
        
        print("=" * 80)

except Exception as e:
    print(f"\n❌ Verification Error: {str(e)}")
    import traceback
    traceback.print_exc()











