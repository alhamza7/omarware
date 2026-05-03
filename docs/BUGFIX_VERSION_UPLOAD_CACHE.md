# Bug Fix: Version Upload - Preview Shows Old File

## Date: 2026-02-14

## Problem

After uploading a new document version:
- ✅ Upload succeeds (HTTP 200)
- ✅ New version created in database
- ✅ `current_version_id` updated correctly
- ❌ **Preview still shows OLD file**

### Database Verification

```sql
-- Document 98
current_version_id = 89 ✅ (updated)

-- Versions
Version 4: file-sample_150kB.pdf (14:22:00) ← NEW
Version 3: file-sample_150kB.pdf (14:21:07)
Version 2: file-sample_150kB.pdf (14:19:26)
Version 1: d - Copy (26).pdf (original)
```

**Backend is correct**, but preview shows old file.

---

## Root Causes

### 1. Backend Cache Issue ✓ FIXED

**Problem:** After `document.write()`, the document object still had cached `current_version_id` value.

**Fix:** Added cache invalidation:
```python
# Update document current version
document.write({
    'current_version_id': version.id,
    'is_locked': False,
})

# Invalidate cache and refresh to get updated current_version_id
document.invalidate_recordset(['current_version_id'])
document = request.env['nbs.document'].browse(document_id)
```

### 2. Browser Cache Issue ✓ FIXED

**Problem:** Browser caches the downloaded file. Same URL = cached file.

**Fix:** Added no-cache headers to download endpoint:
```python
return request.make_response(
    base64.b64decode(file_data),
    headers=[
        ('Content-Type', 'application/octet-stream'),
        ('Content-Disposition', f'attachment; filename="{file_name}"'),
        ('Cache-Control', 'no-cache, no-store, must-revalidate'),
        ('Pragma', 'no-cache'),
        ('Expires', '0'),
    ]
)
```

### 3. Frontend Cache Busting 🔧 FRONTEND ACTION NEEDED

**Problem:** Frontend uses same URL for preview, browser serves cached version.

**Fix:** Frontend should add timestamp parameter to force refresh.

---

## Frontend Solution

### JavaScript: Add Timestamp to Download URL

```javascript
function getDocumentPreviewUrl(documentId, versionId = null) {
  const timestamp = Date.now();  // Current timestamp
  const baseUrl = `/api/documents/${documentId}/download`;
  
  if (versionId) {
    return `${baseUrl}?version_id=${versionId}&t=${timestamp}`;
  } else {
    return `${baseUrl}?t=${timestamp}`;
  }
}

// Usage
const previewUrl = getDocumentPreviewUrl(98);
// Result: /api/documents/98/download?t=1708178400000

// After upload, generate NEW URL with NEW timestamp
const newPreviewUrl = getDocumentPreviewUrl(98);
// Result: /api/documents/98/download?t=1708178500000
// Different URL → Forces browser to fetch fresh file
```

### React: Force Re-render After Upload

```jsx
const DocumentPreview = ({ documentId }) => {
  const [cacheKey, setCacheKey] = useState(Date.now());
  
  const handleVersionUpload = async (file) => {
    const result = await uploadVersion(documentId, file);
    
    if (result.success) {
      // Force preview to reload with new cache key
      setCacheKey(Date.now());
      
      // Or use timestamp from response
      setCacheKey(result.data.timestamp);
    }
  };
  
  return (
    <div>
      <iframe 
        src={`/api/documents/${documentId}/download?t=${cacheKey}`}
        key={cacheKey}  // Force re-mount
      />
      <button onClick={handleVersionUpload}>Upload New Version</button>
    </div>
  );
};
```

### Vue: Reactive Cache Key

```vue
<template>
  <div>
    <iframe 
      :src="`/api/documents/${documentId}/download?t=${cacheKey}`"
      :key="cacheKey"
    />
    <button @click="uploadNewVersion">Upload</button>
  </div>
</template>

<script>
export default {
  data() {
    return {
      documentId: 98,
      cacheKey: Date.now()
    }
  },
  methods: {
    async uploadNewVersion() {
      const result = await this.uploadVersion();
      if (result.success) {
        // Update cache key to force preview refresh
        this.cacheKey = Date.now();
        // Or use result.data.timestamp
      }
    }
  }
}
</script>
```

---

## Updated Response Format

After version upload, the response now includes cache-busting data:

```json
{
  "success": true,
  "data": {
    "version_id": 89,
    "version_number": 4,
    "file_name": "file-sample_150kB.pdf",
    "current_version_id": 89,
    "upload_date": "2026-02-14T14:22:00",
    "timestamp": "2026-02-14T14:22:01",  // ← Use this for cache busting!
    "message": "Version 4 uploaded successfully"
  }
}
```

**Frontend should use `timestamp` in preview URL:**
```javascript
const previewUrl = `/api/documents/${docId}/download?t=${result.data.timestamp}`;
```

---

## Complete Frontend Flow

### Step 1: Upload New Version

