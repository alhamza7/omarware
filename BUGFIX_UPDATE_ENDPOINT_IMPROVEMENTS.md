# Bug Fix: Update Endpoint Improvements

## Date: 2026-02-14

## Issues Fixed

### 1. Accept "title" Field ✓

**Problem:**
Frontend was sending `"title"` but backend only accepted `"name"`.

**Solution:**
Endpoint now accepts both `"title"` and `"name"` fields and maps them to the document's `name` field.

```python
# Accept both 'name' and 'title'
if 'name' in data:
    vals['name'] = data['name']
elif 'title' in data:
    vals['name'] = data['title']
```

---

### 2. Update folder_id ✓

**Problem:**
Cannot update the folder a document belongs to.

**Solution:**
Added `folder_id` to updatable fields. When updated:
- Updates `folder_id` (Many2one)
- Updates `folder_ids` (Many2many) to maintain consistency

```python
if 'folder_id' in data:
    if data['folder_id']:
        vals['folder_id'] = data['folder_id']
        vals['folder_ids'] = [(6, 0, [data['folder_id']])]
    else:
        vals['folder_id'] = False
        vals['folder_ids'] = [(5, 0, 0)]  # Remove all folders
```

---

### 3. Return Full Document Data ✓

**Problem:**
Response only returned minimal data (`id` and `name`).

**Solution:**
Now returns complete document data in response, matching the format of GET endpoints.

**Before:**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": 96,
    "name": "sec"
  }
}
```

**After:**
```json
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": 96,
    "title": "seccondaryEdited",
    "name": "seccondaryEdited",
    "department_id": 2,
    "department_name": "Sales",
    "document_type_id": 2,
    "document_type_name": "Invoice",
    "confidentiality_level": "internal",
    "folder_id": 74,
    "folder_name": "Sales-Invoice-2024",
    "barcode": "NBSNBS000096",
    "po_number": "PO-123",
    "bl_number": null,
    "container_number": null,
    "invoice_number": null,
    "envoy_number": null,
    "is_main_document": false,
    "document_role": "sub",
    "relation_type": "secondary_document"
  }
}
```

---

## Updated API Specification

### POST /api/documents/<document_id>/update

**Request Body:**
```json
{
  "title": "string (optional - mapped to name)",
  "name": "string (optional - alternative to title)",
  "confidentiality_level": "public|internal|confidential|strict (optional)",
  "folder_id": "integer (optional - updates document folder)",
  "po_number": "string (optional)",
  "bl_number": "string (optional)",
  "container_number": "string (optional)",
  "invoice_number": "string (optional)",
  "envoy_number": "string (optional)",
  "custom_fields": "object (optional)",
  "tag_ids": "array of integers (optional)"
}
```

**Response Fields:**
- `id` - Document ID
- `title` - Document title (same as name)
- `name` - Document name
- `department_id` - Department ID
- `department_name` - Department name
- `document_type_id` - Document type ID
- `document_type_name` - Document type name
- `confidentiality_level` - Confidentiality level
- `folder_id` - Folder ID (null if not in folder)
- `folder_name` - Folder name (null if not in folder)
- `barcode` - Document barcode
- `po_number` - Purchase order number
- `bl_number` - Bill of lading number
- `container_number` - Container number
- `invoice_number` - Invoice number
- `envoy_number` - Envoy number
- `is_main_document` - Boolean indicating if main document
- `document_role` - Document role (main/sub/attachment/other)
- `relation_type` - Relation type (main/secondary_document/attachment/other)

---

## Example Requests

### Update Title and Folder
```bash
curl -X POST http://localhost:8070/api/documents/96/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Document Title",
    "folder_id": 74,
    "confidentiality_level": "confidential"
  }'
```

### Update Reference Numbers
```bash
curl -X POST http://localhost:8070/api/documents/96/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "po_number": "PO-2024-001",
    "invoice_number": "INV-2024-123",
    "container_number": "CONT-456"
  }'
```

### Move to Different Folder
```bash
curl -X POST http://localhost:8070/api/documents/96/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": 80
  }'
```

### Remove from Folder
```bash
curl -X POST http://localhost:8070/api/documents/96/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "folder_id": null
  }'
