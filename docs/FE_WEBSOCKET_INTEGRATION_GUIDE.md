# Frontend WebSocket Integration Guide
## Lugal CRM — Real-time Connection Setup

**Version:** 3.1 — critical live-connection fixes  
**Branch:** `branch_websocket-migration`  
**Sandbox DB:** `lugal_ws_sandbox`  
**Backend host:** `192.168.116.204` (Linux server)  
**Status:** WS flag is **ON** — WebSocket is active on the sandbox right now

---

## 🚨 MUST READ BEFORE ANYTHING ELSE — WHY MESSAGES ARE NOT ARRIVING

If you have implemented the WebSocket but **chat messages are not arriving in real-time** (they only appear after a list-API poll), **you have this bug**:

```javascript
// ❌ WRONG — this will silently connect as an anonymous/guest user.
//    The session_id cookie is bound to your Vite host (e.g. 192.168.116.229:5174).
//    Sending it to a DIFFERENT host (192.168.116.204) is blocked by the browser
//    same-site cookie policy. Odoo receives no cookie → authenticates as public user
//    → subscribes to ZERO channels → you receive ZERO events.
const ws = new WebSocket("ws://192.168.116.204:8076/websocket");

// ✅ CORRECT — always use window.location.host (your Vite dev server).
//    Vite proxies this to ws://192.168.116.204:8076/websocket and forwards
//    the cookie. Odoo sees the cookie, authenticates as the real user,
//    subscribes to all their supply_chat.* channels, messages flow.
const proto = location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${proto}://${location.host}/websocket`);
```

> **The Vite proxy MUST have `ws: true`** for the `/websocket` path — see [Section 3](#3-vite-config--required-proxy-setup).

### What changed in v3.1 — session cookie is now automatic

The `/api/crm/ws/session` endpoint now returns a **`Set-Cookie`** header.  
You **no longer need** `document.cookie = "session_id=..."` — the browser sets it automatically.  
Step 4 in the connection flow is now optional (but harmless if you keep it).

---

## Table of Contents

1. [Sandbox Server Endpoints](#1-sandbox-server-endpoints)
2. [How The Real-Time System Works](#2-how-the-real-time-system-works)
3. [Vite Config — Required Proxy Setup](#3-vite-config--required-proxy-setup)
4. [Login Flow — Correct Endpoint](#4-login-flow--correct-endpoint)
5. [Step-by-Step Connection Flow](#5-step-by-step-connection-flow)
6. [Message Protocol — Exact Format](#6-message-protocol--exact-format)
7. [All Push Event Types & Payloads](#7-all-push-event-types--payloads)
8. [Delivery and Read Ticks — How They Work](#8-delivery-and-read-ticks--how-they-work)
9. [Pin / Unpin Messages — New API](#9-pin--unpin-messages--new-api)
10. [Complete BusClient Implementation](#10-complete-busclient-implementation)
11. [Startup Router — Feature Flag](#11-startup-router--feature-flag)
12. [Notification Badge Logic](#12-notification-badge-logic)
13. [WebSocket Close Codes — Full Reference](#13-websocket-close-codes--full-reference)
14. [Multi-Tab Deduplication](#14-multi-tab-deduplication)
15. [Testing Checklist](#15-testing-checklist)
16. [Troubleshooting](#16-troubleshooting)
17. [Quick Reference Card](#17-quick-reference-card)

---

## 1. Sandbox Server Endpoints

The backend runs on a **Linux server at `192.168.116.204`**. If your Vite dev server is on Windows, `localhost` does not reach the backend — use the IP below in all proxy configurations.

| Purpose | Address |
|---------|---------|
| HTTP API (all existing endpoints) | `http://192.168.116.204:8075` |
| WebSocket gevent worker | `ws://192.168.116.204:8076` |
| WebSocket via Vite proxy (what your code uses) | `ws://localhost:5174/websocket` |
| Database | `lugal_ws_sandbox` |
| Required header on every HTTP API call | `X-Odoo-Database: lugal_ws_sandbox` |

> **In production** Nginx proxies `wss://yourdomain.com/websocket` → port 8076. The frontend code uses `location.host` so no URL change is needed between dev and prod.

---

## 2. How The Real-Time System Works

### What changed and what didn't

| Aspect | Before (Long-Poll) | After (WebSocket) |
|--------|-------------------|-------------------|
| Protocol | `POST /web/bus/poll` every ~1s | One persistent TCP connection |
| Latency | Up to 1 second | Under 50ms |
| DB load at idle | 1 SELECT/user/second | Zero |
| Auth | JWT Bearer only | JWT → session bridge → cookie |
| All existing HTTP APIs | Unchanged ✅ | Unchanged ✅ |
| All event types and payloads | Unchanged ✅ | Unchanged ✅ |

**Nothing about how you call the chat, email, or stories APIs changes.** Only the real-time delivery channel changes.

### Channel architecture

One WebSocket connection per user — the backend automatically subscribes to all channels on connect:

```
WebSocket /websocket
  ├── supply_chat.<conv_id>     ← messages, edits, deletes, reactions, typing, pin/unpin
  ├── supply_chat.<conv_id_2>   ← one channel per active conversation
  ├── supply_user.<uid>         ← delivery/read receipts, story views, email notifications
  └── supply_stories            ← story created/deleted broadcasts
```

