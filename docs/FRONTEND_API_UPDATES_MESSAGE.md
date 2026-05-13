# 📢 Frontend Team - API Updates & Type Changes

**Date:** February 12, 2026  
**Priority:** High - Type definitions and UI updates required

---

## 🎯 Summary

Multiple fields have been **added** to document and folder APIs. Please update your TypeScript interfaces and UI to use these new fields.

---

## 📄 DOCUMENT API CHANGES

### All Document Endpoints Updated:
- `POST /api/documents` (list)
- `POST /api/documents/<id>` (single document)
- `POST /api/folders/<id>/documents` (folder documents)
- `POST /api/search` (search results)
- `POST /api/search/global` (global search)

### NEW FIELDS ADDED:

```typescript
interface Document {
  // ... existing fields ...
  
  // ✅ NEW: Reference Numbers
  po_number: string | null;           // Purchase Order Number
  bl_number: string | null;           // Bill of Lading Number
  container_number: string | null;    // Container Number
  invoice_number: string | null;      // Invoice Number
  envoy_number: string | null;        // Envoy Number
  
  // ✅ NEW: Folder Information
  folder_id: number | null;           // Primary folder ID
  folder_name: string | null;         // Primary folder name
  
  // ✅ NEW: Document Relationships
  parent_document_id: number | null;  // Parent document (for sub-docs/attachments)
  relation_type: 'attachment' | 'secondary_document' | null;
  
  // ✅ NEW: Notes & Updates
  note_count: number;                 // Number of notes
  last_modified: string;              // ISO datetime - last change to doc/versions/notes
}
```

---

## 🔴 IMPORTANT: parent_document_id & relation_type

### How These Fields Work:

| Document Type | parent_document_id | relation_type | folder_id |
|--------------|-------------------|---------------|-----------|
| **Main Document** | `null` | `null` | Folder ID |
| **Sub Document** | Main doc ID | `"secondary_document"` | Same folder as main |
| **Attachment** | Document ID | `"attachment"` | Same folder |

### ⚠️ Current Issue with Your Data:

Looking at your response:
```json
{
  "id": 66,
  "title": "sub document",
  "parent_document_id": null,  // ❌ Should be 65
  "relation_type": null         // ❌ Should be "secondary_document"
}
```

**Why this is happening:**
- When uploading a sub document, the **frontend must send** `parent_document_id` in the upload request
- The backend doesn't automatically link sub documents to main documents just because they're in the same folder
- This is **by design** - parent relationships must be explicitly set

### 🔧 How to Fix:

#### Option 1: Set parent during upload (Recommended)
```typescript
// When uploading sub document
const uploadData = {
  title: "Sub document",
  department_id: 4,
  document_type_id: 5,
  folder_id: 60,
  parent_document_id: 65,        // ✅ Add this
  upload_kind: "sub",            // ✅ Add this
  file_data: base64,
  file_name: "doc.pdf"
};
```

#### Option 2: Set parent after upload
```typescript
// After uploading document
await fetch('/api/documents/66/set-parent', {
  method: 'POST',
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      parent_document_id: 65
    },
    id: 1
  })
});
```

---

## 📁 FOLDER API CHANGES

### All Folder Endpoints Updated:
- `POST /api/folders/<id>`
- `POST /api/folders/<id>/documents`

### NEW FIELDS ADDED:

```typescript
interface Folder {
  // ... existing fields ...
  
  // ✅ NEW: Notes
  note_count: number;                 // Number of notes
  user_note: string | null;           // Quick note field
  
  // ✅ NEW: Updates
  last_modified: string;              // ISO datetime - last change to folder/docs/notes
}
```

### Update Folder Note:
```typescript
await fetch(`/api/folders/${folderId}/update`, {
  method: 'POST',
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      user_note: "Your note here"
    },
    id: 1
  })
});
```

---

## 📝 NOTES SYSTEM - NEW APIs

### TypeScript Interface:

