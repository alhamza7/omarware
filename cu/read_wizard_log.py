wizard = env['sap.product.complete.migration'].browse(6)

print("WIZARD STATUS:")
print("ID:", wizard.id)
print("State:", wizard.state)
print("Start:", wizard.start_time)
print("Products:", wizard.total_products)
print("UoM Groups:", wizard.total_uom_groups)
print("Errors:", wizard.errors_count)
print("")

if wizard.migration_log:
    lines = wizard.migration_log.split('\n')
    print(f"Log has {len(lines)} lines")
    print("")
    print("LAST 30 LINES:")
    print("=" * 60)
    for line in lines[-30:]:
        # Remove emojis for Windows console
        clean_line = line.encode('ascii', 'ignore').decode('ascii')
        if clean_line.strip():
            print(clean_line)

print("")
print("=" * 60)

env.cr.commit()











