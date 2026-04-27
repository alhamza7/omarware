# LocalSend CRM API

Integration module (`lugal_localsend`) — all endpoints are JSON-RPC and require a JWT bearer token.

- Method: `POST`
- Type: `jsonrpc`
- Base path: `/api/crm/localsend/*`
- Auth header: `Authorization: Bearer <access_token>`

Unauthorized response:
```json
{ "success": false, "error": "Unauthorized", "data": null }
```

---

## Architecture

**Odoo is a device directory only.** It stores each user's device IP and port so peers can find each other. The actual file transfer is **direct device-to-device (P2P)** — the file never touches the Odoo database or server.

```
Sender FE  →  Odoo: POST /resolve  →  returns target IP:Port
Sender FE  →  Target Device (LAN): POST /api/localsend/v2/prepare-upload
Sender FE  →  Target Device (LAN): POST /api/localsend/v2/upload?sessionId=...
```

The target device must have the **LocalSend app** running with "Receive mode" active.

---

## Quick Start

1. On login call **`/devices/register`** — sends the machine's LAN IP + port to the server.
   Always pass `lan_ip` with the real local network IP (e.g. `192.168.1.50`), otherwise the server
   may store the wrong IP (proxy/NAT).
2. Start a background heartbeat every **30 seconds** calling **`/devices/heartbeat`** to stay marked online.
3. To send a file to a colleague:
   - Call **`/resolve`** with `target_user_id` → receive `prepare_upload_url` and `upload_url`.
   - Call `prepare_upload_url` directly from the browser to the target device.
   - Upload the file directly to `upload_url` on the target device.

---

## Endpoints

### 1) Register Device

**POST** `/api/crm/localsend/devices/register`

Stores this user's device LAN address. One row per user — re-calling updates the existing row.

| Field | Required | Description |
|---|---|---|
| `lan_ip` | **recommended** | This machine's LAN IP (e.g. `192.168.1.50`). If omitted, server falls back to HTTP client IP which may be wrong behind a proxy. |
| `port` | no | LocalSend receiver port (default: `53317`) |
| `protocol` | no | `"http"` or `"https"` (default: `"http"`) |
| `device_name` | no | Display name (default: `"<username>'s Device"`) |
| `device_uid` | no | Stable fingerprint from the LocalSend app |

Response `data`: device object.

---

### 2) Heartbeat (keep-alive)

**POST** `/api/crm/localsend/devices/heartbeat`

Updates `is_online = true` and `last_seen = now`. Call every 30 seconds.
Pass `lan_ip` if the IP may change (DHCP).

Response `data`: device object.

---

### 3) Resolve Target (P2P connection info)

**POST** `/api/crm/localsend/resolve`

**This is the main endpoint for sending.** Returns all the URLs needed for the frontend to
initiate a direct LocalSend transfer without involving the Odoo server.

| Field | Required | Description |
|---|---|---|
| `target_user_id` | **yes** | Odoo user ID of the recipient |
| `target_device_id` | no | Only needed if the recipient has multiple registered machines |

Response:
```json
{
  "success": true,
  "data": {
    "device": { ...device fields... },
    "localsend_url": "http://192.168.1.50:53317",
    "prepare_upload_url": "http://192.168.1.50:53317/api/localsend/v2/prepare-upload",
    "upload_url": "http://192.168.1.50:53317/api/localsend/v2/upload",
    "sender_device": { ...sender device fields or null... }
  }
}
```

**Frontend flow after receiving this response:**

```js
// Step 1 — prepare-upload (tell target what's coming)
const prepareResp = await fetch(data.prepare_upload_url, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    info: {
      alias: senderDeviceName,
      version: "2.1",
      deviceModel: "Browser",
      deviceType: "browser",
      fingerprint: senderDeviceUid,
      port: 53317,
      protocol: "http",
      download: false,
    },
    files: {
      [fileId]: { id: fileId, fileName: file.name, size: file.size, fileType: file.type }
    }
  })
});
const { sessionId, files } = await prepareResp.json();
const token = files[fileId];

// Step 2 — upload directly to target device
await fetch(`${data.upload_url}?sessionId=${sessionId}&fileId=${fileId}&token=${token}`, {
  method: "POST",
  headers: { "Content-Type": file.type },
  body: file,
});
```

---

### 4) List Devices

**POST** `/api/crm/localsend/devices/list`

| Field | Required | Description |
|---|---|---|
| `owner_only` | no | `true` → only current user's devices |
| `online_only` | no | `true` → only devices currently online |

Response: `{ total, items[] }` — array of device objects.

---

### 5) Create Device (manual, manager use)

**POST** `/api/crm/localsend/devices/create`

Requires `name` and `ip_address`. Managers can assign to other users via `user_id`.

---

## Device Object Fields

| Field | Type | Description |
|---|---|---|
| `id` | int | |
| `name` | string | |
| `device_uid` | string | Stable fingerprint from LocalSend app |
| `ip_address` | string | LAN IP address |
| `port` | int | Default 53317 |
| `protocol` | string | `"http"` or `"https"` |
| `require_pin` | bool | Always `false` for auto-registered devices |
| `owner_user_id` | int | |
| `owner_name` | string | |
| `is_online` | bool | Updated by heartbeat |
| `last_seen` | string | ISO 8601 datetime |

---

## Security Groups

| Group | Access |
|---|---|
| `LocalSend User` | Own devices (read/write); read other users' online devices for discovery; no file access |
| `LocalSend Manager` | All devices |

> Files are never stored in Odoo. The `resolve` endpoint only returns connection metadata.