```typescript
interface Note {
  id: number;
  title: string | null;
  content: string;
  user_id: number;
  user_name: string;
  document_id: number | null;
  document_title: string | null;
  folder_id: number | null;
  folder_name: string | null;
  department_id: number | null;
  department_name: string | null;
  has_image: boolean;
  image_filename: string | null;
  is_private: boolean;
  is_pinned: boolean;
  color: number;  // 0-9
  created_at: string;
  updated_at: string;
}
```

### New Endpoints:

```typescript
// 1. List notes
POST /api/notes
{
  document_id?: number,
  folder_id?: number,
  page?: number,
  per_page?: number
}

// 2. Create note
POST /api/notes/create
{
  content: string,           // Required
  title?: string,
  document_id?: number,
  folder_id?: number,
  image?: string,            // Base64
  image_filename?: string,
  is_private?: boolean,      // Default: true
  is_pinned?: boolean,       // Default: false
  color?: number             // 0-9, Default: 0
}

// 3. Update note
POST /api/notes/<id>/update
{
  content?: string,
  title?: string,
  is_pinned?: boolean,
  color?: number,
  image?: string
}

// 4. Delete note
DELETE /api/notes/<id>
```

---

## 🗑️ BULK OPERATIONS - NEW APIs

### Bulk Permanent Delete:
```typescript
POST /api/documents/permanent-delete

Request: { ids: number[] }
Response: { deleted: number[], failed: number[] }
```

### Bulk Restore:
```typescript
POST /api/documents/restore

Request: { ids: number[] }
Response: { restored: number[], failed: number[] }
```

---

## 🔍 SEARCH UPDATES

### Global Search Now Includes Notes:

```typescript
interface SearchResult {
  entity_type: 'folder' | 'document' | 'attachment' | 'note';  // ✅ 'note' added
  id: number;
  title: string;
  // ... other fields depend on entity_type
}
```

When `entity_type === 'note'`:
```typescript
{
  entity_type: 'note',
  id: 15,
  title: 'Note title',
  content: 'Content preview (max 200 chars)...',
  user_name: 'Ahmed',
  document_id: 123,
  folder_id: 50,
  has_image: true,
  is_pinned: true,
  color: 3,
  created_at: '2026-02-11T...',
  updated_at: '2026-02-11T...'
}
```

---

## 🎨 UI RECOMMENDATIONS

### 1. Display Reference Numbers
```tsx
<div className="document-references">
  {doc.po_number && <Badge>PO: {doc.po_number}</Badge>}
  {doc.bl_number && <Badge>BL: {doc.bl_number}</Badge>}
  {doc.container_number && <Badge>Container: {doc.container_number}</Badge>}
  {doc.invoice_number && <Badge>Invoice: {doc.invoice_number}</Badge>}
  {doc.envoy_number && <Badge>Envoy: {doc.envoy_number}</Badge>}
</div>
```

### 2. Show Folder Path
```tsx
{doc.folder_id && (
  <div className="folder-path">
    📁 {doc.folder_name}
  </div>
)}
```

### 3. Document Type Badge
```tsx
{doc.relation_type === 'secondary_document' && (
  <Badge color="blue">Sub Document</Badge>
)}
{doc.relation_type === 'attachment' && (
  <Badge color="orange">Attachment</Badge>
)}
{!doc.relation_type && (
  <Badge color="green">Main Document</Badge>
)}
```

### 4. Parent Document Link
```tsx
{doc.parent_document_id && (
  <Link to={`/documents/${doc.parent_document_id}`}>
    ↑ Parent Document
  </Link>
)}
```

### 5. Notes Indicator
```tsx
{doc.note_count > 0 && (
  <Badge>
    📝 {doc.note_count} {doc.note_count === 1 ? 'note' : 'notes'}
  </Badge>
)}
```

### 6. Last Modified
```tsx
<span className="last-modified">
  Last modified: {formatRelativeTime(doc.last_modified)}
</span>
```

---

## ⚠️ BREAKING CHANGES & ACTION ITEMS

### 1. Update TypeScript Interfaces ✅
Add all new fields to your Document and Folder interfaces

### 2. Fix Sub Document Creation Logic ⚠️
**Current issue:** When uploading sub documents, you're not sending `parent_document_id`

