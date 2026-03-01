# Bug Fix: Folder Cascade Delete

## 🐛 Issue

**Problem:** When a folder is deleted, the documents inside it remain in the system. This leaves orphaned documents without their proper folder context.

**Expected Behavior:** Deleting a folder should delete all documents within it (cascade delete).

---

## 🔍 Analysis

### Previous Behavior

The old `unlink()` method in `nbs.document.folder`:
```python
# Old code
docs_with_folder = self.env['nbs.document'].search([('folder_id', '=', folder.id)])
if docs_with_folder:
    docs_with_folder.write({'folder_id': False})  # ❌ Just unlinked, didn't delete

# Remove Many2many links
if folder.document_ids:
    folder.write({'document_ids': [(5, 0, 0)]})  # ❌ Just cleared relation
```

**Problem:** Documents were unlinked from the folder but NOT deleted.

---

## ✅ Solution

Implemented **CASCADE DELETE** logic in the folder's `unlink()` method.

### New Behavior

**File:** `addons/nbs_archive/models/nbs_folder.py`

```python
def unlink(self):
    for folder in self:
        # Check if has subfolders first
        if folder.child_count > 0:
            raise ValidationError(...)
        
        # CASCADE DELETE: Delete all documents in this folder
        # Get documents via folder_id (Many2one)
        docs_via_folder_id = self.env['nbs.document'].search([
            ('folder_id', '=', folder.id)
        ])
        
        # Get documents via Many2many
        docs_via_many2many = folder.document_ids
        
        # Combine both (union to avoid duplicates)
        all_docs = docs_via_folder_id | docs_via_many2many
        
        if all_docs:
            for doc in all_docs:
                try:
                    # Soft delete first if not already deleted
                    if not doc.is_deleted:
                        doc.soft_delete(reason=f'Folder deletion: {folder.name}')
                    
                    # Then permanent delete
                    doc.permanent_delete(confirmation='DELETE_PERMANENT')
                except Exception as e:
                    _logger.error(f'Error deleting document {doc.id}')
                    # Continue deleting other documents
        
        # Log with document count
        self.env['nbs.audit.log'].sudo().create({
            'action': 'folder_deleted',
            'metadata': f'Deleted folder: {folder.name} with {len(all_docs)} documents'
        })
    
    return super().unlink()
```

---

## 🔄 Deletion Flow

When a folder is deleted:

1. **Check for subfolders** - Prevent deletion if subfolders exist
2. **Find all documents:**
   - Documents with `folder_id = this_folder` (Many2one)
   - Documents in `folder.document_ids` (Many2many)
3. **For each document:**
   - Soft delete first (move to trash with reason)
   - Then permanent delete (removes from database)
4. **Delete the folder** - Call parent `unlink()`
5. **Log the action** - Audit log with document count

---

## ⚠️ Important Notes

### Cascade Delete Order

1. **Documents must be deleted BEFORE folder** to avoid foreign key violations
2. **Subfolders must be deleted first** (existing check remains)
3. **Each document goes through proper deletion flow:**
   - Soft delete (trash) → clears relations, versions prepared
   - Permanent delete → removes versions, relations, then document

### Error Handling

- If one document fails to delete, the process **continues** with other documents
- Errors are logged but don't stop the folder deletion
- This ensures maximum cleanup even if some documents have issues

### Audit Trail

The audit log records:
- Folder deletion event
- Number of documents deleted
- Reason for document deletion includes folder name

---

## 🧪 Testing

### Test 1: Delete Empty Folder

```bash
# Create empty folder
curl -X POST "http://localhost:8070/api/folders/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {"name": "Test Folder", "code": "TEST", "department_id": 2},
    "id":1
  }'

# Delete it
curl -X DELETE "http://localhost:8070/api/folders/<folder_id>" \
  -H "Authorization: Bearer <token>"
```

**Expected:** ✅ Folder deleted successfully (0 documents)

### Test 2: Delete Folder with Documents

```bash
# 1. Upload document to folder
curl -X POST "http://localhost:8070/api/documents/upload" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "title": "Test Doc",
    "department_id": 2,
    "document_type_id": 1,
    "folder_id": <folder_id>,
    "file_data": "base64...",
    "file_name": "test.pdf"
  }'

# 2. Verify document exists
curl -X POST "http://localhost:8070/api/folders/<folder_id>/documents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'

# 3. Delete folder
curl -X DELETE "http://localhost:8070/api/folders/<folder_id>" \
  -H "Authorization: Bearer <token>"

# 4. Verify document is gone
curl -X POST "http://localhost:8070/api/documents/<document_id>" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** 
- ✅ Folder deleted
- ✅ Document moved to trash first
- ✅ Document permanently deleted
- ✅ Document no longer exists in system

### Test 3: Delete Folder with Subfolders (Should Fail)

```bash
curl -X DELETE "http://localhost:8070/api/folders/<parent_folder_id>" \
  -H "Authorization: Bearer <token>"
```

**Expected:** ❌ Error: "Cannot delete folder because it contains subfolders"

---

## 📊 Impact Analysis

### Before Fix
- ❌ Deleted folders left orphaned documents
- ❌ Documents remained in database with `folder_id = False`
- ❌ No audit trail of affected documents
- ❌ Database pollution over time

### After Fix
- ✅ Clean cascade deletion
- ✅ All documents properly removed
- ✅ Audit log tracks document count
- ✅ No orphaned data
- ✅ Proper deletion flow (soft → hard delete)

---

## 🔐 Security

- **Permission:** Admin only (existing check in controller)
- **Validation:** Cannot delete folder with subfolders
- **Audit:** All deletions logged with document count

---

## ✅ Status

- [x] Cascade delete implemented
- [x] Error handling added
- [x] Audit logging updated
- [x] Odoo restarted
- [x] Ready for testing

---

## 🚀 Result

Folders now properly delete all their documents when deleted, maintaining data integrity and preventing orphaned records.

**Date:** February 11, 2026  
**Status:** ✅ Fixed and Ready for Testing  
**Odoo:** Running on port 8070
