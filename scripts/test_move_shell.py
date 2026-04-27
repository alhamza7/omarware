#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run this via: ./venv/bin/python odoo-bin shell -c odoo_local.conf -d lugal_local --shell-interface=python < test_move_shell.py"""

print("=" * 70)
print("SHELL TEST: Document Move Between Folders")
print("=" * 70)

# 1. Get test data
print("\n1. Getting test data...")
dept = env['nbs.department'].search([], limit=1)
print(f"✓ Department: {dept.name} (ID: {dept.id})")

doc_type = env['nbs.document.type'].search([('department_id', '=', dept.id)], limit=1)
print(f"✓ Document Type: {doc_type.name} (ID: {doc_type.id})")

# 2. Create folders
print("\n2. Creating test folders...")

source = env['nbs.document.folder'].sudo().create({
    'name': 'TEST_SOURCE_MOVE',
    'code': 'TST_SRC_MV',
    'department_id': dept.id,
})
print(f"✓ Source: {source.id}")

target = env['nbs.document.folder'].sudo().create({
    'name': 'TEST_TARGET_MOVE',
    'code': 'TST_TGT_MV',
    'department_id': dept.id,
})
print(f"✓ Target: {target.id}")

# 3. Create document
print("\n3. Creating document in source...")

doc = env['nbs.document'].sudo().create({
    'name': 'TEST_MOVE_DOC',
    'department_id': dept.id,
    'document_type_id': doc_type.id,
    'folder_id': source.id,
    'state': 'active',
})
doc.write({'folder_ids': [(4, source.id)]})
env.cr.commit()

print(f"✓ Document: {doc.id}")
print(f"   folder_id: {doc.folder_id.id if doc.folder_id else None}")
print(f"   folder_ids: {doc.folder_ids.ids}")

# 4. Verify in source
src_docs = env['nbs.document'].search([('folder_id', '=', source.id)])
tgt_docs = env['nbs.document'].search([('folder_id', '=', target.id)])
print(f"   Source has: {src_docs.ids}")
print(f"   Target has: {tgt_docs.ids}")

# 5. MOVE
print(f"\n4. MOVING doc {doc.id} from {source.id} to {target.id}...")

doc.write({
    'folder_id': target.id,
    'folder_ids': [(3, source.id), (4, target.id)]
})
env.cr.commit()

print("✓ Move executed")

# 6. Verify AFTER
print("\n5. Verifying AFTER move...")
doc.invalidate_recordset()
print(f"   folder_id: {doc.folder_id.id if doc.folder_id else None}")
print(f"   folder_ids: {doc.folder_ids.ids}")

src_after = env['nbs.document'].search([('folder_id', '=', source.id)])
tgt_after = env['nbs.document'].search([('folder_id', '=', target.id)])
print(f"   Source has: {src_after.ids}")
print(f"   Target has: {tgt_after.ids}")

# 7. Results
print("\n6. Results:")

if doc.folder_id.id == target.id:
    print("   ✅ folder_id = target")
else:
    print(f"   ❌ folder_id wrong: {doc.folder_id.id if doc.folder_id else None}")

if target.id in doc.folder_ids.ids:
    print("   ✅ In target folder_ids")
else:
    print(f"   ❌ NOT in target folder_ids: {doc.folder_ids.ids}")

if source.id not in doc.folder_ids.ids:
    print("   ✅ Removed from source folder_ids")
else:
    print(f"   ❌ STILL in source folder_ids")

if doc.id not in src_after.ids:
    print("   ✅ NOT in source search")
else:
    print(f"   ❌ STILL in source search")

if doc.id in tgt_after.ids:
    print("   ✅ IN target search")
else:
    print(f"   ❌ NOT in target search")

# 8. Cleanup
print("\n7. Cleanup...")
doc.write({'state': 'trash', 'is_deleted': True})
source.unlink()
target.unlink()
env.cr.commit()
print("✓ Done")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
