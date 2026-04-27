# Supply Chat — Frontend Integration Guide

> **Stack:** Odoo 19 backend · JSON-RPC 2.0 · JWT Bearer auth · TanStack Query v5 polling  
> **Base prefix for every call below:** `POST /api/crm/supply/*`  
> All requests go through `crmPost()` which wraps the JSON-RPC 2.0 envelope and attaches the Bearer token automatically.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Authentication](#2-authentication)
3. [Data Models (Response Shapes)](#3-data-models-response-shapes)
4. [API Reference](#4-api-reference)
   - 4.1 [Conversations](#41-conversations)
   - 4.2 [Messages](#42-messages)
   - 4.3 [Message Receipts](#43-message-receipts)
   - 4.4 [Realtime Hooks](#44-realtime-hooks)
5. [Complete Message Flow](#5-complete-message-flow)
6. [Polling Strategy — No Infinite Loops](#6-polling-strategy--no-infinite-loops)
7. [Query Keys Reference](#7-query-keys-reference)
8. [Frontend Setup Checklist](#8-frontend-setup-checklist)

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        NBS-CRM Frontend                         │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │ Conversation │   │   Message    │   │  Typing / Bus    │   │
│  │   Sidebar    │   │    Panel     │   │   Indicator      │   │
│  └──────┬───────┘   └──────┬───────┘   └────────┬─────────┘   │
│         │                  │                    │             │
│         ▼                  ▼                    ▼             │
│  useQuery(stale:15s)  useQuery(stale:3s)   fire-and-forget   │
│  conversations/list   messages/list        typing / bus_poll │
└─────────────────────────────────────────────────────────────────┘
                            │
                    crmPost() / Axios
                    Authorization: Bearer <JWT>
                            │
                     Odoo 19 Backend
              POST /api/crm/supply/*  (JSON-RPC)
```

**There is no WebSocket server** in this project. Real-time feel comes from:
- Short **TanStack Query polling intervals** (`refetchInterval`)
- **Optimistic UI updates** on send (add message to cache before server confirms)
- Fire-and-forget typing events (no response waited for)

---

## 2. Authentication

Every request uses the JWT token stored in `useAuthStore`:

```ts
// Handled automatically by crmApiClient interceptor
// Authorization: Bearer <tokenForCrm ?? posAccessToken ?? sessionId>
```

The backend validates the token on every supply endpoint. A `401 Unauthorized` response means the token is expired — redirect to login.

---

## 3. Data Models (Response Shapes)

### `CrmSupplyConversation`

```ts
interface CrmSupplyConversation {
  id:              number;
  type:            'team' | 'dm' | 'group';
  name:            string;
  participant_ids: number[];
  participants:    { id: number; name: string; avatar: string }[];
  last_activity:   string | null;   // ISO-8601 UTC
  is_archived:     boolean;
  unread_count:    number;          // messages not sent by me, not yet read
}
```

### `CrmSupplyMessage`

```ts
interface CrmSupplyMessage {
  id:               number;
  thread_id:        number;         // conversation id
  conversation_type:'team' | 'dm' | 'group';
  sender_id:        number | null;
  sender_name:      string;
  sender_avatar:    string | null;  // e.g. /web/image/res.users/5/avatar_128
  participant_ids:  number[];
  content:          string;
  attachments:      { name: string; url: string }[];
  created_at:       string | null;  // ISO-8601 UTC
  edited_at:        string | null;  // null if never edited
  reply_to_id:      number | null;
  reply_to_content: string | null;  // first 200 chars of quoted message
  reply_to_sender:  string | null;
  reactions:        Record<string, number[]>; // emoji → [user_id, ...]
}
```

---

## 4. API Reference

> **Envelope reminder:** every response is wrapped in a JSON-RPC 2.0 envelope.  
> `crmApiClient` unwraps it automatically — the shapes below show the **unwrapped** value.

---

### 4.1 Conversations

#### `POST /api/crm/supply/conversations/list`

Returns all non-archived conversations the authenticated user is a participant in, newest activity first.

**Request params:** _(none)_

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [ <CrmSupplyConversation>, ... ],
    "total": 3
  }
}
```

**When to call:** On app mount and as a background poll (see §6).

---

#### `POST /api/crm/supply/conversations/<id>/get`

Fetch a single conversation (e.g. to refresh after a mutation).

**Request params:** _(none)_

**Response:**
```json
{ "success": true, "data": <CrmSupplyConversation> }
```

---

#### `POST /api/crm/supply/conversations/<id>/rename`

Rename a **group** conversation. Fails for `dm` and `team` types.

**Request params:**
```json
{ "name": "Supply Core Team" }
```

**Response:**
```json
{ "success": true, "data": <CrmSupplyConversation> }
```

---

#### `POST /api/crm/supply/conversations/<id>/archive`

Archive a `dm` or `group` conversation. Fails for `team` channels.

**Request params:** _(none)_

**Response:**
```json
{ "success": true }
```

---

#### `POST /api/crm/supply/conversations/<id>/mark_read`

Mark every unread message in a conversation as read for the calling user.  
Call this once when the user opens (switches to) a conversation.

**Request params:** _(none — empty `{}`)_

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": 8,
    "unread_count": 0
  }
}
```

**Behaviour:**
- Finds all messages in the conversation where `sender_id != caller` AND `caller NOT IN read_user_ids`
- Bulk-adds the caller to each message's `read_user_ids` in a single write
- Subsequent `conversations/list` calls return `unread_count: 0` for that conversation
- Idempotent — safe to call multiple times; second call is a no-op

**When to call:**  
Once per conversation switch (on sidebar item click). Do **not** call on every scroll or render.

---

### 4.2 Messages

#### `POST /api/crm/supply/messages/list`

Paginated list of messages for a conversation. Messages are returned oldest-first.

**Request params:**
```json
{
  "thread_id":    8,       // required OR use recipient_ids
  "page":         1,       // default 1
  "per_page":     50       // default 50
}
```

— **OR** open a DM/group by recipients instead of a known thread:
```json
{
  "recipient_ids": [5, 12],   // will auto-find or create the thread
  "page": 1,
  "per_page": 50
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items":             [ <CrmSupplyMessage>, ... ],
    "total":             42,
    "thread_id":         8,
    "conversation_type": "group"
  }
}
```

---

#### `POST /api/crm/supply/messages/create`

Send a new message. If `thread_id` is given the message is posted there.  
If `recipient_ids` is given instead, the backend finds or creates the correct thread automatically.

**Request params:**
```json
{
  "content":       "Hello team!",
  "thread_id":     8,           // use this if conversation already exists
  // -- OR --
  "recipient_ids": [5, 12],     // auto-creates DM (1 recipient) or group (2+)
  "group_name":    "PO Review", // only when creating a new group via recipient_ids

  // optional
  "attachments": [{ "name": "invoice.pdf", "url": "https://..." }],
  "reply_to_id": 47             // quote another message
}
```

**Response:**
```json
{ "success": true, "data": <CrmSupplyMessage> }
```

> **Note:** The returned `thread_id` may differ from the one you sent if the backend  
> resolved a different DM thread. Always use `data.thread_id` as the canonical reference  
> for subsequent calls.

---

#### `POST /api/crm/supply/messages/<id>/edit`

Edit the **content** of a message. Only the original sender can edit.

**Request params:**
```json
{ "content": "Updated message text" }
```

**Response:**
```json
{ "success": true, "data": <CrmSupplyMessage> }
```

---

#### `POST /api/crm/supply/messages/<id>/react`

Toggle an emoji reaction. Calling the same emoji again removes it.

**Request params:**
```json
{ "emoji": "👍" }
```

**Response:**
```json
{
  "success": true,
  "data": {
    "reactions": { "👍": [2, 5], "❤️": [9] }
  }
}
```

---

#### `POST /api/crm/supply/messages/<id>/delete`

Soft-delete a message (only the sender can). Content is replaced with a placeholder — the message record remains so reply-to threads are not broken.

**Request params:**
```json
{ "for_everyone": true }   // or omit / false
```

**Response:**
```json
{ "success": true }
```

---

### 4.3 Message Receipts

> These three endpoints record the message lifecycle status.  
> Call them **fire-and-forget** — do **not** block UI or await them for optimistic rendering.

#### `POST /api/crm/supply/messages/<id>/delivered`

Call as soon as a message arrives in the client (e.g. in the `onSuccess` of `messages/list` or `messages/create`). Records that this user's device received the payload.

**Request params:** _(none)_

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id":      47,
    "conversation_id": 8,
    "delivered_to":    [2, 5],
    "delivered_count": 2
  }
}
```

---

#### `POST /api/crm/supply/messages/<id>/read`

Call when the user **views** the message (conversation panel is open and message is visible in viewport). Returns the updated unread count for badge display.

**Request params:** _(none)_

**Response:**
```json
{
  "success": true,
  "data": {
    "message_id":      47,
    "conversation_id": 8,
    "unread_count":    0
  }
}
```

---

### 4.4 Realtime Hooks

#### `POST /api/crm/supply/chat/bus_channels`

Call **once per session** (on login or when the chat panel mounts) to get the list of Odoo bus channels this user should subscribe to. Use the returned channel names in `/web/bus/poll`.

**Request params:** _(none)_

**Response:**
```json
{
  "success": true,
  "data": {
    "channels": ["supply_chat.8", "supply_chat.10", "supply_user.2"],
    "uid": 2
  }
}
```

---

#### `POST /web/bus/poll`

Long-polling compatibility endpoint (Odoo 19 shim). Call to check for new bus notifications without a WebSocket. Returns an array of pending notifications since `last`.

**Request params:**
```json
{
  "channels": ["supply_chat.8", "supply_user.2"],
  "last": 0
}
```

**Response:** Array of notification objects (or empty array if no new events):
```json
[
  { "id": 103, "message": { "type": "supply_chat_message", "payload": { ... } } }
]
```

> Update `last` to the highest `id` you received on each successful poll.

---

#### `POST /api/crm/supply/conversations/<id>/typing`

Signal that the current user is (or stopped) typing. Fire-and-forget — never await.

**Request params:**
```json
{ "is_typing": true }    // or false when user stops / sends
```

**Response:**
```json
{
  "success": true,
  "data": {
    "conversation_id": 8,
    "user_id": 2,
    "user_name": "Admin",
    "is_typing": true
  }
}
```

**Bus publish (automatic — no extra call needed):**  
On every successful typing request the backend immediately publishes a bus notification
to **all other participants** in the conversation. Your `/web/bus/poll` loop receives it
on the next cycle.

| `is_typing` | `message.type` published |
|---|---|
| `true` | `supply.chat.typing.start` |
| `false` | `supply.chat.typing.stop` |

**Server-side auto-stop timer:**  
When `is_typing: true` is received the server arms an **8-second timer** per `(user, conversation)`.  
If no new `is_typing: true` heartbeat arrives within 8 seconds, the server automatically
broadcasts `supply.chat.typing.stop` — even if the FE never calls `is_typing: false`.  
A new heartbeat arriving within the 8 s window resets the timer.  
The state is stored in the `lugal.supply.typing` DB table so the cross-process guard works
across all Odoo worker processes.

**FE heartbeat contract:**

| FE event | What to send |
|---|---|
| User starts typing | `is_typing: true` (debounced ≤ 300 ms) |
| User is still typing | `is_typing: true` again every **4 s** (heartbeat) |
| User stops / sends | `is_typing: false` immediately |

The 4-second heartbeat + 8-second server timer gives a 4-second grace window before
the server auto-stops.

**Bus notification shape** (received inside `/web/bus/poll` result):
```json
{
  "id": 1421666,
  "message": {
    "type": "supply.chat.typing.start",
    "payload": {
      "conversation_id": 8,
      "user_id":         2,
      "user_name":       "Admin",
      "is_typing":       true
    }
  }
}
```

Published on:
- `supply_chat.<conversation_id>` **only** — single channel, no per-user duplicates.

> **Deduplication note (breaking change):** the backend no longer publishes on
> `supply_user.<uid>` for typing events. If your FE subscribed to `supply_user.<uid>`
> expecting typing notifications, remove that expectation — typing events arrive exclusively
> on `supply_chat.<conv_id>`. All other event types still go through `supply_user.<uid>`
> when applicable.

> The sender is **excluded** from the publish — the typist does not receive their own echo.

---

## 5. Complete Message Flow

```
SENDER                                      RECEIVER
──────────────────────────────────────────────────────────────────
1. User types  →  startTyping()
                  → POST .../typing { is_typing: true }  (immediate)
                  → setInterval heartbeat every 4 s (reset server 8s timer)
   (fire-and-forget, no await)

2. User pauses 4 s → stopTyping() auto-fires
   OR User sends → stopTyping() + POST .../messages/create
   ├─ optimistic: add to local cache immediately
   ├─ on success: use returned thread_id as canonical
   ├─ invalidate ['crm','supply','messages'] query
   ├─ invalidate ['crm','supply','conversations'] query
   └─ POST .../typing { is_typing: false }  (fire-and-forget)

                                    3. Receiver's refetchInterval fires
                                       POST .../messages/list { thread_id }
                                       → new message appears in list

                                    4. On message render (visible in DOM):
                                       POST .../messages/<id>/delivered (fire-and-forget)
                                       POST .../messages/<id>/read (fire-and-forget)
                                       → badge count updates via returned unread_count

5. Sender sees double-tick via:
   next messages/list poll includes
   delivered_to[] / read_user_ids[] in future
   (if FE renders it from the receipt counts)
──────────────────────────────────────────────────────────────────
```

---

## 6. Polling Strategy — No Infinite Loops

This is the most important section. Follow these rules exactly to prevent runaway polling.

### Rule 1 — Use `staleTime` + `refetchInterval`, not `refetchOnWindowFocus` alone

```ts
// ✅ CORRECT
useQuery({
  queryKey: queryKeys.crmSupply.conversationsList(),
  queryFn:  ({ signal }) => listCrmSupplyConversations(signal),
  staleTime:       15_000,   // 15 s — don't re-fetch if data is fresh
  refetchInterval: 15_000,   // background poll every 15 s
  refetchIntervalInBackground: false, // STOP polling when tab is hidden
});

// ✅ CORRECT — messages poll faster (active conversation)
useQuery({
  queryKey: queryKeys.crmSupply.messagesList({ thread_id }),
  queryFn:  ({ signal }) => listCrmSupplyMessages({ thread_id }, signal),
  staleTime:       3_000,    // 3 s
  refetchInterval: 3_000,
  refetchIntervalInBackground: false,
  enabled:  !!thread_id,     // NEVER poll when no conversation is open
});
```

### Rule 2 — Always gate `enabled` on required state

```ts
// ✅ NO thread → NO poll
enabled: queriesOn && threadId != null

// ✅ NO token → NO poll
enabled: !!authToken && !!threadId
```

### Rule 3 — Fire-and-forget endpoints must NOT be in useQuery

`typing`, `delivered`, `read`, `bus_channels` — these are **mutations or effects**, never queries.

```ts
// ❌ WRONG — this will poll endlessly
useQuery({ queryKey: ['typing'], queryFn: () => sendTyping(id) })

// ✅ CORRECT — use useMutation or a plain async call
const sendTypingIndicator = useCallback(
  debounce((convId: number, isTyping: boolean) => {
    crmPost(`/supply/conversations/${convId}/typing`, { is_typing: isTyping })
      .catch(() => {});   // intentionally swallow — don't crash UI
  }, 300),
  []
);
```

### Rule 4 — Typing indicator heartbeat pattern

The server arms an **8-second auto-stop timer** on every `is_typing: true`. The FE must
send a heartbeat every **4 seconds** while the user is still typing, so the timer is always
reset before it expires.

```ts
const typingTimerRef   = useRef<ReturnType<typeof setTimeout> | null>(null);
const heartbeatRef     = useRef<ReturnType<typeof setInterval> | null>(null);
const isTypingActiveRef = useRef(false);

function startTyping(convId: number) {
  if (isTypingActiveRef.current) return;   // already in typing state
  isTypingActiveRef.current = true;

  // First fire immediately
  crmPost(`/supply/conversations/${convId}/typing`, { is_typing: true }).catch(() => {});

  // Then heartbeat every 4 s while still typing
  heartbeatRef.current = setInterval(() => {
    crmPost(`/supply/conversations/${convId}/typing`, { is_typing: true }).catch(() => {});
  }, 4_000);
}

function stopTyping(convId: number) {
  if (!isTypingActiveRef.current) return;
  isTypingActiveRef.current = false;

  if (heartbeatRef.current) { clearInterval(heartbeatRef.current); heartbeatRef.current = null; }
  if (typingTimerRef.current) { clearTimeout(typingTimerRef.current); typingTimerRef.current = null; }

  crmPost(`/supply/conversations/${convId}/typing`, { is_typing: false }).catch(() => {});
}

function onDraftChange(value: string, convId: number) {
  setDraft(value);

  startTyping(convId);

  // Reset the inactivity timeout — if user pauses for 4 s, send stop
  if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
  typingTimerRef.current = setTimeout(() => stopTyping(convId), 4_000);
}

// On send — cancel immediately
function onSend(convId: number) {
  stopTyping(convId);
  // ... send logic
}
```

### Rule 5 — Receipt endpoints use intersection observer, not scroll events

```ts
// ✅ Mark as delivered + read only once per message per session
const deliveredSet = useRef(new Set<number>());

function onMessageVisible(messageId: number) {
  if (deliveredSet.current.has(messageId)) return;   // already sent — SKIP
  deliveredSet.current.add(messageId);
  // fire-and-forget both receipts
  crmPost(`/supply/messages/${messageId}/delivered`, {}).catch(() => {});
  crmPost(`/supply/messages/${messageId}/read`,      {}).catch(() => {});
}
```

### Rule 6 — `bus/poll` must use sequential polling, not concurrent

```ts
// ✅ CORRECT sequential bus polling
const lastBusIdRef = useRef(0);
const busPollingRef = useRef<ReturnType<typeof setTimeout> | null>(null);

async function pollBus(channels: string[]) {
  try {
    const notifications = await rawPost('/web/bus/poll', {
      channels,
      last: lastBusIdRef.current,
    });
    if (notifications.length > 0) {
      lastBusIdRef.current = Math.max(...notifications.map((n: any) => n.id));
      // Invalidate queries to pick up new messages
      queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'messages'] });
      queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'conversations'] });
    }
  } catch {
    // swallow errors — next tick will retry
  } finally {
    // Schedule NEXT poll only after THIS one completes
    busPollingRef.current = setTimeout(() => pollBus(channels), 5_000);
  }
}

// On mount:
useEffect(() => {
  let channels: string[] = [];
  crmPost('/supply/chat/bus_channels', {})
    .then((data: any) => { channels = data.channels ?? []; })
    .then(() => pollBus(channels));

  return () => {
    if (busPollingRef.current) clearTimeout(busPollingRef.current);
  };
}, []);  // ← empty deps — run once per session
```

> **Never use `setInterval` for bus polling.** If the previous request is slow, `setInterval`
> fires concurrent requests causing a flood. Use `setTimeout` inside the `finally` block instead.

---

## 6b. Typing Indicator — Remote Display

### How it works end-to-end

```
User A types                       User B's bus poll loop
──────────────────────────────────────────────────────────
onDraftChange()
  → startTyping()
  → POST .../typing { is_typing: true }
  ← success: true
  [backend: arms 8s auto-stop timer, publishes typing.start on supply_chat.8]
  [4s heartbeat: repeat POST .../typing { is_typing: true } to reset timer]

                          setTimeout loop fires
                          → POST /web/bus/poll { channels, last: N }
                          ← [{ id: 1421666, message: {
                                type: "supply.chat.typing.start",
                                payload: {
                                  conversation_id: 8,
                                  user_id: 2,
                                  user_name: "Admin",
                                  is_typing: true
                                }
                              }}]
                          → set typingUsers[8] = ["Admin"]
                          → render "Admin is typing..."

User pauses 4 s / sends
  → stopTyping()
  → POST .../typing { is_typing: false }  (or no action — server 8s timer fires)
  [backend: cancels timer, publishes typing.stop on supply_chat.8]

                          next poll cycle receives:
                          type: "supply.chat.typing.stop"
                          → remove "Admin" from typingUsers[8]
                          → hide indicator
```

### Recommended FE state shape

```ts
// State: Map<conversationId, Map<userId, { name: string; timer: ReturnType<typeof setTimeout> }>>
const typingUsersRef = useRef<Map<number, Map<number, { name: string; timer: any }>>>(new Map());
```

### Handling bus notifications in the poll loop

```ts
// Inside your pollBus() handler, route by type:
for (const notification of notifications) {
  lastBusIdRef.current = Math.max(lastBusIdRef.current, notification.id);
  const { type, payload } = notification.message;

  if (type === 'supply.chat.typing.start') {
    const { conversation_id, user_id, user_name } = payload;
    const convMap = typingUsersRef.current.get(conversation_id) ?? new Map();

    // Clear any existing auto-expire timer for this user
    const existing = convMap.get(user_id);
    if (existing?.timer) clearTimeout(existing.timer);

    // Auto-remove after 5 s in case typing.stop is lost
    // (server will broadcast stop after 8 s but bus poll may lag)
    const timer = setTimeout(() => {
      convMap.delete(user_id);
      typingUsersRef.current.set(conversation_id, convMap);
      forceUpdate(); // trigger re-render
    }, 5_000);

    convMap.set(user_id, { name: user_name, timer });
    typingUsersRef.current.set(conversation_id, convMap);
    forceUpdate();

    // Do NOT invalidate message queries — typing is not a new message
    continue;
  }

  if (type === 'supply.chat.typing.stop') {
    const { conversation_id, user_id } = payload;
    const convMap = typingUsersRef.current.get(conversation_id);
    if (convMap) {
      const existing = convMap.get(user_id);
      if (existing?.timer) clearTimeout(existing.timer);
      convMap.delete(user_id);
      typingUsersRef.current.set(conversation_id, convMap);
      forceUpdate();
    }
    continue;
  }

  // Other event types → invalidate message queries
  queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'messages'] });
  queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'conversations'] });
}
```

### Critical: do NOT re-fetch messages on typing events

The `supply.chat.typing.start/stop` events carry only presence data — they do **not** indicate a new message. Invalidating message queries on these events causes a refetch storm (every keystroke triggers a messages/list call for all participants). Only invalidate queries for unknown event types.

### Confirmed type name strings (exact literals)

| Direction | `message.type` string | Trigger |
|---|---|---|
| Start | `supply.chat.typing.start` | `is_typing: true` |
| Stop | `supply.chat.typing.stop` | `is_typing: false` |

These are the exact strings published by the backend. The FE `if (type === '...')` checks must use these verbatim.

---

## 7. Query Keys Reference

Use these exact keys so invalidation works across all hooks:

| Data | Query Key | Invalidate On |
|---|---|---|
| Conversations list | `['crm','supply','conversations']` | send message, archive, rename, mark_read |
| Messages list | `['crm','supply','messages', params]` | send, edit, delete, react |
| Supply users | `['crm','supply','users']` | rarely |

```ts
// Invalidation after send:
await queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'messages'] });
await queryClient.invalidateQueries({ queryKey: ['crm', 'supply', 'conversations'] });
```

---

## 8. Frontend Setup Checklist

Use this checklist when wiring up the supply chat feature:

### Conversation Sidebar

- [ ] `useQuery` on `conversations/list` with `staleTime: 15_000`, `refetchInterval: 15_000`, `refetchIntervalInBackground: false`
- [ ] Display `unread_count` badge from conversation object
- [ ] On select: set active `threadId` in local state
- [ ] On select: call `mark_read` immediately (fire-and-forget) so the badge clears at once

### Message Panel

- [ ] `useQuery` on `messages/list` with `enabled: !!threadId`, `staleTime: 3_000`, `refetchInterval: 3_000`, `refetchIntervalInBackground: false`
- [ ] On each message render: call `delivered` + `read` via IntersectionObserver (once per message per session)
- [ ] Scroll to bottom on new messages (only if already at bottom — do not force-scroll mid-read)

### Message Composer

- [ ] `useMutation` wrapping `messages/create`
- [ ] **Optimistic update:** `onMutate` — add message to cache with `status: 'sending'`; `onSuccess` — replace with server response; `onError` — remove from cache
- [ ] On input change: call `startTyping(convId)` — sends immediate `is_typing: true` + arms 4s inactivity timer + 4s heartbeat interval
- [ ] On pause (4 s inactivity) or send: call `stopTyping(convId)` — cancels heartbeat + sends `is_typing: false`

### Realtime

- [ ] Call `chat/bus_channels` once on login / chat panel mount — store channel list
- [ ] Start sequential `bus/poll` loop (timeout-based, NOT interval-based)
- [ ] In the poll handler, route by `message.type`:
  - `supply.chat.typing.start` → add user to `typingUsers[conv_id]`, set 5 s auto-expire timer
  - `supply.chat.typing.stop`  → remove user from `typingUsers[conv_id]`, clear timer
  - anything else              → invalidate `messages` + `conversations` query keys
- [ ] **Do NOT invalidate message queries for typing events** — causes refetch storms
- [ ] Stop polling on unmount / logout (clear timeout in cleanup)

### Receipts (Fire-and-Forget)

- [ ] `delivered`: call when message DOM node becomes visible
- [ ] `read`: call when message is visible AND conversation panel is focused
- [ ] Both: guarded by `Set` to ensure at most **one call per message per session**
- [ ] Both: errors swallowed — never show error toast for receipt failures

### Anti-Patterns to Avoid

| ❌ Don't | ✅ Do Instead |
|---|---|
| `useQuery` for typing/delivered/read | `useMutation` or plain `crmPost()` |
| `setInterval` for bus poll | `setTimeout` inside `finally` |
| Poll when no conversation open | Gate with `enabled: !!threadId` |
| `refetchOnWindowFocus: true` for messages | Keep default `false` for chat |
| Await typing before showing UI | Fire-and-forget, swallow errors |
| Call `delivered`/`read` on every render | Use a `Set` + IntersectionObserver |
| Multiple concurrent `bus/poll` requests | Sequential with `setTimeout` in `finally` |
