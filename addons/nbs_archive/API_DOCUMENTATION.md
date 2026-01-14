# NBS Archive API Documentation (English)

This document describes **all API endpoints** exposed by the `nbs_archive` module in this repo.

---

## Base URL

- Local (typical): `http://192.168.116.204:8070`
- All endpoints are under: `/api/...`

---

## Authentication

Most endpoints require JWT:

- **Header**: `Authorization: Bearer <access_token>`
- Auth helper in controllers: `ensure_jwt_user_id()` (rejects missing/invalid token)

### Token endpoints

#### POST `/api/auth/login` (type=`http`)

- **Body**: JSON
  - `username` (string, required)
  - `password` (string, required)
- **Response**: JSON
  - `success` boolean
  - plus tokens (from `nbs.jwt.service.authenticate_user`)

Example:

```bash
curl -X POST "http://192.168.116.204:8070/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'
```

#### POST `/api/auth/refresh` (type=`http`)

- **Body**: JSON
  - `refresh_token` (string, required)

```bash
curl -X POST "http://192.168.116.204:8070/api/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"<REFRESH_TOKEN>"}'
```

#### POST `/api/auth/logout` (type=`http`)

- Stateless logout (client deletes tokens).

```bash
curl -X POST "http://192.168.116.204:8070/api/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### POST `/api/auth/me` (type=`http`)

```bash
curl -X POST "http://192.168.116.204:8070/api/auth/me" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{}'
```

---

## Request formats (IMPORTANT)

Controllers use three different route types, which affects the payload format:

### 1) JSON-RPC endpoints (`type='jsonrpc'`)

Send a **JSON-RPC 2.0** envelope and put parameters inside `params`.

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { "param1": "..." },
  "id": 1
}
```

`curl` template:

```bash
curl -X POST "http://192.168.116.204:8070/api/..." \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### 2) JSON endpoints (`type='json'`)

Send normal JSON (no JSON-RPC envelope).

```bash
curl -X POST "http://192.168.116.204:8070/api/..." \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{}'
```

### 3) HTTP endpoints (`type='http'`)

Send normal JSON in the raw request body (or do a GET for downloads).

---

## Common response shape

Most endpoints return:

- `success` (boolean)
- on success: `data` or `message` or `stats`
- on failure: `error` (string)

Notes:
- Some endpoints also return `pagination`.
- Some endpoints return files (binary) for downloads.

---

## Health + CORS

### GET `/api/health` (type=`http`)

```bash
curl -X GET "http://192.168.116.204:8070/api/health"
```

### OPTIONS `/api/<path>` (type=`http`)

Used for CORS preflight.

---

## Documents

### POST `/api/documents` (type=`jsonrpc`) — list documents

**Params**:
- `department_id` (int, optional)
- `document_type_id` (int, optional)
- `status` (string, optional) **mapped to** document `state`
  - If not provided, defaults to `state='active'`
- `search` (string, optional) — searches `name`
- `page` (int, default 1)
- `per_page` (int, default 20)

Example:

```bash
curl -X POST "http://192.168.116.204:8070/api/documents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"page":1,"per_page":20},"id":1}'
```

### POST `/api/documents/<document_id>` (type=`jsonrpc`) — document details

Returns document + versions + OCR preview.

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/documents/upload` (type=`http`) — upload new document

**Body** (JSON):
- Required:
  - `department_id` (int)
  - `document_type_id` (int)
  - `title` (string)
  - `file_data` (string base64, or dataURL-like string in some clients)
  - `file_name` (string)
- Optional:
  - `confidentiality_level` (string, default `internal`)
  - reference fields: `po_number`, `bl_number`, `container_number`, `invoice_number`, `envoy_number`
  - `tags` (list[int]) — tag ids
  - `custom_fields` (object) — stored JSON
  - folder linking: `folder_id` (int) or `folder_ids` (list[int])
  - upload structure:
    - `upload_kind` (string: `main|sub|attachment`)
    - `parent_document_id` (int)
  - auto-create folder (main only):
    - `create_folder` (bool)
    - `folder_name`, `folder_code`, `folder_type`, `folder_description`

Example (with placeholders):

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/upload" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "department_id": 1,
    "document_type_id": 1,
    "title": "Test Document",
    "file_name": "test.pdf",
    "file_data": "<BASE64_CONTENT>",
    "confidentiality_level": "internal",
    "upload_kind": "main",
    "create_folder": true
  }'
