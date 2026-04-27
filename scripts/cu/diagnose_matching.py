
# Run: python odoo-bin shell -c odoo.conf -d lugal

backend = env['sap.backend'].browse(2)
connection = backend.get_connection()

# Get one group with details
response = connection.get('UnitOfMeasurementGroups(2)', {})
defs = response.get('UoMGroupDefinitionCollection', [])

print("Group 2 has %%d definitions" %% len(defs))
print()

# Show what AlternateUoM values we get
print("AlternateUoM entries in Group 2:")
for d in defs:
    alt_uom = d.get('AlternateUoM')
    base_qty = d.get('BaseQuantity')
    alt_qty = d.get('AlternateQuantity')
    factor = base_qty / alt_qty if alt_qty != 0 else 1.0
    print(f"   AlternateUoM: {alt_uom}, Factor: {factor:.4f} ({alt_qty} = {base_qty} base)")

print()
print("Now checking if these entries exist in sap.uom.sync:")
for d in defs:
    alt_uom = d.get('AlternateUoM')
    sync = env['sap.uom.sync'].search([
        ('sap_uom_entry', '=', alt_uom),
        ('backend_id', '=', 2)
    ])
    
    if sync:
        print(f"   ✓ Entry {alt_uom}: FOUND -> {sync.sap_uom_id}")
    else:
        print(f"   ✗ Entry {alt_uom}: NOT FOUND in sap.uom.sync")
