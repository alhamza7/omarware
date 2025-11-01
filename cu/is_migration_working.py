import time

wizard = env['sap.product.complete.migration'].browse(6)

print("Checking if migration is working...")
print("=" * 60)

extended_before = env['sap.product.extended'].search_count([])
print(f"Extended Info now: {extended_before}")
print("Waiting 30 seconds...")
time.sleep(30)

# Refresh
extended_after = env['sap.product.extended'].search_count([])
print(f"Extended Info after 30s: {extended_after}")

if extended_after > extended_before:
    print(f"\n✅ MIGRATION IS WORKING!")
    print(f"   Created {extended_after - extended_before} records in 30 seconds")
    print(f"   Estimated rate: {(extended_after - extended_before) * 2} records/minute")
else:
    print(f"\n⚠ MIGRATION MAY HAVE STOPPED")
    print(f"   No new records in 30 seconds")
    
    # Check wizard state
    wizard.invalidate_recordset()
    wizard = env['sap.product.complete.migration'].browse(6)
    print(f"   Wizard State: {wizard.state}")

print("=" * 60)
env.cr.commit()