The **backend builds this list automatically** when you subscribe. Send an **empty `channels` array** — the backend fills in everything. You never need to manage channel IDs on the FE side.

---

## 3. Vite Config — Required Proxy Setup

> ⚠️ **Critical:** The backend is on a Linux machine at `192.168.116.204`. Using `localhost` in proxy targets will silently fail on Windows because `localhost:8075` on Windows has nothing listening.

```typescript
// vite.config.ts

import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://192.168.116.204:8075',
        changeOrigin: true,
      },
      '/lugal': {
        target: 'http://192.168.116.204:8075',
        changeOrigin: true,
      },
      '/web': {
        target: 'http://192.168.116.204:8075',
        changeOrigin: true,
      },

      // WebSocket proxy — required for WS connection
      '/websocket': {
        target: 'ws://192.168.116.204:8076',
        ws: true,           // tells Vite to handle the WS upgrade
        changeOrigin: true,
      },
    },
  },
});
```

After this, `BusClient` always uses a relative URL — no IP or port hardcoded in JS:

```typescript
const proto = location.protocol === 'https:' ? 'wss' : 'ws';
const WS_URL = `${proto}://${location.host}/websocket`;
// → ws://localhost:5174/websocket in dev (Vite proxies to 192.168.116.204:8076)
// → wss://yourdomain.com/websocket in production (Nginx proxies to port 8076)
```

### Verify proxy is working (from Windows terminal)

```powershell
# Should return JSON with a token — confirms the proxy reaches the backend
curl http://localhost:5174/lugal/auth/login `
  -H "Content-Type: application/json" `
  -H "X-Odoo-Database: lugal_ws_sandbox" `
  -d '{"jsonrpc":"2.0","method":"call","id":1,"params":{"username":"admin","password":"admin"}}'
```

---

## 4. Login Flow — Correct Endpoint

> ⚠️ Do **not** call `POST /web/session/authenticate`. That is Odoo's built-in login — it does not issue JWTs and is not compatible with this app's auth system.

### Correct login request

```
POST /lugal/auth/login
Content-Type: application/json
X-Odoo-Database: lugal_ws_sandbox

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "username": "admin",
    "password": "admin"
  }
}
```

### Login response

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "token_type": "Bearer",
      "user": {
        "id": 2,
        "name": "Admin",
        "login": "admin"
      }
    }
  }
}
```

The `user` object may return either `login` or `username` — your mapper should accept both.

### Token storage

| Store key | Value |
|-----------|-------|
| `tokenForCrm` | `access_token` |
| `posAccessToken` | `access_token` |
| `posRefreshToken` | `refresh_token` |

### After login — add `X-Odoo-Database` to all API clients

Every Axios client and every `fetch` call must include:

```
X-Odoo-Database: <import.meta.env.VITE_API_DB>
```

Never hardcode the database name. Always read it from `VITE_API_DB`.

---

## 5. Step-by-Step Connection Flow

```
Step 1 ── Login
          POST /lugal/auth/login  →  access_token stored

Step 2 ── Check WS flag (once per page load — result is cached)
          GET /api/crm/ws/config
          Header: Authorization: Bearer <access_token>
          Header: X-Odoo-Database: <VITE_API_DB>
          ↓
          { "use_websocket": true }   ← proceed with WebSocket
          { "use_websocket": false }  ← fall back to long-poll (no action needed)

Step 3 ── Exchange JWT for Odoo session (session bridge)
          POST /api/crm/ws/session
          Header: Authorization: Bearer <access_token>
          Header: Content-Type: application/json
          Header: X-Odoo-Database: <VITE_API_DB>
          Body: {}
          ↓
          Response includes Set-Cookie: session_id=<sid>; Path=/; HttpOnly; SameSite=Lax
          AND body: { "success": true, "data": { "session_id": "abc123", "expires_in": 3600 } }

Step 4 ── (Optional) Verify the cookie was set
          // The Set-Cookie header does it automatically — no document.cookie needed.
          // Only add this if your axios/fetch config strips cookies for some reason:
          // document.cookie = "session_id=abc123; path=/; SameSite=Lax"

Step 5 ── Open WebSocket — MUST go through Vite proxy, NOT direct to port 8076
          const proto = location.protocol === 'https:' ? 'wss' : 'ws';
          const ws = new WebSocket(`${proto}://${location.host}/websocket`);
          //
          // When accessed via http://192.168.116.229:5174/ :
          //   → ws://192.168.116.229:5174/websocket  (Vite proxies)
          //   → ws://192.168.116.204:8076/websocket   (backend)
          //   Cookie is forwarded by Vite → Odoo authenticates as real user ✅
          //
          // ❌ NEVER do: new WebSocket("ws://192.168.116.204:8076/websocket")
          //    → cookie is NOT sent (cross-origin) → public user → no channels → no events

Step 6 ── On ws.onopen → send subscribe frame IMMEDIATELY
          ws.send(JSON.stringify({
            event_name: "subscribe",   ← MUST be "event_name" (not "event_type")
            data: {
              channels: [],            ← ALWAYS send empty — backend builds the full list
              last: 0                  ← MUST be "last" (not "last_notification_id")
            }
          }))

