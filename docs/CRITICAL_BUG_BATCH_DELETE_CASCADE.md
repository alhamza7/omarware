# 🚨 CRITICAL BUG FIX: Batch Delete Cascade Deletion

## Date: 2026-02-15

## ⚠️ SEVERITY: CRITICAL - DATA LOSS BUG

### Impact
- Documents were **PERMANENTLY DELETED** instead of moved to trash
- Entire folders with all documents were CASCADE DELETED
- No recovery possible (documents not in trash)

---

## 🐛 Bug Description

### What Happened

User scenario:
1. User batch deleted secondary documents (113, 114, 115, 116)
2. **All documents in folder 81 were PERMANENTLY DELETED** (including main document)
3. **Folder 81 was deleted**
4. **Nothing appeared in trash** - documents gone forever

### Expected Behavior ✓
- Documents should be moved to trash
- Documents should appear in `/api/documents/trash`
- Documents can be restored within 30 days
- Folder should remain if it has documents

### Actual Behavior ❌
- Documents were permanently deleted (cascade)
- Nothing in trash API response
- Folder was deleted
- All documents in folder lost

---

## 🔍 Root Causes

### Cause 1: Wrong "is_main_document" Check

**Location:** `nbs_document.py` line ~441

**Before (WRONG):**
```python
is_main_document = not document.parent_document_id
```

**Problem:**
- Secondary documents might have `parent_document_id = null`
- They were incorrectly identified as "main documents"
- Triggered folder auto-deletion logic

**After (FIXED):**
```python
is_main_document = (document.folder_role == 'main')
```

**Now correctly checks `folder_role` field.**

---

### Cause 2: Folder Cascade Deletion

**Location:** `nbs_folder.py` line ~365-373

**Before (CATASTROPHIC):**
```python
# For each document: move to trash first, then permanent delete
for doc in all_docs:
    if not doc.is_deleted:
        doc.soft_delete(reason=f'Folder deletion: {folder.name}')
    
    # Then permanent delete ← THIS CAUSED PERMANENT DATA LOSS!
    doc.permanent_delete(confirmation='DELETE_PERMANENT')
```

**Problem:**
- When folder was deleted, it PERMANENTLY deleted all documents
- Called `permanent_delete()` which removes from database
- Documents didn't stay in trash - gone forever

**After (FIXED):**
```python
# For each document: ONLY move to trash (do NOT permanently delete)
for doc in all_docs:
    if not doc.is_deleted:
        # Pass context flag to prevent infinite recursion
        doc.with_context(skip_folder_auto_delete=True).soft_delete(
            reason=f'Folder deletion: {folder.name}'
        )
```

**Now only soft deletes - documents stay in trash.**

---

### Cause 3: Infinite Recursion Prevention

**Problem:**
- Deleting main doc → triggers folder delete
- Folder delete → triggers document soft_delete
- Document soft_delete → might trigger folder delete again
- **Infinite loop!**

**Solution:** Context flag
```python
# In soft_delete():
if is_main_document and folder_id and not self._context.get('skip_folder_auto_delete'):
    # Auto-delete folder

# When folder calls soft_delete:
doc.with_context(skip_folder_auto_delete=True).soft_delete(...)
```

---

## 🔧 The Complete Chain of Events

### What Happened (Bug)

```
1. User: batch/trash [113, 114, 115, 116] (secondary docs)
   ↓
2. For each document: soft_delete()
   ↓
3. Check: is_main_document = not parent_document_id
   Result: TRUE (because parent_document_id was null) ❌
   ↓
4. Auto-delete folder 81 (thinking main doc was deleted)
   ↓
5. Folder.unlink() CASCADE DELETES all documents:
   - Calls soft_delete() on each doc
   - Then calls permanent_delete() ← PERMANENT DATA LOSS!
   ↓
6. Result:
   - Documents 113-116: GONE (permanently)
   - All other docs in folder 81: GONE (permanently)  
   - Folder 81: DELETED
   - Trash: EMPTY
```

### What Happens Now (Fixed)

