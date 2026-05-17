# Lugal CRM — Complete Frontend API Reference
**Last updated:** 2026-05-17  
**Base URL:** `http://<server>:8069` (proxied through the WS proxy on port 8069)

---

## Table of Contents

1. [Request Format](#1-request-format)
2. [Authentication](#2-authentication)
3. [Real-time & WebSocket Channels](#3-real-time--websocket-channels)
4. [File Upload](#4-file-upload)
5. [Users & Profile](#5-users--profile)
6. [Admin — User Management](#6-admin--user-management)
7. [Admin — Permissions & Roles](#7-admin--permissions--roles)
8. [Customers (CRM)](#8-customers-crm)
9. [Tickets](#9-tickets)
10. [Tasks](#10-tasks)
11. [Conversations (Chat)](#11-conversations-chat)
12. [Email (Inbox / Outbox)](#12-email-inbox--outbox)
13. [Employees & Workforce](#13-employees--workforce)
14. [Analytics](#14-analytics)
15. [Supply Chain](#15-supply-chain)
16. [LocalSend File Transfers](#16-localsend-file-transfers)
17. [Notifications](#17-notifications)
18. [POS Perfume — Orders API](#18-pos-perfume--orders-api)
19. [Inventory API](#19-inventory-api)
20. [Config & Misc](#20-config--misc)
21. [Error Responses](#21-error-responses)

---

## 1. Request Format

### JSON-RPC Envelope

Every endpoint marked **`jsonrpc`** uses this POST body:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "key": "value"
  }
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { "success": true, "data": { ... } }
}
```

**Content-Type:** `application/json`

### HTTP endpoints

A few endpoints (`/api/crm/upload/*`, `/api/crm/analytics/export_kpi`, file downloads) use `multipart/form-data` or plain HTTP — noted explicitly in each section.

---

## 2. Authentication

All API endpoints use JWT Bearer tokens. Pass the token in every request:

```
Authorization: Bearer <access_token>
```

### `POST /lugal/auth/login`

```json
{
  "params": {
    "username": "user@example.com",
    "password": "secret",
    "remember_me": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "user": { "id": 52, "name": "Ahmed", "email": "...", "role": "agent" }
}
```

### `POST /lugal/auth/refresh`

```json
{ "params": { "refresh_token": "eyJ..." } }
```

### `POST /lugal/auth/logout`

No body — reads `Authorization` header.

### `POST /lugal/auth/forgot-password`

```json
{ "params": { "email_or_username": "user@example.com", "fe_url": "https://app.example.com" } }
```

### `POST /lugal/auth/reset-password`

```json
{ "params": { "token": "...", "new_password": "abc123", "confirm_password": "abc123" } }
```

---

## 3. Real-time & WebSocket Channels

The server uses Odoo's `bus.bus` for real-time pushes.

**Polling endpoint:** `POST /web/bus/poll`

```json
{ "params": { "channels": ["supply_user.52", "localsend_user.52"], "last": 0 } }
```

> For WebSocket-based apps, connect to `ws://<server>:8076/websocket`.

### Channel Reference

| Channel | Events pushed |
|---------|---------------|
| `supply_user.<uid>` | Chat messages, story views, conversation updates |
| `localsend_user.<uid>` | File transfer events (available, sent, downloaded) |
| `supply_chat.<conv_id>` | Typing indicators |
| `crm_marquee` | Scrolling notice updates |

### LocalSend Bus Events

```js
// Subscribe
busService.subscribe('localsend_user.' + myUserId, (eventType, payload) => {
  // payload always includes: transfer_id, file_name, file_size, mime_type,
  //   download_url, preview_url, source_user_name, target_user_name, status
});
```

| `eventType` | When | Key action |
|-------------|------|-----------|
| `localsend.transfer.available` | File ready to download (LocalSend not running) | Show **Download** button using `payload.download_url` |
| `localsend.transfer.sent` | File delivered via LocalSend P2P | Show success toast |
| `localsend.transfer.downloaded` | Receiver confirmed download | Show receipt to sender |
| `localsend.transfer.cancelled` | Transfer cancelled | Dismiss notification |

---

## 4. File Upload

### `POST /api/crm/upload/image` *(multipart)*

Upload an image. Returns `attachment_id`.

```
Content-Type: multipart/form-data
Fields: file (or files[] for multiple), customer_id (optional)
```

Response:

```json
{ "success": true, "data": { "attachment_id": 379001, "url": "/web/content/379001" } }
```

### `POST /api/crm/upload/document` *(multipart)*

```
Fields: file, type ("pdf"|"docx"|...), name (optional), customer_id (optional)
```

### `POST /api/lugal/email/attachments/upload` *(multipart)*

Upload email attachment.

```
Fields: file (or files[]), account_id (optional), inline (bool, default false)
```

### `POST /api/crm/supply/chat/upload` *(multipart)*

Upload file for chat message.

```
Fields: file, conversation_id, kind ("image"|"video"|"audio"|"document"), duration_seconds (for audio/video)
```

---

## 5. Users & Profile

### `POST /api/crm/users/me`

Get current authenticated user with full permissions and routes map.

**Response fields:** `id`, `name`, `email`, `login`, `role`, `job_title`, `permissions`, `routes`, `route_visibility`, `avatar_url`, `branch`

### `POST /api/crm/users/me/preferences`

Get current user preferences (`lang`, `tz`, `signature`).

### `POST /api/crm/users/me/preferences/update`

```json
{ "params": { "lang": "ar_001", "tz": "Asia/Baghdad", "notify_email": true, "signature": "<p>Best regards</p>" } }
```

### `POST /api/crm/users/me/update`

```json
{ "params": { "name": "Ahmed", "phone": "+964...", "mobile": "...", "email": "...", "job_title": "Agent" } }
```

### `POST /api/crm/users/me/change_password`

```json
{ "params": { "current_password": "old", "new_password": "new", "confirm_password": "new" } }
```

### `POST /api/crm/users/list`

List all CRM users (all roles).

```json
{
  "params": {
    "search": "ahmed",
    "role": "agent",
    "branch_id": 3,
    "active": true,
    "page": 1,
    "per_page": 50
  }
}
```

### `POST /api/crm/users/<user_id>`

Get a single user profile.

### `POST /api/crm/users/<user_id>/permissions`

Get a user's full permission map + routes (alias of admin permissions/get, admin-only).

---

## 6. Admin — User Management

> All endpoints in this section require admin role.

### `POST /api/crm/admin/users/list`

```json
{
  "params": {
    "search": "john",
    "role": "supervisor",
    "job_title": "Agent",
    "active": true,
    "page": 1,
    "per_page": 50,
    "with_perms": false
  }
}
```

### `POST /api/crm/admin/users/<id>/get`

Full user detail with permissions.

### `POST /api/crm/admin/users/create`

```json
{
  "params": {
    "name": "John Doe",
    "login": "john@company.com",
    "password": "secret",
    "role": "agent",
    "job_title": "Customer Service Agent",
    "branch_id": 2
  }
}
```

### `POST /api/crm/admin/users/<id>/update`

```json
{ "params": { "name": "...", "phone": "...", "job_title": "..." } }
```

### `POST /api/crm/admin/users/<id>/change_password`

```json
{ "params": { "new_password": "...", "confirm_password": "..." } }
```

### `POST /api/crm/admin/users/<id>/deactivate`
### `POST /api/crm/admin/users/<id>/activate`
### `POST /api/crm/admin/users/<id>/delete`

### `POST /api/crm/admin/users/assign_role`

```json
{ "params": { "user_id": 52, "role": "supervisor" } }
```

### `POST /api/crm/admin/users/bulk_assign`

```json
{ "params": { "user_ids": [52, 53, 54], "role": "agent" } }
```

### `POST /api/crm/admin/users/<id>/remove_role`

### `POST /api/crm/admin/stats`

Dashboard stats: total users, by role, active/inactive counts.

---

## 7. Admin — Permissions & Roles

### `POST /api/crm/admin/permissions/schema`

Returns the full permission tree definition (all possible keys and their types). Use to build permission editor UI.

### `POST /api/crm/me/permissions`

Current user's own permissions (non-admin, returns own merged permissions).

### `POST /api/crm/admin/users/<id>/permissions/get`

Full permission breakdown for a specific user.

**Response:**

```json
{
  "success": true,
  "data": {
    "user_id": 52,
    "role": "agent",
    "role_baseline": { ... },
    "job_title_template": { "found": true, "permissions": { ... } },
    "individual_overrides": {
      "found": true,
      "overrides": { ... },
      "route_visibility": { "conversations": true, "dashboard": false },
      "last_modified_by": "Admin",
      "last_modified_at": "2026-05-17T09:00:00"
    },
    "effective_permissions": { ... },
    "routes": {
      "conversations": true,
      "dashboard": false,
      "customers": false,
      ...
    },
    "route_visibility": { "conversations": true, "dashboard": false }
  }
}
```

> **`routes`** is the flat map the FE should use for showing/hiding navigation items.

### `POST /api/crm/admin/users/<id>/permissions/set`

```json
{
  "params": {
    "permissions": {
      "conversations": { "chat": { "view": true, "send": true } }
    },
    "route_visibility": {
      "conversations": true,
      "dashboard": false,
      "customers": false,
      "tickets": false,
      "tasks": false,
      "employees": false,
      "supply_chain": false,
      "analytics": false,
      "settings": false
    },
    "notes": "Only allow conversations",
    "apply_to_all_same_crm_role": false
  }
}
```

> **Important:** `route_visibility` is the definitive nav visibility map. To restrict a user to only see Conversations, explicitly set all other routes to `false`.

### `POST /api/crm/admin/users/<id>/permissions/reset`

Reset user to role defaults (removes individual overrides).

### `POST /api/crm/admin/permissions/job_titles/list`
### `POST /api/crm/admin/permissions/job_titles/upsert`
### `POST /api/crm/admin/permissions/job_titles/delete`
### `POST /api/crm/admin/permissions/job_titles/get`

Job title template management (applies permissions to all users with that job title).

### `POST /api/crm/admin/users/bulk_permissions`

Set permissions for multiple users at once.

```json
{ "params": { "user_ids": [52, 53], "permissions": { ... }, "route_visibility": { ... } } }
```

### `POST /api/crm/admin/users/compare_permissions`

```json
{ "params": { "user_id_a": 52, "user_id_b": 53 } }
```

### `POST /api/crm/admin/audit/permissions`

Audit log of permission changes (who changed what and when).

### `POST /api/crm/admin/export/permissions`

Export all user permissions as JSON.

### `POST /api/crm/admin/import/permissions`

Import permissions from previously exported JSON.

---

## 8. Customers (CRM)

### `POST /api/crm/customers/list`

```json
{
  "params": {
    "search": "Ahmed",
    "stage_id": 2,
    "branch_id": 1,
    "assigned_to": 52,
    "page": 1,
    "per_page": 20
  }
}
```

### `POST /api/crm/customers/search`

Quick search by name/phone/email.

```json
{ "params": { "query": "ahmed", "limit": 10 } }
```

### `POST /api/crm/customers/<id>`

Get full customer detail.

### `POST /api/crm/customers/create`

```json
{
  "params": {
    "name": "Customer Name",
    "phone": "+964...",
    "email": "c@example.com",
    "stage_id": 1,
    "branch_id": 2,
    "notes": "..."
  }
}
```

### `POST /api/crm/customers/<id>/update`

Same fields as create (partial update).

### `POST /api/crm/customers/<id>/delete`

### `POST /api/crm/customers/<id>/kanban_move`

```json
{ "params": { "stage_id": 3 } }
```

### `POST /api/crm/customers/<id>/activity`

Customer activity log (calls, tickets, notes, emails).

```json
{ "params": { "page": 1, "per_page": 20, "type": "all" } }
```

### `POST /api/crm/customers/<id>/calls`

```json
{ "params": { "page": 1, "per_page": 20 } }
```

### `POST /api/crm/customers/<id>/tickets`

### `POST /api/crm/customers/<id>/note/add`

```json
{ "params": { "content": "Called customer, follow up next week." } }
```

### `POST /api/crm/customers/<id>/channel_identity/add`

Link a channel identity (WhatsApp number, email, etc.) to a customer.

```json
{ "params": { "channel": "whatsapp", "value": "+9647...", "label": "Personal" } }
```

### `POST /api/crm/customers/<id>/channel_identity/<ci_id>/update`
### `POST /api/crm/customers/<id>/channel_identity/<ci_id>/delete`

### `POST /api/crm/customers/<id>/interactions`

```json
{ "params": { "page": 1, "per_page": 20 } }
```

### `POST /api/crm/interactions/create`

```json
{
  "params": {
    "customer_id": 123,
    "type": "call",
    "notes": "...",
    "outcome": "interested"
  }
}
```

### `POST /api/crm/customers/setup_stages`

Initialize default kanban stages (admin/first-run only).

---

## 9. Tickets

### `POST /api/crm/tickets/list`

```json
{
  "params": {
    "status": "open",
    "assigned_to": 52,
    "customer_id": 100,
    "priority": "high",
    "page": 1,
    "per_page": 20,
    "search": "billing issue"
  }
}
```

### `POST /api/crm/tickets/search`

```json
{ "params": { "query": "login problem", "limit": 10 } }
```

### `POST /api/crm/tickets/<id>`

Get ticket detail.

### `POST /api/crm/tickets/create`

```json
{
  "params": {
    "subject": "Cannot log in",
    "description": "User reports error 403",
    "customer_id": 100,
    "priority": "high",
    "assigned_to": 52
  }
}
```

### `POST /api/crm/tickets/<id>/update`

```json
{ "params": { "subject": "...", "priority": "low", "description": "..." } }
```

### `POST /api/crm/tickets/<id>/update_status`

```json
{ "params": { "status": "resolved" } }
```

Valid statuses: `open`, `in_progress`, `resolved`, `closed`

### `POST /api/crm/tickets/<id>/assign`

```json
{ "params": { "assigned_to": 52 } }
```

### `POST /api/crm/tickets/<id>/escalate`

```json
{ "params": { "reason": "Customer escalated to manager" } }
```

### `POST /api/crm/tickets/<id>/delete`

### `POST /api/crm/tickets/<id>/note/add`

```json
{ "params": { "content": "Waiting for confirmation from IT." } }
```

### `POST /api/crm/tickets/<id>/notes`

List all notes on a ticket.

---

## 10. Tasks

### `POST /api/crm/tasks/list`

```json
{
  "params": {
    "project_id": 5,
    "assigned_to": 52,
    "status": "todo",
    "page": 1,
    "per_page": 20
  }
}
```

### `POST /api/crm/tasks/my`

Tasks assigned to the current user.

### `POST /api/crm/tasks/<id>`

### `POST /api/crm/tasks/create`

```json
{
  "params": {
    "name": "Follow up with customer",
    "project_id": 5,
    "assigned_to": 52,
    "deadline": "2026-05-30",
    "description": "..."
  }
}
```

### `POST /api/crm/tasks/<id>/update`

### `POST /api/crm/tasks/<id>/update_status`

```json
{ "params": { "status": "done" } }
```

Valid: `todo`, `in_progress`, `done`, `cancelled`

### `POST /api/crm/tasks/<id>/assign`

```json
{ "params": { "user_id": 52 } }
```

### `POST /api/crm/tasks/<id>/delete`

---

## 11. Conversations (Chat)

### `POST /api/crm/supply/conversations/list`

```json
{ "params": { "page": 1, "per_page": 20, "search": "group name" } }
```

### `POST /api/crm/supply/conversations/create`

```json
{
  "params": {
    "name": "Project Alpha",
    "recipient_ids": [32, 53],
    "group_name": "Alpha Team"
  }
}
```

### `POST /api/crm/supply/conversations/<id>/get`

### `POST /api/crm/supply/conversations/<id>/rename`

```json
{ "params": { "name": "New Group Name" } }
```

### `POST /api/crm/supply/conversations/<id>/archive`

### `POST /api/crm/supply/conversations/<id>/leave`

### `POST /api/crm/supply/conversations/<id>/update`

Generic update (avatar, description, settings).

### `POST /api/crm/supply/conversations/<id>/mark_read`

### `POST /api/crm/supply/conversations/<id>/typing`

```json
{ "params": { "is_typing": true } }
```

### `POST /api/crm/supply/conversations/<id>/pinned`

List pinned messages in a conversation.

### `POST /api/crm/supply/conversations/<id>/members/list`
### `POST /api/crm/supply/conversations/<id>/members/add`

```json
{ "params": { "user_ids": [54, 55] } }
```

### `POST /api/crm/supply/conversations/<id>/members/remove`

```json
{ "params": { "user_id": 54 } }
```

### `POST /api/crm/supply/conversations/<id>/members/role`

```json
{ "params": { "user_id": 54, "role": "admin" } }
```

---

### Messages

### `POST /api/crm/supply/messages/list`

```json
{
  "params": {
    "conversation_id": 10,
    "limit": 50,
    "before_id": 9999
  }
}
```

### `POST /api/crm/supply/messages/create`

```json
{
  "params": {
    "conversation_id": 10,
    "body": "Hello team!",
    "attachment_ids": [379001],
    "reply_to_id": null
  }
}
```

### `POST /api/crm/supply/messages/<id>/edit`

```json
{ "params": { "body": "Edited message text" } }
```

### `POST /api/crm/supply/messages/<id>/pin`
### `POST /api/crm/supply/messages/<id>/react`

```json
{ "params": { "emoji": "👍" } }
```

### `POST /api/crm/supply/messages/<id>/delivered`
### `POST /api/crm/supply/messages/<id>/read`

### `POST /api/crm/supply/messages/<id>/delete`

```json
{ "params": { "mode": "for_me" } }
```

`mode`: `for_me` | `for_everyone`

### `POST /api/crm/supply/messages/broadcast`

Send a message to multiple conversations or users.

```json
{ "params": { "body": "Important announcement", "conversation_ids": [10, 11] } }
```

### `POST /api/crm/supply/messages/forward`

```json
{ "params": { "message_id": 5000, "conversation_ids": [10, 11] } }
```

### `POST /api/crm/supply/messages/search`

```json
{ "params": { "conversation_id": 10, "query": "meeting", "limit": 20 } }
```

### `POST /api/crm/supply/chat/bus_channels`

Returns the list of bus channels the current user should subscribe to.

---

### Stories

### `POST /api/crm/supply/stories/feed`

```json
{ "params": { "include_mine": true, "limit": 50 } }
```

### `POST /api/crm/supply/stories/create`

```json
{
  "params": {
    "kind": "image",
    "content": "base64...",
    "caption": "Team outing!",
    "duration": 5
  }
}
```

`kind`: `image` | `video` | `text`

### `POST /api/crm/supply/stories/<id>/view`
### `POST /api/crm/supply/stories/<id>/viewers`
### `POST /api/crm/supply/stories/<id>/delete`

### `POST /api/crm/supply/stories/upload` *(multipart)*

```
Fields: file, kind, duration_seconds
```

---

## 12. Email (Inbox / Outbox)

### Accounts

### `GET/POST /api/lugal/email/accounts`

List email accounts.

### `GET /api/lugal/email/accounts/<id>`

### `PATCH /api/lugal/email/accounts/<id>`

Update account settings.

### `DELETE /api/lugal/email/accounts/<id>`

### `POST /api/lugal/email/accounts/<id>/test`

Test IMAP/SMTP connection.

### `POST /api/lugal/email/accounts/<id>/sync`

Force sync.

### `POST /api/lugal/email/accounts/<id>/set_default`

### `GET /api/lugal/email/accounts/<id>/folders`

List mailbox folders.

### `POST /api/lugal/email/sync/all`

Sync all active accounts.

### Folders

### `POST /api/lugal/email/folders/create`

```json
{ "params": { "account_id": 1, "path": "Projects/Alpha" } }
```

### `POST /api/lugal/email/folders/rename`

```json
{ "params": { "account_id": 1, "old_path": "Projects/Alpha", "new_path": "Projects/Beta" } }
```

### `POST /api/lugal/email/folders/delete`

```json
{ "params": { "account_id": 1, "path": "Projects/Alpha" } }
```

### Signature

### `GET /api/lugal/email/signature`

### `PATCH /api/lugal/email/signature`

```json
{ "params": { "signature": "<p>Best regards,<br>Ahmed</p>" } }
```

---

### Messages

### `GET /api/lugal/email/messages`  
### `GET /api/lugal/email/mailbox/inbox`  
### `GET /api/lugal/email/mailbox/<folder_name>`

List messages. Query params:

```
?account_id=1&folder=INBOX&search=invoice&is_read=false&page=1&per_page=20
```

### `GET /api/lugal/email/messages/<id>`

Get message detail.

**Key fields in response:**

| Field | Description |
|-------|-------------|
| `body_html_resolved` | HTML with inline images already embedded (use this for display) |
| `inline_attachments` | Always `[]` (images are in `body_html_resolved`) |
| `has_inline_attachments` | `true` if original email had inline images |
| `attachments` | Regular file attachments |
| `is_read` | Whether message is read |
| `read_at` | Timestamp when marked read |
| `recipient_read_at` | For sent messages: when recipient read it |

### `GET /api/lugal/email/messages/<id>/thread`

Full email thread (by `thread_id`).

### `POST /api/lugal/email/messages/details`

Bulk fetch.

```json
{ "params": { "message_ids": [1001, 1002, 1003] } }
```

(max 50 IDs)

### `POST /api/lugal/email/messages/<id>/read`

Toggle read status.

### `POST /api/lugal/email/messages/<id>/star`

Toggle star.

### `POST /api/lugal/email/messages/<id>/archive`
### `POST /api/lugal/email/messages/<id>/unarchive`
### `POST /api/lugal/email/messages/<id>/restore`

(from trash)

### `DELETE /api/lugal/email/messages/<id>/permanent`

Permanent delete (trash only).

### `POST /api/lugal/email/messages/bulk_delete`

```json
{ "params": { "message_ids": [1001, 1002] } }
```

### `POST /api/lugal/email/messages/<id>/move`

```json
{ "params": { "folder": "Archive" } }
```

### `POST /api/lugal/email/messages/bulk_move_by_sender`

Move all messages from a sender.

### `GET /api/lugal/email/messages/<id>/related`

```
?type=thread&scope=account&limit=20&offset=0
```

---

### Send & Compose

### `POST /api/lugal/email/send`

```json
{
  "params": {
    "account_id": 1,
    "to": ["recipient@example.com"],
    "cc": [],
    "bcc": [],
    "subject": "Project Update",
    "body": "<p>Hello</p>",
    "attachment_ids": [379001]
  }
}
```

### `POST /api/lugal/email/messages/<id>/reply`

```json
{
  "params": {
    "body": "<p>Thanks</p>",
    "attachment_ids": []
  }
}
```

### `POST /api/lugal/email/messages/<id>/reply_all`

Same as reply but includes all original recipients.

### `POST /api/lugal/email/messages/<id>/forward`

```json
{
  "params": {
    "to": ["other@example.com"],
    "body": "<p>FYI</p>"
  }
}
```

---

### Drafts

### `GET /api/lugal/email/drafts`

```
?limit=20&offset=0
```

### `POST /api/lugal/email/drafts`

Create draft (same body as send).

### `GET /api/lugal/email/drafts/<id>`
### `PUT /api/lugal/email/drafts/<id>`

Update draft.

### `DELETE /api/lugal/email/drafts/<id>`

### `POST /api/lugal/email/drafts/<id>/send`

Send a saved draft.

---

### Notifications

### `GET /api/lugal/email/notifications`  
### `GET /api/lugal/email/unread`

Returns unread counts and latest notifications.

### `GET /api/lugal/email/senders/resolve`

```
?email=sender@example.com
```

Resolves an email address to a known CRM contact.

---

### CRM Email (customer-linked)

### `POST /api/crm/email/customer/<id>/messages`

```json
{
  "params": {
    "folder": "inbox",
    "page": 1,
    "per_page": 20,
    "is_read": null
  }
}
```

### `POST /api/crm/email/customer/<id>/thread`

```json
{ "params": { "subject_contains": "invoice" } }
```

### `POST /api/crm/email/messages/list`

```json
{
  "params": {
    "folder": "inbox",
    "customer_id": 100,
    "ticket_id": 55,
    "is_read": false,
    "page": 1,
    "per_page": 20
  }
}
```

### `POST /api/crm/email/messages/<id>`

```json
{ "params": { "preview": false } }
```

### Email Rule Management

### `GET/POST /api/lugal/email/rules`

List / create email rules.

### `GET/PUT/DELETE /api/lugal/email/rules/<id>`

### `POST /api/lugal/email/rules/apply_all`

### `POST /api/lugal/email/rules/test`

### `POST /api/lugal/email/rules/from_template`

### Quick Steps

### `GET/POST /api/lugal/email/quick_steps`
### `GET/PUT/DELETE /api/lugal/email/quick_steps/<id>`
### `POST /api/lugal/email/messages/<id>/apply_quick_step`

```json
{ "params": { "quick_step_id": 3 } }
```

---

## 13. Employees & Workforce

### `POST /api/crm/employees/list`

```json
{
  "params": {
    "search": "ahmed",
    "page": 1,
    "per_page": 50,
    "is_active": true,
    "include_kpi": false
  }
}
```

> Search works on name AND email/login.

### `POST /api/crm/employees/<id>`

Get employee detail.

### `POST /api/crm/employees/check-username`

```json
{ "params": { "username": "john.doe" } }
```

### `POST /api/crm/employees/email/test-connection`

Test an email account for a new employee.

### `POST /api/crm/employees/create`

```json
{
  "params": {
    "name": "John Doe",
    "login": "john@company.com",
    "password": "secret",
    "role": "agent",
    "branch_id": 2,
    "job_title": "Agent",
    "phone": "+964..."
  }
}
```

### `POST /api/crm/employees/<id>/update`

### `POST /api/crm/employees/<id>/deactivate`
### `POST /api/crm/employees/<id>/activate`
### `POST /api/crm/employees/<id>/delete`

### `POST /api/crm/employees/<id>/kpi`

```json
{ "params": { "date_from": "2026-01-01", "date_to": "2026-05-17" } }
```

### `POST /api/crm/employees/<id>/attendance`

### Shifts

### `POST /api/crm/shifts/list`
### `POST /api/crm/shifts/create`

```json
{
  "params": {
    "name": "Morning Shift",
    "start_time": "08:00",
    "end_time": "16:00",
    "days": ["mon", "tue", "wed", "thu", "fri"]
  }
}
```

### `POST /api/crm/shifts/<id>/update`
### `POST /api/crm/shifts/<id>/delete`

### Attendance

### `POST /api/crm/attendance/check_in`

```json
{ "params": { "shift_id": 2, "location": "Office" } }
```

### `POST /api/crm/attendance/check_out`

### `POST /api/crm/attendance/list`

```json
{ "params": { "employee_id": 52, "date_from": "2026-05-01", "date_to": "2026-05-17" } }
```

### `POST /api/crm/attendance/live_status`

Who is currently checked in.

### Message Templates

### `POST /api/crm/templates/list`
### `POST /api/crm/templates/create`

```json
{ "params": { "name": "Greeting", "body": "Hello {{name}}, how can I help?" } }
```

### `POST /api/crm/templates/<id>/update`
### `POST /api/crm/templates/<id>/delete`
### `POST /api/crm/templates/<id>/render`

```json
{ "params": { "variables": { "name": "Ahmed" } } }
```

---

## 14. Analytics

All analytics endpoints require supervisor or above role.

### `POST /api/crm/analytics/dashboard_stats`

```json
{ "params": { "date_from": "2026-05-01", "date_to": "2026-05-17", "branch_id": null } }
```

### `POST /api/crm/analytics/channel_report`

```json
{ "params": { "date_from": "...", "date_to": "...", "channel": "email" } }
```

### `POST /api/crm/analytics/employee_kpi`

```json
{ "params": { "employee_id": 52, "date_from": "...", "date_to": "..." } }
```

### `POST /api/crm/analytics/all_employees_kpi`

```json
{ "params": { "date_from": "...", "date_to": "...", "branch_id": null } }
```

### `POST /api/crm/analytics/branch_report`

### `POST /api/crm/analytics/supervisor_dashboard`

```json
{ "params": { "supervisor_id": 30, "date_from": "...", "date_to": "..." } }
```

### `POST /api/crm/analytics/ai_vs_human`

AI-resolved vs human-resolved ticket comparison.

### `POST /api/crm/analytics/audit_log`

```json
{ "params": { "page": 1, "per_page": 50, "user_id": null, "action": null } }
```

### `POST /api/crm/analytics/export_kpi` *(HTTP, returns file)*

Returns a CSV/Excel download.

```
POST with JSON body: { "date_from": "...", "date_to": "...", "format": "xlsx" }
Authorization: Bearer <token>
```

---

## 15. Supply Chain

### Containers

### `POST /api/crm/supply/containers/<id>/attachments/list`
### `POST /api/crm/supply/attachments/upload` *(multipart)*

```
Fields: file (or files[]), container_id
```

### `POST /api/crm/supply/containers/<id>/attachments/<att_id>/delete`

### `POST /api/crm/supply/containers/<id>/penalties/list`

### `POST /api/crm/supply/containers/<id>/add_penalty`

```json
{
  "params": {
    "amount": 500,
    "penalty_type": "delay",
    "reason": "3 days late",
    "currency_id": 1,
    "penalty_date": "2026-05-10"
  }
}
```

### `POST /api/crm/supply/containers/<id>/penalties/<pid>/delete`

### Purchase Orders

### `POST /api/crm/supply/po/suggested`

```json
{ "params": { "page": 1, "per_page": 20, "division": "electronics" } }
```

### Negotiations

### `POST /api/crm/supply/negotiations/list`

```json
{ "params": { "status": "open", "page": 1, "per_page": 20 } }
```

### `POST /api/crm/supply/negotiations/<id>/get`
### `POST /api/crm/supply/negotiations/create`

```json
{
  "params": {
    "vendor_id": 10,
    "subject": "Q2 Supply Agreement",
    "terms": "..."
  }
}
```

### `POST /api/crm/supply/negotiations/<id>/update`
### `POST /api/crm/supply/negotiations/<id>/delete`
### `POST /api/crm/supply/negotiations/<id>/confirm`
### `POST /api/crm/supply/negotiations/<id>/finalize`
### `POST /api/crm/supply/negotiations/<id>/e_sign_approve`

### `POST /api/crm/supply/negotiations/<id>/offers/add`

```json
{ "params": { "price": 10000, "currency_id": 1, "valid_until": "2026-06-01", "notes": "..." } }
```

### Item Requests

### `POST /api/crm/supply/item_requests/list`
### `POST /api/crm/supply/item_requests/<id>/get`
### `POST /api/crm/supply/item_requests/create`
### `POST /api/crm/supply/item_requests/<id>/update`
### `POST /api/crm/supply/item_requests/<id>/update_status`

```json
{ "params": { "status": "approved" } }
```

### `POST /api/crm/supply/item_requests/<id>/delete`

### Clearance Companies

### `POST /api/crm/supply/clearance_companies/list`
### `POST /api/crm/supply/clearance_companies/<id>/get`
### `POST /api/crm/supply/clearance_companies/create`
### `POST /api/crm/supply/clearance_companies/<id>/update`
### `POST /api/crm/supply/clearance_companies/<id>/delete`

### Inventory Min/Max

### `POST /api/crm/supply/inventory/minmax`
### `POST /api/crm/supply/inventory/minmax/update`
### `POST /api/crm/supply/inventory/minmax/delete`

### Payments

### `POST /api/crm/supply/payments/list`

```json
{ "params": { "po_id": 55, "status": "pending", "page": 1, "per_page": 20 } }
```

### `POST /api/crm/supply/payments/<id>/get`
### `POST /api/crm/supply/payments/create`
### `POST /api/crm/supply/payments/<id>/update`
### `POST /api/crm/supply/payments/<id>/delete`

### Shipments

### `POST /api/crm/supply/shipments/list`
### `POST /api/crm/supply/shipments/<id>/get`
### `POST /api/crm/supply/shipments/create`
### `POST /api/crm/supply/shipments/<id>/update`
### `POST /api/crm/supply/shipments/<id>/delete`
### `POST /api/crm/supply/shipments/<id>/link_orders`

### Supply Notifications

### `POST /api/crm/supply/notifications/list`
### `POST /api/crm/supply/notifications/create`
### `POST /api/crm/supply/notifications/<id>/mark_read`
### `POST /api/crm/supply/notifications/mark_all_read`
### `POST /api/crm/supply/notifications/<id>/delete`

---

## 16. LocalSend File Transfers

> The CRM runs in a browser. Files are stored on Odoo server and always downloadable via `download_url`. LocalSend P2P delivery is an optional bonus.

### Device Registration

### `POST /api/crm/localsend/devices/register`

Call once per app session.

```json
{
  "params": {
    "device_name": "Chrome on Ahmed's PC",
    "lan_ip": "192.168.116.228",
    "port": 53317,
    "protocol": "http",
    "device_uid": "optional-stable-id"
  }
}
```

### `POST /api/crm/localsend/devices/heartbeat`

Call every **30 seconds** while app is open. Triggers auto-retry of `available`/`failed` transfers when device transitions offline → online.

```json
{ "params": { "lan_ip": "192.168.116.228" } }
```

### `POST /api/crm/localsend/devices/list`

```json
{ "params": { "owner_only": false, "online_only": false } }
```

### `POST /api/crm/localsend/devices/<id>/ping`

Test if a device's LocalSend port is open.

```json
{ "params": { "timeout": 5 } }
```

Response:

```json
{
  "success": false,
  "error": "Device not reachable: Connection refused — LocalSend app is likely not running.",
  "data": { "device_id": 1, "ip_address": "192.168.1.50", "port": 53317, "reachable": false, "reason": "..." }
}
```

### `POST /api/crm/localsend/resolve`

Get connection URLs for a target user's device (for direct P2P transfers).

```json
{ "params": { "target_user_id": 32, "target_device_id": null } }
```

### `POST /api/crm/localsend/devices/create`

Manually register a device (admin/manager use).

---

### Transfers

### `POST /api/crm/localsend/transfers/create`

```json
{
  "params": {
    "target_user_id": 32,
    "attachment_id": 379001,
    "name": "Project Photo",
    "send_now": true
  }
}
```

**Behavior:**
1. Always creates transfer record and sends bus notification to receiver with `download_url` (includes `access_token` — no login required)
2. If `send_now=true`: attempts LocalSend P2P push
   - LocalSend open → `status: "sent"` + `localsend.transfer.sent` event
   - LocalSend closed → `status: "available"` + `localsend.transfer.available` event with `download_url`
3. File is **always** downloadable via `download_url` regardless of LocalSend status — `access_token` in URL means no Odoo session needed

**Response (LocalSend open):**

```json
{
  "success": true,
  "data": {
    "id": 4,
    "status": "sent",
    "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
    "preview_url":  "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc",
    "target_device_url": "http://192.168.116.228:53317",
    "file_name": "photo.jpg",
    "file_size": 324524,
    "mime_type": "image/jpeg"
  }
}
```

**Response (LocalSend not running — graceful fallback):**

```json
{
  "success": true,
  "data": {
    "id": 4,
    "status": "available",
    "error_message": "LocalSend app is not running on Umar CTO's Device (192.168.116.228:53317). The file is available for download from the app.",
    "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
    "preview_url":  "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc"
  }
}
```

> `success: true` even when LocalSend is not running. `status: "available"` is not an error — the file is ready to download.

### `POST /api/crm/localsend/transfers/list`

```json
{
  "params": {
    "direction": "sent",
    "status": "queued",
    "limit": 50,
    "offset": 0
  }
}
```

`direction`: `sent` | `received` | `all`

### `POST /api/crm/localsend/transfers/<id>/retry`

Retry a `queued` / `available` / `failed` transfer via LocalSend.

### `POST /api/crm/localsend/transfers/<id>/send`

Trigger LocalSend push (re-attempt).

### `POST /api/crm/localsend/transfers/<id>/downloaded`

**Receiver calls this** after downloading from browser. Marks as `downloaded` and notifies sender.

### `POST /api/crm/localsend/transfers/<id>/cancel`

---

### Transfer Status Reference

| Status | Meaning | FE action |
|--------|---------|-----------|
| `queued` | Waiting — LocalSend not reachable | Show **Download** button |
| `available` | File on Odoo, downloadable | Show **Download** button |
| `sending` | LocalSend push in progress | Show spinner |
| `sent` | Delivered via LocalSend P2P | ✅ |
| `downloaded` | Receiver confirmed browser download | ✅ |
| `failed` | Unrecoverable error | ❌ Retry? |
| `cancelled` | Cancelled | — |

### Frontend Integration Pattern

```javascript
// 1. On app startup
await api.post('/api/crm/localsend/devices/register', { lan_ip: myIp });

// 2. Subscribe to bus
busService.subscribe('localsend_user.' + myUserId, (event, payload) => {
  if (event === 'localsend.transfer.available') {
    // Show notification with download button
    showNotification({
      title: `${payload.source_user_name} sent you "${payload.file_name}"`,
      action: () => {
        window.location.href = payload.download_url;
        // After download, confirm receipt
        api.post(`/api/crm/localsend/transfers/${payload.transfer_id}/downloaded`);
      }
    });
  }
  if (event === 'localsend.transfer.sent') {
    showToast(`✅ File delivered via LocalSend`);
  }
  if (event === 'localsend.transfer.downloaded') {
    showToast(`✅ ${payload.target_user_name} downloaded the file`);
  }
});

// 3. Heartbeat every 30s
setInterval(() => api.post('/api/crm/localsend/devices/heartbeat', { lan_ip: myIp }), 30000);

// 4. Send a file
const resp = await api.post('/api/crm/localsend/transfers/create', {
  target_user_id: 32,
  attachment_id: 379001,
  send_now: true
});
// Always show download_url as fallback even if sent via LocalSend
console.log('Download URL:', resp.data.download_url);
```

---

## 17. Notifications

### `GET /api/crm/notifications`

```
?since=2026-05-17T00:00:00&limit=50
```

### `POST /api/crm/notifications/mark_read`

```json
{
  "params": {
    "type": "chat",
    "conversation_id": 10,
    "message_ids": [5001, 5002]
  }
}
```

`type`: `chat` | `email` | `all`

### Marquee Scrolling Notices

### `POST /api/crm/marquee/create`

```json
{
  "params": {
    "message": "System maintenance tonight at 10PM",
    "message_ar": "صيانة النظام الليلة",
    "starts_at": "2026-05-17T20:00:00",
    "expires_at": "2026-05-17T23:00:00",
    "bg_color": "#FF0000",
    "text_color": "#FFFFFF",
    "speed": 50
  }
}
```

### `POST /api/crm/marquee/active`

Returns currently active marquee notices.

### `POST /api/crm/marquee/list`

```json
{ "params": { "page": 1, "per_page": 20 } }
```

### `POST /api/crm/marquee/update`

```json
{ "params": { "id": 5, "message": "Updated text", "speed": 60 } }
```

---

## 18. POS Perfume — Orders API

**Base prefix:** `/api/pos_perfume/v1`

### Reference Data

### `GET /api/pos_perfume/v1/sections`

Product sections.

### `GET /api/pos_perfume/v1/categories`

Product categories.

### `GET /api/pos_perfume/v1/pricelists`

Available pricelists.

### `GET /api/pos_perfume/v1/warehouses`

Available warehouses.

### `GET /api/pos_perfume/v1/customers`

Customer list.

### `GET /api/pos_perfume/v1/invoice-types`

Invoice type enum for order creation.

### Settings

### `GET /api/pos_perfume/v1/settings`

### `PUT /api/pos_perfume/v1/settings`

```json
{ "exchange_rate": 1490.5 }
```

---

### Products

### `GET /api/pos_perfume/v1/products`

```
?search=perfume&categ_id=5&pricelist_id=2&limit=20&offset=0
```

### `GET /api/pos_perfume/v1/products/<id>`

### `GET/POST /api/pos_perfume/v1/products/by_primary_sales_uom`

```
?weight_prefix=heavy&pricelist_id=2&categ_id=5&query=rose&fetch_all=false&limit=20&offset=0
```

---

### Orders

### `GET /api/pos_perfume/v1/orders`

```
?state=quotation&query=S0318&limit=20&offset=0
```

`state` filter: `draft` | `quotation` | `sale` | `done` | `cancel`  
`query` searches: order name, partner name, sale order name

**Response fields per order:** `id`, `name`, `state`, `partner_id`, `partner_name`, `date_order`, `order_line_ids`, `global_discount_percent`, `global_discount_amount`, `amount_untaxed`, `amount_total`, `currency`, `sale_order_id`, `invoice_type_id`, `order_activity`

### `GET /api/pos_perfume/v1/orders/<id>`

Full order with `order_activity` log.

**`order_activity` structure:**

```json
[
  {
    "id": null,
    "type": "created",
    "timestamp": "2026-05-01T10:00:00",
    "author": "Ahmed",
    "description": "Order S03214 created",
    "changes": []
  },
  {
    "id": 5001,
    "type": "status_change",
    "timestamp": "2026-05-02T14:30:00",
    "author": "Ahmed",
    "description": "Status changed: Draft → Sale Order",
    "changes": [{ "field": "state", "old": "draft", "new": "sale" }]
  }
]
```

### `POST /api/pos_perfume/v1/orders`

Create a new order.

```json
{
  "partner_id": 100,
  "invoice_type_id": 1,
  "pricelist_id": 2,
  "warehouse_id": 1,
  "global_discount_percent": 5.0,
  "order_line_ids": [
    {
      "product_id": 13186,
      "uom_id": 30,
      "qty": 3,
      "price_unit": 60.0,
      "discount": 0.0
    }
  ]
}
```

### `PUT /api/pos_perfume/v1/orders/<id>`

Update order (syncs to SAP).

```json
{
  "global_discount_percent": 10.0,
  "order_line_ids": [
    { "id": 999, "qty": 5, "price_unit": 55.0 },
    { "product_id": 13187, "uom_id": 30, "qty": 2, "price_unit": 70.0 }
  ]
}
```

### `DELETE /api/pos_perfume/v1/orders/<id>`

Cancel the order.

### `POST /api/pos_perfume/v1/orders/<id>/confirm`

Confirm quotation → Sale Order (syncs to SAP).

### `POST /api/pos_perfume/v1/orders/<id>/quotation`

Push as SAP quotation.

### `GET /api/pos_perfume/v1/orders/<id>/report`

Download order report.

```
?type=nbs&format=pdf&download=true
```

`type`: `nbs` | `simple` | `gold` | `default`  
`format`: `pdf` | `html`  
`download`: `true` | `false`

---

### Order Line Fields

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | int | Product ID |
| `uom_id` | int | Unit of Measure ID |
| `qty` | float | Quantity |
| `price_unit` | float | Unit price |
| `discount` | float | Line discount % |
| `price_subtotal` | float | Line total (read-only) |

### Order-Level Discount Fields

| Field | Type | Description |
|-------|------|-------------|
| `global_discount_percent` | float | Order-level discount % |
| `global_discount_amount` | float | Order-level discount amount (computed) |

---

## 19. Inventory API

**Base prefix:** `/api/inventory/v1`

### Auth

### `POST /api/inventory/v1/auth/login`

### `GET /api/inventory/v1/auth/me`

### Audits

### `GET/POST /api/inventory/v1/audits`

### `DELETE /api/inventory/v1/audits/<id>`

### Sessions

### `POST /api/inventory/v1/audits/sessions`

### `POST /api/inventory/v1/audits/sessions/<id>/close`

### Items

### `GET /api/inventory/v1/items`

```
?search=SKU001&warehouse_id=1&page=1&per_page=20
```

### `GET /api/inventory/v1/items/<id>`

### `GET /api/inventory/v1/items/stats`

### Warehouses

### `GET /api/inventory/v1/warehouses`

### Barcodes

### `GET/POST /api/inventory/v1/barcodes`

### `PUT/DELETE /api/inventory/v1/barcodes/<id>`

### Search

### `GET/POST /api/inventory/v1/search`

### `GET /api/inventory/v1/products`

### `GET /api/inventory/v1/products/<id>`

### Users

### `GET/POST /api/inventory/v1/users`

### `PUT/DELETE /api/inventory/v1/users/<id>`

### `GET /api/inventory/v1/users/odoo-candidates`

---

## 20. Config & Misc

### CORS Preflight

All `/api/crm/*`, `/api/lugal/*`, `/lugal/*` endpoints respond to **OPTIONS** automatically.

### `GET /api/crm/analytics/audit_log`

Admin audit trail.

### Admin Email Accounts

### `POST /api/crm/admin/email/accounts`

List email accounts (admin view).

### `POST /api/crm/admin/email/accounts/<id>/update`

```json
{
  "params": {
    "imap_server": "imap.gmail.com",
    "imap_port": 993,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "password": "app-password"
  }
}
```

### `POST /api/crm/admin/email/accounts/<id>/sync`

Force admin sync.

---

## 21. Error Responses

### Standard error shape

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Human-readable error message",
    "code": 403
  }
}
```

### Common error codes

| Message | Cause |
|---------|-------|
| `Unauthorized` | Missing or expired JWT token |
| `Forbidden` | Valid token but insufficient role/permission |
| `User not found` | `user_id` does not exist |
| `Attachment not found` | `attachment_id` does not exist |
| `Target device not found` | LocalSend device not registered for user |
| `Cannot cancel a transfer with status '...'` | Status transition not allowed |

### Odoo JSON-RPC error (network-level)

If Odoo itself throws an unhandled exception, the response will have:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": 200,
    "message": "Odoo Server Error",
    "data": { "name": "...", "message": "...", "exception_type": "..." }
  }
}
```

---

*This document covers all endpoints as of 2026-05-17. Generated from live source code.*
