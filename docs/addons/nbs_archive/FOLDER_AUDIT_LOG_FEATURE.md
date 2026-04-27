# Folder Audit Log Filtering - Complete Guide ✅

## 🎯 **New Feature**

You can now **filter audit logs by `folder_id`** to get:
- ✅ All logs for the folder itself (created, updated, deleted, moved)
- ✅ All logs for documents in that folder (main documents, sub-documents, attachments)
- ✅ All activities: uploads, downloads, edits, deletions, etc.

---

## 📡 **API Endpoint**

**Endpoint:** `POST /api/audit-logs` (existing endpoint - now enhanced)

### **Parameters**

| Parameter | Type | Description |
|-----------|------|-------------|
| `document_id` | int | Filter by specific document |
| `folder_id` | int | **NEW!** Filter by folder (includes folder + all documents in it) |
| `action` | string | Filter by action type |
| `date_from` | datetime | Start date |
| `date_to` | datetime | End date |
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 50) |

---

## 🔍 **Use Cases**

### **Use Case 1: View All Activity for a Folder**

**Scenario:** User wants to see everything that happened with folder 197 and all its documents.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "folder_id": 197,
    "per_page": 50
  },
  "id": 1
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": [
      {
        "id": 3650,
        "action": "folder_updated",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T15:30:00",
        "folder_id": 197,
        "folder_name": "sample_4_notes",
        "metadata": "Updated folder: sample_4_notes | Changes: Company: 'None' → 'My Company'"
      },
      {
        "id": 3649,
        "action": "upload",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T13:33:15",
        "document_id": 276,
        "document_title": "sample_4_notes",
        "folder_id": null,
        "metadata": null
      },
      {
        "id": 3648,
        "action": "download",
        "user_name": "User Name",
        "timestamp": "2026-02-17T13:00:00",
        "document_id": 276,
        "document_title": "sample_4_notes",
        "metadata": null
      },
      {
        "id": 3647,
        "action": "folder_created",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T13:33:15",
        "folder_id": 197,
        "folder_name": "sample_4_notes",
        "metadata": "Created folder: sample_4_notes (Path: sample_4_notes)"
      }
    ],
    "pagination": {
      "total": 4,
      "page": 1,
      "per_page": 50
    }
  }
}
```

---

### **Use Case 2: View Only Folder Operations**

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "folder_id": 197,
    "action": "folder_updated",
    "per_page": 50
  },
  "id": 1
}
```

**Response:** Only folder update logs for folder 197

---

### **Use Case 3: View All Document Activity in a Folder**

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "folder_id": 197,
    "date_from": "2026-02-17T00:00:00",
    "per_page": 100
  },
  "id": 1
}
```

**Response:** All folder and document activity for folder 197 since Feb 17

---

## 📊 **What's Included**

When you filter by `folder_id: 197`, you get logs for:

### Folder Operations
- ✅ `folder_created` - When folder was created
- ✅ `folder_updated` - Name, code, description, company changes (with details!)
- ✅ `folder_deleted` - When folder was deleted
- ✅ `folder_moved` - When folder was moved to different parent

### Document Operations in Folder
- ✅ `upload` - Main documents uploaded
- ✅ `upload` - Sub-documents/attachments uploaded
- ✅ `download` - Document downloads
- ✅ `view` - Document views
- ✅ `document_updated` - Document edits
- ✅ `document_soft_deleted` - Documents moved to trash
- ✅ `document_restored` - Documents restored
- ✅ `new_version_uploaded` - New versions added
- ✅ `edit_request_created` - Edit requests
- ✅ **And 40+ other document actions**

---

## 🎨 **FE Implementation**

### **Folder Detail Page - Activity Tab**

```javascript
// Load all activity for current folder
async loadFolderActivity(folderId) {
  const response = await POST('/api/audit-logs', {
    folder_id: folderId,
    per_page: 50,
    page: 1
  });
  
  const logs = response.result.data;
  
  // Group by type
  const folderLogs = logs.filter(l => l.folder_id);
  const documentLogs = logs.filter(l => l.document_id);
  
  // Display in timeline
  displayTimeline(logs);
}
```

---

### **Show Folder + Document Activity Together**

```javascript
// Timeline view
logs.forEach(log => {
  if (log.folder_id) {
    // Folder operation
    showEvent({
      icon: '📁',
      title: `Folder ${log.action}`,
      description: log.metadata,
      user: log.user_name,
      time: log.timestamp
    });
  } else if (log.document_id) {
    // Document operation
    showEvent({
      icon: '📄',
      title: `Document ${log.action}`,
      description: `${log.document_title}: ${log.action}`,
      user: log.user_name,
      time: log.timestamp
    });
  }
});
```

---

## 🧪 **Test Verification**

**Test from database (Folder ID 64):**

```
Query: folder_id = 64