**Fix:** Add to upload payload:
```typescript
const uploadPayload = {
  // ... existing fields ...
  parent_document_id: mainDocumentId,  // ✅ Add this for sub documents
  upload_kind: "sub",                   // ✅ Add this
  folder_id: folderId                   // ✅ Already have
};
```

### 3. Use Set Parent API if Needed
If you need to link existing documents:
```typescript
POST /api/documents/<document_id>/set-parent
{
  parent_document_id: 65  // or null to clear
}
```

### 4. Handle null Values
Many fields can be `null`. Update your UI to handle:
```typescript
// Good
{doc.po_number || 'N/A'}

// Better
{doc.po_number && <span>PO: {doc.po_number}</span>}
```

---

## 🧪 TESTING CHECKLIST

- [ ] Verify all new fields appear in document list
- [ ] Verify all new fields appear in single document
- [ ] Test creating sub document with parent_document_id
- [ ] Test folder_id displays correctly
- [ ] Test reference numbers display
- [ ] Test notes count badge
- [ ] Test last_modified timestamp
- [ ] Test relation_type badge display
- [ ] Test global search includes notes
- [ ] Test bulk delete/restore

---

## 📚 COMPLETE FIELD LIST - DOCUMENT

```typescript
interface Document {
  // Basic Info
  id: number;
  title: string;
  status: 'draft' | 'active' | 'archived';
  
  // Department & Type
  department_id: number;
  department_name: string;
  document_type_id: number;
  document_type_name: string;
  
  // Upload Info
  uploader_id: number;
  uploader_name: string;
  upload_date: string;
  confidentiality_level: 'public' | 'internal' | 'confidential' | 'restricted';
  
  // File Info
  file_name: string | null;
  file_size: number;
  barcode: string;
  
  // Reference Numbers (NEW)
  po_number: string | null;
  bl_number: string | null;
  container_number: string | null;
  invoice_number: string | null;
  envoy_number: string | null;
  
  // Folder (NEW)
  folder_id: number | null;
  folder_name: string | null;
  
  // Relationships (NEW)
  parent_document_id: number | null;
  relation_type: 'attachment' | 'secondary_document' | null;
  
  // Metadata (NEW)
  note_count: number;
  last_modified: string;
  
  // Lock Status
  is_locked: boolean;
  ocr_status: 'pending' | 'processing' | 'completed' | 'failed';
}
```

---

## 📚 COMPLETE FIELD LIST - FOLDER

```typescript
interface Folder {
  // Basic Info
  id: number;
  name: string;
  code: string;
  description: string | null;
  
  // Hierarchy
  parent_id: number | null;
  parent_name: string | null;
  parent_path: string;
  full_path: string;
  level: number;
  child_count: number;
  
  // Department
  department_id: number;
  department_name: string;
  
  // Documents
  document_count: number;
  all_document_count: number;
  
  // Notes (NEW)
  note_count: number;
  user_note: string | null;
  last_modified: string;
  
  // Access Control
  restricted: boolean;
  allowed_users: Array<{id: number, name: string}>;
  allowed_groups: Array<{id: number, name: string}>;
  
  // UI
  color: number;
  icon: string;
  sequence: number;
  active: boolean;
  
  // Metadata
  created_by: string | null;
  create_date: string;
  write_date: string;
}
```

---

## 🚨 CRITICAL: Sub Document Upload Issue

### Current Problem:

Your sub documents have `parent_document_id: null` because you're not sending it during upload.

### Solution:

When creating sub documents, **you MUST send** `parent_document_id`:

```typescript
// Upload main document first
const mainDoc = await uploadDocument({
  title: "Main Document",
  department_id: 4,
  document_type_id: 5,
  folder_id: 60,
  upload_kind: "main",
  file_data: base64,
  file_name: "main.pdf"
});

// Then upload sub document WITH parent_document_id
const subDoc = await uploadDocument({
  title: "Sub Document",
  department_id: 4,
  document_type_id: 5,
  folder_id: 60,
  parent_document_id: mainDoc.id,  // ✅ REQUIRED for sub docs
  upload_kind: "sub",              // ✅ Set type
  file_data: base64,
  file_name: "sub.pdf"
});
```

### Or Use Set Parent API:

