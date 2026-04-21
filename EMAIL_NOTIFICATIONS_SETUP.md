# Email Notifications — Full Setup Guide

> **For:** Frontend developers  
> **Last updated:** 2026-04-21  
> **Base URL:** `http://<server>/api/lugal/email`  
> **Auth:** Every request requires `Authorization: Bearer <access_token>`

---

## Table of Contents

1. [The One Endpoint That Drives Everything](#1-the-one-endpoint)
2. [What Each Field Means](#2-field-reference)
3. [Correct Polling Loop (JavaScript)](#3-correct-polling-loop)
4. [Browser / OS Notifications](#4-browser-notifications)
5. [Sent Message Delivery Status](#5-delivered-status)
6. [The Read API — When and How](#6-read-api)
7. [Inbox Sync — How It Works](#7-inbox-sync)
8. [Common Mistakes](#8-common-mistakes)
9. [Complete Working Example (React)](#9-react-example)
10. [API Quick Reference](#10-api-quick-reference)

---

## 1. The One Endpoint That Drives Everything

```
GET /api/lugal/email/notifications
```

This single endpoint is the heartbeat of the notification system. Poll it on a timer. It returns:

| What | Where in response |
|------|-------------------|
| Unread badge count | `data.inbox` |
| Per-folder unread counts | `data.per_folder` |
| Latest 10 unread inbox messages (for notification previews) | `data.new_messages[]` |
| Last 20 sent messages with delivery status | `data.recently_sent[]` |
| Timestamp to pass on next poll | `data.checked_at` |

### Optional `?since=` parameter

Pass the `checked_at` value from your last response to get only messages that arrived **after that point**:

```
GET /api/lugal/email/notifications?since=2026-04-21T07:14:12
```

When `since` is supplied, `new_messages[]` contains only messages newer than that timestamp — making it easy to know exactly which messages are brand new without comparing counts.

---

## 2. Field Reference

Full response shape:

```json
{
  "success": true,
  "data": {
    "inbox": 5,
    "total": 5,
    "per_folder": {
      "inbox": 5,
      "sent": 0,
      "drafts": 0,
      "trash": 1,
      "archive": 0,
      "spam": 0
    },
    "account_configured": true,
    "accounts": [
      {
        "id": 26,
        "name": "Syed Naqvi",
        "unread_count": 5,
        "sync_status": "ok",
        "last_sync_date": "2026-04-21T07:13:58"
      }
    ],
    "sync_status": "ok",
    "last_sync_date": "2026-04-21T07:13:58",
    "checked_at": "2026-04-21T07:14:12",
    "new_messages": [
      {
        "id": 376,
        "account_id": 26,
        "account_name": "Syed Naqvi",
        "subject": "Hello from Omar",
        "from_name": "Omar",
        "from_address": "omar@nooralnibras.com",
        "date": "2026-04-21T07:04:07",
        "is_read": false
      }
    ],
    "recently_sent": [
      {
        "id": 375,
        "subject": "Hello from Omar",
        "date": "2026-04-21T07:04:07",
        "to_addresses": "[{\"email\": \"syed.naqvi@nooralnibras.com\"}]",
        "smtp_delivered": true,
        "smtp_error": null
      }
    ]
  }
}
```

### Key field explanations

| Field | Type | What it means |
|-------|------|----------------|
| `inbox` | int | Total unread messages across all accounts — use this for the **badge number** |
| `checked_at` | ISO string | Save this and pass as `?since=` on next poll |
| `new_messages[]` | array | Unread inbox messages (with `?since=` = only new arrivals) — use these for **notification toasts/popups** |
| `new_messages[].is_read` | bool | Always `false` here (these are unread messages) |
| `recently_sent[].smtp_delivered` | bool | `true` = SMTP server accepted the email. `false` = delivery failed |
| `recently_sent[].smtp_error` | string\|null | Error message if delivery failed |
| `accounts[].sync_status` | string | `"ok"` = IMAP working, `"error"` = check IMAP config |
| `accounts[].last_sync_date` | ISO string | When the inbox was last checked for new mail |

> **`smtp_delivered` is NOT a read receipt.** It means the mail server accepted the message.  
> There is no feature to know if the recipient opened the email.

---

## 3. Correct Polling Loop (JavaScript)

```javascript
// emailNotifications.js

const POLL_INTERVAL_MS = 15_000; // 15 seconds — do NOT go below 10s

let checkedAt = null;   // tracks the last poll timestamp for ?since= filtering
let pollTimer  = null;

async function pollNotifications(token) {
  const url = checkedAt
    ? `/api/lugal/email/notifications?since=${encodeURIComponent(checkedAt)}`
    : `/api/lugal/email/notifications`;

  try {
    const res  = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    const json = await res.json();
    if (!json.success) return;

    const data = json.data;

    // 1. Update unread badge
    updateBadge(data.inbox);

    // 2. Trigger notifications for NEW messages
    //    When ?since= is used, new_messages[] only contains messages
    //    that arrived after our last check — these are truly new.
    if (checkedAt && data.new_messages.length > 0) {
      for (const msg of data.new_messages) {
        showNotification(msg);
      }
    }

    // 3. Update delivery ticks on sent messages
    for (const sent of data.recently_sent) {
      updateDeliveryStatus(sent.id, sent.smtp_delivered, sent.smtp_error);
    }

    // 4. Save checked_at for next poll — this is the key to efficient polling
    checkedAt = data.checked_at;

  } catch (err) {
    console.error('Notification poll failed:', err);
  }
}

function startPolling(token) {
  // Fire immediately, then every 15 seconds
  pollNotifications(token);
  pollTimer = setInterval(() => pollNotifications(token), POLL_INTERVAL_MS);
}

function stopPolling() {
  clearInterval(pollTimer);
  pollTimer  = null;
  checkedAt  = null;
}
```

---

## 4. Browser / OS Notifications

The `new_messages[]` array gives you everything needed to display browser notifications:

```javascript
async function showNotification(msg) {
  // Request permission once (on login or account setup)
  if (Notification.permission === 'default') {
    await Notification.requestPermission();
  }
  if (Notification.permission !== 'granted') return;

  const notif = new Notification(
    `New email — ${msg.account_name}`,
    {
      body:    `From: ${msg.from_name || msg.from_address}\n${msg.subject}`,
      icon:    '/email-icon.png',      // your app icon
      tag:     `email-${msg.id}`,      // prevents duplicate toasts for same message
      silent:  false,
    }
  );

  // Click → open the inbox and highlight the message
  notif.onclick = () => {
    window.focus();
    navigateToMessage(msg.account_id, msg.id);
    notif.close();
  };
}
```

### In-app notification toast (no browser permission needed)

```javascript
function showToast(msg) {
  const toast = document.createElement('div');
  toast.className = 'email-toast';
  toast.innerHTML = `
    <strong>📧 New Email</strong>
    <div class="from">${msg.from_name || msg.from_address}</div>
    <div class="subject">${msg.subject}</div>
  `;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}
```

---

## 5. Sent Message Delivery Status

When you call `POST /api/lugal/email/send`, the **immediate response** already contains `smtp_delivered`:

```json
{
  "success": true,
  "data": {
    "id": 375,
    "subject": "Hello",
    "smtp_delivered": true,
    "smtp_error": null,
    ...
  }
}
```

| `smtp_delivered` | `smtp_error` | What happened |
|-----------------|--------------|---------------|
| `true` | `null` | ✅ Delivered — mail server accepted it |
| `true` | non-null | ⚠️ Partially delivered — some recipients rejected |
| `false` | non-null | ❌ Failed — show the error to the user |

### Recipient not found (422 error)

If **all** recipients were rejected (e.g., email address doesn't exist):

```json
{
  "success": false,
  "code": "recipient_not_found",
  "error": "Recipient(s) not found or rejected: unknown@bad.com: Mailbox not found (code 550)"
}
```

The message is **NOT saved** to the sent folder in this case.

### Updating delivery indicators on previously sent messages

The `recently_sent[]` array in the poll response lets you update the ✓/✓✓ ticks on your sent list without re-fetching the whole folder:

```javascript
function updateDeliveryStatus(msgId, delivered, error) {
  // Update your local state / store
  store.dispatch('email/updateSentStatus', { msgId, delivered, error });
  
  // Update the UI tick:
  // - delivered = true  → show ✓✓ (double tick, green)
  // - delivered = false and error → show ✗ (red X with tooltip)
  // - delivered = false and no error → show ✓ (single tick, grey, still sending)
}
```

---

## 6. The Read API — When and How

### Auto-mark on detail view

```
GET /api/lugal/email/messages/<id>
```

Opening a message via this endpoint **automatically marks it as read** (`is_read: true`). You do **not** need to make a separate `/read` call after fetching the detail.

### Manual toggle

```
POST /api/lugal/email/messages/<id>/read
Content-Type: application/json
{ "is_read": true }   // or false to mark as unread
```

**Response:**
```json
{ "success": true, "data": { "is_read": true } }
```

### Rules — when to call this

| Situation | Action |
|-----------|--------|
| User opens an inbox message | Call `GET /messages/<id>` — auto-marks read |
| User clicks "Mark as unread" | `POST /messages/<id>/read` with `{ "is_read": false }` |
| Sent message is viewed | **Do nothing** — sent messages are always `is_read: true` |
| User is on the inbox list (not opening a message) | **Do not call `/read`** |

> `is_read` is a **local, per-user flag**. It does NOT send a notification to the original sender. It has no effect on what the other person sees.

---

## 7. Inbox Sync — How It Works

The backend automatically syncs incoming mail from the IMAP server. Understanding this prevents confusion:

```
┌─────────────────────────────────────────────────────────────┐
│  Timeline of a new email arriving                           │
│                                                             │
│  0s   Sender hits Send                                      │
│  ~1s  SMTP delivers to mail.nooralnibras.com IMAP server    │
│  ...  Email sits on IMAP server                             │
│  ≤60s Cron job syncs INBOX → message appears in DB          │
│  Next The FE's next poll of /notifications shows it         │
│  poll new_messages[] contains the new email                 │
└─────────────────────────────────────────────────────────────┘
```

### How sync is triggered

| Trigger | When | What happens |
|---------|------|--------------|
| `GET /mailbox/inbox` | FE fetches inbox | Sync runs, waits up to 7s, returns fresh data |
| `GET /mailbox/inbox?force_sync=1` | Force a fresh sync | Always syncs even if recent |
| `GET /mailbox/inbox?auto_sync=0` | Skip sync | Returns DB cache only (fastest) |
| Cron job | Every ~1 minute | Syncs all accounts in background |

### Sync timing

- **Throttle:** If the last sync was < 15 seconds ago, the API returns from DB cache immediately (< 100ms)
- **First call after 15s:** Sync runs (typically 1–2 seconds for incremental), then response is returned
- **Maximum wait:** The API will wait up to 7 seconds for sync; if sync takes longer, DB cache is returned

### Recommended FE pattern

```javascript
// On inbox page load or tab switch — always fetch fresh
const inboxResponse = await fetch('/api/lugal/email/mailbox/inbox?folder=inbox&limit=50');

// User manually hits refresh — force a new sync
const refreshResponse = await fetch('/api/lugal/email/mailbox/inbox?folder=inbox&limit=50&force_sync=1');

// Already on the inbox page, just updating the list (e.g., every 30s)
// Use auto_sync=0 if you already triggered the sync via /notifications polling
const silentRefresh = await fetch('/api/lugal/email/mailbox/inbox?folder=inbox&limit=50&auto_sync=0');
```

---

## 8. Common Mistakes

### ❌ Polling too fast

```javascript
// WRONG — 1 second polling hammers the server and provides no benefit
setInterval(() => pollNotifications(token), 1_000);

// CORRECT — 15 seconds is plenty; inbox syncs are throttled to 15s minimum anyway
setInterval(() => pollNotifications(token), 15_000);
```

### ❌ Calling `/read` on sent messages

```javascript
// WRONG — sent messages are already is_read: true; calling this is a no-op at best
if (msg.folder === 'sent') {
  await fetch(`/api/lugal/email/messages/${msg.id}/read`, { method: 'POST' });
}

// CORRECT — skip the read call for sent/draft/trash
if (msg.folder === 'inbox' && !msg.is_read) {
  await fetch(`/api/lugal/email/messages/${msg.id}/read`, { method: 'POST' });
}
```

### ❌ Expecting cross-user read receipts

```javascript
// WRONG assumption — there is no read receipt system
if (sentMsg.is_read === true) {
  showDeliveredByRecipient(); // ← this is NOT what is_read means
}

// CORRECT — use smtp_delivered for delivery confirmation
if (sentMsg.smtp_delivered === true) {
  showDeliveredTick(); // ✓✓ mail server accepted it
}
```

### ❌ Sending `to` as a plain string for a single recipient

```javascript
// This works but is fragile — use array of objects consistently
{ "to": "user@example.com" }

// CORRECT — consistent format the backend handles perfectly
{ "to": [{ "email": "user@example.com" }] }
// or
{ "to": ["user@example.com"] }
```

### ❌ Not using `?since=` on notification polls

```javascript
// Without since=, new_messages[] always returns the latest 10 unread messages.
// You can't tell which ones are NEW vs which ones have always been unread.
GET /api/lugal/email/notifications   // ← can't detect new arrivals

// With since=, new_messages[] only contains messages received after that time.
GET /api/lugal/email/notifications?since=2026-04-21T07:14:12   // ← only new arrivals
```

### ❌ Fetching the full inbox on every notification poll

```javascript
// WRONG — heavy, slow, and unnecessary
setInterval(async () => {
  const data = await fetchNotifications(token);     // fast, ≈ 50ms
  await fetchInbox(token);                          // slow, triggers sync
}, 15_000);

// CORRECT — fetch notifications for counts/toasts; only re-fetch inbox when needed
setInterval(async () => {
  const data = await fetchNotifications(token);     // fast poll ≈ 50ms
  if (data.new_messages.length > 0 && userIsOnInboxPage) {
    await fetchInbox(token);                        // only when user is looking at inbox
  }
}, 15_000);
```

---

## 9. React Example

Complete, production-ready implementation:

```jsx
// hooks/useEmailNotifications.js
import { useState, useEffect, useRef, useCallback } from 'react';

const POLL_MS = 15_000;

export function useEmailNotifications(token) {
  const [unreadCount,    setUnreadCount]    = useState(0);
  const [newMessages,    setNewMessages]    = useState([]);
  const [recentlySent,   setRecentlySent]   = useState([]);
  const [accounts,       setAccounts]       = useState([]);
  const checkedAtRef = useRef(null);
  const timerRef     = useRef(null);

  const poll = useCallback(async () => {
    if (!token) return;
    const since = checkedAtRef.current
      ? `?since=${encodeURIComponent(checkedAtRef.current)}`
      : '';
    try {
      const res  = await fetch(`/api/lugal/email/notifications${since}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const json = await res.json();
      if (!json.success) return;

      const d = json.data;

      setUnreadCount(d.inbox);
      setAccounts(d.accounts);
      setRecentlySent(d.recently_sent);

      // Only trigger notifications on subsequent polls (first poll is baseline)
      if (checkedAtRef.current && d.new_messages.length > 0) {
        setNewMessages(d.new_messages);       // trigger toast/popup in UI
        fireBrowserNotifications(d.new_messages);
      }

      checkedAtRef.current = d.checked_at;   // update for next poll
    } catch (e) {
      console.error('Email poll error', e);
    }
  }, [token]);

  useEffect(() => {
    if (!token) return;
    poll();                                   // immediate first poll
    timerRef.current = setInterval(poll, POLL_MS);
    return () => clearInterval(timerRef.current);
  }, [token, poll]);

  return { unreadCount, newMessages, recentlySent, accounts };
}

// Request permission once, show a notification per new message
async function fireBrowserNotifications(messages) {
  if (!('Notification' in window)) return;
  if (Notification.permission === 'default') {
    await Notification.requestPermission();
  }
  if (Notification.permission !== 'granted') return;
  for (const msg of messages.slice(0, 3)) {   // max 3 at once
    new Notification(`New email — ${msg.account_name}`, {
      body:    `${msg.from_name || msg.from_address}: ${msg.subject}`,
      tag:     `email-${msg.id}`,              // deduplicates
      silent:  false,
    });
  }
}
```

```jsx
// components/EmailBadge.jsx
import { useEmailNotifications } from '../hooks/useEmailNotifications';

export function EmailBadge({ token }) {
  const { unreadCount } = useEmailNotifications(token);
  return (
    <div className="email-icon-wrapper">
      <EmailIcon />
      {unreadCount > 0 && (
        <span className="badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
      )}
    </div>
  );
}
```

```jsx
// components/SentMessage.jsx — showing delivery ticks
function DeliveryTick({ smtp_delivered, smtp_error }) {
  if (smtp_error && !smtp_delivered) {
    return <span title={smtp_error} className="delivery-failed">✗</span>;
  }
  if (smtp_delivered) {
    return <span className="delivery-ok" title="Delivered to mail server">✓✓</span>;
  }
  return <span className="delivery-pending" title="Sending…">✓</span>;
}
```

---

## 10. API Quick Reference

### Notifications (poll)
```
GET /api/lugal/email/notifications
GET /api/lugal/email/notifications?since=2026-04-21T07:14:12
```

### Inbox
```
GET /api/lugal/email/mailbox/inbox?folder=inbox&limit=50&offset=0
GET /api/lugal/email/mailbox/inbox?folder=inbox&limit=50&force_sync=1
GET /api/lugal/email/mailbox/inbox?folder=inbox&limit=50&auto_sync=0
```

### Sent folder
```
GET /api/lugal/email/mailbox/inbox?folder=sent&limit=50&offset=0&auto_sync=0
```

### Message detail (auto-marks read)
```
GET /api/lugal/email/messages/<id>
```
Response includes `body_html`, `body_text`, `body_fetched`, `smtp_delivered`.  
If `body_fetched: false`, the body is blank — it will be fetched on this call (takes ~1s).

### Send
```
POST /api/lugal/email/send
{ "account_id": 26, "to": [{"email": "someone@example.com"}], "subject": "...", "body_html": "...", "body_text": "..." }
```
Response: `{ "success": true, "data": { "id": ..., "smtp_delivered": true, ... } }`  
Recipient not found: HTTP 422 `{ "success": false, "code": "recipient_not_found", "error": "..." }`

### Reply
```
POST /api/lugal/email/messages/<id>/reply
{ "body_html": "...", "body_text": "..." }
```

### Forward
```
POST /api/lugal/email/messages/<id>/forward
{ "to": [{"email": "manager@example.com"}], "body_html": "..." }
```

### Mark read / unread
```
POST /api/lugal/email/messages/<id>/read
{ "is_read": true }
```
> Do NOT call on sent messages. `GET /messages/<id>` already auto-marks read.

### Delete (move to trash)
```
DELETE /api/lugal/email/messages/<id>
```

### Restore from trash
```
POST /api/lugal/email/messages/<id>/restore
```

### Archive
```
POST /api/lugal/email/messages/<id>/archive
```

### Star / unstar
```
POST /api/lugal/email/messages/<id>/star
```

### Account list
```
GET /api/lugal/email/accounts
```

### Trigger background sync (no-wait)
```
GET /api/lugal/email/sync/all
GET /api/lugal/email/accounts/<id>/sync
```

---

## Polling Interval Summary

| What you're doing | Interval |
|-------------------|----------|
| Unread badge + new message notifications | Every **15 seconds** |
| Inbox list (auto-syncs on fetch) | On page load + when user manually refreshes |
| Sent folder | On page load only (or when user navigates to it) |
| Message detail | On open only |
