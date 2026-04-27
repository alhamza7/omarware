# FE Prompt — Complete Live WebSocket Connection Fix

## What's broken (confirmed from server logs)

```
RuntimeError: Couldn't bind the websocket.
Is the connection opened on the evented port (8076)?
```

The FE is connecting WebSocket to **port 8075** (Odoo HTTP port) instead of **port 8076**
(the gevent/WebSocket port). Port 8075 does NOT handle WebSocket upgrades. This is why:
- New users see no live chat
- Email notifications are delayed
- Incognito / second browser has no live connection

## Backend status (all fixed, nothing left to do on BE)

| Feature | Status |
|---|---|
| `ws_url` in `/api/crm/ws/config` now returns port **8076** | ✅ deployed |
| `ws/session` sets a persistent session cookie (Max-Age 1 day) | ✅ deployed |
| New DM/group → backend immediately sends `supply.chat.resubscribe` to all participants | ✅ deployed |
| New email account → IDLE watcher starts within 5 seconds | ✅ deployed |
| New user login → `_build_bus_channel_list` auto-subscribes them to all their channels | ✅ deployed |

---

## FE Changes Required

### 1. Use `ws_url` from backend — CRITICAL

Find wherever `BusClient` (or your WebSocket wrapper) builds the WebSocket URL and
**replace it entirely** with the URL from the config response.

**Current broken pattern (any of these):**
```typescript
// Broken: hardcoded localhost / wrong port
const wsUrl = `ws://localhost:${port}/websocket?version=${wsVersion}`;
const wsUrl = `ws://127.0.0.1:${port}/websocket?version=${wsVersion}`;
// Broken: derived from window.location — inherits the wrong port
const wsUrl = `ws://${window.location.hostname}:${port}/websocket?version=${wsVersion}`;
```

**Fix:**
```typescript
// Step 1: get WS config (includes correct ws_url with port 8076)
const config = await fetch('/api/crm/ws/config', {
  headers: { 'Authorization': `Bearer ${accessToken}` },
}).then(r => r.json());

// Step 2: use it directly — do NOT derive from window.location
// config.ws_url is already: ws://192.168.116.204:8076/websocket?version=saas-18.5-1
const wsUrl = config.ws_url;

// Step 3: connect
busClient.connect(wsUrl);
```

Fallback (in case `ws_url` is ever missing from older deployments):
```typescript
const wsVersion = config.ws_version ?? '';
const wsUrl = config.ws_url ?? (() => {
  const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${proto}//${window.location.host}/websocket?version=${wsVersion}`;
})();
```

---

### 2. Call `/api/crm/ws/session` after every login — CRITICAL

Without this, the browser has no `session_id` cookie, and the WebSocket handshake
is rejected with 401/403 — especially noticeable on new browsers and incognito.

**Sequence must be:**
```typescript
// After successful login:
const { access_token, refresh_token } = await loginApi({ username, password });
storeTokens(access_token, refresh_token);

// ALWAYS call ws/session next — this sets the session_id cookie the WS needs
await fetch('/api/crm/ws/session', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({}),
  credentials: 'include',  // ← REQUIRED: browser stores + sends the cookie
});

// Then get config and connect WS
const config = await fetch('/api/crm/ws/config', {
  headers: { 'Authorization': `Bearer ${access_token}` },
}).then(r => r.json());

busClient.connect(config.ws_url);
```

Also repeat `ws/session` + reconnect after **every token refresh**:
```typescript
onTokenRefresh(async (newToken) => {
  await fetch('/api/crm/ws/session', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${newToken}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({}),
    credentials: 'include',
  });
  busClient.resubscribe();
});
```

---

### 3. Handle `supply.chat.resubscribe` WS event

When User A creates a new DM or group with User B, the backend signals User B to
refresh their WS subscription so the new `supply_chat.<conv_id>` channel is included.

In `RealtimeProvider.tsx` (or wherever you handle BUS_EVENTS), add:

```typescript
if (type === 'supply.chat.resubscribe') {
  // A new conversation was just created for this user.
  // Call busClient.resubscribe() so Odoo re-runs _build_bus_channel_list
  // which now includes supply_chat.<new_conv_id>.
  busClient.resubscribe();

  // Also optionally refresh the conversations list so the new DM appears
  void queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'conversations'] });
  return;
}
```

> Note: `busClient.resubscribe()` should send a fresh WS subscribe message.
> In Odoo's BusClient this is the method that re-sends the subscription channel list
> to the server. The server re-runs `_build_bus_channel_list` which auto-includes
> all conversations the user is now in.

---

### 4. Handle `crm.email.message.new` WS event (if not already done)

When a new email arrives via IMAP IDLE, the backend publishes this on `supply_user.<uid>`.
See `FE_EMAIL_WS_PROMPT.md` for the full payload and handler.

```typescript
if (type === 'crm.email.message.new') {
  const payload = data as {
    account_id: number;
    message_id: number;
    subject: string;
    from_address: string;
    snippet: string;
    received_at: string;
  };
  // Show toast notification + increment email unread badge
  // Invalidate email queries for this account
  void queryClient.invalidateQueries({ queryKey: ['crm', 'email', 'messages', payload.account_id] });
  playNotificationSound();
  toast(`New email from ${payload.from_address}: ${payload.subject}`);
  return;
}
```

---

### 5. Handle notification sound for new users

If the notification sound doesn't play for newly created users, it's an AudioContext
autoplay policy issue. The browser blocks audio until the user interacts with the page.

Fix pattern:
```typescript
// In your audio utility — create AudioContext lazily on first user interaction
let audioCtx: AudioContext | null = null;

function ensureAudioCtx() {
  if (!audioCtx) {
    audioCtx = new AudioContext();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

// Call ensureAudioCtx() on any click/keydown anywhere in the app
document.addEventListener('click', () => ensureAudioCtx(), { once: false });

// Then in playNotificationSound():
async function playNotificationSound() {
  const ctx = ensureAudioCtx();
  // ... play your audio file using ctx
}
```

---

## Summary checklist

- [ ] **CRITICAL** Replace hardcoded/derived WS URL with `config.ws_url` from `/api/crm/ws/config`
- [ ] **CRITICAL** Add `credentials: 'include'` to the `/api/crm/ws/session` `fetch` call
- [ ] **CRITICAL** Call `/api/crm/ws/session` on every login (new users, new browsers, incognito)
- [ ] Re-call `/api/crm/ws/session` + `busClient.resubscribe()` after every token refresh
- [ ] Handle `supply.chat.resubscribe` WS event → `busClient.resubscribe()`
- [ ] Handle `crm.email.message.new` WS event → toast + invalidate email queries
- [ ] Fix AudioContext autoplay for notification sound on new users

## What happens after these changes

| Scenario | Before | After |
|---|---|---|
| New user logs in | WS fails (port 8075) | WS connects instantly (port 8076) |
| New user in incognito | WS fails (no session cookie) | WS connects (cookie set by ws/session) |
| User A creates DM with new User B | B has no WS channel for the DM | B receives `resubscribe` → auto-adds channel |
| Email arrives for new employee | Takes 1+ min (no IDLE watcher) | <5 seconds (watchdog picks up in 5s) |
| Notification sound for new user | Silent (AudioContext blocked) | Plays after first user interaction |
