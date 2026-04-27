# FE Live Connection — Required Fixes

**Date:** 2026-04-22  
**Backend:** `http://192.168.116.204:8075` / WS: `ws://192.168.116.204:8076`

These are the **only changes** you need to make. Everything else stays as-is.

---

## Fix 0 — Missing `?version=` param (why WS closes after 16ms)

**This is the root cause of why the live connection never works.**

Odoo's WebSocket server checks that every browser connection includes a version query param matching the server's internal version. If it's missing or wrong, the server **immediately closes the connection** with code 1000 and reason `"OUTDATED_VERSION"`. This happens before any message is exchanged — you connect, get 101, then the server closes in under 20ms.

**How to get the correct version** — call the ws/config endpoint:

```javascript
// Step 2 in your flow: GET /api/crm/ws/config now returns ws_version
const config = await fetch('/api/crm/ws/config', {
  headers: {
    Authorization: `Bearer ${jwt}`,
    'X-Odoo-Database': 'lugal_ws_sandbox',
  }
}).then(r => r.json());

// config = { use_websocket: true, fallback_on_error: true, ws_version: "saas-18.5-1" }
const { use_websocket, ws_version } = config;
```

**Use the version in the WS URL:**

```javascript
// ❌ WRONG — missing version, server closes immediately with code 1000
const ws = new WebSocket(`${proto}://${location.host}/websocket`);

// ✅ CORRECT — include the version the server returned from /api/crm/ws/config
const ws = new WebSocket(`${proto}://${location.host}/websocket?version=${ws_version}`);
```

**How to confirm this is your issue** in Chrome DevTools → Network → WS:
- Click the WS connection → Messages tab
- If it shows nothing OR the connection column shows a duration under 1 second → this is Fix 0
- Frames tab: if you see a Close frame with code 1000 right after open → confirmed

---

## Fix 1 — Wrong WebSocket URL (why messages never arrive)

Your WebSocket is connecting directly to the backend IP, which means the browser never sends the `session_id` cookie. Odoo receives the connection as an anonymous guest → subscribes to zero channels → you receive zero events.

**Find this in your code and change it:**

```javascript
// ❌ WRONG — remove this
const ws = new WebSocket("ws://192.168.116.204:8076/websocket");

// ✅ CORRECT — use this instead
const proto = location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${proto}://${location.host}/websocket`);
// When accessed via http://192.168.116.229:5174/  →  ws://192.168.116.229:5174/websocket
// Vite proxies that to ws://192.168.116.204:8076/websocket + forwards cookie → works ✓
```

**How to verify the fix in Chrome DevTools:**
1. Open DevTools → Network tab → filter by "WS"
2. The WebSocket connection must show `192.168.116.229:5174` (or `localhost:5174`) as the host
3. If it shows `192.168.116.204:8076` directly → fix not applied yet

---

## Fix 2 — Vite config must have `ws: true` for the websocket proxy

Open `vite.config.ts`. The `/websocket` entry must look exactly like this:

```typescript
'/websocket': {
  target: 'ws://192.168.116.204:8076',
  ws: true,          // ← this line is mandatory — without it Vite won't handle the WS upgrade
  changeOrigin: true,
},
```

**Full proxy block for reference:**

```typescript
export default defineConfig({
  server: {
    host: '0.0.0.0',  // allows access from other devices on the network
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
      '/websocket': {
        target: 'ws://192.168.116.204:8076',
        ws: true,
        changeOrigin: true,
      },
    },
  },
});
```

> **Restart Vite** after changing `vite.config.ts` — proxy changes do not hot-reload.

---

## Fix 3 — Session bridge now returns `Set-Cookie` automatically

The `/api/crm/ws/session` endpoint now sets the cookie for you in the HTTP response headers.

**Remove `document.cookie = ...` if you have it.** It is no longer needed and can cause issues.

**Before (what you likely have):**
```javascript
const res = await axios.post('/api/crm/ws/session', {}, {
  headers: { Authorization: `Bearer ${jwt}` }
});
const { session_id } = res.data.data;
document.cookie = `session_id=${session_id}; path=/; SameSite=Strict`; // ← REMOVE THIS
```

**After (correct):**
```javascript
const res = await axios.post('/api/crm/ws/session', {}, {
  headers: { Authorization: `Bearer ${jwt}` }
});
// That's it. The response includes Set-Cookie: session_id=...; Path=/; HttpOnly; SameSite=Lax
// The browser sets the cookie automatically. No manual document.cookie needed.
```

> Make sure your axios instance is configured with `withCredentials: true` so the browser stores and forwards cookies.

---

## Fix 4 — Subscribe frame must use exact field names

In `ws.onopen`, you must send this frame immediately:

```javascript
ws.send(JSON.stringify({
  event_name: "subscribe",     // ← must be "event_name", NOT "event_type"
  data: {
    channels: [],              // ← always empty — backend builds the full channel list
    last: 0,                   // ← must be "last", NOT "last_notification_id"
  }
}));
```

Wrong field names cause a silent failure — the connection stays open but you receive nothing.

---

## Fix 5 — Re-subscribe when a new conversation is created

When the user starts a new chat conversation, send a fresh subscribe frame so the new channel is added:

```javascript
function resubscribe(ws, lastId) {
  ws.send(JSON.stringify({
    event_name: "subscribe",
    data: { channels: [], last: lastId }
  }));
}

