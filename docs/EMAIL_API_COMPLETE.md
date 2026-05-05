# Email System — Complete Backend API Reference

> **Last Updated:** May 2026  
> **Audience:** Frontend developers  
> **Base URL:** All endpoints are relative to the server root (e.g. `http://192.168.116.228:5172`)  
> **Auth:** Every endpoint requires a JWT token in the `Authorization: Bearer <token>` header.

---

## Table of Contents

1. [Authentication Flow](#1-authentication-flow)
2. [Account Management](#2-account-management)
3. [Sync & Notifications](#3-sync--notifications)
4. [Message List & Search](#4-message-list--search)
5. [Message Detail & Thread](#5-message-detail--thread)
6. [Compose — Send / Reply / Reply All / Forward](#6-compose)
7. [Drafts](#7-drafts)
8. [Message Actions](#8-message-actions)
9. [Attachments — Regular & Inline Images](#9-attachments)
10. [Folders — List & Move](#10-folders)
11. [Inbox Rules](#11-inbox-rules)
12. [Quick Steps](#12-quick-steps)
13. [Sender Resolve (Contact Info)](#13-sender-resolve)
14. [Related Messages](#14-related-messages)
15. [Email Signature](#15-email-signature)
16. [CRM Email Layer](#16-crm-email-layer)
17. [Real-time WebSocket Events](#17-real-time-websocket-events)
18. [Message Object Reference](#18-message-object-reference)
19. [Error Reference](#19-error-reference)

---

## 1. Authentication Flow

On **every login** the backend automatically triggers a full IMAP sync for the user's email accounts. No separate sync call is needed after login.

```
POST /api/crm/users/me/login
→ returns { token: "...", ... }
→ backend immediately starts IMAP sync in background
```

Include the token in every subsequent request:
```
Authorization: Bearer <token>
```

---

## 2. Account Management

### List accounts
```
GET /api/lugal/email/accounts
```
**Response:**
```json
{
  "success": true,
  "data": {
    "accounts": [
      {
        "id": 1,
        "email_address": "user@example.com",
        "display_name": "John",
        "is_default": true,
        "imap_host": "mail.example.com",
        "imap_port": 993,
        "smtp_host": "mail.example.com",
        "smtp_port": 465,
        "sync_status": "success",
        "last_sync_date": "2026-05-05T10:00:00+03:00",
        "needs_setup": false
      }
    ]
  }
}
```

### Create account
```
POST /api/lugal/email/accounts
```
**Body:**
```json
{
  "email_address": "user@example.com",
  "password": "secret",
  "display_name": "John",
  "imap_host": "mail.example.com",
  "imap_port": 993,
  "imap_use_ssl": true,
  "smtp_host": "mail.example.com",
  "smtp_port": 465,
  "smtp_use_tls": true,
  "is_default": true
}
```

### Update account
```
PUT /api/lugal/email/accounts/<id>
```
Same body fields as create (all optional).

### Delete account
```
DELETE /api/lugal/email/accounts/<id>
```

### Test connection
```
POST /api/lugal/email/accounts/<id>/test
```
Returns `{ "success": true, "data": { "imap": true, "smtp": true } }`

### Set default account
```
POST /api/lugal/email/accounts/<id>/set_default
```

---

## 3. Sync & Notifications

### Manual sync — all accounts
```
POST /api/lugal/email/sync/all
```

### Manual sync — single account
```
POST /api/lugal/email/accounts/<id>/sync
```

### Unread counts & sync status (poll this every 30s as fallback)
```
GET /api/lugal/email/notifications
GET /api/lugal/email/unread          ← alias
```
Optional query params:
- `since=2026-05-05T10:00:00+03:00` — only return messages newer than this timestamp

**Response:**
```json
{
  "success": true,
  "data": {
    "inbox": 5,
    "total": 12,
    "per_folder": { "inbox": 5, "sent": 0, "drafts": 2, "trash": 0 },
    "account_configured": true,
    "accounts": [
      { "id": 1, "email": "user@example.com", "unread": 5, "sync_status": "success", "needs_setup": false }
    ],
    "sync_status": "success",
    "last_sync_date": "2026-05-05T10:00:00+03:00",
    "checked_at": "2026-05-05T10:00:05+03:00",
    "new_messages": [
      { "id": 99, "subject": "Hello", "from_address": "alice@example.com", "date": "..." }
    ],
    "recently_sent": []
  }
}
```

---

## 4. Message List & Search

### List messages (inbox / folder)
```
GET /api/lugal/email/sync
```
**Query parameters:**

| Param | Type | Default | Description |
|---|---|---|---|
| `folder` | string | `inbox` | `inbox`, `sent`, `drafts`, `trash`, `archive`, `spam`, or IMAP folder name |
| `account_id` | int | — | Filter to a specific account |
| `limit` | int | `50` | Page size |
| `offset` | int | `0` | Pagination offset |
| `search` | string | — | Full-text search across subject, from, body |
| `filter_unread` | bool | — | `true` = only unread |
| `filter_starred` | bool | — | `true` = only starred |
| `filter_important` | bool | — | `true` = only important |
| `filter_mentioned` | bool | — | `true` = only messages where you are in To: |
| `filter_has_attachment` | bool | — | `true` = only messages with attachments |

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [ /* array of Message Objects (see §18) */ ],
    "total": 120,
    "offset": 0,
    "limit": 50,
    "has_more": true
  }
}
```

### Bulk message details (fetch multiple at once)
```
POST /api/lugal/email/messages/details
```
**Body:** `{ "message_ids": [1, 2, 3, 4] }`  
Returns full message objects (including `body_html`, `body_text`, `attachments`) for all IDs in a single call.

---

## 5. Message Detail & Thread

### Single message detail
```
GET /api/lugal/email/messages/<id>
```
Returns a full Message Object including `body_html`, `body_text`, `attachments`.  
**Does NOT auto-mark as read.** Call `POST .../read` explicitly.

### Patch message (update fields)
```
PATCH /api/lugal/email/messages/<id>
```
**Body:** any subset of `{ is_read, is_starred, is_flagged, is_important }`

### Thread view (full email chain)
```
GET /api/lugal/email/messages/<id>/thread
```
Returns:
```json
{
  "success": true,
  "data": {
    "thread_id": "<thread-msg-id@domain>",
    "subject": "Re: Meeting",
    "messages": [ /* full Message Objects ordered oldest→newest */ ]
  }
}
```

---

## 6. Compose

All compose endpoints (send, reply, reply_all, forward, send_draft) share these common optional fields:

| Field | Type | Description |
|---|---|---|
| `importance` | `"high"` \| `"normal"` | Sets `X-Priority`, `X-MSMail-Priority`, `Importance` headers. Default: `"normal"` |
| `request_read_receipt` | boolean | Adds `Disposition-Notification-To` header (RFC 3798). Prompts recipient's client for a read notification. Default: `false` |
| `attachment_ids` | int[] | IDs from the upload endpoint (both regular and inline images) |

### Send new email
```
POST /api/lugal/email/send
```
**Body:**
```json
{
  "account_id": 1,
  "to": ["alice@example.com"],
  "cc": ["bob@example.com"],
  "bcc": ["charlie@example.com"],
  "subject": "Hello",
  "body_html": "<p>Hi Alice</p>",
  "body_text": "Hi Alice",
  "attachment_ids": [42, 43],
  "importance": "high",
  "request_read_receipt": false
}
```

### Reply
```
POST /api/lugal/email/messages/<id>/reply
```
**Body:**
```json
{
  "body_html": "<p>Thanks!</p>",
  "body_text": "Thanks!",
  "attachment_ids": [],
  "importance": "normal",
  "request_read_receipt": false
}
```
The backend automatically appends the quoted original email below your reply text in both HTML and plain-text versions.

**GET prefill** (populate the compose form):
```
GET /api/lugal/email/messages/<id>/reply
```
Returns `{ to, subject, account_id }`.

### Reply All
```
POST /api/lugal/email/messages/<id>/reply_all
```
Same body as reply. The backend auto-populates `to` and `cc` from the original message's From/To/Cc fields, excluding your own address.

**GET prefill:**
```
GET /api/lugal/email/messages/<id>/reply_all
```
Returns `{ to: [...], cc: [...], subject, account_id }` — use this to pre-fill the compose form.

### Forward
```
POST /api/lugal/email/messages/<id>/forward
```
**Body:**
```json
{
  "to": ["dave@example.com"],
  "cc": [],
  "body_html": "<p>FYI</p>",
  "attachment_ids": [],
  "importance": "normal",
  "request_read_receipt": false
}
```
The backend prepends the original message body with a `Fwd:` attribution block.

---

## 7. Drafts

### Create draft
```
POST /api/lugal/email/drafts
```
**Body:** Same fields as Send. Returns a draft Message Object.

### List drafts
```
GET /api/lugal/email/drafts
```

### Update draft
```
PUT /api/lugal/email/drafts/<id>
```
**Body:** Any fields to update. Pass `attachment_ids` to update attachments.

### Delete draft
```
DELETE /api/lugal/email/drafts/<id>
```

### Send draft
```
POST /api/lugal/email/drafts/<id>/send
```
**Body (optional overrides):**
```json
{
  "to": ["alice@example.com"],
  "subject": "Updated subject",
  "body_html": "<p>Updated body</p>",
  "attachment_ids": [42],
  "importance": "high",
  "request_read_receipt": true
}
```
All fields are optional — omit them to send with whatever was saved in the draft.

---

## 8. Message Actions

### Mark read / unread
```
POST /api/lugal/email/messages/<id>/read
```
**Body:** `{ "is_read": true }` or `{ "is_read": false }`

### Star / unstar
```
POST /api/lugal/email/messages/<id>/star
```
**Body:** `{ "is_starred": true }` or `{ "is_starred": false }`

> **Note:** `is_starred` and `is_flagged` are now **independent** fields. Setting one does not affect the other.

### Archive
```
POST /api/lugal/email/messages/<id>/archive
```

### Unarchive
```
POST /api/lugal/email/messages/<id>/unarchive
```

### Move to trash (restore)
```
POST /api/lugal/email/messages/<id>/restore
```
Body: `{ "folder": "trash" }` or `{ "folder": "inbox" }` to restore.

### Permanent delete
```
DELETE /api/lugal/email/messages/<id>/permanent
```

### Bulk delete
```
POST /api/lugal/email/messages/bulk_delete
```
**Body:** `{ "message_ids": [1, 2, 3] }`

### Link message to CRM customer / ticket
```
POST /api/lugal/email/messages/<id>/link
```
**Body:** `{ "customer_id": 5 }` or `{ "ticket_id": 12 }`

### Unlink from CRM
```
POST /api/lugal/email/messages/<id>/unlink
```

---

## 9. Attachments

### Upload regular attachments
```
POST /api/lugal/email/attachments/upload
Content-Type: multipart/form-data

files[]: <file1>
files[]: <file2>
```
**Response:**
```json
{
  "success": true,
  "data": {
    "attachments": [
      {
        "id": 42,
        "name": "invoice.pdf",
        "mimetype": "application/pdf",
        "size": 102400,
        "url": "/web/content/42?access_token=...",
        "inline": false
      }
    ]
  }
}
```
Pass the returned `id` values in `attachment_ids` when sending.

---

### Upload inline images (insert image in body)
```
POST /api/lugal/email/attachments/upload
Content-Type: multipart/form-data

files[]: <image file>
inline: true
```
**Response:**
```json
{
  "success": true,
  "data": {
    "attachments": [
      {
        "id": 123,
        "name": "photo.png",
        "mimetype": "image/png",
        "size": 45678,
        "url": "/web/content/123?access_token=...",
        "inline": true,
        "cid": "cid:img-abc123def456@lugal.mail"
      }
    ]
  }
}
```

**Embed in the HTML body:**
```html
<img src="cid:img-abc123def456@lugal.mail" alt="photo" />
```

**Include the attachment ID in `attachment_ids`** when calling send/reply/etc. — along with regular attachment IDs:
```json
{ "attachment_ids": [42, 123] }
```

The backend automatically:
- Detects inline images by their stored `cid` marker
- Wraps them in a `multipart/related` MIME structure so email clients render them inline
- **Excludes inline images from the `attachments[]` list** returned by message detail — only regular file attachments appear there

**Size limit:** 1 GB per file.

---

### How to build "Insert Image" in the composer

1. User clicks "Insert Image" → open file picker
2. Upload the file with `inline: true`
3. Get back `cid: "cid:img-xxx@lugal.mail"`
4. Insert into the rich-text editor as `<img src="cid:img-xxx@lugal.mail">`
5. Store the `id` in a local list of inline attachment IDs
6. On send, merge inline IDs + regular attachment IDs → pass as `attachment_ids`

---

### Supported compose insert options (backend status)

| Feature | Backend Support | Notes |
|---|---|---|
| **Inline images** | ✅ Full support | Upload with `inline: true`, embed CID |
| **File attachments** | ✅ Full support | Upload then pass `attachment_ids` |
| **Tables** | ✅ No extra work | Pure HTML in `body_html` |
| **Hyperlinks** | ✅ No extra work | `<a href="...">` in `body_html` |
| **Emoji** | ✅ No extra work | Unicode in `body_html` or `subject` |
| **Text formatting** | ✅ No extra work | Inline styles in `body_html` |
| **Signature** | ✅ Via API | FE appends to `body_html` (see §15) |

---

## 10. Folders

### List IMAP folders for an account
```
GET /api/lugal/email/accounts/<account_id>/folders
```
**Response:**
```json
{
  "success": true,
  "data": {
    "folders": [
      { "id": "INBOX", "name": "Inbox", "path": "INBOX", "special": "inbox" },
      { "id": "Sent",  "name": "Sent",  "path": "Sent",  "special": "sent" },
      { "id": "Drafts","name": "Drafts","path": "Drafts","special": "drafts" },
      { "id": "Trash", "name": "Trash", "path": "Trash", "special": "trash" },
      { "id": "Work",  "name": "Work",  "path": "Work",  "special": null }
    ]
  }
}
```
`special` is one of `inbox`, `sent`, `drafts`, `trash`, `spam`, `archive`, or `null` for user-created folders.

### Move message to folder
```
POST /api/lugal/email/messages/<id>/move
```
**Body:**
```json
{ "folder": "Work" }
```
Uses the `path` value returned by the folders endpoint. Also accepts the special aliases: `inbox`, `sent`, `drafts`, `trash`, `spam`, `archive`.

---

## 11. Inbox Rules

Rules run automatically on every incoming message. They can mark messages read, star them, move them, or forward them.

### List rules
```
GET /api/lugal/email/rules
```

### Create rule
```
POST /api/lugal/email/rules
```
**Body:**
```json
{
  "name": "Star newsletters",
  "account_id": 1,
  "is_active": true,
  "sequence": 10,
  "match_mode": "all",
  "conditions": [
    { "field": "from", "op": "contains", "value": "newsletter" }
  ],
  "actions": [
    { "action": "star" }
  ],
  "stop_processing": false
}
```

**Condition fields:** `from`, `to`, `subject`, `body`  
**Condition operators:** `contains`, `not_contains`, `equals`, `starts_with`, `ends_with`  
**Action types:**
- `{ "action": "mark_read" }`
- `{ "action": "star" }`
- `{ "action": "move", "folder": "Work" }`
- `{ "action": "forward", "to": "manager@example.com" }`
- `{ "action": "mark_important" }`
- `{ "action": "trash" }`

### Get rule
```
GET /api/lugal/email/rules/<id>
```

### Update rule
```
PUT /api/lugal/email/rules/<id>
```

### Delete rule
```
DELETE /api/lugal/email/rules/<id>
```

### Dry-run / test rule against a message
```
POST /api/lugal/email/rules/<id>/test
```
**Body:** `{ "message_id": 99 }`  
Returns `{ "matches": true, "actions_that_would_run": [...] }` without actually applying the rule.

---

## 12. Quick Steps

Quick Steps are named bundles of actions the user can apply to any message with one click (e.g. "Move to Archive + Mark Read").

### List
```
GET /api/lugal/email/quick_steps
```

### Create
```
POST /api/lugal/email/quick_steps
```
**Body:**
```json
{
  "name": "Archive & Read",
  "description": "Marks read and archives",
  "icon": "archive",
  "sequence": 1,
  "steps": [
    { "action": "mark_read" },
    { "action": "move", "folder": "Archive" }
  ]
}
```

### Get
```
GET /api/lugal/email/quick_steps/<id>
```

### Update
```
PUT /api/lugal/email/quick_steps/<id>
```

### Delete
```
DELETE /api/lugal/email/quick_steps/<id>
```

### Apply quick step to a message
```
POST /api/lugal/email/messages/<id>/apply_quick_step
```
**Body:** `{ "quick_step_id": 3 }`

---

## 13. Sender Resolve

Look up contact information for an email sender (phone, social profiles) from CRM data.

```
GET /api/lugal/email/senders/resolve?email=alice@example.com
```
**Response:**
```json
{
  "success": true,
  "data": {
    "email": "alice@example.com",
    "name": "Alice Smith",
    "phone": "+966 50 123 4567",
    "mobile": "+966 55 987 6543",
    "job_title": "Sales Manager",
    "company": "Acme Corp",
    "avatar_url": "/web/image/res.partner/5/image_128",
    "crm_partner_id": 5
  }
}
```
Returns `null` data fields if no CRM contact is found for that email address.

---

## 14. Related Messages

### All messages from the same sender
```
GET /api/lugal/email/messages/<id>/related?type=sender
GET /api/lugal/email/messages/<id>/related?type=sender&scope=all&limit=100&offset=0
```

### All messages in the same conversation / thread (by subject)
```
GET /api/lugal/email/messages/<id>/related?type=conversation
GET /api/lugal/email/messages/<id>/related?type=conversation&scope=all&limit=100&offset=0
```

**Query params:**

| Param | Default | Description |
|---|---|---|
| `type` | required | `sender` or `conversation` |
| `scope` | `account` | `account` = same account only, `all` = all accounts |
| `limit` | `50` | Max results |
| `offset` | `0` | Pagination |

**Response:**
```json
{
  "success": true,
  "data": {
    "type": "sender",
    "reference_message_id": 2285,
    "messages": [ /* Message Objects */ ],
    "total": 14
  }
}
```

---

## 15. Email Signature

### Get current user's signature
```
GET /api/lugal/email/signature
```
**Response:** `{ "success": true, "data": { "signature": "<p>Best, John</p>" } }`

### Update signature
```
PATCH /api/lugal/email/signature
```
**Body:** `{ "signature": "<p>Best regards,<br>John</p>" }` (HTML string, max 10,000 chars)  
Pass `null` to clear the signature.

**Integration note:** The signature is stored per-user. The FE should fetch it on compose-mount and append it to `body_html` in the editor. The backend does NOT auto-append — FE controls the compose experience.

---

## 16. CRM Email Layer

These endpoints return emails in the context of a specific CRM customer or across all customers.

### Customer's email history
```
GET /api/crm/email/customer/<customer_id>/messages
```
**Query params:** `limit`, `offset`, `folder`, `search`

### Customer email thread
```
GET /api/crm/email/customer/<customer_id>/thread
```

### CRM inbox (all customers)
```
GET /api/crm/email/messages/list
```
**Query params:** `limit`, `offset`, `folder`, `search`, `customer_id`, `is_read`  
Results ordered: newest first.

### CRM message detail
```
GET /api/crm/email/messages/<id>
```

### Apply template
```
POST /api/crm/email/templates/<id>/apply
```
**Body:** `{ "message_id": 99 }` or `{ "customer_id": 5 }`

### Bulk mark read
```
POST /api/crm/email/bulk/read
```
**Body:** `{ "message_ids": [1, 2, 3, ..., 100] }` — supports large arrays (e.g. "Mark all read").

### Bulk trash
```
POST /api/crm/email/bulk/trash
```
**Body:** `{ "message_ids": [1, 2, 3] }`

### CRM bulk delete
```
POST /api/crm/email/messages/bulk_delete
```
**Body:** `{ "message_ids": [1, 2, 3] }`

### Subscribe to customer email updates (WebSocket)
```
POST /api/crm/email/subscribe
```
**Body:** `{ "customer_id": 5 }` — subscribes the current user to real-time updates for that customer's emails.

### CRM email stats
```
GET /api/crm/email/stats
```
Returns unread counts, message totals, and recent activity summary.

---

## 17. Real-time WebSocket Events

Connect to the WebSocket bus. Email events arrive on the user's personal channel.

**Channel:** `supply_user.<your_user_id>`

### New email notification
```json
{
  "type": "new_email",
  "payload": {
    "message_id": 99,
    "account_id": 1,
    "subject": "Hello",
    "from_name": "Alice",
    "from_address": "alice@example.com",
    "folder": "inbox",
    "date": "2026-05-05T10:00:00+03:00",
    "is_read": false,
    "is_important": false,
    "is_mentioned": false,
    "has_attachments": false
  }
}
```
On receiving this event, refresh the inbox message list and increment unread count. Do **not** call `GET /api/lugal/email/messages/<id>` automatically — that endpoint no longer marks messages as read.

### Sync status update
```json
{
  "type": "email_sync_status",
  "payload": { "account_id": 1, "status": "success" }
}
```

---

## 18. Message Object Reference

Every message endpoint returns this structure (abbreviated fields marked with `*` only in list view):

```json
{
  "id": 99,
  "account_id": 1,
  "folder": "inbox",
  "subject": "Hello",
  "from_name": "Alice Smith",
  "from_address": "alice@example.com",
  "to_addresses": [{ "name": "John", "email": "john@example.com" }],
  "cc_addresses": [],
  "bcc_addresses": [],
  "date": "2026-05-05T10:00:00+03:00",
  "is_read": false,
  "is_starred": false,
  "is_flagged": false,
  "is_important": false,
  "is_draft": false,
  "is_mentioned": true,
  "message_size": 14523,
  "smtp_delivered": null,
  "smtp_error": null,
  "smtp_status": "pending",
  "thread_id": "<thread-id@domain>",
  "in_reply_to": "<orig-id@domain>",
  "has_attachments": true,
  "attachment_count": 2,
  "crm_links": {
    "customer": { "id": 5, "name": "Acme Corp" },
    "ticket": null
  },

  // Only in full detail responses (GET /messages/<id>, bulk details, thread):
  "body_html": "<p>Hi</p>",
  "body_text": "Hi",
  "body_fetched": true,
  "attachments": [
    {
      "id": 42,
      "name": "invoice.pdf",
      "mimetype": "application/pdf",
      "size": 102400,
      "url": "/web/content/42?access_token=..."
    }
  ]
}
```

**Field notes:**
- `is_mentioned` — `true` when you are in the `To:` header (not just CC). Use this to power the "Mentioned Mail" filter.
- `is_starred` and `is_flagged` are **independent** — setting one does not affect the other.
- `has_attachments` / `attachment_count` are always present (even in list view) so you can show the paperclip icon without fetching the full message.
- Inline images are **never** included in `attachments[]` — only downloadable file attachments appear there.
- `message_size` is the approximate RFC-822 size in bytes.

---

## 19. Error Reference

All errors follow:
```json
{ "success": false, "error": "Human-readable error message" }
```

| HTTP Status | Meaning |
|---|---|
| `400` | Bad request (missing required field, validation failure) |
| `401` | Missing or invalid JWT token |
| `403` | Action not permitted for the current user |
| `404` | Message / account / resource not found |
| `500` | Server-side error (check logs) |

---

## Quick Cheat Sheet — New Features Added (May 2026)

| Feature | Endpoint / Field | Notes |
|---|---|---|
| Inline image upload | `POST /attachments/upload` with `inline: true` | Returns `cid` to embed in HTML |
| Inline image in MIME | Automatic | Backend builds `multipart/related` |
| Inline images excluded from attachment list | Automatic | Never appear in `attachments[]` |
| Read receipt | `"request_read_receipt": true` in any send body | Adds `Disposition-Notification-To` header |
| High importance | `"importance": "high"` in any send body | Sets Outlook/Mail priority flags |
| `is_mentioned` field | On every message | True when you are in To: |
| `message_size` field | On every message | RFC-822 bytes |
| `has_attachments` + `attachment_count` | On every message (list + detail) | Show paperclip without full fetch |
| Folder list | `GET /accounts/<id>/folders` | All IMAP folders incl. custom |
| Move to folder | `POST /messages/<id>/move` | Works with any IMAP folder path |
| Inbox rules CRUD | `GET/POST/PUT/DELETE /rules` | Auto-runs on ingest |
| Rule dry-run | `POST /rules/<id>/test` | Non-destructive test |
| Quick Steps CRUD | `GET/POST/PUT/DELETE /quick_steps` | Named action bundles |
| Apply quick step | `POST /messages/<id>/apply_quick_step` | One-click multi-action |
| Sender resolve | `GET /senders/resolve?email=...` | Phone/social from CRM |
| Related by sender | `GET /messages/<id>/related?type=sender` | All mail from same sender |
| Related by thread | `GET /messages/<id>/related?type=conversation` | All mail same subject |
| Signature API | `GET/PATCH /signature` | Per-user HTML signature |
| Reply All prefill | `GET /messages/<id>/reply_all` | Returns to/cc pre-filled |
| Thread view | `GET /messages/<id>/thread` | Full ordered email chain |
| Bulk mark read (large) | `POST /crm/email/bulk/read` | Accepts 100+ IDs at once |
| No auto-mark-read on GET | Automatic | Must call `/read` explicitly |
| is_starred ≠ is_flagged | Automatic | Fully decoupled fields |