```
1. User: batch/trash [113, 114, 115, 116] (secondary docs)
   ↓
2. For each document: soft_delete()
   ↓
3. Check: is_main_document = (folder_role == 'main')
   Result: FALSE (secondary docs have folder_role='sub') ✓
   ↓
4. Skip folder auto-delete (not main documents)
   ↓
5. Documents moved to trash:
   - state = 'trash'
   - is_deleted = True
   - restore_deadline = now + 30 days
   ↓
6. Result:
   - Documents 113-116: IN TRASH ✓
   - Folder 81: STILL EXISTS ✓
   - Main document: STILL EXISTS ✓
   - Can restore within 30 days ✓
```

---

## 🛠️ Fixes Applied

### Fix 1: Correct Main Document Detection

**File:** `addons/nbs_archive/models/nbs_document.py`

**Line ~441:**
```python
# Before
is_main_document = not document.parent_document_id

# After
is_main_document = (document.folder_role == 'main')
```

### Fix 2: Count Only Main Documents

**File:** `addons/nbs_archive/models/nbs_document.py`

**Line ~459-462:**
```python
# Before
remaining_docs = search_count([
    ('folder_id', '=', folder_id),
    ('is_deleted', '=', False)
])

# After
remaining_main_docs = search_count([
    ('folder_id', '=', folder_id),
    ('folder_role', '=', 'main'),  # ← Only count main docs
    ('is_deleted', '=', False)
])
```

### Fix 3: Only Soft Delete (No Permanent Delete)

**File:** `addons/nbs_archive/models/nbs_folder.py`

**Line ~365-373:**
```python
# Before
for doc in all_docs:
    if not doc.is_deleted:
        doc.soft_delete(reason=f'Folder deletion: {folder.name}')
    
    doc.permanent_delete(confirmation='DELETE_PERMANENT')  # ❌ DATA LOSS!

# After
for doc in all_docs:
    if not doc.is_deleted:
        doc.with_context(skip_folder_auto_delete=True).soft_delete(
            reason=f'Folder deletion: {folder.name}'
        )
    # NO permanent_delete() call! Documents stay in trash ✓
```

### Fix 4: Prevent Infinite Recursion

**File:** `addons/nbs_archive/models/nbs_document.py`

**Line ~455:**
```python
# Before
if is_main_document and folder_id:
    folder.sudo().unlink()

# After
if is_main_document and folder_id and not self._context.get('skip_folder_auto_delete'):
    folder.sudo().unlink()
```

---

## 🧪 Testing Scenarios

### Test 1: Delete Secondary Documents Only

```bash
POST /api/documents/batch/trash
{
  "document_ids": [113, 114, 115, 116]  # All secondary docs
}

Expected:
✓ Secondary docs moved to trash
✓ Main document still active
✓ Folder still exists
✓ Documents appear in /api/documents/trash
```

### Test 2: Delete Main Document

```bash
POST /api/documents/batch/trash
{
  "document_ids": [101]  # Main document
}

Expected:
✓ Main document moved to trash
✓ Folder auto-deleted (if no other main docs)
✓ Secondary docs moved to trash
✓ All documents appear in /api/documents/trash
```

### Test 3: Delete Mixed Documents

```bash
POST /api/documents/batch/trash
{
  "document_ids": [101, 113, 114]  # Main + secondaries
}

Expected:
✓ All documents moved to trash
✓ Folder auto-deleted
✓ All documents in trash (not permanently deleted)
```

---

## 📊 Before vs After Comparison

### Scenario: Delete 4 Secondary Documents

| Aspect | Before (Bug) | After (Fixed) |
|--------|-------------|---------------|
| Secondary docs in trash | ❌ No (permanently deleted) | ✅ Yes |
| Main doc status | ❌ Permanently deleted | ✅ Still active |
| Folder status | ❌ Deleted | ✅ Still exists |
| Can restore | ❌ No (data lost) | ✅ Yes (within 30 days) |
| Trash API response | ❌ Empty | ✅ Shows deleted docs |

---

## 🔐 Data Loss Prevention

### New Safeguards

