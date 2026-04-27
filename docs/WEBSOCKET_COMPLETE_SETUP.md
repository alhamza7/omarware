# WebSocket Complete Setup — Lugal CRM
## Email · Chat · Stories · Notifications

**Branch:** `branch_websocket-migration`  
**Sandbox DB:** `lugal_ws_sandbox`  
**Backend:** `192.168.116.204` — HTTP `:8075` · WebSocket `:8076`  
**Last updated:** 2026-04-26

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Changed / Added Files](#2-changed--added-files)
3. [How the WebSocket Connection Works](#3-how-the-websocket-connection-works)
4. [IMAP Email Worker — How It Stays Alive](#4-imap-email-worker--how-it-stays-alive)
5. [All Bus Events & Payloads](#5-all-bus-events--payloads)
6. [All WebSocket-Related API Endpoints](#6-all-websocket-related-api-endpoints)
7. [What the FE Must Do](#7-what-the-fe-must-do)
8. [Known Issues Fixed](#8-known-issues-fixed)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Frontend (React)                                                   │
│                                                                     │
│  RealtimeProvider (mounted at APP ROOT — not inside any page)       │
│    │                                                                │
│    ├── On login:  token stored → useEffect fires → WS opens        │
│    ├── On WS open: subscribe frame sent → events flow in           │
│    ├── On logout: token cleared → useEffect cleanup → WS closed    │
│    └── Handles:  chat · email · stories · notifications            │
└────────────────────────┬────────────────────────────────────────────┘
                         │  wss://host/websocket  (via Vite proxy)
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│  Odoo Gevent Worker  :8076                                          │
│                                                                     │
│  ir.websocket._authenticate()       — validates session cookie      │
│  ir.websocket._build_bus_channel_list()  — builds channel list:    │
│    ├── supply_chat.<conv_id>   (one per active conversation)       │
│    ├── supply_user.<uid>       (per-user: email + receipts)        │
│    └── supply_stories          (global story broadcast)            │
└────────────────────────┬────────────────────────────────────────────┘
                         │  bus.bus._sendone()
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│  Odoo HTTP Workers  :8075                                           │
│                                                                     │
│  ├── lugal_ws_migration         — WS session bridge + flag         │
│  ├── lugal_email / lugal_crm    — REST + JSON-RPC APIs             │
│  └── lugal_auth                 — JWT login/refresh/logout         │
└─────────────────────────────────────────────────────────────────────┘
                         ▲
                         │  IMAP IDLE (persistent daemon threads)
┌────────────────────────┴────────────────────────────────────────────┐
│  IMAP Mail Server  mail.nooralnibras.com:993                        │
│                                                                     │
│  LugalEmailIdleWatcher                                              │
│    ├── One thread per unique (host, port, username)                │
│    ├── IMAP IDLE — instant push on EXISTS                          │
│    ├── 5-second watchdog for new accounts                          │
│    └── 1-minute cron as crash-restart fallback                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Changed / Added Files

### Core WebSocket Layer — `addons/lugal_ws_migration/`

| File | What it does |
|------|-------------|
| `controllers/ws_session.py` | `POST /api/crm/ws/session` — JWT → Odoo session cookie bridge. `GET /api/crm/ws/config` — returns WS flag + ws_url + version. |
| `controllers/push_controller.py` | Web Push (VAPID) subscribe/unsubscribe/public key endpoints. |
| `models/lugal_ir_websocket.py` | Overrides `ir.websocket._authenticate()` to handle stale sessions gracefully. Overrides `_build_bus_channel_list()` to auto-add `supply_chat.*`, `supply_user.<uid>`, `supply_stories` channels on WS connect. |
| `models/lugal_ir_http.py` | Overrides `ir.http._authenticate_explicit()` to handle stale `session_token=None` cookies without crashing. |
| `models/lugal_email_ws.py` | **Changed:** Overrides `lugal.email.message.create()` to push `crm.email.message.new` bus event + Web Push notification. Now includes `unread_count`, `uid`, `mailbox` fields in payload. |
| `models/lugal_push_notification.py` | Sends VAPID Web Push to all subscribed devices for a user. |
| `data/ws_config.xml` | Odoo system parameter `ws.rollout.enabled = True` (controls FE WS vs long-poll). |

---

### Auth Layer — `addons/lugal_auth/`

| File | What changed |
|------|-------------|
| `controllers/auth_controller.py` | **Changed:** Login now calls `_attach_ws_session(uid)` → creates Odoo session + `Set-Cookie` in the login response. Also calls `lugal.email.idle.watcher.start_all()` on login to wake IMAP worker immediately. Refresh also re-attaches WS session. |

---

### Email Layer — `addons/lugal_email/`

| File | What changed |
|------|-------------|
| `controllers/email_controller.py` | **Added:** `GET/PATCH /api/lugal/email/signature` — read/save HTML email signature. **Added:** `POST /api/lugal/email/messages/details` — bulk fetch full body for up to 50 messages. **Added:** `DELETE /api/lugal/email/messages/<id>/permanent` — hard delete from trash. **Added:** `POST /api/lugal/email/messages/bulk_delete` — bulk hard delete from trash (max 50). |
| `controllers/crm_email_controller.py` | **Added:** `POST /api/crm/email/subscribe` — idempotent endpoint to wake IMAP worker; called once after WS connects. **Added:** `POST /api/crm/email/messages/bulk_delete` — CRM-layer bulk permanent delete (was 404). |
| `models/email_idle_watcher.py` | Persistent IMAP IDLE daemon. One thread per credential group. Single-process ownership via PID param. 5-second watchdog. Crash-restart on failure. *(not changed today — was already working)* |
| `models/email_account.py` | IMAP sync logic, `action_sync()`, `unread_count` tracking. *(not changed today)* |

---

### CRM Chat Layer — `addons/lugal_crm/`

| File | What changed |
|------|-------------|
| `controllers/supply_chat_controller.py` | **Fixed:** Typing indicator endpoint (`POST /api/crm/supply/conversations/<id>/typing`) was causing `psycopg2 SerializationFailure` → HTTP 500 under concurrent workers. Fixed by removing all DB writes from the typing handler — now pure bus events + in-memory timers only. |

---

## 3. How the WebSocket Connection Works

### Step-by-step connection flow

```
Step 1 — User logs in
         POST /lugal/auth/login
         ↓ response:
           { access_token, refresh_token, ws_session_id }
           Set-Cookie: session_id=<sid>; Path=/; SameSite=Lax; Max-Age=86400

Step 2 — FE stores token, sets cookie fallback
         localStorage.setItem('tokenForCrm', access_token)
         // If Set-Cookie did not arrive:
         document.cookie = `session_id=${ws_session_id}; path=/; SameSite=Lax`

Step 3 — RealtimeProvider detects accessToken → opens WebSocket
         const proto = location.protocol === 'https:' ? 'wss' : 'ws'
         new WebSocket(`${proto}://${location.host}/websocket`)
         // Goes through Vite proxy → ws://192.168.116.204:8076/websocket
         // Cookie is forwarded by proxy → Odoo authenticates as real user
         //
         // ❌ NEVER: new WebSocket("ws://192.168.116.204:8076/websocket")
         //    cross-origin: cookie NOT sent → public user → no channels → no events

Step 4 — ws.onopen: send subscribe frame IMMEDIATELY
         ws.send(JSON.stringify({
           event_name: "subscribe",    ← must be "event_name"
           data: {
             channels: [],             ← always empty — backend fills the list
             last: 0                   ← must be "last"
           }
         }))
         Backend adds ALL channels automatically:
           supply_chat.<id>  for every active conversation
           supply_user.<uid>
           supply_stories

Step 5 — Call subscribe endpoint once (fire-and-forget)
         POST /api/crm/email/subscribe
         → wakes IMAP worker immediately
         → returns { subscribed: true, accounts: [...] }

Step 6 — Listen on ws.onmessage
         Events arrive as JSON arrays of { type, payload } objects

Step 7 — On ws.onclose (not code 1000)
         Reconnect with exponential backoff
         If code 4001: re-call POST /api/crm/ws/session first, then reconnect

Step 8 — On logout
         ws.close(1000, "user_logout")
         Clear token → RealtimeProvider useEffect cleanup fires → done
```

---

### Vite proxy config (required)

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    port: 5174,
    proxy: {
      '/api':      { target: 'http://192.168.116.204:8075', changeOrigin: true },
      '/lugal':    { target: 'http://192.168.116.204:8075', changeOrigin: true },
      '/web':      { target: 'http://192.168.116.204:8075', changeOrigin: true },
      '/websocket': {
        target: 'ws://192.168.116.204:8076',
        ws: true,           // ← critical
        changeOrigin: true,
      },
    },
  },
});
```

---

### Channel architecture

```
One WebSocket connection per browser tab
  ├── supply_chat.<conv_id>      Messages, edits, deletes, reactions, typing, pins
  ├── supply_chat.<conv_id_2>    One channel per active conversation
  ├── supply_user.<uid>          Email notifications, delivery/read receipts, story views
  └── supply_stories             Story created/deleted broadcasts (all users)
```

Backend builds this list **automatically** on subscribe. FE sends empty `channels: []`.

---

## 4. IMAP Email Worker — How It Stays Alive

The IMAP worker is a **server-side persistent daemon** — not tied to any HTTP request or UI state.

### Persistence mechanisms

| Mechanism | Interval | Purpose |
|---|---|---|
| IMAP IDLE thread | Always running | Instant push when mail server signals EXISTS |
| Watchdog thread | Every 5 s | Picks up newly added email accounts |
| Cron supervisor | Every 1 min | Restarts crashed threads |
| **Login hook** | On login | Wakes supervisor immediately — zero delay |
| **Subscribe endpoint** | After WS connects | FE confirms + wakes supervisor |

### Thread design

- One thread per unique `(imap_host, imap_port, username)` credential group
- Multiple email accounts sharing the same IMAP login share one connection
- Single-process ownership via PID tracking in `ir.config_parameter`
- Smart backoff: auth failure → 60 min, connection limit → 5 min, other → 2 min

### When new email arrives (EXISTS from IMAP server)

```
IMAP IDLE thread receives EXISTS
  ↓
action_sync() called → new lugal.email.message records created
  ↓
lugal.email.message.create() hook fires (lugal_email_ws.py)
  ↓
bus.bus._sendone(f'supply_user.{uid}', 'crm.email.message.new', payload)
  ↓
Odoo gevent worker pushes to all WS connections subscribed to supply_user.<uid>
  ↓
FE receives event → updates badge + shows toast → no page navigation needed
```

---

## 5. All Bus Events & Payloads

### Email

```json
{
  "type": "crm.email.message.new",
  "payload": {
    "uid": 42,
    "message_id": 1337,
    "account_id": 7,
    "mailbox": "INBOX",
    "subject": "Re: Order #1042",
    "from_name": "Ahmed Ali",
    "from": "ahmed@example.com",
    "from_address": "ahmed@example.com",
    "received_at": "2026-04-26T14:00:00+03:00",
    "unread_count": 5
  }
}
```

`unread_count` = total unread inbox messages for this account. Use it to update the badge without an extra API call.

---

### Chat messages

```json
{ "type": "supply.chat.message.new",       "payload": { /* full message object */ } }
{ "type": "supply.chat.message.updated",   "payload": { /* full message object */ } }
{ "type": "supply.chat.message.deleted",   "payload": { "message_id": 247, "conversation_id": 28, "deleted_by": 2, "scope": "for_everyone" } }
{ "type": "supply.chat.message.pinned",    "payload": { "message_id": 247, "conversation_id": 28, "is_pinned": true, "pinned_by_id": 2, "pinned_at": "..." } }
{ "type": "supply.chat.message.delivered", "payload": { "message_id": 247, "conversation_id": 28, "delivery_state": "delivered", "delivered_to": [38] } }
{ "type": "supply.chat.message.read",      "payload": { "message_id": 247, "conversation_id": 28, "delivery_state": "read", "read_by": [38] } }
```

---

### Typing indicators

```json
{ "type": "supply.chat.typing.start", "payload": { "conversation_id": 28, "user_id": 38, "user_name": "Omar", "is_typing": true } }
{ "type": "supply.chat.typing.stop",  "payload": { "conversation_id": 28, "user_id": 38, "user_name": "Omar", "is_typing": false } }
```

Typing is **in-memory only** — no DB writes. Auto-stop fires after 8 s if no heartbeat.

---

### Stories

```json
{ "type": "supply.story.new",     "payload": { /* full story object */ } }
{ "type": "supply.story.deleted", "payload": { "story_id": 10, "author_id": 2 } }
{ "type": "supply.story.viewed",  "payload": { "story_id": 10, "viewer_id": 38, "viewer_name": "Sami", "view_count": 5 } }
```

`supply.story.viewed` only arrives for the **story author**.

---

## 6. All WebSocket-Related API Endpoints

### Session & Config

| Method | URL | Type | Purpose |
|--------|-----|------|---------|
| `POST` | `/lugal/auth/login` | JSON-RPC | Login — returns JWT + `ws_session_id` + `Set-Cookie` |
| `POST` | `/lugal/auth/refresh` | JSON-RPC | Refresh token — also re-attaches WS session |
| `POST` | `/api/crm/ws/session` | HTTP | JWT → Odoo session bridge (fallback only — login now does this automatically) |
| `GET`  | `/api/crm/ws/config`  | HTTP | Returns `{ use_websocket, ws_url, ws_version }` |

### Email Subscribe (new)

| Method | URL | Type | Purpose |
|--------|-----|------|---------|
| `POST` | `/api/crm/email/subscribe` | JSON-RPC | Wake IMAP worker + return monitored accounts. Call once after WS connects. |

### Email Signature (new)

| Method | URL | Type | Purpose |
|--------|-----|------|---------|
| `GET` | `/api/lugal/email/signature` | HTTP | Read current HTML signature |
| `PATCH` | `/api/lugal/email/signature` | HTTP | Save HTML signature — body: `{ "signature": "<html>..." }` |

### Email Bulk Operations (new / fixed)

| Method | URL | Type | Purpose |
|--------|-----|------|---------|
| `POST` | `/api/lugal/email/messages/details` | HTTP | Bulk fetch full body for up to 50 messages — body: `{ "message_ids": [...] }` |
| `DELETE` | `/api/lugal/email/messages/<id>/permanent` | HTTP | Hard delete single message (must be in trash) |
| `POST` | `/api/lugal/email/messages/bulk_delete` | HTTP | Hard delete up to 50 messages from trash |
| `POST` | `/api/crm/email/messages/bulk_delete` | JSON-RPC | Same — CRM layer path (was returning 404) |

### Web Push (existing)

| Method | URL | Type | Purpose |
|--------|-----|------|---------|
| `GET`  | `/api/crm/push/vapid-public-key` | HTTP | Get VAPID public key for push registration |
| `POST` | `/api/crm/push/subscribe`        | HTTP | Register push subscription |
| `POST` | `/api/crm/push/unsubscribe`      | HTTP | Remove push subscription |

---

## 7. What the FE Must Do

### Critical structural fix

`RealtimeProvider` **must be at the app root**, not inside any specific page or route:

```tsx
// src/app/providers/AppProviders.tsx
export function AppProviders({ children }) {
  return (
    <ReduxProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RealtimeProvider>   {/* ← wraps EVERYTHING */}
            {children}
          </RealtimeProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ReduxProvider>
  );
}
```

### `RealtimeProvider` internal logic

```tsx
const accessToken = useSelector(selectAccessToken);

useEffect(() => {
  if (!accessToken) return;   // not logged in — do nothing

  let ws: WebSocket | null = null;
  let destroyed = false;

  async function connect() {
    // Cookie is set by login response automatically.
    // Call ws/session as a safety fallback only.
    try {
      await fetch('/api/crm/ws/session', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Odoo-Database': import.meta.env.VITE_API_DB,
        },
        body: '{}',
        credentials: 'include',
      });
    } catch { /* non-fatal */ }

    if (destroyed) return;

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/websocket`);

    ws.onopen = () => {
      // 1. Subscribe to all channels
      ws!.send(JSON.stringify({
        event_name: 'subscribe',
        data: { channels: [], last: 0 },
      }));

      // 2. Wake IMAP worker (fire-and-forget)
      fetch('/api/crm/email/subscribe', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json',
          'X-Odoo-Database': import.meta.env.VITE_API_DB,
        },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', id: 1, params: {} }),
        credentials: 'include',
      }).catch(() => {});
    };

    ws.onmessage = (e) => {
      const frames = JSON.parse(e.data);
      for (const { type, payload } of frames) {
        handleBusEvent(type, payload);
      }
    };

    ws.onclose = (e) => {
      if (destroyed || e.code === 1000) return;
      setTimeout(connect, Math.min(3000 * 2 ** retries++, 30000));
    };
  }

  connect();
  return () => { destroyed = true; ws?.close(1000, 'provider_unmount'); };

}, [accessToken]);  // ← key dependency: fires on login and logout
```

### Event handler additions needed

```typescript
function handleBusEvent(type: string, payload: any) {

  // ── Email ────────────────────────────────────────────────────────────
  if (type === 'crm.email.message.new') {
    dispatch(setEmailUnreadCount(payload.unread_count));   // badge — no API call needed
    queryClient.invalidateQueries({ queryKey: ['email', 'mailbox', 'inbox'] });
    toast.info(`📧 ${payload.from_name || payload.from_address}`, {
      description: payload.subject,
      duration: 5000,
    });
    return;
  }

  // ── Chat messages ─────────────────────────────────────────────────────
  if (type === 'supply.chat.message.new') { /* existing handler */ }
  if (type === 'supply.chat.message.updated') { /* existing handler */ }
  if (type === 'supply.chat.message.deleted') { /* existing handler */ }
  if (type === 'supply.chat.message.delivered') { /* existing handler */ }
  if (type === 'supply.chat.message.read') { /* existing handler */ }

  // ── Typing ────────────────────────────────────────────────────────────
  if (type === 'supply.chat.typing.start') { /* show typing indicator */ }
  if (type === 'supply.chat.typing.stop')  { /* hide typing indicator */ }

  // ── Stories ───────────────────────────────────────────────────────────
  if (type === 'supply.story.new')     { /* add to stories list */ }
  if (type === 'supply.story.deleted') { /* remove from stories list */ }
  if (type === 'supply.story.viewed')  { /* update view count (author only) */ }
}
```

### Login flow update

```typescript
const result = await loginMutation({ username, password });
const { access_token, refresh_token, ws_session_id } = result.data;

// 1. Store tokens
localStorage.setItem('tokenForCrm', access_token);
dispatch(setTokens({ accessToken: access_token, refreshToken: refresh_token }));

// 2. Cookie fallback (in case proxy stripped Set-Cookie header)
if (ws_session_id && !document.cookie.includes('session_id=')) {
  document.cookie = `session_id=${ws_session_id}; path=/; SameSite=Lax; Max-Age=86400`;
}

// 3. Navigate — RealtimeProvider detects token and opens WS automatically
navigate('/dashboard');
```

---

## 8. Known Issues Fixed

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `POST /api/crm/supply/conversations/<id>/typing` → 500 | `lugal.supply.typing` DB upsert caused `psycopg2 SerializationFailure` under 9 concurrent workers | Removed all DB writes from typing handler — pure bus events + in-memory timers |
| `POST /api/crm/email/messages/bulk_delete` → 404 | Endpoint existed at `/api/lugal/email/...` but FE calls CRM path | Added `POST /api/crm/email/messages/bulk_delete` to `crm_email_controller.py` |
| `PATCH /api/lugal/email/signature` → 404 | Route never existed | Added `GET/PATCH /api/lugal/email/signature` to `email_controller.py` |
| WebSocket 1006 on first connect | WS opened before session cookie was ready | Login now sets cookie synchronously; FE should `await` session setup before opening WS |
| Email notifications only work on email page | `RealtimeProvider` mounted inside email route, not at app root | **FE must fix**: move `RealtimeProvider` to `AppProviders.tsx` |
| IMAP worker starts after up to 5 s delay for new users | Watchdog runs every 5 s | Login now calls `start_all()` immediately |
| `crm.email.message.new` missing `unread_count` | Original payload had only basic fields | Added `unread_count`, `uid`, `mailbox`, `from` to payload |
