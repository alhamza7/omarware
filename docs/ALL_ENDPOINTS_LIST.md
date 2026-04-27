# NBS Archive System - Complete Endpoint List

## Total: 70+ API Endpoints

---

## 🔐 Authentication (5 endpoints)
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/me` - Get current user info
- `GET /api/health` - Health check

---

## 📄 Documents (15 endpoints)
- `POST /api/documents` - List documents with filters
- `POST /api/documents/<id>` - Get single document
- `POST /api/documents/upload` - Upload new document
- `POST /api/documents/<id>/update` - Update document metadata
- `GET /api/documents/<id>/download` - Download document
- `POST /api/documents/<id>/upload-version` - Upload new version
- `POST /api/documents/<id>/versions` - Get version history
- `POST /api/documents/<id>/archive` - Archive document
- `POST /api/documents/<id>/unarchive` - Unarchive document
- `POST /api/documents/<id>/trash` - Move to trash
- `POST /api/documents/<id>/restore` - Restore from trash
- `DELETE /api/documents/<id>/permanent` - Permanent delete (legacy)
- `POST /api/documents/trash` - List trash
- `POST /api/documents/restore` - Batch restore
- `POST /api/documents/permanent-delete` - Batch permanent delete

---

## 📁 Folders (10 endpoints)
- `POST /api/folders` - List folders
- `POST /api/folders/create` - Create folder
- `POST /api/folders/tree` - Get folder tree
- `POST /api/folders/<id>` - Get single folder
- `POST /api/folders/<id>/documents` - Get folder documents
- `POST /api/folders/<id>/update` - Update folder
- `POST /api/folders/<id>/add-document` - Add document to folder
- `POST /api/folders/<id>/move` - Move folder to parent
- `POST /api/folders/<id>/workflow` - Get folder workflow
- `POST /api/folders/<id>/workflow/set` - Set folder workflow
- `POST /api/folders/<id>/workflow/transition` - Transition workflow

---

## 🔗 Relations & Attachments (12 endpoints)
- `POST /api/documents/<id>/relations` - Get document relations
- `POST /api/documents/<id>/add-relation` - Add relation
- `POST /api/documents/<id>/attachments` - List attachments
- `POST /api/documents/<id>/add-attachment` - Add single attachment
- `POST /api/documents/<id>/attachments/multiple` - Add multiple attachments
- `GET /api/documents/<id>/attachments/<att_id>/download` - Download attachment
- `POST /api/documents/<id>/attachments/<att_id>` - Get attachment details
- `POST /api/documents/<id>/attachments/<att_id>/update` - Update attachment
- `POST /api/documents/<id>/attachments/<att_id>/restore` - Restore attachment
- `DELETE /api/documents/<id>/attachments/<att_id>/permanent` - Delete attachment
- `POST /api/documents/<id>/set-parent` - Set parent document

---

## 📝 Notes System (6 endpoints)
- `POST /api/notes` - List notes (document/folder/system)
- `POST /api/notes/create` - Create note
- `POST /api/notes/<id>` - Get single note
- `POST /api/notes/<id>/update` - Update note
- `POST /api/notes/<id>/delete` - Delete note (soft)
- `POST /api/notes/<id>/reply` - Reply to note (future)
- `POST /api/notes/<id>/reactions` - Add reaction (future)

---

## 🔄 Batch Operations (3 endpoints)
- `POST /api/documents/batch/archive` - Batch archive
- `POST /api/documents/batch/trash` - Batch trash
- `POST /api/documents/batch/move-folder` - Batch move to folder

---

## 📤 Bulk Upload (4 endpoints)
- `POST /api/documents/bulk-upload/start` - Start bulk upload job
- `POST /api/documents/bulk-upload/<job_id>/upload` - Upload files
- `POST /api/documents/bulk-upload/<job_id>/progress` - Check progress
- `POST /api/documents/bulk-upload/<job_id>/cancel` - Cancel job
- `POST /api/documents/bulk-upload/jobs` - List jobs

---

## 🔍 Search (4 endpoints)
- `POST /api/search` - Basic search
- `POST /api/search/advanced` - Advanced search
- `POST /api/search/global` - Global search
- `POST /api/search/barcode` - Barcode search
- `POST /api/search/suggestions` - Search suggestions (future)

---

## ✍️ Edit Requests (5 endpoints)
- `POST /api/edit-requests` - List edit requests
- `POST /api/edit-requests/create` - Create edit request
- `POST /api/edit-requests/<id>/approve` - Approve request
- `POST /api/edit-requests/<id>/reject` - Reject request
- `POST /api/edit-requests/pending-approvals` - Get pending approvals

---

## 🏢 Departments & Types (8 endpoints)
- `POST /api/departments` - List departments
- `POST /api/departments/create` - Create department
- `POST /api/departments/<id>` - Get department
- `POST /api/departments/<id>/update` - Update department
- `POST /api/document-types` - List document types
- `POST /api/document-types/create` - Create type
- `POST /api/document-types/<id>` - Get type
- `POST /api/document-types/<id>/update` - Update type

---

## 👥 Admin & Users (3 endpoints)
- `POST /api/nbs/admin/users` - List users
- `POST /api/nbs/admin/users/<id>/update` - Update user
- `POST /api/users/managers` - List managers

---

## 🔔 Notifications (4 endpoints)
- `POST /api/notifications` - List notifications
- `POST /api/notifications/<id>/mark-read` - Mark as read
- `POST /api/notifications/mark-all-read` - Mark all read
- `POST /api/notifications/unread-count` - Get unread count

---

## 🎯 Signatures (4 endpoints)
- `POST /api/signatures` - List signature requests
- `POST /api/signatures/create` - Create signature request
- `POST /api/signatures/<id>/approve` - Approve signature
- `POST /api/signatures/<id>/reject` - Reject signature
- `POST /api/signatures/<id>/upload-signed` - Upload signed document

---

## 🤖 OCR (2 endpoints)
- `POST /api/ocr/test` - Test OCR
- `POST /api/ocr/run/<document_id>` - Run OCR on document

---

## 📊 Statistics & Reports (1 endpoint)
- `POST /api/stats/dashboard` - Dashboard statistics

---

## 🏷️ Tags (1 endpoint)
- `POST /api/tags` - List tags

---

## 📋 Templates (2 endpoints)
- `POST /api/templates` - List templates
- `POST /api/templates/<id>/create-document` - Create from template

---

## 🔄 Workflows (2 endpoints)
- `POST /api/workflows` - List workflows
- `POST /api/workflows/<id>/detail` - Get workflow details

---

## 📱 Mobile API (2 endpoints)
- `POST /api/mobile/register` - Register mobile device
- `POST /api/mobile/sync` - Sync data

---

## 📊 Audit (1 endpoint)
- `POST /api/audit-logs` - Get audit logs

---

## 🌐 WebSocket (1 endpoint)
- `POST /api/ws/poll` - WebSocket polling

---

## 🔍 How to Find Specific API Details

### Option 1: Read Documentation Files
```bash
# Main API docs
cat addons/nbs_archive/API_DOCUMENTATION.md

