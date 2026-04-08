# NBS Archive API – Complete Reference for Frontend

This document is a **full API reference** for frontend developers integrating with the **nbs_archiving** (NBS Archive) backend. Use it to implement login, document list/upload/download, folders, search, attachments, and all other features.

---

## Table of Contents

1. [Base URL & Environment](#1-base-url--environment)
2. [Authentication](#2-authentication)
3. [Request Formats (Critical)](#3-request-formats-critical)
4. [Common Response & Errors](#4-common-response--errors)
5. [Documents](#5-documents)
6. [Folders](#6-folders)
7. [Search](#7-search)
8. [Attachments](#8-attachments)
9. [Departments & Document Types](#9-departments--document-types)
10. [Batch Operations](#10-batch-operations)
11. [Bulk Upload](#11-bulk-upload)
12. [Templates](#12-templates)
13. [Document Hierarchy & Relations](#13-document-hierarchy--relations)
14. [Trash & Archive](#14-trash--archive)
15. [Edit Requests](#15-edit-requests)
16. [Signatures](#16-signatures)
17. [Notifications](#17-notifications)
18. [Admin & Dashboard](#18-admin--dashboard)
19. [Mobile & Polling](#19-mobile--polling)
20. [CORS & Headers](#20-cors--headers)

---

## 1. Base URL & Environment

- **Base URL (local):** `http://localhost:8070` or your Odoo server URL (e.g. `http://192.168.116.204:8070`).
- **API prefix:** All endpoints are under `/api/...`.
- **Health check:** `GET /api/health` — returns `{ "status": "healthy", "service": "NBS Archive API", "version": "1.0.0" }`. Use it to verify the backend is up before calling other APIs.

---

## 2. Authentication

All document/folder/search endpoints require a **JWT access token** in the header:

```http
Authorization: Bearer <access_token>
```

### 2.1 Login

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/auth/login` |
| **Content-Type** | `application/json` |
| **Body type** | Plain JSON (no JSON-RPC envelope) |

**Request body:**

```json
{
  "username": "admin",
  "password": "admin"
}
```

**Success response (200):**

```json
{
  "success": true,
  "access_token": "<JWT_ACCESS_TOKEN>",
  "refresh_token": "<JWT_REFRESH_TOKEN>",
  "expires_in": 3600
}
```

**Error (401):** `{ "success": false, "error": "Invalid credentials" }`

**Frontend usage:** Store `access_token` and `refresh_token` (e.g. in memory or secure storage). Send `access_token` in `Authorization: Bearer <token>` for all subsequent requests.

---

### 2.2 Refresh token

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/auth/refresh` |
| **Body** | `{ "refresh_token": "<REFRESH_TOKEN>" }` |

**Success:** Same shape as login (`access_token`, `refresh_token`, `expires_in`). Use the new `access_token` and optionally update the stored refresh token.

---

### 2.3 Logout

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/auth/logout` |
| **Body** | `{}` (optional) |

**Response:** `{ "success": true }`. Logout is stateless: the frontend should **discard** stored tokens.

---

### 2.4 Current user (me)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/auth/me` |
| **Headers** | `Authorization: Bearer <access_token>` |
| **Body** | `{}` (optional) |

**Success response:**

```json
{
  "success": true,
  "user": {
    "id": 2,
    "name": "Admin User",
    "username": "admin",
    "email": "admin@example.com",
    "departments": [],
    "language": "ar_SA",
    "is_admin": true,
    "is_manager": true,
    "uploaded_documents": 0,
    "pending_approvals": 0,
    "unread_notifications": 0
  }
}
```

Use this on app load to restore session and get user info (roles, language, etc.).

---

## 3. Request Formats (Critical)

The backend uses **two** body formats. Sending the wrong format will cause 400/500 or empty params.

### 3.1 JSON-RPC (most endpoints)

Endpoints documented as **type: jsonrpc** expect a **JSON-RPC 2.0** envelope. All method parameters go inside `params`.

**Template:**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "param1": "value1",
    "param2": 123
  },
  "id": 1
}
```

- `params`: object containing all endpoint parameters (e.g. `page`, `per_page`, `department_id`).
- `id`: any number or string (used for matching responses in JSON-RPC; you can use a simple increment).

**Example (list documents):**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "department_id": 1,
    "page": 1,
    "per_page": 20,
    "status": "active"
  },
  "id": 1
}
```

**Response:** The server may return either:

- Direct result: `{ "success": true, "data": [...], "pagination": {...} }`
- Or wrapped: `{ "jsonrpc": "2.0", "result": { "success": true, "data": [...] }, "id": 1 }`

Handle both in your client: check for `result` first; if present, use `result` as the actual payload.

---

### 3.2 Plain JSON (Auth, Signatures, some Admin)

Endpoints documented as **type: json** or **type: http** with JSON body expect **plain JSON** (no `jsonrpc`/`method`/`params`).

**Example:** Login, refresh, `/api/auth/me`, `/api/signatures/*`, `/api/users/managers`, `/api/nbs/admin/users`, etc.

---

### 3.3 Summary by section

| Section | Typical body format |
|--------|----------------------|
| Auth (login, refresh, logout, me) | Plain JSON |
| Documents (list, get, versions, archive, trash, restore) | JSON-RPC |
| Documents upload | Plain JSON |
| Documents download | GET (no body) |
| Folders | JSON-RPC |
| Search | JSON-RPC |
| Attachments | JSON-RPC (list/add); GET for download |
| Departments, Document Types, Tags, Dashboard, Audit | JSON-RPC |
| Signatures | Plain JSON |
| Admin users (list/update) | Plain JSON |
| Bulk upload | JSON-RPC |

When in doubt, check the section below for each endpoint: **Body** will say either **JSON-RPC** or **Plain JSON**.

---

## 4. Common Response & Errors

- **Success:** Responses include `"success": true` and often `data`, `pagination`, or `message`.
- **Error:** `"success": false` and `"error": "Message"`. Optional: `error_code`, `errors` (validation).
- **HTTP status:** 200 for most success; 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 500 (server error).

Always check `success` and handle `error` for user feedback and retry/refresh token logic.

---

## 5. Documents

Base path: `/api/documents`. All document endpoints below that are **JSON-RPC** (use the envelope) unless noted.

### 5.1 List documents

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents` |
| **Body** | JSON-RPC |

**Params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| department_id | int | No | Filter by department |
| document_type_id | int | No | Filter by document type |
| status | string | No | Document state: `active`, `archived`. Default: `active` |
| search | string | No | Search in document name/title |
| page | int | No | Default 1 |
| per_page | int | No | Default 20 |

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Document title",
      "department_id": 1,
      "department_name": "Sales",
      "document_type_id": 1,
      "document_type_name": "Contract",
      "uploader_id": 2,
      "uploader_name": "Admin",
      "upload_date": "2025-02-07T12:00:00",
      "status": "active",
      "confidentiality_level": "internal",
      "barcode": "DOC-001",
      "file_name": "file.pdf",
      "file_size": 102400
    }
  ],
  "pagination": {
    "total": 50,
    "page": 1,
    "per_page": 20,
    "total_pages": 3
  }
}
```

---

### 5.2 Get single document

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>` |
| **Body** | JSON-RPC, `params` can be `{}` |

**Response:** `success`, `data` with full document details: `id`, `title`, `department_id`, `document_type_id`, `uploader_id`, `upload_date`, `status`, `confidentiality_level`, `barcode`, `file_name`, `file_size`, `is_locked`, `ocr_status`, `ocr` (preview, length), `tags`, `versions` (list of version objects with `id`, `version_number`, `file_name`, `uploaded_by`, `upload_date`, `change_description`, `ocr_completed`, etc.).

---

### 5.3 Upload document

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/upload` |
| **Body** | **Plain JSON** (no JSON-RPC) |
| **Headers** | `Authorization: Bearer <access_token>`, `Content-Type: application/json` |

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| department_id | int | Yes | |
| document_type_id | int | Yes | |
| title | string | Yes | Document title |
| file_data | string | Yes | Base64-encoded file content (or data URL; backend strips `data:...;base64,` if present) |
| file_name | string | Yes | Original file name |
| confidentiality_level | string | No | Default `internal` |
| folder_id | int | No | Single folder |
| folder_ids | array of int | No | Multiple folders |
| tags | array of int | No | Tag IDs |
| po_number, bl_number, container_number, invoice_number, envoy_number | string | No | Reference fields |
| custom_fields | object | No | Custom metadata |
| upload_kind | string | No | `main`, `sub`, or `attachment` |
| parent_document_id | int | No | For sub/attachment |
| create_folder | bool | No | If true, create folder from next fields |
| folder_name, folder_code, folder_type, folder_description | string | No | Used when create_folder is true |

**Success:** `{ "success": true, "data": { "id": <document_id>, "name": "...", ... } }`

**Frontend:** For file input, read file as base64 (e.g. `FileReader.readAsDataURL` then strip prefix if you send data URL) and send in `file_data`.

---

### 5.4 Download document

| Item | Value |
|------|--------|
| **Method** | `GET` |
| **URL** | `/api/documents/<document_id>/download` |
| **Query** | `version_id` (optional) – download specific version |
| **Headers** | `Authorization: Bearer <access_token>` |

**Response:** Binary file (e.g. `application/octet-stream`) with `Content-Disposition: attachment; filename="..."`. Handle as blob and trigger download in the browser.

---

### 5.5 List versions

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/versions` |
| **Body** | JSON-RPC, `params`: `{}` |

**Response:** `success`, `data`: array of `{ id, version_number, file_name, file_size, uploaded_by, upload_date, change_description }`.

---

## 6. Folders

Base path: `/api/folders`. All folder endpoints are **JSON-RPC**.

### 6.1 List folders

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders` |
| **Body** | JSON-RPC |

**Params:** `department_id` (optional), `parent_id` (optional; use `0` or `false` for root).

**Response:** `success`, `data`: array of folder objects (`id`, `name`, `code`, `description`, `parent_id`, `parent_name`, `level`, `full_path`, `child_count`, `document_count`, `all_document_count`, `department_id`, `department_name`, `restricted`, `color`, `icon`, `sequence`), `count`.

---

### 6.2 Get folder

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/<folder_id>` |
| **Body** | JSON-RPC |

**Response:** `success`, `data`: full folder details including `allowed_users`, `allowed_groups`, `parent_path`, `created_by`, `create_date`, `write_date`, etc.

---

### 6.3 Create folder

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/create` |
| **Body** | JSON-RPC |

**Params:** `name` (required), `department_id` (required), `parent_id` (optional), `code`, `description`, `restricted`, `color`, `icon`, `sequence`.

---

### 6.4 Update folder

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/<folder_id>/update` |
| **Body** | JSON-RPC |

**Params:** any of `name`, `code`, `description`, `parent_id`, `restricted`, `color`, `icon`, `sequence`.

---

### 6.5 Delete folder

| Item | Value |
|------|--------|
| **Method** | `DELETE` |
| **URL** | `/api/folders/<folder_id>` |
| **Headers** | `Authorization: Bearer <access_token>` |

---

### 6.6 Move folder

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/<folder_id>/move` |
| **Body** | JSON-RPC |

**Params:** `target_parent_id` (optional; `null` to move to root).

---

### 6.7 Folder tree

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/tree` |
| **Body** | JSON-RPC |

**Params:** `department_id` (optional).

**Response:** `success`, `data`: nested tree structure of folders (e.g. with `children` array per node). Use for tree views in the UI.

---

### 6.8 Folder documents (alternative)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/folders/<folder_id>/documents` |
| **Body** | JSON-RPC |

**Response:** List of documents in that folder. Same idea as filtering documents by `folder_id` where applicable.

---

## 7. Search

All search endpoints are **JSON-RPC**.

### 7.1 Search documents

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/search` |
| **Body** | JSON-RPC |

**Params:**

| Param | Type | Description |
|-------|------|-------------|
| query | string | Required. Search term |
| search_in_content | bool | Search in OCR text if available |
| department_id | int | Filter |
| document_type_id | int | Filter |
| date_from, date_to | string | Date range (ISO) |
| fuzzy | bool | Fuzzy matching |
| page, per_page | int | Pagination |

**Response:** `success`, `data` (list of document summaries), `content_matches` (if content search used), `pagination`.

---

### 7.2 Global search

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/search/global` |
| **Body** | JSON-RPC |

**Params:** `query`, `search_in_content` (default true), `fuzzy` (default true), `page`, `per_page`.

**Response:** Unified list of folders, documents, attachments (and content hits) with `entity_type` so the frontend can show mixed results (e.g. "Folder: X", "Document: Y").

---

### 7.3 Search by barcode

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/search/barcode` |
| **Body** | JSON-RPC |

**Params:** `barcode` (string).

**Response:** Document(s) matching the barcode (exact or primary match). Use for barcode scanner flows.

---

### 7.4 Advanced search

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/search/advanced` |
| **Body** | JSON-RPC |

**Params:** `query`, `department_ids` (array), `document_type_ids` (array), `folder_ids`, `date_from`, `date_to`, `state`, `confidentiality`, `tags`, `uploader_ids`.

**Response:** `success`, `data` (list of documents with basic fields), `count`.

---

## 8. Attachments

Attachments are **supporting files** linked to a document (separate from document versions). Base path: `/api/documents/<document_id>/attachments...`. All list/add/update/delete are **JSON-RPC**; download is **GET**.

### 8.1 List attachments

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/attachments` |
| **Body** | JSON-RPC, `params`: `{}` |

**Response:** `success`, `data`: list of attachment objects (`id`, `name`, `file_name`, `description`, `attachment_type`, `created_date`, etc.).

---

### 8.2 Add attachment

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/add-attachment` |
| **Body** | JSON-RPC |

**Params:** `name`, `file_name`, `file_data` (base64 or data URL), `description`, `attachment_type` (e.g. `supporting`).

---

### 8.3 Download attachment

| Item | Value |
|------|--------|
| **Method** | `GET` |
| **URL** | `/api/documents/<document_id>/attachments/<attachment_id>/download` |
| **Headers** | `Authorization: Bearer <access_token>` |

**Response:** Binary file.

---

### 8.4 Update attachment

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/attachments/<attachment_id>/update` |
| **Body** | JSON-RPC |

**Params:** `name`, `description`, `attachment_type`.

---

### 8.5 Delete attachment

| Item | Value |
|------|--------|
| **Method** | `POST` or `DELETE` (check backend) |
| **URL** | `/api/documents/<document_id>/attachments/<attachment_id>` |
| **Body** | JSON-RPC, optional `reason`. |

---

### 8.6 Upload multiple attachments

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/attachments/multiple` |
| **Body** | JSON-RPC |

**Params:** `attachments`: array of `{ name, file_name, file_data, description, attachment_type }`.

---

## 9. Departments & Document Types

Use these for dropdowns and filters. **JSON-RPC.**

### 9.1 List departments

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/departments` |
| **Body** | JSON-RPC |

**Params:** `include_inactive` (optional bool).

**Response:** `success`, `data`: list of departments (`id`, `name`, `code`, `description`, `sequence`, etc.).

---

### 9.2 Get department

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/departments/<department_id>` |
| **Body** | JSON-RPC |

---

### 9.3 Create department (admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/departments/create` |
| **Body** | JSON-RPC |

**Params:** `name`, `code`, `description`, `manager_ids`, `sequence`.

---

### 9.4 Update department (admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/departments/<department_id>/update` |
| **Body** | JSON-RPC |

**Params:** `name`, `code`, `description`, `manager_ids`, `sequence`, `active`.

---

### 9.5 Delete department (admin)

| Item | Value |
|------|--------|
| **Method** | `DELETE` |
| **URL** | `/api/departments/<department_id>` |

---

### 9.6 List document types

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/document-types` |
| **Body** | JSON-RPC |

**Params:** `department_id` (optional), `include_inactive` (optional).

**Response:** `success`, `data`: list of document types (`id`, `name`, `code`, `department_id`, `description`, `sequence`).

---

### 9.7 Get / Create / Update / Delete document type

- Get: `POST /api/document-types/<doc_type_id>`, JSON-RPC.
- Create: `POST /api/document-types/create`, params: `name`, `code`, `department_id`, `description`, `sequence`.
- Update: `POST /api/document-types/<doc_type_id>/update`, params as needed.
- Delete: `DELETE /api/document-types/<doc_type_id>`.

---

## 10. Batch Operations

**JSON-RPC.** All require list of document IDs.

### 10.1 Batch archive

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/batch/archive` |
| **Body** | JSON-RPC |

**Params:** `document_ids` (array of int).

---

### 10.2 Batch trash

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/batch/trash` |
| **Body** | JSON-RPC |

**Params:** `document_ids`, optional `reason`.

---

### 10.3 Batch move to folder

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/batch/move-folder` |
| **Body** | JSON-RPC |

**Params:** `document_ids`, `target_folder_id`.

---

## 11. Bulk Upload

Flow: **start job** → **upload files** (one or more calls) → **poll progress** → optional **cancel**. All **JSON-RPC.**

### 11.1 Start bulk upload

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/bulk-upload/start` |
| **Body** | JSON-RPC |

**Params:** `department_id`, `document_type_id`, `folder_id` (optional), `confidentiality_level`, `auto_ocr`, `auto_barcode`.

**Response:** `success`, `data`: `{ "job_id": "<uuid>", "id": <internal_id> }`. Store `job_id` for next steps.

---

### 11.2 Upload files to job

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/bulk-upload/<job_id>/upload` |
| **Body** | JSON-RPC |

**Params:** `files`: array of `{ file_name, file_data, name, description }`. `file_data` can be base64 or data URL (prefix stripped by backend).

---

### 11.3 Get progress

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/bulk-upload/<job_id>/progress` |
| **Body** | JSON-RPC |

**Response:** `success`, `data`: e.g. `{ "status": "processing", "total": 10, "processed": 3, "failed": 0 }`. Poll periodically for progress UI.

---

### 11.4 Cancel job

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/bulk-upload/<job_id>/cancel` |
| **Body** | JSON-RPC |

---

### 11.5 List jobs

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/bulk-upload/jobs` |
| **Body** | JSON-RPC |

**Params:** `status`, `limit`, `offset`.

---

## 12. Templates

Create a new document from a template. **JSON-RPC.**

### 12.1 List templates

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/templates` |
| **Body** | JSON-RPC |

**Params:** `department_id` (optional).

**Response:** `success`, `data`: list of templates (`id`, `name`, `document_type_id`, etc.).

---

### 12.2 Create document from template

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/templates/<template_id>/create-document` |
| **Body** | JSON-RPC |

**Params:** optional overrides (e.g. title, department). **Response:** New document id/details.

---

## 13. Document Hierarchy & Relations

### 13.1 Set parent (document hierarchy)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/set-parent` |
| **Body** | JSON-RPC |

**Params:** `parent_document_id` (int or `null` to clear).

---

### 13.2 Get relations

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/relations` |
| **Body** | JSON-RPC |

**Response:** List of related documents with relation type and notes.

---

### 13.3 Add relation

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/add-relation` |
| **Body** | JSON-RPC |

**Params:** `related_document_id`, `relation_type` (e.g. `related`), `notes`.

---

## 14. Trash & Archive

### 14.1 Archive document

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/archive` |
| **Body** | JSON-RPC |

**Permission:** Manager or Admin. Document state becomes `archived`. List with `status: "archived"` in `/api/documents`.

---

### 14.2 Unarchive document

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/unarchive` |
| **Body** | JSON-RPC |

---

### 14.3 Move to trash (soft delete)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/trash` |
| **Body** | JSON-RPC |

**Params:** optional `reason`.

**Response:** May include `restore_deadline`. Document is hidden from normal list; use list trash to show.

---

### 14.4 Restore from trash

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/restore` |
| **Body** | JSON-RPC |

---

### 14.5 Permanent delete (admin only)

| Item | Value |
|------|--------|
| **Method** | `DELETE` |
| **URL** | `/api/documents/<document_id>/permanent` |
| **Body** | Required for the delete to be performed: `{ "confirmation": "DELETE_PERMANENT" }`. If missing or wrong, the API returns `success: false` and does **not** delete. |

**Permission:** Admin only.

---

### 14.6 List trash

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/trash` |
| **Body** | JSON-RPC |

**Response:** List of documents in trash (e.g. with `deleted_at`, `restore_deadline`). Use for a "Trash" view in the UI.

---

## 15. Edit Requests

For **locked** documents: user requests edit → manager approves (receives `unlock_token`) → user uploads new version with that token.

### 15.1 List edit requests

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/edit-requests` |
| **Body** | JSON-RPC |

**Params:** `state`, `document_id`, `page`, `per_page`.

---

### 15.2 Create edit request

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/edit-requests/create` |
| **Body** | JSON-RPC |

**Params:** `document_id`, `reason`.

---

### 15.3 Approve edit request (manager/admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/edit-requests/<request_id>/approve` |
| **Body** | JSON-RPC |

**Response:** Includes `unlock_token`. Requester uses this in upload-version.

---

### 15.4 Reject edit request

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/edit-requests/<request_id>/reject` |
| **Body** | JSON-RPC |

**Params:** optional `rejection_reason`.

---

### 15.5 Upload new version (with unlock token)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/documents/<document_id>/upload-version` (if exists; else under edit flow) |
| **Body** | JSON-RPC |

**Params:** `file_name`, `file_data`, `unlock_token`, `change_description`.

---

## 16. Signatures

**Plain JSON** (no JSON-RPC). Flow: create request → approver approves (gets `sign_token`) → signer uploads signed file with `sign_token`.

### 16.1 List signature requests

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/signatures` |
| **Body** | `{ "state": "pending", "page": 1, "per_page": 20 }` |

---

### 16.2 Create signature request

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/signatures/create` |
| **Body** | `{ "document_id": 123, "signer_id": 9, "message": "Please sign" }` |

---

### 16.3 Approve (get sign token)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/signatures/<request_id>/approve` |
| **Body** | `{}` |

**Response:** `sign_token` for use in upload-signed.

---

### 16.4 Reject

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/signatures/<request_id>/reject` |
| **Body** | `{ "rejection_reason": "..." }` |

---

### 16.5 Upload signed document

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/signatures/<request_id>/upload-signed` |
| **Body** | `{ "file_name", "file_data" (base64), "sign_token", "notes" }` |

---

## 17. Notifications

**JSON-RPC.** Use for inbox and unread badge.

### 17.1 Get notifications

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/notifications` |
| **Body** | JSON-RPC |

**Params:** `unread_only`, `page`, `per_page`.

**Response:** `success`, `data` (list of notifications with `id`, `title`, `message`, `notification_type`, `is_read`, `created_date`, `related_document_id`), `unread_count`, `pagination`.

---

### 17.2 Mark as read

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/notifications/<notification_id>/mark-read` |
| **Body** | JSON-RPC |

---

### 17.3 Mark all as read

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/notifications/mark-all-read` |
| **Body** | JSON-RPC |

---

### 17.4 Unread count

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/notifications/unread-count` |
| **Body** | JSON-RPC |

**Response:** e.g. `{ "success": true, "count": 5 }`. Use for badge in header.

---

### 17.5 Poll (lightweight “push”)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/ws/poll` |
| **Body** | JSON-RPC |

**Params:** `last_poll_id` (optional). **Response:** New notifications or events since last poll. Use with a timer (e.g. every 30s) to refresh notifications without full list.

---

## 18. Admin & Dashboard

**JSON-RPC** unless noted.

### 18.1 Dashboard stats

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/stats/dashboard` |
| **Body** | JSON-RPC |

**Response:** Aggregated counts (documents by department/type, recent activity, etc.). Use for dashboard widgets.

---

### 18.2 Tags

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/tags` |
| **Body** | JSON-RPC |

**Response:** List of tags for filter dropdowns and document tagging.

---

### 18.3 Managers (plain JSON)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/users/managers` |
| **Body** | `{ "department_id": 1 }` |

**Response:** List of manager users (e.g. for signature/edit request assignees).

---

### 18.4 Audit logs (admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/audit-logs` |
| **Body** | JSON-RPC |

**Params:** `document_id`, `action`, `date_from`, `date_to`, `page`, `per_page`.

---

### 18.5 Admin: list users (plain JSON, admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/nbs/admin/users` |
| **Body** | `{ "search": "ali" }` |

---

### 18.6 Admin: update user (plain JSON, admin)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/nbs/admin/users/<user_id>/update` |
| **Body** | `{ "role": "manager", "department_ids": [1,2], "manager_department_ids": [1] }` |

---

## 19. Mobile & Polling

### 19.1 Mobile sync

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/mobile/sync` |
| **Body** | JSON-RPC |

**Params:** `last_sync_date` (ISO string). **Response:** Delta of documents/updates since that date for offline/mobile sync.

---

### 19.2 Register device (push)

| Item | Value |
|------|--------|
| **Method** | `POST` |
| **URL** | `/api/mobile/register` |
| **Body** | JSON-RPC |

**Params:** `device_id`, `device_type`, `fcm_token` (optional).

---

## 20. CORS & Headers

- **CORS:** The API allows configured origins (and often `localhost`). Preflight: `OPTIONS /api/<path>` returns 200 with CORS headers.
- **Headers to send:**
  - `Content-Type: application/json` for all POST bodies.
  - `Authorization: Bearer <access_token>` for all authenticated endpoints.
- **File downloads:** Use `GET` with the same `Authorization` header; handle response as blob and set filename from `Content-Disposition` if present.

---

## Quick Reference Table (for copy-paste)

| Feature | Method | URL | Body type |
|--------|--------|-----|-----------|
| Health | GET | `/api/health` | - |
| Login | POST | `/api/auth/login` | Plain JSON |
| Refresh | POST | `/api/auth/refresh` | Plain JSON |
| Me | POST | `/api/auth/me` | Plain JSON |
| List documents | POST | `/api/documents` | JSON-RPC |
| Get document | POST | `/api/documents/<id>` | JSON-RPC |
| Upload document | POST | `/api/documents/upload` | Plain JSON |
| Download | GET | `/api/documents/<id>/download` | - |
| List versions | POST | `/api/documents/<id>/versions` | JSON-RPC |
| List folders | POST | `/api/folders` | JSON-RPC |
| Folder tree | POST | `/api/folders/tree` | JSON-RPC |
| Create folder | POST | `/api/folders/create` | JSON-RPC |
| Search | POST | `/api/search` | JSON-RPC |
| Global search | POST | `/api/search/global` | JSON-RPC |
| Barcode search | POST | `/api/search/barcode` | JSON-RPC |
| Advanced search | POST | `/api/search/advanced` | JSON-RPC |
| List attachments | POST | `/api/documents/<id>/attachments` | JSON-RPC |
| Add attachment | POST | `/api/documents/<id>/add-attachment` | JSON-RPC |
| Departments | POST | `/api/departments` | JSON-RPC |
| Document types | POST | `/api/document-types` | JSON-RPC |
| Batch archive | POST | `/api/documents/batch/archive` | JSON-RPC |
| Batch trash | POST | `/api/documents/batch/trash` | JSON-RPC |
| Batch move folder | POST | `/api/documents/batch/move-folder` | JSON-RPC |
| Bulk upload start | POST | `/api/documents/bulk-upload/start` | JSON-RPC |
| Bulk upload files | POST | `/api/documents/bulk-upload/<job_id>/upload` | JSON-RPC |
| Bulk progress | POST | `/api/documents/bulk-upload/<job_id>/progress` | JSON-RPC |
| Templates | POST | `/api/templates` | JSON-RPC |
| Create from template | POST | `/api/templates/<id>/create-document` | JSON-RPC |
| Archive | POST | `/api/documents/<id>/archive` | JSON-RPC |
| Unarchive | POST | `/api/documents/<id>/unarchive` | JSON-RPC |
| Trash | POST | `/api/documents/<id>/trash` | JSON-RPC |
| Restore | POST | `/api/documents/<id>/restore` | JSON-RPC |
| List trash | POST | `/api/documents/trash` | JSON-RPC |
| Permanent delete | DELETE | `/api/documents/<id>/permanent` | Optional JSON |
| Set parent | POST | `/api/documents/<id>/set-parent` | JSON-RPC |
| Relations | POST | `/api/documents/<id>/relations` | JSON-RPC |
| Add relation | POST | `/api/documents/<id>/add-relation` | JSON-RPC |
| Edit requests | POST | `/api/edit-requests` | JSON-RPC |
| Create edit request | POST | `/api/edit-requests/create` | JSON-RPC |
| Approve edit | POST | `/api/edit-requests/<id>/approve` | JSON-RPC |
| Signatures | POST | `/api/signatures` | Plain JSON |
| Create signature | POST | `/api/signatures/create` | Plain JSON |
| Approve signature | POST | `/api/signatures/<id>/approve` | Plain JSON |
| Upload signed | POST | `/api/signatures/<id>/upload-signed` | Plain JSON |
| Notifications | POST | `/api/notifications` | JSON-RPC |
| Mark read | POST | `/api/notifications/<id>/mark-read` | JSON-RPC |
| Unread count | POST | `/api/notifications/unread-count` | JSON-RPC |
| Poll | POST | `/api/ws/poll` | JSON-RPC |
| Dashboard stats | POST | `/api/stats/dashboard` | JSON-RPC |
| Tags | POST | `/api/tags` | JSON-RPC |
| Audit logs | POST | `/api/audit-logs` | JSON-RPC |
| Admin users | POST | `/api/nbs/admin/users` | Plain JSON |
| Admin update user | POST | `/api/nbs/admin/users/<id>/update` | Plain JSON |
| Mobile sync | POST | `/api/mobile/sync` | JSON-RPC |

---

**Document version:** 1.0  
**Module:** nbs_archive (nbs_archiving)  
**Audience:** Frontend developers integrating with NBS Archive API.
