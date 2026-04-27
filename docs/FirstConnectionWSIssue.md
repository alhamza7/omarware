# FirstConnectionWSIssue.md
# WebSocket Live Connection Issue for Newly Created Users — Full Context

---

## 1. Problem Statement

When a **newly created employee/user** logs in, the WebSocket connection either:
- Fails to establish at all (error in browser console)
- Connects but receives **zero events** (messages, notifications, delivery ticks)
- Works **one-way only** (sender sees delivery, recipient does not receive)
- Only starts working after the **browser is manually refreshed** or after messages are exchanged back and forth

The bug is **intermittent** — sometimes it works after a second attempt, sometimes never. Existing users with older sessions are unaffected; the failure rate is close to 100% for first-login from a new browser/device.

---

## 2. Root Cause Analysis

### A. Session Token Missing (Primary Cause)

When the FE calls `POST /api/crm/ws/session` to exchange a JWT for an Odoo session cookie, the resulting session had:
```
session.uid = <user_id>      ✅
session.session_token = None  ❌  ← was never computed
```

Odoo's `check_session()` internally calls `consteq(expected_token, session.session_token)` where `session.session_token` is `None`. This throws a `TypeError` instead of returning `False`.

In `odoo/addons/bus/websocket.py`, this `TypeError` is caught by a broad `except Exception` handler and **silently swallowed**, leaving the WebSocket open but with **zero channel subscriptions**. No messages ever arrive.

### B. Wrong WebSocket URL (Secondary Cause)

The FE was constructing the WebSocket URL as `ws://127.0.0.1:<random_port>` (from a stale config) or using `ws://192.168.116.204:8075` (HTTP port, not WebSocket port 8076). Odoo's gevent worker only handles WS upgrades on port **8076**.

### C. HTTPS/WSS Mismatch (Tertiary Cause)

When the Vite dev server runs with `basicSsl()` (HTTPS), the FE auto-upgraded `ws://` URLs to `wss://`. This sent a TLS ClientHello to port 8076 which does not have TLS termination — Odoo logged `Invalid HTTP method: "\x16\x03..."` and closed the connection.

### D. New Conversation Race Condition (for first message only)

When a brand-new DM is created and the first message sent in the same HTTP request:
1. Backend publishes `supply.chat.resubscribe` to `supply_user.<uid>` (tells FE to resubscribe)
2. Backend immediately publishes `supply.chat.message.new` to `supply_chat.<new_conv_id>`
3. The recipient's FE receives (1) and needs time to call `resubscribe()` and establish the new channel subscription
4. By the time the new subscription is active, event (2) has already been dispatched on the old subscription state → **first message always missed**

### E. `ws.rollout.enabled` Not Always True

The WebSocket feature flag was stored in `ir.config_parameter` but could be reset to `False` after DB restores or module updates, causing the FE to silently fall back to long-poll mode.

---

## 3. What Was Tried and What Is the Current State

### Fix 1 — Session Token Computation (APPLIED ✅)

**File:** `addons/lugal_ws_migration/controllers/ws_session.py`
**Function:** `WsSessionController.get_ws_session()`
**Lines:** 62–101

Added explicit `session.session_token = compute_session_token(session, request.env)` and forced `session.can_save = True` + `root.session_store.save(session)` so the session is fully valid before the cookie is emitted.

```python
# Line 72 — KEY FIX: compute and store the session token
session.session_token = compute_session_token(session, request.env)
# Lines 79–81 — force-save
session.can_save = True
request.session.touch()
root.session_store.save(session)
# Line 89 — cookie with Max-Age=86400 (1 day persistence)
cookie_header = f'session_id={session.sid}; Path=/; HttpOnly; SameSite=Lax; Max-Age=86400'
```

---

### Fix 2 — Stale Session TypeError Recovery on WebSocket (APPLIED ✅)

