# Notes System - API Documentation

## 📋 Overview

A comprehensive notes system has been added allowing users to add notes to documents and folders with image upload support.

---

## ✨ New Features

### 1. Notes System
- ✅ Create notes linked to documents
- ✅ Create notes linked to folders
- ✅ Standalone notes (without linking)
- ✅ Upload image with note
- ✅ Private or public notes
- ✅ Pin important notes
- ✅ Custom colors for notes

### 2. Update Fields
- ✅ `last_modified` for folders (includes document and note modifications)
- ✅ `last_modified` for documents (includes version and note modifications)
- ✅ `note_count` number of notes for folders and documents
- ✅ `user_note` quick note field for folders

---

## 🔍 Notes in Global Search

Notes are now included in the global search API (`POST /api/search/global`).

**Search filters:**
- Searches in note `title` and `content` fields
- Only returns notes accessible by current user (respects private/public settings)
- Limited by `per_page` parameter

**Response format:**
```json
{
  "success": true,
  "data": [
    {
      "entity_type": "note",
      "id": 15,
      "title": "Important Note",
      "content": "Note content preview (max 200 chars)...",
      "user_name": "Ahmed",
      "document_id": 123,
      "document_title": "Contract",
      "folder_id": 50,
      "folder_name": "FIN-CONTRACT",
      "department_name": "Finance",
      "has_image": true,
      "is_pinned": true,
      "color": 3,
      "created_at": "2026-02-11T12:00:00",
      "updated_at": "2026-02-11T13:30:00"
    },
    {
      "entity_type": "document",
      ...
    },
    {
      "entity_type": "folder",
      ...
    }
  ]
}
```

**Example:**
```bash
curl -X POST "http://localhost:8070/api/search/global" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {"query": "important"},
    "id":1
  }'
```

---

## 🔐 Authentication

All APIs require JWT token in header:

```
Authorization: Bearer <access_token>
```

---

## 📝 Notes APIs

### 1. List Notes

**Endpoint:** `POST /api/notes`  
**Type:** JSON-RPC

**Parameters:**
```json
{
  "document_id": 123,          // Optional - filter by document
  "folder_id": 50,             // Optional - filter by folder
  "user_id": null,             // Default: current user
  "include_private": true,     // Show private notes
  "page": 1,
  "per_page": 50
}
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "Important Note",
      "content": "Note content",
      "user_id": 2,
      "user_name": "Ahmed",
      "document_id": 123,
      "document_title": "Contract",
      "folder_id": 50,
      "folder_name": "FIN-CONTRACT",
      "department_id": 2,
      "department_name": "Finance",
      "has_image": true,
      "image_filename": "screenshot.png",
      "is_private": false,
      "is_pinned": true,
      "color": 3,
      "created_at": "2026-02-11T12:00:00",
      "updated_at": "2026-02-11T13:30:00"
    }
  ],
  "pagination": {
    "total": 45,
    "page": 1,
    "per_page": 50,
    "total_pages": 1
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8070/api/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "document_id": 123,
      "page": 1,
      "per_page": 50
    },
    "id":1
  }'
```

---

### 2. Get Single Note

**Endpoint:** `POST /api/notes/<note_id>`  
**Type:** JSON-RPC

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "Note",
    "content": "Content",
    "user_id": 2,
    "user_name": "Ahmed",
    "document_id": 123,
    "document_title": "Contract",
    "folder_id": 50,
    "folder_name": "FIN-CONTRACT",
    "department_id": 2,
    "department_name": "Finance",
    "image": "base64_encoded_image_string",
    "image_filename": "screenshot.png",
    "is_private": false,
    "is_pinned": true,
    "color": 3,
    "created_at": "2026-02-11T12:00:00",
    "updated_at": "2026-02-11T13:30:00"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8070/api/notes/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

---

### 3. Create Note

**Endpoint:** `POST /api/notes/create`  
**Type:** HTTP (Plain JSON)

