# NBS Archive — REST API Documentation

**Base URL:** `http://<server>:3003`  
**Auth:** All endpoints require `Authorization: Bearer <jwt_token>`  
**Date:** 2026-04-20

---

## Authentication

### Login
```
POST /api/auth/login
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "username": "admin",
    "password": "admin"
  },
  "id": 1
}
```
**Response:**
```json
{
  "result": {
    "success": true,
    "token": "eyJ...",
    "user": { "id": 2, "name": "Administrator", "email": "admin@example.com" }
  }
}
```

---

## Document Upload

### ✅ Single-Call Multi-File Upload (NEW — Recommended)

Upload all files in **one request**. No need for start/upload/finalize steps.

```
POST /api/documents/bulk-upload/upload
Content-Type: multipart/form-data
Authorization: Bearer <token>
```

**Form fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `department_id` | int | ✅ | Target department ID |
| `document_type_id` | int | ✅ | Document type ID |
| `company_id` | int | — | Company/brand ID |
| `confidentiality_level` | string | — | `internal` / `confidential` / `public` (default: `internal`) |
| `create_folder_per_file` | bool | — | Create a folder for each file (default: `true`) |
| `auto_ocr` | bool | — | Run OCR on files after upload (default: `true`) |
| `file` | File | ✅ | Repeat this field for each file |

**JavaScript example:**
```javascript
async function uploadDocuments(files, token) {
  const fd = new FormData();
  fd.append('department_id', '4');
  fd.append('document_type_id', '5');
  fd.append('company_id', '7437');
  fd.append('auto_ocr', 'true');
  fd.append('create_folder_per_file', 'true');

  // Add ALL files using the same field name "file"
  for (const file of files) {
    fd.append('file', file);
  }

  const resp = await fetch('/api/documents/bulk-upload/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    // Do NOT set Content-Type manually — browser sets it with boundary
    body: fd,
  });
  return resp.json();
}
```

**Response:**
```json
{
  "success": true,
  "job_id": "2eb93cd3-54bd-4178-b21f-1a58bb93ba75",
  "status": "completed",
  "total": 3,
  "successful": 3,
  "failed": 0,
  "error_log": null,
  "documents": [
    {
      "file_name": "invoice-april.pdf",
      "success": true,
      "document_id": 123,
      "folder_id": 45,
      "error": null
    },
    {
      "file_name": "contract.xlsx",
      "success": true,
      "document_id": 124,
      "folder_id": 46,
      "error": null
    }
  ]
}
```

---

### Legacy 3-Step Upload (kept for backward compatibility)

> Use the single-call endpoint above instead. These endpoints remain available.

#### Step 1 — Create Job
```
POST /api/documents/bulk-upload/start
Content-Type: application/json

{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "department_id": 4,
    "document_type_id": 5,
    "company_id": 7437,
    "total_files": 3,
    "create_folder_per_file": true,
    "confidentiality_level": "internal",
    "auto_ocr": true
  }, "id": 1
}
```
Returns: `{ "result": { "data": { "job_id": "...", "id": 10 } } }`

#### Step 2 — Upload One File
```
POST /api/documents/bulk-upload/{job_id}/upload-file
Content-Type: multipart/form-data   OR   raw binary
Authorization: Bearer <token>
```

Three upload modes (most reliable → least):

**Mode A — Raw Binary (bypasses all axios interceptors):**
```javascript
fetch(url, {
  method: 'POST',
  headers: {
    'Content-Type': file.type || 'application/octet-stream',
    'X-File-Name': file.name,
    'X-Doc-Name': file.name.replace(/\.[^.]+$/, ''),
    'Authorization': `Bearer ${token}`,
  },
  body: file,  // raw File object
})
```

**Mode B — FormData:**
```javascript
const fd = new FormData();
fd.append('file', file);
fd.append('file_name', file.name);
fetch(url, { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: fd });
```

**Mode C — JSON + Base64:**
```javascript
const reader = new FileReader();
reader.readAsDataURL(file);
reader.onload = () => {
  fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ file_data: reader.result, file_name: file.name }),
  });
};
```

#### Step 3 — Finalize
```
POST /api/documents/bulk-upload/{job_id}/finalize
{ "jsonrpc": "2.0", "method": "call", "params": {}, "id": 1 }
```

---

## OCR — Text Extraction

OCR runs **automatically** on every uploaded file when `auto_ocr: true`.  
Supported formats:

| Format | Engine |
|--------|--------|
| PDF | Google Cloud Vision API |
| JPEG, PNG, BMP, WEBP, GIF, TIFF | Google Cloud Vision API |
| XLSX, XLS, ODS | openpyxl / xlrd (direct, free) |
| CSV, TXT | Direct decode (free) |

### Check OCR Provider Status
```
POST /api/ocr/test
{ "jsonrpc": "2.0", "method": "call", "params": {}, "id": 1 }
```
Response:
```json
{
  "result": {
    "success": true,
    "data": {
      "provider": "Google Cloud Vision API",
      "key_configured": true
    }
  }
}
```