1. **Correct main document detection**
   - Uses `folder_role == 'main'`
   - No longer misidentifies secondary docs

2. **Count only main documents**
   - Folder auto-delete only if NO main docs remain
   - Secondary docs don't trigger folder deletion

3. **No permanent delete in folder cascade**
   - Documents only soft-deleted
   - All documents go to trash
   - Can be restored

4. **Recursion prevention**
   - Context flag prevents infinite loops
   - Safe cascade operations

---

## 🚨 Recovery for Lost Data

### For Production (If This Bug Occurred)

**Option 1: Database Backup Restore**
```sql
-- Restore from most recent backup before bug occurred
pg_restore -d lugal_local backup_file.sql
```

**Option 2: Audit Log Analysis**
```sql
-- Find deleted documents from audit logs
SELECT document_id, metadata, timestamp
FROM nbs_audit_log
WHERE action = 'folder_deleted'
  AND timestamp > '2026-02-15 07:00:00'
ORDER BY timestamp DESC;

-- Recreate documents based on audit trail
```

**Option 3: Filestore Recovery**
```bash
# Check filestore for orphaned files
ls -lah filestore_local/filestore/lugal_local/

# Files might still exist even if DB records deleted
```

---

## 📋 Files Modified

### 1. nbs_document.py
**Lines changed:**
- ~441: Fixed `is_main_document` check
- ~459-462: Count only main documents
- ~455: Added recursion prevention check

### 2. nbs_folder.py
**Lines changed:**
- ~350: Updated comment (CASCADE → SOFT DELETE)
- ~363: Changed log message
- ~365-376: Removed permanent_delete, kept only soft_delete
- Added context flag to prevent recursion

---

## ✅ Verification Steps

After deploying the fix:

### 1. Test Secondary Document Deletion
```bash
# Create test folder with 1 main + 2 secondary docs
# Delete only secondary docs
# Verify:
# - Secondary docs in trash ✓
# - Main doc still active ✓
# - Folder still exists ✓
```

### 2. Test Main Document Deletion
```bash
# Create test folder with 1 main doc only
# Delete main doc
# Verify:
# - Main doc in trash ✓
# - Folder auto-deleted ✓
# - Can restore main doc ✓
```

### 3. Check Trash API
```bash
POST /api/documents/trash

# Should show all deleted documents
# Should include deletion_reason
# Should include restore_deadline
```

---

## 🎯 Prevention Checklist

- [x] Fixed `is_main_document` logic
- [x] Fixed folder auto-delete condition
- [x] Removed permanent delete from folder cascade
- [x] Added recursion prevention
- [x] Documents go to trash, not deleted
- [ ] Add unit tests for batch delete
- [ ] Add integration tests for folder deletion
- [ ] Add monitoring alerts for cascade deletes
- [ ] Document recovery procedures

---

## 📝 Deployment Notes

### Critical Priority: IMMEDIATE DEPLOYMENT REQUIRED

This is a **data loss bug** that must be fixed immediately.

**Steps:**
1. ✅ Stop Odoo
2. ✅ Apply code changes
3. ✅ Restart Odoo
4. ✅ Test batch delete immediately
5. [ ] Notify users if data was lost
6. [ ] Check if backups need to be restored

---

## 🔔 User Communication

If this bug affected production data:

**Message to affected users:**
```
Critical Bug Fix Applied

We discovered and fixed a critical bug where deleting secondary 
documents could cause permanent data loss. 

If you deleted documents on [DATE] between [TIME] and [TIME], 
please contact support immediately for data recovery assistance.

We apologize for any inconvenience and have implemented additional 
safeguards to prevent this issue.
```

---

## 📊 Statistics

### Bug Impact Analysis

**If bug occurred in production:**
- Check audit logs for `folder_deleted` actions
- Count affected folders
- Estimate documents lost
- Plan recovery strategy