```

---

## Frontend Integration

### JavaScript/TypeScript Example

```javascript
async function updateDocument(documentId, updates) {
  try {
    const response = await fetch(`/api/documents/${documentId}/update`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log('Document updated:', result.data);
      // Result.data now contains full document info
      displayDocument(result.data);
      return result.data;
    } else {
      console.error('Update failed:', result.error);
      showError(result.error);
      return null;
    }
  } catch (error) {
    console.error('Request failed:', error);
    showError('Network error');
    return null;
  }
}

// Usage examples
updateDocument(96, {
  title: 'New Title',
  folder_id: 74
});

updateDocument(96, {
  confidentiality_level: 'confidential',
  po_number: 'PO-2024-001'
});
```

### React Example

```jsx
const UpdateDocumentForm = ({ documentId, onSuccess }) => {
  const [formData, setFormData] = useState({
    title: '',
    folder_id: null,
    confidentiality_level: 'internal'
  });
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const response = await fetch(`/api/documents/${documentId}/update`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });
    
    const result = await response.json();
    
    if (result.success) {
      onSuccess(result.data);
      toast.success('Document updated successfully');
    } else {
      toast.error(result.error);
    }
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={formData.title}
        onChange={e => setFormData({...formData, title: e.target.value})}
        placeholder="Document Title"
      />
      <select
        value={formData.folder_id || ''}
        onChange={e => setFormData({...formData, folder_id: parseInt(e.target.value)})}
      >
        <option value="">No Folder</option>
        {folders.map(f => (
          <option key={f.id} value={f.id}>{f.name}</option>
        ))}
      </select>
      <button type="submit">Update</button>
    </form>
  );
};
```

---

## Field Mapping Reference

| Frontend Field | Backend Field | Notes |
|---------------|---------------|-------|
| `title` | `name` | Preferred field name |
| `name` | `name` | Alternative (for consistency) |
| `folder_id` | `folder_id` + `folder_ids` | Updates both relations |
| `confidentiality_level` | `confidentiality_level` | Must be valid value |
| `po_number` | `po_number` | Purchase Order |
| `bl_number` | `bl_number` | Bill of Lading |
| `container_number` | `container_number` | Container |
| `invoice_number` | `invoice_number` | Invoice |
| `envoy_number` | `envoy_number` | Envoy |

---

## Validation & Constraints

### Cannot Update (Security/Integrity)
- `department_id` - Cannot change department (use transfer endpoint)
- `document_type_id` - Cannot change type (structural integrity)
- `state` - Use archive/unarchive endpoints
- `barcode` - System-generated, immutable
- `uploader_id` - Historical record, immutable
- `upload_date` - Historical record, immutable

### Can Update
- ✅ `title`/`name` - Document title
- ✅ `folder_id` - Move to different folder
- ✅ `confidentiality_level` - Change access level
- ✅ Reference numbers (PO, BL, Container, Invoice, Envoy)
- ✅ `custom_fields` - Dynamic fields
- ✅ `tag_ids` - Document tags

---

## Consistency Features

### Folder Synchronization
When `folder_id` is updated:
1. Updates `folder_id` (Many2one) - Primary folder reference
2. Updates `folder_ids` (Many2many) - Multi-folder relationships
3. Maintains data consistency across both fields

### Null Handling
Setting `folder_id: null`:
- Clears `folder_id`
- Removes all entries from `folder_ids`
- Document becomes "standalone" (not in any folder)

---

## Testing Checklist

- [x] Update with `title` field works
- [x] Update with `name` field works
- [x] Update `folder_id` works
- [x] Response includes all document fields
- [x] Response includes `folder_name`
- [x] Response includes document role fields
- [ ] Test with invalid folder_id (should fail gracefully)
- [ ] Test null folder_id (should remove from folder)
- [ ] Test updating multiple fields at once
- [ ] Verify audit log is created

---

## Files Modified

1. `addons/nbs_archive/controllers/document_controller.py`
   - Enhanced `update_document()` endpoint
   - Added `title` → `name` mapping
   - Added `folder_id` update support
   - Returns full document data

---

## Deployment Status

- ✅ Code updated
- ✅ Odoo restarted (PID: 1480119)
- ✅ Service responding
- ✅ Ready for testing

**Version:** 1.4  
**Date:** 2026-02-14  
**Status:** Deployed and Active