Step 7 ── Listen for push events in ws.onmessage
          Events arrive as JSON text frames — always an array

Step 8 ── On ws.onclose → reconnect with exponential backoff
          Exception: code 1000 → do NOT reconnect (intentional close)
          Exception: code 4001 → refresh session first (Step 3-4), then reconnect

Step 9 ── When a new conversation is created → re-subscribe
          ws.send(JSON.stringify({
            event_name: "subscribe",
            data: { channels: [], last: <current_lastId> }
          }))
          Backend adds the new channel automatically

Step 10 ── On logout
           ws.close(1000, "user_logout")
           Do NOT reconnect after close code 1000
```

---

## 6. Message Protocol — Exact Format

### FE → Server (subscribe frame — the only message you send)

```json
{
  "event_name": "subscribe",
  "data": {
    "channels": [],
    "last": 0
  }
}
```

| Field | Type | Notes |
|-------|------|-------|
| `event_name` | `string` | Must be exactly `"subscribe"` |
| `data.channels` | `array` | **Always `[]`** — backend builds all channels server-side |
| `data.last` | `number` | Last bus notification ID seen. `0` on first connect. Update on every received event so reconnects replay missed messages. |

> ⚠️ **These field names are exact — wrong names = silent connection with zero events:**
> - `event_name` — not `event_type`
> - `last` — not `last_notification_id`

### Server → FE (push notification array)

The server always pushes an **array**. Never assume a single object.

```json
[
  {
    "id": 1042,
    "message": {
      "type": "supply.chat.message.new",
      "payload": { ...event-specific fields... }
    }
  }
]
```

Always:
- Sort by `id` ascending before processing
- Track `lastId = Math.max(lastId, n.id)` on every event
- Deduplicate by `id` (see Section 14)

### Full message object shape (returned in most chat event payloads)

```json
{
  "id": 247,
  "thread_id": 28,
  "conversation_type": "dm",
  "sender_id": 2,
  "sender_name": "Admin",
  "sender_avatar": "/web/image/res.users/2/avatar_128",
  "participant_ids": [2, 38],
  "content": "Hello!",
  "kind": "text",
  "duration_seconds": 0,
  "attachments": [],
  "created_at": "2026-04-21T19:32:39",
  "edited_at": null,
  "reply_to_id": null,
  "reply_to_content": null,
  "reply_to_sender": null,
  "reactions": {},
  "is_deleted": false,
  "is_pinned": false,
  "pinned_at": null,
  "pinned_by_id": null,
  "delivery_state": "sent",
  "delivered_to": [],
  "read_by": []
}
```

`kind` values: `"text"` | `"image"` | `"video"` | `"audio"` | `"voice"` | `"file"`

---

## 7. All Push Event Types & Payloads

### Chat events

| `message.type` | Channel | Trigger |
|----------------|---------|---------|
| `supply.chat.message.new` | `supply_chat.<id>` | New message sent |
| `supply.chat.message.updated` | `supply_chat.<id>` | Message edited (within 5-minute window) |
| `supply.chat.message.deleted` | `supply_chat.<id>` | Message deleted for everyone |
| `supply.chat.message.reaction.changed` | `supply_chat.<id>` | Emoji added or removed |
| `supply.chat.message.pinned` | `supply_chat.<id>` | Message pinned or unpinned |
| `supply.chat.typing.start` | `supply_chat.<id>` | Participant started typing |
| `supply.chat.typing.stop` | `supply_chat.<id>` | Participant stopped / 8s auto-stop fired |
| `supply.chat.message.delivered` | `supply_user.<sender_uid>` | Recipient called `/messages/<id>/delivered` |
| `supply.chat.message.read` | `supply_user.<sender_uid>` | Recipient called `/messages/<id>/read` or `/conversations/<id>/mark_read` |

#### `supply.chat.message.new` payload
Full message object (see Section 6 for all fields). `delivery_state` = `"sent"` on arrival.

#### `supply.chat.message.updated` payload
Full message object with updated `content` and `edited_at`.

#### `supply.chat.message.deleted` payload
```json
{
  "message_id": 247,
  "conversation_id": 28,
  "deleted_by": 2,
  "scope": "for_everyone"
}
```

#### `supply.chat.message.pinned` payload
```json
{
  "message_id": 247,
  "conversation_id": 28,
  "is_pinned": true,
  "pinned_by_id": 2,
  "pinned_at": "2026-04-21T21:06:12",
  "message": { ...full message object... }
}
```
When `is_pinned` is `false`, `pinned_at` and `pinned_by_id` are `null` — an unpin event.

#### `supply.chat.message.delivered` payload
```json
{
  "message_id": 247,
  "conversation_id": 28,
  "delivery_state": "delivered",
  "delivered_to": [38]
}
```

#### `supply.chat.message.read` payload (single message read)
```json
{
  "message_id": 247,
  "conversation_id": 28,
  "delivery_state": "read",
  "read_by": [38]
}
```

#### `supply.chat.message.read` payload (conversation mark-all-read)
```json
{
  "conversation_id": 28,
  "read_by_uid": 38,
  "message_ids": [245, 246, 247]
}
```

#### `supply.chat.typing.start` / `.stop` payload
```json
{
  "conversation_id": 28,
  "user_id": 38,
  "user_name": "Omar",
  "is_typing": true
}
```

### Stories events

| `message.type` | Channel | Key payload fields |
|----------------|---------|-------------------|
| `supply.story.new` | `supply_stories` | Full story object (id, author_id, kind, caption, media_url, view_count, expires_at) |
| `supply.story.deleted` | `supply_stories` | `{ story_id, author_id }` |
| `supply.story.viewed` | `supply_user.<author_uid>` | `{ story_id, viewer_id, viewer_name, view_count }` |

> `supply.story.viewed` only arrives for the **story author** — use it to update the view count in their "My Stories" UI. All other users do not receive this event.

### Email events

| `message.type` | Channel | Payload |
|----------------|---------|---------|
| `crm.email.message.new` | `supply_user.<uid>` | `{ message_id, account_id, subject, from_name, from_address, received_at }` |

---

## 8. Delivery and Read Ticks — How They Work

> ⚠️ **This is commonly misunderstood.** The backend does NOT automatically fire delivered/read events when a message arrives. The FE must explicitly call HTTP endpoints to trigger them.

### Tick states

| `delivery_state` | UI display |
|-----------------|------------|
| `"sent"` | Single grey tick ✓ |
| `"delivered"` | Double grey tick ✓✓ |
| `"read"` | Double colored tick ✓✓ |

### What you must do to move ticks

**Step 1 — Mark delivered** (call this when a new message arrives via WebSocket for the current user)

```
POST /api/crm/supply/messages/<message_id>/delivered
Content-Type: application/json
Authorization: Bearer <token>
X-Odoo-Database: <VITE_API_DB>

