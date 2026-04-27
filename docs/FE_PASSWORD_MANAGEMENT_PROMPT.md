# FE Prompt — Password Management (Change Password + Forgot/Reset Password)

## Overview

Three features to implement:

1. **Change Password** — inside the employee profile update form (admin or self)
2. **Forgot Password** — link on the login page that sends a reset e-mail
3. **Reset Password** — a dedicated page that accepts the new password from the reset link

---

## 1. Change Password (inside Employee Profile / Update Form)

### When to show it

- **Admin view** (`role === 'general_manager'` or session user is system admin): show the
  "Change Password" section on ANY employee's profile edit page.
- **Own profile**: show the "Change Password" section when the logged-in user is editing
  their own profile (`employee_id === currentUser.id`).
- Hide it entirely if neither condition is met.

### Fields

| Field | Admin | Self |
|-------|-------|------|
| `new_password` | required | required |
| `confirm_password` | required (FE only, not sent) | required (FE only, not sent) |
| `current_password` | NOT shown / NOT sent | required |

### API call

**Endpoint:** `POST /api/crm/employees/{id}/update`  
**Auth:** `Authorization: Bearer <access_token>`

Extend the existing update payload with:

```json
{
  "password": "newPlainTextPassword",
  "current_password": "oldPassword"   // omit entirely if admin is changing another user's password
}
```

**Success response:**
```json
{ "success": true, "data": { ...employee fields... } }
```

**Error responses:**
```json
{ "success": false, "error": "Current password is incorrect" }
{ "success": false, "error": "Password must be at least 6 characters" }
{ "success": false, "error": "You do not have permission to change another user's password" }
```

### UX

- Only submit the password fields if the user actually typed in the `new_password` field.
  If left blank, omit `password` and `current_password` from the payload.
- Show a success toast: **"Password updated successfully"**
- Clear the password fields after success.
- Validate FE-side that `new_password === confirm_password` before submitting.
- Minimum length: 6 characters.

---

## 2. Forgot Password (Login Page)

### Where

Add a **"Forgot password?"** link below the login form's password field.

### Flow

1. User clicks "Forgot password?" → show a small inline form (or modal) asking for their
   **email address or username**.
2. On submit, call `POST /lugal/auth/forgot-password`.
3. Show the message returned by the API regardless of whether the account existed
   (the backend always returns the same message to avoid leaking information).

### API call

**Endpoint:** `POST /lugal/auth/forgot-password`  
**Auth:** none required

```json
{
  "email_or_username": "user@nooralnibras.com",
  "fe_url": "http://192.168.116.204:5173"
}
```

| Field | Required | Description |
|---|---|---|
| `email_or_username` | yes | Registered email address **or** system login username |
| `fe_url` | first call only | Base URL of the frontend app. Persisted automatically — omit on subsequent calls unless the URL changes |

> **Always send `fe_url` for now** because the backend may not have the frontend URL stored yet on fresh environments.
> Use `window.location.origin` so it never needs to be hardcoded.

```ts
const FE_BASE_URL = import.meta.env.VITE_APP_URL ?? window.location.origin;

await api.forgotPassword({
  email_or_username: value,   // accepts email address or username — backend detects automatically
  fe_url: FE_BASE_URL,
});
```

**Response (always success=true):**
```json
{
  "success": true,
  "data": {
    "message": "If that account exists, a password-reset link has been sent to the registered e-mail."
  }
}
```

**Error (only if field is missing):**
```json
{ "success": false, "error": "email_or_username is required" }
```

### UX

- After submitting, display the `data.message` to the user regardless of success/error.
- Show a loading spinner on the button while the request is in flight.
- Add a "Back to login" link.

---

## 3. Reset Password Page (from the e-mail link)

### Route

The reset e-mail contains a link like:
```
https://yourapp.com/reset-password?token=<token>
```

Add a **React route** `/reset-password` that:
1. Reads `token` from the URL query string (`useSearchParams`).
2. If there is no token, shows an error: "Invalid reset link. Please request a new one."
3. Otherwise shows a form with two fields: **New Password** and **Confirm Password**.

### API call

**Endpoint:** `POST /lugal/auth/reset-password`  
**Auth:** none required

```json
{
  "token": "the_token_from_url",
  "new_password": "NewPassword123",
  "confirm_password": "NewPassword123"
}
```

**Success response:**
```json
{
  "success": true,
  "data": {
    "message": "Password updated successfully. You can now log in with your new password."
  }
}
```

**Error responses:**
```json
{ "success": false, "error": "Passwords do not match" }
{ "success": false, "error": "Password must be at least 6 characters" }
{ "success": false, "error": "Reset link has expired. Please request a new one." }
{ "success": false, "error": "Invalid or expired reset link" }
```

### UX

- FE-side validation: `new_password === confirm_password` before calling the API.
- On **success**: show the `data.message` and a **"Go to Login"** button. Do NOT auto-redirect
  immediately — let the user read the message first, then redirect to `/login` on button click
  (or auto-redirect after 3 seconds).
- On **error**: display the error message from the response in red below the form. Allow the
  user to try again (do not clear the token from the URL).
- Show a loading spinner while the request is in flight.
- Minimum length hint: "At least 6 characters".

---

## Summary of all API endpoints involved

| Method | URL | Auth | Purpose |
|--------|-----|------|---------|
| `POST` | `/api/crm/employees/{id}/update` | Bearer | Change password (add `password` + optional `current_password` to existing payload) |
| `POST` | `/lugal/auth/forgot-password` | None | Request reset e-mail |
| `POST` | `/lugal/auth/reset-password` | None | Set new password using token from e-mail |

---

## Notes for the FE developer

- All endpoints use **JSON-RPC format**: wrap params in `{ "jsonrpc": "2.0", "method": "call", "params": { ...fields... } }`.
- The `/reset-password` page must be **publicly accessible** (no auth guard) since the user
  is not logged in when they open it.
- The token in the URL is single-use — it is invalidated immediately after a successful reset.
  If the user submits the form twice, the second attempt will get "Invalid or expired reset link".
- After a successful reset, all existing login sessions for that user are invalidated on the
  backend. The user will need to log in fresh with their new password.
