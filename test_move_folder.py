#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for folder move operations
"""

import xmlrpc.client
import sys

# Configuration
url = 'http://localhost:8070'
db = 'lugal_local'
username = 'admin@example.com'
password = 'admin'

def test_folder_move():
    """Test document move between folders"""
    
    print("=" * 60)
    print("TEST: Document Move Between Folders")
    print("=" * 60)
    
    # Connect
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("❌ Authentication failed")
        return False
    
    print(f"✓ Authenticated as user {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # 1. Get or create test folders
    print("\n1. Setting up test folders...")
    
    # Get department
    dept_ids = models.execute_kw(db, uid, password, 'nbs.department', 'search', [[]], {'limit': 1})
    if not dept_ids:
        print("❌ No department found")
        return False
    dept_id = dept_ids[0]
    print(f"✓ Using department ID: {dept_id}")
    
    # Get document type
    doc_type_ids = models.execute_kw(db, uid, password, 'nbs.document.type', 'search', 
                                     [[('department_id', '=', dept_id)]], {'limit': 1})
    if not doc_type_ids:
        print("❌ No document type found")
        return False
    doc_type_id = doc_type_ids[0]
    print(f"✓ Using document type ID: {doc_type_id}")
    
    # Create source folder
    source_folder_id = models.execute_kw(db, uid, password, 'nbs.document.folder', 'create', [{
        'name': 'Test Source Folder',
        'code': 'TEST_SRC',
        'department_id': dept_id,
    }])
    print(f"✓ Created source folder ID: {source_folder_id}")
    
    # Create target folder
    target_folder_id = models.execute_kw(db, uid, password, 'nbs.document.folder', 'create', [{
        'name': 'Test Target Folder',
        'code': 'TEST_TGT',
        'department_id': dept_id,
    }])
    print(f"✓ Created target folder ID: {target_folder_id}")
    
    # 2. Create test document in source folder
    print("\n2. Creating test document...")
    
    doc_id = models.execute_kw(db, uid, password, 'nbs.document', 'create', [{
        'name': 'Test Move Document',
        'department_id': dept_id,
        'document_type_id': doc_type_id,
        'folder_id': source_folder_id,
        'state': 'active',
    }])
    print(f"✓ Created document ID: {doc_id}")
    
    # Link to folder Many2many
    models.execute_kw(db, uid, password, 'nbs.document', 'write', 
                     [[doc_id], {'folder_ids': [(4, source_folder_id)]}])
    print(f"✓ Linked document {doc_id} to source folder {source_folder_id}")
    
    # 3. Verify document is in source folder
    print("\n3. Verifying document in source folder...")
    
    doc_data = models.execute_kw(db, uid, password, 'nbs.document', 'read', 
                                 [[doc_id], ['folder_id', 'folder_ids']])
    print(f"   Document {doc_id}:")
    print(f"   - folder_id: {doc_data[0]['folder_id']}")
    print(f"   - folder_ids: {doc_data[0]['folder_ids']}")
    
    source_docs = models.execute_kw(db, uid, password, 'nbs.document', 'search', 
                                    [[('folder_id', '=', source_folder_id)]])
    print(f"   Source folder {source_folder_id} has {len(source_docs)} document(s): {source_docs}")
    
    target_docs_before = models.execute_kw(db, uid, password, 'nbs.document', 'search', 
                                          [[('folder_id', '=', target_folder_id)]])
    print(f"   Target folder {target_folder_id} has {len(target_docs_before)} document(s): {target_docs_before}")
    
    # 4. Move document
    print(f"\n4. Moving document {doc_id} from folder {source_folder_id} to {target_folder_id}...")
    
    # Build folder_ids commands
    models.execute_kw(db, uid, password, 'nbs.document', 'write', [[doc_id], {
        'folder_id': target_folder_id,
        'folder_ids': [(3, source_folder_id), (4, target_folder_id)]  # unlink from source, link to target
    }])
    print(f"✓ Move command executed")
    
    # 5. Verify after move
    print("\n5. Verifying after move...")
    
    doc_data_after = models.execute_kw(db, uid, password, 'nbs.document', 'read', 
                                      [[doc_id], ['folder_id', 'folder_ids']])
    print(f"   Document {doc_id} after move:")
    print(f"   - folder_id: {doc_data_after[0]['folder_id']}")
    print(f"   - folder_ids: {doc_data_after[0]['folder_ids']}")
    
    source_docs_after = models.execute_kw(db, uid, password, 'nbs.document', 'search', 
                                         [[('folder_id', '=', source_folder_id)]])
    print(f"   Source folder {source_folder_id} now has {len(source_docs_after)} document(s): {source_docs_after}")
    
    target_docs_after = models.execute_kw(db, uid, password, 'nbs.document', 'search', 
                                         [[('folder_id', '=', target_folder_id)]])
    print(f"   Target folder {target_folder_id} now has {len(target_docs_after)} document(s): {target_docs_after}")
    
    # 6. Verify result
    print("\n6. Test Results:")
    
    if doc_data_after[0]['folder_id'] and doc_data_after[0]['folder_id'][0] == target_folder_id:
        print("   ✅ folder_id updated correctly")
    else:
        print(f"   ❌ folder_id NOT updated (expected {target_folder_id}, got {doc_data_after[0]['folder_id']})")
        return False
    
    if target_folder_id in doc_data_after[0]['folder_ids']:
        print("   ✅ Document in target folder_ids")
    else:
        print(f"   ❌ Document NOT in target folder_ids (got {doc_data_after[0]['folder_ids']})")
        return False
    
    if source_folder_id not in doc_data_after[0]['folder_ids']:
        print("   ✅ Document removed from source folder_ids")
    else:
        print(f"   ❌ Document STILL in source folder_ids")
        return False
    
    if doc_id not in source_docs_after:
        print("   ✅ Document NOT in source folder documents list")
    else:
        print(f"   ❌ Document STILL in source folder")
        return False
    
    if doc_id in target_docs_after:
        print("   ✅ Document in target folder documents list")
    else:
        print(f"   ❌ Document NOT in target folder")
        return False
    
    # 7. Cleanup
    print("\n7. Cleanup...")
    models.execute_kw(db, uid, password, 'nbs.document', 'write', 
                     [[doc_id], {'state': 'trash', 'is_deleted': True}])
    models.execute_kw(db, uid, password, 'nbs.document.folder', 'unlink', [[source_folder_id, target_folder_id]])
    print("✓ Test data cleaned up")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Document move works correctly!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    try:
        success = test_folder_move()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