{ "jsonrpc": "2.0", "method": "call", "id": 1, "params": {} }
```

This publishes `supply.chat.message.delivered` on the **sender's** `supply_user.<uid>` channel.  
The sender's FE receives it and updates the tick from single → double grey.

**Step 2 — Mark read** (call this when the user opens/views the conversation)

Option A — single message:
```
POST /api/crm/supply/messages/<message_id>/read
Content-Type: application/json
Authorization: Bearer <token>
X-Odoo-Database: <VITE_API_DB>

{ "jsonrpc": "2.0", "method": "call", "id": 1, "params": {} }
```

Option B — mark all messages in a conversation as read (recommended when opening a conversation):
```
POST /api/crm/supply/conversations/<conv_id>/mark_read
Content-Type: application/json
Authorization: Bearer <token>
X-Odoo-Database: <VITE_API_DB>

{ "jsonrpc": "2.0", "method": "call", "id": 1, "params": {} }
```

Both options publish `supply.chat.message.read` on the **sender's** `supply_user.<uid>` channel.  
The sender's FE receives it and updates the tick from double grey → double colored.

### Recommended implementation pattern

```typescript
// In your message dispatcher — when a new message arrives via WS:
case 'supply.chat.message.new':
  addMessageToConversation(payload);

  // If this message was sent to us (not by us), mark it delivered immediately
  if (payload.sender_id !== currentUserId) {
    incrementBadge(1);
    markMessageDelivered(payload.id); // fire-and-forget HTTP call
  }
  break;

// In your conversation open/focus handler:
function onConversationOpened(convId: number): void {
  markConversationRead(convId); // POST /conversations/<id>/mark_read
  resetBadgeForConversation(convId);
}

async function markMessageDelivered(messageId: number): Promise<void> {
  await crmPost(`/api/crm/supply/messages/${messageId}/delivered`, {});
}

async function markConversationRead(convId: number): Promise<void> {
  await crmPost(`/api/crm/supply/conversations/${convId}/mark_read`, {});
}
```

---

## 9. Pin / Unpin Messages — New API

A complete pin system has been added. All endpoints are JSON-RPC.

### Pin or unpin a message

```
POST /api/crm/supply/messages/<message_id>/pin
Content-Type: application/json
Authorization: Bearer <token>
X-Odoo-Database: <VITE_API_DB>

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "pin": true
  }
}
```

`pin: false` to unpin. Any conversation participant can pin or unpin.

**Response:** Full updated message object (with `is_pinned`, `pinned_at`, `pinned_by_id` fields).

**Bus event fired:** `supply.chat.message.pinned` on `supply_chat.<conv_id>` — all participants receive it in real time via WebSocket.

### Fetch all pinned messages in a conversation

```
POST /api/crm/supply/conversations/<conv_id>/pinned
Content-Type: application/json
Authorization: Bearer <token>
X-Odoo-Database: <VITE_API_DB>

{ "jsonrpc": "2.0", "method": "call", "id": 1, "params": {} }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [ ...array of pinned message objects, newest pin first... ]
  }
}
```

Use this endpoint to populate a "Pinned messages" panel when a user opens it. After that, listen to `supply.chat.message.pinned` WS events to keep the list updated in real time.

---

## 10. Complete BusClient Implementation

```typescript
// src/shared/realtime/BusClient.ts

export type EventDispatcher = (type: string, payload: unknown) => void;