**Body:**
```json
{
  "content": "Note content",                        // Required
  "title": "Note title",                           // Optional
  "document_id": 123,                              // Optional
  "folder_id": 50,                                 // Optional
  "department_id": 2,                              // Optional
  "image": "base64_encoded_image",                 // Optional
  "image_filename": "screenshot.png",              // Optional
  "is_private": true,                              // Default true
  "is_pinned": false,                              // Default false
  "color": 0                                       // Default 0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Note created successfully",
  "data": {
    "id": 15,
    "created_at": "2026-02-11T14:00:00"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8070/api/notes/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "content": "This is an important note",
    "title": "Urgent Note",
    "document_id": 123,
    "is_private": false,
    "is_pinned": true,
    "color": 3
  }'
```

---

### 4. Update Note

**Endpoint:** `POST /api/notes/<note_id>/update`  
**Type:** HTTP (Plain JSON)

**Body:**
```json
{
  "title": "Updated title",
  "content": "Updated content",
  "is_private": false,
  "is_pinned": true,
  "color": 5,
  "image": "base64_encoded_new_image",
  "image_filename": "new_image.png"
}
```

**Note:** Only the creator can update the note

**Response:**
```json
{
  "success": true,
  "message": "Note updated successfully",
  "data": {
    "updated_at": "2026-02-11T14:30:00"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8070/api/notes/15/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "content": "Updated content",
    "is_pinned": true
  }'
```

---

### 5. Delete Note

**Endpoint:** `DELETE /api/notes/<note_id>`  
**Type:** HTTP

**Note:** Soft delete - sets `active=False`

**Response:**
```json
{
  "success": true,
  "message": "Note deleted successfully"
}
```

**cURL Example:**
```bash
curl -X DELETE "http://localhost:8070/api/notes/15" \
  -H "Authorization: Bearer <token>"
```

---

## 📁 Folder APIs Updates

### New Fields in Response

#### 1. `POST /api/folders/<folder_id>`
#### 2. `POST /api/folders/<folder_id>/documents`

**Additional Fields:**
```json
{
  "note_count": 5,                                    // Number of notes
  "user_note": "Quick note",                          // User note
  "last_modified": "2026-02-11T14:00:00"             // Last modified
}
```

**Full Response Example:**
```json
{
  "success": true,
  "folder": {
    "id": 50,
    "name": "FIN-CONTRACT-asd1_814",
    "code": "814",
    "description": "Folder description",
    "department_id": 2,
    "department_name": "Finance",
    "document_count": 12,
    "note_count": 5,
    "user_note": "Q1 financial contracts folder",
    "last_modified": "2026-02-11T14:00:00",
    "updated_at": "2026-02-11T13:45:00"
  }
}
```

---

### Update Folder Note

**Endpoint:** `POST /api/folders/<folder_id>/update`  
**Type:** JSON-RPC

**Parameters:**
```json
{
  "user_note": "New folder note",
  "name": "New name",
  "description": "New description"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8070/api/folders/50/update" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "jsonrpc":"2.0",
    "method":"call",
    "params": {
      "user_note": "Important financial contracts folder"
    },
    "id":1
  }'
```

---

## 📄 Document APIs Updates

### New Fields in Response

#### 1. `POST /api/documents` (List)
#### 2. `POST /api/documents/<id>` (Single)

**Additional Fields:**
```json
{
  "note_count": 3,                                   // Number of notes
  "last_modified": "2026-02-11T14:00:00"            // Last modified
}
```

