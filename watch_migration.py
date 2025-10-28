#!/usr/bin/env python3
"""Watch Migration Progress - Real-time monitoring"""

import time

wizard = env['sap.product.complete.migration'].search([], order='id desc', limit=1)

if not wizard:
    print("No wizard found - Create one first!")
else:
    print("=" * 80)
    print(f"WATCHING MIGRATION - Wizard ID: {wizard.id}")
    print("=" * 80)
    print("")
    
    last_products = 0
    last_state = ''
    last_log_length = 0
    
    for i in range(120):  # Watch for 20 minutes max (120 * 10s)
        try:
            # Refresh wizard data
            wizard.invalidate_recordset()
            wizard = env['sap.product.complete.migration'].browse(wizard.id)
            
            # Show progress if changed
            if wizard.total_products != last_products or wizard.state != last_state:
                elapsed = i * 10
                print(f"[{elapsed}s] State: {wizard.state} | Products: {wizard.total_products} | Errors: {wizard.errors_count}")
                last_products = wizard.total_products
                last_state = wizard.state
            
            # Show new log entries
            if wizard.migration_log:
                current_log_length = len(wizard.migration_log)
                if current_log_length > last_log_length:
                    # Get new lines
                    new_log = wizard.migration_log[last_log_length:]
                    if new_log.strip():
                        for line in new_log.split('\n')[-5:]:  # Last 5 lines
                            if line.strip() and ('Progress' in line or 'Batch' in line or 'Complete' in line):
                                print(f"  {line.strip()}")
                    last_log_length = current_log_length
            
            # Check if done
            if wizard.state == 'done':
                print("\n" + "=" * 80)
                print("MIGRATION COMPLETE!")
                print("=" * 80)
                print(f"Duration: {wizard.duration_seconds}s")
                print(f"UoM Groups: {wizard.total_uom_groups}")
                print(f"Products: {wizard.total_products}")
                print(f"Pricelists: {wizard.total_pricelists}")
                print(f"Prices: {wizard.total_prices}")
                print(f"Warehouses: {wizard.total_warehouses}")
                print(f"Errors: {wizard.errors_count}")
                
                # Verify in database
                extended = env['sap.product.extended'].search_count([])
                prices = env['sap.product.pricelist.sync'].search_count([])
                wh = env['sap.product.warehouse.info'].search_count([])
                
                print(f"\nDatabase Verification:")
                print(f"  Extended Info: {extended}")
                print(f"  Prices: {prices}")
                print(f"  Warehouse Info: {wh}")
                
                break
            elif wizard.state == 'error':
                print("\n" + "=" * 80)
                print("MIGRATION FAILED!")
                print("=" * 80)
                print("Last log entries:")
                if wizard.migration_log:
                    for line in wizard.migration_log.split('\n')[-20:]:
                        print(line)
                break
            
            time.sleep(10)  # Check every 10 seconds
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
            break
        except Exception as e:
            print(f"Error monitoring: {e}")
            time.sleep(10)

env.cr.commit()









