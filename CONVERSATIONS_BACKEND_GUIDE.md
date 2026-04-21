# Conversations — Frontend Integration Guide (Production Edition)

> **Audience:** Frontend engineers integrating Chat and Email into the Conversations feature.  
> **Backend:** Odoo 19 · lugal_crm + lugal_email addons.  
> **Last updated:** 2026-04-20

---

## Table of Contents

1. [What Changed](#1-what-changed)
2. [Authentication](#2-authentication)
3. [User Roles — Who Can Do What](#3-user-roles--who-can-do-what)
4. [Unified CRM Notifications](#4-unified-crm-notifications)
5. [Chat — Supply Chat API](#5-chat--supply-chat-api)
   - 5.1 [Base URL & Envelope](#51-base-url--envelope)
   - 5.2 [Conversations](#52-conversations)
   - 5.3 [Messages — All Types](#53-messages--all-types)
   - 5.4 [File, Image & Video Upload](#54-file-image--video-upload)
   - 5.5 [Audio & Voice Messages](#55-audio--voice-messages)
   - 5.6 [Delivery Ticks — Single / Double / Blue](#56-delivery-ticks--single--double--blue)
   - 5.7 [Typing Indicators](#57-typing-indicators)
   - 5.8 [Real-time: bus_channels + /web/bus/poll](#58-real-time-bus_channels--webbuspoll)
   - 5.9 [Group Members](#59-group-members)
   - 5.10 [Correct Integration Sequence](#510-correct-integration-sequence)
6. [Email — Lugal Email API](#6-email--lugal-email-api)
   - 6.1 [Accounts](#61-accounts)
   - 6.2 [Mailbox](#62-mailbox)
   - 6.3 [Compose — Send / Reply / Forward](#63-compose--send--reply--forward)
   - 6.4 [Email Attachments Upload](#64-email-attachments-upload)
   - 6.5 [Email Notifications & Polling](#65-email-notifications--polling)
7. [CRM Email Helpers (JSON-RPC)](#7-crm-email-helpers-json-rpc)
8. [Complete TypeScript Shapes](#8-complete-typescript-shapes)
9. [Backend Restart Required](#9-backend-restart-required)

---

## 1. What Changed

| Area | Before | Now |
|------|--------|-----|
| `GET /api/crm/notifications` | Missing | **New** — unified chat + email unread counts |
| `POST /api/crm/notifications/mark_read` | Missing | **New** — mark all/chat/email read at once |
| `/web/bus/poll` | Not registered → 404 | **Working** |
| `bus_channels` endpoint | Missing | **Working** |
| All conversation/message routes | Missing | **All implemented** |
| `delivery_state` on messages | Missing | On every message response |
| `kind` field on messages | Missing | `text`\|`image`\|`video`\|`audio`\|`voice`\|`file` |
| `duration_seconds` on messages | Missing | Float, seconds for audio/video |
| Audio/voice upload | MIME blocked | **Supported** (mp3, ogg, webm, wav, aac, amr…) |
| Video upload | MIME blocked | **Supported** up to **100 MB** (mp4, webm, mov…) |
| Email attachment upload | Missing | **New** `/api/lugal/email/attachments/upload` |
| Email BCC stored in DB | Not stored | **Fixed** — `bcc_addresses` persisted |
| Multiple CC / BCC | Worked via SMTP, not stored | **Fixed** — stored and returned |

---

## 2. Authentication

```
Authorization: Bearer <lugal_jwt_or_crm_jwt>
```

- `401` = token missing or expired → redirect to login.
- All supply chat and CRM notification routes accept the same Bearer token used for other CRM calls.
- All Lugal email routes use the same token.

---

## 3. User Roles — Who Can Do What

All authenticated users (any valid JWT) can use the full chat and email APIs. There are **no role restrictions** on supply chat — any user can:

- Create DMs and group conversations
- Send/edit/delete/react to messages
- Upload files, images, audio, video
- Access team channels (broadcast channels)

**The only access controls are:**
- DM and group conversations: only **participants** can see messages or send
- Team channels: any authenticated user can read and write
- Delete-for-everyone: only the **original sender** of the message
- Email: each user only sees their own accounts (`account_id.user_id === current_user`)

> **FE tip:** Do not build role-based UI around chat. Show all features to all logged-in users.

---

## 4. Unified CRM Notifications

One endpoint replaces separate polling of chat and email unread counts. Use this to drive the global badge/notification bell.

### `GET /api/crm/notifications`

**Query params:**

| Param | Default | Notes |
|-------|---------|-------|
| `since` | — | ISO-8601 UTC. Only count items created after this time. |
| `limit` | 20 | Max items per section (capped at 50). |

**Response:**
```json
{
  "success": true,
  "data": {
    "total_unread": 5,
    "chat": {
      "unread": 3,
      "conversations": [
        {
          "id":            8,
          "name":          "PO Review",
          "type":          "group",
          "unread_count":  3,
          "last_message":  "Can you confirm the delivery date?",
          "last_activity": "2026-04-20T10:14:00"
        }
      ]
    },
    "email": {
      "unread": 2,
      "items": [
        {
          "id":           55,
          "account_id":   30,
          "subject":      "Invoice #1234",
          "from_name":    "Alice",
          "from_address": "alice@example.com",
          "date":         "2026-04-20T10:13:00"
        }
      ]
    },
    "checked_at": "2026-04-20T10:15:30"
  }
}
```

**Audio/video message previews:** the `last_message` field returns emoji previews for media:
- `🎤 Voice message`
- `🎵 Audio`
- `🎥 Video`
- `🖼 Image`
- `📎 File`

---

### `POST /api/crm/notifications/mark_read`

**Body options:**

```json
// Mark all unread in one chat conversation
{ "type": "chat", "conversation_id": 8 }

// Mark specific email messages as read
{ "type": "email", "message_ids": [55, 56] }

// Mark everything (all chat + all inbox email)
{ "type": "all" }
```

**Response:**
```json
{ "success": true, "data": { "chat_marked": 3, "email_marked": 2 } }
```

**When to call:**
- When the user opens the notifications panel and dismisses it → `{ "type": "all" }`
- When the user opens a specific conversation → `{ "type": "chat", "conversation_id": X }`
- When the user opens an email → `{ "type": "email", "message_ids": [X] }`

---

### Polling pattern (React example)

```ts
let lastChecked = '';

async function pollNotifications() {
  const url = lastChecked
    ? `/api/crm/notifications?since=${lastChecked}`
    : '/api/crm/notifications';

  const res  = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  const json = await res.json();
  const data = json.data;

  // Update global badge
  setTotalUnread(data.total_unread);
  setChatUnread(data.chat.unread);
  setEmailUnread(data.email.unread);

  // Toast for new chat messages
  for (const conv of data.chat.conversations) {
    showChatToast(conv.name, conv.last_message, conv.id);
  }

  // Toast for new emails
  for (const email of data.email.items) {
    showEmailToast(email.from_name, email.subject, email.id);
  }

  lastChecked = data.checked_at;
}

setInterval(pollNotifications, 15_000);   // poll every 15 seconds
```

---

## 5. Chat — Supply Chat API

### 5.1 Base URL & Envelope

- All chat routes: **JSON-RPC 2.0 POST**
- Base prefix: `/api/crm/supply/`
- `crmPost()` in your `crmApiClient` wraps the envelope automatically.

```json
// Unwrapped response shape (crmApiClient removes the jsonrpc wrapper)
{ "success": true, "data": { ... } }
```

---

### 5.2 Conversations

| Route | Purpose |
|-------|---------|
| `POST /conversations/list` | All non-archived conversations for the user |
| `POST /conversations/create` | New DM (1 recipient) or group (2+) |
| `POST /conversations/<id>/get` | Refresh one conversation |
| `POST /conversations/<id>/rename` | Rename a group |
| `POST /conversations/<id>/archive` | Archive dm/group |
| `POST /conversations/<id>/leave` | Leave group |
| `POST /conversations/<id>/update` | Update name / metadata |
| `POST /conversations/<id>/mark_read` | Mark all messages in conv as read |
| `POST /conversations/<id>/typing` | Signal typing start/stop |
| `POST /conversations/<id>/members/list` | List members |
| `POST /conversations/<id>/members/add` | Add users: `{ "user_ids": [5, 12] }` |
| `POST /conversations/<id>/members/remove` | Remove user: `{ "user_id": 5 }` |

**`conversations/list` response:**
```json
{
  "success": true,
  "data": {
    "items": [ /* CrmSupplyConversation[] */ ],
    "total": 3
  }
}
```

**`conversations/create` params:**
```json
{ "recipient_ids": [5], "group_name": "PO Review" }
```
Idempotent — returns existing DM/group if same participants exist.

---

### 5.3 Messages — All Types

#### `POST /messages/list`

```json
{
  "thread_id": 8,
  "page": 1,
  "per_page": 50
}
```

Or by recipients (auto-creates thread if needed):
```json
{ "recipient_ids": [5, 12], "page": 1, "per_page": 50 }
```

#### `POST /messages/create`

```json
{
  "thread_id": 8,
  "content":   "See the attached invoice",

  // Message kind — drives FE rendering
  "kind":             "text",   // "text"|"image"|"video"|"audio"|"voice"|"file"
  "duration_seconds": 0,        // seconds, for audio/video/voice

  // Attachments — use IDs from /chat/upload
  "attachment_ids": [101, 102],

  // Quote/reply
  "reply_to_id": 47
}
```

> **Kind is auto-inferred** from `attachment_ids` if not provided:
> - audio/* → `"audio"` (or `"voice"` if filename contains "voice")
> - video/* → `"video"`
> - image/* → `"image"`
> - other → `"file"`

#### `POST /messages/<id>/edit`
```json
{ "content": "Updated text" }
```

#### `POST /messages/<id>/react`
```json
{ "emoji": "👍" }
```
Toggle — calling same emoji again removes it.

#### `POST /messages/<id>/delete`
```json
{ "for_everyone": true }   // sender only; replaces content with placeholder
// OR
{ "for_me": true }         // hides for current user only, others still see it
```

#### `POST /messages/forward`
```json
{ "message_id": 47, "thread_id": 12 }
```

#### `POST /messages/search`
```json
{ "query": "invoice", "thread_id": 8, "page": 1, "per_page": 20 }
```

---

### 5.4 File, Image & Video Upload

#### `POST /api/crm/supply/chat/upload` — multipart/form-data

Upload before calling `messages/create`. Returns file IDs to pass in `attachment_ids`.

**Form fields:**

| Field | Required | Notes |
|-------|----------|-------|
| `file` / `files` / `files[]` | Yes | Binary file parts |
| `conversation_id` | No | Links attachment to the conversation |
| `kind` | No | Hint: `image`\|`video`\|`audio`\|`voice`\|`file` |
| `duration_seconds` | No | For audio/video, length in seconds |

**Supported MIME types:**

| Category | Types |
|----------|-------|
| Images | `image/jpeg`, `image/png`, `image/gif`, `image/webp`, `image/svg+xml`, `image/bmp` |
| Documents | `application/pdf`, `.doc`, `.docx`, `.xls`, `.xlsx` |
| Audio | `audio/mpeg` (.mp3), `audio/ogg`, `audio/webm`, `audio/wav`, `audio/aac`, `audio/x-m4a`, `audio/amr` |
| Video | `video/mp4`, `video/webm`, `video/quicktime` (.mov), `video/x-msvideo` (.avi), `video/3gpp`, `video/x-matroska` (.mkv) |
| Other | `text/plain`, `text/csv`, `application/zip` |

**Size limits:**
- Video files: **100 MB**
- All other files: **25 MB**

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id":               101,
        "name":             "product_demo.mp4",
        "mimetype":         "video/mp4",
        "size":             52428800,
        "url":              "/web/content/101?download=true",
        "kind":             "video",
        "duration_seconds": 0
      }
    ],
    "uploaded_count": 1
  }
}
```

**Correct flow:**
```
1. POST /api/crm/supply/chat/upload
   Form: file=<blob>, kind="video", duration_seconds=45
   → { files: [{ id: 101, kind: "video", duration_seconds: 45 }] }

2. POST /api/crm/supply/messages/create
   { thread_id: 8, content: "", kind: "video", duration_seconds: 45,
     attachment_ids: [101] }
```

**Image quality:** Files are stored as-is — no server-side compression or resizing. The browser/app should compress before upload if needed (e.g. resize images to max 2048px before sending). This preserves quality while keeping upload sizes reasonable.

**Video quality:** Same — no transcoding. Use `video/mp4` (H.264) for maximum browser compatibility. If the user records on mobile (`.3gp` or `.mov`), the browser should ideally re-encode to mp4 before upload.

---

### 5.5 Audio & Voice Messages

Voice notes recorded in-app and audio file shares use the same upload endpoint.

#### Recording a voice note (FE flow)

```ts
// 1. Record via MediaRecorder API
const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
const chunks: Blob[] = [];
mediaRecorder.ondataavailable = e => chunks.push(e.data);
mediaRecorder.onstop = async () => {
  const blob = new Blob(chunks, { type: 'audio/webm' });
  const durationSeconds = recordingStopTime - recordingStartTime;

  // 2. Upload
  const form = new FormData();
  form.append('file', blob, 'voice_note.webm');
  form.append('kind', 'voice');
  form.append('duration_seconds', String(durationSeconds));
  form.append('conversation_id', String(conversationId));

  const upload = await fetch('/api/crm/supply/chat/upload', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: form,
  });
  const { data } = await upload.json();
  const file = data.files[0];

  // 3. Send message
  await crmPost('/api/crm/supply/messages/create', {
    thread_id:        conversationId,
    content:          '',
    kind:             'voice',
    duration_seconds: durationSeconds,
    attachment_ids:   [file.id],
  });
};
```

#### Rendering a voice message (FE)

When `msg.kind === 'voice'` or `msg.kind === 'audio'`:

```tsx
function VoiceMessage({ msg }) {
  const att  = msg.attachments[0];
  const secs = msg.duration_seconds;
  return (
    <div className="voice-message">
      <button onClick={() => playAudio(att.url)}>▶</button>
      <span>{formatDuration(secs)}</span>   {/* e.g. "0:32" */}
      <audio src={att.url} controls />
    </div>
  );
}
```

The `att.url` is a direct link to the Odoo attachment (`/web/content/<id>?download=true`). The browser plays it natively with `<audio>`.

#### Recommended audio format

| Use case | Format | Notes |
|----------|--------|-------|
| In-app recording | `audio/webm;codecs=opus` | Best quality at small size, supported in Chrome/Firefox/Edge |
| Fallback | `audio/mp4` (AAC) | Safari compatible |
| File share | any of the allowed types | |

---

### 5.6 Delivery Ticks — Single / Double / Blue

#### The four states

| `delivery_state` | Who sees it | UI | Meaning |
|-----------------|-------------|-----|---------|
| `"sent"` | Sender | ✓ grey | Saved on server |
| `"delivered"` | Sender | ✓✓ grey | At least one recipient's device received it |
| `"read"` | Sender | ✓✓ **blue** | At least one recipient viewed it |
| `"received"` | Recipient | _(no tick)_ | Recipient's own view |

> **Rule:** Only show ticks when `msg.sender_id === currentUserId`.

#### Full lifecycle

```
Sender                                Recipient
──────────────────────────────────    ──────────────────────────────────
Optimistic msg added (delivery_state: "sending")

POST /messages/create
  → server saves message
  → delivery_state: "sent"            Bus: supply.chat.message.new arrives
  → render: ✓ grey                    → recipient sees message

                                      POST /messages/<id>/delivered
                                        (fire & forget, auto-called on
                                         messages/list success)
                                        → server updates delivered_user_ids
                                        → bus publishes message.delivered
                                           to supply_user.<sender_uid>

Bus: supply.chat.message.delivered
  → patch msg: delivery_state="delivered"
  → render: ✓✓ grey

                                      User opens conversation, message
                                      is visible in viewport
                                      POST /messages/<id>/read
                                        (fire & forget)
                                        → server updates read_user_ids
                                        → bus publishes message.read
                                           to supply_user.<sender_uid>

Bus: supply.chat.message.read
  → patch msg: delivery_state="read"
  → render: ✓✓ blue
```

#### Recipient: when to call /delivered and /read

```ts
// On messages/list success — mark all fetched messages as delivered
async function onMessagesLoaded(messages: CrmSupplyMessage[]) {
  for (const msg of messages) {
    if (msg.sender_id !== currentUserId
        && !msg.delivered_to.includes(currentUserId)) {
      crmPost(`/api/crm/supply/messages/${msg.id}/delivered`, {}); // fire & forget
    }
  }
}

// When a message scrolls into the viewport
function onMessageVisible(msg: CrmSupplyMessage) {
  if (msg.sender_id !== currentUserId
      && !msg.read_by.includes(currentUserId)) {
    crmPost(`/api/crm/supply/messages/${msg.id}/read`, {}); // fire & forget
  }
}
```

#### Bus event patch (sender side)

```ts
// In your bus poll handler:
switch (event.type) {
  case 'supply.chat.message.new':
    mergeMessageIntoCache(event.payload);
    break;

  case 'supply.chat.message.delivered':
    // event.payload: { message_id, conversation_id, delivery_state, delivered_to }
    updateMessageInCache(event.payload.message_id, {
      delivery_state: 'delivered',
      delivered_to:   event.payload.delivered_to,
    });
    break;

  case 'supply.chat.message.read':
    // event.payload: { message_id, conversation_id, delivery_state, read_by }
    updateMessageInCache(event.payload.message_id, {
      delivery_state: 'read',
      read_by:        event.payload.read_by,
    });
    break;

  case 'supply.chat.message.updated':
    updateMessageInCache(event.payload.id, event.payload);
    break;

  case 'supply.chat.message.reaction.changed':
    updateMessageInCache(event.payload.message_id, {
      reactions: event.payload.reactions,
    });
    break;
}
```

#### Tick renderer

```tsx
function DeliveryTick({ msg, currentUserId }: { msg: CrmSupplyMessage; currentUserId: number }) {
  if (msg.sender_id !== currentUserId) return null;
  switch (msg.delivery_state) {
    case 'sending':   return <span className="tick sending">⏳</span>;
    case 'sent':      return <span className="tick sent">✓</span>;         // single grey
    case 'delivered': return <span className="tick delivered">✓✓</span>;   // double grey
    case 'read':      return <span className="tick read">✓✓</span>;        // double blue (CSS color)
    default:          return <span className="tick sent">✓</span>;
  }
}
```

CSS:
```css
.tick { font-size: 12px; color: #8c8c8c; }
.tick.read { color: #4fc3f7; }   /* WhatsApp blue */
```

#### Group chats
- `delivered` = at least **one** other participant called `/delivered`
- `read` = at least **one** other participant called `/read`

To show "read by X people" on long-press: use `msg.read_by` (array of user IDs) → cross-reference with conversation `participants`.

---

### 5.7 Typing Indicators

#### `POST /conversations/<id>/typing`

Fire-and-forget — never await.

```json
{ "is_typing": true }   // or false
```

**FE heartbeat contract:**

| Event | Action |
|-------|--------|
| User starts typing | Send `is_typing: true` (debounced ≤ 300ms) |
| Still typing | Repeat `is_typing: true` every **4 seconds** |
| User stops or sends | Send `is_typing: false` immediately |

Server auto-stops after **8 seconds** without a heartbeat — no need to handle network drops.

**Bus events received:**

```ts
case 'supply.chat.typing.start': {
  const { conversation_id, user_id, user_name } = event.payload;
  showTypingIndicator(conversation_id, user_id, user_name);
  break;
}
case 'supply.chat.typing.stop': {
  const { conversation_id, user_id } = event.payload;
  hideTypingIndicator(conversation_id, user_id);
  break;
}
```

---

### 5.8 Real-time: bus_channels + /web/bus/poll

#### Step 1 — Get channels (once per session)

```
POST /api/crm/supply/chat/bus_channels    params: {}
```

Response:
```json
{
  "success": true,
  "data": {
    "channels": ["supply_chat.8", "supply_chat.10", "supply_user.2"],
    "uid": 2
  }
}
```

Also call this after creating a new conversation to pick up the new `supply_chat.<id>` channel.

#### Step 2 — Poll loop

```
POST /web/bus/poll    (NOT under /api/crm/ — direct path)
```

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "channels": ["supply_chat.8", "supply_user.2"],
    "last": 0
  }
}
```

Response (array, may be empty):
```json
[
  {
    "id": 1042,
    "message": {
      "type": "supply.chat.message.new",
      "payload": { /* CrmSupplyMessage */ }
    }
  }
]
```

Always update `last` to the highest `id` received.

#### Bus event reference

| `type` | Channel | Payload |
|--------|---------|---------|
| `supply.chat.message.new` | `supply_chat.<conv_id>` + `supply_user.<recipient_uid>` | Full `CrmSupplyMessage` |
| `supply.chat.message.updated` | `supply_chat.<conv_id>` | Full `CrmSupplyMessage` |
| `supply.chat.message.deleted` | `supply_chat.<conv_id>` | `{ message_id, conversation_id }` |
| `supply.chat.message.delivered` | `supply_user.<sender_uid>` | `{ message_id, conversation_id, delivery_state, delivered_to }` |
| `supply.chat.message.read` | `supply_user.<sender_uid>` | `{ message_id, conversation_id, delivery_state, read_by }` |
| `supply.chat.message.reaction.changed` | `supply_chat.<conv_id>` | `{ message_id, conversation_id, reactions }` |
| `supply.chat.typing.start` | `supply_chat.<conv_id>` | `{ conversation_id, user_id, user_name, is_typing: true }` |
| `supply.chat.typing.stop` | `supply_chat.<conv_id>` | `{ conversation_id, user_id, user_name, is_typing: false }` |

---

### 5.9 Group Members

| Route | Params |
|-------|--------|
| `POST /conversations/<id>/members/list` | `{}` |
| `POST /conversations/<id>/members/add` | `{ "user_ids": [5, 12] }` |
| `POST /conversations/<id>/members/remove` | `{ "user_id": 5 }` |

---

### 5.10 Correct Integration Sequence

```
App mounts
  ├─ 1. GET  /api/crm/notifications             → badge count
  ├─ 2. POST /conversations/list                → sidebar
  ├─ 3. POST /chat/bus_channels                 → get channel names
  └─ 4. Enter bus poll loop (POST /web/bus/poll)

User opens conversation
  ├─ POST /messages/list { thread_id }
  ├─ POST /conversations/<id>/mark_read         (once)
  └─ For each message visible on screen:
       fire-and-forget /messages/<id>/delivered
       fire-and-forget /messages/<id>/read

User sends text message
  ├─ Optimistic: push to cache with delivery_state: "sending"
  ├─ POST /messages/create { content, thread_id, kind: "text" }
  └─ On success: replace optimistic with real msg (delivery_state: "sent")

User sends image/file
  ├─ POST /chat/upload  (multipart)  → { files: [{ id, kind, url }] }
  └─ POST /messages/create { thread_id, kind: "image", attachment_ids: [id] }

User records voice note
  ├─ Record via MediaRecorder → audio/webm blob
  ├─ POST /chat/upload  kind=voice, duration_seconds=32  → { files: [{ id }] }
  └─ POST /messages/create { thread_id, kind: "voice",
                              duration_seconds: 32, attachment_ids: [id] }

Bus: supply.chat.message.delivered  → patch tick to grey ✓✓
Bus: supply.chat.message.read       → patch tick to blue ✓✓
```

---

## 6. Email — Lugal Email API

All email routes are plain **REST** (GET/POST/PATCH/DELETE), not JSON-RPC.  
Base prefix: `/api/lugal/email/`  
Auth: `Authorization: Bearer <lugal_jwt>`

### 6.1 Accounts

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/accounts` | List user's accounts |
| POST | `/accounts` | Create account |
| GET | `/accounts/<id>` | Get one |
| PATCH | `/accounts/<id>` | Update IMAP/SMTP settings |
| DELETE | `/accounts/<id>` | Soft-delete |
| POST | `/accounts/<id>/test` | Test connectivity |
| POST | `/accounts/<id>/set_default` | Set default "From" |

---

### 6.2 Mailbox

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/messages` | List messages |
| GET | `/mailbox/inbox` | Inbox shortcut |
| GET | `/mailbox/<folder>` | Folder shortcut |
| GET | `/messages/<id>` | Full message (auto-marks read, fetches body on demand) |
| DELETE | `/messages/<id>` | Move to trash |
| POST | `/messages/<id>/restore` | Restore from trash |
| POST | `/messages/<id>/archive` | Archive |
| POST | `/messages/<id>/read` | Toggle read: `{ "is_read": true }` |
| POST | `/messages/<id>/star` | Toggle starred |
| POST | `/messages/<id>/link` | Link to CRM record |
| POST | `/messages/<id>/unlink` | Unlink |

**Mailbox query params:**

| Param | Default | Notes |
|-------|---------|-------|
| `account_id` | all user accounts | Filter by account |
| `folder` | `inbox` | `inbox` / `sent` / `drafts` / `trash` / `archive` |
| `limit` | 50 | Max 200 |
| `offset` | 0 | Pagination |
| `search` | — | Substring search on subject/from |
| `is_read` | — | `true` / `false` |
| `is_starred` | — | `true` / `false` |

> **Important:** The inbox endpoint auto-triggers an IMAP background sync and waits up to 7 seconds. You do NOT need to call `sync/all` manually before loading the inbox.

---

### 6.3 Compose — Send / Reply / Forward

All three accept the same body structure. Multiple CC and BCC are fully supported.

#### `POST /send`

```json
{
  "account_id":     30,
  "to":             ["alice@example.com", "bob@example.com"],
  "cc":             ["manager@example.com"],
  "bcc":            ["archive@example.com", "compliance@example.com"],
  "subject":        "Q2 Invoice",
  "body_html":      "<p>Please find attached...</p>",
  "body_text":      "Please find attached...",
  "attachment_ids": [42, 43]
}
```

`to` / `cc` / `bcc` accept:
- `["email@example.com", ...]` — plain string array
- `[{"email": "email@example.com"}, ...]` — object array
- A mix of both

**CC and BCC are now stored in the database** on the sent message record.

**Response (201):**
```json
{
  "success": true,
  "data": {
    "id":             342,
    "smtp_delivered": true,
    "smtp_error":     null,
    "cc_addresses":   "[{\"email\": \"manager@example.com\"}]",
    "bcc_addresses":  "[{\"email\": \"archive@example.com\"}]"
  }
}
```

**Error (422 — recipient not found):**
```json
{ "success": false, "error": "Recipient(s) not found...", "code": "recipient_not_found" }
```

#### `POST /messages/<id>/reply`

```json
{
  "body_html":      "<p>My reply</p>",
  "body_text":      "My reply",
  "cc":             ["cc@example.com"],
  "bcc":            ["bcc@example.com"],
  "attachment_ids": [44]
}
```

#### `POST /messages/<id>/forward`

```json
{
  "to":             ["bob@example.com"],
  "cc":             [],
  "bcc":            [],
  "body_html":      "<p>FYI</p>",
  "attachment_ids": [45]
}
```

---

### 6.4 Email Attachments Upload

#### `POST /api/lugal/email/attachments/upload` — multipart/form-data

Upload before composing. Returns `ir.attachment` IDs to pass in `attachment_ids`.

**Form fields:** `file` / `files` / `files[]`  
**Limit:** 25 MB per file

**Response:**
```json
{
  "success": true,
  "data": {
    "attachments": [
      {
        "id":       42,
        "name":     "invoice.pdf",
        "mimetype": "application/pdf",
        "size":     102400,
        "url":      "/web/content/42?download=true"
      }
    ]
  }
}
```

**Flow:**
```
1. POST /api/lugal/email/attachments/upload  →  { id: 42 }
2. POST /api/lugal/email/send
   { "to": [...], "subject": "...", "body_html": "...", "attachment_ids": [42] }
```

---

### 6.5 Email Notifications & Polling

#### `GET /api/lugal/email/notifications?since=<ISO>`

For email-specific polling (use `GET /api/crm/notifications` for combined chat+email).

```json
{
  "success": true,
  "data": {
    "inbox":       12,
    "total":       12,
    "per_folder":  { "inbox": 12, "sent": 0 },
    "checked_at":  "2026-04-20T10:15:30",
    "new_messages": [{ "id": 55, "subject": "...", "from_name": "..." }],
    "recently_sent": [{ "id": 342, "smtp_delivered": true, "smtp_error": null }]
  }
}
```

**`smtp_delivered` on sent messages:**
- `true` = SMTP server accepted the message (→ show ✓ in sent folder)
- `false` with `smtp_error` = delivery failed (→ show error icon)
- **Not** a read receipt — email has no real-time read confirmation

**Sync triggers:**

| Route | Effect |
|-------|--------|
| `POST /sync/all` | Background IMAP sync for all accounts |
| `POST /accounts/<id>/sync` | Sync one account |
| `GET /mailbox/inbox` | Auto-syncs, waits up to 7 s |

---

## 7. CRM Email Helpers (JSON-RPC)

These are under `/api/crm/email/...` and use JSON-RPC envelope.

| Path | Purpose |
|------|---------|
| `POST /api/crm/email/templates/list` | Get email templates |
| `POST /api/crm/email/templates/<id>/apply` | Apply with variables |
| `POST /api/crm/email/bulk/read` | Bulk mark read: `{ "message_ids": [1,2,3], "is_read": true }` |
| `POST /api/crm/email/bulk/delete` | Bulk delete: `{ "message_ids": [1,2,3] }` |

> Correct bulk-read path is `/api/crm/email/bulk/read` — NOT `/api/crm/email/messages/bulk_read`.

---

## 8. Complete TypeScript Shapes

### `CrmSupplyConversation`

```ts
interface CrmSupplyConversation {
  id:              number;
  type:            'team' | 'dm' | 'group';
  name:            string;
  participant_ids: number[];
  participants:    { id: number; name: string; avatar: string | null }[];
  last_activity:   string | null;   // ISO-8601 UTC
  is_archived:     boolean;
  unread_count:    number;
}
```

### `CrmSupplyMessage`

```ts
type MessageKind = 'text' | 'image' | 'video' | 'audio' | 'voice' | 'file';
type DeliveryState = 'sending' | 'sent' | 'delivered' | 'read' | 'received';

interface ChatAttachment {
  id?:              number;
  name:             string;
  url:              string;
  mimetype?:        string;
  size?:            number;
  kind?:            MessageKind;
  duration_seconds?: number;
}

interface CrmSupplyMessage {
  id:               number;
  thread_id:        number;
  conversation_type:'team' | 'dm' | 'group';
  sender_id:        number | null;
  sender_name:      string;
  sender_avatar:    string | null;
  participant_ids:  number[];
  content:          string;
  kind:             MessageKind;
  duration_seconds: number;
  attachments:      ChatAttachment[];
  created_at:       string | null;
  edited_at:        string | null;
  reply_to_id:      number | null;
  reply_to_content: string | null;
  reply_to_sender:  string | null;
  reactions:        Record<string, number[]>;  // emoji → [user_id, ...]
  is_deleted:       boolean;
  delivery_state:   DeliveryState;
  delivered_to:     number[];
  read_by:          number[];
}
```

### `LugalEmailMessage`

```ts
interface LugalEmailMessage {
  id:             number;
  account_id:     number;
  folder:         'inbox' | 'sent' | 'drafts' | 'trash' | 'archive';
  subject:        string;
  from_name:      string;
  from_address:   string;
  to_addresses:   string;   // JSON: [{"email": "..."}]
  cc_addresses:   string;   // JSON: [{"email": "..."}]
  bcc_addresses:  string;   // JSON: [{"email": "..."}] — now persisted
  date:           string;
  is_read:        boolean;
  is_starred:     boolean;
  is_draft:       boolean;
  body_html:      string | null;
  body_text:      string | null;
  body_fetched:   boolean;   // false = only headers; body arrives on GET /messages/<id>
  smtp_delivered: boolean;
  smtp_error:     string | null;
  attachments:    any[];     // populated on GET /messages/<id>
}
```

### `CrmNotifications`

```ts
interface CrmNotifications {
  total_unread: number;
  chat: {
    unread:        number;
    conversations: {
      id:            number;
      name:          string;
      type:          'team' | 'dm' | 'group';
      unread_count:  number;
      last_message:  string;
      last_activity: string | null;
    }[];
  };
  email: {
    unread: number;
    items:  {
      id:           number;
      account_id:   number;
      subject:      string;
      from_name:    string;
      from_address: string;
      date:         string | null;
    }[];
  };
  checked_at: string;
}
```

---

## 9. Backend Restart Required

The following changes require the Odoo module to be updated (`-u lugal_crm`) to add the new DB columns:

1. `lugal.supply.message` model — new columns: `kind` (varchar), `duration_seconds` (float8)

Until the module is restarted/updated, the `kind` and `duration_seconds` fields will return as `null` from existing messages, and `messages/create` will ignore those params. All other changes (controller routes, MIME types, notifications endpoint) are **live immediately** without a restart.

**How to apply:**
```bash
# Stop Odoo, update module, restart
pkill -9 -f odoo-bin
python3 odoo-bin -u lugal_crm -d <db_name> --stop-after-init
python3 odoo-bin --config=...  # normal start
```

---

*This document covers backend state as of 2026-04-20. Update in lockstep with `supply_chat_controller.py`, `supply_controller.py`, `email_controller.py`, and `crm_notifications_controller.py`.*
