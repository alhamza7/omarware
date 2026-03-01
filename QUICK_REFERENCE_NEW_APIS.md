# Quick Reference - New APIs & Fields

## 🚀 Ready to Use Now

**Base URL:** `http://localhost:8070`  
**Status:** ✅ All systems operational

---

## 📄 DOCUMENT API - NEW FIELDS

All document responses now include:

```typescript
{
  id: number,
  title: string,
  // ... existing fields ...
  parent_document_id: number | null,      // ✅ NEW - Parent document ID
  relation_type: "attachment" | "secondary_document" | null,  // ✅ NEW
  note_count: number,                     // ✅ NEW - Number of notes
  last_modified: string                   // ✅ NEW - ISO datetime
}
```

**Endpoints:**
- `POST /api/documents`
- `POST /api/documents/<id>`
- `POST /api/folders/<id>/documents`
- `POST /api/search`

---

## 📁 FOLDER API - NEW FIELDS

All folder responses now include:

```typescript
{
  id: number,
  name: string,
  // ... existing fields ...
  note_count: number,                     // ✅ NEW - Number of notes
  user_note: string | null,               // ✅ NEW - Quick note
  last_modified: string                   // ✅ NEW - ISO datetime
}
```

**Endpoints:**
- `POST /api/folders/<id>`
- `POST /api/folders/<id>/documents`

**Update folder note:**
```bash
POST /api/folders/<id>/update
Body: {"user_note": "My folder note"}
```

---

## 🗑️ BULK DELETE

**NEW:** `POST /api/documents/permanent-delete`

**Request:**
```json
{
  "ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "deleted": [1, 2],
  "failed": [3]
}
```

**Old endpoint still works:** `DELETE /api/documents/<id>/permanent`

---

## ♻️ BULK RESTORE

**NEW:** `POST /api/documents/restore`

**Request:**
```json
{
  "ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "restored": [1, 2],
  "failed": [3]
}
```

**Old endpoint still works:** `POST /api/documents/<document_id>/restore`

---

## 📝 NOTES SYSTEM

### Create Note
```bash
POST /api/notes/create
Content-Type: application/json

{
  "content": "Note text",              // Required
  "title": "Note title",               // Optional
  "document_id": 123,                  // Optional
  "folder_id": 50,                     // Optional
  "image": "base64_image",             // Optional
  "image_filename": "image.png",       // Optional
  "is_private": true,                  // Default: true
  "is_pinned": false,                  // Default: false
  "color": 0                           // 0-9, Default: 0
}
```

### List Notes
```bash
POST /api/notes
JSON-RPC

{
  "document_id": 123,    // Optional filter
  "folder_id": 50,       // Optional filter
  "page": 1,
  "per_page": 50
}
```

### Update Note
```bash
POST /api/notes/<id>/update

{
  "content": "Updated text",
  "is_pinned": true
}
```

### Delete Note
```bash
DELETE /api/notes/<id>
```

---

## 🎨 Note Colors

| Code | Color | Use Case |
|------|-------|----------|
| 0 | Default | Regular notes |
| 1 | Red | Urgent/Critical |
| 2 | Blue | Information |
| 3 | Green | Approved/Good |
| 4 | Yellow | Warning |
| 5 | Orange | Important |
| 6 | Purple | Review |
| 7 | Pink | Personal |
| 8 | Brown | Archive |
| 9 | Gray | Draft |

---

## ⚠️ BREAKING CHANGES

### Folder Deletion
**OLD:** Deleting folder left documents orphaned  
**NEW:** Deleting folder CASCADE DELETES all documents inside it

**Important:** 
- Test this carefully in staging first
- Documents are soft-deleted first (moved to trash)
- Then permanently deleted
- Cannot be undone

---

## 🔐 PERMISSIONS

### Notes
- **Create:** Any user
- **Read:** Creator (private) | Dept managers (public)
- **Update:** Creator only
- **Delete:** Creator or admin

### Folder user_note
- **Update:** Manager or admin

### Bulk Delete/Restore
- **Delete:** Admin only
- **Restore:** Same as single restore

---

## 📱 TYPESCRIPT INTERFACES

```typescript
// Document response
interface Document {
  id: number;
  title: string;
  parent_document_id: number | null;        // ✅ NEW
  relation_type: 'attachment' | 'secondary_document' | null;  // ✅ NEW
  note_count: number;                       // ✅ NEW
  last_modified: string;                    // ✅ NEW - ISO date
  // ... existing fields
}

// Folder response
interface Folder {
  id: number;
  name: string;
  note_count: number;                       // ✅ NEW
  user_note: string | null;                 // ✅ NEW
  last_modified: string;                    // ✅ NEW - ISO date
  // ... existing fields
}

// Note
interface Note {
  id: number;
  title: string | null;
  content: string;
  user_id: number;
  user_name: string;
  document_id: number | null;
  folder_id: number | null;
  department_id: number | null;
  has_image: boolean;
  image_filename: string | null;
  is_private: boolean;
  is_pinned: boolean;
  color: number;  // 0-9
  created_at: string;
  updated_at: string;
}

// Bulk operations
interface BulkDeleteRequest {
  ids: number[];
}

interface BulkDeleteResponse {
  deleted: number[];
  failed: number[];
}

interface BulkRestoreRequest {
  ids: number[];
}

interface BulkRestoreResponse {
  restored: number[];
  failed: number[];
}
```

---

## ⚡ QUICK EXAMPLES

### Frontend: Create Note with Screenshot
```typescript
async function addNoteWithScreenshot(documentId: number, screenshot: File) {
  const base64 = await fileToBase64(screenshot);
  
  const response = await fetch('/api/notes/create', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      content: 'See screenshot',
      title: 'Issue found',
      document_id: documentId,
      image: base64,
      image_filename: screenshot.name,
      is_pinned: true,
      color: 1  // Red for urgent
    })
  });
  
  return response.json();
}
```

### Frontend: Bulk Delete Documents
```typescript
async function bulkDelete(documentIds: number[]) {
  const response = await fetch('/api/documents/permanent-delete', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ ids: documentIds })
  });
  
  const result = await response.json();
  console.log(`Deleted: ${result.deleted.length}`);
  console.log(`Failed: ${result.failed.length}`);
  return result;
}
```

### Frontend: Update Folder Note
```typescript
async function updateFolderNote(folderId: number, note: string) {
  const response = await fetch(`/api/folders/${folderId}/update`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      params: { user_note: note },
      id: 1
    })
  });
  
  return response.json();
}
```

---

## ✅ VERIFICATION

All systems tested and working:
- ✅ Document APIs with new fields
- ✅ Folder APIs with new fields
- ✅ Notes CRUD operations
- ✅ Bulk delete/restore
- ✅ Dashboard stats corrected
- ✅ Cascade folder delete

**Ready for frontend integration!** 🎉

---

**Updated:** February 11, 2026  
**Odoo:** http://localhost:8070  
**Status:** ✅ Production Ready
