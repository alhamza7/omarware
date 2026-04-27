# Bug Fixes: Folder Move API & Document Validations

## Date: 2026-02-14

## Issues Fixed

### 1. Move Folder API - Secondary Documents Replacing Main Documents ✓

**Problem:**
When moving a secondary/sub document from one folder to another, it was replacing the target folder's main document instead of being added as a secondary document.

**Root Cause:**
The `batch_move_folder` API in `batch_operations_controller.py` was updating both `folder_id` (Many2one) and `folder_ids` (Many2many) for ALL documents, regardless of whether they were main or secondary documents.

**Solution:**
Modified the move logic to:
- Detect if a document is a secondary document (has `parent_document_id` or `folder_role` = 'sub'/'attachment')
- For secondary documents:
  - Only update `folder_ids` (Many2many) - NOT `folder_id` (Many2one)
  - Find the target folder's main document
  - Update `parent_document_id` to point to the target folder's main document
  - Preserve `folder_role` as 'sub' or 'attachment'
- For main documents:
  - Update both `folder_id` (Many2one) and `folder_ids` (Many2many)

**Files Changed:**
- `addons/nbs_archive/controllers/batch_operations_controller.py`

---

### 2. Missing Document Role Key in API Response ✓

**Problem:**
The document API response didn't have a clear key to indicate whether a document is a main document or a sub/secondary document. The `relation_type` field was returning `null` for main documents.

**Solution:**
Added two new keys to all document API responses:
- `is_main_document`: Boolean - `true` if document has no parent, `false` otherwise
- `document_role`: String - 'main', 'sub', 'attachment', or 'other'
- `relation_type`: Fixed to return 'main' for main documents instead of `null`

**Example Response:**
```json
{
  "id": 85,
  "title": "d - Copy (19).pdf",
  "parent_document_id": null,
  "is_main_document": true,
  "document_role": "main",
  "relation_type": "main",
  ...
}
```

For secondary documents:
```json
{
  "id": 86,
  "title": "sub-document.pdf",
  "parent_document_id": 85,
  "is_main_document": false,
  "document_role": "sub",
  "relation_type": "secondary_document",
  ...
}
```

**Files Changed:**
- `addons/nbs_archive/controllers/document_controller.py`
  - Updated `get_documents()` endpoint
  - Updated `get_document()` endpoint
  - Updated `list_trash()` endpoint

---

### 3. Folder Not Auto-Deleted When Main Document is Deleted ✓

**Problem:**
When deleting the main document from the documents page, the folder remained with 0 documents. The folder should be automatically removed.

**Solution:**
Enhanced the `soft_delete()` method in `nbs_document.py` to:
1. Check if the document being deleted is a main document (no `parent_document_id`)
2. If yes, check if it has an associated folder
3. Count remaining active documents in that folder
4. If count is 0, automatically delete the folder
5. Log the auto-deletion

**Files Changed:**
- `addons/nbs_archive/models/nbs_document.py`

---

### 4. No Validation for Duplicate Document Names ✓

**Problem:**
Users could create multiple documents with the same name, leading to confusion and potential data integrity issues.

**Solution:**
Added validation in the `create()` method to check for duplicate names within the same department and document type combination. If a duplicate is found, raises a `ValidationError` with a clear message.

**Validation Rules:**
- Document name must be unique within: department + document type
- Only checks active documents (excludes deleted ones)
- Error message: "A document with the name 'XXX' already exists in this department and document type. Please use a different name."

**Files Changed:**
- `addons/nbs_archive/models/nbs_document.py`

---

## Technical Details

### Modified Files Summary

1. **addons/nbs_archive/models/nbs_document.py**
   - Added logging import
   - Added duplicate name validation in `create()`
   - Enhanced `soft_delete()` with auto-folder deletion logic

2. **addons/nbs_archive/controllers/document_controller.py**
   - Added `is_main_document` field to all document responses
   - Added `document_role` field to all document responses
   - Fixed `relation_type` to return 'main' instead of null