# Notes system
cat NOTES_SYSTEM_API_DOCUMENTATION_EN.md

# Complete reference
cat API_REFERENCE_COMPLETE.md
```

### Option 2: Search Controllers
```bash
# Find document upload endpoint
grep -A 20 "def upload_document" addons/nbs_archive/controllers/document_controller.py

# Find all endpoints in a controller
grep "@http.route" addons/nbs_archive/controllers/document_controller.py
```

### Option 3: Use IDE
Open any controller file in:
```
addons/nbs_archive/controllers/
```

Look for `@http.route` decorators.

---

## 📝 Controller → Endpoints Mapping

| Controller File | Main Endpoints |
|----------------|----------------|
| `auth_controller.py` | Login, logout, refresh, me |
| `document_controller.py` | Documents CRUD, upload, download, archive, trash |
| `folder_controller.py` | Folders CRUD, tree, workflow |
| `relations_controller.py` | Relations, folder links |
| `attachments_controller.py` | Attachments upload, download, delete |
| `edit_request_controller.py` | Edit requests, version upload |
| `batch_operations_controller.py` | Batch archive, trash, move |
| `notes_controller.py` | Notes CRUD, replies |
| `search_controller.py` | Search, advanced search, barcode |
| `department_management_controller.py` | Departments, types CRUD |
| `admin_controller.py` | User management, system admin |
| `permissions_controller.py` | User permissions |
| `notification_controller.py` | Notifications |
| `bulk_upload_controller.py` | Bulk upload jobs |
| `signature_controller.py` | Digital signatures |
| `ocr_controller.py` | OCR processing |
| `workflow_controller.py` | Workflow management |
| `template_controller.py` | Document templates |
| `mobile_api_controller.py` | Mobile sync |
| `advanced_search_controller.py` | Advanced search |
| `websocket_controller.py` | WebSocket polling |

---

## 🎯 Quick Access

**Currently open in your IDE:**
- `NOTES_SYSTEM_API_DOCUMENTATION_EN.md` (line 622)

**Recommended to open:**
- `addons/nbs_archive/API_DOCUMENTATION.md` - Main reference
- `API_REFERENCE_COMPLETE.md` - Complete guide

**Source code:**
- `addons/nbs_archive/controllers/` - All implementations

---

## 💡 Pro Tip

To generate a custom API list with details:

```bash
cd addons/nbs_archive/controllers
for file in *.py; do
  echo "=== $file ==="
  grep -A 3 "@http.route" "$file" | head -20
done
```
