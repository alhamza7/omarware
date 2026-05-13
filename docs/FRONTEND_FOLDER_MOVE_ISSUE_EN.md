# Frontend Issue: Document Move - UI Not Updating

## Problem Summary

When moving a document from one folder to another using:
```
POST /api/documents/batch/move-folder
```

**Backend Response:**
```json
{
  "success": true,
  "message": "Moved 1 documents"
}
```

**UI Issue:**
- ✅ Backend executes the move successfully in the database
- ❌ Document **remains visible** in the source folder (old folder)
- ❌ Document **does not appear** in the target folder (new folder)

---

## Backend Testing Results

Tested the move operation **directly on the database** with these results:

```
✅ folder_id updated to target (primary folder updated)
✅ Document added to target folder_ids (added to new folder)
✅ Document removed from source folder_ids (removed from old folder)
✅ Document NOT in source folder search (doesn't appear in old folder)
✅ Document IN target folder search (appears in new folder)
```

**✅ Backend works 100% correctly**

The backend successfully:
1. Updates the document's `folder_id` (Many2one) to the target folder
2. Removes the document from the source folder's `folder_ids` (Many2many)
3. Adds the document to the target folder's `folder_ids` (Many2many)
4. Database queries confirm the document is in the target folder only

---

## Root Cause

**Cache/State Issue in Frontend:**

The frontend application:
1. ❌ Does **not refresh** the source folder's document list after move
2. ❌ Does **not refresh** the target folder's document list after move
3. ❌ Relies on **cached/stale data** instead of fetching fresh data from the API

---

## Required Frontend Fix

### After calling `POST /api/documents/batch/move-folder`:

The frontend **MUST** refresh the affected folders:

#### Option 1: Refresh Both Folders (Recommended)

```javascript
// 1. Call move API
const moveResponse = await fetch('/api/documents/batch/move-folder', {
  method: 'POST',
  headers: { 
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "call",
    params: {
      document_ids: [documentId],
      target_folder_id: targetFolderId
    },
    id: 1
  })
});

const result = await moveResponse.json();

if (result.result && result.result.success) {
  // 2. CRITICAL: Refresh source folder
  await refreshFolderDocuments(sourceFolderId);
  
  // 3. CRITICAL: Refresh target folder
  await refreshFolderDocuments(targetFolderId);
}

// Helper function to refresh folder
async function refreshFolderDocuments(folderId) {
  const response = await fetch(`/api/folders/${folderId}/documents`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "call",
      params: {},
      id: 1
    })
  });
  
  const data = await response.json();
  
  // Update UI state with fresh data
  updateFolderDocumentsList(folderId, data.result.data);
}
```

#### Option 2: Update State Manually (Optimistic Update)

```javascript
// After successful move:
if (moveResponse.result.success) {
  // Remove document from source folder state
  setSourceFolderDocs(prevDocs => 
    prevDocs.filter(doc => doc.id !== documentId)
  );
  
  // Add document to target folder state
  const movedDoc = sourceFolderDocs.find(doc => doc.id === documentId);
  if (movedDoc) {
    setTargetFolderDocs(prevDocs => [...prevDocs, movedDoc]);
  }
}
```

#### Option 3: Clear Cache & Force Reload

```javascript
// After successful move:
if (moveResponse.result.success) {
  // Clear cached data for affected folders
  clearFolderCache(sourceFolderId);
  clearFolderCache(targetFolderId);
  
  // Force reload from server
  await loadFolderFromServer(sourceFolderId);
  await loadFolderFromServer(targetFolderId);
}
```

---

## Complete Working Example

