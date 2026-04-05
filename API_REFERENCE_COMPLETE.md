# 📚 NBS Archive - Complete API Reference v2.0.0

## جميع APIs (62+)

---

## 📄 1. Documents APIs (8)

### 1.1 List Documents
```http
POST /api/documents
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "token": "your_jwt_token"
  }
}
```

### 1.2 Get Document
```http
POST /api/documents/<int:document_id>
```

### 1.3 Create Document
```http
POST /api/documents/create
{
  "name": "Document Name",
  "department_id": 1,
  "document_type_id": 1
}
```

### 1.4 Update Document
```http
POST /api/documents/<int:document_id>/update
```

### 1.5 Move to Trash
```http
POST /api/documents/<int:document_id>/trash
{
  "reason": "Optional reason"
}
```

### 1.6 Restore from Trash
```http
POST /api/documents/<int:document_id>/restore
```

### 1.7 Permanent Delete
```http
DELETE /api/documents/<int:document_id>/permanent
```

### 1.8 List Trash
```http
POST /api/documents/trash
```

---

## 📎 2. Attachments APIs (8)

### 2.1 List Attachments
```http
POST /api/documents/<int:document_id>/attachments
```

### 2.2 Add Single Attachment
```http
POST /api/documents/<int:document_id>/add-attachment
{
  "file_name": "file.pdf",
  "file_data": "base64_encoded_data",
  "description": "Optional"
}
```

### 2.3 Add Multiple Attachments
```http
POST /api/documents/<int:document_id>/attachments/multiple
{
  "attachments": [
    {
      "file_name": "file1.pdf",
      "file_data": "base64_data1"
    },
    {
      "file_name": "file2.pdf",
      "file_data": "base64_data2"
    }
  ]
}
```

### 2.4 Update Attachment
```http
POST /api/documents/<doc_id>/attachments/<att_id>/update
{
  "name": "New Name",
  "description": "New description"
}
```

### 2.5 Delete Attachment (Soft)
```http
DELETE /api/documents/<doc_id>/attachments/<att_id>
{
  "reason": "Optional reason"
}
```

### 2.6 Restore Attachment
```http
POST /api/documents/<doc_id>/attachments/<att_id>/restore
```

### 2.7 Permanent Delete
```http
DELETE /api/documents/<doc_id>/attachments/<att_id>/permanent
```

### 2.8 Download Attachment
```http
GET /api/documents/<doc_id>/attachments/<att_id>/download
```

---

## 📤 3. Bulk Upload APIs (5)

### 3.1 Start Bulk Upload
```http
POST /api/documents/bulk-upload/start
{
  "department_id": 1,
  "document_type_id": 1,
  "folder_id": 2,
  "auto_ocr": true
}
```
**Response:** `{ "job_id": 123 }`

### 3.2 Upload Files
```http
POST /api/documents/bulk-upload/<job_id>/upload
{
  "files": [
    {
      "name": "doc1.pdf",
      "data": "base64_data"
    }
  ]
}
```

### 3.3 Get Progress
```http
POST /api/documents/bulk-upload/<job_id>/progress
```
**Response:** `{ "progress": 75, "total": 10, "completed": 7 }`

### 3.4 Cancel Upload
```http
POST /api/documents/bulk-upload/<job_id>/cancel
```

### 3.5 List Jobs
```http
POST /api/documents/bulk-upload/jobs
```

---

## 📁 4. Folders APIs (7)

### 4.1 List Folders
```http
POST /api/folders
{
  "department_id": 1,
  "parent_id": null
}
```

### 4.2 Get Folder
```http
POST /api/folders/<int:folder_id>
```

### 4.3 Create Folder
```http
POST /api/folders/create
{
  "name": "Folder Name",
  "parent_id": null,
  "department_id": 1
}
```

### 4.4 Update Folder
```http
POST /api/folders/<int:folder_id>/update
{
  "name": "New Name"
}
```

### 4.5 Delete Folder
```http
DELETE /api/folders/<int:folder_id>
```

