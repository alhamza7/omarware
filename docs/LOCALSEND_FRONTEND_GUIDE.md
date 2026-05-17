# LocalSend File Transfer — Frontend Integration Guide
**Last updated:** 2026-05-17

---

## Overview

The LocalSend integration lets users send files to each other inside the CRM browser app.

**Key principle:** Files are stored on the Odoo server and **always downloadable via a browser URL**. LocalSend P2P delivery (direct device-to-device) is an optional fast-path — it works when the native LocalSend app is installed and open, but the file is always accessible from the browser regardless.

```
Sender (browser)
  └─→ POST /transfers/create
        │
        ├─→ ① Bus notification → receiver (download_url always included + access_token)
        │
        └─→ ② LocalSend TCP push attempted
              ├─ App open    → status: "sent"      + bus "localsend.transfer.sent"
              └─ App closed  → status: "available" + bus "localsend.transfer.available"
                               (file immediately downloadable via download_url — no login required)
```

---

## Table of Contents

1. [Request Format](#1-request-format)
2. [Authentication](#2-authentication)
3. [Device Registration](#3-device-registration)
4. [Real-time Events (Bus / WebSocket)](#4-real-time-events-bus--websocket)
5. [Sending a File](#5-sending-a-file)
6. [Receiving & Downloading a File](#6-receiving--downloading-a-file)
7. [Transfer Status Reference](#7-transfer-status-reference)
8. [All API Endpoints](#8-all-api-endpoints)
9. [Transfer Object Reference](#9-transfer-object-reference)
10. [Device Object Reference](#10-device-object-reference)
11. [Complete Integration Example](#11-complete-integration-example)

---

## 1. Request Format

All LocalSend endpoints use **JSON-RPC over HTTP POST**:

```http
POST /api/crm/localsend/...
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    ... your params here ...
  }
}
```

Response:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { ... }
  }
}
```

On error:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Human-readable error message",
    "data": { ... }
  }
}
```

---

## 2. Authentication

All endpoints require a JWT Bearer token in the `Authorization` header:

```
Authorization: Bearer eyJhbGci...
```

To get a token:

```http
POST /lugal/auth/login
{ "params": { "username": "user@example.com", "password": "secret" } }
```

Response: `{ "access_token": "...", "refresh_token": "..." }`

---

## 3. Device Registration

### Why it's needed

Every user must register their device (browser session) so Odoo knows their IP address and can track online status. Without registration, the user cannot be a sender or receiver.

### `POST /api/crm/localsend/devices/register`

Call **once per app startup** (or when the device IP changes).

**Request:**

```json
{
  "params": {
    "lan_ip": "192.168.1.100",
    "device_name": "Chrome on Ahmed's PC",
    "port": 53317,
    "protocol": "http",
    "device_uid": "optional-stable-unique-id"
  }
}
```

| Param | Required | Description |
|-------|----------|-------------|
| `lan_ip` | Recommended | LAN IP of this device. If omitted, Odoo uses the HTTP connection IP |
| `device_name` | No | Human label. Auto-generated as `"<username>'s Device"` if omitted |
| `port` | No | LocalSend port (default: `53317`) |
| `protocol` | No | `"http"` or `"https"` (default: `"http"`) |
| `device_uid` | No | Stable ID from the native LocalSend app, if available |

**Response:**

```json
{
  "success": true,
  "data": {
    "id": 9,
    "name": "Ahmed's Device",
    "ip_address": "192.168.1.100",
    "port": 53317,
    "protocol": "http",
    "is_online": true,
    "last_seen": "2026-05-17T09:00:00"
  }
}
```

---

### `POST /api/crm/localsend/devices/heartbeat`

Call **every 30 seconds** while the app is open.

**Why it matters:**
- Keeps `is_online = true` in the database
- If the device was previously marked offline (missed heartbeats), coming back online **automatically retries all `available` / `queued` / `failed` transfers** targeting this device

**Request:**

```json
{
  "params": {
    "lan_ip": "192.168.1.100"
  }
}
```

**Response:** same device object as register.

---

### `POST /api/crm/localsend/devices/<id>/ping`

Test if a specific device's LocalSend port (53317) is reachable — i.e., whether the native LocalSend app is running on that machine.

**Request:**

```json
{
  "params": {
    "timeout": 5
  }
}
```

| Param | Description |
|-------|-------------|
| `timeout` | TCP connect timeout in seconds. Default: 5, max: 15 |

**Response (reachable):**

```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "device_name": "Umar CTO's Device",
    "ip_address": "192.168.116.228",
    "port": 53317,
    "reachable": true,
    "reason": ""
  }
}
```

**Response (not reachable):**

```json
{
  "success": false,
  "error": "Device not reachable: Connection refused — LocalSend app is likely not running on the device.",
  "data": {
    "device_id": 1,
    "device_name": "Umar CTO's Device",
    "ip_address": "192.168.116.228",
    "port": 53317,
    "reachable": false,
    "reason": "Connection refused — LocalSend app is likely not running on the device."
  }
}
```

> Calling `/ping` also updates the device's `is_online` flag in the database.

---

### `POST /api/crm/localsend/devices/list`

List registered devices.

**Request:**

```json
{
  "params": {
    "owner_only": false,
    "online_only": false
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "total": 3,
    "items": [ { ... device objects ... } ]
  }
}
```

---

### `POST /api/crm/localsend/resolve`

Get the full connection info (LocalSend URLs) for a target user's device. Used if the FE wants to initiate a direct P2P transfer itself (bypassing the Odoo server).

**Request:**

```json
{
  "params": {
    "target_user_id": 32,
    "target_device_id": null
  }
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "device": { ... device object ... },
    "localsend_url": "http://192.168.116.228:53317",
    "prepare_upload_url": "http://192.168.116.228:53317/api/localsend/v2/prepare-upload",
    "upload_url": "http://192.168.116.228:53317/api/localsend/v2/upload",
    "sender_device": { ... your own device object ... }
  }
}
```

---

## 4. Real-time Events (Bus / WebSocket)

Subscribe to **`localsend_user.<your_user_id>`** on the Odoo bus to receive file transfer events in real time.

### Subscribing

**Via Odoo longpolling:**

```javascript
// POST /web/bus/poll
{
  "params": {
    "channels": ["localsend_user.52"],
    "last": 0
  }
}
```

**Via WebSocket:**

Connect to `ws://<server>:8076/websocket` and subscribe to channel `localsend_user.<uid>`.

---

### Event Types

| Event | Who receives it | When it fires |
|-------|----------------|--------------|
| `localsend.transfer.available` | **Receiver** + Sender | File ready to download from Odoo (LocalSend not running or transfer just created) |
| `localsend.transfer.sent` | **Receiver** + Sender | File delivered directly via LocalSend P2P |
| `localsend.transfer.downloaded` | **Sender** + Receiver | Receiver confirmed browser download |
| `localsend.transfer.cancelled` | Both | Transfer was cancelled |

---

### Event Payload (all events share this shape)

```json
{
  "transfer_id": 4,
  "name": "photo.jpg",
  "status": "available",
  "source_user_id": 52,
  "source_user_name": "Ahmed",
  "target_user_id": 32,
  "target_user_name": "Umar",
  "file_name": "photo.jpg",
  "file_size": 324524,
  "mime_type": "image/jpeg",
  "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
  "preview_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc",
  "error_message": "",
  "message": "Ahmed sent you 'photo.jpg'. You can download it now."
}
```

> **`download_url`** is always present in every event and includes an **`access_token`** — the link works directly in any browser without an Odoo session or login.

---

### Handling Events

```javascript
busService.subscribe('localsend_user.' + currentUserId, (eventType, payload) => {

  if (eventType === 'localsend.transfer.available') {
    // File is ready to download (LocalSend was not running on target device)
    showNotification({
      title: `📎 ${payload.source_user_name} sent you a file`,
      body:  `"${payload.file_name}" — ${formatBytes(payload.file_size)}`,
      actions: [
        {
          label: 'Download',
          onClick: () => handleDownload(payload.transfer_id, payload.download_url, payload.file_name),
        },
        {
          label: 'Preview',
          onClick: () => window.open(payload.preview_url, '_blank'),
        },
      ],
    });
  }

  if (eventType === 'localsend.transfer.sent') {
    // File was delivered directly via LocalSend (native app was open)
    if (payload.target_user_id === currentUserId) {
      showToast(`✅ "${payload.file_name}" was delivered to your device via LocalSend`);
    } else {
      showToast(`✅ "${payload.file_name}" sent successfully via LocalSend`);
    }
  }

  if (eventType === 'localsend.transfer.downloaded') {
    // Receiver confirmed they downloaded the file
    if (payload.source_user_id === currentUserId) {
      showToast(`✅ ${payload.target_user_name} downloaded "${payload.file_name}"`);
    }
  }

  if (eventType === 'localsend.transfer.cancelled') {
    dismissNotification(payload.transfer_id);
  }

});

async function handleDownload(transferId, downloadUrl, fileName) {
  // Trigger browser download
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);

  // Tell the server the file was downloaded (notifies sender)
  await api.post(`/api/crm/localsend/transfers/${transferId}/downloaded`);
}
```

---

## 5. Sending a File

### Step 1 — Upload the file to Odoo

First upload the file as an `ir.attachment` to get an `attachment_id`:

```javascript
async function uploadFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch('/api/crm/upload/document', {
    method: 'POST',
    headers: { 'Authorization': 'Bearer ' + token },
    body: formData,
  });

  const result = await response.json();
  return result.data.attachment_id;
}
```

---

### Step 2 — Create the transfer

```http
POST /api/crm/localsend/transfers/create
```

**Request:**

```json
{
  "params": {
    "target_user_id": 32,
    "attachment_id": 379001,
    "name": "Project Photo",
    "send_now": true
  }
}
```

| Param | Required | Description |
|-------|----------|-------------|
| `target_user_id` | **Yes** | User ID of the recipient |
| `attachment_id` | **Yes** | ID of the uploaded file (from Step 1) |
| `name` | No | Human label for the transfer. Defaults to filename |
| `send_now` | No | `true` (default): attempt LocalSend push immediately. `false`: just queue it |

**What happens internally:**

1. Transfer record created with `status: "draft"` → immediately changes
2. **Bus notification sent immediately to receiver** with `download_url` (with `access_token`) — the receiver can already download it
3. If `send_now: true`: LocalSend TCP push attempted
   - App open → `status: "sent"`, bus event `localsend.transfer.sent`
   - App closed → `status: "available"`, bus event `localsend.transfer.available` (file immediately downloadable)

**Response (LocalSend succeeded):**

```json
{
  "success": true,
  "data": {
    "id": 4,
    "status": "sent",
    "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
    "preview_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc",
    "file_name": "photo.jpg",
    "file_size": 324524,
    "mime_type": "image/jpeg",
    "target_device_ip": "192.168.116.228",
    "target_device_port": 53317,
    "target_device_url": "http://192.168.116.228:53317"
  }
}
```

**Response (LocalSend not running — graceful fallback):**

```json
{
  "success": true,
  "data": {
    "id": 4,
    "status": "available",
    "error_message": "LocalSend app is not running on Umar CTO's Device (192.168.116.228:53317). The file is available for download from the app.",
    "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
    "preview_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc"
  }
}
```

> **`success: true`** even when LocalSend is not running — the file is `available` for browser download and the receiver was notified. This is **not** an error.

---

### Retrying an available/failed transfer

If the receiver later opens LocalSend, the heartbeat auto-retries automatically. But you can also retry manually:

```http
POST /api/crm/localsend/transfers/4/retry
```

No body required.

---

## 6. Receiving & Downloading a File

### Option A — From a bus notification (recommended)

When you receive a `localsend.transfer.available` or `localsend.transfer.sent` event, the payload contains `download_url`. Use it:

```javascript
// Download the file
window.location.href = payload.download_url;
// OR open in new tab for preview
window.open(payload.preview_url, '_blank');

// Confirm receipt (notifies sender)
await api.post(`/api/crm/localsend/transfers/${payload.transfer_id}/downloaded`);
```

### Option B — From the transfers list

```http
POST /api/crm/localsend/transfers/list
{ "params": { "direction": "received", "status": "available" } }
```

Then use `item.download_url` from each item.

### Download URL format

```
/web/content/<attachment_id>?download=true
```

This is a standard Odoo URL. The browser will prompt a file save dialog.

**Preview URL** (no download prompt, inline display):

```
/web/content/<attachment_id>
```

Good for images, PDFs shown in `<img>` or `<iframe>`.

---

## 7. Transfer Status Reference

| Status | Meaning | Suggested FE Display |
|--------|---------|----------------------|
| `draft` | Created but not yet sent | Internal — usually transient |
| `available` | LocalSend not reachable; file is on Odoo and **immediately downloadable** | 📥 Show **Download** button + "File available" |
| `sending` | LocalSend push in progress | ⏳ Spinner |
| `sent` | Delivered directly via LocalSend P2P | ✅ "Delivered via LocalSend" |
| `downloaded` | Receiver confirmed browser download | ✅ "Downloaded by receiver" |
| `failed` | Unrecoverable error | ❌ Show error + Retry button |
| `cancelled` | Cancelled by sender | — |

> **`queued`** is an internal/legacy status — you should not normally see it. All graceful fallbacks now set `available`.

> For `available` and `sent` — always show `download_url`. The file is ready. `download_url` includes an `access_token` and works in any browser without login.

---

## 8. All API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /api/crm/localsend/devices/register` | Register this browser session's device |
| `POST /api/crm/localsend/devices/heartbeat` | Keep-alive every 30s; auto-retries `available`/`failed` transfers |
| `POST /api/crm/localsend/devices/list` | List registered devices |
| `POST /api/crm/localsend/devices/<id>/ping` | TCP check — is LocalSend app running on that device? |
| `POST /api/crm/localsend/devices/create` | Manually create a device record (admin use) |
| `POST /api/crm/localsend/resolve` | Get LocalSend P2P URLs for a user's device |
| `POST /api/crm/localsend/transfers/create` | Send a file |
| `POST /api/crm/localsend/transfers/list` | List sent/received transfers |
| `POST /api/crm/localsend/transfers/<id>/retry` | Retry a queued/failed transfer via LocalSend |
| `POST /api/crm/localsend/transfers/<id>/send` | Trigger LocalSend push for existing transfer |
| `POST /api/crm/localsend/transfers/<id>/downloaded` | Receiver confirms browser download |
| `POST /api/crm/localsend/transfers/<id>/cancel` | Cancel a transfer |

---

## 9. Transfer Object Reference

Every transfer API response and bus event payload includes these fields:

```json
{
  "id": 4,
  "name": "photo.jpg",
  "status": "available",

  "source_user_id": 52,
  "source_user_name": "Ahmed",
  "target_user_id": 32,
  "target_user_name": "Umar",

  "source_device_id": 9,
  "source_device_name": "Ahmed's Device",
  "target_device_id": 1,
  "target_device_name": "Umar CTO's Device",
  "target_device_ip": "192.168.116.228",
  "target_device_port": 53317,
  "target_device_url": "http://192.168.116.228:53317",

  "attachment_id": 379001,
  "file_name": "photo.jpg",
  "file_size": 324524,
  "mime_type": "image/jpeg",

  "download_url": "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc&download=true",
  "preview_url":  "/web/content/379001?access_token=4843d30571864e48aee66c26c921eedc",

  "error_message": "",
  "localsend_session_id": "",

  "started_at": "2026-05-17T08:44:50",
  "finished_at": null,
  "created_at": "2026-05-17T08:44:17.232540"
}
```

> **`download_url`** and **`preview_url`** include a permanent `access_token` — paste them directly into an `<a href>` or `window.location.href`. No Odoo login required.

---

## 10. Device Object Reference

```json
{
  "id": 9,
  "name": "Ahmed's Device",
  "device_uid": "optional-uid",
  "ip_address": "192.168.116.228",
  "port": 53317,
  "protocol": "http",
  "require_pin": false,
  "owner_user_id": 52,
  "owner_name": "Ahmed",
  "is_online": true,
  "last_seen": "2026-05-17T09:27:26"
}
```

---

## 11. Complete Integration Example

Full working example covering registration, bus subscription, send, receive, and download:

```javascript
class LocalSendService {
  constructor(api, busService, currentUserId, myLanIp) {
    this.api = api;
    this.currentUserId = currentUserId;
    this.myLanIp = myLanIp;
    this.heartbeatTimer = null;
  }

  // ── Startup ──────────────────────────────────────────────────────────────

  async init() {
    // 1. Register device
    await this.register();

    // 2. Subscribe to bus events
    busService.subscribe('localsend_user.' + this.currentUserId, (event, payload) => {
      this.handleEvent(event, payload);
    });

    // 3. Start heartbeat
    this.heartbeatTimer = setInterval(() => this.heartbeat(), 30_000);
  }

  async register() {
    return this.api.post('/api/crm/localsend/devices/register', {
      lan_ip:      this.myLanIp,
      device_name: navigator.userAgent.includes('Chrome') ? 'Chrome Browser' : 'Browser',
    });
  }

  async heartbeat() {
    return this.api.post('/api/crm/localsend/devices/heartbeat', {
      lan_ip: this.myLanIp,
    });
  }

  // ── Send ─────────────────────────────────────────────────────────────────

  async sendFile(file, targetUserId) {
    // Step 1: Upload file to Odoo
    const formData = new FormData();
    formData.append('file', file);
    const uploadResp = await fetch('/api/crm/upload/document', {
      method: 'POST',
      headers: { 'Authorization': 'Bearer ' + this.api.token },
      body: formData,
    });
    const { data: { attachment_id } } = await uploadResp.json();

    // Step 2: Create transfer
    const resp = await this.api.post('/api/crm/localsend/transfers/create', {
      target_user_id: targetUserId,
      attachment_id:  attachment_id,
      send_now:       true,
    });

    if (!resp.success && resp.data?.status !== 'available') {
      throw new Error(resp.error);
    }

    // Always return download_url — includes access_token, works without login
    return {
      transferId:  resp.data.id,
      status:      resp.data.status,  // "sent" | "available"
      downloadUrl: resp.data.download_url,  // already has ?access_token=...
    };
  }

  async retryTransfer(transferId) {
    return this.api.post(`/api/crm/localsend/transfers/${transferId}/retry`);
  }

  async cancelTransfer(transferId) {
    return this.api.post(`/api/crm/localsend/transfers/${transferId}/cancel`);
  }

  // ── Receive ───────────────────────────────────────────────────────────────

  async downloadTransfer(transferId, downloadUrl, fileName) {
    // Trigger browser download
    const a = document.createElement('a');
    a.href = downloadUrl;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    // Notify server — marks as "downloaded" and notifies sender
    await this.api.post(`/api/crm/localsend/transfers/${transferId}/downloaded`);
  }

  // ── Real-time events ──────────────────────────────────────────────────────

  handleEvent(eventType, payload) {
    switch (eventType) {

      case 'localsend.transfer.available':
        // File is ready to download (LocalSend not used / not running)
        this.showIncomingFile(payload);
        break;

      case 'localsend.transfer.sent':
        // File delivered via LocalSend P2P
        if (payload.target_user_id === this.currentUserId) {
          this.showToast(`✅ "${payload.file_name}" arrived via LocalSend`);
          // Still offer download from Odoo as backup
          this.showDownloadButton(payload);
        } else {
          this.showToast(`✅ "${payload.file_name}" delivered via LocalSend`);
        }
        break;

      case 'localsend.transfer.downloaded':
        // Receiver confirmed download — notify sender
        if (payload.source_user_id === this.currentUserId) {
          this.showToast(`✅ ${payload.target_user_name} downloaded "${payload.file_name}"`);
        }
        break;

      case 'localsend.transfer.cancelled':
        this.dismissNotification(payload.transfer_id);
        break;
    }
  }

  showIncomingFile(payload) {
    // Show notification banner with download button
    const notification = {
      id:      payload.transfer_id,
      title:   `📎 ${payload.source_user_name} sent you a file`,
      body:    `"${payload.file_name}" · ${this.formatBytes(payload.file_size)}`,
      actions: [
        {
          label:   'Download',
          primary: true,
          onClick: () => this.downloadTransfer(
            payload.transfer_id,
            payload.download_url,
            payload.file_name,
          ),
        },
        {
          label:   'Preview',
          onClick: () => window.open(payload.preview_url, '_blank'),
        },
      ],
    };
    this.notify(notification);
  }

  showDownloadButton(payload) {
    // For LocalSend-delivered files, also offer browser download as backup
    this.notify({
      id:      'download_' + payload.transfer_id,
      title:   `📁 "${payload.file_name}" available`,
      body:    'File also available for browser download',
      actions: [{
        label:   'Download',
        onClick: () => this.downloadTransfer(
          payload.transfer_id,
          payload.download_url,
          payload.file_name,
        ),
      }],
    });
  }

  // ── Utilities ─────────────────────────────────────────────────────────────

  async listTransfers(direction = 'all', status = null, limit = 50, offset = 0) {
    const params = { direction, limit, offset };
    if (status) params.status = status;
    return this.api.post('/api/crm/localsend/transfers/list', params);
  }

  async pingDevice(deviceId) {
    return this.api.post(`/api/crm/localsend/devices/${deviceId}/ping`, { timeout: 5 });
  }

  formatBytes(bytes) {
    if (bytes < 1024)        return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  }

  destroy() {
    clearInterval(this.heartbeatTimer);
  }
}

// ── Usage ─────────────────────────────────────────────────────────────────────

const localSend = new LocalSendService(api, busService, currentUser.id, myLanIp);
await localSend.init();

// Send a file
const fileInput = document.querySelector('#file-input');
fileInput.addEventListener('change', async (e) => {
  const file = e.target.files[0];
  const result = await localSend.sendFile(file, targetUserId);

  if (result.status === 'sent') {
    showToast('File delivered via LocalSend!');
  } else {
    // status === 'available' — file is on server, receiver was notified
    showToast('File available — receiver can download from the browser.');
  }
  console.log('File always accessible at:', result.downloadUrl);
});
```

---

## FAQ

**Q: The transfer says `"available"` instead of `"sent"` — is that an error?**  
No. It means the LocalSend app was not running on the receiver's device. The file is already on the Odoo server and the receiver got a bus notification with a `download_url` (including access token). They can download it immediately from the browser — no login needed.

**Q: When will the transfer auto-retry via LocalSend?**  
When the receiver's device calls `/devices/heartbeat` after having been offline. The heartbeat auto-retries all transfers in `available` / `failed` status targeting that device. This happens when the LocalSend native app is opened (it sends heartbeats) or when the CRM is reopened in the browser.

**Q: What if the receiver never downloads the file?**  
The file stays in `status: "available"`. The sender can resend a reminder or retry via `/transfers/<id>/retry`. The file stays accessible via `download_url` indefinitely (as long as it's not deleted from Odoo).

**Q: Do I need an Odoo session to use `download_url`?**  
No. The URL includes a permanent `access_token` parameter. You can paste it directly in a browser, put it in an `<a href>`, or trigger it with `window.location.href`. No authentication required.

**Q: How do I get the receiver's `target_user_id`?**  
From `/api/crm/users/list` — search by name or email and use the `id` field.

**Q: Does the sender also need to register a device?**  
Yes. Call `/devices/register` for both sender and receiver. The sender device is used as the `source_device_id` on the transfer record.

**Q: What file types / sizes are supported?**  
Any file type. Size limit is determined by Odoo's upload limit (default 1 GB for supply chat uploads; check your server config). The `file_size` is stored in bytes on the transfer object.
