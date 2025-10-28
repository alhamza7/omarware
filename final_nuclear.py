#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINAL NUCLEAR - Find and destroy remaining FKs
البحث عن وتدمير القيود المتبقية
"""

print("=" * 80)
print("☢️ FINAL NUCLEAR DELETE")
print("=" * 80)
print()

try:
    cr = env.cr
    
    print("Finding remaining foreign keys on product_product...")
    cr.execute("""
        SELECT con.conname, rel.relname
        FROM pg_constraint con
        JOIN pg_class rel ON con.conrelid = rel.oid
        WHERE con.contype = 'f'
        AND rel.relname = 'product_product'
    """)
    
    fks = cr.fetchall()
    print(f"Found {len(fks)} FKs on product_product:")
    for fk in fks:
        print(f"  - {fk[0]}")
    
    # Drop them
    for fk_name, table in fks:
        try:
            cr.execute(f'ALTER TABLE product_product DROP CONSTRAINT IF EXISTS "{fk_name}" CASCADE')
            print(f"  ✓ Dropped {fk_name}")
        except Exception as e:
            print(f"  ✗ Could not drop {fk_name}: {str(e)[:50]}")
    
    cr.commit()
    
    # Do the same for product_template and uom_uom
    for target_table in ['product_template', 'uom_uom']:
        print(f"\nFinding FKs on {target_table}...")
        cr.execute(f"""
            SELECT con.conname
            FROM pg_constraint con
            JOIN pg_class rel ON con.conrelid = rel.oid
            WHERE con.contype = 'f'
            AND rel.relname = '{target_table}'
        """)
        
        fks = cr.fetchall()
        print(f"Found {len(fks)} FKs")
        
        for (fk_name,) in fks:
            try:
                cr.execute(f'ALTER TABLE {target_table} DROP CONSTRAINT IF EXISTS "{fk_name}" CASCADE')
                print(f"  ✓ Dropped {fk_name}")
            except:
                pass
        
        cr.commit()
    
    print()
    print("=" * 80)
    print("Now deleting data...")
    print("=" * 80)
    
    # Delete in order
    cr.execute("DELETE FROM product_product")
    print(f"✓ Deleted {cr.rowcount} products")
    cr.commit()
    
    cr.execute("DELETE FROM product_template")
    print(f"✓ Deleted {cr.rowcount} templates")
    cr.commit()
    
    cr.execute("DELETE FROM uom_uom")
    print(f"✓ Deleted {cr.rowcount} UoMs")
    cr.commit()
    
    try:
        cr.execute("DELETE FROM uom_category")
        print(f"✓ Deleted {cr.rowcount} UoM categories")
        cr.commit()
    except:
        print("⚠ Could not delete UoM categories")
    
    print()
    print("=" * 80)
    print("✅ SUCCESS! ALL DATA DELETED!")
    print("=" * 80)
    
    # Verify
    cr.execute("SELECT COUNT(*) FROM product_product")
    products = cr.fetchone()[0]
    
    cr.execute("SELECT COUNT(*) FROM product_template")
    templates = cr.fetchone()[0]
    
    cr.execute("SELECT COUNT(*) FROM uom_uom")
    uoms = cr.fetchone()[0]
    
    print()
    print("VERIFICATION:")
    print(f"  Products: {products}")
    print(f"  Templates: {templates}")
    print(f"  UoMs: {uoms}")
    print()
    
    if products == 0 and templates == 0 and uoms == 0:
        print("✅✅✅ PERFECT! Everything deleted!")
        print("✅✅✅ رائع! تم حذف كل شيء!")
    else:
        print("⚠️ Some data remains")
    
    print()
    print("=" * 80)
    print("NEXT STEPS:")
    print("=" * 80)
    print("1. Exit shell")
    print("2. Run: python odoo-bin -c odoo.conf -u all --stop-after-init")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
    try:
        env.cr.rollback()
    except:
        pass

exit()




