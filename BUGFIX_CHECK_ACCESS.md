# Bug Fix: check_access() Method Conflict

## 🐛 Issue

**Error:**
```
NBSNote.check_access() takes 1 positional argument but 2 were given
```

**Endpoint:** `POST /api/folders/50`

---

## 🔍 Root Cause

The method name `check_access()` in the `NBSNote` model conflicted with Odoo's internal access control methods. When Odoo's framework tried to call access control methods, it was getting confused between our custom method and its internal methods.

---

## ✅ Solution

Renamed the method from `check_access()` to `can_user_access()` to avoid naming conflicts with Odoo's internal framework methods.

### Changes Made:

#### 1. Model Method Renamed
**File:** `addons/nbs_archive/models/nbs_note.py`

```python
# Before
def check_access(self):
    """Check if current user can access this note"""
    ...

# After
def can_user_access(self):
    """Check if current user can access this note"""
    ...
```

#### 2. Controller Calls Updated
**File:** `addons/nbs_archive/controllers/notes_controller.py`

```python
# Before
if note.check_access():
    ...

# After
if note.can_user_access():
    ...
```

All 2 occurrences in the notes controller were updated.

---

## 🧪 Testing

### Test 1: Get Folder Details
```bash
curl -X POST "http://localhost:8070/api/folders/50" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** ✅ Returns folder data with `note_count` field without errors

### Test 2: List Notes
```bash
curl -X POST "http://localhost:8070/api/notes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** ✅ Returns notes list, filtering by user access correctly

### Test 3: Get Single Note
```bash
curl -X POST "http://localhost:8070/api/notes/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"jsonrpc":"2.0","method":"call","params":{},"id":1}'
```

**Expected:** ✅ Returns note if user has access, otherwise "Access denied"

---

## 📝 Technical Details

### Why This Happened

Odoo's ORM has built-in access control methods that are part of the base model infrastructure. When we named our custom method `check_access()`, it likely conflicted with:

1. Odoo's internal `check_access_rights()` method
2. Odoo's access control rule evaluation
3. Odoo's security framework method resolution

### Best Practices

When creating custom methods in Odoo models:
- ✅ Use descriptive, specific names (e.g., `can_user_access`, `has_permission_to_view`)
- ❌ Avoid generic names that might conflict with framework methods (e.g., `check`, `access`, `validate`)
- ✅ Check Odoo's base model methods before naming your custom methods

---

## ✅ Status

- [x] Issue identified
- [x] Method renamed in model
- [x] All controller calls updated
- [x] Odoo restarted
- [x] Tests passed

---

## 🚀 Result

All folder and note APIs now work correctly without the `check_access()` error.

**Date:** February 11, 2026  
**Status:** ✅ Fixed and Verified
