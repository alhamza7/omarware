# FE Prompt — Fix WebSocket URL + New User Live Connection

## Problem (updated)
Two related errors reported:
1. `WebSocket connection to 'ws://127.0.0.1:61528/' failed` — localhost hardcoded
2. `WebSocket connection to 'ws://192.168.116.204:8075/websocket?version=saas-18.5-1' failed`
   — correct IP but **wrong port**: `8075` is Odoo's HTTP port; WebSocket is on `8076`

Both fail because the FE is NOT using the `ws_url` provided by the backend config.

---

## Backend change already deployed
`GET /api/crm/ws/config` now returns `ws_url` — the full, correct WebSocket URL
using the **gevent port (8076)** derived from the server's Odoo configuration:

```json
{
  "use_websocket": true,
  "ws_version": "saas-18.5-1",
  "ws_url": "ws://192.168.116.204:8076/websocket?version=saas-18.5-1",
  "fallback_on_error": true
}
```

The URL always uses the correct WebSocket port (`8076`) regardless of which port
or browser the FE is accessed from.

---

## FE Changes Required

### 1. Use `ws_url` from the config response

In the file where `BusClient` (or your WebSocket wrapper) is initialized, replace
the hardcoded URL construction with the backend-provided `ws_url`:

```typescript
// BEFORE (broken on other devices):
const wsVersion = config.ws_version;
const wsUrl = `ws://localhost:${SOME_PORT}/websocket?version=${wsVersion}`;

// AFTER (correct — works from any browser, any machine):
const wsUrl = config.ws_url;   // already includes ?version=...
```

If you need a fallback (in case `ws_url` is absent in older deployments):
```typescript
const wsVersion = config.ws_version ?? '';
const wsUrl = config.ws_url
  ?? (() => {
       const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
       return `${proto}//${window.location.host}/websocket?version=${wsVersion}`;
     })();
```

### 2. Ensure `/api/crm/ws/session` is called after every login

This applies to ALL users (existing and newly created). The sequence must be:

```typescript
// Step 1: authenticate
const { access_token } = await loginApi({ username, password });
storeTokens(access_token, refresh_token);

// Step 2: ALWAYS create the WS session — this sets the session_id cookie
//          that the WebSocket handshake requires.
await fetch('/api/crm/ws/session', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({}),
  credentials: 'include',   // ← REQUIRED: tells fetch to store + send cookies
});

// Step 3: get WS config (includes ws_url)
const config = await fetch('/api/crm/ws/config', {
  headers: { 'Authorization': `Bearer ${access_token}` },
}).then(r => r.json());

// Step 4: connect WebSocket using the URL from config
busClient.connect(config.ws_url);
```

**`credentials: 'include'` is critical** — without it the browser discards the
`Set-Cookie` header and the WebSocket handshake fails with 401/403.

### 3. Reconnect / resubscribe on token refresh

Whenever the access token is refreshed (the `remember_me` flow or silent refresh),
repeat steps 2–4 to refresh the session cookie and reconnect the WebSocket.

```typescript
// In your auth refresh handler:
onTokenRefresh(async (newToken) => {
  await refreshWsSession(newToken);   // calls /api/crm/ws/session
  busClient.resubscribe();            // re-sends subscription list to Odoo
});
```

### 4. Handle `supply.chat.resubscribe` for new conversations

When the backend creates a new DM or group for a user who has no prior
conversations, it sends a `supply.chat.resubscribe` event on `supply_user.<uid>`.
The FE must call `bus_channels` and re-subscribe when this event arrives:

```typescript
// In RealtimeProvider.tsx — alongside other BUS_EVENTS handlers:
if (type === 'supply.chat.resubscribe') {
  // New conversation was created — fetch updated channel list and resubscribe
  const channels = await fetchBusChannels();   // GET /api/crm/supply/chat/bus_channels
  busClient.updateSubscriptions(channels);     // your BusClient method
  return;
}
```

---

## Summary checklist

- [ ] Replace hardcoded WebSocket URL with `config.ws_url` from `/api/crm/ws/config`
- [ ] Add `credentials: 'include'` to the `/api/crm/ws/session` fetch call
- [ ] Call `/api/crm/ws/session` on every login (including new users, new browsers)
- [ ] Re-call `/api/crm/ws/session` + `busClient.resubscribe()` after token refresh
- [ ] Handle `supply.chat.resubscribe` WS event to pick up new conversations
- [ ] Handle `crm.email.message.new` WS event (see `FE_EMAIL_WS_PROMPT.md`)
