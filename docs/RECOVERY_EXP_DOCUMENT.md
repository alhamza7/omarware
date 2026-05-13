# 🔄 Document Recovery: EXP25.04.04565

## Date: 2026-02-15

## 🎉 GOOD NEWS: FILE CAN BE RECOVERED!

The PDF file still exists in the filestore even though the database record was permanently deleted.

---

## 📋 EXP Documents Status

### ✅ ACTIVE (Can Access)
**Document ID 73: EXP25.06.06720**
- Barcode: NBSNBS000084
- Status: ACTIVE
- Uploaded: 2026-02-12
- File Location: `filestore_local/.../SC/SHIP/73/v1/EXP25.06.06720.pdf`
- **Action: None needed** ✓

### ✗ PERMANENTLY DELETED (Can Recover)
**Document ID 78: EXP25.04.04565**
- Status: PERMANENTLY DELETED
- Deleted: 2026-02-15 07:44:05
- Reason: Folder deletion cascade (bug)
- Database Record: DELETED
- Version Record: DELETED
- **File in Filestore: STILL EXISTS!** ✓

**File Location:**
```
/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf
```

---

## 🔧 Recovery Options

### Option 1: Manual Re-Upload (Recommended)

**Steps:**
1. Download the file from filestore:
   ```bash
   cp "/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf" ~/Desktop/
   ```

2. Re-upload via API:
   ```bash
   # Convert to base64
   base64 -w 0 ~/Desktop/EXP25.04.04565.pdf > file.base64
   
   # Upload via API
   curl -X POST http://localhost:8070/api/documents/upload \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "EXP25.04.04565",
       "department_id": 5,
       "document_type_id": 3,
       "file_name": "EXP25.04.04565.pdf",
       "file_data": "<base64_content>",
       "upload_kind": "main",
       "create_folder": true,
       "folder_name": "SC-SHIP-EXP25.04.04565",
       "folder_code": "EXP25.04.04565"
     }'
   ```

---

### Option 2: Database Record Recreation (Advanced)

Create a Python script to restore the document with original ID:

```python
#!/usr/bin/env python3
"""
Recovery script for document 78: EXP25.04.04565
"""
import base64
import sys
sys.path.insert(0, '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai')

# Read the file from filestore
file_path = '/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf'

with open(file_path, 'rb') as f:
    file_content = f.read()
    file_base64 = base64.b64encode(file_content).decode('utf-8')

file_size = len(file_content)

print(f"File found: {file_path}")
print(f"File size: {file_size} bytes")
print(f"Base64 length: {len(file_base64)} characters")
print()
print("File is ready to be re-uploaded!")
print()
print("Use the API to upload with this data")
```

---

### Option 3: Direct Database Insert (Expert Only)

⚠️ **Use with caution** - May break constraints

```python
import psycopg2
import base64
from datetime import datetime

conn = psycopg2.connect(dbname='lugal_local', user='capo7amzah')
cur = conn.cursor()

# Read file
with open('/path/to/EXP25.04.04565.pdf', 'rb') as f:
    file_data = base64.b64encode(f.read()).decode('utf-8')

# Recreate document record
# Note: ID 78 might conflict, use new ID
cur.execute('''
    INSERT INTO nbs_document 
    (name, department_id, document_type_id, barcode, state, is_locked, 
     uploader_id, upload_date, confidentiality_level, is_deleted)
    VALUES 
    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
''', ('EXP25.04.04565', 5, 3, 'NBSNBS-RECOVERED', 'active', True, 
      2, datetime.now(), 'internal', False))

new_doc_id = cur.fetchone()[0]
print(f"Created document with ID: {new_doc_id}")

# Create version record with file path
cur.execute('''
    INSERT INTO nbs_document_version
    (document_id, version_number, file_name, file_size, file_path,
     uploader_id, upload_date, notes)
    VALUES
    (%s, %s, %s, %s, %s, %s, %s, %s)
    RETURNING id
''', (new_doc_id, 1, 'EXP25.04.04565.pdf', file_size, 
      'nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf',
      2, datetime.now(), 'Recovered from filestore after permanent deletion'))

version_id = cur.fetchone()[0]

# Update document current_version_id
cur.execute('''
    UPDATE nbs_document 
    SET current_version_id = %s 
    WHERE id = %s
''', (version_id, new_doc_id))

conn.commit()
print(f"Document recovered! New ID: {new_doc_id}")

cur.close()
conn.close()
```

---

## 📊 Found EXP Files

### File 1: EXP25.06.06720.pdf ✅
**Status:** ACTIVE (Document ID 73)
- Location: `filestore_local/.../SC/SHIP/73/v1/EXP25.06.06720.pdf`
- Database: EXISTS
- **Action:** None needed (accessible)

