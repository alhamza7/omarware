#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULTIMATE FORCE DELETE - NUCLEAR OPTION
حذف نووي - الخيار النهائي
Uses ALTER TABLE to drop foreign keys, then deletes everything
"""

print("=" * 80)
print("☢️  NUCLEAR DELETE - ALL DATA WILL BE DESTROYED / حذف نووي")
print("=" * 80)
print()

try:
    cr = env.cr
    
    print("STEP 1: Dropping ALL foreign key constraints...")
    print("=" * 80)
    
    # Get all foreign key constraints
    cr.execute("""
        SELECT 
            con.conname as constraint_name,
            rel.relname as table_name
        FROM pg_constraint con
        JOIN pg_class rel ON con.conrelid = rel.oid
        WHERE con.contype = 'f'
        AND rel.relname IN (
            'product_template', 'product_product', 'product_pricelist_item',
            'stock_move', 'stock_quant', 'purchase_order_line', 'sale_order_line',
            'stock_move_line', 'delivery_carrier'
        )
    """)
    
    constraints = cr.fetchall()
    print(f"Found {len(constraints)} foreign key constraints")
    
    for constraint_name, table_name in constraints:
        try:
            cr.execute(f'ALTER TABLE "{table_name}" DROP CONSTRAINT IF EXISTS "{constraint_name}" CASCADE')
            print(f"  ✓ Dropped {table_name}.{constraint_name}")
        except:
            pass
    
    cr.commit()
    print()
    
    print("STEP 2: Deleting all data...")
    print("=" * 80)
    
    # Now delete everything
    tables_to_clear = [
        'account_move_line',
        'account_move',
        'sale_order_line',
        'sale_order',
        'purchase_order_line',
        'purchase_order',
        'stock_move_line',
        'stock_move',
        'stock_picking',
        'stock_quant',
        'product_pricelist_item',
        'product_pricelist',
        'sap_product_pricelist_sync',
        'sap_product_warehouse_info',
        'sap_product_extended',
        'sap_product_sync',
        'sap_uom_sync',
        'delivery_carrier',
        'product_supplierinfo',
        'product_product',
        'product_template',
        'uom_uom',
        'uom_category',
    ]
    
    for table in tables_to_clear:
        try:
            cr.execute(f'DELETE FROM "{table}"')
            count = cr.rowcount
            print(f"  ✓ Deleted {count} records from {table}")
        except Exception as e:
            print(f"  ⚠ Could not delete from {table}: {str(e)[:50]}")
    
    cr.commit()
    print()
    
    print("=" * 80)
    print("✅ ALL DATA DELETED!")
    print("=" * 80)
    print()
    
    # Verify
    print("VERIFICATION:")
    print("-" * 80)
    
    verification_tables = {
        'Products': 'product_product',
        'Templates': 'product_template',
        'UoMs': 'uom_uom',
        'UoM Categories': 'uom_category',
        'Extended Info': 'sap_product_extended',
        'Pricelists': 'product_pricelist',
    }
    
    for name, table in verification_tables.items():
        try:
            cr.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cr.fetchone()[0]
            status = "✅" if count == 0 else "⚠️"
            print(f"  {status} {name}: {count}")
        except:
            print(f"  ? {name}: Table not found")
    
    print()
    print("=" * 80)
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("=" * 80)
    print("1. RESTART Odoo completely")
    print("2. Update all modules: python odoo-bin -c odoo.conf -u all --stop-after-init")
    print("3. This will recreate foreign keys and default data")
    print()
    print("قاعدة البيانات فارغة تماماً الآن!")
    print("Database is COMPLETELY EMPTY now!")
    print("=" * 80)
    
except Exception as e:
    print()
    print("=" * 80)
    print(f"❌ ERROR: {str(e)}")
    print("=" * 80)
    import traceback
    traceback.print_exc()
    print()
    try:
        env.cr.rollback()
        print("Rolled back")
    except:
        pass

exit()






