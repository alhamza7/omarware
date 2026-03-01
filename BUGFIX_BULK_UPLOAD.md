# Bug Fix: Bulk Upload - Invalid Field 'description'

## 🐛 Issue

**Error:**
```
Invalid field 'description' in 'nbs.document'
```

**Endpoint:** `POST /api/documents/bulk-upload/<job_id>/upload`

**Result:** All 10 files failed to upload with the same error

---

## 🔍 Root Cause

The bulk upload code was trying to set a `description` field on `nbs.document` model, but this field doesn't exist.

**Problem code:**
```python
doc_vals = {
    'name': file_info.get('name') or file_info.get('file_name'),
    'description': file_info.get('description', ''),  # ❌ Field doesn't exist
    'department_id': self.department_id.id,
    ...
}
```

---

## ✅ Solution

Removed the `description` field from document creation in bulk upload.

**File:** `addons/nbs_archive/models/nbs_bulk_upload.py`

```python
# Fixed code
doc_vals = {
    'name': file_info.get('name') or file_info.get('file_name'),
    # 'description' removed - field doesn't exist on nbs.document
    'department_id': self.department_id.id,
    'document_type_id': self.document_type_id.id,
    'folder_id': self.folder_id.id if self.folder_id else False,
    'confidentiality_level': self.confidentiality_level,
    'state': 'active',
    'uploader_id': self.uploader_id.id,
}
```

**Note:** `description` is kept for attachments (line 171) because `nbs.document.attachment` DOES have a description field.

---

## 📋 Additional Fix: Bulk Upload Permissions

Also added missing access rights for bulk upload:

**File:** `addons/nbs_archive/security/ir.model.access.csv`

```csv
access_nbs_bulk_upload_job_user,nbs.bulk.upload.job.user,model_nbs_bulk_upload_job,group_nbs_user,1,1,1,0
access_nbs_bulk_upload_job_manager,nbs.bulk.upload.job.manager,model_nbs_bulk_upload_job,group_nbs_manager,1,1,1,0
access_nbs_bulk_upload_job_admin,nbs.bulk.upload.job.admin,model_nbs_bulk_upload_job,group_nbs_admin,1,1,1,1
```

---

## 🧪 Testing

### Step 1: Start Bulk Upload Job
```bash
curl -X POST "http://localhost:3003/api/documents/bulk-upload/start" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "department_id": 4,
      "document_type_id": 5,
      "folder_id": 60,
      "confidentiality_level": "internal",
      "auto_ocr": false,
      "auto_barcode": false
    },
    "id":1
  }'
```

**Expected:** ✅ Returns job_id

### Step 2: Upload Files
```bash
curl -X POST "http://localhost:3003/api/documents/bulk-upload/<job_id>/upload" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "files": [
        {
          "file_name": "document.pdf",
          "file_data": "base64_data...",
          "name": "Document Title"
        }
      ]
    },
    "id":1
  }'
```

**Expected:** ✅ Files upload successfully without 'description' field error

---

## 📊 Expected Results

### Before Fix
```json
{
  "status": "failed",
  "total": 10,
  "successful": 0,
  "failed": 10,
  "errors": [
    "File 1: Invalid field 'description' in 'nbs.document'",
    ...
  ]
}
```

### After Fix
```json
{
  "status": "completed",
  "total": 10,
  "successful": 10,
  "failed": 0,
  "errors": []
}
```

---

## 🔍 Technical Details

### nbs.document Model Fields

The `nbs.document` model does NOT have:
- ❌ `description` field

The model HAS:
- ✅ `name` - Document title
- ✅ `custom_fields_data` - JSON field for type-specific data
- ✅ Other standard fields

### nbs.document.attachment Model Fields

The `nbs.document.attachment` model HAS:
- ✅ `description` field
- ✅ `name` - Attachment name
- ✅ `file_name` - Original filename
- ✅ Other fields

So `description` can be used for attachments but NOT for documents.

---

## ✅ Status

- [x] Removed invalid description field from document creation
- [x] Kept description for attachment (valid field)
- [x] Added bulk upload access rights
- [x] Module updated
- [x] Odoo restarted

---

## 🚀 Result

Bulk upload now works correctly without field validation errors.

**Date:** February 12, 2026  
**Status:** ✅ Fixed and Ready  
**Odoo:** Running on 192.168.116.15:8070