export class BusClient {
  private ws: WebSocket | null = null;
  private lastId = 0;
  private backoff = 1_000;
  private seenIds = new Set<number>();
  private sessionId: string | null = null;
  private sessionExpiresAt = 0;
  private stopped = false;

  constructor(private readonly dispatch: EventDispatcher) {}

  // ── Public API ────────────────────────────────────────────────────

  async connect(): Promise<void> {
    this.stopped = false;
    await this._ensureSession();
    this._openSocket();
  }

  /**
   * Call immediately after a new DM or group conversation is created.
   * The backend adds the new supply_chat.<id> channel automatically.
   */
  resubscribe(): void {
    this._sendSubscribe();
  }

  disconnect(): void {
    this.stopped = true;
    this.ws?.close(1000, 'user_logout');
    this.ws = null;
  }

  markSeen(id: number): void {
    this.seenIds.add(id);
  }

  // ── Session Bridge ────────────────────────────────────────────────

  private async _ensureSession(): Promise<void> {
    if (this.sessionId && Date.now() < this.sessionExpiresAt - 60_000) return;

    const jwt = this._getJwt();
    const res = await fetch('/api/crm/ws/session', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${jwt}`,
        'Content-Type': 'application/json',
        'X-Odoo-Database': import.meta.env.VITE_API_DB,
      },
      body: '{}',
    });

    if (!res.ok) throw new Error(`WS session bridge HTTP ${res.status}`);
    const json = await res.json();
    if (!json.success) throw new Error(`Session bridge: ${json.error}`);

    this.sessionId = json.data.session_id;
    this.sessionExpiresAt = Date.now() + json.data.expires_in * 1_000;
    document.cookie = `session_id=${this.sessionId}; path=/; SameSite=Strict`;
  }

  // ── WebSocket ─────────────────────────────────────────────────────

  private _openSocket(): void {
    if (this.stopped) return;
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    this.ws = new WebSocket(`${proto}://${location.host}/websocket`);
    this.ws.onopen    = () => { this._resetBackoff(); this._sendSubscribe(); };
    this.ws.onmessage = (e: MessageEvent) => this._handleMessage(e.data);
    this.ws.onclose   = (e: CloseEvent)   => this._handleClose(e);
    this.ws.onerror   = () => {};
  }

  private _sendSubscribe(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    this.ws.send(JSON.stringify({
      event_name: 'subscribe',   // ← "event_name", NOT "event_type"
      data: {
        channels: [],            // ← always empty — backend fills in all channels
        last: this.lastId,       // ← "last", NOT "last_notification_id"
      },
    }));
  }

  private _handleMessage(raw: string): void {
    let notifications: Array<{ id: number; message: { type: string; payload: unknown } }>;
    try {
      notifications = JSON.parse(raw);
    } catch { return; }
    if (!Array.isArray(notifications)) return;

    notifications
      .sort((a, b) => a.id - b.id)
      .forEach((n) => {
        if (typeof n.id !== 'number') return;

        // Deduplicate within this tab (reconnects can replay recent events)
        if (this.seenIds.has(n.id)) return;
        this.seenIds.add(n.id);

        if (n.id > this.lastId) this.lastId = n.id;

        // Tell other tabs to skip this event
        try {
          new BroadcastChannel('lugal_ws_events').postMessage({ seenId: n.id });
        } catch { /* BroadcastChannel not available — ok to continue without it */ }

        const type    = n?.message?.type;
        const payload = n?.message?.payload;
        if (type) this.dispatch(type, payload);
      });
  }

  // ── Close Code Handling ───────────────────────────────────────────

  private _handleClose(event: CloseEvent): void {
    this.ws = null;
    if (this.stopped) return;

    switch (event.code) {
      case 1000:
        // CLEAN — intentional. Never reconnect.
        return;

      case 4001:
        // SESSION_EXPIRED — must refresh session before reconnecting
        this.sessionId = null;
        this.sessionExpiresAt = 0;
        this._scheduleReconnect(true);
        return;

      case 1001:  // GOING_AWAY — server restarting
      case 1012:  // RESTART
      case 1013:  // TRY_LATER — server under load
      case 4002:  // KEEP_ALIVE_TIMEOUT
      case 4003:  // KILL_NOW
      default:    // 1006 = network drop (no close frame from server)
        this._scheduleReconnect(false);
        return;
    }
  }

  private _scheduleReconnect(refreshSession: boolean): void {
    const delay = this._nextBackoff();
    setTimeout(async () => {
      try {
        if (refreshSession) await this._ensureSession();
        this._openSocket();
      } catch {
        this._scheduleReconnect(true);
      }
    }, delay);
  }

  private _nextBackoff(): number {
    this.backoff = Math.min(this.backoff * 2, 30_000);
    return this.backoff + Math.random() * 1_000;
  }

  private _resetBackoff(): void { this.backoff = 1_000; }

  private _getJwt(): string {
    return localStorage.getItem('access_token') ?? '';
  }
}
```

---

## 11. Startup Router — Feature Flag

The WS flag is currently **ON** in the sandbox. Long-poll code still exists and works as a fallback — it is not deleted.

```typescript
// src/shared/realtime/initRealtime.ts

import { BusClient, EventDispatcher } from './BusClient';

let _configCache: { use_websocket: boolean; fallback_on_error: boolean } | null = null;

export async function fetchWsConfig() {
  if (_configCache) return _configCache;
  try {
    const res = await fetch('/api/crm/ws/config', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token') ?? ''}`,
        'X-Odoo-Database': import.meta.env.VITE_API_DB,
      },
    });
    _configCache = await res.json();
  } catch {
    _configCache = { use_websocket: false, fallback_on_error: true };
  }
  return _configCache!;
}

