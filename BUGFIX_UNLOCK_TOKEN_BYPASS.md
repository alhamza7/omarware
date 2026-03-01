# Development Feature: Unlock Token Bypass for Version Upload

## Date: 2026-02-14

## Change Summary

**DISABLED unlock token validation** for document version uploads to enable easier development and testing.

⚠️ **WARNING:** This bypasses security controls. **Re-enable for production!**

---

## What Was Changed

### Endpoint: POST /api/documents/<document_id>/upload-version

**Before (Production Mode):**
- Required valid `unlock_token` from approved edit request
- Validated token belongs to requester
- Locked document after upload
- Marked edit request as completed

**After (Development Mode):**
- ✅ `unlock_token` is now **optional** (can be empty string)
- ✅ No validation performed
- ✅ Anyone can upload new versions
- ✅ Documents remain **unlocked** after upload
- ✅ No edit request required

---

## API Usage

### Request (JSON-RPC format)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "file_data": "base64_encoded_file_content",
    "file_name": "document.pdf",
    "unlock_token": "",  // ← Can be empty now!
    "change_description": "Updated document"
  },
  "id": 1
}
```

**All params are now optional except `file_data` and `file_name`:**
- `file_data` - Base64 encoded file (required)
- `file_name` - File name (required)
- `unlock_token` - **Optional** (ignored in dev mode)
- `change_description` - **Optional** (defaults to "New version uploaded")

### Response (Success)

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": {
      "version_id": 123,
      "version_number": 2,
      "file_name": "document.pdf",
      "message": "Version 2 uploaded successfully (unlock validation disabled for development)"
    }
  }
}
```

### Response (Error)

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": false,
    "error": "Document not found"
  }
}
```

---

## cURL Example

```bash
curl -X POST http://localhost:8070/api/documents/98/upload-version \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "file_data": "JVBERi0xLjQKJcOkw7zDtsOfCjIgMC...",
      "file_name": "updated-document.pdf",
      "unlock_token": "",
      "change_description": "Development upload"
    },
    "id": 1
  }'
```

---

## What Happens Now

### Version Upload Flow (Development)

1. ✅ User authenticated via JWT
2. ✅ Document exists check
3. ⚠️ **SKIP:** Unlock token validation (commented out)
4. ✅ Calculate new version number
5. ✅ Create new version record
6. ✅ Update document's current version
7. ✅ Keep document **unlocked** (`is_locked = False`)
8. ✅ Log audit trail
9. ⚠️ **SKIP:** Mark edit request as completed (no edit request)
10. ⚠️ **SKIP:** Send notifications (no approver)
11. ✅ Return success response

---

## Code Changes

**File:** `addons/nbs_archive/controllers/edit_request_controller.py`

### Changes Made:

1. **Function signature updated:**
   ```python
   # Before
   def upload_new_version(self, document_id, file_data, file_name, unlock_token, change_description, **kwargs):
   
   # After  
   def upload_new_version(self, document_id, file_data, file_name, unlock_token=None, change_description=None, **kwargs):
   ```
   Made `unlock_token` and `change_description` optional.

2. **Token validation commented out:**
   ```python
   # # Find approved edit request with valid unlock token
   # edit_request = request.env['nbs.edit.request'].search([
   #     ('document_id', '=', document_id),
   #     ('state', '=', 'approved'),
   #     ('unlock_token', '=', unlock_token),
   #     ('token_used', '=', False),
   # ], limit=1)
   # 
   # if not edit_request:
   #     return {
   #         'success': False,
   #         'error': 'Invalid or expired unlock token'
   #     }
   ```

3. **Bypass added:**
   ```python
   # BYPASS: Allow upload without validation
   edit_request = None  # No edit request needed
   ```

4. **Document kept unlocked:**
   ```python
   document.write({
       'current_version_id': version.id,
       'is_locked': False,  # Keep unlocked for development
   })
   ```

5. **Edit request completion disabled:**
   ```python
   # # Mark token as used and complete the edit request (DISABLED)
   # if edit_request:
   #     edit_request.write({
   #         'token_used': True,
   #         'state': 'completed',
   #     })
   ```

6. **Notifications disabled:**
   ```python
   # # Notify relevant users (DISABLED - no edit request)
   # if edit_request and edit_request.approver_id:
   #     request.env['nbs.notification'].create({...})
   ```

---

## Re-enabling for Production

⚠️ **IMPORTANT:** Before deploying to production, you **MUST** re-enable security:

### Step 1: Uncomment Token Validation

In `edit_request_controller.py`, find and uncomment:

```python
# Find approved edit request with valid unlock token
edit_request = request.env['nbs.edit.request'].search([
    ('document_id', '=', document_id),
    ('state', '=', 'approved'),
    ('unlock_token', '=', unlock_token),
    ('token_used', '=', False),
], limit=1)

if not edit_request:
    return {
        'success': False,
        'error': 'Invalid or expired unlock token'
    }

# Check if token belongs to the requester
if edit_request.requester_id.id != request.env.user.id:
    return {
        'success': False,
        'error': 'This unlock token does not belong to you'
    }