**Response Example:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "title": "Financial Contract",
    "department_id": 2,
    "department_name": "Finance",
    "document_type_id": 5,
    "document_type_name": "Contract",
    "uploader_id": 2,
    "uploader_name": "Ahmed",
    "upload_date": "2026-01-15T10:00:00",
    "status": "active",
    "barcode": "DOC-123",
    "note_count": 3,
    "last_modified": "2026-02-11T14:00:00"
  }
}
```

---

## 🎨 Color Codes

Available codes for notes:

| Code | Color |
|------|-------|
| 0    | Default |
| 1    | Red |
| 2    | Blue |
| 3    | Green |
| 4    | Yellow |
| 5    | Orange |
| 6    | Purple |
| 7    | Pink |
| 8    | Brown |
| 9    | Gray |

---

## 🔒 Permissions

### Notes

- **Create:** Any authenticated user
  
- **Read:**
  - Private notes: Creator only
  - Public notes: Managers and admins in same department
  
- **Update:** Creator only
  
- **Delete:** Creator or admin

### Folder user_note Field

- **Update:** Managers and admins only

---

## 📊 last_modified Calculation

### For Folders
```
last_modified = max(
    folder.write_date,
    max(document.write_date for all documents),
    max(note.write_date for all notes)
)
```

### For Documents
```
last_modified = max(
    document.write_date,
    max(version.write_date for all versions),
    max(note.write_date for all notes)
)
```

---

## ⚠️ Important Notes

1. **Images:**
   - Images must be in Base64 format
   - Recommended max size: 5MB

2. **Private Notes:**
   - By default all notes are private
   - Can be changed to public on create or update

3. **Deletion:**
   - Soft delete (sets active=False)
   - Notes are not permanently deleted from database

4. **Performance:**
   - `last_modified` is computed dynamically (not stored)
   - May impact performance on large folders

---

## 📱 Usage Examples

### Example 1: Create Note with Image

```javascript
const imageBase64 = canvas.toDataURL('image/png').split(',')[1]; // Extract base64

const response = await fetch('http://localhost:8070/api/notes/create', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    content: 'Note with screenshot',
    title: 'Screenshot',
    document_id: 123,
    image: imageBase64,
    image_filename: 'screenshot.png',
    is_private: false,
    color: 3
  })
});
```

### Example 2: List Document Notes

```javascript
const response = await fetch('http://localhost:8070/api/notes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      document_id: 123,
      page: 1,
      per_page: 50
    },
    id: 1
  })
});
```

### Example 3: Update Folder Note

```javascript
const response = await fetch('http://localhost:8070/api/folders/50/update', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      user_note: 'Financial contracts folder - Q1 2026'
    },
    id: 1
  })
});
```

---

## 🔧 Troubleshooting

### Error: "Unauthorized"
- Check JWT token in header

### Error: "Access denied"
- Check user permissions
- Private notes are only accessible by their creator

### Error: "Only creator can update"
- Only the note creator can update it

### Error: "Field 'content' is required"
- Note content is required

---

## 📞 Support

For help or inquiries:

- Site: http://localhost:8070

---

## 🚀 Quick Reference

### All Note Endpoints

```
POST   /api/notes                     - List notes with filters
POST   /api/notes/<id>                - Get single note with image
POST   /api/notes/create              - Create note (with image)
POST   /api/notes/<id>/update         - Update note
DELETE /api/notes/<id>                - Delete note (soft delete)
```

### Updated Folder Endpoints

```
POST   /api/folders/<id>              - Now returns note_count, user_note, last_modified
POST   /api/folders/<id>/documents    - Now returns note_count, user_note, last_modified
POST   /api/folders/<id>/update       - Now accepts user_note parameter
```

### Updated Document Endpoints

```
POST   /api/documents                 - Now returns note_count, last_modified
POST   /api/documents/<id>            - Now returns note_count, last_modified
```

---

## 📋 Testing Checklist

- [ ] Create note without image
- [ ] Create note with image
- [ ] List notes by document
- [ ] List notes by folder
- [ ] Update note
- [ ] Delete note
- [ ] Pin/unpin note
- [ ] Change note color
- [ ] Test private/public access
- [ ] Verify folder note_count
- [ ] Verify document note_count
- [ ] Verify last_modified updates
- [ ] Update folder user_note

---

## 🐛 Fixed Issues

### Database Column Errors (Fixed ✅)
```
Error: column "note_count" does not exist
Error: column "last_modified" does not exist
```

**Solution:** Added `store=False` to computed fields

### Dashboard Stats Incorrect (Fixed ✅)
```
Issue: Dashboard showed 3 documents, API returned 0
```

**Solution:** Added `is_deleted=False` filter to all document queries

---

**Last Updated:** February 11, 2026  
**Version:** 1.1.0  
**Status:** ✅ All systems operational
