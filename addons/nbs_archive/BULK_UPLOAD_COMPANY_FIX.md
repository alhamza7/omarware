# Bulk Upload Company_ID Fix - COMPLETE ✅

## 📋 Problem Report

When using bulk upload with `create_folder_per_file: true` and `company_id: 1`:
- ❌ Auto-created folders had NO `company_id`
- ❌ Documents had NO `company_id`
- ❌ Both showed `null` in API responses

---

## 🔍 Root Cause Analysis

### Issue 1: Controller didn't accept `company_id`
**File:** `controllers/bulk_upload_controller.py`

**Line 17-19 BEFORE:**
```python
def start_bulk_upload(self, department_id, document_type_id, folder_id=None, 
                     confidentiality_level='internal', auto_ocr=False, 
                     auto_barcode=False, create_folder_per_file=False, **kwargs):
```

The `company_id` parameter wasn't accepted, so it was ignored.

### Issue 2: Job model didn't store `company_id`
**File:** `models/nbs_bulk_upload.py`

The job model had no `company_id` field to store the company for later use.

### Issue 3: Folder creation didn't use `company_id`
**File:** `models/nbs_bulk_upload.py` line 175-182

When creating folders, no `company_id` was set:
```python
folder = self.env['nbs.document.folder'].create({
    'name': doc_name,
    'code': folder_code,
    'department_id': self.department_id.id,
    # ❌ Missing: 'company_id': ...
})
```

---

## ✅ The Complete Fix

### Fix 1: Added `company_id` parameter to controller
**File:** `controllers/bulk_upload_controller.py` line 17

**AFTER:**
```python
def start_bulk_upload(self, department_id, document_type_id, folder_id=None, 
                     confidentiality_level='internal', auto_ocr=False, 
                     auto_barcode=False, create_folder_per_file=False, 
                     company_id=None, **kwargs):  # ✅ ADDED
```

### Fix 2: Added `company_id` field to job model
**File:** `models/nbs_bulk_upload.py` line 58-63

**ADDED:**
```python
company_id = fields.Many2one(
    'res.partner',
    string='Company/Brand',
    domain="[('is_company', '=', True)]",
    help='Company for auto-created folders'
)
```

### Fix 3: Pass `company_id` to job creation
**File:** `controllers/bulk_upload_controller.py` line 43

**ADDED:**
```python
'company_id': company_id if company_id else False,
```

### Fix 4: Use `company_id` when creating folders
**File:** `models/nbs_bulk_upload.py` line 175-187

**BEFORE:**
```python
folder = self.env['nbs.document.folder'].create({
    'name': doc_name,
    'code': folder_code,
    'department_id': self.department_id.id,
    'description': f'Auto-created for {doc_name}',
    'owner_id': self.uploader_id.id,
    'active': True
})
```

**AFTER:**
```python
folder_vals = {
    'name': doc_name,
    'code': folder_code,
    'department_id': self.department_id.id,
    'description': f'Auto-created for {doc_name}',
    'owner_id': self.uploader_id.id,
    'active': True
}
# Set company_id if provided in job
if self.company_id:
    folder_vals['company_id'] = self.company_id.id

folder = self.env['nbs.document.folder'].create(folder_vals)
```

---

## 🧪 Test Results

**Test scenario:** Create bulk upload job with `company_id: 1`

```python
Job: company_id = 1 ✓
  └─ Creates Folder: company_id = 1 ✓
      └─ Creates Document: company_id = 1 ✓ (inherited from folder)
```

**Result:** ✅ SUCCESS!

```
📄 Document: Bulk Test 1
   ├─ folder_id: 202 ✓
   ├─ folder.company_id: 1 ✓
   ├─ doc.company_id: 1 ✓
   └─ doc.company_name: My Company ✓
```

---

## 🎯 How to Use (For FE)

### Start Bulk Upload with Company

**Request:**
```json
POST /api/documents/bulk-upload/start
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "department_id": 8,
    "document_type_id": 10,
    "create_folder_per_file": true,
    "company_id": 1,  // ✅ ADD THIS!
    "confidentiality_level": "internal",
    "auto_ocr": false,
    "auto_barcode": false
  },
  "id": 1
}
```

### Upload Files
Same as before - no changes needed:

```json
POST /api/documents/bulk-upload/{job_id}/upload
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "files": [
      {
        "file_name": "sample_2_report.pdf",
        "file_data": "base64...",
        "name": "sample_2_report",
        "description": ""
      }
    ]
  },
  "id": 1
}
```

### Result

**After upload completes:**

1. **Folders API** will show:
```json
{
  "id": 202,
  "name": "sample_2_report",
  "company_id": 1,         // ✅ Present!
  "company_name": "My Company"  // ✅ Present!
}
```

2. **Documents API** will show:
```json
{
  "id": 280,
  "name": "sample_2_report",
  "folder_id": 202,
  "company_id": 1,         // ✅ Present!
  "company_name": "My Company"  // ✅ Present!
}
```

---

## 📊 Status

| Component | Status |
|-----------|--------|
| Controller accepts company_id | ✅ Fixed |
| Job model stores company_id | ✅ Fixed |
| Folders created with company_id | ✅ Fixed |
| Documents inherit company_id | ✅ Fixed |
| Module updated | ✅ Done |
| Odoo restarted | ✅ Done (16:58) |
| Tested successfully | ✅ Yes |

---

## 🚀 Ready to Test

**The bulk upload with company_id is NOW WORKING!**

Try the same request again (after restart at 16:58):
- ✅ Folders will have `company_id` and `company_name`
- ✅ Documents will have `company_id` and `company_name`

**Test it now and you'll see the values!** 🎉

---

## 📝 Note

All previous bulk uploads (before 16:58) don't have company_id because the feature didn't exist yet. 

**New bulk uploads from NOW onwards will work correctly.** ✅
