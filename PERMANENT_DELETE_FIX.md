# Permanent Delete - Frontend Fix Required

## المشكلة (Problem)

When calling `DELETE /api/documents/<id>/permanent`, the API returns:

```json
{
  "success": false,
  "error": "Invalid confirmation. Use \"DELETE_PERMANENT\""
}
```

## السبب (Root Cause)

From backend logs:
- **Route param confirmation:** `None`
- **Query string:** empty
- **Request body:** empty (`''`)

**The frontend is NOT sending the `confirmation` parameter at all.**

---

## الحل (Solution for Frontend)

The backend **requires** the `confirmation` parameter with value `"DELETE_PERMANENT"` for the delete to execute.

### Option 1: Query String (Recommended)

Send `confirmation` as a **query parameter**:

```javascript
DELETE http://localhost:3003/api/documents/14/permanent?confirmation=DELETE_PERMANENT
```

**Example (fetch):**
```javascript
fetch(`http://localhost:3003/api/documents/${documentId}/permanent?confirmation=DELETE_PERMANENT`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`,
  }
})
```

### Option 2: Request Body

Send `confirmation` in the **JSON body**:

```javascript
DELETE http://localhost:3003/api/documents/14/permanent
Content-Type: application/json

{"confirmation": "DELETE_PERMANENT"}
```

**Example (fetch):**
```javascript
fetch(`http://localhost:3003/api/documents/${documentId}/permanent`, {
  method: 'DELETE',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    confirmation: 'DELETE_PERMANENT'
  })
})
```

---

## تحسينات رسائل الخطأ (Enhanced Error Messages)

All API endpoints now return enhanced error information:

```json
{
  "success": false,
  "error": "Error message",
  "error_type": "ValidationError",
  "error_location": "File \"/path/to/file.py\", line 123, in method_name",
  "traceback": "... last 10 lines of stack trace ..."
}
```

For the permanent delete specifically, when confirmation is missing:

```json
{
  "success": false,
  "error": "Invalid confirmation. Use \"DELETE_PERMANENT\"",
  "error_detail": {
    "received_confirmation": null,
    "expected": "DELETE_PERMANENT",
    "method": "Send as query param: ?confirmation=DELETE_PERMANENT OR in JSON body: {\"confirmation\": \"DELETE_PERMANENT\"}",
    "received_from_query": null,
    "body_was_empty": true
  }
}
```

This tells the frontend developer exactly:
- What was received (`null`)
- What is expected (`"DELETE_PERMANENT"`)
- How to send it (query or body)
- Whether the body was empty

---

## Backend Changes Applied

1. ✅ **Audit log action values added:**
   - `document_soft_deleted`
   - `document_restored`
   - `document_permanently_deleted`

2. ✅ **Audit logging made non-blocking:**
   - Trash, Restore, Archive, Unarchive operations succeed even if audit log fails
   - All use `sudo()` to avoid permission issues

3. ✅ **Enhanced error responses:**
   - All endpoints now include `error_type`, `error_location`, and `traceback`
   - Permanent delete includes detailed `error_detail` explaining what was received

4. ✅ **Improved confirmation reading:**
   - Backend reads `confirmation` from: kwargs → query string → JSON body

---

## Frontend Action Required

**Update the permanent delete API call** to include `confirmation=DELETE_PERMANENT`:

**Before (current - broken):**
```javascript
DELETE http://localhost:3003/api/documents/14/permanent
// No confirmation sent!
```

**After (working):**
```javascript
DELETE http://localhost:3003/api/documents/14/permanent?confirmation=DELETE_PERMANENT
// ✓ Confirmation sent in query string
```

---

## Testing

1. Update frontend code to send `confirmation` parameter
2. Try permanent delete again
3. Check the new error response format - it will tell you exactly what was received
4. If still not working, share the full JSON response including `error_detail`
