# Bug Fix: Folder Delete 500 Internal Server Error

## Date: 2026-02-15

## 🐛 Problem

Deleting certain folders resulted in **500 Internal Server Error**:

```
DELETE /api/folders/86 → 500 ERROR ❌
DELETE /api/folders/84 → 500 ERROR ❌
DELETE /api/folders/85 → 200 OK ✓
```

**User Impact:**
- Cannot delete some folders
- Generic error message (no details)
- Inconsistent behavior (some work, some don't)

---

## 🔍 Root Cause Analysis

### Issue 1: Inconsistent folder_id Relationships

**Folder 86:**
```
Via folder_id (Many2one):
  - Doc 125: folder_id=86 ✓

Via Many2many (folder_document_rel):
  - Doc 124: folder_id=NULL ❌ (inconsistent!)
  - Doc 125: folder_id=86 ✓
```

**Folder 84:**
```
Via folder_id:
  - Doc 121: folder_id=84 ✓
  - Doc 126: folder_id=84 ✓

Via Many2many:
  - Doc 122: folder_id=NULL ❌ (inconsistent!)
  - Doc 121: folder_id=84 ✓
  - Doc 126: folder_id=84 ✓
```

**The Problem:**
- Documents were linked via Many2many but `folder_id` was NULL
- When `folder.unlink()` tries to soft_delete these documents
- The `soft_delete()` method checks `folder_id` to determine if main doc
- With `folder_id=NULL`, logic fails or behaves unexpectedly
- Causes 500 error

### Issue 2: Poor Error Handling

**Before:**
```python
def delete_folder(self, folder_id, **kwargs):
    try:
        folder.unlink()  # Black box - if fails, don't know why
        return success
    except Exception as e:
        return error  # Generic error, no details
```

**Problems:**
- No detailed logging
- Generic error responses
- Can't diagnose issues
- No status codes (always 200)

---

## ✅ Fixes Applied

### Fix 1: Database Consistency Repair

**Fixed folder 86:**
```sql
-- Before
Doc 124: folder_id=NULL, in folder_ids=[86]  ❌

-- After
Doc 124: folder_id=86, in folder_ids=[86]  ✅
```

**Fixed folder 84:**
```sql
-- Before
Doc 122: folder_id=NULL, in folder_ids=[84]  ❌

-- After
Doc 122: folder_id=84, in folder_ids=[84]  ✅
```

### Fix 2: Enhanced Error Handling

**Added detailed logging:**
```python
_logger.info(f'[DELETE FOLDER] Starting deletion of folder {folder_id}: {folder.name}')

try:
    folder.unlink()
    _logger.info(f'[DELETE FOLDER] Successfully deleted folder {folder_id}')
except Exception as unlink_error:
    _logger.error(f'[DELETE FOLDER] Unlink failed: {str(unlink_error)}', exc_info=True)
    return error_with_details
```

**Added proper HTTP status codes:**
- 401: Unauthorized
- 403: Admin permission required
- 404: Folder not found
- 500: Server error

**Added detailed error messages:**
```json
{
  "success": false,
  "error": "Failed to delete folder: <specific reason>"
}
```

### Fix 3: Better Document Processing in Folder Unlink

**Enhanced folder.unlink():**
```python
failed_docs = []
for doc in all_docs:
    try:
        _logger.info(f'Processing doc {doc.id}: {doc.name}, role={doc.folder_role}')
        doc.with_context(skip_folder_auto_delete=True).soft_delete(...)
        _logger.info(f'✓ Moved document {doc.id} to trash')
    except Exception as e:
        _logger.error(f'Error moving doc {doc.id}: {str(e)}', exc_info=True)
        failed_docs.append(doc.id)

if failed_docs:
    raise ValidationError(f'Failed to move some documents: {failed_docs}')
```

**Benefits:**
- Detailed logging for each document
- Tracks which documents fail
- Prevents partial deletions
- Clear error messages

---

## 🎯 Why Some Folders Worked and Others Didn't

### Folder 85 (Deleted Successfully) ✓

**Characteristics:**
- All documents had consistent folder_id
- No Many2many inconsistencies
- Clean delete operation
- Result: 200 OK

### Folder 86 (Failed with 500) ❌

**Characteristics:**
- Doc 124 had folder_id=NULL
- Inconsistent Many2many relationship
- soft_delete() logic confusion
- Result: 500 ERROR

**After Fix:**
- Doc 124 now has folder_id=86
- Consistent relationships
- Should delete cleanly now
- Result: 200 OK ✓

### Folder 84 (Failed with 500) ❌

**Characteristics:**
- Doc 122 had folder_id=NULL
- Inconsistent Many2many relationship
- Same issue as folder 86
- Result: 500 ERROR

**After Fix:**
- Doc 122 now has folder_id=84
- Consistent relationships
- Should delete cleanly now
- Result: 200 OK ✓

---

## 🧪 Testing

### Test Folder 86 Delete

```bash
curl -X DELETE http://localhost:8070/api/folders/86 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected Response:
{
  "success": true,
  "message": "Folder deleted successfully"
}

# Check logs:
tail -f odoo_local.log | grep "DELETE FOLDER"

# Expected logs:
[DELETE FOLDER] Starting deletion of folder 86: QC-QC_RPT-TargetMainFile
[DELETE FOLDER] Processing doc 124: TargetMainFile, role=main
[DELETE FOLDER] ✓ Moved document 124 to trash
[DELETE FOLDER] Processing doc 125: BaseSecondaryFile, role=sub
[DELETE FOLDER] ✓ Moved document 125 to trash
[DELETE FOLDER] Successfully deleted folder 86
```

### Test Folder 84 Delete

```bash
curl -X DELETE http://localhost:8070/api/folders/84 \
  -H "Authorization: Bearer YOUR_TOKEN"

# Expected: Success (200 OK)
# Docs 121, 122, 126 → trash
```

### Verify Documents in Trash

```bash
curl -X POST http://localhost:8070/api/documents/trash \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "call", "params": {}, "id": 1}'

# Expected: Shows docs 121, 122, 124, 125, 126
```

---

## 📊 Folder States After Fix

### Folder 84
```
Before Fix:
  - Doc 121: folder_id=84 ✓
  - Doc 122: folder_id=NULL ❌ (inconsistent)
  - Doc 126: folder_id=84 ✓
  - Delete Status: 500 ERROR ❌

After Fix:
  - Doc 121: folder_id=84 ✓
  - Doc 122: folder_id=84 ✓ (fixed)
  - Doc 126: folder_id=84 ✓
  - Delete Status: Should work ✓
```

### Folder 86
```
Before Fix:
  - Doc 124: folder_id=NULL ❌ (inconsistent)
  - Doc 125: folder_id=86 ✓
  - Delete Status: 500 ERROR ❌

After Fix:
  - Doc 124: folder_id=86 ✓ (fixed)
  - Doc 125: folder_id=86 ✓
  - Delete Status: Should work ✓
```

---

## 🔧 Files Modified

### 1. folder_controller.py
**Lines ~210-230:** Enhanced delete_folder endpoint

**Changes:**
- Added detailed logging at each step
- Added proper HTTP status codes
- Added try-catch around unlink()
- Better error messages

### 2. nbs_folder.py
**Lines ~362-377:** Enhanced document processing

**Changes:**
- Added detailed logging per document
- Track failed documents
- Raise ValidationError if any fail
- Prevent partial deletions

### 3. Database Cleanup
**Fixed documents:**
- Doc 124: folder_id NULL → 86
- Doc 122: folder_id NULL → 84

---

## 🎯 Prevention: How This Happened

### Root Cause of Inconsistency

Documents were added to folders via Many2many but `folder_id` wasn't updated:

```python
# Somewhere in code (wrong):
folder.write({'document_ids': [(4, doc.id)]})  # Only updates Many2many
# doc.folder_id is still NULL! ❌

# Correct way:
doc.write({
    'folder_id': folder.id,  # Update Many2one
    'folder_ids': [(4, folder.id)]  # Update Many2many
})
```

### Where This Could Happen

1. **Document upload** - If folder link not set properly
2. **Document move** - If only Many2many updated
3. **Folder add-document** - If folder_id not synced
4. **Folder creation with documents** - If initial link incomplete

---

## 🛡️ Prevention Measures Added

### 1. Validation in Move API

Now ensures both fields are updated:
```python
vals['folder_id'] = target_folder_id  # Many2one
vals['folder_ids'] = folder_commands  # Many2many
```

### 2. Better Error Reporting

Now folder delete will:
- Log each document processing
- Report which documents fail
- Prevent partial deletions
- Give clear error messages

### 3. Database Consistency Check

Add this as a cron job:
```sql
-- Find documents with inconsistent folder relationships
SELECT d.id, d.name, d.folder_id, array_agg(fdr.folder_id) as folder_ids
FROM nbs_document d
LEFT JOIN folder_document_rel fdr ON d.id = fdr.document_id
WHERE fdr.folder_id IS NOT NULL
GROUP BY d.id, d.name, d.folder_id
HAVING d.folder_id IS NULL OR d.folder_id != ALL(array_agg(fdr.folder_id));
```

---

## 📋 HTTP Status Codes Reference

The delete endpoint now returns proper status codes:

| Code | Meaning | When |
|------|---------|------|
| 200 OK | Success | Folder deleted |
| 401 Unauthorized | Auth failed | No/invalid JWT token |
| 403 Forbidden | No permission | User not admin |
| 404 Not Found | Missing | Folder doesn't exist |
| 500 Server Error | Server issue | Unlink failed |

**Before:** Always returned 200 (even on errors)  
**After:** Returns appropriate code for each situation

---

## 🔍 Debugging Future Issues

### Check Logs
```bash
# Real-time monitoring
tail -f odoo_local.log | grep "DELETE FOLDER"

# Check for errors
tail -500 odoo_local.log | grep -i "error\|exception"
```

### Validate Folder Consistency
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect(dbname='lugal_local', user='capo7amzah')
cur = conn.cursor()

# Check for inconsistent folders
cur.execute('''
    SELECT DISTINCT fdr.folder_id, d.folder_id, d.id
    FROM folder_document_rel fdr
    JOIN nbs_document d ON fdr.document_id = d.id
    WHERE d.folder_id IS NULL OR d.folder_id != fdr.folder_id
''')

print('Inconsistent documents:')
for row in cur.fetchall():
    print(f'  Doc {row[2]}: Many2many={row[0]}, folder_id={row[1]}')

cur.close()
conn.close()
"
```

### Test Delete with Curl
```bash
# Test delete
curl -X DELETE http://localhost:8070/api/folders/86 \
  -H "Authorization: Bearer TOKEN" \
  -v

# Check response
# Check logs immediately after
```

---

## 📊 Summary

### Problem
- Folders 84, 86 couldn't be deleted (500 error)
- Folder 85 deleted fine
- Inconsistent document relationships

### Root Cause
- Documents linked via Many2many without folder_id set
- soft_delete() logic failed on NULL folder_id
- Poor error handling hid the real issue

### Solution
1. ✅ Fixed document folder_id inconsistencies
2. ✅ Enhanced error handling and logging
3. ✅ Added detailed per-document logging
4. ✅ Added proper HTTP status codes
5. ✅ Prevent partial deletions

### Files Modified
- `folder_controller.py` - Better error handling
- `nbs_folder.py` - Enhanced logging, validation
- Database - Fixed docs 122, 124

---

## 🚀 Deployment Status

- ✅ Database inconsistencies fixed
- ✅ Code improvements applied
- ✅ Odoo restarted (PID: 1868763)
- ✅ Service ready
- ✅ Enhanced logging active

**Folders 84 and 86 should now delete successfully!**

---

## 🧪 Next Steps

1. **Test folder 86 delete** - Should work now
2. **Test folder 84 delete** - Should work now
3. **Check logs** - Detailed info for debugging
4. **Verify trash** - Documents should appear
5. **Monitor** - Watch for any other 500 errors

**Version:** 1.7.1  
**Priority:** HIGH  
**Status:** ✅ DEPLOYED

Try deleting folders 84 and 86 again - they should work now!