### 4.6 Move Folder
```http
POST /api/folders/<int:folder_id>/move
{
  "new_parent_id": 5
}
```

### 4.7 Get Folder Tree
```http
POST /api/folders/tree
```
**Response:** Hierarchical tree structure

---

## 🔍 5. Advanced Search API (1)

### 5.1 Advanced Search
```http
POST /api/search/advanced
{
  "query": "search term",
  "department_ids": [1, 2],
  "document_type_ids": [3],
  "folder_ids": [5],
  "date_from": "2026-01-01",
  "date_to": "2026-12-31",
  "state": "active",
  "confidentiality": "internal",
  "uploader_ids": [10]
}
```

---

## 📋 6. Templates APIs (2)

### 6.1 List Templates
```http
POST /api/templates
{
  "department_id": 1
}
```

### 6.2 Create Document from Template
```http
POST /api/templates/<int:template_id>/create-document
```

---

## 🔄 7. Batch Operations APIs (3)

### 7.1 Batch Archive
```http
POST /api/documents/batch/archive
{
  "document_ids": [1, 2, 3, 4]
}
```

### 7.2 Batch Trash
```http
POST /api/documents/batch/trash
{
  "document_ids": [5, 6, 7],
  "reason": "Cleanup"
}
```

### 7.3 Batch Move Folder
```http
POST /api/documents/batch/move-folder
{
  "document_ids": [8, 9],
  "target_folder_id": 10
}
```

---

## 🏢 8. Department Management APIs (5)

### 8.1 List Departments
```http
POST /api/departments
```

### 8.2 Get Department
```http
POST /api/departments/<int:department_id>
```

### 8.3 Create Department
```http
POST /api/departments/create
{
  "name": "Department Name",
  "code": "DEPT001",
  "description": "Optional"
}
```

### 8.4 Update Department
```http
POST /api/departments/<int:department_id>/update
```

### 8.5 Delete Department
```http
DELETE /api/departments/<int:department_id>
```

---

## 📚 9. Document Type APIs (5)

### 9.1 List Document Types
```http
POST /api/document-types
```

### 9.2 Get Document Type
```http
POST /api/document-types/<int:type_id>
```

### 9.3 Create Document Type
```http
POST /api/document-types/create
{
  "name": "Type Name",
  "code": "TYPE001"
}
```

### 9.4 Update Document Type
```http
POST /api/document-types/<int:type_id>/update
```

### 9.5 Delete Document Type
```http
DELETE /api/document-types/<int:type_id>
```

---

## 📱 10. Mobile APIs (2)

### 10.1 Mobile Sync
```http
POST /api/mobile/sync
{
  "last_sync_date": "2026-02-01T00:00:00"
}
```

### 10.2 Register Device
```http
POST /api/mobile/register
{
  "device_id": "unique_device_id",
  "device_type": "android",
  "fcm_token": "firebase_token"
}
```

---

## 📊 Total APIs Summary

```yaml
Documents:        8 APIs
Attachments:      8 APIs
Bulk Upload:      5 APIs
Folders:          7 APIs
Search:           1 API
Templates:        2 APIs
Batch Ops:        3 APIs
Departments:      5 APIs
Document Types:   5 APIs
Mobile:           2 APIs

TOTAL:           46 Core APIs ✅
```

Plus additional APIs for:
- Version Control
- Workflow Management
- OCR Processing
- Notifications
- Analytics
- Permissions
- Sharing

**Grand Total: 62+ APIs ✅**

---

## 🔐 Authentication

All APIs require JWT token:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "token": "your_jwt_token_here",
    ...other params...
  }
}
```

---

## ✅ Status Codes

```
200 - Success
400 - Bad Request
401 - Unauthorized
404 - Not Found
500 - Server Error
```

---

## 📚 Related Documentation

- **START_HERE.md** - Quick start guide
- **ALL_WEEKS_COMPLETE.md** - Full implementation details
- **SYSTEM_ARCHITECTURE.md** - System architecture

---

**Version:** 2.0.0  
**Status:** Production Ready  
**Last Updated:** February 7, 2026
