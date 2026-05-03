# Frontend Integration Guide - Document API Changes

## Date: 2026-02-14

## Overview
New fields have been added to document API responses to clearly identify document types and roles. These changes affect all document-related endpoints.

---

## New Response Fields

### 1. `is_main_document` (Boolean)
Indicates whether the document is a main document or a sub/secondary document.

- `true` - This is a main/primary document (has no parent)
- `false` - This is a sub/secondary document (has a parent)

**Usage:**
```javascript
if (document.is_main_document) {
  // Show as main document
  showMainDocumentBadge();
} else {
  // Show as secondary document
  showSecondaryDocumentBadge();
}
```

### 2. `document_role` (String)
Specifies the document's role within a folder.

**Possible Values:**
- `"main"` - Main document in folder
- `"sub"` - Sub/secondary document
- `"attachment"` - Attachment document
- `"other"` - Other role

**Usage:**
```javascript
const roleIcons = {
  main: '📄',
  sub: '📋',
  attachment: '📎',
  other: '📃'
};

const icon = roleIcons[document.document_role] || '📃';
```

### 3. `relation_type` (String) - UPDATED
Previously returned `null` for main documents, now returns clear values.

**Possible Values:**
- `"main"` - Main document (NEW - was `null` before)
- `"secondary_document"` - Secondary document
- `"attachment"` - Attachment document

**Migration:**
```javascript
// OLD CODE (may break):
if (document.relation_type === null) {
  // Main document
}

// NEW CODE (recommended):
if (document.relation_type === 'main') {
  // Main document
}

// OR use the new field:
if (document.is_main_document) {
  // Main document
}
```

---

## Affected Endpoints

All document endpoints now include these fields:

### 1. GET Documents List
**Endpoint:** `POST /api/documents`

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 85,
      "title": "Main Document.pdf",
      "parent_document_id": null,
      "is_main_document": true,
      "document_role": "main",
      "relation_type": "main",
      ...
    },
    {
      "id": 86,
      "title": "Sub Document.pdf",
      "parent_document_id": 85,
      "is_main_document": false,
      "document_role": "sub",
      "relation_type": "secondary_document",
      ...
    }
  ]
}
```

### 2. GET Single Document
**Endpoint:** `POST /api/documents/<document_id>`

**Response:** Same structure as above

### 3. GET Trash Documents
**Endpoint:** `POST /api/documents/trash`

**Response:** Same structure as above

---

## UI/UX Recommendations

### Document List Display

```javascript
function renderDocumentRow(document) {
  const badge = document.is_main_document 
    ? '<span class="badge badge-primary">Main</span>'
    : '<span class="badge badge-secondary">Sub</span>';
  
  const indentation = document.is_main_document ? '' : 'ml-4';
  
  return `
    <div class="${indentation}">
      ${badge}
      <span>${document.title}</span>
    </div>
  `;
}
```

### Folder View Hierarchy

```javascript
function organizeDocumentsByRole(documents) {
  return {
    main: documents.filter(d => d.document_role === 'main'),
    secondary: documents.filter(d => d.document_role === 'sub'),
    attachments: documents.filter(d => d.document_role === 'attachment')
  };
}

// Display
const organized = organizeDocumentsByRole(documents);
console.log(`Main: ${organized.main.length}`);
console.log(`Secondary: ${organized.secondary.length}`);
console.log(`Attachments: ${organized.attachments.length}`);
```

### Filter by Document Type

```javascript
// Filter main documents only
const mainDocuments = allDocuments.filter(d => d.is_main_document);

// Filter secondary documents only
const secondaryDocuments = allDocuments.filter(d => !d.is_main_document);

