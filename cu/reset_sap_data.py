#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reset SAP Data - Clear all imported data"""

print("=" * 80)
print("RESET SAP DATA - Clearing all imported data")
print("=" * 80)

backend = env['sap.backend'].search([('active', '=', True)], limit=1)

if backend:
    print(f"\nBackend: {backend.name}")
    print("\nThis will DELETE:")
    print("  - All SAP imported products")
    print("  - All SAP Extended Info")
    print("  - All SAP UoM Sync records")
    print("  - All SAP Pricelist Sync records")
    print("  - All SAP Warehouse Info records")
    print("  - All SAP Migration wizards")
    print("  - Stock quantities for SAP products")
    
    print("\n" + "=" * 80)
    print("COUNTING RECORDS TO DELETE")
    print("=" * 80)
    
    # Count what will be deleted
    products_to_delete = env['product.product'].with_context(active_test=False).search([
        ('default_code', '!=', False),
        ('create_date', '>=', '2025-10-22 00:00:00')
    ])
    
    extended_to_delete = env['sap.product.extended'].search([
        ('backend_id', '=', backend.id)
    ])
    
    uom_sync_to_delete = env['sap.uom.sync'].search([
        ('backend_id', '=', backend.id)
    ])
    
    pricelist_sync_to_delete = env['sap.product.pricelist.sync'].search([
        ('backend_id', '=', backend.id)
    ])
    
    warehouse_info_to_delete = env['sap.product.warehouse.info'].search([
        ('backend_id', '=', backend.id)
    ])
    
    migration_wizards = env['sap.product.complete.migration'].search([])
    
    # Stock quants for SAP products
    product_ids = products_to_delete.ids
    quants_to_delete = env['stock.quant'].search([
        ('product_id', 'in', product_ids)
    ])
    
    print(f"\n  Products: {len(products_to_delete)}")
    print(f"  Extended Info: {len(extended_to_delete)}")
    print(f"  UoM Sync: {len(uom_sync_to_delete)}")
    print(f"  Pricelist Sync: {len(pricelist_sync_to_delete)}")
    print(f"  Warehouse Info: {len(warehouse_info_to_delete)}")
    print(f"  Migration Wizards: {len(migration_wizards)}")
    print(f"  Stock Quants: {len(quants_to_delete)}")
    
    print("\n" + "=" * 80)
    print("DELETING RECORDS")
    print("=" * 80)
    
    # Delete in correct order (to avoid constraint errors)
    
    # 1. Delete Extended Info first (depends on products)
    if extended_to_delete:
        print(f"\n1. Deleting {len(extended_to_delete)} Extended Info records...")
        extended_to_delete.unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 2. Delete Warehouse Info
    if warehouse_info_to_delete:
        print(f"\n2. Deleting {len(warehouse_info_to_delete)} Warehouse Info records...")
        warehouse_info_to_delete.unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 3. Delete Pricelist Sync
    if pricelist_sync_to_delete:
        print(f"\n3. Deleting {len(pricelist_sync_to_delete)} Pricelist Sync records...")
        pricelist_sync_to_delete.unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 4. Delete Stock Quants
    if quants_to_delete:
        print(f"\n4. Deleting {len(quants_to_delete)} Stock Quants...")
        quants_to_delete.sudo().unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 5. Delete Products
    if products_to_delete:
        print(f"\n5. Deleting {len(products_to_delete)} Products...")
        # Delete with sudo to bypass constraints
        products_to_delete.sudo().unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 6. Delete UoM Sync
    if uom_sync_to_delete:
        print(f"\n6. Deleting {len(uom_sync_to_delete)} UoM Sync records...")
        uom_sync_to_delete.unlink()
        env.cr.commit()
        print(f"   DONE")
    
    # 7. Delete Migration Wizards
    if migration_wizards:
        print(f"\n7. Deleting {len(migration_wizards)} Migration Wizards...")
        migration_wizards.unlink()
        env.cr.commit()
        print(f"   DONE")
    
    print("\n" + "=" * 80)
    print("RESET COMPLETE!")
    print("=" * 80)
    
    # Verify
    print("\nVerifying deletion:")
    products_remain = env['product.product'].search([('default_code', '!=', False)])
    extended_remain = env['sap.product.extended'].search([])
    uom_sync_remain = env['sap.uom.sync'].search([])
    
    print(f"  Products with code: {len(products_remain)}")
    print(f"  Extended Info: {len(extended_remain)}")
    print(f"  UoM Sync: {len(uom_sync_remain)}")
    
    print("\n" + "=" * 80)
    print("READY FOR FRESH MIGRATION!")
    print("=" * 80)

env.cr.commit()