**File:** `addons/lugal_ws_migration/models/lugal_ir_websocket.py`
**Class:** `LugalIrWebsocket` (inherits `ir.websocket`)
**Function:** `_authenticate()` (classmethod)
**Lines:** 24–60

Overrides Odoo's native `_authenticate` to catch the `TypeError` from `check_session` when `session_token` is `None`. Instead of being silently swallowed, it now:
1. Logs it as INFO
2. Calls `wsrequest.session.logout(keep_db=True)` to clear the stale session
3. Raises `SessionExpiredException` → Odoo closes WS with code **4001**
4. FE's `_handleClose(4001)` calls `_ensureSession()` → fresh session → reconnect

```python
# Lines 24–60
@classmethod
def _authenticate(cls):
    if wsrequest.session.uid is not None:
        session_valid = False
        try:
            session_valid = security.check_session(
                wsrequest.session, wsrequest.env, wsrequest
            )
        except TypeError:               # ← catches session_token=None
            _logger.info('_authenticate: stale WS session ...')
            wsrequest.session.logout(keep_db=True)
            raise SessionExpiredException()  # → WS close code 4001
        if not session_valid:
            wsrequest.session.logout(keep_db=True)
            raise SessionExpiredException()
    else:
        public_user = wsrequest.env.ref('base.public_user')
        wsrequest.update_env(user=public_user.id)
```

---

### Fix 3 — Stale Session Recovery for HTTP Routes (APPLIED ✅)

**File:** `addons/lugal_ws_migration/models/lugal_ir_http.py`
**Class:** `LugalIrHttp` (inherits `ir.http`)
**Function:** `_authenticate_explicit()` (classmethod)
**Lines:** 30–64

Catches `TypeError` from `check_session` on HTTP routes (notifications API, ws/config). Clears the stale session and falls through to JWT Bearer auth so the request still succeeds.

```python
# Lines 30–64
@classmethod
def _authenticate_explicit(cls, auth):
    try:
        if request.session.uid is not None:
            session_valid = False
            try:
                session_valid = security.check_session(...)
            except TypeError:          # ← stale session_token=None
                _logger.info('lugal_ws_migration: stale session ...')
            if not session_valid:
                request.session.logout(keep_db=True)
                request.env = api.Environment(request.env.cr, None, ...)
        getattr(cls, f'_auth_method_{auth}')()
    except (AccessDenied, SessionExpiredException, ...):
        raise
```

---

### Fix 4 — Channel Subscription at Connect Time (APPLIED ✅)

**File:** `addons/lugal_ws_migration/models/lugal_ir_websocket.py`
**Class:** `LugalIrWebsocket`
**Function:** `_build_bus_channel_list()`
**Lines:** 62–96

Overrides `_build_bus_channel_list` to automatically append all relevant channels whenever the WS sends a subscribe frame (on connect and on every `resubscribe()` call from the FE):

```python
# Lines 62–96
def _build_bus_channel_list(self, channels):
    result = super()._build_bus_channel_list(channels)
    uid = self.env.uid
    # ... public user guard ...

    # Lines 76–88: ALL active conversations this user participates in
    Conv = self.env['lugal.supply.conversation'].sudo()
    convs = Conv.search([
        ('is_archived', '=', False),
        ('participant_ids', 'in', [uid]),
    ])
    for conv in convs:
        result.append(f'supply_chat.{conv.id}')   # e.g. 'supply_chat.42'

    # Line 91: Per-user channel (delivery/read receipts, resubscribe signals)
    result.append(f'supply_user.{uid}')

    # Line 94: Global stories channel
    result.append('supply_stories')

    return result
```

---

### Fix 5 — Resubscribe Signal on New Conversation (APPLIED ✅)

**File:** `addons/lugal_crm/controllers/supply_chat_controller.py`
**Function:** `_notify_participants_resubscribe(conv, participant_ids)`
**Lines:** 310–335