### File 2: EXP25.04.04565.pdf ✓ RECOVERABLE!
**Status:** PERMANENTLY DELETED (Document ID 78)
- Location: `filestore_local/.../SC/SHIP/78/v1/EXP25.04.04565.pdf`
- Database: DELETED
- **File:** STILL EXISTS IN FILESTORE!
- **Action:** CAN BE RECOVERED

---

## 🎯 Recommended Recovery Steps

### Step 1: Copy File to Safe Location

```bash
# Copy to desktop for safekeeping
cp "/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf" \
   ~/Desktop/EXP25.04.04565_RECOVERED.pdf

# Verify
ls -lh ~/Desktop/EXP25.04.04565_RECOVERED.pdf
```

### Step 2: Re-upload via Frontend UI

1. Go to Documents page
2. Click "Upload Document"
3. Select department: Supply Chain
4. Select type: Shipment Document (or appropriate type)
5. Upload the recovered file from Desktop
6. Title: EXP25.04.04565
7. Create new folder if needed

---

## 🔍 What Happened

### Timeline of Document 78

```
2026-02-12 13:57:03 - Folder created: SC-SHIP-EXP25.04.04565
                    ↓
2026-02-12 ~13:57   - Document 78 uploaded: EXP25.04.04565
                    ↓
2026-02-15 07:44:05 - Folder deleted (cascade bug)
                    ↓
                    - Document soft deleted
                    ↓
                    - Document PERMANENTLY deleted ❌
                    ↓
                    - Database record removed
                    ↓
                    - Version records removed
                    ↓
                    - BUT: File left in filestore ✓ (orphaned)
```

### Why File Still Exists

Odoo's `permanent_delete()` method:
- Deletes database records
- **Does NOT delete files from filestore** (by design)
- Files remain as orphans
- Allows recovery in situations like this!

---

## 📁 All SC/SHIP Files in Filestore

```bash
# List all files
ls -lh /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/*/v1/*.pdf
```

**Found files:**
1. `/SC/SHIP/73/v1/EXP25.06.06720.pdf` - Active (Doc 73) ✓
2. `/SC/SHIP/78/v1/EXP25.04.04565.pdf` - Orphaned (can recover) ✓
3. `/SC/SHIP/41/v1/pdf-sample_0 (2).pdf` - Check status

---

## 💾 Recovery Using Backup (Alternative)

If you need the complete database record with all metadata:

### Step 1: Extract from Backup

```bash
# Check backup file
pg_restore --list backup | grep -i "document\|78"

# Extract specific table data
pg_restore backup --table=nbs_document --data-only \
  --file=documents_backup.sql

# Find document 78 in the SQL
grep "78.*EXP" documents_backup.sql
```

### Step 2: Restore Metadata

```bash
# Extract document 78 INSERT statement
# Modify ID if needed (to avoid conflicts)
# Run the INSERT manually
```

---

## 🛠️ Automated Recovery Script

I can create a script to automate the recovery:

```bash
#!/bin/bash
# recover_exp_document.sh

echo "=== Document Recovery Script ==="
echo ""

# Source file
SOURCE="/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf"

# Check file exists
if [ ! -f "$SOURCE" ]; then
    echo "❌ File not found: $SOURCE"
    exit 1
fi

echo "✓ File found: $SOURCE"
FILE_SIZE=$(stat -f%z "$SOURCE" 2>/dev/null || stat -c%s "$SOURCE")
echo "  Size: $FILE_SIZE bytes"

# Copy to recovery folder
RECOVERY_DIR="$HOME/recovered_documents"
mkdir -p "$RECOVERY_DIR"
cp "$SOURCE" "$RECOVERY_DIR/EXP25.04.04565.pdf"

echo ""
echo "✓ File copied to: $RECOVERY_DIR/EXP25.04.04565.pdf"
echo ""
echo "Next steps:"
echo "1. Open the NBS Archive system"
echo "2. Upload this file as a new document"
echo "3. Set title: EXP25.04.04565"
echo "4. Create folder: SC-SHIP-EXP25.04.04565"
```

---

## 📝 Summary

### Found EXP Documents:

1. **EXP25.06.06720** (Doc 73)
   - Status: ✅ ACTIVE
   - Action: None needed

2. **EXP25.04.04565** (Doc 78)
   - Status: ❌ PERMANENTLY DELETED
   - File: ✅ STILL EXISTS
   - Recovery: ✅ POSSIBLE

### Recovery Status: ✅ RECOVERABLE

The file **EXP25.04.04565.pdf** is still in the filestore and can be recovered!

---

## 🚀 Quick Recovery Command

```bash
# Copy file to a safe location
cp "/home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai/filestore_local/filestore/lugal_local/nbs_archive/SC/SHIP/78/v1/EXP25.04.04565.pdf" \
   ~/EXP25.04.04565_RECOVERED.pdf

echo "File recovered to: ~/EXP25.04.04565_RECOVERED.pdf"
echo "Re-upload this file via the UI or API"
```

**Would you like me to create an automated recovery script to restore this document?**
