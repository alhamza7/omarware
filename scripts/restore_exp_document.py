#!/usr/bin/env python3
"""
Restore permanently deleted document EXP25.04.04565 (ID 78)
This script recreates the database records and links to existing file in filestore
"""
import psycopg2
import os
from datetime import datetime, timedelta

# Database connection (using peer authentication - no password needed)
conn = psycopg2.connect(
    dbname='lugal_local',
    user='capo7amzah'
    # No host specified = uses Unix socket with peer authentication
)
conn.autocommit = False
cur = conn.cursor()

try:
    print("=" * 60)
    print("DOCUMENT RECOVERY: EXP25.04.04565")
    print("=" * 60)
    print()
    
    # Check if file exists
    file_path = '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf'
    
    if not os.path.exists(file_path):
        print(f"❌ ERROR: File not found at: {file_path}")
        exit(1)
    
    file_size = os.path.getsize(file_path)
    print(f"✓ File found: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print()
    
    # Step 1: Check if department and document type exist
    print("Step 1: Validating department and document type...")
    cur.execute("SELECT id, name FROM nbs_department WHERE id = 5")
    dept = cur.fetchone()
    if dept:
        print(f"  ✓ Department: {dept[1]} (ID: {dept[0]})")
    else:
        print("  ⚠ Department ID 5 not found, using ID 1")
        cur.execute("SELECT id FROM nbs_department LIMIT 1")
        dept_id = cur.fetchone()[0]
    
    cur.execute("SELECT id, name FROM nbs_document_type WHERE id = 3")
    doc_type = cur.fetchone()
    if doc_type:
        print(f"  ✓ Document Type: {doc_type[1]} (ID: {doc_type[0]})")
    else:
        print("  ⚠ Document Type ID 3 not found, using ID 1")
        cur.execute("SELECT id FROM nbs_document_type LIMIT 1")
        doc_type_id = cur.fetchone()[0]
    
    print()
    
    # Step 2: Generate new barcode
    print("Step 2: Generating barcode...")
    cur.execute("SELECT MAX(id) FROM nbs_document")
    max_id = cur.fetchone()[0] or 0
    barcode = f"NBSRECOVERED{str(max_id + 1).zfill(6)}"
    print(f"  ✓ Barcode: {barcode}")
    print()
    
    # Step 3: Insert document record
    print("Step 3: Creating document record...")
    cur.execute("""
        INSERT INTO nbs_document (
            name, department_id, document_type_id, barcode,
            state, is_locked, uploader_id, upload_date,
            confidentiality_level, is_deleted, folder_role
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        'EXP25.04.04565',  # name
        5,  # department_id (Supply Chain)
        3,  # document_type_id (Shipment)
        barcode,  # barcode
        'active',  # state
        False,  # is_locked
        2,  # uploader_id (admin)
        datetime.now(),  # upload_date
        'internal',  # confidentiality_level
        False,  # is_deleted
        'main'  # folder_role
    ))
    
    new_doc_id = cur.fetchone()[0]
    print(f"  ✓ Document created with ID: {new_doc_id}")
    print()
    
    # Step 4: Create version record pointing to existing file
    print("Step 4: Creating version record...")
    # Use relative path from filestore root
    relative_file_path = 'nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf'
    
    cur.execute("""
        INSERT INTO nbs_document_version (
            document_id, version_number, file_name, file_size,
            file_path, uploader_id, upload_date, notes
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        new_doc_id,  # document_id
        1,  # version_number
        'EXP25.04.04565.pdf',  # file_name
        file_size,  # file_size
        relative_file_path,  # file_path (points to existing file)
        2,  # uploader_id
        datetime.now(),  # upload_date
        'Recovered from filestore after permanent deletion on 2026-02-15'  # notes
    ))
    
    version_id = cur.fetchone()[0]
    print(f"  ✓ Version created with ID: {version_id}")
    print()
    
    # Step 5: Link version to document
    print("Step 5: Linking version to document...")
    cur.execute("""
        UPDATE nbs_document 
        SET current_version_id = %s
        WHERE id = %s
    """, (version_id, new_doc_id))
    print(f"  ✓ Document {new_doc_id} now points to version {version_id}")
    print()
    
    # Step 6: Optionally recreate folder
    print("Step 6: Recreating folder...")
    cur.execute("""
        INSERT INTO nbs_document_folder (
            name, code, department_id, description,
            active, owner_id, created_by
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s
        ) RETURNING id
    """, (
        'SC-SHIP-EXP25.04.04565',  # name
        'EXP25.04.04565',  # code
        5,  # department_id
        'Recovered folder for EXP25.04.04565',  # description
        True,  # active
        2,  # owner_id
        2   # created_by
    ))
    
    folder_id = cur.fetchone()[0]
    print(f"  ✓ Folder created with ID: {folder_id}")
    print()
    
    # Step 7: Link document to folder
    print("Step 7: Linking document to folder...")
    cur.execute("""
        UPDATE nbs_document
        SET folder_id = %s
        WHERE id = %s
    """, (folder_id, new_doc_id))
    
    cur.execute("""
        INSERT INTO folder_document_rel (folder_id, document_id)
        VALUES (%s, %s)
    """, (folder_id, new_doc_id))
    
    print(f"  ✓ Document {new_doc_id} linked to folder {folder_id}")
    print()
    
    # Step 8: Create audit log entry
    print("Step 8: Creating audit log...")
    cur.execute("""
        INSERT INTO nbs_audit_log (
            timestamp, user_id, action, document_id, department_id, metadata
        ) VALUES (
            %s, %s, %s, %s, %s, %s
        )
    """, (
        datetime.now(),
        2,  # admin user
        'upload',
        new_doc_id,
        5,
        f'Document recovered from filestore. Original ID: 78, Deleted: 2026-02-15, Recovered: {datetime.now()}'
    ))
    print(f"  ✓ Audit log created")
    print()
    
    # Commit all changes
    conn.commit()
    
    print("=" * 60)
    print("✓ RECOVERY SUCCESSFUL!")
    print("=" * 60)
    print()
    print("Document Details:")
    print(f"  Document ID: {new_doc_id}")
    print(f"  Title: EXP25.04.04565")
    print(f"  Barcode: {barcode}")
    print(f"  Folder ID: {folder_id}")
    print(f"  Folder Name: SC-SHIP-EXP25.04.04565")
    print(f"  File Size: {file_size / 1024 / 1024:.2f} MB")
    print()
    print("The document is now accessible via:")
    print(f"  - GET /api/documents/{new_doc_id}")
    print(f"  - GET /api/documents/{new_doc_id}/download")
    print(f"  - GET /api/folders/{folder_id}/documents")
    print()
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    exit(1)
finally:
    cur.close()
    conn.close()
