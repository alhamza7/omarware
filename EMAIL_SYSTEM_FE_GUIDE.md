# Email & Messaging System — Complete Frontend Integration Guide

> **Audience:** Frontend developers integrating the Lugal CRM email system.  
> **Covers:** Architecture, authentication, account linking, every API endpoint, state management, workflows, and edge cases.

---

## Table of Contents

1. [System Architecture Overview](#1-system-architecture-overview)
2. [Two API Layers — What They Are and Why Both Exist](#2-two-api-layers)
3. [Authentication — How User Login Connects to Email](#3-authentication)
4. [Email Accounts — What They Are and How to Manage Them](#4-email-accounts)
5. [CRM Accounts vs Email Accounts — The Link Explained](#5-crm-accounts-vs-email-accounts)
6. [Complete API Reference — `/api/lugal/email`](#6-lugal-email-api)
7. [Complete API Reference — `/api/crm/email`](#7-crm-email-api)
8. [Complete API Reference — `/api/crm/settings/email`](#8-settings-email-api)
9. [Message Templates API](#9-templates-api)
10. [Frontend Architecture — What Screens to Build](#10-frontend-architecture)
11. [State Management Design](#11-state-management)
12. [Full User Workflow — Step by Step](#12-full-user-workflow)
13. [Common Patterns and Code Examples](#13-code-examples)
14. [Error Handling Reference](#14-error-handling)

---

## 1. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React/Vue)                         │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  Inbox Screen│  │Customer 360° │  │   Settings / Accounts    │  │
│  │  (personal   │  │  (email tab) │  │   (IMAP/SMTP config)     │  │
│  │   mailbox)   │  │              │  │                          │  │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬─────────────┘  │
│         │                 │                        │                │
└─────────┼─────────────────┼────────────────────────┼────────────────┘
          │                 │                        │
          ▼                 ▼                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         ODOO BACKEND                                │
│                                                                     │
│  ┌──────────────────────────┐   ┌────────────────────────────────┐  │
│  │   /api/lugal/email/*     │   │      /api/crm/email/*          │  │
│  │                          │   │                                │  │
│  │  Low-level IMAP/SMTP     │   │  CRM-context wrappers:         │  │
│  │  engine. Handles:        │   │  - Link emails to customers    │  │
│  │  - Account CRUD          │   │  - Link emails to tickets      │  │
│  │  - IMAP sync             │   │  - Log interactions timeline   │  │
│  │  - SMTP send             │   │  - Reply/Forward CRM-aware     │  │
│  │  - Message storage       │   │  - Bulk actions                │  │
│  │  - Notifications         │   │  - Stats per customer          │  │
│  └──────────┬───────────────┘   └──────────────┬─────────────────┘  │
│             │                                  │                    │
│  ┌──────────▼──────────────────────────────────▼─────────────────┐  │
│  │                    lugal.email.message                        │  │
│  │          (database table: all stored emails)                  │  │
│  │                                                               │  │
│  │   linked_customer_id ──────────► lugal.crm.customer          │  │
│  │   linked_ticket_id   ──────────► lugal.crm.ticket            │  │
│  │   account_id         ──────────► lugal.email.account         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              /api/crm/settings/email/*                       │   │
│  │     (User-facing settings: add/edit/delete accounts)         │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
          │                 │
          ▼                 ▼
   Gmail IMAP          Gmail SMTP
   (fetch new)         (send out)
```

---

## 2. Two API Layers

The system is deliberately split into **two layers**. Understanding this split is critical.

### Layer 1 — `/api/lugal/email/` (The Engine)

- **What it is:** Pure email management. Works completely independently of CRM.
- **What it does:** IMAP sync, SMTP send, folder management, account CRUD.
- **Who uses it:** Any module that needs email (CRM, supply, billing, etc.)
- **Auth type:** JWT Bearer token (HTTP endpoints — not JSON-RPC)

### Layer 2 — `/api/crm/email/` (CRM Wrappers)

- **What it is:** CRM-specific email operations built **on top of** Layer 1.
- **What it adds:** Customer linking, ticket linking, interaction timeline logging.
- **Who uses it:** The CRM frontend only.
- **Auth type:** JWT Bearer token (JSON-RPC `type='jsonrpc'` — body must be `{"jsonrpc":"2.0","method":"call","params":{...}}`)

### Layer 3 — `/api/crm/settings/email/` (Settings UI)

- **What it is:** User-facing account configuration (JSON-RPC).
- **What it does:** CRUD for IMAP/SMTP account settings.
- **When to use:** The Settings screen where users configure their mailbox.

### ⚠️ CRITICAL: Request Format Difference

```javascript
// Layer 1 (/api/lugal/email/) — plain HTTP/JSON
fetch('/api/lugal/email/accounts', {
  method: 'GET',
  headers: { 'Authorization': `Bearer ${token}` }
})

// Layer 2 (/api/crm/email/) — JSON-RPC envelope
fetch('/api/crm/email/messages/list', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    jsonrpc: '2.0',
    method: 'call',
    id: 1,
    params: {
      folder: 'inbox',
      page: 1,
      per_page: 30
    }
  })
})
```

---

## 3. Authentication

### Login Flow

Every API call requires a JWT access token. Get it at login:

```http
POST /lugal/auth/login
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "username": "agent@company.com",
    "password": "password123",
    "db": "lugal_local"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "user_id": 24,
      "username": "agent@company.com",
      "name": "Ahmed Al-Rashid"
    }
  }
}
```

### Token Usage

```javascript
// Store both tokens on login
localStorage.setItem('access_token', data.access_token)
localStorage.setItem('refresh_token', data.refresh_token)

// Use on every request
headers: { 'Authorization': `Bearer ${access_token}` }
```

### Token Refresh

```http
POST /lugal/auth/refresh
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "refresh_token": "eyJ..."
  }
}
```

**How JWT connects to email:**  
The JWT token contains `user_id`. Every email API endpoint extracts this user ID internally and scopes all results to **that user's email accounts only**. A user can never see another user's emails.

---

## 4. Email Accounts

### What Is an Email Account?

A `lugal.email.account` is the user's **personal IMAP/SMTP mailbox configuration**. Think of it as "connecting Gmail/Outlook to the app."

```
res.users (Odoo user — one per employee)
    │
    │ has many
    ▼
lugal.email.account (one per mailbox — Gmail, Outlook, etc.)
    │
    │ owns many
    ▼
lugal.email.message (every email ever synced or sent)
```

### Key Properties

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique account ID |
| `name` | str | Friendly label (e.g., "Work Email") |
| `email_address` | str | The actual email address |
| `display_name` | str | Sender name shown on outgoing emails |
| `imap_host` | str | Incoming mail server |
| `imap_port` | int | Usually 993 (SSL) |
| `imap_use_ssl` | bool | Always true for modern providers |
| `smtp_host` | str | Outgoing mail server |
| `smtp_port` | int | Usually 587 (TLS) |
| `smtp_use_tls` | bool | Always true for modern providers |
| `username` | str | Login username for IMAP/SMTP |
| `is_active` | bool | Whether syncing is enabled |
| `is_default` | bool | Which account is used for composing |
| `sync_status` | str | `ok` \| `error` \| `never` |
| `last_sync_date` | ISO | When inbox was last synced |
| `unread_count` | int | Unread messages in inbox |

> **Note:** `password` is never returned in any API response. It is write-only.

### Common Providers Quick Reference

| Provider | IMAP Host | IMAP Port | SMTP Host | SMTP Port |
|----------|-----------|-----------|-----------|-----------|
| Gmail | `imap.gmail.com` | `993` | `smtp.gmail.com` | `587` |
| Outlook | `outlook.office365.com` | `993` | `smtp.office365.com` | `587` |
| Yahoo | `imap.mail.yahoo.com` | `993` | `smtp.mail.yahoo.com` | `587` |
| Custom | `mail.domain.com` | `993` | `mail.domain.com` | `587` |

> **Gmail Warning:** Gmail requires an **App Password**, not the regular account password.  
> Users must enable 2FA → go to Google Account → Security → App Passwords → generate one.

---

## 5. CRM Accounts vs Email Accounts

This is the most important conceptual distinction.

```
┌──────────────────────────────────────────────────────────┐
│  res.users  (System user = one human = one login)        │
│  ─────────────────────────────────────────────────────   │
│  id: 24                                                  │
│  name: "Ahmed Al-Rashid"                                 │
│  login: "ahmed@company.com"                              │
└────────────┬─────────────────────────────────────────────┘
             │
             │ 1-to-many
             ▼
┌──────────────────────────────────────────────────────────┐
│  lugal.email.account  (The actual mailbox config)        │
│  ─────────────────────────────────────────────────────   │
│  id: 3                                                   │
│  name: "Work Gmail"                                      │
│  email_address: "ahmed@company.com"                      │
│  imap_host: "imap.gmail.com"  ← credentials             │
│  smtp_host: "smtp.gmail.com"                             │
│  is_default: true                                        │
└────────────┬─────────────────────────────────────────────┘
             │
             │ 1-to-many
             ▼
┌──────────────────────────────────────────────────────────┐
│  lugal.email.message  (Every email stored)               │
│  ─────────────────────────────────────────────────────   │
│  id: 1001                                                │
│  subject: "Order #4521 Inquiry"                          │
│  from_address: "customer@gmail.com"                      │
│  folder: "inbox"                                         │
│  is_read: false                                          │
│  linked_customer_id: 42  ──────►  lugal.crm.customer     │
│  linked_ticket_id: 7     ──────►  lugal.crm.ticket       │
└──────────────────────────────────────────────────────────┘
```

### The Link: How an Email Gets Connected to a CRM Customer

There are **three ways** an email becomes linked to a CRM customer:

#### Method A — Automatic (Auto-Link Hook)
When a new email arrives and the sender's email address matches a `lugal.crm.customer.email`, it is automatically linked. **No action needed from frontend.**

#### Method B — Manual Link via API
The agent reads an email and manually links it to a customer:
```http
POST /api/crm/email/messages/42/link
{ "model": "lugal.crm.customer", "record_id": 99 }
```

#### Method C — At Send Time
When composing an email, pass `customer_id` and/or `ticket_id`:
```json
{
  "to": ["customer@gmail.com"],
  "subject": "Your order",
  "body_text": "Hello",
  "customer_id": 42,
  "ticket_id": 7
}
```

---

## 6. Lugal Email API (`/api/lugal/email/`)

> **Request format:** Standard HTTP. Use `Authorization: Bearer <token>` header.  
> **Response format:** `{ "success": true/false, "data": {...} }` or `{ "success": false, "error": "..." }`

---

### 6.1 Account Management

#### List All Accounts
```http
GET /api/lugal/email/accounts
Authorization: Bearer <token>
```
Returns all email accounts for the current user.

#### Create Account
```http
POST /api/lugal/email/accounts
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Work Gmail",
  "email_address": "ahmed@company.com",
  "display_name_field": "Ahmed Al-Rashid",
  "username": "ahmed@company.com",
  "password": "app_password",
  "imap_host": "imap.gmail.com",
  "imap_port": 993,
  "imap_use_ssl": true,
  "smtp_host": "smtp.gmail.com",
  "smtp_port": 587,
  "smtp_use_tls": true,
  "is_default": true
}
```

#### Update Account
```http
PATCH /api/lugal/email/accounts/<id>
Authorization: Bearer <token>
Content-Type: application/json

{ "name": "Personal Email", "is_active": false }
```
Partial update — only send changed fields.

#### Delete Account
```http
DELETE /api/lugal/email/accounts/<id>
Authorization: Bearer <token>
```

#### Test IMAP Connection
```http
POST /api/lugal/email/accounts/<id>/test
Authorization: Bearer <token>
```

#### Trigger Sync
```http
POST /api/lugal/email/accounts/<id>/sync
Authorization: Bearer <token>
```

#### Set Default
```http
POST /api/lugal/email/accounts/<id>/set_default
Authorization: Bearer <token>
```

---

### 6.2 Message List & Search

#### List Messages
```http
GET /api/lugal/email/messages
Authorization: Bearer <token>

Query params:
  account_id=<id>       (optional — filter to one account)
  folder=inbox          (inbox|sent|drafts|trash|archive|spam)
  limit=50
  offset=0
  query=invoice         (search subject + body)
  starred=1
  linked_model=lugal.crm.customer
  linked_id=42
```

#### Get Message Detail
```http
GET /api/lugal/email/messages/<id>
Authorization: Bearer <token>
```
Automatically marks the message as read.

#### Notifications (Unread Counts + Delivery Status)
```http
GET /api/lugal/email/notifications
Authorization: Bearer <token>
```
**Response:**
```json
{
  "success": true,
  "data": {
    "inbox": 5,
    "total": 5,
    "per_folder": { "inbox": 5, "sent": 0, "drafts": 2 },
    "account_configured": true,
    "accounts": [
      { "id": 1, "name": "Work Gmail", "unread_count": 5, "sync_status": "ok" }
    ],
    "sync_status": "ok",
    "last_sync_date": "2026-04-11T10:00:00",
    "recently_sent": [
      {
        "id": 42,
        "subject": "Your order",
        "date": "2026-04-21T10:00:00",
        "to_addresses": "[{\"email\": \"customer@example.com\"}]",
        "smtp_delivered": true,
        "smtp_error": null
      }
    ]
  }
}
```

> **`smtp_delivered`** means the SMTP server accepted the message for delivery.  
> It does **NOT** mean the recipient has opened or read it (there is no read-receipt feature).  
> Poll this endpoint every **10–30 seconds** for unread badge updates and delivery confirmations.  
> **Do NOT poll every 1 second** — it is wasteful and provides no benefit.

---

### 6.3 Compose Actions

#### Send New Email
```http
POST /api/lugal/email/send
Authorization: Bearer <token>
Content-Type: application/json

{
  "to": ["customer@gmail.com"],
  "subject": "Your order",
  "body_html": "<p>Hello</p>",
  "body_text": "Hello",
  "cc": ["manager@company.com"],
  "bcc": [],
  "account_id": 1,
  "attachment_ids": []
}
```
> `to` accepts **string** `"a@b.com"`, **list of strings** `["a@b.com"]`, or **list of objects** `[{"email": "a@b.com"}]`  
> `body` is accepted as alias for `body_text`

**Success Response (`201`):**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "subject": "Your order",
    "smtp_delivered": true,
    "smtp_error": null,
    ...
  }
}
```
> **`smtp_delivered: true`** → SMTP server accepted the message (it will be delivered to the recipient's mailbox).  
> **`smtp_delivered: false`** with `smtp_error` → SMTP delivery failed (check `smtp_error` string for details).

**Error Response (`422`) — recipient does not exist:**
```json
{
  "success": false,
  "code": "recipient_not_found",
  "error": "Recipient(s) not found or rejected: unknown@bad.com: Mailbox not found (code 550)"
}
```

#### Reply
```http
POST /api/lugal/email/messages/<id>/reply
Authorization: Bearer <token>
Content-Type: application/json

{
  "body_html": "<p>Thank you</p>",
  "body_text": "Thank you"
}
```
`to`, `subject`, and `In-Reply-To` are automatically inferred from the original message.

#### Forward
```http
POST /api/lugal/email/messages/<id>/forward
Authorization: Bearer <token>
Content-Type: application/json

{
  "to": ["manager@company.com"],
  "body_html": "<p>Please see below</p>"
}
```
Attachments from the original are automatically included.

---

### 6.4 Status Actions

#### Toggle Read
```http
POST /api/lugal/email/messages/<id>/read
Content-Type: application/json
{ "is_read": true }
```

> **When to call this:**  
> - Call it when the user opens an **inbox** message that has `is_read: false`.  
> - `GET /api/lugal/email/messages/<id>` (message detail) **automatically** marks the message as read — you do NOT need to call `/read` separately after a detail fetch.  
> - **Do NOT call `/read` on sent messages** — they are always `is_read: true` by design.  
> - `is_read` is a **per-user, local flag**. It does not notify the sender that the recipient has read the email. There is no cross-user read-receipt system.

#### Toggle Star
```http
POST /api/lugal/email/messages/<id>/star
```

#### Delete (Move to Trash)
```http
DELETE /api/lugal/email/messages/<id>
```

#### Restore from Trash
```http
POST /api/lugal/email/messages/<id>/restore
```

#### Archive
```http
POST /api/lugal/email/messages/<id>/archive
```

---

### 6.5 Record Linking

#### Link to Any Odoo Record
```http
POST /api/lugal/email/messages/<id>/link
Content-Type: application/json

{
  "model": "lugal.crm.customer",
  "record_id": 42,
  "record_name": "Acme Corp"
}
```
Allowed models: `lugal.crm.customer`, `lugal.crm.ticket`, `lugal.crm.interaction`

#### Unlink
```http
POST /api/lugal/email/messages/<id>/unlink
```

---

## 7. CRM Email API (`/api/crm/email/`)

> **Request format:** JSON-RPC. ALL requests use `POST` with the JSON-RPC envelope.  
> **Response:** `{ "jsonrpc": "2.0", "result": { "success": true, "data": {...} } }`

```javascript
// Every CRM email call looks like this:
const call = (endpoint, params = {}) => fetch(endpoint, {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params })
}).then(r => r.json()).then(r => r.result)
```

---

### 7.1 Customer-Scoped Inbox

#### All Emails for One Customer
```javascript
call('/api/crm/email/customer/42/messages', {
  folder: 'inbox',  // optional
  page: 1,
  per_page: 30
})
```
**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 42,
    "customer_name": "Acme Corp",
    "total": 15,
    "page": 1,
    "per_page": 30,
    "items": [ { ...email_object... } ]
  }
}
```

#### Thread View (Grouped by Subject)
```javascript
call('/api/crm/email/customer/42/thread', {
  subject_contains: 'order'  // optional
})
```
**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 42,
    "total_threads": 3,
    "threads": [
      {
        "subject": "Invoice #1234",
        "count": 4,
        "messages": [ {...}, {...}, {...}, {...} ]
      }
    ]
  }
}
```

---

### 7.2 User's Personal CRM Inbox

```javascript
call('/api/crm/email/messages/list', {
  folder: 'inbox',
  page: 1,
  per_page: 30,
  customer_id: 42,   // optional filter
  ticket_id: 7,      // optional filter
  is_read: false     // optional filter
})
```

---

### 7.3 Message Detail

```javascript
call('/api/crm/email/messages/1001', {
  preview: false   // true = view without marking as read
})
```
**Response includes:** full `body_html`, `attachments[]`, `crm_links`

**Message object shape:**
```json
{
  "id": 1001,
  "account_id": 1,
  "folder": "inbox",
  "subject": "Order Inquiry",
  "from_name": "Customer Name",
  "from_address": "customer@gmail.com",
  "to_addresses": "[{\"email\":\"agent@company.com\"}]",
  "date": "2026-04-11T08:30:00",
  "is_read": false,
  "is_starred": false,
  "body_html": "<p>...</p>",
  "body_text": "...",
  "attachments": [],
  "crm_links": {
    "customer": { "id": 42, "name": "Acme Corp" },
    "ticket": null
  }
}
```

---

### 7.4 Send / Reply / Forward (CRM-Aware)

All three automatically log a `lugal.crm.interaction` entry in the customer timeline.

#### Send
```javascript
call('/api/crm/email/send', {
  account_id: 1,
  to_addresses: [{ name: 'Customer', email: 'customer@gmail.com' }],
  subject: 'Your order update',
  body_html: '<p>Hello</p>',
  body_text: 'Hello',
  customer_id: 42,    // links + logs interaction
  ticket_id: 7        // optional additional link
})
```

#### Reply (CRM-Aware)
```javascript
call('/api/crm/email/messages/1001/reply', {
  body_html: '<p>Thank you for reaching out...</p>',
  body_text: 'Thank you for reaching out...',
  customer_id: 42   // auto-inherited from original if not set
})
```

#### Forward (CRM-Aware)
```javascript
call('/api/crm/email/messages/1001/forward', {
  to_addresses: [{ name: 'Manager', email: 'mgr@company.com' }],
  body_html: '<p>FYI</p>'
})
```

---

### 7.5 Bulk Actions

#### Mark Multiple as Read
```javascript
call('/api/crm/email/messages/bulk_read', {
  message_ids: [101, 102, 103, 104],
  is_read: true
})
// Response: { "updated": 4, "is_read": true }
```

#### Move Multiple to Trash
```javascript
call('/api/crm/email/messages/bulk_delete', {
  message_ids: [101, 102, 103]
})
// Response: { "deleted": 3 }
```

---

### 7.6 Advanced Search

```javascript
call('/api/crm/email/messages/search', {
  query: 'invoice',
  folder: 'inbox',
  date_from: '2026-01-01',
  date_to: '2026-04-11',
  from_address: '@gmail.com',
  customer_id: 42,
  is_read: false,
  is_starred: null,
  page: 1,
  per_page: 30
})
```
Max `per_page` = 100.

---

### 7.7 Stats

```javascript
call('/api/crm/email/stats', {
  customer_id: 42   // optional
})
```
**Response:**
```json
{
  "success": true,
  "data": {
    "total_unread": 12,
    "by_folder": { "inbox": 10, "drafts": 2 },
    "accounts": [
      { "id": 1, "name": "Work Gmail", "unread_count": 12, "sync_status": "ok" }
    ],
    "customer": {
      "id": 42,
      "name": "Acme Corp",
      "total": 25,
      "unread": 3
    }
  }
}
```

---

### 7.8 Linking

```javascript
// Link email to customer
call('/api/crm/email/messages/1001/link', {
  model: 'lugal.crm.customer',
  record_id: 42,
  record_name: 'Acme Corp'  // optional
})

// Link to ticket
call('/api/crm/email/messages/1001/link', {
  model: 'lugal.crm.ticket',
  record_id: 7
})

// Remove all links
call('/api/crm/email/messages/1001/unlink', {})
```

---

## 8. Settings Email API (`/api/crm/settings/email/`)

> Format: JSON-RPC (same as CRM email)

### List Accounts
```javascript
call('/api/crm/settings/email/accounts', {})
```

### Add Account
```javascript
call('/api/crm/settings/email/accounts/add', {
  name: 'Work Gmail',
  email_address: 'ahmed@company.com',
  username: 'ahmed@company.com',
  password: 'xxxx xxxx xxxx xxxx',  // Google App Password
  imap_host: 'imap.gmail.com',
  imap_port: 993,
  imap_use_ssl: true,
  smtp_host: 'smtp.gmail.com',
  smtp_port: 587,
  smtp_use_tls: true,
  display_name: 'Ahmed Al-Rashid',
  is_default: true
})
```

### Update Account (Partial)
```javascript
call('/api/crm/settings/email/accounts/3/update', {
  name: 'Personal Email',
  is_active: false
})
```

### Delete Account
```javascript
call('/api/crm/settings/email/accounts/3/delete', {})
```

### Test Connection
```javascript
call('/api/crm/settings/email/accounts/3/test', {})
// Success: { "status": "ok", "message": "Connection successful" }
// Failure: { "success": false, "error": "IMAP connection refused" }
```

### Sync Inbox
```javascript
call('/api/crm/settings/email/accounts/3/sync', {})
// Response: { "sync_status": "ok", "last_sync_date": "...", "unread_count": 8 }
```

### Set Default
```javascript
call('/api/crm/settings/email/accounts/3/set_default', {})
```

---

## 9. Templates API

Message templates are pre-written text that agents can insert when composing emails.

### List Email Templates
```javascript
call('/api/crm/email/templates/list', {
  branch_id: 3,       // optional
  category: 'followup'  // optional
})
```
**Response:**
```json
{
  "total": 5,
  "items": [
    {
      "id": 1,
      "name": "Follow-up Email",
      "name_ar": "رسالة متابعة",
      "channel": "email",
      "category": "followup",
      "body": "Dear {customer_name}, just following up on our last conversation...",
      "body_ar": "عزيزي {customer_name}، نتابع معك...",
      "branch_id": null
    }
  ]
}
```

### Apply Template (Variable Substitution)
```javascript
call('/api/crm/email/templates/1/apply', {
  customer_id: 42   // resolves {customer_name}, {branch_name}
})
```
**Response:**
```json
{
  "template_id": 1,
  "subject": "Follow-up Email",
  "body": "Dear Acme Corp, just following up on our last conversation...",
  "body_ar": "عزيزي Acme Corp، نتابع معك...",
  "channel": "email",
  "variables": {
    "customer_name": "Acme Corp",
    "agent_name": "Ahmed",
    "branch_name": "Baghdad Branch"
  }
}
```

**Supported placeholders:** `{customer_name}`, `{agent_name}`, `{branch_name}`

**FE Usage Pattern:**
```javascript
// 1. User opens compose dialog with customer_id=42
// 2. User clicks "Use Template" 
// 3. FE shows template list filtered by channel='email'
// 4. User selects template id=1
// 5. FE calls apply_template(1, { customer_id: 42 })
// 6. FE populates compose body with the rendered result
```

---

## 10. Frontend Architecture

### Screens to Build

```
App
├── Inbox (Personal Email)
│   ├── Folder sidebar (inbox, sent, drafts, trash, archive)
│   ├── Message list (paginated, filterable)
│   ├── Message detail pane
│   │   ├── Body viewer
│   │   ├── Attachment list
│   │   ├── CRM links (customer / ticket badges)
│   │   └── Actions (reply, forward, link, trash, archive, star)
│   ├── Compose dialog
│   │   ├── To / CC / BCC fields
│   │   ├── Subject
│   │   ├── Rich text body
│   │   ├── Template picker
│   │   └── Account selector (if multiple accounts)
│   └── Search bar (with date, from, folder filters)
│
├── Customer 360° Card  (part of CRM customer profile)
│   └── Email tab
│       ├── Thread view (grouped conversations)
│       ├── Unread badge count
│       ├── Quick compose (pre-fills to=customer email)
│       └── Link/unlink controls
│
├── Settings
│   └── Email Accounts
│       ├── Account list (with sync status badges)
│       ├── Add account form (IMAP/SMTP fields + test button)
│       ├── Edit account form
│       ├── Delete confirmation
│       └── Set default button
│
└── Notification Bar (global)
    └── Email bell icon with unread count badge
```

---

### Component Tree (React Example)

```
<EmailModule>
  <EmailSidebar>          // folder list + unread counts
  <EmailList>             // paginated message list
    <EmailListItem />     // single row
  <EmailDetail>           // message viewer
    <EmailBody />
    <AttachmentList />
    <CrmLinkPanel />      // shows linked customer/ticket
    <EmailActions />      // reply, forward, link, trash, etc.
  <ComposeDialog>         // modal for new / reply / forward
    <TemplatePicker />
    <RichTextEditor />
  <EmailSearchBar />
  <EmailSettingsPage>     // Settings → Email Accounts
    <AccountForm />
    <ConnectionTestButton />
```

---

## 11. State Management

### Recommended Store Structure (Pinia / Zustand)

```typescript
// emailStore.ts
interface EmailState {
  // Accounts
  accounts: EmailAccount[]
  defaultAccountId: number | null
  
  // Inbox
  currentFolder: 'inbox' | 'sent' | 'drafts' | 'trash' | 'archive' | 'spam'
  messages: EmailMessage[]
  selectedMessage: EmailMessage | null
  totalMessages: number
  currentPage: number
  perPage: number
  
  // Filters
  searchQuery: string
  filterCustomerId: number | null
  filterTicketId: number | null
  filterIsRead: boolean | null
  
  // Unread counts
  unreadByFolder: Record<string, number>
  totalUnread: number
  
  // UI state
  isLoading: boolean
  isComposing: boolean
  composeMode: 'new' | 'reply' | 'forward'
  replyToMessage: EmailMessage | null
}

// Actions
loadAccounts()           // GET /api/lugal/email/accounts
loadMessages(params)     // GET /api/lugal/email/messages
loadNotifications()      // GET /api/lugal/email/notifications
sendEmail(payload)       // POST /api/lugal/email/send (personal)
sendCrmEmail(payload)    // POST /api/crm/email/send (with CRM link)
markRead(ids, isRead)    // POST /api/crm/email/messages/bulk_read
deleteMessages(ids)      // POST /api/crm/email/messages/bulk_delete
searchMessages(params)   // POST /api/crm/email/messages/search
```

### Polling for New Mail

The backend syncs IMAP automatically via cron every ~1 minute. The FE should **poll notifications** to update the badge count:

```javascript
// Poll every 60 seconds
useEffect(() => {
  const interval = setInterval(async () => {
    const data = await fetch('/api/lugal/email/notifications', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(r => r.json())
    
    setUnreadCount(data.data.inbox)
  }, 60_000)
  
  return () => clearInterval(interval)
}, [token])
```

---

## 12. Full User Workflow

### Workflow A: First-Time Setup (New Agent)

```
1. Agent logs in → gets JWT token
2. FE calls GET /api/crm/users/me
   → email_accounts: []  (no accounts configured)
3. FE shows "Connect your email" prompt
4. Agent fills the "Add Email Account" form
5. FE calls POST /api/crm/settings/email/accounts/add
6. After creating → FE calls POST /api/crm/settings/email/accounts/<id>/test
   → If "Connection successful" → show green badge
   → If error → show error message with fix hint (App Password for Gmail)
7. FE calls POST /api/crm/settings/email/accounts/<id>/sync
   → First sync fetches last 50 inbox messages
8. FE calls GET /api/lugal/email/messages?folder=inbox
   → Shows inbox
```

### Workflow B: Daily Inbox Use

```
1. Agent opens app → navbar shows unread count (from polling)
2. Agent clicks Inbox → FE loads messages from /api/lugal/email/messages
3. Agent clicks a message
   → FE calls GET /api/lugal/email/messages/<id>
   → Message marked as read automatically
   → If crm_links.customer is set → shows "Linked to: Acme Corp" badge
4. Agent replies
   → FE opens compose dialog pre-filled with Re: subject
   → Agent writes body
   → FE calls POST /api/crm/email/messages/<id>/reply
   → Interaction logged automatically in customer timeline
5. Agent links an unlinked email to a customer
   → FE shows "Link to Customer" button
   → Agent searches and selects customer
   → FE calls POST /api/crm/email/messages/<id>/link
```

### Workflow C: Customer 360° Email Tab

```
1. Agent opens customer profile (customer_id=42)
2. FE calls POST /api/crm/email/customer/42/messages
   → Shows all emails ever sent/received from this customer
3. FE calls POST /api/crm/email/customer/42/thread
   → Shows grouped conversation threads
4. Agent clicks "Send Email to Customer"
   → FE opens compose with to=customer.email pre-filled
   → FE calls POST /api/crm/email/send with customer_id=42
   → Email sent + interaction logged in timeline
5. Agent uses template
   → FE calls POST /api/crm/email/templates/list?channel=email
   → Agent selects template
   → FE calls POST /api/crm/email/templates/1/apply { customer_id: 42 }
   → Body populated with rendered text
```

### Workflow D: Compose with Template

```
1. Agent opens compose dialog
2. Agent clicks "Templates" button
3. FE loads: POST /api/crm/email/templates/list
4. Agent selects "Follow-up Email"
5. If customer is selected:
   → FE calls POST /api/crm/email/templates/1/apply { customer_id: 42 }
   → Rendered body fills the editor
6. If no customer selected:
   → FE calls POST /api/crm/email/templates/1/apply {}
   → {customer_name} shows as empty or placeholder
```

---

## 13. Code Examples

### Axios Helper (recommended pattern)

```typescript
// emailApi.ts
import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8070'

// Layer 1: Plain HTTP (lugal/email)
const http = axios.create({ baseURL: `${BASE}/api/lugal/email` })
http.interceptors.request.use(cfg => {
  cfg.headers.Authorization = `Bearer ${useAuthStore().token}`
  return cfg
})

// Layer 2 & 3: JSON-RPC (crm/email)
const rpc = (url: string, params: object = {}) =>
  axios.post(`${BASE}${url}`, {
    jsonrpc: '2.0', method: 'call', id: Date.now(), params
  }, {
    headers: { Authorization: `Bearer ${useAuthStore().token}` }
  }).then(r => r.data.result)


// ─── Accounts ───────────────────────────────────────────────
export const listAccounts = () => 
  http.get('/accounts').then(r => r.data.data)

export const addAccount = (data: AccountForm) =>
  rpc('/api/crm/settings/email/accounts/add', data)

export const testConnection = (id: number) =>
  rpc(`/api/crm/settings/email/accounts/${id}/test`, {})

export const syncAccount = (id: number) =>
  rpc(`/api/crm/settings/email/accounts/${id}/sync`, {})


// ─── Messages ────────────────────────────────────────────────
export const listMessages = (params: MessageListParams) =>
  http.get('/messages', { params }).then(r => r.data.data)

export const getNotifications = () =>
  http.get('/notifications').then(r => r.data.data)

export const getMessage = (id: number) =>
  http.get(`/messages/${id}`).then(r => r.data.data)


// ─── CRM-scoped ───────────────────────────────────────────────
export const customerMessages = (customerId: number, params = {}) =>
  rpc(`/api/crm/email/customer/${customerId}/messages`, params)

export const customerThread = (customerId: number, subjectContains = '') =>
  rpc(`/api/crm/email/customer/${customerId}/thread`, 
      subjectContains ? { subject_contains: subjectContains } : {})

export const sendCrmEmail = (payload: SendEmailPayload) =>
  rpc('/api/crm/email/send', payload)

export const bulkMarkRead = (ids: number[], isRead = true) =>
  rpc('/api/crm/email/messages/bulk_read', { message_ids: ids, is_read: isRead })

export const emailStats = (customerId?: number) =>
  rpc('/api/crm/email/stats', customerId ? { customer_id: customerId } : {})

export const applyTemplate = (templateId: number, customerId?: number) =>
  rpc(`/api/crm/email/templates/${templateId}/apply`,
      customerId ? { customer_id: customerId } : {})
```

### Compose Dialog Example

```typescript
// ComposeDialog.tsx
const handleSend = async () => {
  if (!subject || !to) return

  const payload = {
    account_id: selectedAccountId || defaultAccountId,
    to_addresses: [{ name: '', email: to }],
    subject,
    body_html: editorHtml,
    body_text: editorText,
    ...(customerId && { customer_id: customerId }),
    ...(ticketId   && { ticket_id:   ticketId   }),
  }

  if (mode === 'reply' && originalMessageId) {
    // Use CRM reply endpoint — logs interaction automatically
    await rpc(`/api/crm/email/messages/${originalMessageId}/reply`, {
      body_html: editorHtml,
      body_text: editorText,
      customer_id: customerId,
    })
  } else {
    // Use CRM send — logs interaction if customer_id provided
    await sendCrmEmail(payload)
  }

  onClose()
  refreshInbox()
}
```

### Unread Badge Component

```typescript
// UnreadBadge.tsx
const UnreadBadge = () => {
  const [count, setCount] = useState(0)
  
  const refresh = async () => {
    const data = await getNotifications()
    setCount(data.inbox)
  }
  
  useEffect(() => {
    refresh()
    const t = setInterval(refresh, 60_000)  // poll every 60s
    return () => clearInterval(t)
  }, [])
  
  return count > 0 ? <span className="badge">{count}</span> : null
}
```

---

## 14. Error Handling Reference

### Standard Error Response Shape

All endpoints return errors in one of two formats:

```json
// JSON-RPC (crm/email endpoints)
{
  "jsonrpc": "2.0",
  "result": {
    "success": false,
    "error": "Unauthorized"
  }
}

// HTTP (lugal/email endpoints)
{
  "success": false,
  "error": "Account not found"
}
```

### Common Errors and How to Handle Them

| Error | Cause | FE Action |
|-------|-------|-----------|
| `"Unauthorized"` | JWT expired or missing | Refresh token, or redirect to login |
| `"No email account configured."` | User has no IMAP account | Show "Connect Email" prompt |
| `"Account not found"` | Wrong account_id or not owned by user | Reload account list |
| `"SMTP send failed: (535, b'5.7.8 Username and Password not accepted...')"` | Gmail App Password not set or wrong | Show help: "Update your Gmail App Password in Settings" |
| `"IMAP connection refused"` | Wrong host/port | Show: "Check your IMAP settings" |
| `"Message not found"` | Message deleted or wrong user | Remove from local list |
| `"model is not an allowed link target"` | Wrong model string in link request | Fix the model name in code |

### Token Refresh Pattern

```typescript
// axiosInterceptor.ts
http.interceptors.response.use(
  r => r,
  async err => {
    if (err.response?.status === 401) {
      const newToken = await refreshToken()
      if (newToken) {
        err.config.headers.Authorization = `Bearer ${newToken}`
        return axios(err.config)
      }
      logout()
    }
    return Promise.reject(err)
  }
)
```

---

## Quick Reference Card

### Which API to Call?

| Task | Endpoint | Format |
|------|----------|--------|
| Read personal inbox | `GET /api/lugal/email/messages?folder=inbox` | HTTP |
| Get unread count badge | `GET /api/lugal/email/notifications` | HTTP |
| Get message detail | `GET /api/lugal/email/messages/<id>` | HTTP |
| Send personal email (no CRM) | `POST /api/lugal/email/send` | HTTP |
| Send email to customer (logs to timeline) | `POST /api/crm/email/send` | JSON-RPC |
| Reply to email (CRM-aware) | `POST /api/crm/email/messages/<id>/reply` | JSON-RPC |
| View customer's email history | `POST /api/crm/email/customer/<id>/messages` | JSON-RPC |
| View customer emails by thread | `POST /api/crm/email/customer/<id>/thread` | JSON-RPC |
| Search across inbox | `POST /api/crm/email/messages/search` | JSON-RPC |
| Bulk mark as read | `POST /api/crm/email/messages/bulk_read` | JSON-RPC |
| Get email stats | `POST /api/crm/email/stats` | JSON-RPC |
| Load email templates | `POST /api/crm/email/templates/list` | JSON-RPC |
| Render template with customer name | `POST /api/crm/email/templates/<id>/apply` | JSON-RPC |
| Add email account (Settings) | `POST /api/crm/settings/email/accounts/add` | JSON-RPC |
| Test IMAP connection | `POST /api/crm/settings/email/accounts/<id>/test` | JSON-RPC |
| Update account settings | `POST /api/crm/settings/email/accounts/<id>/update` | JSON-RPC |
| Set default account | `POST /api/crm/settings/email/accounts/<id>/set_default` | JSON-RPC |
