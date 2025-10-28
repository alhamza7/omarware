#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check Final Migration Result"""

print("=" * 80)
print("نتيجة Migration النهائية")
print("=" * 80)

# Get latest wizard
wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)

if wizard:
    print(f"\n✅ State: {wizard.state}")
    print(f"⏱️ Started: {wizard.start_time}")
    print(f"⏱️ Ended: {wizard.end_time}")
    print(f"⏱️ Duration: {wizard.duration_seconds} seconds ({wizard.duration_seconds // 60} minutes)")
    
    print(f"\n📊 Statistics:")
    print(f"   UoM Groups: {wizard.total_uom_groups}")
    print(f"   Products: {wizard.total_products}")
    print(f"   Pricelists: {wizard.total_pricelists}")
    print(f"   Prices: {wizard.total_prices}")
    print(f"   Warehouses: {wizard.total_warehouses}")
    print(f"   Errors: {wizard.errors_count}")
    
    print(f"\n📈 Progress: {wizard.progress_percentage}%")
    print(f"📍 Current Stage: {wizard.current_stage}")
    
    # Count actual records
    print(f"\n🔍 Verification:")
    products = env['product.product'].search([('default_code', '!=', False)])
    print(f"   Products in system: {len(products)}")
    
    extended = env['sap.product.extended'].search([])
    print(f"   Extended Info: {len(extended)}")
    
    uoms = env['sap.uom.sync'].search([])
    print(f"   UoM Syncs: {len(uoms)}")
    
    # Show last 30 lines of log
    if wizard.migration_log:
        print(f"\n📝 Last lines of Migration Log:")
        print("=" * 80)
        lines = wizard.migration_log.split('\n')
        for line in lines[-30:]:
            print(line)

env.cr.commit()





