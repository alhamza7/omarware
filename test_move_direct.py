#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct test via Odoo shell for folder move
"""

import sys
import os

# Add Odoo to path
sys.path.insert(0, '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai')

import odoo
from odoo.api import Environment

# Initialize Odoo
odoo.tools.config.parse_config(['--config=/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/odoo_local.conf'])

def test_move():
    """Test document move between folders"""
    
    print("=" * 70)
    print("DIRECT TEST: Document Move Between Folders")
    print("=" * 70)
    
    # Connect to database
    db_name = 'lugal_local'
    
    with Environment.manage():
        registry = odoo.registry(db_name)
        with registry.cursor() as cr:
            env = Environment(cr, odoo.SUPERUSER_ID, {})
            
            # 1. Get department and doc type
            print("\n1. Getting test data...")
            dept = env['nbs.department'].search([], limit=1)
            if not dept:
                print("❌ No department found")
                return False
            print(f"✓ Department: {dept.name} (ID: {dept.id})")
            
            doc_type = env['nbs.document.type'].search([('department_id', '=', dept.id)], limit=1)
            if not doc_type:
                print("❌ No document type found")
                return False
            print(f"✓ Document Type: {doc_type.name} (ID: {doc_type.id})")
            
            # 2. Create test folders
            print("\n2. Creating test folders...")
            
            source_folder = env['nbs.document.folder'].create({
                'name': 'TEST SOURCE FOLDER',
                'code': 'TST_SRC',
                'department_id': dept.id,
            })
            print(f"✓ Source Folder created: ID {source_folder.id}")
            
            target_folder = env['nbs.document.folder'].create({
                'name': 'TEST TARGET FOLDER',
                'code': 'TST_TGT',
                'department_id': dept.id,
            })
            print(f"✓ Target Folder created: ID {target_folder.id}")
            
            # 3. Create test document in source folder
            print("\n3. Creating test document...")
            
            doc = env['nbs.document'].create({
                'name': 'TEST MOVE DOCUMENT',
                'department_id': dept.id,
                'document_type_id': doc_type.id,
                'folder_id': source_folder.id,
                'state': 'active',
                'is_locked': False,
            })
            print(f"✓ Document created: ID {doc.id}")
            
            # Link to source folder Many2many
            doc.write({'folder_ids': [(4, source_folder.id)]})
            print(f"✓ Linked to source folder via folder_ids")
            
            # Commit to save
            cr.commit()
            
            # 4. Verify before move
            print("\n4. Verifying BEFORE move...")
            doc_before = env['nbs.document'].browse(doc.id)
            print(f"   folder_id: {doc_before.folder_id.id if doc_before.folder_id else None}")
            print(f"   folder_ids: {doc_before.folder_ids.ids}")
            
            source_docs_before = env['nbs.document'].search([('folder_id', '=', source_folder.id)])
            print(f"   Source folder contains: {source_docs_before.ids}")
            
            target_docs_before = env['nbs.document'].search([('folder_id', '=', target_folder.id)])
            print(f"   Target folder contains: {target_docs_before.ids}")
            
            # 5. MOVE document
            print(f"\n5. MOVING document {doc.id} from folder {source_folder.id} to {target_folder.id}...")
            
            doc.write({
                'folder_id': target_folder.id,
                'folder_ids': [(3, source_folder.id), (4, target_folder.id)]
            })
            
            cr.commit()
            print("✓ Move command executed")
            
            # 6. Verify after move
            print("\n6. Verifying AFTER move...")
            doc_after = env['nbs.document'].browse(doc.id)
            print(f"   folder_id: {doc_after.folder_id.id if doc_after.folder_id else None}")
            print(f"   folder_ids: {doc_after.folder_ids.ids}")
            
            source_docs_after = env['nbs.document'].search([('folder_id', '=', source_folder.id)])
            print(f"   Source folder contains: {source_docs_after.ids}")
            
            target_docs_after = env['nbs.document'].search([('folder_id', '=', target_folder.id)])
            print(f"   Target folder contains: {target_docs_after.ids}")
            
            # 7. Check results
            print("\n7. Test Results:")
            
            success = True
            
            # Check folder_id
            if doc_after.folder_id.id == target_folder.id:
                print("   ✅ folder_id updated to target")
            else:
                print(f"   ❌ folder_id NOT updated (expected {target_folder.id}, got {doc_after.folder_id.id if doc_after.folder_id else None})")
                success = False
            
            # Check in target folder_ids
            if target_folder.id in doc_after.folder_ids.ids:
                print("   ✅ Document in target folder_ids")
            else:
                print(f"   ❌ Document NOT in target folder_ids")
                success = False
            
            # Check NOT in source folder_ids
            if source_folder.id not in doc_after.folder_ids.ids:
                print("   ✅ Document removed from source folder_ids")
            else:
                print(f"   ❌ Document STILL in source folder_ids")
                success = False
            
            # Check source folder search
            if doc.id not in source_docs_after.ids:
                print("   ✅ Document NOT in source folder search results")
            else:
                print(f"   ❌ Document STILL appears in source folder")
                success = False
            
            # Check target folder search
            if doc.id in target_docs_after.ids:
                print("   ✅ Document appears in target folder search results")
            else:
                print(f"   ❌ Document NOT in target folder search results")
                success = False
            
            # 8. Cleanup
            print("\n8. Cleanup...")
            doc.write({'state': 'trash', 'is_deleted': True})
            source_folder.unlink()
            target_folder.unlink()
            cr.commit()
            print("✓ Test data cleaned up")
            
            if success:
                print("\n" + "=" * 70)
                print("✅ ALL TESTS PASSED - Document move works correctly!")
                print("=" * 70)
            else:
                print("\n" + "=" * 70)
                print("❌ TESTS FAILED - Document move has issues")
                print("=" * 70)
            
            return success

if __name__ == '__main__':
    try:
        success = test_move()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
