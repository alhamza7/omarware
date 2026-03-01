# Bug Fix: Notes Access Rights

## 🐛 Issue

**Error:**
```
Failed to read field nbs.document.folder.note_ids
You are not allowed to access 'User Notes for Documents and Folders' (nbs.note) records.

No group currently allows this operation.
```

**Endpoint:** `POST /api/folders/50`

---

## 🔍 Root Cause

The new `nbs.note` model was created without any access rights (ir.model.access) entries in the security CSV file. Odoo's security system denied all access to the model by default.

---

## ✅ Solution

Added access rights for all three user groups (user, manager, admin) in the security file.

### Changes Made:

**File:** `addons/nbs_archive/security/ir.model.access.csv`

Added these lines:
```csv
access_nbs_note_user,nbs.note.user,model_nbs_note,group_nbs_user,1,1,1,1
access_nbs_note_manager,nbs.note.manager,model_nbs_note,group_nbs_manager,1,1,1,1
access_nbs_note_admin,nbs.note.admin,model_nbs_note,group_nbs_admin,1,1,1,1
```

### Permissions Granted:

| Group | Read | Write | Create | Unlink |
|-------|------|-------|--------|--------|
| **User** | ✅ | ✅ | ✅ | ✅ |
| **Manager** | ✅ | ✅ | ✅ | ✅ |
| **Admin** | ✅ | ✅ | ✅ | ✅ |

**Note:** Fine-grained access control (private notes, creator-only updates) is handled in the model's `can_user_access()` method and controller logic.

---

## 🔧 Update Process

1. Stop Odoo
2. Update `security/ir.model.access.csv`
3. Run module update: `odoo-bin -u nbs_archive --stop-after-init`
4. Restart Odoo

---

## 🧪 Testing

### Test 1: Get Folder Details
```bash
curl -X POST "http://localhost:8070/api/folders/50" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** ✅ Returns folder with `note_count` field without access errors

### Test 2: List Notes
```bash
curl -X POST "http://localhost:8070/api/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** ✅ Returns notes list successfully

### Test 3: Create Note
```bash
curl -X POST "http://localhost:8070/api/notes/create" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "content": "Test note",
    "folder_id": 50
  }'
```

**Expected:** ✅ Creates note successfully

---

## 📝 Technical Details

### Odoo Access Rights System

In Odoo, every model needs explicit access rights defined in `security/ir.model.access.csv`. Without these entries:
- No user can read/write/create/delete records
- Even computed fields that reference the model will fail
- The error message indicates "No group currently allows this operation"

### Our Security Configuration

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_nbs_note_user,nbs.note.user,model_nbs_note,group_nbs_user,1,1,1,1
```

Where:
- `perm_read=1`: Can read records
- `perm_write=1`: Can update records
- `perm_create=1`: Can create records
- `perm_unlink=1`: Can delete records

### Additional Access Control

Beyond these base permissions, the `nbs.note` model implements:
- **Private notes:** Only creator can access (checked in `can_user_access()`)
- **Public notes:** Visible to managers/admins in same department
- **Updates:** Only creator can update (checked in controller)
- **Deletion:** Creator or admin can delete (checked in controller)

---

## ✅ Status

- [x] Access rights added to CSV
- [x] Module updated
- [x] Odoo restarted
- [x] Tests passed

---

## 🚀 Result

All note-related APIs and folder/document APIs with `note_count` now work correctly.

**Date:** February 11, 2026  
**Status:** ✅ Fixed and Verified  
**Odoo:** Running on port 8070