```

### GET `/api/documents/<document_id>/download` (type=`http`) — download document/version

- Optional query: `version_id`

```bash
curl -L -X GET "http://192.168.116.204:8070/api/documents/123/download" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -o document.bin
```

Download a specific version:

```bash
curl -L -X GET "http://192.168.116.204:8070/api/documents/123/download?version_id=55" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -o document-v55.bin
```

### POST `/api/documents/<document_id>/versions` (type=`jsonrpc`) — list versions

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/versions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

---

## Archiving (Document state)

Archiving here is **not** `active=false`; it is:
- `nbs.document.state = 'archived'` / `'active'`

### POST `/api/documents/<document_id>/archive` (type=`jsonrpc`)

- **Permission**: manager or admin only (`group_nbs_manager` / `group_nbs_admin`)

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/archive" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/documents/<document_id>/unarchive` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/unarchive" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

To list archived documents, call `/api/documents` with `status="archived"`:

```bash
curl -X POST "http://192.168.116.204:8070/api/documents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"status":"archived","page":1,"per_page":20},"id":1}'
```

---

## Document hierarchy (parent/child)

### POST `/api/documents/<document_id>/set-parent` (type=`jsonrpc`)

Set parent:

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/set-parent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"parent_document_id":999},"id":1}'
```

Clear parent:

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/set-parent" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"parent_document_id":null},"id":1}'
```

---

## Edit Requests + Uploading new versions (locked docs)

### POST `/api/edit-requests` (type=`jsonrpc`) — list edit requests

```bash
curl -X POST "http://192.168.116.204:8070/api/edit-requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"page":1,"per_page":20},"id":1}'
```

### POST `/api/edit-requests/create` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/edit-requests/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"document_id":123,"reason":"Need to update content"},"id":1}'
```

### POST `/api/edit-requests/<request_id>/approve` (type=`jsonrpc`) — manager/admin

Returns `unlock_token` (one-time token).

```bash
curl -X POST "http://192.168.116.204:8070/api/edit-requests/10/approve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/edit-requests/<request_id>/reject` (type=`jsonrpc`) — manager/admin

```bash
curl -X POST "http://192.168.116.204:8070/api/edit-requests/10/reject" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"rejection_reason":"Not allowed"},"id":1}'
```

### POST `/api/documents/<document_id>/upload-version` (type=`jsonrpc`)

Requires `unlock_token` from an approved edit request (must belong to requester).

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/upload-version" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params":{
      "file_name":"updated.pdf",
      "file_data":"<BASE64_CONTENT>",
      "unlock_token":"<UNLOCK_TOKEN>",
      "change_description":"Updated content"
    },
    "id":1
  }'
```

### POST `/api/edit-requests/pending-approvals` (type=`jsonrpc`) — manager/admin

```bash
curl -X POST "http://192.168.116.204:8070/api/edit-requests/pending-approvals" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

---

## Attachments (separate from versions)

### POST `/api/documents/<document_id>/attachments` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/attachments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/documents/<document_id>/add-attachment` (type=`jsonrpc`)

Accepts base64 or a DataURL (it strips `base64,` prefix).

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/add-attachment" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params":{
      "name":"Supporting file",
      "file_name":"support.txt",
      "file_data":"<BASE64_CONTENT>",
      "description":"Extra info",
      "attachment_type":"supporting"
    },
    "id":1
  }'
```

### GET `/api/documents/<document_id>/attachments/<attachment_id>/download` (type=`http`)

```bash
curl -L -X GET "http://192.168.116.204:8070/api/documents/123/attachments/77/download" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -o attachment.bin
```

---

## Folders

### POST `/api/folders` (type=`jsonrpc`) — list folders

Params: `department_id?`, `folder_type?`, `state='active'`

```bash
curl -X POST "http://192.168.116.204:8070/api/folders" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"state":"active"},"id":1}'
```

### POST `/api/folders/<folder_id>/documents` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/5/documents" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/folders/create` (type=`jsonrpc`)

Required: `name`, `code`, `department_id`

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"name":"Folder A","code":"F-A","department_id":1,"folder_type":"other"},"id":1}'
```

### POST `/api/folders/<folder_id>/add-document` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/5/add-document" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"document_id":123},"id":1}'
```

---

## Folder workflows

### POST `/api/workflows` (type=`jsonrpc`) — admin only

```bash
curl -X POST "http://192.168.116.204:8070/api/workflows" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/workflows/<workflow_id>/detail` (type=`jsonrpc`) — admin only

```bash
curl -X POST "http://192.168.116.204:8070/api/workflows/3/detail" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/folders/<folder_id>/workflow` (type=`jsonrpc`)

