# WebSocket, Email, Chat & Stories — System Documentation

> **Last updated:** 2026-04-30  
> Covers the full architecture, every file, all API endpoints, the real-time push flow, and all changes applied during the Email System Hardening session.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [WebSocket Layer](#2-websocket-layer)
3. [Email Engine](#3-email-engine)
4. [Supply Chat](#4-supply-chat)
5. [Stories](#5-stories)
6. [Cross-Cutting: Bus Channels & Push Notification Matrix](#6-cross-cutting-bus-channels--push-notification-matrix)
7. [FE Connection Startup Flow](#7-fe-connection-startup-flow)
8. [All Changes Made (Hardening Session)](#8-all-changes-made-hardening-session)
9. [File Reference Table](#9-file-reference-table)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser / Mobile FE                                            │
│                                                                 │
│  ┌─────────────┐  ┌───────────────────────┐  ┌─────────────┐  │
│  │  REST API   │  │  Odoo WebSocket       │  │  Web Push   │  │
│  │  (JWT Auth) │  │  (session_id cookie)  │  │  (VAPID)    │  │
│  └──────┬──────┘  └──────────┬────────────┘  └──────┬──────┘  │
└─────────┼────────────────────┼───────────────────────┼─────────┘
          │ HTTP               │ WS                    │ HTTPS
          ▼                    ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  aiohttp ws_proxy.py  (port 5172 / 3003)                        │
│  client_max_size = 1 GB                                         │
│  Routes: /websocket → gevent :8072                              │
│          everything else → werkzeug :8069                       │
└─────────────────────────────────────────────────────────────────┘
          │                    │
          ▼                    ▼
┌──────────────────┐  ┌────────────────────────────────────────┐
│  Odoo Workers    │  │  Odoo Gevent Worker (:8072)            │
│  (werkzeug)      │  │  addons/bus/websocket.py               │
│  REST endpoints  │  │  → lugal_ir_websocket._authenticate()  │
│                  │  │  → _build_bus_channel_list()           │
└──────────────────┘  └────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL (bus.bus table)                                      │
│  Real-time fan-out: INSERT → Odoo notifies gevent → WS push     │
└──────────────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────────────┐
│  Background Threads (per-process daemons)                        │
│  • IMAP IDLE watcher threads  (one per credential group)         │
│  • SMTP background threads    (one per outbound email)           │
│  • Typing auto-stop timers    (one per active typist)            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 2. WebSocket Layer

### 2.1 Session Bootstrap (`ws_session.py`)

**File:** `addons/lugal_ws_migration/controllers/ws_session.py`

The FE cannot open an Odoo WebSocket with a JWT token — Odoo requires an `Odoo-Session` cookie.  
The session bootstrap endpoint converts a JWT into a session cookie in one step.

#### `POST /api/crm/ws/session`

```
Authorization: Bearer <jwt>
→ validates JWT with ensure_jwt_user_id()
→ creates Odoo session (session.uid, session.login, session.session_token)
→ saves session to session store
→ returns Set-Cookie: session_id=<sid>; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400
```

**Response:**
```json
{
  "success": true,
  "data": { "session_id": "<sid>", "expires_in": 3600 }
}
```

The browser automatically stores the cookie. The FE does not need to parse the response body — when the Vite proxy forwards the `/websocket` upgrade, the cookie goes along automatically.

#### `GET /api/crm/ws/config`

Returns whether WebSocket mode is enabled and the current WS version string the FE must include in the URL:

```json
{
  "use_websocket": true,
  "fallback_on_error": true,
  "ws_version": "saas-18.5-1",
  "ws_url": "ws://192.168.116.228:3003/websocket?version=saas-18.5-1"
}
```

If `use_websocket=false`, the FE falls back to long-polling (`/web/bus/poll`).  
Controlled by `ir.config_parameter` key `ws.rollout.enabled`.

---

### 2.2 Channel Subscription (`lugal_ir_websocket.py`)

**File:** `addons/lugal_ws_migration/models/lugal_ir_websocket.py`

Extends Odoo's `ir.websocket` model with two overrides:

#### `_authenticate()`

Catches `TypeError` from `security.check_session()` when `session.session_token = None` (stale session from before the session bootstrap fix). Instead of leaving the socket subscribed to zero channels, it:
- Logs INFO (not ERROR)
- Clears the session
- Raises `SessionExpiredException` → Odoo sends WS close code `4001`
- FE's `_handleClose(4001)` calls `POST /api/crm/ws/session` to get a fresh session and reconnects

#### `_build_bus_channel_list(channels)`

Automatically adds three types of channels to every authenticated user's WebSocket subscription:

| Channel | Purpose |
|---|---|
| `supply_chat.<conv_id>` | One per active conversation the user participates in |
| `supply_user.<uid>` | Per-user private channel (email alerts, delivery receipts, SMTP failures) |
| `supply_stories` | Global broadcast for new story posts |

---

### 2.3 Email WebSocket Push (`lugal_email_ws.py`)

**File:** `addons/lugal_ws_migration/models/lugal_email_ws.py`

Inherits `lugal.email.message` and overrides `create()`. For every new **unread inbox** message:

1. Counts current unread messages for the account
2. Publishes `crm.email.message.new` event on `supply_user.<uid>` with payload:
   ```json
   {
     "message_id": 42,
     "account_id": 3,
     "mailbox": "INBOX",
     "subject": "Your order shipped",
     "from_name": "Shop",
     "from_address": "shop@example.com",
     "received_at": "2026-04-30T14:00:00+03:00",
     "unread_count": 7,
     "uid": 5
   }
   ```
3. Also fires a **Web Push** notification (works even when the browser tab is closed) via `lugal.push.subscription.send_push_to_user()`

---

### 2.4 Push Notifications (`lugal_push_notification.py`)

**File:** `addons/lugal_ws_migration/models/lugal_push_notification.py`

Stores VAPID push subscriptions per user. Used as the last-resort delivery channel when:
- The browser tab is closed
- The WebSocket is not connected
- The user is on mobile with the app backgrounded

Called by both email (`lugal_email_ws.py`) and chat (`supply_chat_controller.py`).

---

## 3. Email Engine

### 3.1 Data Model (`email_message.py`)

**File:** `addons/lugal_email/models/email_message.py`

Model: `lugal.email.message`

| Field | Type | Description |
|---|---|---|
| `account_id` | Many2one | Owning `lugal.email.account` |
| `folder` | Selection | `inbox / sent / drafts / trash / archive / spam` |
| `imap_uid` | Integer | IMAP UID (null for local-only rows) |
| `subject`, `from_name`, `from_address` | Char | Headers |
| `to_addresses`, `cc_addresses`, `bcc_addresses` | Text | JSON lists of `{name, email}` |
| `body_html`, `body_text` | Html/Text | Full body (fetched on demand) |
| `is_read` | Boolean | Sync'd to IMAP `\Seen` flag |
| `is_starred` | Boolean | UI bookmark (independent of IMAP) |
| `is_flagged` | Boolean | IMAP `\Flagged` flag (independent of `is_starred`) |
| `is_important` | Boolean | Gmail `\Important` or manual |
| `is_draft` | Boolean | True for unsent drafts |
| `smtp_delivered` | Boolean | True when SMTP server accepted the message |
| `smtp_error` | Char | Last SMTP error string |
| `smtp_status` | Selection | **NEW:** `pending / delivered / failed` |
| `body_fetched` | Boolean | False = headers only; lazy-fetch on first open |

---

### 3.2 Account & Sync (`email_account.py`)

**File:** `addons/lugal_email/models/email_account.py`

Model: `lugal.email.account`

#### Key methods

| Method | Description |
|---|---|
| `create()` | ORM hook — calls `_schedule_idle_start()` immediately when a new account is saved |
| `action_sync()` | Full INBOX + Sent folder sync over IMAP (called by IDLE watcher and cron) |
| `action_sync_if_stale()` | Throttled wrapper — skips if recently synced |
| `action_sync_all_accounts()` | Cron entry point — deduplicates by credential so shared logins only open one IMAP connection |
| `_get_server_folder_name(purpose)` | Discovers and caches real IMAP folder name for `sent / trash / archive / drafts / spam` |
| `_sync_sent_folder(conn)` | Incrementally imports messages from the IMAP Sent folder into Odoo |
| `_imap_append_sent_async(raw_message)` | Background: uploads a raw RFC-2822 email to the IMAP Sent folder after SMTP delivery |
| `_imap_store_async(uid, folder, add_flags, remove_flags)` | Background: pushes flag changes (`\Seen`, `\Flagged`) to IMAP server |
| `_imap_move_async(uid, from_folder, to_folder_purpose)` | Background: moves message between IMAP folders (MOVE → COPY+DELETE fallback) |
| `_imap_expunge_async(uid, folder)` | Background: marks deleted + EXPUNGEs from IMAP |
| `fetch_message_body(message_id)` | Lazy-fetches full body + attachments from IMAP for a headers-only row |
| `_store_imap_attachments(msg_record, email_msg)` | Extracts MIME attachments from a parsed email and stores as `ir.attachment` |
| `_schedule_idle_start()` | Spawns a one-shot background thread to call `start_all()` after 0.5 s |

#### Folder Name Discovery

`_get_server_folder_name(purpose)` runs IMAP LIST once and caches the result in `ir.config_parameter` under key `lugal.email.folder.<account_id>.<purpose>`. Provider defaults:

| Host | sent | trash | archive | drafts | spam |
|---|---|---|---|---|---|
| `gmail.com` | `[Gmail]/Sent Mail` | `[Gmail]/Trash` | `[Gmail]/All Mail` | `[Gmail]/Drafts` | `[Gmail]/Spam` |
| Other | `Sent` | `Trash` | `Archive` | `Drafts` | `Spam` |

---

### 3.3 IMAP IDLE Watcher (`email_idle_watcher.py`)

**File:** `addons/lugal_email/models/email_idle_watcher.py`

One long-running IDLE thread per unique `(imap_host, imap_port, username)` credential group. Multiple accounts sharing the same IMAP login share one connection.

#### Thread lifecycle

```
start_all() ──► credential group detected
                │
                ├─ Thread already alive?
                │   ├─ YES → check _thread_acc_ids for new accounts → update if needed
                │   └─ NO  → start new thread (staggered 2s apart)
                │
                └─ _run_idle_watcher_classified()
                    │
                    ├─ acquire server semaphore (max 15 concurrent per server)
                    ├─ IMAP4_SSL connect + login + SELECT INBOX
                    ├─ IDLE command loop:
                    │   ├─ wait for EXISTS / RECENT (up to 8 minutes)
                    │   ├─ on EXISTS → logout → call _sync_account() for all acc_ids
                    │   └─ refresh IDLE (DONE + re-IDLE) every 8 minutes
                    ├─ on error → exponential backoff (30s → 300s max)
                    └─ on exit → release semaphore, remove from _idle_threads
```

#### Key module-level state

| Variable | Type | Purpose |
|---|---|---|
| `_idle_threads` | `dict[tuple, Thread]` | Running thread per credential key |
| `_stop_events` | `dict[tuple, Event]` | Shutdown signal per credential key |
| `_thread_acc_ids` | `dict[tuple, set]` | **NEW:** Live set of account IDs per thread — updated when new accounts are added without restarting the thread |
| `_next_retry` | `dict[tuple, float]` | Backoff cooldown timestamps |
| `_server_sems` | `dict[tuple, Semaphore]` | Max 15 concurrent connections per `(host, port)` |

#### Ownership (multi-process)

Only **one** Odoo worker process owns the IDLE threads. Ownership is stored in `ir.config_parameter` key `lugal.idle.supervisor.pid`. Other workers see the PID is alive and skip. When the owner dies, the next `start_all()` call claims ownership.

A 5-second watchdog thread runs inside the owner process and calls `start_all()` repeatedly so new accounts are picked up in under 5 seconds (instead of waiting up to 60 seconds for the cron).

---

### 3.4 Email REST API (`email_controller.py`)

**File:** `addons/lugal_email/controllers/email_controller.py`

All endpoints: `GET/POST/PATCH/DELETE /api/lugal/email/*` — plain HTTP with `Authorization: Bearer <jwt>`.

#### Account Management

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/accounts` | GET | List user's email accounts |
| `/api/lugal/email/accounts` | POST | Create new email account |
| `/api/lugal/email/accounts/<id>` | GET/PATCH/DELETE | Read / update / delete account |
| `/api/lugal/email/accounts/<id>/test` | POST | Test IMAP connection |
| `/api/lugal/email/accounts/<id>/sync` | POST | Force IMAP sync |
| `/api/lugal/email/accounts/<id>/set_default` | POST | Set as default account |

#### Message Listing & Detail

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/messages` | GET | List messages with filters |
| `/api/lugal/email/messages/<id>` | GET | Get single message (lazy-fetches body) |
| `/api/lugal/email/messages/<id>` | PATCH | Update `is_flagged`, `is_starred`, `is_important` |
| `/api/lugal/email/messages/<id>` | DELETE | Move to trash |
| `/api/lugal/email/messages/details` | POST | Bulk fetch message details |

**Filter params for GET `/api/lugal/email/messages`:**

| Param | Value | Behavior |
|---|---|---|
| `folder` | string | `inbox / sent / drafts / trash / archive / spam` |
| `unread` | `1` | Only unread messages |
| `flagged` | `1` | Only flagged (`is_flagged=True`) |
| `important` | `1` | Only important |
| `sent_to_me` | `1` | Only messages where To includes the user's email |
| `has_attachments` | `1` | Reserved for future use |

#### Compose

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/send` | POST | Send new email (async SMTP) |
| `/api/lugal/email/messages/<id>/reply` | POST | Reply to email (async SMTP) |
| `/api/lugal/email/messages/<id>/reply_all` | POST | Reply-All (async SMTP) |
| `/api/lugal/email/messages/<id>/forward` | POST | Forward email (async SMTP) |

#### Drafts

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/drafts` | POST | Create draft |
| `/api/lugal/email/drafts` | GET | List all drafts |
| `/api/lugal/email/drafts/<id>` | GET | Get single draft |
| `/api/lugal/email/drafts/<id>` | PATCH | Update draft |
| `/api/lugal/email/drafts/<id>` | DELETE | Delete draft |
| `/api/lugal/email/drafts/<id>/send` | POST | Send draft (idempotent — uses `SELECT FOR UPDATE NOWAIT`) |

#### Status Actions

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/messages/<id>/read` | POST | Toggle `is_read` + sync to IMAP |
| `/api/lugal/email/messages/<id>/star` | POST | Toggle `is_starred` + sync `\Flagged` to IMAP |
| `/api/lugal/email/messages/<id>/archive` | POST | Move to archive + IMAP MOVE |
| `/api/lugal/email/messages/<id>/unarchive` | POST | Move archive → inbox + IMAP MOVE |
| `/api/lugal/email/messages/<id>/restore` | POST | Move trash → inbox + IMAP MOVE |
| `/api/lugal/email/messages/<id>/permanent` | DELETE | Hard-delete (trash only) |

#### Attachments

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/attachments/upload` | POST | Upload one or more files (multipart, max 1 GB total) |

#### Notifications / Polling

| Endpoint | Method | Description |
|---|---|---|
| `/api/lugal/email/notifications` | GET | Unread counts, new messages, SMTP status |
| `/api/lugal/email/unread` | GET | Alias for notifications |

**Notification endpoint params:**

| Param | Description |
|---|---|
| `?since=<ISO>` | Only return inbox messages received after this timestamp |
| `?last_seen_id=<int>` | **NEW:** Only return inbox messages with `id > last_seen_id` (catch-up for missed push) |

**Notification response includes:**
- `total` / `inbox` unread counts
- `per_folder` counts
- `accounts[]` per-account unread + sync status
- `new_messages[]` up to 10 most recent unread inbox messages
- `recently_sent[]` last 20 sent messages with `smtp_status` (pending / delivered / failed)
- `checked_at` — use as `?since=` on the next poll

#### SMTP Send Flow (async)

```
POST /api/lugal/email/send
    │
    ├─ Validate JWT, resolve account
    ├─ Create lugal.email.message row (folder='sent', smtp_status='pending')
    ├─ Attach uploaded ir.attachment records
    ├─ request.env.cr.commit()     ← DB committed BEFORE background thread
    ├─ _send_via_smtp_async()      ← fires background daemon thread
    └─ return 201 { smtp_pending: true }

Background thread _bg():
    ├─ Read attachment binaries from DB (fresh cursor)
    ├─ Build MIME message (_build_mime_message)
    ├─ _do_smtp_send()
    │   ├─ Port 465  → SMTP_SSL
    │   ├─ smtp_use_tls=True + other port → SMTP + STARTTLS
    │   └─ otherwise → plain SMTP
    ├─ Write smtp_delivered / smtp_error / smtp_status back to DB
    ├─ On failure → bus push 'crm.email.smtp.failed' to supply_user.<uid>
    └─ On success → IMAP APPEND raw message to Sent folder
            (acquires _server_semaphore before connecting)
```

---

### 3.5 CRM Email API (`crm_email_controller.py`)

**File:** `addons/lugal_email/controllers/crm_email_controller.py`

JSON-RPC endpoints for CRM-context email operations.

| Endpoint | Description |
|---|---|
| `POST /api/crm/email/subscribe` | Wake IDLE supervisor + trigger immediate IMAP sync. Returns `unread_count` so FE can reconcile on connect. **NEW: returns `unread_count`** |
| `POST /api/crm/email/messages/list` | CRM inbox list with customer/ticket links |
| `POST /api/crm/email/messages/<id>` | CRM message detail |
| `POST /api/crm/email/customer/<id>/messages` | All emails linked to a customer |
| `POST /api/crm/email/customer/<id>/thread` | Email thread grouped by subject |
| `POST /api/crm/email/templates/list` | List email templates |
| `POST /api/crm/email/templates/<id>/apply` | Render template with variables |
| `POST /api/crm/email/bulk/read` | Mark multiple messages as read |
| `POST /api/crm/email/bulk/trash` | Move multiple messages to trash |
| `POST /api/crm/email/messages/bulk_delete` | Hard-delete from trash (max 50) |
| `POST /api/crm/email/stats` | Message counts by folder |

---

## 4. Supply Chat

### 4.1 Models

#### `crm_supply_conversation.py`
Model: `lugal.supply.conversation`

| Field | Description |
|---|---|
| `type` | `dm / group / team` |
| `name` | Display name |
| `participant_ids` | Many2many `res.users` |
| `created_by_id` | Creator |
| `group_admin_ids` | Group admins (Many2many) |
| `group_supervisor_ids` | Group supervisors (Many2many) |
| `only_admins_can_send` | Boolean — broadcast mode |
| `group_description` | Text |
| `last_activity` | Datetime — drives sort order |
| `is_archived` | Boolean |

#### `crm_supply_message.py`
Model: `lugal.supply.message`

| Field | Description |
|---|---|
| `conversation_id` | Many2one conversation |
| `sender_id` | Many2one res.users |
| `content` | Text body |
| `kind` | `text / image / video / audio / voice / file` |
| `duration_seconds` | Float (for audio/video) |
| `attachments_json` | JSON list of attachment objects |
| `reply_to_id` | Many2one self (reply threading) |
| `reactions_json` | JSON `{emoji: [uid, ...]}` |
| `read_user_ids` | Many2many res.users |
| `delivered_user_ids` | Many2many res.users |
| `read_receipts_json` | JSON `{uid: ISO_timestamp}` |
| `is_deleted` | Soft delete |
| `is_pinned` | Pin flag |
| `client_message_id` | FE dedup key |

#### `crm_supply_typing.py`
Model: `lugal.supply.typing` — kept for schema compatibility. Typing state is now maintained **entirely in-memory** (module-level `_typing_timers` dict in the controller) to avoid DB serialization failures under concurrent load.

---

### 4.2 Chat REST API (`supply_chat_controller.py`)

**File:** `addons/lugal_crm/controllers/supply_chat_controller.py`

All endpoints: JSON-RPC POST with JWT auth.

#### Conversations

| Endpoint | Description |
|---|---|
| `/api/crm/supply/conversations/list` | List active conversations (sorted by last_activity) |
| `/api/crm/supply/conversations/create` | Create DM (1 recipient) or group (2+ recipients) |
| `/api/crm/supply/conversations/<id>/get` | Get single conversation |
| `/api/crm/supply/conversations/<id>/rename` | Rename group |
| `/api/crm/supply/conversations/<id>/archive` | Archive conversation |
| `/api/crm/supply/conversations/<id>/leave` | Leave conversation (removes participant) |
| `/api/crm/supply/conversations/<id>/update` | Generic update (name, settings) |
| `/api/crm/supply/conversations/<id>/mark_read` | Mark all unread messages as read |
| `/api/crm/supply/conversations/<id>/typing` | Send typing indicator (in-memory only) |
| `/api/crm/supply/conversations/<id>/members/list` | List members |
| `/api/crm/supply/conversations/<id>/members/add` | Add members (admin/supervisor only) |
| `/api/crm/supply/conversations/<id>/members/remove` | Remove member (admin, or self-remove) |
| `/api/crm/supply/conversations/<id>/members/role` | Assign role + group settings |
| `/api/crm/supply/conversations/<id>/pinned` | List all pinned messages |
| `/api/crm/supply/chat/bus_channels` | Return channel names the FE should subscribe to |

#### Messages

| Endpoint | Description |
|---|---|
| `/api/crm/supply/messages/list` | Paginated list (cursor-based: `before_id`) |
| `/api/crm/supply/messages/create` | Send new message + broadcast via bus |
| `/api/crm/supply/messages/forward` | Forward message to another conversation |
| `/api/crm/supply/messages/search` | Full-text search across conversations |
| `/api/crm/supply/messages/<id>/edit` | Edit (sender only, within 5-minute window) |
| `/api/crm/supply/messages/<id>/react` | Toggle emoji reaction |
| `/api/crm/supply/messages/<id>/delivered` | Mark message as delivered (by recipient) |
| `/api/crm/supply/messages/<id>/read` | Mark message as read + record timestamp |
| `/api/crm/supply/messages/<id>/pin` | Pin / unpin message |

#### Real-time Push (Chat)

Every message send fires two bus publishes:

```
1. supply_chat.<conv_id>  ← 'supply.chat.message.new'  (primary, conversation subscribers)
2. supply_user.<uid>      ← 'supply.chat.message.new'  (fallback for each non-sender participant)
   (_via_personal_channel: true on copy 2 — FE must deduplicate by message_id)
```

Also fires a Web Push for closed-tab delivery.

**Other bus events published by the chat controller:**

| Bus Channel | Event Type | Trigger |
|---|---|---|
| `supply_chat.<conv_id>` | `supply.chat.typing.start` | Typing heartbeat |
| `supply_chat.<conv_id>` | `supply.chat.typing.stop` | Stop typing / 8s auto-expire |
| `supply_chat.<conv_id>` | `supply.chat.message.updated` | Message edited |
| `supply_chat.<conv_id>` | `supply.chat.message.pinned` | Message pinned/unpinned |
| `supply_chat.<conv_id>` | `supply.chat.message.reaction.changed` | Reaction toggled |
| `supply_user.<uid>` | `supply.chat.message.reaction.notify` | Reaction added to your message |
| `supply_user.<uid>` | `supply.chat.message.delivered` | Recipient marked delivered |
| `supply_user.<uid>` | `supply.chat.message.read` | Recipient read your message |
| `supply_user.<uid>` | `supply.chat.resubscribe` | New conversation created → FE re-subscribes |

#### New Conversation Flow

When a DM or group is created (`_find_or_create_dm` / `_find_or_create_group`):
1. Conversation row created in DB
2. `_notify_participants_resubscribe()` publishes `supply.chat.resubscribe` to `supply_user.<uid>` for every participant
3. FE receives the event and calls `busClient.resubscribe()` so the new `supply_chat.<conv_id>` channel is added to the active WebSocket subscription
4. Subsequent messages to that conversation reach all participants immediately

---

## 5. Stories

### 5.1 Model (`crm_supply_story.py`)

**File:** `addons/lugal_crm/models/crm_supply_story.py`

Model: `crm.supply.story`

| Field | Description |
|---|---|
| `author_id` | Many2one res.users |
| `text_content` | Text body |
| `attachment_id` | Many2one ir.attachment (image / video / audio) |
| `media_type` | `text / image / video / audio` |
| `background_color` | Hex colour (text stories) |
| `expires_at` | Datetime (default: 24 hours from creation) |
| `viewer_ids` | Many2many res.users (who viewed) |
| `view_count` | Integer |
| `is_active` | Computed: True when not expired |

---

### 5.2 Stories REST API (`supply_stories_controller.py`)

**File:** `addons/lugal_crm/controllers/supply_stories_controller.py`

| Endpoint | Method | Description |
|---|---|---|
| `/api/crm/supply/stories/feed` | POST | Active stories feed grouped by author |
| `/api/crm/supply/stories/create` | POST | Post a new story (text or with media attachment) |
| `/api/crm/supply/stories/<id>/view` | POST | Record that current user viewed the story |
| `/api/crm/supply/stories/<id>/delete` | POST | Soft-expire story (author only) |
| `/api/crm/supply/stories/upload` | POST | Upload media for a story (multipart, max 1 GB) |
| `/api/crm/supply/stories/my` | POST | Current user's own stories |
| `/api/crm/supply/stories/<id>` | POST | Single story detail |

On story create, the event is broadcast to the `supply_stories` channel:
```
bus._sendone('supply_stories', 'supply.stories.new', { story: {...} })
```

All authenticated users' WebSocket connections subscribe to `supply_stories` via `_build_bus_channel_list()`.

---

## 6. Cross-Cutting: Bus Channels & Push Notification Matrix

### Bus Channels Summary

| Channel Name | Subscriber | Events Carried |
|---|---|---|
| `supply_chat.<conv_id>` | All participants of that conversation | `message.new`, `typing.start/stop`, `message.updated`, `message.pinned`, `message.reaction.changed` |
| `supply_user.<uid>` | Single user (always subscribed) | Email arrivals, SMTP failures, chat delivery/read receipts, reaction notifications, new conversation resubscribe signals |
| `supply_stories` | All authenticated users | `supply.stories.new` |

### Complete Event Type Reference

| Event Type | Channel | Payload Key Fields | Sender |
|---|---|---|---|
| `crm.email.message.new` | `supply_user.<uid>` | `message_id`, `subject`, `from_address`, `unread_count` | `lugal_email_ws.py` |
| `crm.email.smtp.failed` | `supply_user.<uid>` | `msg_id`, `subject`, `error` | `_do_smtp_send()` |
| `supply.chat.message.new` | `supply_chat.<conv_id>` and `supply_user.<uid>` | Full message object | `_publish_new_message()` |
| `supply.chat.typing.start` | `supply_chat.<conv_id>` | `user_id`, `user_name`, `is_typing:true` | `conversation_typing()` |
| `supply.chat.typing.stop` | `supply_chat.<conv_id>` | `user_id`, `is_typing:false` | `conversation_typing()` / auto-stop timer |
| `supply.chat.message.updated` | `supply_chat.<conv_id>` | Full message object | `message_edit()` |
| `supply.chat.message.pinned` | `supply_chat.<conv_id>` | `message_id`, `is_pinned`, `pinned_by_id` | `message_pin()` |
| `supply.chat.message.reaction.changed` | `supply_chat.<conv_id>` | `message_id`, `reactions` | `message_react()` |
| `supply.chat.message.reaction.notify` | `supply_user.<author_uid>` | `emoji`, `reactor_id`, `reactor_name` | `message_react()` |
| `supply.chat.message.delivered` | `supply_user.<sender_uid>` | `message_id`, `delivered_to` | `message_delivered()` |
| `supply.chat.message.read` | `supply_user.<sender_uid>` | `message_id`, `read_by`, `read_receipts` | `message_read()` / `conversation_mark_read()` |
| `supply.chat.resubscribe` | `supply_user.<uid>` | `conversation_id`, `conversation_type` | `_notify_participants_resubscribe()` |
| `supply.stories.new` | `supply_stories` | Full story object | `story_create()` |

---

## 7. FE Connection Startup Flow

```
App loads
    │
    ▼
GET /api/crm/ws/config
    │  use_websocket: true
    ▼
POST /api/crm/ws/session          ← exchanges JWT for session cookie
    │  Set-Cookie: session_id=...
    ▼
WebSocket connect to ws://<host>/websocket?version=<ws_version>
    │  Cookie: session_id=<sid>  (sent automatically by browser)
    ▼
Odoo _authenticate()              ← validates session_token
    │  → SessionExpiredException on stale session → FE re-does /api/crm/ws/session → reconnect
    ▼
_build_bus_channel_list()
    ├─ supply_chat.<conv_id>  for every active conversation
    ├─ supply_user.<uid>      (always)
    └─ supply_stories         (always)
    ▼
POST /api/crm/email/subscribe     ← wakes IDLE supervisor, triggers IMAP sync
    │  returns { subscribed: true, unread_count: N, accounts: [...] }
    │  FE updates badge immediately from unread_count
    ▼
GET /api/lugal/email/notifications  ← initial poll to catch any emails
    │  params: ?last_seen_id=0
    │  returns new_messages[], unread counts, checked_at
    ▼
Running state:
    • WebSocket receives push events in real time
    • FE polls /api/lugal/email/notifications every 30s with ?last_seen_id=<last_known_id>
      as a safety net (catches any push that was missed while tab was hidden)
    • On browser tab focus / visibility-change: call notifications endpoint
```

---

## 8. All Changes Made (Hardening Session)

### Fix 1 — Stale `acc_ids` in IDLE thread (new user misses notifications)

**File:** `addons/lugal_email/models/email_idle_watcher.py`

**Problem:** When a new `lugal.email.account` row was added for a credential that already had a live IDLE thread, `start_all()` skipped starting a new thread (`if existing and existing.is_alive(): continue`). The thread's `acc_ids` list was frozen at startup — the new account never received IDLE coverage.

**Fix:**
- Added module-level `_thread_acc_ids: dict[tuple, set]` — maps `cred_key` → current set of account IDs served by the live thread
- `start_all()` now detects new acc_ids for alive threads and updates `_thread_acc_ids` atomically
- `_run_idle_watcher_classified` reads `_thread_acc_ids.get(cred_key)` on each EXISTS event so newly added accounts are synced immediately
- Thread exit now cleans up `_thread_acc_ids[cred_key]`

---

### Fix 2 — Multi-browser notification gap

**File:** `addons/lugal_email/controllers/crm_email_controller.py`

`POST /api/crm/email/subscribe` now returns `unread_count` (current unread inbox count) so the FE can update the badge immediately on WebSocket connect without waiting for the next IMAP sync.

**File:** `addons/lugal_email/controllers/email_controller.py`

`GET /api/lugal/email/notifications` now accepts `?last_seen_id=<int>`. The endpoint returns only inbox messages with `id > last_seen_id`, giving the FE a reliable catch-up mechanism for any push notifications it missed while the WebSocket was not subscribed.

---

### Fix 3 — IMAP folder name mapping

**File:** `addons/lugal_email/controllers/email_controller.py`

Added `_resolve_imap_folder(account, local_folder)` helper:
```python
def _resolve_imap_folder(account, local_folder):
    if local_folder == 'inbox':
        return 'INBOX'
    try:
        return account.sudo()._get_server_folder_name(local_folder)
    except Exception:
        return local_folder.capitalize()
```

Replaced all uses of `msg.folder.upper()` and hardcoded `'archive'`/`'SENT'` strings in:
- `toggle_read` (mark-read IMAP sync)
- `toggle_star` (flag IMAP sync)
- `archive_msg` (IMAP MOVE source folder)
- `unarchive_msg` (IMAP MOVE source folder — was passing wrong string `'INBOX'` as purpose)
- `restore` (IMAP MOVE source folder)
- `message_detail` PATCH handler (is_flagged IMAP sync)
- `message_detail` DELETE handler (IMAP MOVE to trash)

---

### Fix 4 — SMTP SSL/TLS logic

**File:** `addons/lugal_email/controllers/email_controller.py`

**Before (broken):** `use_ssl = (not smtp_use_tls) or (smtp_port == 465)` — this caused `smtp_use_tls=False` (plain SMTP) to use `SMTP_SSL`, which fails on port 25.

**After (correct):**
```python
if smtp_port == 465:
    server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30)
elif smtp_use_tls:          # port 587 and others with STARTTLS
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
    server.ehlo()
    server.starttls()
else:                       # plain SMTP (port 25 / custom relay)
    server = smtplib.SMTP(smtp_host, smtp_port, timeout=30)
```

---

### Fix 5 — Draft double-send race condition

**File:** `addons/lugal_email/controllers/email_controller.py`

`POST /api/lugal/email/drafts/<id>/send` now uses `SELECT FOR UPDATE NOWAIT` to atomically claim the draft row. A concurrent request that hits the locked row gets `409 Conflict` instead of a second SMTP delivery.

---

### Fix 6 — IMAP APPEND bypasses connection semaphore

**File:** `addons/lugal_email/controllers/email_controller.py`

The IMAP APPEND connection (uploading sent email to Sent folder) in `_send_via_smtp_async._bg()` now acquires `_server_semaphore(imap_host, imap_port)` and releases it in a `finally` block, keeping bulk sends within the same 15-connection cap as IDLE threads.

---

### Fix 7 — Silent Sent folder sync failure

**File:** `addons/lugal_email/models/email_account.py`

`_sync_sent_folder()` now logs a `WARNING` when `SELECT` on the Sent folder fails, clears the cached folder name, and attempts auto-discovery before giving up silently.

---

### Fix 8 — SMTP failures invisible to FE

**File:** `addons/lugal_email/models/email_message.py`

Added `smtp_status = fields.Selection(['pending', 'delivered', 'failed'], default='pending')`.

**File:** `addons/lugal_email/controllers/email_controller.py`

`_do_smtp_send()` now:
- Writes `smtp_status='delivered'` on success
- Writes `smtp_status='failed'` and publishes `crm.email.smtp.failed` bus event on failure
- `_message_to_dict()` includes `smtp_status` in every message response

**DB Migration:**
```sql
ALTER TABLE lugal_email_message ADD COLUMN IF NOT EXISTS smtp_status VARCHAR DEFAULT 'pending';
UPDATE lugal_email_message SET smtp_status = 'delivered' WHERE smtp_delivered = TRUE;
UPDATE lugal_email_message SET smtp_status = 'failed'    WHERE smtp_error IS NOT NULL AND smtp_error != '';
CREATE INDEX lugal_email_message_smtp_status_idx ON lugal_email_message(smtp_status);
```

---

## 9. File Reference Table

| File | Addon | Purpose | Changed |
|---|---|---|---|
| `controllers/ws_session.py` | `lugal_ws_migration` | JWT → Odoo session cookie exchange; WS config | — |
| `models/lugal_ir_websocket.py` | `lugal_ws_migration` | Channel list builder; stale-session auth fix | — |
| `models/lugal_email_ws.py` | `lugal_ws_migration` | ORM hook: email `create()` → bus push + web push | — |
| `models/lugal_push_notification.py` | `lugal_ws_migration` | VAPID push subscription model | — |
| `controllers/push_controller.py` | `lugal_ws_migration` | Push subscription register/unregister endpoint | — |
| `models/email_message.py` | `lugal_email` | Email message model | **YES** — `smtp_status` field |
| `models/email_account.py` | `lugal_email` | IMAP/SMTP account model + sync methods | **YES** — `_sync_sent_folder` warning |
| `models/email_idle_watcher.py` | `lugal_email` | IMAP IDLE supervisor | **YES** — `_thread_acc_ids` fix |
| `controllers/email_controller.py` | `lugal_email` | Core email REST API | **YES** — multiple fixes |
| `controllers/crm_email_controller.py` | `lugal_email` | CRM email JSON-RPC API | **YES** — `unread_count` in subscribe |
| `controllers/settings_email_controller.py` | `lugal_email` | Account settings CRUD | — |
| `controllers/supply_chat_controller.py` | `lugal_crm` | Chat REST API + real-time bus | — |
| `models/crm_supply_conversation.py` | `lugal_crm` | Conversation model | — |
| `models/crm_supply_message.py` | `lugal_crm` | Message model | — |
| `models/crm_supply_typing.py` | `lugal_crm` | Typing model (schema only; state is in-memory) | — |
| `controllers/supply_stories_controller.py` | `lugal_crm` | Stories REST API | — |
| `models/crm_supply_story.py` | `lugal_crm` | Story model | — |
| `controllers/crm_notifications_controller.py` | `lugal_crm` | General CRM notification endpoints | — |
| `controllers/bus_compat_controller.py` | `lugal_crm` | Bus compatibility bridge | — |
| `addons/auth_controller.py` | `lugal_auth` | Login — triggers immediate IMAP sync | — |
| `scripts/ws_proxy.py` | root | aiohttp reverse proxy (1 GB client_max_size) | — |
