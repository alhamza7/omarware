# Bug Fix: Document Role Logic Correction

## Date: 2026-02-14 (Second Update)

## Issue
After initial implementation, the `is_main_document` field was showing `true` for ALL documents because the logic only checked `parent_document_id`, which many documents don't have set.

## Root Cause
The system uses BOTH `parent_document_id` AND `folder_role` to determine document type:
- Documents with `folder_role = 'main'` are main documents
- Documents with `folder_role = 'sub'` are secondary documents  
- Documents with `folder_role = 'attachment'` are attachments
- Documents with `folder_role = 'other'` or NULL need additional logic

The initial fix only checked `parent_document_id`, missing the `folder_role` field.

## Solution

### Updated Logic for `is_main_document`:
```python
is_main_document = (
    doc.folder_role == 'main' or 
    (not doc.parent_document_id and doc.folder_role not in ('sub', 'attachment'))
)
```

**Breakdown:**
- If `folder_role == 'main'` → Main document ✓
- If no `parent_document_id` AND `folder_role` is NOT 'sub' or 'attachment' → Main document ✓
- Otherwise → Secondary document ✓

### Updated Logic for `document_role`:
```python
document_role = doc.folder_role or 'other'
```

**Simpler:** Just return the actual `folder_role` value, or 'other' if not set.

### Updated Logic for `relation_type`:
```python
relation_type = (
    'attachment' if (doc.parent_document_id and doc.is_attachment) or doc.folder_role == 'attachment'
    else 'secondary_document' if doc.parent_document_id or doc.folder_role == 'sub'
    else 'main'
)
```

**Breakdown:**
- If has parent AND is_attachment flag, OR folder_role='attachment' → 'attachment'
- Else if has parent_document_id OR folder_role='sub' → 'secondary_document'
- Otherwise → 'main'

## Files Modified
- `addons/nbs_archive/controllers/document_controller.py`
  - Updated `get_documents()` endpoint (line ~110-112)
  - Updated `get_document()` endpoint (line ~175-177)
  - Updated `list_trash()` endpoint (line ~1030-1032)

## Examples

### Main Document
```json
{
  "folder_role": "main",
  "parent_document_id": null,
  "is_main_document": true,
  "document_role": "main",
  "relation_type": "main"
}
```

### Secondary Document
```json
{
  "folder_role": "sub",
  "parent_document_id": 123,
  "is_main_document": false,
  "document_role": "sub",
  "relation_type": "secondary_document"
}
```

### Attachment Document
```json
{
  "folder_role": "attachment",
  "parent_document_id": 123,
  "is_attachment": true,
  "is_main_document": false,
  "document_role": "attachment",
  "relation_type": "attachment"
}
```

### Legacy Document (no folder_role set)
```json
{
  "folder_role": null,
  "parent_document_id": null,
  "is_main_document": true,
  "document_role": "other",
  "relation_type": "main"
}
```

## Testing

After restart, verify:

1. **Main documents** show `is_main_document: true`
2. **Sub documents** show `is_main_document: false` and `document_role: "sub"`
3. **Attachments** show `is_main_document: false` and `document_role: "attachment"`
4. **Legacy documents** (no folder_role) show `document_role: "other"`

## Impact
- ✅ Correctly identifies main vs secondary documents
- ✅ Uses both `folder_role` and `parent_document_id` fields
- ✅ Backward compatible with documents that don't have folder_role set
- ✅ No database changes required
- ✅ All endpoints updated consistently

## Deployment
1. Stop Odoo: `pkill -f "odoo-bin -c odoo_local.conf"`
2. Start Odoo: `bash start_local.sh`
3. Test document list API to verify correct values