export async function initRealtime(dispatch: EventDispatcher): Promise<void> {
  const config = await fetchWsConfig();

  if (config.use_websocket) {
    const client = new BusClient(dispatch);
    try {
      await client.connect();
      (window as any).__busClient = client;

      try {
        const bc = new BroadcastChannel('lugal_ws_events');
        bc.onmessage = (e) => client.markSeen(e.data.seenId);
      } catch { /* BroadcastChannel not available */ }

    } catch (err) {
      console.warn('[WS] Connection failed, falling back to long-poll:', err);
      if (config.fallback_on_error) startPolling(dispatch);
    }
  } else {
    startPolling(dispatch);
  }
}

export function onNewConversationCreated(): void {
  (window as any).__busClient?.resubscribe();
}

export function onUserLogout(): void {
  (window as any).__busClient?.disconnect();
  (window as any).__busClient = null;
}
```

### Wire typing-stop on disconnect

If the user is mid-typing when the WS closes, other participants see a stuck typing indicator. Fix:

```typescript
ws.addEventListener('close', () => {
  if (isCurrentlyTyping && activeConversationId) {
    fetch(`/api/crm/supply/conversations/${activeConversationId}/typing`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token') ?? ''}`,
        'Content-Type': 'application/json',
        'X-Odoo-Database': import.meta.env.VITE_API_DB,
      },
      body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: { is_typing: false } }),
    }).catch(() => {});
  }
});
```

---

## 12. Notification Badge Logic

```typescript
// Fetch initial counts once on WS connect — then rely on push events only
async function initBadge(): Promise<void> {
  const res = await crmGet('/api/crm/notifications');
  setBadgeCount(res.data.total_unread);
}

function dispatch(type: string, payload: any): void {
  switch (type) {

    // ── Chat ──────────────────────────────────────────────────────
    case 'supply.chat.message.new':
      addMessageToConversation(payload);
      if (payload.sender_id !== currentUserId) {
        incrementBadge(1);
        markConversationUnread(payload.thread_id);
        // Mark delivered immediately — this fires the delivered tick on sender's screen
        markMessageDelivered(payload.id);
      }
      break;

    case 'supply.chat.message.updated':
      updateMessageInConversation(payload);
      break;

    case 'supply.chat.message.deleted':
      removeMessageFromConversation(payload.message_id, payload.conversation_id);
      break;

    case 'supply.chat.message.reaction.changed':
      updateMessageReactions(payload.message_id, payload.reactions);
      break;

    case 'supply.chat.message.pinned':
      // Update the message's pin state in your cache
      updateMessagePinState(payload.message_id, payload.is_pinned, payload.pinned_at, payload.pinned_by_id);
      // If you have a "pinned messages" panel open, refresh it
      if (isPinnedPanelOpen(payload.conversation_id)) {
        refreshPinnedPanel(payload.conversation_id);
      }
      break;

    case 'supply.chat.typing.start':
      showTypingIndicator(payload.conversation_id, payload.user_id, payload.user_name);
      break;

    case 'supply.chat.typing.stop':
      hideTypingIndicator(payload.conversation_id, payload.user_id);
      break;

    case 'supply.chat.message.delivered':
      // Single tick → double grey tick on sender's message
      updateMessageDeliveryState(payload.message_id, 'delivered');
      break;

    case 'supply.chat.message.read':
      // Double grey tick → double colored tick on sender's message
      if (payload.message_id) {
        updateMessageDeliveryState(payload.message_id, 'read');
      } else if (payload.message_ids) {
        // mark_read bulk event — update all messages in the batch
        payload.message_ids.forEach((id: number) =>
          updateMessageDeliveryState(id, 'read')
        );
      }
      reduceBadgeByConversation(payload.conversation_id);
      break;

    // ── Stories ───────────────────────────────────────────────────
    case 'supply.story.new':
      addStoryToFeed(payload);
      break;

    case 'supply.story.deleted':
      removeStoryFromFeed(payload.story_id);
      break;

    case 'supply.story.viewed':
      // Only arrives for the story author
      updateMyStoryViewCount(payload.story_id, payload.view_count);
      break;

    // ── Email ─────────────────────────────────────────────────────
    case 'crm.email.message.new':
      incrementBadge(1);
      addEmailToInbox(payload); // { subject, from_name, from_address, received_at }
      break;
  }
}
```

---

## 13. WebSocket Close Codes — Full Reference

All codes verified from `addons/bus/websocket.py` (`CloseCode` enum):

| Code | Name | When it fires | FE action |
|------|------|---------------|-----------|
| `1000` | `CLEAN` | Intentional server-side close | **Do NOT reconnect** |
| `1001` | `GOING_AWAY` | Server is restarting | Reconnect with backoff |
| `1006` | *(browser)* | Network drop — no close frame sent | Reconnect with backoff |
| `1012` | `RESTART` | Odoo worker restarted | Reconnect with backoff |
| `1013` | `TRY_LATER` | Server under load / no DB cursor | Reconnect with backoff |
| `4001` | `SESSION_EXPIRED` | Odoo session invalidated | Refresh session (Step 3-4), then reconnect |
| `4002` | `KEEP_ALIVE_TIMEOUT` | Missed PING/PONG | Reconnect with backoff |
| `4003` | `KILL_NOW` | Server-side forced kill | Reconnect with backoff |

### Backoff schedule

```
Attempt 1:  1s  + random jitter (0–1s)
Attempt 2:  2s  + jitter
Attempt 3:  4s  + jitter
Attempt 4:  8s  + jitter
Attempt 5: 16s  + jitter
Attempt 6+: 30s + jitter   (cap — never exceeds 31s)
```

Reset to 1s after a successful connection.

---

## 14. Multi-Tab Deduplication

Each browser tab has its own WebSocket. The same event arrives on every open tab. Without deduplication, the badge would increment once per tab.

The `seenIds` Set in `BusClient` handles dedup **within one tab**. `BroadcastChannel` handles **cross-tab** dedup:

```
Tab A receives bus event id=1042
  → Marks 1042 in seenIds
  → Broadcasts { seenId: 1042 } via BroadcastChannel("lugal_ws_events")
  → Dispatches event → badge +1