// Call after creating a new conversation:
resubscribe(ws, currentLastNotificationId);
```

---

## Fix 6 — WS URL must not use `X-Odoo-Database` header

The WebSocket upgrade is a standard HTTP GET — no custom headers are allowed by the browser.  
Do **not** add `X-Odoo-Database` when opening the WebSocket. Authentication is done entirely via the `session_id` cookie.

```javascript
// ❌ WRONG — browsers ignore custom headers on WS connections
const ws = new WebSocket(url, [], { headers: { 'X-Odoo-Database': 'lugal_ws_sandbox' } });

// ✅ CORRECT — no headers, just the URL
const ws = new WebSocket(url);
```

---

## Correct end-to-end flow (summary)

```
1. POST /lugal/auth/login
   Body: { jsonrpc: "2.0", method: "call", params: { username, password } }
   Header: X-Odoo-Database: lugal_ws_sandbox
   → save access_token

2. GET /api/crm/ws/config
   Header: Authorization: Bearer <access_token>
   Header: X-Odoo-Database: lugal_ws_sandbox
   → { use_websocket: true, fallback_on_error: true, ws_version: "saas-18.5-1" }
   → if use_websocket === false → skip WebSocket, use polling only
   → save ws_version for step 4

3. POST /api/crm/ws/session
   Header: Authorization: Bearer <access_token>
   Header: X-Odoo-Database: lugal_ws_sandbox
   → browser automatically receives Set-Cookie: session_id=...
   → NO document.cookie needed

4. const proto = location.protocol === 'https:' ? 'wss' : 'ws';
   const ws = new WebSocket(`${proto}://${location.host}/websocket?version=${ws_version}`);
   //                                                               ^^^^^^^^^^^^^^^^^^^
   //  MUST include ?version= or server closes immediately (code 1000, "OUTDATED_VERSION")
   //  MUST use location.host, NOT hardcoded 192.168.116.204:8076

5. ws.onopen = () => {
     ws.send(JSON.stringify({
       event_name: "subscribe",     // MUST be "event_name" not "event_type"
       data: { channels: [], last: 0 }  // MUST be "last" not "last_notification_id"
     }));
   };

6. ws.onmessage = (e) => {
     const events = JSON.parse(e.data);  // always an array
     for (const n of events) {
       const { type, payload } = n.message;
       handleEvent(type, payload);
     }
   };

7. ws.onclose = (e) => {
     if (e.code === 1000 && e.reason === 'OUTDATED_VERSION') {
       // Fetch new ws_version from /api/crm/ws/config and reconnect
       reconnectWithNewVersion();
     } else if (e.code === 1000) {
       return; // intentional close — do not reconnect
     } else if (e.code === 4001) {
       // session expired — redo steps 3-4, then reconnect
       refreshSessionAndReconnect();
     } else {
       reconnectWithBackoff();
     }
   };
```

---

## Quick self-check

Open Chrome DevTools → Network → WS. After login you should see:

| Check | Expected | How to verify |
|-------|----------|---------------|
| WS URL includes `?version=saas-18.5-1` | ✅ Yes | Network tab → WS request URL |
| WS URL uses `location.host` | ✅ Yes, e.g. `localhost:5174` — NOT `192.168.116.204` | Network tab → WS request URL |
| WS stays open > 5 seconds | ✅ Yes (if < 1s → Fix 0 not applied) | Network tab → WS row duration |
| WS response status | `101 Switching Protocols` | Network tab |
| `session_id` cookie exists before WS connect | ✅ Yes | Application → Cookies |
| Vite has `ws: true` in proxy | ✅ Yes | `vite.config.ts` |
| First frame sent | `{"event_name":"subscribe","data":{"channels":[],"last":0}}` | WS Frames tab |
| Messages received | Array of `{id, message: {type, payload}}` objects | WS Frames tab |
| WS onmessage wired to UI state updater | ✅ Yes | Send a message — does the other user's chat update instantly? |

**If WS connects for under 1 second** → Fix 0 not applied (missing `?version=`).  
If the WS host shows `192.168.116.204` → Fix 1 + Fix 2 are not applied.  
If WS status is `403` → session bridge was not called (Fix 3) or Vite was not restarted (Fix 2).  
If WS status is `101`, stays open, but no messages arrive → subscribe frame is wrong (Fix 4).
