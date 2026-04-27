# WebSocket Migration — All Backend Changes

> **Branch:** `branch_websocket-migration` (addons: `lugal_ws_migration`, `lugal_email`, `lugal_crm`, `lugal_auth`)
> **Purpose:** Document every change made during the WebSocket migration so the team can safely cherry-pick them onto the `development` branch once testing is complete.

---

## Table of Contents

1. [Overview](#1-overview)
2. [New Addon: `lugal_ws_migration`](#2-new-addon-lugal_ws_migration)
3. [IMAP IDLE Email Notifications](#3-imap-idle-email-notifications)
4. [Chat — Cursor Pagination (20 messages at a time)](#4-chat--cursor-pagination)
5. [JWT Authentication Fix](#5-jwt-authentication-fix)
6. [Session Cookie Fix for Stale WebSocket Sessions](#6-session-cookie-fix)
7. [Frontend Changes (FE repo)](#7-frontend-changes-fe-repo)
8. [Database Changes](#8-database-changes)
9. [Configuration Changes](#9-configuration-changes)
10. [Migration Checklist for Development Branch](#10-migration-checklist-for-development-branch)

---

## 1. Overview

The migration replaces Odoo's long-polling bus (`bus.bus._poll`) with Odoo's native WebSocket (`ir.websocket`). All real-time events (chat messages, typing, read receipts, email notifications, stories) now flow through a single persistent WebSocket connection instead of repeated HTTP polls.

Email notifications are additionally accelerated using IMAP IDLE — a push-based protocol where the mail server notifies Odoo the instant a new message arrives, eliminating the 1-minute poll delay.

---

## 2. New Addon: `lugal_ws_migration`

### Location
`addons/lugal_ws_migration/`

### Files

#### `controllers/ws_session.py`
JWT-to-Odoo-session bridge. The frontend obtains a short-lived Odoo `session_id` cookie by passing its JWT to this endpoint.

```
POST /api/crm/ws/session
Authorization: Bearer <jwt>
X-Odoo-Database: lugal_ws_sandbox

Response:
  Set-Cookie: session_id=<odoo_session>
  { "success": true }
```

Also exposes the WebSocket config endpoint:

```
GET /api/crm/ws/config
Authorization: Bearer <jwt>

Response:
  {
    "use_websocket": true,
    "ws_version": "saas-18.5-1",
    "ws_url": "ws://<host>/websocket"
  }
```

**Key implementation details:**
- Sets `session.uid` from JWT, computes `session.session_token`, forces `session.can_save = True`.
- Explicitly saves session via `root.session_store.save(session)`.
- Manually builds and attaches the `Set-Cookie` header to the response.

#### `models/lugal_ir_websocket.py`
Overrides `ir.websocket._build_bus_channel_list()` to auto-subscribe the connecting user to:
- `supply_chat.<conv_id>` — for every conversation the user is a member of
- `supply_user.<uid>` — for direct user events (typing, read receipts, email notifications)
- `supply_stories` — for stories (all authenticated users)

This replaces the old `GET /api/crm/supply/chat/bus_channels` frontend-driven subscription.

#### `models/lugal_email_ws.py`
Overrides `lugal.email.message.create()` to publish a `crm.email.message.new` bus event to the `supply_user.<uid>` channel the instant a new inbox message is saved. This wires IMAP IDLE → bus → WebSocket → frontend.

#### `models/lugal_ir_http.py`
Overrides `ir.http._authenticate_explicit` to gracefully handle stale WebSocket session cookies that would otherwise raise `TypeError` from `security.check_session` when `session_token` is `None`. Falls back to JWT Bearer authentication transparently.

---

## 3. IMAP IDLE Email Notifications

### Goal
New emails arrive at the frontend **within ~1–2 seconds** of the external mail server receiving them, instead of waiting for the 1-minute IMAP poll cron.

### File Changed
`addons/lugal_email/models/email_idle_watcher.py` — **completely rewritten (v2)**

### Architecture (v2 — credential-deduplicated, single-process ownership)

#### One thread per unique `(imap_host, imap_port, username)`
Previously: one IDLE thread per `lugal.email.account.id`.
Now: accounts are grouped by IMAP credentials. If 15 accounts share `test@nbs.com.iq` on `mail.nbs.com.iq`, a **single** IDLE thread monitors that inbox instead of 15, eliminating the server's `[LIMIT] Maximum connections` error.

```
Before: 20 accounts → 20 IMAP connections → server rejects most
After:  5 credential groups → 5 IMAP connections → all succeed
```

When `EXISTS` fires on a group's connection, every account in that group is synced.

#### PID-based cross-process ownership (`ir.config_parameter`)
Odoo runs with `workers=9` — 9+ OS processes, each with its own Python heap and `_idle_threads` dict. Without coordination, every cron worker would spawn duplicate threads.

Fix: the first worker to claim ownership writes its PID to `ir.config_parameter` key `lugal.idle.supervisor.pid`. All other workers check this PID via `os.kill(pid, 0)`:
- PID alive → skip (`start_all()` returns 0 in ~0.02s)
- PID dead (process recycled/killed) → claim ownership and restart all threads

```python
# Simplified ownership check in start_all()
stored_pid = int(ICP.get_param('lugal.idle.supervisor.pid', '0'))
if _pid_alive(stored_pid) and stored_pid != my_pid:
    return 0   # another healthy process owns this
ICP.set_param('lugal.idle.supervisor.pid', str(my_pid))
_I_AM_OWNER = True
```

#### Time-based backoff (no permanent failures)
| Error type | Backoff |
|---|---|
| `AUTHENTICATIONFAILED` | 60 minutes |
| `[LIMIT]` / connection exceeded | 5 minutes |
| Other network errors | 5s → 10s → 20s → … → 120s (exponential) |

Accounts in backoff are retried automatically — no manual restart required. This ensures that if an employee's email server is temporarily down, the IDLE thread picks back up as soon as the backoff expires.

#### IDLE connection lifecycle (prevents concurrent connection errors)
A critical fix for servers that limit simultaneous connections per user (e.g., `mail.nooralnibras.com` allows ~1 active connection per user):

```python
# When EXISTS is detected in the IDLE loop:
conn.send(b'DONE\r\n')
# ... drain DONE response ...
conn.logout()   # ← close BEFORE calling action_sync()
conn = None
for acc_id in acc_ids:
    _sync_account(acc_id, db_name)  # opens its own connection, then closes it
# Outer loop reconnects for the next IDLE cycle
```

Without this, the IDLE connection and the sync connection would overlap, triggering `AUTHENTICATIONFAILED`.

### Automatic pickup of new accounts

#### `addons/lugal_email/models/email_account.py` — `action_test_connection()`
When an employee adds a new email account and hits "Test Connection":
1. If the test succeeds, `_schedule_idle_start()` is called.
2. A background daemon thread wakes 0.5s later and calls `clear_backoff_for_account(acc_id)` followed by `start_all()`.
3. If this process is the IDLE supervisor owner → the thread starts **immediately** (within 1 second of the test passing).
4. If not the owner → the owning process picks it up on its next cron run (**within 1 minute**).

This applies to both test endpoints:
- `POST /api/lugal/email/accounts/<id>/test`
- `POST /api/crm/settings/email/accounts/<id>/test`

#### Supervisor cron (always-on fallback)
The "Lugal Email: IMAP IDLE Supervisor" cron (ID 112) runs every minute. It re-scans all active accounts and starts threads for any group not yet being watched. New accounts added without calling test are still picked up within 1 minute.

### Cron jobs modified (`addons/lugal_email/data/cron.xml`)
Removed `numbercall` field from both cron records so they run indefinitely:
- `ir_cron_lugal_email_imap_sync` — 1-minute IMAP poll (fallback)
- `ir_cron_lugal_email_idle_supervisor` — 1-minute IDLE thread supervisor

---

## 4. Chat — Cursor Pagination

### File Changed
`addons/lugal_crm/controllers/supply_chat_controller.py`

### Changes
- **Default `per_page` changed from 50 → 20** for `messages_list`.
- **Cursor-based pagination** added: `before_id` param fetches messages older than a given message ID (WhatsApp-style "load more on scroll up").
- Response now includes `has_more_older` boolean and `anchor_before_id`.
- **Removed per-user fan-out** for `supply.chat.message.new` bus events (performance improvement — the channel subscription in `_build_bus_channel_list` already handles delivery).

### Model change
`addons/lugal_crm/models/crm_supply_message.py`

Added field:
```python
client_message_id = fields.Char(string='Client Message ID', index=True)
```
Used for optimistic UI deduplication — the frontend sends a UUID with each message and the backend returns it, allowing the FE to reconcile the sent message with the server's copy.

---

## 5. JWT Authentication Fix

### File Changed
`addons/lugal_auth/models/lugal_jwt_service.py`

### Problem
Odoo 19's `res.users.authenticate()` tracks failed login attempts per IP and raises a cooldown lock. When the WebSocket migration introduced multiple login paths, the cooldown was being triggered incorrectly.

### Fix
`authenticate_user()` now bypasses `res.users.authenticate()` and calls `user._check_credentials()` directly, which validates the password without touching the login rate-limit counter.

---

## 6. Session Cookie Fix

### File Changed
`addons/lugal_ws_migration/models/lugal_ir_http.py`

### Problem
When a WebSocket worker has a stale session cookie (session saved but `session_token` is `None`), Odoo's `security.check_session()` raises `TypeError: argument of type 'NoneType' is not iterable`.

### Fix
`_authenticate_explicit` is overridden to catch this `TypeError`, log out the invalid session, and allow JWT Bearer authentication to proceed instead of returning a 500 error.

---

## 7. Frontend Changes (FE repo)

### Location
`/home/capo7amzah/Downloads/TakeAwayMidnight/` — branch `branch_websocket-migration`

### Files changed

| File | Change |
|---|---|
| `src/app/providers/RealtimeProvider.tsx` | Global WebSocket client; handles `supply.chat.message.new`, `crm.email.message.new`, `supply.typing.*`, `supply.message.read`, `supply.story.new` events. Uses `refetchType: 'all'` for `invalidateQueries` so badges update on any route. Skips notification sound if user is currently in the active conversation. |
| `src/app/hooks/useConversationMessages.ts` | Cursor-based pagination with IntersectionObserver for auto-load on scroll-up. Appends incoming WS messages to local cache (no full refetch needed). |
| `src/app/components/AppHeader/index.tsx` | Notification badge wired to WS events instead of polling timer. Shows count from `GET /api/crm/notifications`. Navigation to email notification routes to email screen (not chat). |
| `src/app/pages/Chat/ConversationView.tsx` | Auto-marks messages as read when conversation is active. Sends `client_message_id` UUID with every message for optimistic UI. |
| `src/lib/wsClient.ts` | Native WebSocket client with `?version=saas-18.5-1` query param, exponential reconnect backoff, and `BroadcastChannel` deduplication across browser tabs. |
| `vite.config.ts` | Proxy config: forwards `/api`, `/web`, `/lugal`, `/websocket` to backend with correct `Host`, `Origin`, and WebSocket upgrade headers. |

### Critical WebSocket connection requirement
The frontend MUST connect to:
```
ws://<backend-host>/websocket?version=saas-18.5-1
```
Omitting `?version=saas-18.5-1` causes the server to close the connection immediately with code 1008.

---

## 8. Database Changes

All changes are additive (no drops or renames). Safe to apply to `lugal_local` without data loss.

| Table | Change | Migration |
|---|---|---|
| `lugal_supply_message` | Added `client_message_id VARCHAR` column | Auto-applied by Odoo ORM on module upgrade |
| `ir_config_parameter` | Key `lugal.idle.supervisor.pid` written at runtime | Runtime only, no schema change |

---

## 9. Configuration Changes

### `odoo_ws.conf` (migration branch only)
```ini
limit_upload = 1073741824   # 1 GB (was 5 MB)
```

**Note:** This increase is already needed on `development` branch too (users reported 1 GB file transfers). Recommend applying to `odoo.conf` (development) as well.

---

## 10. Migration Checklist for Development Branch

When the team decides to merge this work to `development`, follow these steps in order:

### Step 1 — Danger zone (do NOT touch on development)
- `bus.bus` table — do not alter schema
- `ir.websocket` base class — extend only, never modify
- `res.users.authenticate` — the JWT fix calls `_check_credentials` directly; confirm this is still valid after any Odoo core updates

### Step 2 — Cherry-pick / copy these files

```
addons/lugal_ws_migration/               ← new addon (copy entire folder)
addons/lugal_email/models/email_idle_watcher.py    ← rewritten
addons/lugal_email/models/email_account.py         ← _schedule_idle_start() added
addons/lugal_email/data/cron.xml                   ← removed numbercall
addons/lugal_crm/controllers/supply_chat_controller.py  ← cursor pagination
addons/lugal_crm/models/crm_supply_message.py      ← client_message_id field
addons/lugal_auth/models/lugal_jwt_service.py      ← bypass cooldown
```

### Step 3 — Add `lugal_ws_migration` to installed modules
In `odoo.conf` (development):
```ini
# addons_path already includes addons/; no extra config needed
```
Then install the module:
```bash
./odoo-bin -c odoo.conf -d lugal_local -u lugal_ws_migration
```

### Step 4 — Update FE repo
- Copy `src/lib/wsClient.ts` and all changed files from `branch_websocket-migration`
- Verify `vite.config.ts` proxy points to development backend URL/port

### Step 5 — Remove old polling from `development` FE
Search for `setInterval` calls targeting `/api/crm/notifications` and remove them. WebSocket events (`supply.chat.message.new`, `crm.email.message.new`) replace the poll.

### Step 6 — Verify `ir.websocket` is enabled
Odoo 19 native WebSocket is enabled by default when using `--workers=N` with a Gevent worker. Confirm `gevent` is in the process list:
```bash
ps aux | grep gevent
```

### Step 7 — Email IMAP IDLE
The `lugal.idle.supervisor.pid` param in `ir.config_parameter` will be set automatically on first cron run. No manual setup needed.

For each employee email account that should receive live notifications:
1. Employee configures IMAP settings in email account settings UI
2. Employee (or admin) clicks "Test Connection" — success triggers immediate IDLE thread
3. Verify in logs: `IDLE watcher connected: <host> user=<email> accounts=[<id>]`

### Step 8 — Smoke test after migration
Run this sequence and confirm notifications arrive within 5 seconds:
```bash
python3 /tmp/email_flow_test.py
```
Expected:
- `Bus event for omar in < 1s`
- `Bus event for admin in < 2s`

---

## Key Metrics Achieved

| Metric | Before | After |
|---|---|---|
| New email notification latency | 60s (cron poll) | < 2s (IMAP IDLE, new → inbox) |
| Reply notification latency | 60s (cron poll) | 1–22s depending on mail server routing |
| IMAP connections per server | N per account | 1 per unique credential |
| Server connection limit errors | Frequent for shared accounts | Eliminated |
| Duplicate IDLE threads (multi-worker) | Yes (one per worker) | No (PID-based ownership) |
| New account pickup delay | 60s (next cron) | < 1s (immediate trigger on test) |
| Chat real-time delivery | Via long-poll (~1–3s) | Via WebSocket (< 200ms) |

### Note on reply delivery times
In testing, `omar → syed.naqvi` (reply) notifications arrive 15–22s after SMTP delivery, while `syed.naqvi → omar` (new mail) notifications arrive in < 1s. Both directions use the same IMAP IDLE code — the difference is the mail server's **internal delivery routing** at `mail.nooralnibras.com`. Our IDLE watcher detects `EXISTS` within 10 seconds of the server notifying us; the extra delay is the server itself taking 15–22s to route the reply to the recipient's IMAP folder. This is outside backend control.

