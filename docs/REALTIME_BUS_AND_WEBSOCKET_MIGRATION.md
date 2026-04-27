# Real-Time System: Bus Polling Architecture & WebSocket Migration Guide

**Odoo Version:** 19.0  
**Status:** Production (Long-Poll) → Planned Migration to Native WebSocket  
**Audience:** Backend engineers, frontend engineers, DevOps  

---

## Table of Contents

1. [How the Current System Works — Full Stack Overview](#1-how-the-current-system-works)
2. [The Bus Polling Layer in Detail](#2-the-bus-polling-layer-in-detail)
3. [Database Layer: How bus.bus Talks to PostgreSQL](#3-database-layer-how-busbus-talks-to-postgresql)
4. [Our Custom Channel Architecture](#4-our-custom-channel-architecture)
5. [What Every Event Looks Like End-to-End](#5-what-every-event-looks-like-end-to-end)
6. [Typing Indicators — Special Case](#6-typing-indicators--special-case)
7. [Odoo 19's Native WebSocket — What Already Exists](#7-odoo-19s-native-websocket--what-already-exists)
8. [Migration Plan: Long-Poll → WebSocket](#8-migration-plan-long-poll--websocket)
9. [Will the Database Be Affected?](#9-will-the-database-be-affected)
10. [Risks, Precautions & Gotchas](#10-risks-precautions--gotchas)
11. [Infrastructure Changes Required](#11-infrastructure-changes-required)
12. [Summary Comparison Table](#12-summary-comparison-table)

---

## 1. How the Current System Works

### Bird's-eye view

```
┌──────────────────────────────────────────────────────────────┐
│  React Frontend (port 5173)                                  │
│                                                              │
│  1. On app start → POST /api/crm/supply/chat/bus_channels   │
│     Gets: ["supply_chat.11", "supply_chat.19", "supply_user.2", "supply_stories"] │
│                                                              │
│  2. Every ~1s → POST /web/bus/poll                           │
│     Body: { channels: [...], last: <last_id> }               │
│     Gets: [] or [{ id, message: { type, payload } }]        │
│                                                              │
│  3. On new event → update local state                        │
└──────────────────────────────────────────────────────────────┘
              │ HTTP POST every ~1 second
              ▼
┌──────────────────────────────────────────────────────────────┐
│  Odoo 19 HTTP Workers (9 workers, port 8070)                 │
│                                                              │
│  BusPollCompatController                                     │
│    POST /web/bus/poll                                        │
│    → calls bus.bus._poll(channels, last_id)                  │
│    → queries bus_bus table in PostgreSQL                     │
│    → returns new rows (or [] if nothing new)                 │
└──────────────────────────────────────────────────────────────┘
              │ SQL SELECT from bus_bus
              ▼
┌──────────────────────────────────────────────────────────────┐
│  PostgreSQL (DB: lugal_local)                                │
│                                                              │
│  Table: bus_bus                                              │
│    id | channel (JSON) | message (JSON) | create_date        │
│                                                              │
│  NOTIFY imbus  ← pg_notify() called on each _sendone()      │
│  LISTEN imbus  ← Odoo's gevent/dispatch thread listens       │
└──────────────────────────────────────────────────────────────┘
```

### Key facts
- This is **short-polling disguised as long-polling**: the frontend calls `/web/bus/poll` repeatedly, and each call either returns queued messages or returns `[]`.
- The poll endpoint does NOT hold connections open. Each request is answered immediately by reading the `bus_bus` database table.
- **All real-time data goes through PostgreSQL** — every message, typing event, story update, delivery receipt is written as a row in `bus_bus` first, then read on the next poll.

---

## 2. The Bus Polling Layer in Detail

### 2.1 The Shim Controller

File: `addons/lugal_crm/controllers/bus_compat_controller.py`

Odoo 19 removed the legacy `/web/bus/poll` endpoint (it moved everything to WebSocket). We added this shim so our frontend could continue using the old URL without modification:

```python
@http.route('/web/bus/poll', type='jsonrpc', auth='public', csrf=False, methods=['POST'])
def bus_poll(self, channels=None, last=0, **kwargs):
    from odoo.addons.bus.models.bus import channel_with_db
    channels_with_db = [channel_with_db(db, c) for c in channels]
    notifications = request.env['bus.bus'].sudo()._poll(channels_with_db, last_id)
    return notifications
```

The shim converts our plain string channel names (`"supply_chat.11"`) into Odoo's internal tuple format `(db_name, "supply_chat.11")` before querying the table.

### 2.2 What `_poll()` Does in bus.py

```python
TIMEOUT = 50  # seconds — used as the time window for "first poll" (last=0)

def _poll(self, channels, last=0):
    if last == 0:
        # First connection: return anything in the last 50 seconds
        timeout_ago = now() - timedelta(seconds=TIMEOUT)
        domain = [('create_date', '>', timeout_ago)]
    else:
        # Subsequent polls: return everything newer than the last id seen
        domain = [('id', '>', last)]
    
    domain.append(('channel', 'in', channels))
    notifications = self.sudo().search_read(domain, ["message"])
    return [{'id': n['id'], 'message': json.loads(n['message'])} for n in notifications]
```

**Critical behaviour:**
- When `last=0` (fresh connection or page reload), the backend returns everything from the last 50 seconds — so the FE catches up on missed messages.
- After that, every poll passes the `id` of the last message it received, and gets back only newer rows.
- The FE must store and advance `last_id` on every response.

### 2.3 What `_sendone()` Does in bus.py

Every time code calls `_sendone(channel, event_type, payload)`:

```python
def _sendone(self, target, notification_type, message):
    # Step 1 — queue the INSERT for pre-commit
    self.env.cr.precommit.data["bus.bus.values"].append({
        "channel": json_dump(channel_with_db(dbname, target)),
        "message": json_dump({"type": notification_type, "payload": message}),
    })

    # Step 2 — queue a pg_notify() for post-commit
    self.env.cr.postcommit.data["bus.bus.channels"].add(channel)
```

Then on transaction commit:
1. A row is **INSERTed into `bus_bus`** table.
2. `SELECT pg_notify('imbus', payload)` is executed — PostgreSQL notifies any LISTEN clients.

**The INSERT into bus_bus happens inside the same DB transaction as the originating action.** If the transaction rolls back (e.g., message save fails), the bus notification also rolls back. This is the atomicity guarantee.

---

## 3. Database Layer: How bus.bus Talks to PostgreSQL

### 3.1 The `bus_bus` Table

```sql
CREATE TABLE bus_bus (
    id          SERIAL PRIMARY KEY,
    create_date TIMESTAMP WITHOUT TIME ZONE,
    channel     TEXT NOT NULL,   -- JSON: ["lugal_local", "supply_chat.11"]
    message     TEXT NOT NULL    -- JSON: {"type": "supply.chat.message.new", "payload": {...}}
);
```

**This table is a message log, not a message queue.** Rows are never "consumed" — all clients read from the same table using their own `last_id` pointer. Rows are cleaned up by a GC cron job.

### 3.2 Garbage Collection

Odoo runs `_gc_messages()` periodically via `@api.autovacuum`:

```python
DEFAULT_GC_RETENTION_SECONDS = 60 * 60 * 24  # 24 hours

def _gc_messages(self):
    gc_retention_seconds = int(ir_config_parameter.get_param(
        "bus.gc_retention_seconds", DEFAULT_GC_RETENTION_SECONDS
    ))
    timeout_ago = now() - timedelta(seconds=gc_retention_seconds)
    self.env.cr.execute("DELETE FROM bus_bus WHERE create_date < %s", (timeout_ago,))
```

**Key point:** Rows older than 24 hours are deleted. If a client goes offline for more than 24 hours and reconnects with an old `last_id`, it may miss events (the `id` may reference a deleted row). The FE should handle this by resetting `last=0` if the returned notification list seems broken/out of order.

### 3.3 PostgreSQL LISTEN/NOTIFY

When the Odoo `ImDispatch` thread starts, it executes:
```sql
LISTEN imbus;
```

When `_sendone()` commits, it executes:
```sql
SELECT pg_notify('imbus', '<channel_json_list>');
```

PostgreSQL pushes this to the LISTEN connection. The dispatch thread wakes up and triggers WebSocket clients (if any). For long-poll clients, this doesn't matter — they just query the table directly on their next poll.

**The NOTIFY payload is capped at 8000 bytes** (`NOTIFY_PAYLOAD_MAX_LENGTH`). If the list of channels to notify is too large, it's automatically split into multiple NOTIFY calls.

### 3.4 DB Connection Cost of Long-Polling

- **Each poll request uses one DB connection** from the worker's pool.
- Config: `workers = 9`, each with ~16 DB connections = **144 total DB connections**.
- With aggressive polling (every 1s), a single user makes ~60 DB requests/minute.
- At scale: 50 concurrent users = ~3,000 DB queries/minute — all of them simple `SELECT` on `bus_bus`.
- The `bus_bus` table should have an index on `(channel, id)` and `(create_date)` — Odoo creates these by default.

---

## 4. Our Custom Channel Architecture

We use three categories of channels. The FE subscribes to all of them simultaneously.

### 4.1 Conversation-Level Channels: `supply_chat.<conv_id>`

```
supply_chat.11   — events for conversation ID 11
supply_chat.19   — events for conversation ID 19
```

**Events published on these channels:**

| Event Type | Published When | Payload |
|------------|---------------|---------|
| `supply.chat.message.new` | New message created | Full message object |
| `supply.chat.message.updated` | Message edited | `{ message_id, content, edited_at }` |
| `supply.chat.message.deleted` | Message deleted | `{ message_id, conversation_id }` |
| `supply.chat.message.reaction.changed` | Emoji reaction added/removed | `{ message_id, conversation_id, reactions }` |
| `supply.chat.typing.start` | User starts typing | `{ conversation_id, user_id, user_name }` |
| `supply.chat.typing.stop` | User stops typing (or timer fires) | `{ conversation_id, user_id }` |

### 4.2 User-Level Channels: `supply_user.<uid>`

```
supply_user.2    — private channel for user ID 2 (admin)
supply_user.15   — private channel for user ID 15
```

**Events published on these channels:**

| Event Type | Published When | Payload |
|------------|---------------|---------|
| `supply.chat.message.new` | A new DM arrives (redundant delivery to ensure the user's device wakes up) | Full message object |
| `supply.chat.message.delivered` | A recipient called `/messages/<id>/delivered` | `{ message_id, conversation_id, delivery_state, delivered_to }` |
| `supply.chat.message.read` | A recipient called `/messages/<id>/read` | `{ message_id, conversation_id, delivery_state, read_by }` |
| `supply.story.viewed` | Someone viewed the user's story | `{ story_id, viewer_id, viewer_name, view_count }` |

### 4.3 Global Stories Channel: `supply_stories`

```
supply_stories   — broadcast to all users for story events
```

| Event Type | Published When | Payload |
|------------|---------------|---------|
| `supply.story.new` | A story is posted | Full story object |
| `supply.story.deleted` | A story is expired/deleted | `{ story_id, author_id }` |

### 4.4 Channel Discovery Endpoint

The FE calls this once at startup (and after login) to know which channels to subscribe to:

```
POST /api/crm/supply/chat/bus_channels
→ {
    "channels": [
      "supply_chat.11",
      "supply_chat.17",
      "supply_chat.19",
      "supply_user.2",
      "supply_stories"
    ]
  }
```

The `supply_stories` channel is always included. The `supply_chat.*` channels include only active (non-archived) conversations the user is in.

---

## 5. What Every Event Looks Like End-to-End

### Example: User A sends a message to User B

```
User A (FE)          Backend                   PostgreSQL              User B (FE)
    │                    │                           │                       │
    │ POST /messages/create                          │                       │
    │────────────────────►                           │                       │
    │                    │ INSERT lugal_supply_message                        │
    │                    │ _sendone("supply_chat.11", "message.new", payload)│
    │                    │ _sendone("supply_user.2",  "message.new", payload)│
    │                    │ (queued in cr.precommit)   │                       │
    │                    │ COMMIT                     │                       │
    │                    │──── INSERT bus_bus row ───►│                       │
    │                    │──── pg_notify('imbus') ───►│                       │
    │◄───────────────────│                           │                       │
    │ { success, message }                           │                       │
    │                    │                           │  (next poll cycle)    │
    │                    │◄────── POST /web/bus/poll ─────────────────────── │
    │                    │       { channels: ["supply_chat.11",...], last: N}│
    │                    │                           │                       │
    │                    │ SELECT * FROM bus_bus      │                       │
    │                    │ WHERE channel IN (...)     │                       │
    │                    │ AND id > N ───────────────►│                       │
    │                    │◄─────── [{ id, message }] ─│                       │
    │                    │─────── [{ id, message }] ──────────────────────► │
    │                    │                           │  FE updates UI        │
    │                    │                           │  POST /messages/<id>/delivered
    │                    │◄──────────────────────────────────────────────── │
    │                    │ UPDATE delivered_user_ids  │                       │
    │                    │ _sendone("supply_user.A",  │                       │
    │                    │    "message.delivered", ..)│                       │
    │ (next poll)        │                           │                       │
    │──────────────────►│                           │                       │
    │◄── delivery event ─│                           │                       │
    │ render ✓✓          │                           │                       │
```

---

## 6. Typing Indicators — Special Case

Typing events use an **in-memory timer** in addition to the bus. This is important for the WebSocket migration.

```python
# In supply_chat_controller.py
_typing_timers: dict = {}   # { (uid, conv_id): threading.Timer }
_typing_lock   = threading.Lock()
_TYPING_EXPIRE_SECS = 8

# When is_typing=True:
#   1. Publish typing.start on bus
#   2. Cancel existing timer for (uid, conv_id)
#   3. Start new 8-second threading.Timer
#      On timeout: publish typing.stop on bus

# When is_typing=False:
#   1. Cancel the timer
#   2. Publish typing.stop immediately
```

**Problem with long-poll:** The 8-second auto-stop timer exists *specifically* because the FE sends a heartbeat `is_typing=true` every 3 seconds. If the heartbeat stops (network drop, browser tab closed), the timer fires after 8 seconds and sends `typing.stop`. Without this timer, typing indicators would get stuck forever.

**Impact on WebSocket migration:** With WebSocket, the connection close event (`onclose`) can be used to immediately send a `typing.stop`. The 8-second in-memory timer should be kept as a fallback, but its purpose changes.

**Caveat:** `_typing_timers` is stored in-process memory. In a multi-worker setup (9 workers), a user's typing heartbeat could hit a different worker each time. The timer cancellation (`cancel_existing`) might not find the timer if it's in a different worker's memory. This is a **known limitation** that doesn't break anything (worst case: a ghost typing indicator for 8 seconds) but is important to document.

---

## 7. Odoo 19's Native WebSocket — What Already Exists

Odoo 19 ships with a **full production-grade WebSocket implementation** in the `bus` addon. It is already installed in this project at:

```
addons/bus/websocket.py          — WebSocket protocol implementation
addons/bus/models/ir_websocket.py — Server-side WebSocket event handlers
addons/bus/controllers/websocket.py — HTTP upgrade → WebSocket route
```

### 7.1 How It Works

```
Frontend                              Odoo WebSocket Worker
    │                                        │
    │  HTTP GET /websocket                   │
    │  Upgrade: websocket                    │
    │  Sec-WebSocket-Key: ...                │
    │───────────────────────────────────────►│
    │◄── 101 Switching Protocols ────────────│
    │  (persistent TCP connection)           │
    │                                        │
    │  send: { event_type: "subscribe",      │
    │          data: { channels: [...],      │
    │                  last: N } }           │
    │───────────────────────────────────────►│
    │                           dispatch.subscribe(channels, last, ws)
    │                                        │ (waits for pg_notify)
    │◄── { type: "notification",             │
    │      payload: [...] } ─────────────────│ (pushed immediately on event)
    │                                        │
    │  send: { event_type: "ping" }          │
    │───────────────────────────────────────►│
    │◄── pong ───────────────────────────────│
```

### 7.2 Key WebSocket Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `CONNECTION_TIMEOUT` | 60 seconds | Total idle timeout |
| `INACTIVITY_TIMEOUT` | 45 seconds | PING sent after 45s of no frames |
| `RL_BURST` | Configurable | Max messages in burst window |
| `RL_DELAY` | Configurable | Min delay between messages |
| Supported versions | `13` (RFC 6455) | Standard WebSocket |

### 7.3 Authentication in the Native WebSocket

The native WebSocket uses **Odoo session cookies** (`session_id`), not JWT:

```python
@classmethod
def _authenticate(cls):
    if wsrequest.session.uid is not None:
        if not security.check_session(wsrequest.session, wsrequest.env, wsrequest):
            wsrequest.session.logout(keep_db=True)
            raise SessionExpiredException()
    else:
        public_user = wsrequest.env.ref('base.public_user')
        wsrequest.update_env(user=public_user.id)
```

**This is the single biggest challenge for migration.** Our frontend authenticates with **JWT Bearer tokens**, not Odoo sessions. The native WebSocket expects a valid `session_id` cookie.

### 7.4 Channel Building in Native WebSocket

The native system adds default channels automatically:

```python
def _build_bus_channel_list(self, channels):
    channels.append('broadcast')         # global broadcast
    channels.extend(self.env.user.all_group_ids)  # user's Odoo groups
    if req.session.uid:
        channels.append(self.env.user.partner_id)  # user's partner record
    return channels
```

Our custom channels (`supply_chat.*`, `supply_user.*`) are not in this list — they would need to be added by overriding `_build_bus_channel_list` in a custom module.

---

## 8. Migration Plan: Long-Poll → WebSocket

### Phase 0: Pre-conditions (before writing any code)

- [ ] Decide on auth strategy (see Section 10.1)
- [ ] Confirm Nginx/reverse-proxy supports WebSocket upgrades (`proxy_http_version 1.1; proxy_set_header Upgrade $http_upgrade;`)
- [ ] Confirm `longpolling_port = 8072` can also serve WebSocket (Odoo 19 uses the same port)

### Phase 1: Backend — Override `ir.websocket` to Support JWT

Create `addons/lugal_crm/models/crm_ir_websocket.py`:

```python
class LugalIrWebsocket(models.AbstractModel):
    _inherit = 'ir.websocket'

    def _build_bus_channel_list(self, channels):
        """Add our custom channels to the WebSocket subscription."""
        # Let Odoo add its default channels first
        result = super()._build_bus_channel_list(channels)
        
        uid = self.env.uid
        if uid and uid != self.env.ref('base.public_user').id:
            # Add all active supply chat conversations
            Conv = self.env['lugal.supply.conversation'].sudo()
            convs = Conv.search([
                ('is_archived', '=', False),
                ('participant_ids', 'in', [uid]),
            ])
            for conv in convs:
                result.append(f'supply_chat.{conv.id}')
            result.append(f'supply_user.{uid}')
            result.append('supply_stories')
        return result

    @classmethod
    def _authenticate(cls):
        """
        Override to accept JWT Bearer token in addition to session cookie.
        If a valid JWT is present, create/restore a session for the WS connection.
        """
        # Try JWT from query param or cookie first
        from addons.lugal_crm.controllers._auth import ensure_jwt_user_id
        uid = ensure_jwt_user_id()
        if uid:
            wsrequest.update_env(user=uid)
            return
        # Fall back to Odoo session
        super()._authenticate()
```

### Phase 2: Frontend Changes

Replace the polling loop:

```typescript
// BEFORE: Long-poll loop
async function startPolling(channels: string[], lastId: number) {
  while (true) {
    const result = await crmPost('/web/bus/poll', { channels, last: lastId });
    for (const notif of result) {
      lastId = notif.id;
      handleBusEvent(notif.message.type, notif.message.payload);
    }
    await sleep(1000);
  }
}

// AFTER: WebSocket
function startWebSocket(token: string) {
  const ws = new WebSocket(`wss://your-server.com/websocket`);
  
  ws.onopen = () => {
    // Subscribe after connection
    ws.send(JSON.stringify({
      event_type: 'subscribe',
      data: { channels: [], last: 0 }  // backend adds our channels automatically
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === 'notification') {
      for (const notif of data.payload) {
        handleBusEvent(notif.message.type, notif.message.payload);
      }
    }
  };
  
  // Heartbeat (Odoo sends PING, FE must respond PONG)
  ws.onclose = () => {
    // Stop any active typing indicators immediately
    sendTypingStop();
    // Reconnect with backoff
    setTimeout(() => startWebSocket(token), 3000);
  };
}
```

### Phase 3: Dual-Mode Transition Period

Run both systems in parallel during transition:

```typescript
const USE_WEBSOCKET = featureFlag('USE_WEBSOCKET');

if (USE_WEBSOCKET) {
  startWebSocket(token);
} else {
  startPolling(channels, 0);
}
```

The backend does not need to change — `_sendone()` writes to `bus_bus` the same way regardless of whether clients use WebSocket or long-poll. Both consume from the same table.

### Phase 4: Remove Long-Poll

Once all FE clients have migrated:
- Remove `bus_compat_controller.py` (or keep it for older API consumers)
- Remove the `/web/bus/poll` route
- Remove the `startPolling()` function from the FE

---

## 9. Will the Database Be Affected?

### Short answer: No structural changes needed.

| Concern | Long-Poll | WebSocket | Impact |
|---------|-----------|-----------|--------|
| `bus_bus` table structure | Used (SELECT every poll) | Used (INSERT still, SELECT by dispatch) | **None — same table** |
| `_sendone()` calls | Unchanged | Unchanged | **None** |
| `bus_bus` INSERT on event | Yes | Yes | **None** |
| DB connections per notification | 1 connection per poll request | 1 persistent connection per user | **Fewer connections** |
| GC of old rows | 24h retention | 24h retention | **None** |
| `lugal_supply_message` table | Unchanged | Unchanged | **None** |
| `lugal_supply_conversation` table | Unchanged | Unchanged | **None** |
| `lugal_supply_story` table | Unchanged | Unchanged | **None** |

### The only DB improvement from WebSocket:

With 50 concurrent users on long-poll:
- 50 users × 1 request/second = 50 SELECT queries/second against `bus_bus`

With 50 concurrent users on WebSocket:
- 50 persistent TCP connections
- 0 SELECT queries/second (notifications pushed via pg_notify → dispatch → push)
- Only SELECT when there are actual new notifications

**WebSocket significantly reduces DB load at scale.**

---

## 10. Risks, Precautions & Gotchas

### 10.1 Authentication: JWT vs Odoo Session

**This is the hardest part of the migration.**

Odoo's native WebSocket only understands Odoo sessions (`session_id` cookie). Our API uses JWT Bearer tokens. Options:

| Option | Pros | Cons |
|--------|------|------|
| **A) Override `_authenticate()` in ir.websocket** | Clean, stays inside Odoo | Need to decode JWT inside Odoo's WS auth flow |
| **B) Issue a short-lived Odoo session on login alongside JWT** | No WS code changes | Two auth systems; session management overhead |
| **C) Build a custom WebSocket endpoint (separate from Odoo's)** | Full control | More code; must implement protocol yourself |
| **D) Pass JWT as query param on WS URL** | Simple FE change | Token visible in server logs |

**Recommendation: Option A** — override `_authenticate()` in a custom `ir.websocket` model extension. See Phase 1 in Section 8.

### 10.2 Channel Subscription at Connect Time

Long-poll: FE calls `/bus_channels` to get the list, then polls with that list on every request.

WebSocket: channels are sent once at subscribe time. If a new conversation is created, the backend must push a message to the FE telling it to re-subscribe with the new channel added.

**Action needed:** Implement a `supply.chat.conversation.created` bus event that triggers the FE to call `ws.send({ event_type: 'subscribe', data: { channels: [...new list] } })`.

### 10.3 In-Memory Typing Timers

The `_typing_timers` dict is stored in one worker's memory. With WebSocket:
- Each user has a persistent connection to **one** worker
- The typing timer will always be in the same process as the user
- This actually **fixes** the multi-worker issue

But during migration, if some users are on WebSocket and some on long-poll, the timer behavior is still correct because both paths call the same `/conversations/<id>/typing` endpoint which modifies `_typing_timers`.

### 10.4 Message Ordering with High Traffic

`_sendone()` queues the INSERT on `cr.precommit`, and the `pg_notify` on `cr.postcommit`. With high concurrency:
- Transaction T1 gets id=100, T2 gets id=101
- But T2 commits first → pg_notify for id=101 fires first
- T1 commits → pg_notify for id=100 fires
- WebSocket dispatch processes 101 then 100 → clients see 100 arrive after 101

Odoo's WebSocket implementation handles this with a **history window** (see `Websocket` class comments in `websocket.py`):
> "Lower id notifications might be dispatched after higher id notifications. The history of already dispatched notifications is kept for a window to avoid sending duplicates."

For long-poll this is not an issue because clients always query `WHERE id > last_id` and get a sorted batch.

**Action needed:** On the FE, sort received messages by `id` or `created_at` before rendering, never assume bus delivery order = chronological order.

### 10.5 Multi-Tab / Multi-Device

Long-poll: each tab independently polls, each gets its own copy of all events. No coordination.

WebSocket (Odoo 19): a user opening 2 tabs creates 2 WebSocket connections. Both subscribe to the same channels. Both receive every event. The FE must handle deduplication (`if (cache.has(msg.id)) return;`).

### 10.6 Load Balancer / Nginx Sticky Sessions

WebSocket connections are long-lived TCP connections. If you have multiple Odoo servers behind a load balancer:
- The initial HTTP upgrade handshake hits server A
- All subsequent frames on that connection stay on server A
- But another tab on the same browser might connect to server B
- Server B's `_typing_timers` doesn't know about the timer on server A

**Action needed:** Configure Nginx with `ip_hash` or cookie-based sticky sessions for `/websocket` to ensure all connections from the same user land on the same backend worker. OR externalize `_typing_timers` to Redis/PostgreSQL.

### 10.7 Firewall / Proxy WebSocket Support

WebSocket requires:
```nginx
location /websocket {
    proxy_pass http://odoo_upstream;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
    proxy_read_timeout 300s;   # Keep alive for 5 minutes min
}
```

Without these headers, the upgrade handshake fails with HTTP 400.

### 10.8 Rate Limiting

Odoo's WebSocket has built-in rate limiting:
```python
RL_BURST = int(config['websocket_rate_limit_burst'])
RL_DELAY = float(config['websocket_rate_limit_delay'])
```

If a user sends too many events (e.g., spamming typing indicators), the connection gets a `RateLimitExceededException` and closes. The FE must handle reconnection gracefully.

---

## 11. Infrastructure Changes Required

### Current Setup
```
Internet → Nginx (proxy) → Odoo port 8070 (9 HTTP workers)
                         → Odoo port 8072 (longpolling worker - gevent)
```

### After WebSocket Migration
```
Internet → Nginx (proxy, with WebSocket support) → Odoo port 8072
                                                    (handles both HTTP upgrades
                                                     and WebSocket frames)
```

The longpolling port (8072) is the same port Odoo uses for WebSocket. It runs under gevent (cooperative I/O) which is essential for holding thousands of persistent connections efficiently.

**Changes to `odoo_local.conf`:**

No changes required for the port numbers. The `longpolling_port = 8072` is already configured. You may want to tune:
```ini
# Increase gevent worker connection limit for WebSocket
limit_time_real = 1200000    # already high — keep as is
workers = 9                  # HTTP workers, keep as is
```

---

## 12. Summary Comparison Table

| Aspect | Current (Long-Poll) | Target (WebSocket) |
|--------|--------------------|--------------------|
| **Protocol** | HTTP POST every ~1s | Persistent TCP (WS) |
| **Latency** | Up to 1 second delay | Sub-50ms |
| **DB queries** | 1 SELECT/user/second | 0 queries when idle |
| **DB connections** | 1 per poll request | 1 persistent per user |
| **Server port** | 8070 (HTTP workers) | 8072 (gevent/WS worker) |
| **Auth** | JWT Bearer (custom) | Odoo session + JWT override needed |
| **Typing timers** | In-memory, multi-worker issue | In-memory, single connection → no issue |
| **Channel subscription** | Sent on every poll request | Sent once at connect + on change |
| **Missed events on reconnect** | `last=0` catches last 50s | Subscribe with last known id |
| **bus_bus table** | Read on every poll | Written same way, read by dispatch |
| **Code changes (BE)** | None to _sendone() | Override `_authenticate()` + `_build_bus_channel_list()` |
| **Code changes (FE)** | None | Replace poll loop with WS client |
| **Nginx changes** | None needed now | Add Upgrade headers for /websocket |
| **DB schema changes** | None | **None** |
| **Risk to existing data** | None | **None** |
| **Rollback plan** | Keep compat controller | Keep both modes with feature flag |

---

## Quick Reference: All Bus Channels in This System

| Channel Name | Scope | Subscribers |
|-------------|-------|-------------|
| `supply_chat.<conv_id>` | Per-conversation | All participants of that conversation |
| `supply_user.<uid>` | Per-user private | Only that user |
| `supply_stories` | Global | All authenticated users |

## Quick Reference: All Event Types

| Event Type | Channel | Trigger |
|------------|---------|---------|
| `supply.chat.message.new` | `supply_chat.<id>` + `supply_user.<uid>` | Message sent |
| `supply.chat.message.updated` | `supply_chat.<id>` | Message edited |
| `supply.chat.message.deleted` | `supply_chat.<id>` | Message deleted |
| `supply.chat.message.reaction.changed` | `supply_chat.<id>` | Reaction added/removed |
| `supply.chat.typing.start` | `supply_chat.<id>` | User starts typing |
| `supply.chat.typing.stop` | `supply_chat.<id>` | User stops typing / 8s timer |
| `supply.chat.message.delivered` | `supply_user.<sender_uid>` | Recipient calls /delivered |
| `supply.chat.message.read` | `supply_user.<sender_uid>` | Recipient calls /read |
| `supply.story.new` | `supply_stories` | Story posted |
| `supply.story.deleted` | `supply_stories` | Story expired/deleted |
| `supply.story.viewed` | `supply_user.<author_uid>` | Someone views a story |