Tab B receives bus event id=1042 from its own WS
  → BroadcastChannel listener already called markSeen(1042)
  → seenIds.has(1042) === true → skipped
  → Badge stays the same ✅
```

`BroadcastChannel` is supported in all modern browsers. The code wraps it in `try/catch` — if unavailable, WS still works, just without cross-tab dedup.

---

## 15. Testing Checklist

All tests on `lugal_ws_sandbox` with `ws.rollout.enabled = True` (already set).

### Connection & Auth

- [ ] Vite proxy for `/api`, `/lugal`, `/web` → `http://192.168.116.204:8075`
- [ ] Vite proxy for `/websocket` → `ws://192.168.116.204:8076` with `ws: true`
- [ ] Vite restarted after adding the proxy entry
- [ ] WS URL in code uses `${location.host}` — **NOT hardcoded `192.168.116.204:8076`**
- [ ] In Chrome DevTools Network tab, WebSocket connection is to `ws://192.168.116.229:5174/websocket` (or `localhost:5174`) — NOT to `192.168.116.204:8076`
- [ ] `POST /lugal/auth/login` returns `access_token` and `refresh_token`
- [ ] `GET /api/crm/ws/config` with valid JWT → `{ "use_websocket": true }`
- [ ] `POST /api/crm/ws/session` with valid JWT → `{ success: true, data: { session_id, expires_in: 3600 } }`
- [ ] `new WebSocket("ws://localhost:5174/websocket")` → HTTP 101 in Network tab
- [ ] Subscribe frame visible in Network → WS → Messages: `{ "event_name": "subscribe", "data": { "channels": [], "last": 0 } }`

### Chat Events

- [ ] Send a message via HTTP → WS pushes `supply.chat.message.new` within 50ms
- [ ] **Message appears exactly once** (not twice) — no duplicate in the conversation
- [ ] `delivery_state` in new message = `"sent"`
- [ ] Call `POST /messages/<id>/delivered` → sender receives `supply.chat.message.delivered` → tick goes to double grey
- [ ] Open conversation / call `POST /conversations/<id>/mark_read` → sender receives `supply.chat.message.read` → tick goes to double colored
- [ ] Edit message (within 5 min) → `supply.chat.message.updated` arrives on all participants
- [ ] Edit after 5 min → HTTP returns `{ "code": "EDIT_WINDOW_EXPIRED" }`, no WS event
- [ ] Delete for all → `supply.chat.message.deleted` arrives on all participants
- [ ] Pin message → `supply.chat.message.pinned` with `is_pinned: true` arrives on all participants
- [ ] Unpin message → `supply.chat.message.pinned` with `is_pinned: false` arrives on all participants
- [ ] `POST /conversations/<id>/pinned` returns the list of pinned messages
- [ ] Typing start → `supply.chat.typing.start` on other participants' connections
- [ ] Typing stop (or 8s timeout) → `supply.chat.typing.stop` on other participants' connections

### Stories

- [ ] Post story → all connected users receive `supply.story.new`
- [ ] View story → author only receives `supply.story.viewed` with correct `view_count`
- [ ] Delete story → all connected users receive `supply.story.deleted`

### Reliability

- [ ] Disconnect and reconnect → `last` ID sent in re-subscribe → no missed or duplicate events
- [ ] Close code `4001` → FE refreshes session and reconnects
- [ ] Close code `1013` → FE reconnects with backoff
- [ ] Two tabs open → same event → badge increments once total
- [ ] Create new DM while WS is open → call `onNewConversationCreated()` → messages on that DM arrive in real time
- [ ] Logout → `ws.close(1000, "user_logout")` → no reconnect loop