```sql
-- Count folders deleted recently
SELECT COUNT(*), MAX(timestamp)
FROM nbs_audit_log
WHERE action = 'folder_deleted'
  AND timestamp > '2026-02-14 00:00:00';

-- Get metadata about deleted folders
SELECT metadata, timestamp
FROM nbs_audit_log
WHERE action = 'folder_deleted'
  AND timestamp > '2026-02-14 00:00:00'
ORDER BY timestamp DESC;
```

---

## 🛡️ Future Prevention

### 1. Add Confirmation for Cascade Operations
```python
# Require explicit confirmation for operations that affect multiple records
def unlink(self):
    if self._context.get('cascade_confirmation') != 'CONFIRM_CASCADE_DELETE':
        raise ValidationError('Cascade delete requires explicit confirmation')
```

### 2. Add Soft Delete Flag to Folder
```python
# Instead of permanently deleting folders, soft delete them too
folder.write({'active': False, 'deleted_at': now()})
```

### 3. Add Trash Retention Policy
```python
# Ensure documents stay in trash for minimum period
if document.deleted_at:
    days_in_trash = (now() - document.deleted_at).days
    if days_in_trash < 30:
        raise ValidationError('Cannot permanently delete within 30 days')
```

### 4. Add Unit Tests
```python
def test_batch_delete_secondary_documents(self):
    # Delete secondary docs
    # Assert: main doc still exists
    # Assert: folder still exists
    # Assert: secondary docs in trash
```

---

## 🔄 Recovery Procedure (If Needed)

### For Documents Lost to This Bug

1. **Check Latest Backup**
   ```bash
   # Find most recent backup before incident
   ls -lht /path/to/backups/ | head -5
   ```

2. **Extract Lost Documents**
   ```sql
   -- From backup database
   SELECT id, name, folder_id, file_data
   FROM nbs_document
   WHERE id IN (113, 114, 115, 116, ...);
   ```

3. **Restore to Current Database**
   ```python
   # Script to restore documents from backup
   # Set state='trash' and is_deleted=True
   # Preserve audit trail
   ```

4. **Verify Filestore**
   ```bash
   # Check if file data still exists in filestore
   cd filestore_local/filestore/lugal_local
   # Files might still be there even if DB record deleted
   ```

---

## 📈 Monitoring

### Add Alerts For

1. **Multiple cascade deletes**
   - Alert if >10 documents deleted in single operation
   
2. **Folder deletions**
   - Alert on any folder delete
   - Require admin approval

3. **Permanent deletes**
   - Alert on any permanent_delete() call
   - Log full stack trace

---

## 🎯 Summary

### The Bug (Before)
1. ❌ Wrong main document detection
2. ❌ Folder cascade PERMANENTLY deleted documents
3. ❌ No documents in trash
4. ❌ Data loss - no recovery

### The Fix (After)
1. ✅ Correct main document detection using `folder_role`
2. ✅ Folder only SOFT DELETES documents
3. ✅ Documents appear in trash
4. ✅ Can restore within 30 days
5. ✅ Recursion prevention
6. ✅ No data loss

---

## 📄 Related Documentation

- `BUGFIX_FOLDER_MOVE_AND_VALIDATIONS.md` - Folder move fixes
- `DOCUMENT_ROLE_FINAL_LOGIC.md` - Document role logic
- `BUGFIX_FOLDER_INCONSISTENCY.md` - Folder consistency

---

## ⚡ Action Items

### Immediate (DONE)
- [x] Fix `is_main_document` logic
- [x] Remove permanent delete from folder cascade
- [x] Add recursion prevention
- [x] Deploy fix

### Short-term (TODO)
- [ ] Add unit tests for batch delete
- [ ] Add integration tests
- [ ] Review all cascade delete operations
- [ ] Add deletion confirmations

### Long-term (TODO)
- [ ] Implement soft delete for folders
- [ ] Add trash retention policies
- [ ] Add monitoring alerts
- [ ] Document recovery procedures
- [ ] User training on delete operations

---

**Status:** ✅ CRITICAL FIX DEPLOYED  
**Version:** 1.6.0  
**Priority:** URGENT  
**Data Loss Risk:** ELIMINATED

⚠️ **If production data was affected, initiate recovery procedures immediately!**