If documents already exist without parent:
```typescript
// Link document 66 to main document 65
await fetch('/api/documents/66/set-parent', {
  method: 'POST',
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      parent_document_id: 65
    },
    id: 1
  })
});
```

---

## 🎨 UI IMPLEMENTATION EXAMPLES

### Document Card Component:

```tsx
function DocumentCard({ doc }: { doc: Document }) {
  return (
    <div className="document-card">
      {/* Type Badge */}
      {doc.relation_type === 'secondary_document' && (
        <Badge color="blue">Sub Document</Badge>
      )}
      {doc.relation_type === 'attachment' && (
        <Badge color="orange">Attachment</Badge>
      )}
      {!doc.relation_type && (
        <Badge color="green">Main</Badge>
      )}
      
      {/* Title */}
      <h3>{doc.title}</h3>
      
      {/* Folder */}
      {doc.folder_id && (
        <div className="folder-info">
          📁 {doc.folder_name}
        </div>
      )}
      
      {/* Parent Link */}
      {doc.parent_document_id && (
        <Link to={`/documents/${doc.parent_document_id}`}>
          ↑ View Parent Document
        </Link>
      )}
      
      {/* Reference Numbers */}
      <div className="references">
        {doc.po_number && <span>PO: {doc.po_number}</span>}
        {doc.bl_number && <span>BL: {doc.bl_number}</span>}
        {doc.invoice_number && <span>INV: {doc.invoice_number}</span>}
      </div>
      
      {/* Notes Count */}
      {doc.note_count > 0 && (
        <Badge>📝 {doc.note_count}</Badge>
      )}
      
      {/* Last Modified */}
      <span className="text-muted">
        Modified {formatRelativeTime(doc.last_modified)}
      </span>
    </div>
  );
}
```

### Search Result Display:

```tsx
function SearchResult({ item }: { item: SearchResult }) {
  return (
    <div className="search-result">
      {/* Icon based on type */}
      {item.entity_type === 'folder' && '📁'}
      {item.entity_type === 'document' && '📄'}
      {item.entity_type === 'attachment' && '📎'}
      {item.entity_type === 'note' && '📝'}
      
      {/* Content */}
      <div>
        <strong>{item.title}</strong>
        
        {/* Show note content preview */}
        {item.entity_type === 'note' && (
          <p className="note-preview">{item.content}</p>
        )}
        
        {/* Show linked document/folder for notes */}
        {item.entity_type === 'note' && item.document_title && (
          <small>📄 {item.document_title}</small>
        )}
        {item.entity_type === 'note' && item.folder_name && (
          <small>📁 {item.folder_name}</small>
        )}
      </div>
    </div>
  );
}
```

---

## 🔧 MIGRATION CHECKLIST

### Step 1: Update Type Definitions
- [ ] Update Document interface
- [ ] Update Folder interface
- [ ] Add Note interface
- [ ] Update SearchResult union type

### Step 2: Update Upload Logic
- [ ] Add `parent_document_id` when uploading sub documents
- [ ] Add `upload_kind` parameter
- [ ] Test main document upload
- [ ] Test sub document upload with parent

### Step 3: Update UI Components
- [ ] Add reference number display
- [ ] Add folder name display
- [ ] Add document type badges (main/sub/attachment)
- [ ] Add parent document link
- [ ] Add notes count badge
- [ ] Add last_modified display
- [ ] Update search results to handle notes

### Step 4: Test Everything
- [ ] Test document list shows all new fields
- [ ] Test sub document shows correct parent_document_id
- [ ] Test folder shows note_count
- [ ] Test global search returns notes
- [ ] Test bulk operations
- [ ] Test notes CRUD

---

## 📞 QUESTIONS?

If you need clarification on:
- How to set parent_document_id
- How relation_type works
- Notes system usage
- Any field meaning

Contact backend team immediately!

---

## ✅ READY TO USE

All backend changes are deployed and running on:
- **Backend:** http://192.168.116.15:8070
- **Via Proxy:** http://localhost:3003

**Start updating your types and UI now!** 🚀

---

**Document Version:** 1.2.0  
**Date:** February 12, 2026  
**Status:** ✅ Production Ready
