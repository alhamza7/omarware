# WebSocket Final Fix — Apply These 2 Changes to the Frontend

> **Status**: Backend fully verified and working. Two FE-only changes needed.

---

## Root Cause (Diagnosed from Server Logs)

`basicSsl()` in `vite.config.ts` makes Vite serve over **HTTPS** (`https://…:5174`).  
`BusClient.ts` then upgrades `ws://192.168.116.204:8076` → `wss://192.168.116.204:8076`.  
Port **8076 has NO TLS** → browser sends TLS ClientHello → Odoo logs `Invalid HTTP method: "\x16\x03\x01…"` → WebSocket **never connects**.

The fix: when HTTPS, route through the **Vite proxy** at the same origin instead of going directly to port 8076. Vite terminates TLS and forwards plain `ws://` to 8076.

---

## Change 1 — `src/shared/realtime/BusClient.ts`

Find this block (~lines 258–263):

```typescript
    // CRITICAL: Upgrade ws:// to wss:// if the page is served over HTTPS.
    // Browsers block mixed content (HTTPS page trying to connect to ws://).
    if (location.protocol === 'https:' && url.startsWith('ws://')) {
      url = url.replace('ws://', 'wss://');
      console.log('[BusClient] Upgraded ws:// to wss:// for HTTPS page');
    }
```

**Replace with:**

```typescript
    // When the page is HTTPS, the browser blocks plain ws:// (mixed content).
    // DO NOT upgrade the backend URL directly — port 8076 has no TLS and
    // would fail with an "Invalid HTTP method" TLS handshake error.
    // Instead, route through the Vite/Nginx proxy at the same origin:
    // the proxy handles TLS termination and forwards plain ws:// to port 8076.
    if (location.protocol === 'https:' && url.startsWith('ws://')) {
      const versionParam = this.wsVersion ? `?version=${this.wsVersion}` : '';
      url = `wss://${location.host}/websocket${versionParam}`;
      console.log('[BusClient] HTTPS: routing WS through proxy:', url);
    }
```

---

## Change 2 — `vite.config.ts`

Find this block (~lines 71–73):

```typescript
  const wsProxyEntry = isWsSandboxBranch
    ? { '/websocket': { target: 'ws://192.168.116.204:8076', ws: true, changeOrigin: true as const } }
    : {};
```

**Replace with:**

```typescript
  // WebSocket proxy — always active so HTTPS pages (basicSsl()) route correctly.
  // Vite terminates WSS and forwards plain WS to the gevent port.
  // In production Nginx handles this; the proxy is a no-op there.
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

---

## After Applying Changes

1. Restart Vite dev server
2. Hard-reload browser (`Ctrl+Shift+R`) on all devices
3. Verify in browser console:
   ```
   [BusClient] HTTPS: routing WS through proxy: wss://192.168.116.204:5174/websocket?version=saas-18.5-1
   [BusClient] WebSocket CONNECTED
   [BusClient] Sending subscribe frame (lastId: 0 )
   ```

---

## What the Backend Already Fixed (No Action Needed)

All changes below are already live on the server:

| Fix | Detail |
|-----|--------|
| **Stale session TypeError** | `_authenticate` override catches `TypeError` when `session_token=None` → closes WS with code 4001 → FE calls `_ensureSession()` → reconnects with fresh session |
| **ws.rollout.enabled** | Permanently set to `True` in DB via data XML — survives restarts and DB restores |
| **IDLE supervisor** | Watchdog thread running every 5s picks up new email accounts immediately |
| **supply.chat.resubscribe** | Sent to all participants when a new conversation is created → FE resubscribes to new channel automatically |
| **Channel auto-subscription** | On every WS connect, server adds `supply_chat.<id>`, `supply_user.<uid>`, `supply_stories` to the subscription |

---

## System Verification Results (Tested on Server)

```
✓ Login + session bridge          — JWT → Odoo session cookie
✓ ws_config                       — use_websocket=True, ws_url port 8076
✓ WS connect + subscribe          — Alpha connected in < 1s
✓ Chat delivery (Test 4)          — Alpha received supply.chat.message.new from Beta
✓ Chat stability (Test 6)         — Second pass: same result, consistent
✓ IDLE supervisor (pid=520446)    — Email watcher alive and running
✓ _authenticate override          — LugalIrWebsocket._authenticate active in MRO
✓ Real browser (192.168.116.228)  — Live session at 11:44 with read/delivered requests
```

---

## Connection Lifecycle (For Reference)

```
User logs in
  → BusClient.connect()
    → GET /api/crm/ws/config        — gets ws_url + use_websocket flag
    → POST /api/crm/ws/session      — JWT → Odoo session_id cookie (HttpOnly)
    → new WebSocket(wss://...:5174/websocket)   — through Vite proxy
    → Vite proxy → ws://192.168.116.204:8076    — plain WS to gevent
    → subscribe frame: { event_name: "subscribe", data: { channels: [], last: 0 } }
    → Server builds channel list: supply_chat.*, supply_user.<uid>, supply_stories
    → Events flow in real-time forever

New employee added
  → Server creates conversation
  → Sends supply.chat.resubscribe to supply_user.<uid> channel
  → FE calls busClient.resubscribe()
  → Server adds new supply_chat.<new_id> to subscription
  → Live from that moment, no restart needed

Session expires (code 4001)
  → BusClient._handleClose(4001)
  → calls _ensureSession() → POST /api/crm/ws/session → fresh cookie
  → calls _openSocket() → reconnects automatically

Network drop
  → _scheduleReconnect(false)
  → exponential backoff: 2s → 4s → 8s → ... → 30s cap
  → reconnects automatically when network recovers
```
