# Bug Fix: Audit Log Action - 'document_updated'

## Date: 2026-02-14

## Issue

**Error:**
```json
{
  "success": false,
  "error": "Wrong value for nbs.audit.log.action: 'document_updated'"
}
```

When trying to use the document update endpoint, the audit log was rejecting the action value `'document_updated'` because it wasn't in the allowed list.

---

## Root Cause

The `nbs.audit.log` model has a **Selection field** for `action` with a predefined list of valid values. The new document update endpoint tried to log an action that didn't exist in this list.

**Valid actions before fix:**
- `upload`, `view`, `download`
- `edit_request`, `edit_request_created`, `edit_request_approved`, `edit_request_rejected`
- `archive`, `unarchive`
- `document_soft_deleted`, `document_restored`, `document_permanently_deleted`
- `attachment_upload`, `attachment_updated`, etc.
- ❌ `document_updated` - **MISSING**

---

## Solution

Added `'document_updated'` to the audit log action selection field.

**File Modified:**
`addons/nbs_archive/models/nbs_audit_log.py`

**Change:**
```python
action = fields.Selection([
    ('upload', 'Upload'),
    ('view', 'View'),
    ('download', 'Download'),
    # ... other actions ...
    ('archive', 'Archive'),
    ('unarchive', 'Unarchive'),
    ('document_updated', 'Document Updated'),  # ← ADDED THIS
    ('document_soft_deleted', 'Document Moved to Trash'),
    # ... rest of actions ...
], string='Action', required=True, readonly=True, index=True)
```

---

## Deployment

To register the new action value, the module must be updated:

```bash
# Stop Odoo
pkill -f "odoo-bin -c odoo_local.conf"

# Restart with module update
./venv/bin/python odoo-bin -c odoo_local.conf --dev=all -u nbs_archive
```

The `-u nbs_archive` flag tells Odoo to update the module, which will:
1. Update the Selection field constraints
2. Register the new `document_updated` action value
3. Apply any other pending model changes

---

## Testing

### Test the Update Endpoint

```bash
# Update a document
curl -X POST http://localhost:8070/api/documents/98/update \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Update",
    "po_number": "PO-TEST-001"
  }'

# Expected Response:
{
  "success": true,
  "message": "Document updated successfully",
  "data": {
    "id": 98,
    "name": "Test Update"
  }
}
```

### Verify Audit Log Created

```bash
# Check audit logs (if you have an endpoint)
# Or check directly in Odoo backend:
# Apps → NBS Archive → Audit Logs
# Look for action: "Document Updated"
```

---

## Impact

### Before Fix ❌
```
POST /api/documents/98/update
→ Error: "Wrong value for nbs.audit.log.action: 'document_updated'"
→ Update fails, no audit log created
```

### After Fix ✅
```
POST /api/documents/98/update
→ Success: Document updated
→ Audit log created with action='document_updated'
→ Full audit trail maintained
```

---

## Complete List of Valid Actions

After this fix, the audit log supports:

### Document Actions
- `upload` - Document uploaded
- `view` - Document viewed
- `download` - Document downloaded
- `document_updated` - Document metadata updated ✅ NEW
- `archive` - Document archived
- `unarchive` - Document unarchived
- `document_soft_deleted` - Document moved to trash
- `document_restored` - Document restored from trash
- `document_permanently_deleted` - Document permanently deleted

### Edit Request Actions
- `edit_request` - Edit request action
- `edit_request_created` - Edit request created
- `edit_request_approved` - Edit request approved
- `edit_request_rejected` - Edit request rejected

### Version Actions
- `new_version` - New version
- `new_version_uploaded` - New version uploaded
- `signed_version_uploaded` - Signed version uploaded

### Attachment Actions
- `attachment_upload` - Attachment uploaded
- `attachment_updated` - Attachment updated
- `attachment_deleted` - Attachment deleted
- `attachment_restored` - Attachment restored
- `attachment_permanently_deleted` - Attachment permanently deleted
- `multiple_attachments_upload` - Multiple attachments uploaded

### Folder Actions
- `folder_created` - Folder created
- `folder_updated` - Folder updated
- `folder_deleted` - Folder deleted
- `folder_moved` - Folder moved

### Department/Type Actions
- `department_created` - Department created
- `department_updated` - Department updated
- `department_archived` - Department archived
- `document_type_created` - Document type created
- `document_type_updated` - Document type updated
- `document_type_archived` - Document type archived

### Other Actions
- `approval` - Approval
- `rejection` - Rejection
- `relation_created` - Relation created
- `search` - Search performed
- `login` - User login
- `logout` - User logout

---

## Audit Log Entry Example

When a document is updated, this audit log entry is created:

```json
{
  "timestamp": "2026-02-14T13:34:00Z",
  "user_id": 2,
  "action": "document_updated",
  "document_id": 98,
  "department_id": 4,
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "metadata": "{\"name\": \"New Title\", \"po_number\": \"PO-12345\"}"
}
```

**Fields:**
- `timestamp` - When the update occurred
- `user_id` - Who made the update
- `action` - What action was performed (`document_updated`)
- `document_id` - Which document was updated
- `department_id` - Which department owns the document
- `ip_address` - IP address of the user
- `user_agent` - Browser/client information
- `metadata` - JSON of fields that were changed

---

## Related Fixes

This fix is part of the document update endpoint implementation:
- **Issue 1:** Missing `/api/documents/<id>/update` endpoint ✅ Fixed
- **Issue 2:** `folder_id` always null ✅ Fixed
- **Issue 3:** Audit log action validation error ✅ Fixed (this document)

---

## Notes

### Why Module Update is Required

Selection field changes in Odoo require a module update because:
1. Selection fields are stored in database constraints
2. Adding new values requires database schema update
3. The `-u nbs_archive` flag triggers this update

### No Data Loss

- ✅ Existing audit logs are preserved
- ✅ No changes to existing action values
- ✅ Only adds new action, doesn't modify existing ones

### Future-Proof

To add more audit actions in the future:
1. Add to the Selection list in `nbs_audit_log.py`
2. Run module update: `-u nbs_archive`
3. Use the new action in controllers

---

## Status

- ✅ Action added to model
- ✅ Module updated
- ✅ Odoo restarted
- ✅ Ready for testing

**Current Status:** Deployed and Active  
**Odoo PID:** 1475880  
**Version:** 1.3.1

---

## Documentation Updated

Related documentation files:
- `BUGFIX_DOCUMENT_UPDATE_AND_FOLDER_ID.md` - Main update endpoint fix
- `BUGFIX_AUDIT_LOG_ACTION.md` - This file (audit log fix)