// Filter by specific role
const attachments = allDocuments.filter(d => d.document_role === 'attachment');
```

---

## Move Folder API Changes

### Enhanced Behavior

The move folder API now intelligently handles main vs secondary documents:

**Main Documents:**
- Moves the folder_id reference
- Updates folder_ids relationships
- Becomes the primary document in target folder

**Secondary Documents:**
- Does NOT change folder_id
- Updates folder_ids relationships only
- Automatically links to target folder's main document
- Preserves secondary/sub document status

### Frontend Validation

Before allowing document move, check document type:

```javascript
function canMoveToFolder(document, targetFolder) {
  if (document.is_main_document) {
    // Check if target folder already has a main document
    const hasMainDoc = targetFolder.documents.some(d => d.is_main_document);
    if (hasMainDoc) {
      return {
        allowed: false,
        reason: 'Target folder already has a main document'
      };
    }
  }
  
  return { allowed: true };
}
```

### UI Indicators During Move

```javascript
function showMovePreview(documents, targetFolder) {
  const mainDocs = documents.filter(d => d.is_main_document);
  const subDocs = documents.filter(d => !d.is_main_document);
  
  return `
    Moving:
    - ${mainDocs.length} main document(s)
    - ${subDocs.length} secondary document(s)
    
    To: ${targetFolder.name}
    
    ${subDocs.length > 0 ? 
      'Note: Secondary documents will be linked to target folder\'s main document' 
      : ''}
  `;
}
```

---

## Duplicate Name Validation

### Error Response

When creating a document with a duplicate name:

```json
{
  "success": false,
  "error": "A document with the name \"document.pdf\" already exists in this department and document type. Please use a different name."
}
```

### Frontend Handling

```javascript
async function uploadDocument(formData) {
  try {
    const response = await api.post('/api/documents/upload', formData);
    
    if (!response.success) {
      if (response.error.includes('already exists')) {
        // Show user-friendly duplicate name message
        showError('Document name already exists. Please choose a different name.');
        highlightField('documentName');
      } else {
        showError(response.error);
      }
    }
  } catch (error) {
    console.error('Upload failed:', error);
  }
}
```

### Real-time Name Validation

```javascript
// Optional: Check name availability before upload
async function checkDocumentNameAvailable(name, departmentId, documentTypeId) {
  // This would require a new API endpoint (future enhancement)
  // For now, just attempt upload and handle error
  return true;
}
```

---

## Folder Auto-Deletion

### Behavior

When a main document is deleted:
- If folder has no other active documents → Folder is automatically deleted
- If folder has secondary documents → Folder is kept

### Frontend Considerations

```javascript
function showDeleteWarning(document) {
  if (document.is_main_document) {
    const folder = getDocumentFolder(document.folder_id);
    const otherDocs = folder.documents.filter(d => d.id !== document.id);
    
    if (otherDocs.length === 0) {
      return 'Warning: This is the only document in the folder. The folder will be automatically deleted.';
    } else {
      return `Warning: This folder has ${otherDocs.length} other document(s) that will remain.`;
    }
  }
  
  return 'Are you sure you want to delete this document?';
}
```

---

## TypeScript Interfaces

```typescript
interface Document {
  id: number;
  title: string;
  department_id: number;
  department_name: string;
  document_type_id: number;
  document_type_name: string;
  uploader_id: number;
  uploader_name: string;
  upload_date: string;
  status: 'draft' | 'active' | 'archived' | 'trash';
  confidentiality_level: 'public' | 'internal' | 'confidential' | 'strict';
  barcode: string;
  po_number: string | false;
  bl_number: string | false;
  container_number: string | false;
  invoice_number: string | false;
  envoy_number: string | false;
  file_name: string | null;
  file_size: number;
  folder_id: number | null;
  folder_name: string | null;
  parent_document_id: number | null;
  
  // NEW FIELDS
  is_main_document: boolean;
  document_role: 'main' | 'sub' | 'attachment' | 'other';
  relation_type: 'main' | 'secondary_document' | 'attachment';
  
  note_count: number;
  last_modified: string | null;
}
```

---

## Migration Checklist

- [ ] Update document list component to show new badges/indicators
- [ ] Update move document validation logic
- [ ] Handle duplicate name errors in upload form
- [ ] Update delete confirmation messages for main documents
- [ ] Add folder hierarchy visualization
- [ ] Test document move scenarios (main → main, sub → sub, etc.)
- [ ] Update TypeScript/Flow types
- [ ] Update documentation/tooltips

---

## Common Patterns

### Display Document Hierarchy

```javascript
function renderDocumentTree(documents) {
  const tree = {};
  
  // Group by parent
  documents.forEach(doc => {
    if (doc.is_main_document) {
      tree[doc.id] = {
        main: doc,
        children: []
      };
    }
  });
  
  // Add children
  documents.forEach(doc => {
    if (!doc.is_main_document && doc.parent_document_id) {
      if (tree[doc.parent_document_id]) {
        tree[doc.parent_document_id].children.push(doc);
      }
    }
  });
  
  return tree;
}
```

### Filter Bar

```javascript
const documentTypeFilters = [
  { label: 'All Documents', value: null },
  { label: 'Main Documents', value: 'main', filter: d => d.is_main_document },
  { label: 'Secondary Documents', value: 'sub', filter: d => !d.is_main_document && d.document_role === 'sub' },
  { label: 'Attachments', value: 'attachment', filter: d => d.document_role === 'attachment' }
];
```

---

## Support & Questions

For any issues or questions regarding these changes:
1. Check the main bugfix document: `BUGFIX_FOLDER_MOVE_AND_VALIDATIONS.md`
2. Review API documentation: `NOTES_SYSTEM_API_DOCUMENTATION_EN.md`
3. Test in development environment first
4. Report any inconsistencies or bugs

---

## Version

- **API Version:** 1.1.0
- **Changes Date:** 2026-02-14
- **Backward Compatible:** Yes (with minor updates needed for null checks)