```

### Step 2: Remove Bypass

Delete or comment:
```python
# BYPASS: Allow upload without validation
edit_request = None  # No edit request needed
```

### Step 3: Re-lock Documents

Change:
```python
document.write({
    'current_version_id': version.id,
    'is_locked': True,  # Lock after upload
    'unlock_token': False,
    'unlock_expiry': False,
})
```

### Step 4: Re-enable Edit Request Completion

Uncomment:
```python
# Mark token as used and complete the edit request
edit_request.write({
    'token_used': True,
    'state': 'completed',
})
```

### Step 5: Re-enable Notifications

Uncomment:
```python
# Notify relevant users
request.env['nbs.notification'].create({
    'user_id': edit_request.approver_id.id,
    'title': 'New Version Uploaded',
    'message': f'{request.env.user.name} uploaded version {new_version_number} of "{document.name}"',
    'notification_type': 'new_version',
    'related_document_id': document_id,
})
```

### Step 6: Update Function Signature

Change back:
```python
def upload_new_version(self, document_id, file_data, file_name, unlock_token, change_description, **kwargs):
```
(Make `unlock_token` and `change_description` required again)

---

## Production Workflow (When Re-enabled)

For production, the proper workflow is:

1. **User creates edit request**
   - POST /api/documents/<id>/edit-request
   - Specifies reason for edit

2. **Manager approves request**
   - POST /api/edit-requests/<id>/approve
   - Generates unlock token

3. **User receives unlock token**
   - Token sent via notification/email
   - Token valid for 24 hours

4. **User uploads new version**
   - POST /api/documents/<id>/upload-version
   - Provides valid unlock token
   - Token is validated and consumed

5. **Document is locked again**
   - Edit request marked as completed
   - Token invalidated
   - Notifications sent

---

## Security Implications

### Current (Development Mode)

⚠️ **Risks:**
- Anyone can upload new versions without approval
- No audit trail of who approved changes
- Documents remain unlocked (can be overwritten repeatedly)
- No notification to document owners
- Bypasses document control policies

✅ **Benefits:**
- Fast development/testing
- No need to create edit requests
- No need for manager approval
- Immediate file replacement

### Production Mode (When Re-enabled)

✅ **Security:**
- Requires manager approval for edits
- Token-based authorization
- Audit trail maintained
- Documents locked after upload
- Notifications keep stakeholders informed
- Enforces document control policies

---

## Testing

### Test 1: Upload Without Token

```bash
curl -X POST http://localhost:8070/api/documents/98/upload-version \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {
      "file_data": "JVBERi0xLjQK...",
      "file_name": "test.pdf",
      "unlock_token": ""
    }
  }'
```

**Expected:** Success (bypass enabled)

### Test 2: Upload Multiple Versions

Upload version 2, then version 3, then version 4 without any approval.

**Expected:** All succeed, version numbers increment correctly.

### Test 3: Check Document Remains Unlocked

After upload, check document:
```bash
curl -X POST http://localhost:8070/api/documents/98 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected:** `"is_locked": false`

---

## Audit Logging

Version uploads are still logged:

```json
{
  "action": "new_version_uploaded",
  "document_id": 98,
  "user_id": 2,
  "metadata": "Version 2 (direct upload - no edit request)"
}
```

Note the metadata clearly indicates this was a direct upload without edit request.

---

## Frontend Integration

### JavaScript Example

```javascript
async function uploadDocumentVersion(documentId, fileData, fileName, description) {
  try {
    const response = await fetch(`/api/documents/${documentId}/upload-version`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'call',
        params: {
          file_data: fileData,  // Base64 encoded
          file_name: fileName,
          unlock_token: '',  // Empty - bypass enabled
          change_description: description || 'Version updated'
        },
        id: 1
      })
    });
    
    const result = await response.json();
    
    if (result.result.success) {
      console.log('Version uploaded:', result.result.data);
      toast.success(`Version ${result.result.data.version_number} uploaded`);
      return result.result.data;
    } else {
      console.error('Upload failed:', result.result.error);
      toast.error(result.result.error);
      return null;
    }
  } catch (error) {
    console.error('Request failed:', error);
    toast.error('Upload failed');
    return null;
  }
}

// Usage
const fileInput = document.getElementById('fileInput');
const file = fileInput.files[0];

// Convert file to base64
const reader = new FileReader();
reader.onload = async (e) => {
  const base64 = e.target.result.split(',')[1];  // Remove data:xxx prefix
  await uploadDocumentVersion(98, base64, file.name, 'Updated document');
};
reader.readAsDataURL(file);
```

---

## Deployment Status

- ✅ Unlock token validation disabled
- ✅ Documents remain unlocked
- ✅ No edit request required
- ✅ Odoo restarted (PID: 1499621)
- ✅ Ready for development/testing

**Version:** Development Mode  
**Date:** 2026-02-14  
**Status:** Active (⚠️ DO NOT USE IN PRODUCTION)

---

## Reminder

🔒 **Before Production Deployment:**

1. [ ] Re-enable unlock token validation
2. [ ] Re-enable edit request workflow
3. [ ] Re-enable document locking
4. [ ] Re-enable notifications
5. [ ] Test with proper edit request workflow
6. [ ] Update API documentation
7. [ ] Inform stakeholders of change

---

## Summary

**Development Mode (Current):**
- ✅ No unlock token needed
- ✅ Direct version uploads
- ✅ Fast iteration

**Production Mode (To Be Re-enabled):**
- 🔒 Unlock token required
- 🔒 Edit request workflow enforced
- 🔒 Manager approval needed
- 🔒 Full audit trail