Called after every `_find_or_create_dm()` (line 248) and `_find_or_create_group()` (line 278). Publishes `supply.chat.resubscribe` to every participant's `supply_user.<uid>` channel so their FE calls `busClient.resubscribe()` immediately, adding the new `supply_chat.<id>` channel to their live subscription.

```python
# Lines 310–335
def _notify_participants_resubscribe(conv, participant_ids):
    payload = {
        'conversation_id': conv.id,
        'conversation_type': conv.type,
        'name': conv.name or '',
    }
    for uid in participant_ids:
        request.env['bus.bus'].sudo()._sendone(
            f'supply_user.{uid}',      # ← always-subscribed personal channel
            'supply.chat.resubscribe',
            payload,
        )
```

Called from:
- `_find_or_create_dm()` — **line 248** — sends to `[uid, other_uid]`
- `_find_or_create_group()` — **line 278** — sends to all `all_ids`

---

### Fix 6 — Dual-Channel Message Publishing (APPLIED ✅)

**File:** `addons/lugal_crm/controllers/supply_chat_controller.py`
**Function:** `_publish_new_message(msg, uid, conv)`
**Lines:** 338–403

Fixes the race condition where the first message in a brand-new conversation arrives before the recipient has resubscribed.

**Before:** Only published to `supply_chat.<conv_id>` — recipient missed it if not yet subscribed.

**After:** Publishes to **both**:
1. `supply_chat.<conv_id>` — primary path (conversation channel)
2. `supply_user.<participant_uid>` — **fallback path** (personal channel, always subscribed)

The personal-channel copy carries `_via_personal_channel: True` so the FE can deduplicate by `message_id`.

```python
# Lines 338–403
def _publish_new_message(msg, uid, conv):
    payload = _serialize_message(msg, uid)

    # Line 360 — Path 1: conversation channel
    _bus_publish(f'supply_chat.{conv.id}', 'supply.chat.message.new', payload)

    # Line 364 — personal copy with dedup flag
    personal_payload = dict(payload, _via_personal_channel=True)
    sender_id = msg.sender_id.id if msg.sender_id else uid

    # Lines 369–381 — Path 2: per-recipient personal channel fallback
    for participant in conv.participant_ids:
        if participant.id != sender_id:
            request.env['bus.bus'].sudo()._sendone(
                f'supply_user.{participant.id}',
                'supply.chat.message.new',
                personal_payload,
            )
```

---

### Fix 7 — ws.rollout.enabled Always True (APPLIED ✅)

**File:** `addons/lugal_ws_migration/data/ws_config.xml`
**Lines:** 1–14

Uses `set_param()` (upsert) instead of `<record>` INSERT so the flag is always set to `True` on every module update without risk of unique-constraint failure.

```xml
<function model="ir.config_parameter" name="set_param">
    <value eval="'ws.rollout.enabled'"/>
    <value eval="'True'"/>
</function>
```

---

### Fix 8 — ws_url Returned from Backend Config (APPLIED ✅)

**File:** `addons/lugal_ws_migration/controllers/ws_session.py`
**Function:** `WsSessionController.ws_config()`
**Lines:** 119–181

The `/api/crm/ws/config` endpoint now returns a `ws_url` field built from the request's `Host` header + configured `gevent_port` (8076). This gives the FE the exact correct URL regardless of environment.

```python
# Lines 169–172
raw_host = request.httprequest.host or ''
hostname = raw_host.split(':')[0]          # e.g. "192.168.116.204"
scheme   = 'wss' if request.httprequest.is_secure else 'ws'
ws_url   = f"{scheme}://{hostname}:{gevent_port}/websocket?version={ws_version}"
```

---

## 4. Current Status — What Still Doesn't Work

Despite all the above backend fixes, the issue **persists for newly created users**. The browser console shows:

```
[BusClient] WebSocket CONNECTED
[BusClient] Config: { ws_url: 'ws://192.168.116.204:8076/websocket?version=saas-18.5-1' }
```

