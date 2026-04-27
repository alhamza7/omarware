# WebSocket Migration Plan — Lugal CRM
## Long-Poll → Native Odoo 19 WebSocket

**Version:** 2.0 (corrected)
**Branch:** `migration`
**New Addon:** `lugal_ws_migration` (only addon touched on this branch)
**Scope:** Chat · Stories · Email Notifications (Phase 4)
**Omnichannel:** OUT OF SCOPE
**Database:** `lugal_ws_sandbox` — cloned from `lugal_local` (**NEVER connect to `lugal_local`**)

---

## Table of Contents

1. [Red Zone — Absolute Constraints](#1-red-zone--absolute-constraints)
2. [Current System Overview](#2-current-system-overview)
3. [Authentication Flow](#3-authentication-flow)
4. [Channel Architecture](#4-channel-architecture)
5. [Phased Migration Plan](#5-phased-migration-plan)
6. [Testing Scenarios](#6-testing-scenarios)
7. [Definition of Done](#7-definition-of-done)

---

## 1. Red Zone — Absolute Constraints

Every engineer must read and acknowledge this section before writing any code.
Any violation here bleeds into production data and the live SAP sync.

### ⛔ Files That Must NEVER Be Touched on This Branch

| File | Reason |
|------|--------|
| `bus_compat_controller.py` | Live long-poll shim — frozen |
| `addons/lugal_auth/` | JWT auth module — zero modifications |
| `addons/bus/` | Odoo core bus addon — zero modifications |
| `crm_supply_message.py` | Live chat message model |
| `crm_supply_conversation.py` | Live conversation model |
| `crm_supply_story.py` | Live story model |
| `addons/lugal_email/` | Live email addon — read only |
| All existing chat, email, stories, CRM notification, supply controllers | Production APIs |
| All existing `__init__.py` files | Additive imports only — never reorder or remove |
| `nginx/nginx.conf` | Already production-ready — do not touch |

### ⛔ Database Rules

- **NEVER** run `-u` or `-i` against `lugal_local`
- **NEVER** run raw `ALTER TABLE`, `DROP TABLE`, or `DELETE` against `lugal_local`
- ALL migration work runs against `lugal_ws_sandbox` only
- `db_name` in `odoo_ws.conf` must always be `lugal_ws_sandbox`
- `bus_bus` table is untouched — `_sendone()`, `_poll()`, and GC cron are untouched
- No new columns, no schema changes anywhere on `lugal_local`

### ⛔ Channel Namespace Rules During Testing

- Test-only channels must use prefix `ws_test.*`
- Production channel names (`supply_chat.*`, `supply_user.*`, `supply_stories`) are only used in code paths gated behind the feature flag

### ✅ The One Safe Pattern

- One new addon only: `lugal_ws_migration`
- ALL overrides live inside this addon
- This addon is completely inert unless explicitly installed — it does not affect dev or production
- SAP sync has zero intersection with the bus layer — untouched throughout

---

## 2. Current System Overview

### 2.1 What We Are Replacing

The current system uses HTTP short-polling. The FE calls `POST /web/bus/poll` every ~1 second. Each call immediately queries the `bus_bus` PostgreSQL table and returns new rows or `[]`. There is no persistent connection.

| Aspect | Current (Long-Poll) | Target (WebSocket) |
|--------|--------------------|--------------------|
| Protocol | HTTP POST every ~1s | Persistent TCP (WS) |
| Latency | Up to 1 second | Sub-50ms |
| DB queries at idle | 1 SELECT/user/second | Zero |
| Server port | 8070 (HTTP workers) | 8072 (gevent/WS worker) |
| Auth | JWT Bearer (custom) | Session bridge + JWT exchange |
| DB schema changes | N/A | **NONE** |

### 2.2 What Is Already On The Bus

| Source | On Bus Today | Channel | WS Phase |
|--------|-------------|---------|---------|
| Chat messages | ✅ Yes | `supply_chat.<id>` | Phase 1 |
| Delivery/read receipts | ✅ Yes | `supply_user.<uid>` | Phase 1 |
| Stories | ✅ Yes | `supply_stories` + `supply_user.<uid>` | Phase 1 |
| Email new message | ❌ No — needs wiring | `supply_user.<uid>` | Phase 4 |
| Notification badge count | ❌ No — HTTP poll | Derived from events | Phase 1 (derived) |

### 2.3 Infrastructure — Already Production Ready

**Nginx is already fully configured. Zero changes needed.**

File: `nginx/nginx.conf` — the `/websocket` location block is already present and correct:

```nginx
location /websocket {
    proxy_pass http://odoo_longpolling;   # → odoo:8072
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;
    proxy_send_timeout 3600s;
}
```

- `proxy_pass` → `odoo:8072` (gevent/WS worker) ✅
- `proxy_http_version 1.1` + `Upgrade` headers ✅
- 3600s timeout for persistent connections ✅
- `/bus/` long-poll block also present — both modes coexist ✅

**Nginx is NOT a Phase 0 checklist item. Do not touch `nginx/nginx.conf`.**

---

## 3. Authentication Flow

### 3.1 The Problem

Odoo 19's native WebSocket (`ir.websocket._authenticate()`) expects an **Odoo session cookie** (`session_id`). Our entire API uses **JWT Bearer tokens**. We cannot send a JWT in a WebSocket handshake header in a cross-browser compatible way.

### 3.2 The Solution: Session Bridge Endpoint

A new endpoint inside `lugal_ws_migration` exchanges a valid JWT for a short-lived Odoo session. This means `ir.websocket._authenticate()` is **never modified** — it just sees a valid session cookie as it normally would.

**Endpoint:**
```
POST /api/crm/ws/session
Content-Type: application/json
Authorization: Bearer <jwt_token>

Body: {}   ← no body needed, JWT is read from Authorization header
```

**Response:**
```json
{
  "success": true,
  "data": {
    "session_id": "abc123xyz",
    "expires_in": 300
  }
}
```

#### Correct Implementation (fixes Issue 1 from v1)

The endpoint must be `type='http'` (plain HTTP), **not** `type='json'` (JSON-RPC). The existing JWT validator reads from the `Authorization` header directly — no token in the body is needed. This matches how every other JWT-auth endpoint in this codebase works.

```python
# addons/lugal_ws_migration/controllers/ws_session.py
# Additive only. Does not touch lugal_auth/ or any existing controller.

import json
import logging
import secrets
from odoo import http
from odoo.http import request, Response
from odoo.addons.lugal_auth.controllers._auth import ensure_jwt_user_id

_logger = logging.getLogger(__name__)
SESSION_TTL = 300  # 5 minutes


class WsSessionController(http.Controller):

    @http.route('/api/crm/ws/session', type='http', auth='none',
                methods=['POST', 'OPTIONS'], csrf=False, cors='*')
    def get_ws_session(self, **kwargs):
        """
        Exchange a valid JWT Bearer token for a short-lived Odoo session_id.
        The FE sets the returned session_id as a cookie before opening /websocket.
        This allows Odoo's native WebSocket auth to work without any modification.
        """
        def _json(payload, status=200):
            return Response(
                json.dumps(payload), status=status,
                headers=[('Content-Type', 'application/json')]
            )

        if request.httprequest.method == 'OPTIONS':
            return Response(status=204, headers=[
                ('Access-Control-Allow-Origin', '*'),
                ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
                ('Access-Control-Allow-Headers', 'Authorization, Content-Type'),
            ])

        # Validate JWT using existing auth helper — reads from Authorization header
        uid = ensure_jwt_user_id()
        if not uid:
            return _json({'success': False, 'error': 'Unauthorized'}, 401)

        try:
            # Create a real Odoo session for this uid
            session = request.session
            session.uid = uid
            session.db = request.db
            session.login = request.env['res.users'].sudo().browse(uid).login
            request.session.touch()

            return _json({
                'success': True,
                'data': {
                    'session_id': session.sid,
                    'expires_in': SESSION_TTL,
                },
            })
        except Exception as exc:
            _logger.exception('ws_session error: %s', exc)
            return _json({'success': False, 'error': 'Session creation failed'}, 500)
```

### 3.3 Full Auth Sequence — FE Perspective

```
Step 1:  FE already has JWT from existing login flow — unchanged.

Step 2:  POST /api/crm/ws/session
         Header: Authorization: Bearer <jwt>
         Body: {}
         Response: { success: true, data: { session_id: "abc123", expires_in: 300 } }

Step 3:  FE sets cookie:
         document.cookie = `session_id=abc123; path=/; SameSite=Strict`;

Step 4:  FE opens WebSocket:
         const ws = new WebSocket('wss://yourapp.com/websocket');
         (Odoo's WS auth reads session_id cookie automatically — authenticated ✅)

Step 5:  On ws.onopen — send subscribe frame:
         ws.send(JSON.stringify({
           event_type: 'subscribe',
           data: { channels: [], last_notification_id: <lastKnownId or 0> }
         }));
         (FE sends empty channels array — BE builds the full list server-side)

Step 6:  WS connection is live. Events start arriving as push notifications.

Step 7:  On close (network drop, etc.) — reconnect with exponential backoff.
         Session_id cookie still valid for remaining expires_in seconds.
         → Restart from Step 4 only (skip Steps 2-3 until session expires).
         → If close code is 4001 (SESSION_EXPIRED): go back to Step 2 first.

Step 8:  On new conversation created — re-subscribe:
         ws.send(JSON.stringify({
           event_type: 'subscribe',
           data: { channels: [], last_notification_id: <current_last> }
         }));
         BE rebuilds channel list including the new conversation automatically.

Step 9:  On user logout:
         ws.close(1000, 'user_logout');
         Do NOT reconnect.
```

### 3.4 WebSocket Close Codes (Odoo 19 — Verified from Source)

The FE must handle these specific close codes from `addons/bus/websocket.py`:

| Code | Name | FE Action |
|------|------|-----------|
| `1000` | `CLEAN` | Do NOT reconnect — intentional close (logout) |
| `1001` | `GOING_AWAY` | Reconnect — server restart/deploy |
| `1012` | `RESTART` | Reconnect — Odoo worker restart |
| `4001` | `SESSION_EXPIRED` | Re-run session bridge (Step 2), then reconnect |
| `4002` | `KEEP_ALIVE_TIMEOUT` | Reconnect — missed PING/PONG (network issue) |
| `4003` | `KILL_NOW` | Reconnect after backoff — server-side kill |

---

## 4. Channel Architecture

### 4.1 Single Connection, All Sources

One persistent WebSocket connection per user handles chat, stories, and email (Phase 4). No separate connections.

```
WebSocket Connection (/websocket)
  ├── supply_chat.<conv_id_1>    ← new messages, typing, edits, reactions
  ├── supply_chat.<conv_id_2>
  ├── supply_chat.<conv_id_N>
  ├── supply_user.<uid>          ← delivery/read receipts, DMs, story views, email (Phase 4)
  └── supply_stories             ← story new/deleted broadcast
```

### 4.2 Channel Builder — BE Delivers This

Override `_build_bus_channel_list()` inside `lugal_ws_migration`. The existing `/api/crm/supply/chat/bus_channels` HTTP controller is **NOT modified** — the channel-building query logic is replicated in the new model:

```python
# addons/lugal_ws_migration/models/lugal_ir_websocket.py

class LugalIrWebsocket(models.AbstractModel):
    _inherit = 'ir.websocket'

    def _build_bus_channel_list(self, channels):
        result = super()._build_bus_channel_list(channels)
        uid = self.env.uid

        # Only add custom channels for real authenticated users
        public_uid = self.env.ref('base.public_user').id
        if not uid or uid == public_uid:
            return result

        # Add all active supply chat conversations for this user
        Conv = self.env['lugal.supply.conversation'].sudo()
        convs = Conv.search([
            ('is_archived', '=', False),
            ('participant_ids', 'in', [uid]),
        ])
        for conv in convs:
            result.append(f'supply_chat.{conv.id}')

        # Per-user private channel (delivery receipts, read receipts, DMs, email)
        result.append(f'supply_user.{uid}')

        # Global stories broadcast
        result.append('supply_stories')

        return result
```

### 4.3 All Event Types (unchanged from current system)

| Event Type | Channel | Trigger |
|------------|---------|---------|
| `supply.chat.message.new` | `supply_chat.<id>` + `supply_user.<uid>` | New message sent |
| `supply.chat.message.updated` | `supply_chat.<id>` | Message edited |
| `supply.chat.message.deleted` | `supply_chat.<id>` | Message deleted |
| `supply.chat.message.reaction.changed` | `supply_chat.<id>` | Reaction added/removed |
| `supply.chat.typing.start` | `supply_chat.<id>` | User starts typing |
| `supply.chat.typing.stop` | `supply_chat.<id>` | User stops / 8s timer fires |
| `supply.chat.message.delivered` | `supply_user.<sender_uid>` | Recipient calls `/delivered` |
| `supply.chat.message.read` | `supply_user.<sender_uid>` | Recipient calls `/read` |
| `supply.story.new` | `supply_stories` | Story posted |
| `supply.story.deleted` | `supply_stories` | Story expired/deleted |
| `supply.story.viewed` | `supply_user.<author_uid>` | Someone views a story |
| `crm.email.message.new` | `supply_user.<uid>` | New email (Phase 4) |

---

## 5. Phased Migration Plan

---

### Phase 0 — Pre-conditions (Before Writing Any Code)

All items must be confirmed complete before Phase 1 begins. No code is written in Phase 0.

| # | Checklist Item | Owner | Status |
|---|---------------|-------|--------|
| 1 | Clone `lugal_local` into `lugal_ws_sandbox`:<br>`createdb lugal_ws_sandbox && pg_dump lugal_local \| psql lugal_ws_sandbox` | DevOps | [ ] |
| 2 | Create `odoo_ws.conf` — copy of `odoo_local.conf` with **only** `db_name = lugal_ws_sandbox` changed.<br>Migration branch always uses `odoo_ws.conf`. Dev branch always uses `odoo_local.conf`. They never cross. | BE | [ ] |
| 3 | Confirm `lugal_ws_migration` is added to `addons_path` in `odoo_ws.conf`.<br>Without this, `-i lugal_ws_migration` silently does nothing. | BE | [ ] |
| 4 | Scaffold `lugal_ws_migration` addon structure:<br>`__manifest__.py`, `__init__.py`, `models/`, `controllers/` | BE | [ ] |
| 5 | Confirm port 8072 (gevent/WS worker) is reachable from sandbox environment | DevOps | [ ] |
| 6 | All team members have read and acknowledged Section 1 (Red Zone) | All | [ ] |
| 7 | Feature flag config parameter created in sandbox DB:<br>`ws.rollout.enabled = False` (via `ir.config_parameter`) | BE | [ ] |

**⛔ Re-clone Instruction — If Sandbox Gets Into a Bad State:**
```bash
dropdb lugal_ws_sandbox
pg_dump lugal_local | psql lugal_ws_sandbox
```
This resets the sandbox to a clean clone. It does not affect `lugal_local` in any way. Use freely.

---

### Phase 1 — Backend: Session Bridge + Channel Builder

**Scope:** Two new code paths inside `lugal_ws_migration` only. Nothing else changes.

#### 1.1 Create Addon Structure

```
addons/lugal_ws_migration/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   └── lugal_ir_websocket.py      ← _build_bus_channel_list() override
└── controllers/
    ├── __init__.py
    └── ws_session.py              ← POST /api/crm/ws/session
```

**`__manifest__.py`:**
```python
{
    'name': 'Lugal WS Migration',
    'version': '1.0.0',
    'depends': ['bus', 'lugal_crm', 'lugal_auth'],
    'installable': True,
    'auto_install': False,
    'application': False,
}
```

#### 1.2 Session Bridge Endpoint

See full implementation in Section 3.2 above (`ws_session.py`).

#### 1.3 Channel Builder Override

See full implementation in Section 4.2 above (`lugal_ir_websocket.py`).

#### 1.4 Feature Flag Config Endpoint

A lightweight endpoint so the FE can check whether to use WS or long-poll:

```python
# Inside ws_session.py (same controller class)

@http.route('/api/crm/ws/config', type='http', auth='none',
            methods=['GET'], csrf=False, cors='*')
def ws_config(self, **kwargs):
    """Returns whether WebSocket is enabled for this user/session."""
    def _json(payload):
        return Response(json.dumps(payload),
                        headers=[('Content-Type', 'application/json')])
    try:
        uid = ensure_jwt_user_id()
        if not uid:
            return _json({'use_websocket': False, 'fallback_on_error': True})

        ICP = request.env['ir.config_parameter'].sudo()
        enabled = ICP.get_param('ws.rollout.enabled', 'False').lower() == 'true'
        return _json({
            'use_websocket': enabled,
            'fallback_on_error': True,
        })
    except Exception:
        return _json({'use_websocket': False, 'fallback_on_error': True})
```

#### Phase 1 Deliverables Checklist

- [ ] `lugal_ws_migration` installs cleanly into `lugal_ws_sandbox` with no errors
- [ ] `POST /api/crm/ws/session` returns `session_id` for a valid JWT
- [ ] `POST /api/crm/ws/session` returns 401 for invalid/expired JWT
- [ ] `GET /api/crm/ws/config` returns `{ use_websocket: false }` (flag is off)
- [ ] `_build_bus_channel_list()` returns correct channels — verified by opening `/websocket` and inspecting subscription
- [ ] Long-poll via `/web/bus/poll` still works exactly as before — not affected

---

### Phase 2 — Frontend: WebSocket Client

**Scope:** Replace the polling loop with a WebSocket client. Feature flag defaults to off — long-poll runs unchanged for all users until flag is turned on per-user.

#### 2.1 BusClient Class (TypeScript)

```typescript
// src/realtime/BusClient.ts

export class BusClient {
  private ws: WebSocket | null = null;
  private lastId = 0;
  private backoff = 1000;
  private seenIds = new Set<number>();
  private sessionId: string | null = null;
  private sessionExpiresAt = 0;

  constructor(private dispatch: (type: string, payload: any) => void) {}

  async connect(): Promise<void> {
    await this.ensureSession();
    const url = `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/websocket`;
    this.ws = new WebSocket(url);
    this.ws.onopen    = () => { this.resetBackoff(); this.subscribe(); };
    this.ws.onmessage = (e) => this.handleMessage(e);
    this.ws.onclose   = (e) => this.handleClose(e);
    this.ws.onerror   = () => {};  // onclose fires after onerror — handle there
  }

  private async ensureSession(): Promise<void> {
    // Refresh session if it doesn't exist or is about to expire (within 30s)
    if (this.sessionId && Date.now() < this.sessionExpiresAt - 30000) return;

    const jwt = getJwtToken();  // existing auth store
    const res = await fetch('/api/crm/ws/session', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${jwt}`, 'Content-Type': 'application/json' },
      body: '{}',
    });
    const data = await res.json();
    if (!data.success) throw new Error('Session bridge failed');

    this.sessionId = data.data.session_id;
    this.sessionExpiresAt = Date.now() + (data.data.expires_in * 1000);
    document.cookie = `session_id=${this.sessionId}; path=/; SameSite=Strict`;
  }

  private subscribe(): void {
    if (this.ws?.readyState !== WebSocket.OPEN) return;
    this.ws.send(JSON.stringify({
      event_type: 'subscribe',
      data: { channels: [], last_notification_id: this.lastId },
    }));
  }

  resubscribe(): void {
    // Call this when a new conversation is created
    this.subscribe();
  }

  private handleMessage(e: MessageEvent): void {
    const notifications = JSON.parse(e.data);
    if (!Array.isArray(notifications)) return;
    // Sort by id — never assume bus delivery order = chronological order
    notifications
      .sort((a: any, b: any) => a.id - b.id)
      .forEach((n: any) => {
        if (this.seenIds.has(n.id)) return;  // multi-tab dedup
        this.seenIds.add(n.id);
        this.lastId = Math.max(this.lastId, n.id);
        this.dispatch(n.message.type, n.message.payload);
      });
  }

  private handleClose(event: CloseEvent): void {
    // Odoo close codes (verified from addons/bus/websocket.py):
    // 1000 = CLEAN (logout)        → do NOT reconnect
    // 1001 = GOING_AWAY            → reconnect (server restart)
    // 1012 = RESTART               → reconnect (worker restart)
    // 4001 = SESSION_EXPIRED       → refresh session, then reconnect
    // 4002 = KEEP_ALIVE_TIMEOUT    → reconnect (network issue)
    // 4003 = KILL_NOW              → reconnect after backoff

    if (event.code === 1000) {
      return;  // intentional logout — do not reconnect
    }
    if (event.code === 4001) {
      // Session expired — force session refresh before reconnecting
      this.sessionId = null;
      this.sessionExpiresAt = 0;
      const delay = this.nextBackoff();
      setTimeout(() => this.connect(), delay);
      return;
    }
    // All other codes: reconnect with backoff
    const delay = this.nextBackoff();
    setTimeout(() => this.connect(), delay);
  }

  private nextBackoff(): number {
    this.backoff = Math.min(this.backoff * 2, 30000);
    return this.backoff + Math.random() * 1000;  // jitter prevents thundering herd
  }

  private resetBackoff(): void { this.backoff = 1000; }

  disconnect(): void {
    this.ws?.close(1000, 'user_logout');
    this.ws = null;
  }
}
```

#### 2.2 Notification Badge — Initial Load + Real-Time Updates

```typescript
// On WS connect — fetch initial badge count once (then never poll this endpoint again)
const notifState = await get('/api/crm/notifications');
setBadgeCount(notifState.data.total_unread);

// In dispatch() — extend existing handler with badge logic
function dispatch(type: string, payload: any) {
  switch (type) {
    case 'supply.chat.message.new':
      if (payload.sender_id !== currentUserId) {
        incrementBadge(1);
        updateConversationUnread(payload.thread_id);
      }
      break;
    case 'supply.chat.message.read':
      // Sender sees their message was read — clear that conversation's unread
      reduceBadgeByConversation(payload.conversation_id);
      break;
    case 'supply.story.new':
      // Stories do not affect unread badge
      updateStoriesFeed(payload);
      break;
    // Phase 4 — email (add when Phase 4 is deployed)
    // case 'crm.email.message.new':
    //   incrementBadge(1);
    //   addEmailNotificationItem(payload);
    //   break;

    // All existing handlers below — UNCHANGED
    // ...
  }
}
```

#### 2.3 Feature Flag Startup Router

```typescript
// src/realtime/initRealtime.ts

export async function initRealtime(dispatch: Function): Promise<void> {
  const config = await get('/api/crm/ws/config');

  if (config.use_websocket) {
    const client = new BusClient(dispatch);
    try {
      await client.connect();
      window.__busClient = client;  // expose for resubscribe calls on new conversation
    } catch (e) {
      if (config.fallback_on_error) {
        console.warn('[WS] Connection failed — falling back to long-poll');
        startPolling(dispatch);  // existing polling code — completely untouched
      }
    }
  } else {
    startPolling(dispatch);  // existing polling code — completely untouched
  }
}
```

#### 2.4 Typing Stop on Disconnect

```typescript
// In the component / hook that manages typing state:
ws.addEventListener('close', () => {
  if (isTyping) {
    // Fire-and-forget HTTP call — WS is gone so we can't send via bus
    crmPost(`/api/crm/supply/conversations/${activeConvId}/typing`, { is_typing: false });
  }
});
```

#### Phase 2 Deliverables Checklist

- [ ] `BusClient` class implemented — connect, subscribe, handleMessage, all close code cases, backoff, dedup
- [ ] `initRealtime()` startup router — flag off by default, polls as normal
- [ ] Notification badge: HTTP fetch on connect, real-time increment/decrement from WS events
- [ ] `dispatch()` extended — all existing cases untouched, new cases added for badge
- [ ] `resubscribe()` wired to new conversation creation flow
- [ ] Typing stop sent immediately on `ws.onclose`
- [ ] Long-poll path fully regression tested — no behaviour change when flag is off

---

### Phase 3 — Parallel Run & Gradual Rollout

Both systems run simultaneously. The feature flag controls rollout. Long-poll stays fully functional throughout.

| Rollout Stage | Who Is On WebSocket | Criteria to Proceed |
|---------------|--------------------|--------------------|
| Stage 0 | No one (flag off) | Phases 1 and 2 complete, all Phase 1 deliverables checked |
| Stage 1 | Internal team only (specific UIDs) | Session bridge + channel builder confirmed on sandbox |
| Stage 2 | 5% of users | Internal team: 3 days clean, no reported issues |
| Stage 3 | 25% of users | 5% stable for 3 days |
| Stage 4 | 100% of users | 25% stable for 5 days, all test scenarios in Section 6 passed |

**Rollback at Any Stage:**
Set `ws.rollout.enabled = False` in `ir.config_parameter`.
All users immediately fall back to long-poll. No code change, no deployment, no data impact.
`bus_compat_controller.py` is always live and untouched.

---

### Phase 4 — Email Bus Wiring

**Scope:** Wire new email arrival events to the bus so the FE badge updates in real time.
Small isolated addition inside `lugal_ws_migration`. No existing email code is modified.

#### Correct Implementation (fixes Issue 2 from v1)

The original plan used `record.user_id` and `record.email_from` — these fields do not exist on `lugal.email.message`. The correct path is `record.account_id.user_id.id` (through the account) and the field is `from_address`:

```python
# addons/lugal_ws_migration/models/lugal_email_ws.py

class LugalEmailMessageWs(models.Model):
    _inherit = 'lugal.email.message'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # Only notify for inbox messages that are unread
            if record.folder == 'inbox' and not record.is_read:
                # Correct path: account_id → user_id
                # lugal.email.message has no direct user_id field
                uid = record.account_id.user_id.id if record.account_id else None
                if uid:
                    try:
                        self.env['bus.bus'].sudo()._sendone(
                            f'supply_user.{uid}',
                            'crm.email.message.new',
                            {
                                'message_id':    record.id,
                                'account_id':    record.account_id.id,
                                'subject':       record.subject or '(no subject)',
                                'from_name':     record.from_name or '',
                                'from_address':  record.from_address or '',  # correct field name
                                'received_at':   record.date.isoformat() if record.date else None,
                            }
                        )
                    except Exception as exc:
                        _logger.debug('email bus notify error: %s', exc)
        return records
```

#### Phase 4 Deliverables Checklist

- [ ] `lugal_email_ws.py` created inside `lugal_ws_migration` — zero changes to `addons/lugal_email/`
- [ ] `crm.email.message.new` event arrives on `supply_user.<uid>` channel via WS
- [ ] FE `dispatch()` handles `crm.email.message.new` — badge increments correctly
- [ ] Email mark-read flow still uses existing HTTP endpoint — no change
- [ ] Confirmed: IMAP sync cron not modified, `lugal_email_message` table not modified
- [ ] Event does NOT fire for sent/drafts/trash folders — inbox only

---

### Phase 5 — Long-Poll Removal

**Only executed after 100% rollout has been stable for a minimum of 14 days with zero reported real-time issues.**

**⛔ Do Not Proceed Until ALL of the Following Are True:**

- [ ] Network tab shows exactly 1 WebSocket connection per user — zero poll requests
- [ ] A user has stayed connected for 8+ hours without missing an event
- [ ] Disconnect/reconnect correctly replays missed events using `last_notification_id`
- [ ] 100% rollout stable for 14 consecutive days
- [ ] Zero chat, story, or notification bug reports linked to real-time delivery
- [ ] All test scenarios in Section 6 have been run and passed

**When all the above are confirmed, the following can be removed:**

```
src/realtime/startPolling()         — the polling loop function
The else branch in initRealtime()   — that calls startPolling()
bus_compat_controller.py            — or keep it for legacy API consumers (recommended)
ws.rollout.enabled config param     — feature flag no longer needed
```

---

## 6. Testing Scenarios

### 6.1 Core Validation — Must Pass Before Any Rollout

Run all on `lugal_ws_sandbox` using real cloned users and real existing conversations.

| # | Scenario | Expected Result |
|---|----------|----------------|
| 1 | WS connection authenticates using a cloned user's JWT via session bridge | HTTP 101 received; no 401 |
| 2 | `_build_bus_channel_list()` returns correct channels for that user | `supply_chat.*`, `supply_user.<uid>`, `supply_stories` all present |
| 3 | Send chat message via HTTP API → WS client receives `supply.chat.message.new` | Event arrives within 50ms |
| 4 | Typing indicator → WS receives `supply.chat.typing.start`, then auto-stop after 8s | Both events arrive without FE action after 8s |
| 5 | Recipient marks message delivered → sender's WS receives `supply.chat.message.delivered` | Delivery tick updates on sender UI |
| 6 | Recipient marks message read → sender's WS receives `supply.chat.message.read` | Read tick updates on sender UI |
| 7 | New story posted → all connected users receive `supply.story.new` | Story appears for all active WS connections |
| 8 | WS disconnection → reconnect restores all channel subscriptions | Events continue after reconnect; no missed events |
| 9 | Long-poll works in parallel — backward compat confirmed | `POST /web/bus/poll` returns events correctly alongside WS |
| 10 | `GET /api/crm/ws/config` returns `use_websocket: false` | Flag is off by default; FE falls back to poll |

### 6.2 Stability & Edge Case Scenarios

| Scenario | What It Catches | Expected Result |
|----------|----------------|----------------|
| Idle connection for 2 hours | Session expiry (code 4001), Nginx timeout, KEEP_ALIVE_TIMEOUT (4002) | Auto-reconnect; session refreshed if expired; no missed events |
| Kill Odoo process mid-connection | Reconnect logic, message gap during restart | Reconnects; replays missed events via `last_notification_id` |
| Same account in 3 browser tabs | Multi-tab dedup (`seenIds` Set) | Badge increments once per event, not 3 times |
| 50 typing events in 2 seconds | Rate limiter (Odoo WS rate limit config) | Connection not dropped; UI degrades gracefully |
| Create new conversation while connected | Resubscribe flow — new `supply_chat.<id>` channel | Messages on new conversation arrive immediately after resubscribe |
| Network drop and restore (Chrome DevTools offline) | Reconnect under packet loss, missed event replay | All messages received after reconnect |
| User logs out while WS is open | Clean disconnect on code 1000 | WS closed with `1000`; no reconnect loop |
| 24-hour offline reconnect | `last_notification_id` references a deleted `bus_bus` row (GC boundary) | FE resets `last=0`, fetches fresh state via `GET /api/crm/notifications` |
| Session bridge called with expired JWT | Correct 401 response | `use_websocket` falls back; polling continues |
| `ws.rollout.enabled` set to False mid-session | Rollback test | Current WS users finish session normally; new sessions get long-poll |

---

## 7. Definition of Done

The migration is complete and safe when every item below is confirmed:

| # | Completion Criterion | Status |
|---|---------------------|--------|
| 1 | Network tab shows exactly 1 WebSocket connection and zero polling requests for real-time | [ ] |
| 2 | User can stay connected for 8 hours without missing an event or ghost state | [ ] |
| 3 | Disconnect and reconnect correctly replays missed events via `last_notification_id` | [ ] |
| 4 | Multi-tab dedup confirmed — badge increments once per event regardless of tabs open | [ ] |
| 5 | All WS close codes (1000, 1001, 1012, 4001, 4002, 4003) handled and tested | [ ] |
| 6 | Internal team has run on WebSocket-only for 14 days without a reported real-time issue | [ ] |
| 7 | Email notifications arrive in real time via WS without polling (Phase 4 complete) | [ ] |
| 8 | `bus_bus` table, `_sendone()`, and all existing models confirmed unchanged | [ ] |
| 9 | Odoo/SAP sync confirmed unaffected throughout entire migration | [ ] |
| 10 | Long-poll controller still present and functional (kept as legacy fallback) | [ ] |
| 11 | All test scenarios in Section 6 passed on `lugal_ws_sandbox` | [ ] |
| 12 | `lugal_local` database schema identical to before migration started | [ ] |

---

## Appendix: What Stays Unchanged After Migration

| Component | Status |
|-----------|--------|
| `bus.bus._sendone()` | Unchanged — WebSocket uses the same dispatch pipeline |
| `bus_bus` PostgreSQL table | Unchanged — events still written here |
| All existing HTTP APIs | Unchanged — chat, email, stories, notifications all work as before |
| JWT auth (`lugal_auth`) | Unchanged — session bridge uses it, doesn't modify it |
| `bus_compat_controller.py` | Unchanged — long-poll shim stays live |
| `/api/crm/notifications` | Unchanged — still used for initial badge count on connect |
| `/api/crm/supply/chat/bus_channels` | Unchanged — kept as fallback/diagnostic endpoint |
| Nginx config | Unchanged — already production-ready |
| SAP sync | Unchanged — zero intersection with bus layer |

---

*Lugal CRM — WebSocket Migration Plan v2.0 | Migration Branch Only | `lugal_ws_migration` addon*
