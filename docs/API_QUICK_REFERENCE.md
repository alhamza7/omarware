# NBS Archive System - API Quick Reference

## 📍 Base URL

- **Local:** `http://localhost:8070`
- **Production:** TBD

---

## 🔐 Authentication

All endpoints require JWT authentication:

```bash
Authorization: Bearer <your_jwt_token>
```

Get token via:
```bash
POST /api/auth/login
{
  "username": "admin",
  "password": "admin"
}
```

---

## 📁 Main API Endpoints by Category

### 1. Documents

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents` | POST | List documents with filters |
| `/api/documents/<id>` | POST | Get single document |
| `/api/documents/upload` | POST | Upload new document |
| `/api/documents/<id>/update` | POST | Update document metadata |
| `/api/documents/<id>/download` | GET | Download document file |
| `/api/documents/<id>/upload-version` | POST | Upload new version |
| `/api/documents/<id>/versions` | POST | Get version history |
| `/api/documents/<id>/archive` | POST | Archive document |
| `/api/documents/<id>/trash` | POST | Move to trash |
| `/api/documents/<id>/restore` | POST | Restore from trash |
| `/api/documents/trash` | POST | List trash documents |

### 2. Folders

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/folders` | POST | List all folders |
| `/api/folders/<id>/documents` | POST | Get folder documents |
| `/api/folders/create` | POST | Create new folder |
| `/api/folders/<id>/update` | POST | Update folder |
| `/api/folders/<id>/delete` | POST | Delete folder |
| `/api/folders/<id>/add-document` | POST | Add document to folder |

### 3. Batch Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/documents/batch/archive` | POST | Batch archive |
| `/api/documents/batch/trash` | POST | Batch move to trash |
| `/api/documents/batch/move-folder` | POST | Move documents to folder |

### 4. Notes

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/notes` | POST | List notes |
| `/api/notes/<id>` | POST | Get single note |
| `/api/notes/create` | POST | Create note |
| `/api/notes/<id>/update` | POST | Update note |
| `/api/notes/<id>/delete` | POST | Delete note |
| `/api/notes/<id>/reply` | POST | Reply to note |
| `/api/notes/<id>/reactions` | POST | Add reaction |

### 5. Search

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/search` | POST | Basic search |
| `/api/search/advanced` | POST | Advanced search |
| `/api/search/suggestions` | POST | Search suggestions |

### 6. Admin

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/admin/users` | POST | List users |
| `/api/admin/users/<id>/update` | POST | Update user |
| `/api/departments` | POST | List departments |
| `/api/departments/create` | POST | Create department |
| `/api/document-types` | POST | List document types |
| `/api/document-types/create` | POST | Create document type |

---

## 📖 Complete Documentation Files

### Main Documentation:
1. **`API_DOCUMENTATION.md`** - Complete API reference
   - Location: `addons/nbs_archive/API_DOCUMENTATION.md`

2. **`NOTES_SYSTEM_API_DOCUMENTATION_EN.md`** - Notes API (English)
   - Location: Root directory
   - Detailed notes endpoints

3. **`API_REFERENCE_COMPLETE.md`** - Full system reference
   - Location: Root directory

### Recent Bug Fix Documentation:
- `BUGFIX_FOLDER_MOVE_AND_VALIDATIONS.md` - Folder move fixes
- `BUGFIX_DOCUMENT_UPDATE_AND_FOLDER_ID.md` - Update endpoint
- `BUGFIX_FOLDER_INCONSISTENCY.md` - Folder duplicate issue
- `API_CHANGES_FRONTEND_GUIDE.md` - Frontend integration guide

---

## 🛠️ Controller Files (Source Code)

All API endpoints are defined in:
```
addons/nbs_archive/controllers/
```

Each controller file contains specific endpoints:

| File | Contains |
|------|----------|
| `auth_controller.py` | Login, logout, token refresh |
| `document_controller.py` | Document CRUD, upload, download |
| `folder_controller.py` | Folder management |
| `notes_controller.py` | Notes system |
| `search_controller.py` | Search functionality |
| `batch_operations_controller.py` | Batch operations |
| `edit_request_controller.py` | Edit workflow, version upload |
| `relations_controller.py` | Document relations |
| `attachments_controller.py` | File attachments |

---

## 📝 How to Find Specific APIs

### Method 1: Search by Endpoint Path
```bash
grep -r "http.route" addons/nbs_archive/controllers/ | grep "api/documents"
```

### Method 2: Search by Functionality
```bash
grep -r "def.*upload" addons/nbs_archive/controllers/
```

### Method 3: Read Documentation Files
```bash
# English notes API
cat NOTES_SYSTEM_API_DOCUMENTATION_EN.md

# Complete API reference
cat API_REFERENCE_COMPLETE.md

# Module-specific docs
cat addons/nbs_archive/API_DOCUMENTATION.md
```

---

## 🎯 Which File Should You Read?

**For frontend development:**
- Start with: `API_CHANGES_FRONTEND_GUIDE.md`
- Then read: `addons/nbs_archive/NBS_ARCHIVE_API_REFERENCE_FRONTEND.md`

**For notes system:**
- Read: `NOTES_SYSTEM_API_DOCUMENTATION_EN.md`

**For complete reference:**
- Read: `API_REFERENCE_COMPLETE.md`

**For source code:**
- Browse: `addons/nbs_archive/controllers/`

---

## 📊 Generate API List from Code

Run this to see all endpoints:

```bash
cd /home/capo7amzah/Documents/NBS-PROJECT/Lugal-ai
grep -r "@http.route" addons/nbs_archive/controllers/ | \
  grep -oP "'/api/[^']+'" | \
  sort -u
```

This will list all API endpoints defined in the system.