But no live messages, typing indicators, or notifications arrive.

**Suspected remaining issue:** The FE `BusClient.ts` is not correctly handling the `supply.chat.resubscribe` event, OR it handles it but then the subscribe frame it sends does not trigger `_build_bus_channel_list` because the FE's channel list is already non-empty (Odoo only appends to whatever the FE sends, it does not replace).

Additionally, when on HTTPS (Vite `basicSsl()`), the FE may be:
- Using `ws_url` directly from the backend (correct `ws://` URL)
- But the browser blocks `ws://` from an `https://` page (mixed content policy)
- And the FE's fallback `wss://` upgrade targets port 8076 which has NO TLS

---

## 5. Frontend Changes Required (Prompts Previously Provided)

### 5a. BusClient.ts — Correct HTTPS/WSS Handling

**File:** `src/shared/realtime/BusClient.ts`
**Function:** `_openSocket()` (approx. line 255)

**Problem:** When `location.protocol === 'https:'`, `BusClient` upgrades `ws://` to `wss://` directly, pointing at port 8076 (no TLS) → TLS handshake failure.

**Required fix:**
```typescript
// In _openSocket(), replace the direct wss:// upgrade with proxy routing:
if (location.protocol === 'https:' && url.startsWith('ws://')) {
  // Route through Vite/Nginx proxy — DO NOT upgrade directly (port 8076 has no TLS)
  const versionParam = this.wsVersion ? `?version=${this.wsVersion}` : '';
  url = `wss://${location.host}/websocket${versionParam}`;
  console.log('[BusClient] HTTPS: routing WS through proxy:', url);
}
```

### 5b. vite.config.ts — WebSocket Proxy Always Active

**File:** `vite.config.ts`
**Problem:** The `/websocket` proxy entry is conditional on `isWsSandboxBranch`. On other branches, the proxy is absent → WS fails on HTTPS.

**Required fix:**
```typescript
// Make the WebSocket proxy ALWAYS active
const wsProxyEntry = {
  '/websocket': {
    target: isWsSandboxBranch
      ? 'ws://192.168.116.204:8076'
      : (isProductionBranch ? 'ws://192.168.116.211:8069' : 'ws://192.168.116.15:8070'),
    ws: true,
    changeOrigin: true as const,
  },
};
```

### 5c. RealtimeProvider.tsx — Handle CHAT_RESUBSCRIBE

**File:** `src/app/providers/RealtimeProvider.tsx`
**Required handler** (in the bus event switch/if block):

```typescript
if (type === 'supply.chat.resubscribe') {
  busClient.resubscribe();                    // re-sends subscribe frame
  void qc.invalidateQueries({
    queryKey: ['crm', 'supply', 'conversations'],
    refetchType: 'all',
  });
  return;
}
```

### 5d. RealtimeProvider.tsx — Deduplicate CHAT_MESSAGE_NEW by message_id

**File:** `src/app/providers/RealtimeProvider.tsx`

Because the backend now sends each message on **two channels** (conversation + personal fallback), the FE receives it twice. Add dedup:

```typescript
// Near top of RealtimeProvider component:
const seenMsgIds = useRef<Set<number>>(new Set());

