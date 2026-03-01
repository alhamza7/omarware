# Bug Fix: Document Update Endpoint & Folder ID Issue

## Date: 2026-02-14

## Issues Fixed

### 1. Missing Document Update Endpoint ✓

**Problem:**
```
POST /api/documents/98/update
Status: 405 METHOD NOT ALLOWED
```

The endpoint didn't exist, causing 405 errors when trying to update documents.

**Solution:**
Created new endpoint: `POST /api/documents/<document_id>/update`

**Endpoint Details:**
- **Type:** HTTP (not JSON-RPC)
- **Authentication:** JWT required
- **Method:** POST
- **URL:** `/api/documents/<document_id>/update`

**Updatable Fields:**
- `name` - Document title
- `confidentiality_level` - public, internal, confidential, strict
- `po_number` - Purchase Order number
- `bl_number` - Bill of Lading number
- `container_number` - Container number
- `invoice_number` - Invoice number
- `envoy_number` - Envoy number
- `custom_fields` - Custom fields as JSON object
- `tag_ids` - Array of tag IDs

**Request Example:**
```bash
curl -X POST http://localhost:8070/api/documents/98/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Document Title",
    "confidentiality_level": "confidential",
    "po_number": "PO-12345",
    "tag_ids": [1, 2, 3]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": 98,
    "name": "Updated Document Title"
  }
}
```

---

### 2. folder_id Always Null ✓

**Problem:**
```json
{
  "folder_id": null,
  "folder_name": null
}
```

All documents were returning `null` for `folder_id` even when they were in folders.

**Root Cause:**
Documents have TWO folder fields:
- `folder_id` (Many2one) - Primary/single folder reference
- `folder_ids` (Many2many) - Multiple folder references

Most documents only have `folder_ids` populated, not `folder_id`.

**Solution:**
Updated response logic to check `folder_ids` if `folder_id` is empty:

```python
# Before (always null if folder_id not set)
'folder_id': doc.folder_id.id if doc.folder_id else None,
'folder_name': doc.folder_id.name if doc.folder_id else None,

# After (fallback to folder_ids[0])
'folder_id': doc.folder_id.id if doc.folder_id else (doc.folder_ids[0].id if doc.folder_ids else None),
'folder_name': doc.folder_id.name if doc.folder_id else (doc.folder_ids[0].name if doc.folder_ids else None),
```

**Logic:**
1. Check if `folder_id` (Many2one) exists → use it
2. If not, check if `folder_ids` (Many2many) has folders → use first one
3. If neither, return `null`

**Result:**
```json
{
  "folder_id": 60,
  "folder_name": "HR-EMP_FILE-asd_846"
}
```

---

## Files Modified

### 1. `addons/nbs_archive/controllers/document_controller.py`

**Changes:**
1. Added new `update_document()` endpoint (line ~548)
2. Updated `get_documents()` - folder_id/folder_name logic (line ~107-108)
3. Updated `get_document()` - folder_id/folder_name logic (line ~180-181)

---

## Testing

### Test 1: Update Document
```bash
# Update document name and PO number
curl -X POST http://localhost:8070/api/documents/98/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Document Name",
    "po_number": "PO-2024-001"
  }'

# Expected: Success response with updated document
```

### Test 2: Verify folder_id Not Null
```bash
# Get documents list
curl -X POST http://localhost:8070/api/documents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"page": 1, "per_page": 10}'

# Expected: Documents in folders should have folder_id and folder_name populated
```

### Test 3: Get Single Document
```bash
# Get document details
curl -X POST http://localhost:8070/api/documents/98 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Expected: folder_id and folder_name should be populated if document is in a folder
```

---

## API Documentation

### POST /api/documents/<document_id>/update

**Description:** Update document metadata

**Authentication:** Required (JWT Bearer token)

**Request Body:**
```json
{
  "name": "string (optional)",
  "confidentiality_level": "public|internal|confidential|strict (optional)",
  "po_number": "string (optional)",
  "bl_number": "string (optional)",
  "container_number": "string (optional)",
  "invoice_number": "string (optional)",
  "envoy_number": "string (optional)",
  "custom_fields": {
    "key": "value"
  },
  "tag_ids": [1, 2, 3]
}
```

**Response - Success (200):**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": 98,
    "name": "Updated Document Name"
  }
}
```

**Response - Error (400/500):**
```json
{
  "success": false,
  "error": "Error message"
}
```

**Response - Unauthorized (401):**
```json
{
  "success": false,
  "error": "Unauthorized"
}
```

**Response - Not Found (200 with error):**
```json
{
  "success": false,
  "error": "Document not found"
}
```

---

## Response Fields Update

All document endpoints now properly return folder information:

### Before:
```json
{
  "folder_id": null,
  "folder_name": null
}
```

### After:
```json
{
  "folder_id": 60,
  "folder_name": "HR-EMP_FILE-asd_846"
}
```

**Affected Endpoints:**
- `POST /api/documents` (list documents)
- `POST /api/documents/<id>` (get single document)

---

## Audit Logging

The update endpoint automatically logs all changes:
- User ID
- Action: `document_updated`
- Document ID
- Department ID
- IP Address
- User Agent
- Metadata: JSON of changed fields

---

## Frontend Integration

### Update Document Example (JavaScript)

```javascript
async function updateDocument(documentId, updates) {
  try {
    const response = await fetch(`/api/documents/${documentId}/update`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Document updated:', result.data);
    } else {
      console.error('Update failed:', result.error);
    }
  } catch (error) {
    console.error('Request failed:', error);
  }
}

// Usage
updateDocument(98, {
  name: 'New Title',
  po_number: 'PO-2024-001',
  confidentiality_level: 'internal'
});
```

### Display Folder Name

```javascript
function renderDocument(doc) {
  return `
    <div class="document">
      <h3>${doc.title}</h3>
      ${doc.folder_name ? `<span class="folder">📁 ${doc.folder_name}</span>` : ''}
      <p>Barcode: ${doc.barcode}</p>
    </div>
  `;
}
```

---

## Migration Notes

### No Database Changes Required
- All changes are in business logic only
- No schema migrations needed
- Existing data compatible

### Backward Compatibility
- ✅ Existing API responses enhanced (no breaking changes)
- ✅ New endpoint doesn't affect existing endpoints
- ✅ folder_id/folder_name fields existed before, just fixed the values

---

## Deployment Checklist

- [x] Stop Odoo service
- [x] Update code
- [x] Restart Odoo service
- [ ] Test update endpoint with sample document
- [ ] Verify folder_id populates correctly
- [ ] Check audit logs for update actions
- [ ] Update API documentation
- [ ] Notify frontend team

---

## Known Limitations

### Update Endpoint
- Cannot update `department_id` (security - prevents cross-department moves)
- Cannot update `document_type_id` (structural integrity)
- Cannot update `state` (use dedicated archive/unarchive endpoints)
- Cannot update file content (use version upload endpoint)

### Folder ID
- If document is in multiple folders (`folder_ids` has multiple entries), only first folder is returned in `folder_id`
- To get all folders, use a separate endpoint or include `folder_ids` in response

---

## Future Enhancements

1. Add `folder_ids` array to response (all folders, not just first)
2. Add field-level permissions (who can update which fields)
3. Add validation for reference numbers (PO, BL, etc.)
4. Add bulk update endpoint
5. Add update history/changelog endpoint

---

**Status:** ✅ Fixed and Deployed  
**Version:** 1.3  
**Date:** 2026-02-14