3. **addons/nbs_archive/controllers/batch_operations_controller.py**
   - Completely rewrote move logic to handle main vs secondary documents
   - Added detection of document type before moving
   - Added parent_document_id update for secondary documents
   - Prevented secondary documents from replacing main documents

### Database Impact
- No database schema changes required
- All changes are in business logic only

### Backward Compatibility
- ✓ All changes are backward compatible
- ✓ Existing API contracts maintained
- ✓ New fields are additions only (no removals)
- ✓ Existing document relationships preserved

---

## Testing Recommendations

### 1. Move Folder API Testing

**Test Case 1: Move Main Document**
```bash
# Should update folder_id and folder_ids
POST /api/documents/batch/move-folder
{
  "document_ids": [85],  # Main document
  "target_folder_id": 61
}
```

**Test Case 2: Move Secondary Document**
```bash
# Should NOT update folder_id, only folder_ids and parent_document_id
POST /api/documents/batch/move-folder
{
  "document_ids": [86],  # Secondary document
  "target_folder_id": 61
}
```

**Test Case 3: Move Multiple Mixed Documents**
```bash
POST /api/documents/batch/move-folder
{
  "document_ids": [85, 86, 87],  # Mix of main and secondary
  "target_folder_id": 61
}
```

### 2. Document Role Key Testing

**Test Case 1: List Documents**
```bash
POST /api/documents
# Verify response includes: is_main_document, document_role, relation_type
```

**Test Case 2: Get Single Document**
```bash
POST /api/documents/85
# Verify response includes the new fields
```

### 3. Auto-Folder Deletion Testing

**Test Case 1: Delete Main Document with Empty Folder**
```bash
# 1. Create folder with only main document
# 2. Delete main document
# 3. Verify folder is auto-deleted
POST /api/documents/85/trash
```

**Test Case 2: Delete Main Document with Other Documents**
```bash
# 1. Create folder with main + secondary documents
# 2. Delete main document
# 3. Verify folder is NOT deleted (has secondary documents)
POST /api/documents/85/trash
```

### 4. Duplicate Name Validation Testing

**Test Case 1: Create Duplicate Name**
```bash
# Should return error
POST /api/documents/upload
{
  "title": "existing-document.pdf",
  "department_id": 4,
  "document_type_id": 5
}
```

**Test Case 2: Create Same Name in Different Department**
```bash
# Should succeed
POST /api/documents/upload
{
  "title": "existing-document.pdf",
  "department_id": 5,  # Different department
  "document_type_id": 5
}
```

---

## Deployment Notes

1. **Restart Odoo Service:** Required after model changes
2. **No Database Migration:** Changes are code-only
3. **No Cache Clear:** Not required unless experiencing issues
4. **Monitoring:** Check logs for auto-folder deletion messages

---

## Error Codes & Messages

### Move Folder API
- `Target folder not found` - Target folder doesn't exist
- `Document {id} not found` - Document doesn't exist
- `Document {id} already in target folder` - Already in target

### Document Creation
- `A document with the name "XXX" already exists in this department and document type. Please use a different name.` - Duplicate name validation

---

## Log Messages

### Move Operation
```
[MOVE] Doc 86 is secondary - updating parent to target main doc
[MOVE] Set parent_document_id to 85
[MOVE] ✓ After: Doc 86 folder_id=60, folder_ids=[61], parent=85
```

### Auto-Folder Deletion
```
Auto-deleting empty folder 60 "HR-EMP_FILE-asd_846" after main document deletion
```

---

## Future Improvements

1. Add bulk document name validation API endpoint
2. Add configuration option to disable auto-folder deletion
3. Add undo functionality for folder moves
4. Add audit trail for folder auto-deletions

---

## Support

If you encounter any issues:
1. Check Odoo logs for detailed error messages
2. Verify document role fields in API response
3. Check folder document count before/after deletion
4. Verify parent_document_id updates correctly after move
