# Frontend Issue: Document Move - UI Not Updating

## المشكلة / Problem

عند نقل مستند من مجلد إلى آخر باستخدام:
```
POST /api/documents/batch/move-folder
```

When moving a document from one folder to another using the batch move API:

**الاستجابة / Response:**
```json
{
  "success": true,
  "message": "Moved 1 documents"
}
```

**المشكلة في الواجهة / UI Issue:**
- ✅ الـ backend ينفذ النقل بنجاح في قاعدة البيانات
- ❌ المستند **يبقى ظاهراً** في المجلد القديم (source folder)
- ❌ المستند **لا يظهر** في المجلد الجديد (target folder)

---

## اختبار الـ Backend / Backend Testing

تم اختبار عملية النقل **مباشرة على قاعدة البيانات** والنتيجة:

```
✅ folder_id updated to target (المجلد الرئيسي محدّث)
✅ Document added to target folder_ids (مضاف للمجلد الجديد)
✅ Document removed from source folder_ids (محذوف من المجلد القديم)
✅ Document NOT in source folder search (لا يظهر في بحث المجلد القديم)
✅ Document IN target folder search (يظهر في بحث المجلد الجديد)
```

**✅ الـ Backend يعمل بشكل صحيح 100%**

---

## السبب المتوقع / Root Cause

**Cache/State Issue in Frontend:**

الواجهة الأمامية:
1. ❌ **لا تُحدّث** قائمة المستندات في المجلد المصدر بعد النقل
2. ❌ **لا تُحدّث** قائمة المستندات في المجلد الهدف بعد النقل
3. ❌ تعتمد على بيانات **cached** (قديمة) بدلاً من إعادة جلب البيانات من الـ API

---

## الحل المطلوب من الـ Frontend / Required Frontend Fix

### بعد استدعاء `POST /api/documents/batch/move-folder`:

يجب على الواجهة تحديث قوائم المجلدات المتأثرة:

#### Option 1: Refresh Both Folders (Recommended)

```javascript
// 1. Move document
const moveResponse = await fetch('/api/documents/batch/move-folder', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    jsonrpc: "2.0",
    method: "call",
    params: {
      document_ids: [documentId],
      target_folder_id: targetFolderId
    }
  })
});

if (moveResponse.success) {
  // 2. Refresh source folder documents
  await refreshFolderDocuments(sourceFolderId);
  
  // 3. Refresh target folder documents
  await refreshFolderDocuments(targetFolderId);
}

// Helper function
async function refreshFolderDocuments(folderId) {
  const response = await fetch(`/api/folders/${folderId}/documents`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      jsonrpc: "2.0",
      method: "call",
      params: {}
    })
  });
  
  const data = await response.json();
  // Update UI with data.result.data
  updateFolderUI(folderId, data.result.data);
}
```

#### Option 2: Update State Manually

```javascript
// After successful move:
if (moveResponse.success) {
  // Remove document from source folder state
  setSourceFolderDocs(prev => prev.filter(doc => doc.id !== documentId));
  
  // Add document to target folder state
  setTargetFolderDocs(prev => [...prev, movedDocument]);
}
```

#### Option 3: Clear Cache & Force Reload

```javascript
// After successful move:
if (moveResponse.success) {
  // Clear any cached folder data
  clearFolderCache(sourceFolderId);
  clearFolderCache(targetFolderId);
  
  // Reload both folders
  await loadFolder(sourceFolderId);
  await loadFolder(targetFolderId);
}
```

---

## مثال كامل / Complete Example

```javascript
async function moveDocumentBetweenFolders(documentId, sourceFolderId, targetFolderId) {
  try {
    // 1. Call move API
    const response = await fetch('/api/documents/batch/move-folder', {
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
          target_folder_id: targetFolderId,
          source_folder_id: sourceFolderId  // Optional but helps backend validate
        },
        id: 1
      })
    });

    const data = await response.json();
    
    if (data.result && data.result.success) {
      // 2. Success - update UI
      console.log('✓ Document moved successfully in backend');
      
      // 3. CRITICAL: Refresh both folders to reflect the change
      await Promise.all([
        fetchFolderDocuments(sourceFolderId),  // Remove from source
        fetchFolderDocuments(targetFolderId)   // Add to target
      ]);
      
      // 4. Show success message
      showToast('Document moved successfully', 'success');
      
    } else {
      console.error('Move failed:', data.result.error);
      showToast('Failed to move document', 'error');
    }
    
  } catch (error) {
    console.error('Move error:', error);
    showToast('Error moving document', 'error');
  }
}
```

---

## نقاط مهمة للـ Frontend / Key Points

1. **Backend works correctly** - عملية النقل تنفذ بنجاح في قاعدة البيانات
2. **UI must refresh** - الواجهة يجب أن تُحدّث القوائم بعد النقل
3. **Fetch both folders** - استدعِ API لكل من المجلد المصدر والهدف
4. **Clear cache if any** - امسح أي cache للمجلدات المتأثرة

---

## APIs المطلوبة لتحديث الواجهة / Required APIs

### 1. Get folder documents:
```
POST /api/folders/<folder_id>/documents
```

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 41,
      "title": "Document name",
      "folder_role": "main",
      ...
    }
  ]
}
```

### 2. Or use general documents API with folder filter:
```
POST /api/documents
Params: { "folder_id": 42 }
```

---

## خطوات التصحيح / Debugging Steps

إذا المشكلة مستمرة بعد تطبيق الحل:

1. **افتح Developer Console في المتصفح**
2. **راقب Network Tab** عند نقل المستند
3. **تحقق من:**
   - ✅ هل يتم استدعاء `batch/move-folder`؟
   - ✅ هل الاستجابة `success: true`؟
   - ✅ هل يتم استدعاء API لتحديث قوائم المجلدات بعد النقل؟
   - ❌ إذا لم يتم استدعاء API للتحديث - هذه المشكلة!

4. **Console Logs:**
```javascript
console.log('Before move - Source folder docs:', sourceFolderDocs);
// ... perform move ...
console.log('After move - Source folder docs:', sourceFolderDocs);
// If they're the same = not refreshed!
```

---

## الخلاصة / Summary

| Item | Status |
|------|--------|
| Backend move operation | ✅ Works correctly |
| Database updated | ✅ Document moved successfully |
| Source folder (backend) | ✅ Document removed |
| Target folder (backend) | ✅ Document added |
| **Frontend UI update** | ❌ **Not refreshing after move** |
| **Frontend cache** | ❌ **Showing stale data** |

**Fix required:** Frontend must call folder documents API after move to refresh the UI.

---

## Contact Backend if:

- You implement the refresh and it still doesn't work
- The API `/api/folders/<id>/documents` returns wrong data
- You need additional fields in the response

Otherwise, this is a **frontend refresh/cache issue** that needs to be fixed in the UI code.