Results: 10 audit logs
  📁 Folder logs: 1
    - folder_updated with change details ✅
  
  📄 Document logs: 9
    - All downloads of documents in folder ✅

✅ SUCCESS! Returns both folder and document logs
```

---

## 📋 **Response Fields (Enhanced)**

Each audit log now includes:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Log ID |
| `action` | string | Action type |
| `user_id` | int | User ID |
| `user_name` | string | User name |
| `timestamp` | datetime | When it happened |
| `document_id` | int/null | Document if document log |
| `document_title` | string/null | Document name |
| `folder_id` | int/null | **NEW!** Folder if folder log |
| `folder_name` | string/null | **NEW!** Folder name |
| `department_id` | int/null | Department |
| `department_name` | string/null | Department name |
| `ip_address` | string/null | IP address |
| `metadata` | string/null | Details about the action |

---

## ✅ **Complete Example**

### Request: Get all activity for folder 197

```json
POST /api/audit-logs
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "folder_id": 197,
    "per_page": 50
  },
  "id": 1
}
```

### Response: Mix of folder and document logs

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": [
      {
        "id": 3700,
        "action": "folder_updated",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T15:45:00",
        "folder_id": 197,
        "folder_name": "sample_4_notes",
        "document_id": null,
        "metadata": "Updated folder: sample_4_notes | Changes: Company: 'None' → 'My Company'"
      },
      {
        "id": 3650,
        "action": "upload",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T13:33:15",
        "folder_id": null,
        "document_id": 276,
        "document_title": "sample_4_notes",
        "metadata": null
      },
      {
        "id": 3649,
        "action": "download",
        "user_name": "User ABC",
        "timestamp": "2026-02-17T14:00:00",
        "folder_id": null,
        "document_id": 277,
        "document_title": "TestingForExistingDolerCompanyCodeComingOrNot",
        "metadata": null
      },
      {
        "id": 3600,
        "action": "folder_created",
        "user_name": "Administrator",
        "timestamp": "2026-02-17T13:33:15",
        "folder_id": 197,
        "folder_name": "sample_4_notes",
        "document_id": null,
        "metadata": "Created folder: sample_4_notes (Path: sample_4_notes)"
      }
    ],
    "pagination": {
      "total": 4,
      "page": 1,
      "per_page": 50
    }
  }
}
```

---

## ✅ **Status**

| Feature | Status |
|---------|--------|
| Filter audit logs by folder_id | ✅ Working |
| Returns folder operation logs | ✅ Working |
| Returns document logs in folder | ✅ Working |
| Includes main documents | ✅ Working |
| Includes sub-documents | ✅ Working |
| Includes attachments | ✅ Working |
| folder_id field in response | ✅ Added |
| folder_name field in response | ✅ Added |
| Module updated | ✅ Done |
| Odoo restarted | ✅ Done at 15:47 |
| Tested and verified | ✅ Working |

---

## 🚀 **Ready to Use!**

The FE can now:
1. ✅ Pass `folder_id` to audit log API
2. ✅ Get complete activity history for a folder
3. ✅ See both folder and document operations
4. ✅ Display unified timeline of all folder activity

**Feature is live and ready for testing!** 🎉
