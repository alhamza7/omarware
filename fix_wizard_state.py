from datetime import timedelta

print("FIXING WIZARD STATE")
print("=" * 60)

wizard = env['sap.product.complete.migration'].browse(6)

print(f"Current State: {wizard.state}")
print(f"Products: {wizard.total_products}")

if wizard.start_time:
    end_time = wizard.start_time + timedelta(minutes=8)
else:
    from datetime import datetime
    end_time = datetime.now()

# Update to done
wizard.write({
    'state': 'done',
    'end_time': end_time,
})

env.cr.commit()

print(f"New State: {wizard.state}")
print(f"End Time: {wizard.end_time}")
print("Wizard state fixed!")
print("=" * 60)