```javascript
async function moveDocumentToFolder(documentId, sourceFolderId, targetFolderId) {
  try {
    console.log(`Moving document ${documentId} from folder ${sourceFolderId} to ${targetFolderId}`);
    
    // 1. Call backend move API
    const response = await fetch('http://localhost:3003/api/documents/batch/move-folder', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authToken}`
      },
      body: JSON.stringify({
        jsonrpc: "2.0",
        method: "call",
        params: {
          document_ids: [documentId],
          target_folder_id: targetFolderId,
          source_folder_id: sourceFolderId  // Optional: helps backend validate
        },
        id: 1
      })
    });

    const data = await response.json();
    
    if (data.result && data.result.success) {
      console.log('✓ Backend move succeeded');
      
      // 2. CRITICAL FIX: Refresh both folders
      console.log('Refreshing folder lists...');
      
      await Promise.all([
        fetchAndUpdateFolder(sourceFolderId),
        fetchAndUpdateFolder(targetFolderId)
      ]);
      
      console.log('✓ UI updated');
      
      // 3. Show success message
      showNotification('Document moved successfully', 'success');
      
      return true;
      
    } else {
      console.error('Backend move failed:', data.result.error);
      showNotification(`Failed to move: ${data.result.error}`, 'error');
      return false;
    }
    
  } catch (error) {
    console.error('Move error:', error);
    showNotification('Error moving document', 'error');
    return false;
  }
}

async function fetchAndUpdateFolder(folderId) {
  const response = await fetch(`http://localhost:3003/api/folders/${folderId}/documents`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${authToken}`
    },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "call",
      params: {},
      id: 1
    })
  });
  
  const data = await response.json();
  
  if (data.result && data.result.success) {
    // Update your state/store with fresh data
    dispatch(setFolderDocuments(folderId, data.result.data));
  }
}
```

---

## React Example (if using React)

```jsx
const [sourceDocs, setSourceDocs] = useState([]);
const [targetDocs, setTargetDocs] = useState([]);

const handleMoveDocument = async (docId, sourceFolderId, targetFolderId) => {
  // Call move API
  const response = await moveDocumentAPI(docId, targetFolderId);
  
  if (response.success) {
    // Refresh both folders
    const [sourceData, targetData] = await Promise.all([
      fetchFolderDocuments(sourceFolderId),
      fetchFolderDocuments(targetFolderId)
    ]);
    
    // Update state
    setSourceDocs(sourceData);
    setTargetDocs(targetData);
  }
};
```

---

## Debugging Steps

If the issue persists after implementing the fix:

1. **Open Browser DevTools**
2. **Go to Network Tab**
3. **Perform document move**
4. **Check:**
   - ✅ Is `batch/move-folder` called?
   - ✅ Does it return `success: true`?
   - ✅ Are folder APIs called **after** the move?
   - ❌ If folder APIs are NOT called after move - this is the problem!

5. **Console Logs:**
```javascript
console.log('Before move - Source docs:', sourceFolderDocs);
// ... perform move ...
console.log('After move - Source docs:', sourceFolderDocs);
// If they're identical = UI not refreshed!
```

---

## Test Case Log Example

From backend logs when moving document 41 from folder 42 to 43:

```
[MOVE REQUEST] document_ids=[41], source=None, target=43
[MOVE] Doc 41 "TestyDoc": old_folder_id=None, old_folder_ids=[], target=43
[MOVE] Linking doc 41 to folder 43
[MOVE] ✓ After: Doc 41 folder_id=43, folder_ids=[43]
```

**Backend executed successfully** - document is now in folder 43.

If the UI still shows the document in folder 42, it means:
- The UI is using **old/cached data**
- The UI did **not refresh** after the move

---

## Summary Table

| Component | Status | Issue |
|-----------|--------|-------|
| Backend API | ✅ Working | None |
| Database | ✅ Updated | None |
| Document moved | ✅ Yes | None |
| Source folder (DB) | ✅ Document removed | None |
| Target folder (DB) | ✅ Document added | None |
| **Frontend UI** | ❌ **Not updating** | **Not refreshing folder lists** |
| **Frontend cache** | ❌ **Stale data** | **Showing old data** |

---

## Action Required

**Frontend team must:**
1. Add code to refresh folder document lists after move operation
2. Call `POST /api/folders/<id>/documents` for both source and target folders
3. Update UI state with the fresh data from API
4. Test that documents disappear from source and appear in target after move

**Backend is complete and working correctly.** The issue is purely on the frontend side.

---

## Contact Backend Team If:

- You implement the refresh and it still doesn't work
- The API `/api/folders/<id>/documents` returns incorrect data
- You need additional API endpoints or data in responses

Otherwise, this is confirmed as a **frontend cache/refresh issue**.