// First thing in CHAT_MESSAGE_NEW handler:
const msgId = raw?.id ?? raw?.message?.id ?? p?.id;
if (msgId != null) {
  if (seenMsgIds.current.has(Number(msgId))) return; // duplicate
  seenMsgIds.current.add(Number(msgId));
  if (seenMsgIds.current.size > 500) {
    const arr = [...seenMsgIds.current];
    seenMsgIds.current = new Set(arr.slice(-250));
  }
}
```

Also check for `_via_personal_channel` flag as secondary dedup signal:
```typescript
if (p?._via_personal_channel && alreadyInCache(msgId)) return;
```

### 5e. _ensureSession() must use `credentials: 'include'`

**File:** Wherever `_ensureSession()` / `fetchWsSession()` is defined (likely `BusClient.ts` or a service file)

```typescript
const res = await fetch('/api/crm/ws/session', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${accessToken}`,
  },
  credentials: 'include',   // ← CRITICAL: lets browser store the Set-Cookie
  body: JSON.stringify({}),
});
```

Without `credentials: 'include'`, the `Set-Cookie: session_id=...` response header is **ignored** by the browser → no cookie → WS opens with no session → zero channels.

---

## 6. Complete File Map

| File | Module | What Changed |
|---|---|---|
| `addons/lugal_ws_migration/controllers/ws_session.py` | lugal_ws_migration | `get_ws_session()`: computes `session_token`, force-saves session, adds `Max-Age=86400` cookie. `ws_config()`: returns `ws_url` with correct host+gevent_port |
| `addons/lugal_ws_migration/models/lugal_ir_websocket.py` | lugal_ws_migration | `_authenticate()`: catches `TypeError` from stale session → `SessionExpiredException` (WS code 4001). `_build_bus_channel_list()`: subscribes user to all their `supply_chat.*`, `supply_user.*`, `supply_stories` channels |
| `addons/lugal_ws_migration/models/lugal_ir_http.py` | lugal_ws_migration | `_authenticate_explicit()`: catches `TypeError` on HTTP routes, clears stale session, falls through to JWT auth |
| `addons/lugal_ws_migration/data/ws_config.xml` | lugal_ws_migration | `set_param('ws.rollout.enabled', 'True')` — always enabled, upsert-safe |
| `addons/lugal_crm/controllers/supply_chat_controller.py` | lugal_crm | `_notify_participants_resubscribe()` (line 310): sends `supply.chat.resubscribe` to all participants on new conversation. `_publish_new_message()` (line 338): dual-channel publish (conversation + personal fallback with `_via_personal_channel=True`) |
| `addons/lugal_ws_migration/models/lugal_email_ws.py` | lugal_ws_migration | `LugalEmailMessageWs.create()` (line 40): publishes `crm.email.message.new` to `supply_user.<uid>` bus channel on new inbox email |

---

## 7. Backend API Endpoints Involved

| Endpoint | Method | Purpose |
|---|---|---|
| `POST /api/crm/ws/session` | HTTP | Exchange JWT for Odoo session cookie |
| `GET /api/crm/ws/config` | HTTP | Returns `{ use_websocket, ws_url, ws_version }` |
| `ws://<host>:8076/websocket?version=<ver>` | WS | Odoo gevent WebSocket endpoint (port 8076 ONLY) |

---

## 8. Key Invariants the External Agent Must Know

1. **Port 8075** = Odoo HTTP workers (JSON-RPC, REST). Does NOT handle WebSocket upgrades.
2. **Port 8076** = Odoo gevent worker. ONLY port that handles WebSocket upgrades. Has NO TLS.
3. **Session cookie** must be set via `POST /api/crm/ws/session` BEFORE the WS connection is opened. The cookie must be present in the WS Upgrade request headers.
4. **`_build_bus_channel_list`** runs every time the FE sends a subscribe frame. It queries the DB for all current conversations — it is the single source of truth for what channels a user should be subscribed to.
5. **`supply_user.<uid>`** — the personal channel — is ALWAYS added in `_build_bus_channel_list`. It is the reliable fallback for delivery receipts, resubscribe signals, and now message fallback delivery.
6. **`supply.chat.resubscribe`** event on `supply_user.<uid>` → FE must call `busClient.resubscribe()` → triggers new subscribe frame → `_build_bus_channel_list` runs again and picks up new conversations.
7. The **`_via_personal_channel: true`** flag in message payloads signals the FE that this is a fallback copy. FE should deduplicate by `message_id`.

---

## 9. Email — Not Live on WebSocket; User Must Manually Hit Sync

### 9.1 Problem Statement

Email notifications do **not arrive in real-time** for any user — newly created or existing. The user sees new emails only when:
- They manually navigate to the Email tab **and** click the Sync button, OR
- The 1-minute supervisor cron fires and the IDLE watcher happens to be running

This affects **all accounts** — the issue is not specific to newly created users, but is significantly worse for them because the IMAP IDLE watcher thread does not start at all until the cron fires (up to 60-second delay for first-ever email notification after account creation).

Expected behaviour: email arrives in the external mail server → Odoo IMAP IDLE watcher detects the EXISTS notification within ~2 seconds → `crm.email.message.new` bus event is published → FE WebSocket receives it → notification bell updates in real-time, no manual sync needed.

---

### 9.2 Root Cause Analysis

#### A. IMAP IDLE Watcher Not Starting for New Accounts

The IDLE watcher is managed by `lugal.email.idle.watcher` and its supervisor cron fires **every 1 minute**. When a brand-new email account is created:
1. `lugal.email.account.create()` is called → account is inserted into DB
2. **Nothing notifies the IDLE supervisor** that a new account needs watching
3. The supervisor cron fires up to 60 seconds later → IDLE thread starts → email notifications begin

During that gap (0–60 seconds), any email that arrives is **not detected in real-time** and only appears when the user manually syncs.

#### B. Multi-Worker Race: `_schedule_idle_start` Goes to Wrong Process

Odoo runs with `workers = 9`. Each OS process has its own Python heap. The IDLE supervisor thread can only run in **one process** (the one that acquired the PostgreSQL advisory lock). When `_schedule_idle_start()` is called on an HTTP worker that is **not** the IDLE supervisor owner, `start_all()` returns 0 immediately and does nothing. The new account is effectively ignored until the owning worker's next cron tick.

#### C. WebSocket Bus Event Not Published Without IDLE Watcher

`lugal_email_ws.py` hooks into `lugal.email.message.create()` to publish `crm.email.message.new` on the bus. But this hook only fires when Odoo **creates** the email record — which only happens after `action_sync()` is called (either by the IDLE watcher detecting EXISTS, or by manual sync). Without the IDLE watcher running, `action_sync()` is never called automatically, so the bus event is never published.

#### D. FE Falls Back to Polling If Bus Event Never Arrives

Since the bus event never arrives, the FE's email inbox stays stale until:
- The user opens the email tab (which triggers an HTTP `inbox/list` fetch), OR
- They click Sync (which calls `POST /api/crm/email/sync` explicitly)

Neither of these is real-time.

---

### 9.3 What Was Applied (Backend Fixes)

#### Fix E1 — Immediate IDLE Start on Account Creation (APPLIED ✅)

**File:** `addons/lugal_email/models/email_account.py`
**Class:** `LugalEmailAccount` (model `lugal.email.account`)
**Function:** `create()` override
**Lines:** 75–84

Added `@api.model_create_multi` override that calls `rec._schedule_idle_start()` immediately after every new account with a password is created, without waiting for the cron.

```python
# Lines 75–84
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    for rec in records:
        if (rec.password or '').strip():
            # Trigger IDLE watcher immediately — no waiting for 1-min cron
            rec._schedule_idle_start()    # line 83
    return records
```

#### Fix E2 — `add_account` API Calls `action_sync` + `_schedule_idle_start` (APPLIED ✅)

**File:** `addons/lugal_email/controllers/settings_email_controller.py`
**Function:** `SettingsEmailController.add_account()`
**Lines:** 74–111

After creating the account via the API, immediately:
1. Calls `acc.action_sync()` (line 105) — imports any existing inbox emails right now
2. Calls `acc._schedule_idle_start()` (line 108) — triggers the IDLE watcher immediately

```python
# Lines 99–108
if (password or '').strip():
    try:
        acc.action_sync()                  # line 105 — import existing emails now
    except Exception:
        _logger.warning('add_account: initial sync failed ...')
    acc._schedule_idle_start()             # line 108 — start IDLE watcher ASAP
```

#### Fix E3 — `_schedule_idle_start` Method (APPLIED ✅)

**File:** `addons/lugal_email/models/email_account.py`
**Function:** `_schedule_idle_start()`
**Lines:** 128–154

Spawns a one-shot background thread that:
1. Waits 0.5 seconds for the DB write to commit
2. Opens a new cursor and calls `clear_backoff_for_account(acc_id)` which resets any backoff and calls `start_all()` in the owner process

```python
# Lines 128–154
def _schedule_idle_start(self):
    def _trigger():
        time.sleep(0.5)   # wait for DB commit
        with _Registry(db_name).cursor() as cr:
            env = odoo.api.Environment(cr, SUPERUSER_ID, {})
            env['lugal.email.idle.watcher'].clear_backoff_for_account(acc_id)
    threading.Thread(target=_trigger, daemon=True, name='idle-on-test').start()
```

#### Fix E4 — Watchdog Thread Every 5 Seconds (APPLIED ✅)

**File:** `addons/lugal_email/models/email_idle_watcher.py`
**Module-level constants:** `_WATCHDOG_INTERVAL_SECS = 5` (line 81)
**Function:** `_watchdog_loop(db_name)` — lines 86–105
**Function:** `start_all()` — lines 487–536 (watchdog start at line 528–536)

When the supervisor process claims IDLE ownership, it starts a watchdog thread (`imap-idle-watchdog`) that calls `start_all()` every **5 seconds**. This means a newly created account that the `_schedule_idle_start` background thread misses (because the HTTP worker is not the owner) will be picked up within 5 seconds by the watchdog — down from up to 60 seconds.

```python
# Lines 81–105 — module-level constants and watchdog loop
_WATCHDOG_INTERVAL_SECS = 5         # line 81
_watchdog_thread: threading.Thread | None = None   # line 82

def _watchdog_loop(db_name: str):   # line 86
    global _I_AM_OWNER
    while _I_AM_OWNER:
        time.sleep(_WATCHDOG_INTERVAL_SECS)  # line 94
        if not _I_AM_OWNER:
            break
        # ... calls start_all() to pick up new accounts ...
        env['lugal.email.idle.watcher'].start_all()   # line 102

# Lines 524–536 — watchdog started when owner claims supervision
_watchdog_db = self.env.cr.dbname
if _watchdog_thread is None or not _watchdog_thread.is_alive():
    _watchdog_thread = threading.Thread(
        target=_watchdog_loop,
        args=(_watchdog_db,),
        daemon=True,
        name='imap-idle-watchdog',
    )
    _watchdog_thread.start()    # line 535
```

#### Fix E5 — Bus Event Published on New Email Creation (APPLIED ✅)

**File:** `addons/lugal_ws_migration/models/lugal_email_ws.py`
**Class:** `LugalEmailMessageWs` (inherits `lugal.email.message`)
**Function:** `create()` override
**Lines:** 40–92

Every time an unread inbox email record is created (by `action_sync()`), publishes:
1. `crm.email.message.new` on `supply_user.<uid>` bus channel → FE WebSocket receives it instantly
2. Web Push notification via `lugal.push.subscription.send_push_to_user()` → works even when browser tab is closed

```python
# Lines 40–74
@api.model_create_multi
def create(self, vals_list):
    records = super().create(vals_list)
    for record in records:
        if record.folder == 'inbox' and not record.is_read:
            uid = record.account_id.user_id.id
            if uid:
                # Line 53–64: WebSocket bus event
                self.env['bus.bus'].sudo()._sendone(
                    f'supply_user.{uid}',        # always-subscribed personal channel
                    'crm.email.message.new',
                    {
                        'message_id':   record.id,
                        'account_id':   record.account_id.id,
                        'subject':      record.subject or '(no subject)',
                        'from_name':    record.from_name or '',
                        'from_address': record.from_address or '',
                        'received_at':  _to_riyadh_iso(record.date),
                    },
                )
                # Lines 76–91: Web Push (tab-closed delivery)
                self.env['lugal.push.subscription'].sudo().send_push_to_user(
                    uid,
                    title=record.from_name or record.from_address or 'New Email',
                    body=record.subject or '(no subject)',
                    data={'type': 'email', 'message_id': record.id, 'url': '/emails'},
                )
```

---

### 9.4 Current Status and What Still Doesn't Work

Despite the above backend fixes, users still report needing to manually visit the email tab and click Sync for new emails to appear. The observed failure modes are:

1. **IDLE watcher started but FE doesn't react to `crm.email.message.new`** — The bus event is being published correctly (confirmed via log), but the FE's `RealtimeProvider.tsx` may not have a handler for this event type, or the handler does not refresh the inbox data.

2. **IDLE thread exits after 5 consecutive failures** — If the IMAP server rejects the connection (bad credentials, OAuth required, too many connections), the watcher backs off and eventually stops. The 5-second watchdog calls `start_all()` but `start_all()` checks the backoff window and skips. Only `clear_backoff_for_account()` resets this.

3. **Multi-worker timing gap still exists** — `_schedule_idle_start()` tries to call `start_all()` in the current HTTP worker, which is likely NOT the IDLE supervisor owner. The call returns 0 (skipped). The 5-second watchdog in the OWNER process picks it up — but only if the watchdog thread is alive and `_I_AM_OWNER` is True in that process.

---

### 9.5 Frontend Changes Required for Email Real-Time

**File:** `src/app/providers/RealtimeProvider.tsx`

The FE must handle the `crm.email.message.new` WebSocket event and trigger an inbox refetch:

```typescript
// In the bus event handler (in RealtimeProvider.tsx):
if (type === 'crm.email.message.new') {
  const payload = raw as {
    message_id: number;
    account_id: number;
    subject: string;
    from_name: string;
    from_address: string;
    received_at: string;
  };

  // 1. Invalidate inbox query so the email list refetches automatically
  void qc.invalidateQueries({
    queryKey: ['crm', 'email', 'inbox'],
    refetchType: 'active',
  });

  // 2. Show a toast notification
  toast(`📧 ${payload.from_name || payload.from_address}: ${payload.subject}`, {
    duration: 5000,
  });

  // 3. Play notification sound (same as chat)
  playNotificationSound();

  // 4. Increment email notification badge
  // (update whatever Zustand store or query key manages the email unread count)
  return;
}
```

---

### 9.6 Complete File Map (Email-Specific)

| File | Module | Function | Lines | What Changed |
|---|---|---|---|---|
| `addons/lugal_email/models/email_account.py` | lugal_email | `create()` | 75–84 | Calls `_schedule_idle_start()` immediately on new account creation |
| `addons/lugal_email/models/email_account.py` | lugal_email | `_schedule_idle_start()` | 128–154 | Spawns background thread → clears backoff → calls `start_all()` in owner process |
| `addons/lugal_email/controllers/settings_email_controller.py` | lugal_email | `add_account()` | 99–108 | Calls `action_sync()` (line 105) + `_schedule_idle_start()` (line 108) immediately after account creation via API |
| `addons/lugal_email/models/email_idle_watcher.py` | lugal_email | `_watchdog_loop()` | 86–105 | 5-second watchdog thread that calls `start_all()` to pick up new accounts |
| `addons/lugal_email/models/email_idle_watcher.py` | lugal_email | `start_all()` | 487–536 | Starts watchdog thread (lines 528–536) when supervisor claims ownership |
| `addons/lugal_ws_migration/models/lugal_email_ws.py` | lugal_ws_migration | `create()` | 40–92 | Publishes `crm.email.message.new` to `supply_user.<uid>` bus channel + Web Push on every new inbox email |