### Run OCR on a Single Document
```
POST /api/ocr/run/{document_id}
{ "jsonrpc": "2.0", "method": "call", "params": {}, "id": 1 }
```
Response:
```json
{
  "result": {
    "success": true,
    "data": {
      "document_id": 123,
      "ok": true,
      "ocr_status": "completed",
      "ocr_text_length": 1842
    }
  }
}
```

### Backfill OCR for All Existing Files (NEW)

Run OCR on all documents that don't have extracted text yet.  
Call repeatedly until `remaining` is `0`.

```
POST /api/ocr/backfill
Content-Type: application/json

{
  "jsonrpc": "2.0", "method": "call",
  "params": { "limit": 50 },
  "id": 1
}
```
Response:
```json
{
  "result": {
    "success": true,
    "processed": 50,
    "successful": 48,
    "failed": 2,
    "remaining": 120,
    "results": [
      { "document_id": 5, "name": "Invoice April", "success": true, "chars": 842 },
      { "document_id": 6, "name": "Contract XYZ",  "success": false, "error": "..." }
    ]
  }
}
```

**Run full backfill in a loop:**
```javascript
async function runFullBackfill(token) {
  let remaining = 1;
  while (remaining > 0) {
    const resp = await fetch('/api/ocr/backfill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { limit: 50 }, id: 1 }),
    }).then(r => r.json());

    const data = resp.result;
    console.log(`Processed: ${data.processed}, Remaining: ${data.remaining}`);
    remaining = data.remaining;

    if (remaining > 0) await new Promise(r => setTimeout(r, 1000)); // 1s pause between batches
  }
  console.log('Backfill complete');
}
```

---

## Search

Search works across document metadata **AND** full OCR-extracted text simultaneously.

### Global Search
```
POST /api/search/global
Content-Type: application/json

{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "query": "INV-2026-001",
    "page": 1,
    "per_page": 20
  }, "id": 1
}
```
Response includes `ocr_snippet` — a highlighted excerpt from the document's OCR text:
```json
{
  "result": {
    "success": true,
    "data": [
      {
        "entity_type": "document",
        "id": 123,
        "title": "Invoice April 2026",
        "department_name": "Finance",
        "document_type_name": "Invoice",
        "upload_date": "2026-04-19T10:30:00",
        "ocr_status": "completed",
        "ocr_snippet": "…Invoice No. INV-2026-001 dated 2026-04-01 Amount: 15,000…"
      },
      {
        "entity_type": "folder",
        "id": 45,
        "title": "SOZIO Contracts"
      }
    ],
    "pagination": { "total": 1, "page": 1, "per_page": 20 }
  }
}
```

### Document Search (with filters)
```
POST /api/search
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "query": "SOZIO",
    "department_id": 4,
    "document_type_id": 5,
    "date_from": "2026-01-01",
    "date_to": "2026-12-31",
    "page": 1,
    "per_page": 20
  }, "id": 1
}
```

---

## Companies

### List Companies
```
POST /api/companies
{ "jsonrpc": "2.0", "method": "call",
  "params": { "search": "SOZIO", "limit": 100, "offset": 0 }, "id": 1 }
```
Response:
```json
{
  "result": {
    "success": true,
    "companies": [
      { "id": 7432, "name": "SOZIO", "phone": null, "email": null }
    ],
    "count": 1,
    "total": 1,
    "offset": 0,
    "limit": 100
  }
}
```

### Create Company
```
POST /api/companies/create
{ "jsonrpc": "2.0", "method": "call",
  "params": { "name": "New Brand", "phone": "+9661234567", "email": "info@brand.com" },
  "id": 1 }
```

### Batch Delete Companies
```
POST /api/companies/batch-delete
Content-Type: application/json

{ "ids": [7432, 7433], "force": false }
```

### Delete All Companies
```
POST /api/companies/delete-all
Content-Type: application/json

{ "force": false }
```
> Set `force: true` to delete companies even if they have linked folders.

---

## Progress Tracking

### Get Upload Job Progress
```
POST /api/documents/bulk-upload/{job_id}/progress
{ "jsonrpc": "2.0", "method": "call", "params": {}, "id": 1 }
```
Response:
```json
{
  "result": {
    "success": true,
    "data": {
      "job_id": "2eb93cd3...",
      "status": "processing",
      "total_files": 38,
      "processed_files": 15,
      "successful_files": 15,
      "failed_files": 0,
      "progress_percentage": 39.47
    }
  }
}
```

---

## Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| `200` | Success |
| `400` | Bad request (missing required fields, invalid data) |
| `401` | Unauthorized — missing or expired JWT token |
| `404` | Resource not found |
| `500` | Internal server error |

---

## What's New (April 2026)

| # | Change |
|---|--------|
| ✅ | **Single-call upload** — `POST /api/documents/bulk-upload/upload` accepts all files in one request |
| ✅ | **Auto-OCR on every upload** — any file uploaded through any endpoint gets OCR'd automatically |
| ✅ | **OCR backfill** — `POST /api/ocr/backfill` processes all existing files without OCR text |
| ✅ | **Search in OCR content** — `/api/search` and `/api/search/global` now search inside extracted text |
| ✅ | **`ocr_snippet`** in search results — highlighted text excerpt around the search keyword |
| ✅ | **Excel support** — `.xlsx`, `.xls`, `.ods` text extracted without calling the Vision API |