```javascript
const uploadResult = await fetch('/api/documents/98/upload-version', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    params: {
      file_data: base64FileData,
      file_name: 'document.pdf',
      unlock_token: '',
      change_description: 'Updated file'
    },
    id: 1
  })
});

const result = await uploadResult.json();
```

### Step 2: Update Preview URL

```javascript
if (result.result.success) {
  const data = result.result.data;
  
  // Method 1: Use timestamp from response
  const newUrl = `/api/documents/98/download?t=${data.timestamp}`;
  
  // Method 2: Use current_version_id
  const newUrl = `/api/documents/98/download?version_id=${data.current_version_id}&t=${Date.now()}`;
  
  // Method 3: Use version_id
  const newUrl = `/api/documents/98/download?version_id=${data.version_id}&t=${Date.now()}`;
  
  // Update iframe/preview src
  document.getElementById('preview').src = newUrl;
}
```

### Step 3: Handle Caching in State Management

```javascript
// Redux example
const documentSlice = createSlice({
  name: 'documents',
  initialState: {
    documents: {},
    cacheBuster: {}
  },
  reducers: {
    versionUploaded: (state, action) => {
      const { documentId, timestamp } = action.payload;
      state.cacheBuster[documentId] = timestamp;
    }
  }
});

// In component
const cacheKey = useSelector(state => state.documents.cacheBuster[documentId]) || Date.now();
const previewUrl = `/api/documents/${documentId}/download?t=${cacheKey}`;
```

---

## Why Preview Shows Old File

### Browser Cache Mechanism

1. **First download:** Browser fetches file, saves to cache with URL as key
   - URL: `/api/documents/98/download`
   - File: version1.pdf (cached)

2. **Version upload:** Backend updated to version 2

3. **Preview refresh:** Browser checks cache
   - URL: `/api/documents/98/download` (same URL!)
   - Cache hit: Returns cached version1.pdf ❌

4. **Solution:** Change URL to force cache miss
   - URL: `/api/documents/98/download?t=1708178500`
   - Cache miss: Fetches new file ✅

### Cache Headers Explanation

```python
'Cache-Control': 'no-cache, no-store, must-revalidate'
# no-cache: Check with server before using cache
# no-store: Don't store in cache at all
# must-revalidate: Force revalidation

'Pragma': 'no-cache'
# HTTP/1.0 backward compatibility

'Expires': '0'
# Expire immediately
```

---

## Testing

### Test 1: Upload New Version

```bash
# Upload version
curl -X POST http://localhost:8070/api/documents/98/upload-version \
  -H "Authorization: Bearer TOKEN" \
  -d '{...file_data...}'

# Check response for timestamp field
# Expected: "timestamp": "2026-02-14T14:25:00"
```

### Test 2: Download with Cache Buster

```bash
# Without timestamp (may be cached)
curl http://localhost:8070/api/documents/98/download

# With timestamp (force fresh)
curl http://localhost:8070/api/documents/98/download?t=1708178500
```

### Test 3: Check Headers

```bash
curl -I http://localhost:8070/api/documents/98/download

# Should see:
# Cache-Control: no-cache, no-store, must-revalidate
# Pragma: no-cache
# Expires: 0
```

---

## Files Modified

1. **addons/nbs_archive/controllers/edit_request_controller.py**
   - Added cache invalidation after version upload
   - Added `timestamp` to response
   - Added `current_version_id` to response

2. **addons/nbs_archive/controllers/document_controller.py**
   - Added no-cache headers to download endpoint

---

## Deployment Status

- ✅ Cache invalidation added
- ✅ No-cache headers added
- ✅ Timestamp in response
- ✅ Odoo restarted (PID: 1504787)
- ✅ Ready for testing

---

## Action Required: Frontend Update

**Frontend must add timestamp to preview URLs:**

```javascript
// After successful upload
const timestamp = result.data.timestamp || Date.now();
const previewUrl = `/api/documents/${docId}/download?t=${timestamp}`;

// Update preview
setPreviewUrl(previewUrl);
// or
iframe.src = previewUrl;
// or
window.open(previewUrl);
```

---

## Alternative: Invalidate Frontend Cache

If using service workers or custom caching:

```javascript
// Clear cache for this document
if ('caches' in window) {
  caches.keys().then(names => {
    names.forEach(name => {
      caches.open(name).then(cache => {
        cache.delete(`/api/documents/${documentId}/download`);
      });
    });
  });
}
```

---

## Summary

### Backend Changes (DONE)
- ✅ Cache invalidation after write
- ✅ No-cache headers in download
- ✅ Timestamp in upload response

### Frontend Changes (NEEDED)
- [ ] Add timestamp parameter to preview URLs
- [ ] Force preview refresh after upload
- [ ] Use response timestamp for cache busting

**The backend is fixed. The frontend needs to add the timestamp parameter to force cache refresh!**

---

**Version:** 1.4.3  
**Date:** 2026-02-14  
**Status:** Backend fixed, frontend action needed