---

## 16. Troubleshooting

### WS flag check in browser console

Open DevTools → Console, filter for `[BusClient]`:

| Log | Meaning |
|-----|---------|
| `WS flag is off — skipping connection` | Flag is `False` — turn it on (see below) |
| `WS session bridge HTTP 401` | JWT rejected — check `Authorization` header |
| `WS session bridge HTTP 500` | Backend error — check Odoo log |
| *(no log, 101 in WS tab)* | Connected ✅ — check event delivery |

### Turn on WS flag (if it was turned off)

```sql
UPDATE ir_config_parameter SET value = 'True' WHERE key = 'ws.rollout.enabled';
```

Then hard-refresh the browser (config is cached per page load).

### WebSocket opens but no events arrive

**Most common cause: hardcoded WS URL bypasses the Vite proxy and cookie.**

Check **DevTools → Network tab → WS connections**:
- ✅ Connection should be to `ws://192.168.116.229:5174/websocket` (or `localhost:5174`)
- ❌ If you see `ws://192.168.116.204:8076/websocket` — this is the bug. Your code is bypassing the proxy. The session cookie is NOT sent cross-origin. Odoo authenticates you as a guest with zero channels subscribed.

Fix: Change the WS URL to use `${location.host}`:
```javascript
const proto = location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${proto}://${location.host}/websocket`);
```

Also check the subscribe frame in **Network → WS → Messages**:
- Must be: `{ "event_name": "subscribe", "data": { "channels": [], "last": 0 } }`
- Wrong: `event_type` instead of `event_name` → fix field name
- Wrong: `last_notification_id` instead of `last` → fix field name

### Messages appear twice in the conversation

The `supply.chat.message.new` event used to be published to two separate bus entries (one per conversation channel + one per user channel). **This has been fixed in the backend.** If you still see duplicates, check that your local deduplication by `seenIds` (bus notification `id`) is working.

### Ticks never change from single grey (sent)

The FE is not calling the HTTP delivered/read endpoints. See Section 8. The backend does not fire these events automatically — they only fire when the FE explicitly calls them.

### HTTP 404 on `ws://localhost:5174/websocket`

The Vite proxy entry for `/websocket` is missing or Vite was not restarted after adding it. Add to `vite.config.ts` and restart Vite.

### HTTP 400 on WebSocket handshake

Session cookie is missing or invalid. The session bridge (`POST /api/crm/ws/session`) must succeed and the cookie must be set before `new WebSocket(...)` is called.

### 500 error from Vite proxy on login

The proxy target is likely wrong. Verify that `/lugal` in `vite.config.ts` points to `http://192.168.116.204:8075`, **not** `http://localhost:8075`. `localhost` on Windows ≠ the Linux backend machine.

### Badge increments 2× with two tabs open

`BroadcastChannel` dedup is not wired. Ensure:
1. `_handleMessage` in `BusClient` calls `new BroadcastChannel('lugal_ws_events').postMessage({ seenId: n.id })`
2. `initRealtime` listens: `bc.onmessage = (e) => client.markSeen(e.data.seenId)`

---

## 17. Quick Reference Card

```
Sandbox HTTP:    http://192.168.116.204:8075
Sandbox WS:      ws://192.168.116.204:8076/websocket
Vite WS URL:     ws://localhost:5174/websocket  (proxied by Vite)
DB header:       X-Odoo-Database: <import.meta.env.VITE_API_DB>   ← never hardcode

STEP  ENDPOINT                                        METHOD   PURPOSE
───────────────────────────────────────────────────────────────────────
 1    /lugal/auth/login                               POST     Get JWT (username/password)
 2    /api/crm/ws/config                              GET      Check if WS is on
 3    /api/crm/ws/session                             POST     Exchange JWT → session_id
 4    document.cookie = "session_id=<sid>; path=/"            Set cookie before WS open
 5    new WebSocket("ws://localhost:5174/websocket")           Open WS connection
 6    send { event_name:"subscribe", data:{channels:[],last:0} }  Subscribe
 7    ws.onmessage → Array<{id, message:{type,payload}}>       Receive push events
 8    POST /messages/<id>/delivered                   POST     Trigger delivered tick
 9    POST /conversations/<id>/mark_read              POST     Trigger read tick
10    POST /messages/<id>/pin  { pin: true/false }    POST     Pin or unpin a message
11    POST /conversations/<id>/pinned                 POST     Get all pinned messages

SUBSCRIBE FRAME (exact field names — wrong names = silent zero events):
  { "event_name": "subscribe", "data": { "channels": [], "last": <lastId> } }

PUSH FORMAT:
  [ { "id": N, "message": { "type": "supply.chat.message.new", "payload": {...} } } ]

RECONNECT RULES:
  1000 CLEAN          → do NOT reconnect
  4001 SESSION_EXPIRED → refresh session first, then reconnect
  all other codes     → reconnect with exponential backoff (1s → 2s → 4s → 8s → 30s cap)
```

---

*Lugal CRM — FE WebSocket Integration Guide v3.0 | Branch: `branch_websocket-migration` | Sandbox: `lugal_ws_sandbox` | Backend: `192.168.116.204`*