Returns allowed transitions for current user.

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/5/workflow" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/folders/<folder_id>/workflow/set` (type=`jsonrpc`) — admin only

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/5/workflow/set" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"workflow_id":3},"id":1}'
```

### POST `/api/folders/<folder_id>/workflow/transition` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/folders/5/workflow/transition" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"transition_id":9,"message":"Approved"},"id":1}'
```

---

## Search

### POST `/api/search` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/search" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"query":"INV-2026","search_in_content":false,"page":1,"per_page":20},"id":1}'
```

### POST `/api/search/global` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/search/global" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"query":"invoice","search_in_content":true,"fuzzy":true},"id":1}'
```

### POST `/api/search/barcode` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/search/barcode" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"barcode":"ABC123"},"id":1}'
```

---

## Notifications + polling

### POST `/api/notifications` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/notifications" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"unread_only":false,"page":1,"per_page":20},"id":1}'
```

### POST `/api/notifications/<notification_id>/mark-read` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/notifications/50/mark-read" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/notifications/mark-all-read` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/notifications/mark-all-read" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/notifications/unread-count` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/notifications/unread-count" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/ws/poll` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/ws/poll" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"last_poll_id":0},"id":1}'
```

---

## OCR

### POST `/api/ocr/test` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/ocr/test" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/ocr/run/<document_id>` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/ocr/run/123" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

---

## Relations (document-to-document)

### POST `/api/documents/<document_id>/relations` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/relations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/documents/<document_id>/add-relation` (type=`jsonrpc`)

Params: `related_document_id`, optional `relation_type`, `notes`

```bash
curl -X POST "http://192.168.116.204:8070/api/documents/123/add-relation" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"related_document_id":456,"relation_type":"related","notes":"Same project"},"id":1}'
```

---

## Signatures (print -> sign -> upload signed scan)

These endpoints are `type='json'` (NOT JSON-RPC).

### POST `/api/signatures` (type=`json`)

```bash
curl -X POST "http://192.168.116.204:8070/api/signatures" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"state":"pending","page":1,"per_page":20}'
```

### POST `/api/signatures/create` (type=`json`)

```bash
curl -X POST "http://192.168.116.204:8070/api/signatures/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"document_id":123,"signer_id":9,"message":"Please sign"}'
```

### POST `/api/signatures/<request_id>/approve` (type=`json`)

Returns `sign_token`.

```bash
curl -X POST "http://192.168.116.204:8070/api/signatures/22/approve" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{}'
```

### POST `/api/signatures/<request_id>/reject` (type=`json`)

```bash
curl -X POST "http://192.168.116.204:8070/api/signatures/22/reject" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"rejection_reason":"Not valid"}'
```

### POST `/api/signatures/<request_id>/upload-signed` (type=`json`)

Requires: `sign_token`, base64 file.

```bash
curl -X POST "http://192.168.116.204:8070/api/signatures/22/upload-signed" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "file_name":"signed.pdf",
    "file_data":"<BASE64_CONTENT>",
    "sign_token":"<SIGN_TOKEN>",
    "notes":"Signed copy"
  }'
```

---

## Admin / reference endpoints

### POST `/api/departments` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/departments" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/document-types` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/document-types" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"department_id":1},"id":1}'
```

### POST `/api/tags` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/tags" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/stats/dashboard` (type=`jsonrpc`)

```bash
curl -X POST "http://192.168.116.204:8070/api/stats/dashboard" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

### POST `/api/users/managers` (type=`json`)

```bash
curl -X POST "http://192.168.116.204:8070/api/users/managers" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"department_id":1}'
```

### POST `/api/audit-logs` (type=`jsonrpc`) — admin only

```bash
curl -X POST "http://192.168.116.204:8070/api/audit-logs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"page":1,"per_page":50},"id":1}'
```

---

## Permissions admin (role + department access)

These endpoints are `type='http'` and require **admin**.

### POST `/api/nbs/admin/users` (type=`http`)

```bash
curl -X POST "http://192.168.116.204:8070/api/nbs/admin/users" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"search":"ali"}'
```

### POST `/api/nbs/admin/users/<user_id>/update` (type=`http`)

Body fields:
- `role` (string: `admin|manager|employee`)
- `department_ids` (list[int])
- `manager_department_ids` (list[int])

```bash
curl -X POST "http://192.168.116.204:8070/api/nbs/admin/users/9/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{"role":"manager","department_ids":[1,2],"manager_department_ids":[1]}'
```




