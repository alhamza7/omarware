# CRM Communication System — Full API Reference

> **Protocol:** JSON-RPC 2.0 over HTTP POST  
> **Auth:** JWT Bearer token — `Authorization: Bearer <token>`  
> **Base URL:** `http(s)://<server>`  
> **All endpoints:** `POST`, `Content-Type: application/json`

---

## How Every Request Works

```json
POST /api/crm/calls/list
Authorization: Bearer eyJhbGc...

{
  "jsonrpc": "2.0",
  "method":  "call",
  "id":      1,
  "params":  { ...endpoint params here... }
}
```

**Success response:**
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

**Error response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Human-readable error message"
  }
}
```

**`*` = required parameter**

---

## Index

| # | System | Endpoints |
|---|--------|-----------|
| 1 | [Calls](#1-calls) | 7 endpoints |
| 2 | [Call Queue](#2-call-queue) | 3 endpoints |
| 3 | [Active Call Context](#3-active-call-context) | 1 endpoint |
| 4 | [Channel Config](#4-channel-config) | 4 endpoints |
| 5 | [Chat Messages (individual)](#5-chat-messages-individual) | 7 endpoints |
| 6 | [Chat Sessions (conversations)](#6-chat-sessions-conversations) | 5 endpoints |
| 7 | [Agent Status](#7-agent-status) | 2 endpoints |
| 8 | [Email — Customer Inbox](#8-email--customer-inbox) | 2 endpoints |
| 9 | [Email — Message Operations](#9-email--message-operations) | 7 endpoints |
| 10 | [Email — Send](#10-email--send) | 1 endpoint |
| 11 | [Supply Internal Messaging](#11-supply-internal-messaging) | 3 endpoints |
| 12 | [Projects](#12-projects) | 7 endpoints |
| 13 | [Kanban Stages](#13-kanban-stages) | 4 endpoints |
| 14 | [Project Tasks](#14-project-tasks) | 8 endpoints |
| 15 | [Milestones](#15-milestones) | 5 endpoints |
| 16 | [Checklists](#16-checklists) | 6 endpoints |
| 17 | [Project Members](#17-project-members) | 3 endpoints |
| 18 | [Project Tags](#18-project-tags) | 2 endpoints |
| 19 | [Project & Task Attachments](#19-project--task-attachments) | 5 endpoints |

**Total: 79 endpoints**

---

## 1. Calls

### 1.1 List Calls

```
POST /api/crm/calls/list
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 50 | Results per page |
| `customer_id` | int | — | Filter by customer |
| `branch_id` | int | — | Filter by branch |
| `agent_id` | int | — | Filter by agent |
| `date_from` | str | — | ISO datetime, e.g. `"2026-01-01T00:00:00"` |
| `date_to` | str | — | ISO datetime |
| `outcome` | str | — | `resolved` / `callback` / `escalated` / `no_answer` |

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "page": 1,
    "per_page": 20,
    "customer_id": 42,
    "outcome": "resolved"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 85,
      "page": 1,
      "per_page": 20,
      "items": [
        {
          "id": 101,
          "customer_id": 42,
          "customer_name": "Ahmed Al-Rashid",
          "agent_id": 7,
          "agent_name": "Sara Hassan",
          "branch_id": 2,
          "call_type": "inbound",
          "channel": "phone",
          "caller_number": "+9647801234567",
          "duration_seconds": 342,
          "started_at": "2026-03-31T09:15:00",
          "ended_at": "2026-03-31T09:20:42",
          "outcome": "resolved",
          "notes": "Customer asked about delivery status",
          "ai_summary": "",
          "qa_score": 4.5,
          "issues_found": "",
          "balance_at_call": 1500.00,
          "outstanding_at_call": 200.00,
          "credit_limit_at_call": 5000.00,
          "catalogue_sent": false,
          "catalogue_sent_via": "",
          "recording_url": "https://storage.example.com/calls/101.mp3",
          "pos_order_id": 0,
          "pos_order_name": "",
          "pos_order_total": 0.0,
          "pos_order_state": "",
          "created_at": "2026-03-31T09:15:00"
        }
      ]
    }
  }
}
```

---

### 1.2 Get Call

```
POST /api/crm/calls/<call_id>
```

**Parameters:** _(none — call_id in URL)_

**Response:** `{ "success": true, "data": { ...call_dict... } }`

---

### 1.3 Create Call (Start)

```
POST /api/crm/calls/create
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | int | ✓ | CRM customer ID |
| `call_type` | str | — | `inbound` (default) / `outbound` |
| `channel` | str | — | e.g. `"phone"`, `"whatsapp"` |
| `caller_number` | str | — | CLI / phone number |
| `branch_id` | int | — | Branch ID |

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "customer_id": 42,
    "call_type": "inbound",
    "caller_number": "+9647801234567",
    "channel": "phone",
    "branch_id": 2
  }
}
```

**Response:** `{ "success": true, "data": { ...call_dict... } }`

**Side effects:**
- Snapshots `balance_at_call`, `outstanding_at_call`, `credit_limit_at_call`
- Sets `customer.last_call_date = now`
- Writes audit log `call_created`

---

### 1.4 End Call

```
POST /api/crm/calls/<call_id>/end
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `duration_seconds` | int | Total call duration |
| `outcome` | str | `resolved` / `callback` / `escalated` / `no_answer` |
| `notes` | str | Agent notes |
| `catalogue_sent` | bool | Was catalogue sent? |
| `catalogue_sent_via` | str | `whatsapp` / `email` / `telegram` |
| `recording_url` | str | External recording URL/path |

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "duration_seconds": 342,
    "outcome": "resolved",
    "notes": "Delivery confirmed for Thursday",
    "catalogue_sent": true,
    "catalogue_sent_via": "whatsapp"
  }
}
```

**Response:** `{ "success": true, "data": { ...call_dict... } }`

---

### 1.5 Update Call

```
POST /api/crm/calls/<call_id>/update
```

Writable fields (pass any subset):

| Name | Type |
|------|------|
| `notes` | str |
| `ai_summary` | str |
| `qa_score` | float |
| `issues_found` | str |
| `outcome` | str |
| `recording_url` | str |
| `catalogue_sent` | bool |
| `catalogue_sent_via` | str |
| `pos_order_id` | int |
| `pos_order_name` | str |
| `pos_order_total` | float |
| `pos_order_total_iqd` | float |
| `pos_order_state` | str |
| `pos_sale_order_name` | str |
| `pos_sap_synced` | bool |

**Response:** `{ "success": true, "data": { ...call_dict... } }`

---

### 1.6 Delete Call (Soft)

```
POST /api/crm/calls/<call_id>/delete
```

**Response:** `{ "success": true }`

---

### 1.7 Attach Recording

```
POST /api/crm/calls/<call_id>/attach_recording
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `recording_url` | str | ✓ | URL or path to the audio file |

**Response:**
```json
{ "success": true, "data": { "id": 101, "recording_url": "https://..." } }
```

---

## 2. Call Queue

### 2.1 List Queue

```
POST /api/crm/calls/queue/list
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `status` | str | `waiting` | `waiting` / `assigned` / `answered` / `abandoned` |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 5,
        "customer_id": 42,
        "customer_name": "Ahmed Al-Rashid",
        "channel": "phone",
        "caller_number": "+9647801234567",
        "queue_position": 1,
        "queued_at": "2026-03-31T09:10:00",
        "status": "waiting"
      }
    ]
  }
}
```

---

### 2.2 Add to Queue

```
POST /api/crm/calls/queue/add
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `customer_id` | int | CRM customer (optional — unknown callers allowed) |
| `channel` | str | Channel the call arrived on |
| `caller_number` | str | Phone number |

**Response:**
```json
{ "success": true, "data": { "id": 5, "queue_position": 3 } }
```

---

### 2.3 Assign Queue Entry

```
POST /api/crm/calls/queue/<queue_id>/assign
```

Assigns the queued call to **current JWT user**. No extra parameters needed.

**Response:** `{ "success": true }`

---

## 3. Active Call Context

### 3.1 Get Context

```
POST /api/crm/calls/active_context
```

Resolves customer by `call_id` or `phone_number` and returns a full context card.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `call_id` | int | Existing call ID |
| `phone_number` | str | Phone to search (phone_1 / phone_2 / phone_3 / whatsapp_number) |

_At least one of `call_id` or `phone_number` is needed to resolve a customer._

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": { "phone_number": "+9647801234567" }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customer": {
      "id": 42,
      "name": "Ahmed Al-Rashid",
      "phone": "+9647801234567",
      "email": "ahmed@example.com",
      "tier": "vip",
      "avatar": null,
      "total_orders": 18,
      "total_spent": 12500.00,
      "last_order_date": "2026-03-20",
      "open_tickets": 1,
      "notes": "Prefers afternoon deliveries"
    },
    "recent_tickets": [
      { "id": 55, "title": "Missing item in order #88", "status": "open", "created_at": "2026-03-28T11:00:00" }
    ],
    "recent_orders": [
      { "id": 88, "total": 750.00, "status": "done", "date": "2026-03-20" }
    ]
  }
}
```

If no customer is found: `"customer": null, "recent_tickets": [], "recent_orders": []`

---

## 4. Channel Config

### 4.1 List Channel Configs

```
POST /api/crm/channels/config_list
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `branch_id` | int | Filter by branch |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "channel": "whatsapp",
        "display_name": "WhatsApp Main",
        "color_hex": "#25D366",
        "icon": "whatsapp",
        "branch_id": 2,
        "branch_name": "Baghdad Branch",
        "assigned_user_ids": [7, 9],
        "assigned_user_names": ["Sara Hassan", "Ali Kareem"],
        "is_free_for_all": false,
        "is_active": true,
        "sla_threshold_seconds": 300,
        "work_hours_start": 8.0,
        "work_hours_end": 18.0
      }
    ]
  }
}
```

---

### 4.2 Create Channel Config

```
POST /api/crm/channels/config/create
```

**Parameters:**

| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| `channel` | str | ✓ | — | `whatsapp` / `instagram` / `telegram` / `tiktok` / `x` / `snapchat` / `email` / `website` |
| `branch_id` | int | — | — | Branch |
| `display_name` | str | — | — | UI label |
| `color_hex` | str | — | — | e.g. `"#25D366"` |
| `is_free_for_all` | bool | — | `true` | Any agent can handle |
| `sla_threshold_seconds` | int | — | 300 | SLA breach threshold |
| `work_hours_start` | float | — | 8.0 | e.g. `8.5` = 08:30 |
| `work_hours_end` | float | — | 18.0 | |

**Response:** `{ "success": true, "data": { ...config_dict... } }`

---

### 4.3 Update Channel Config

```
POST /api/crm/channels/config/<config_id>/update
```

**Updatable fields:** `display_name`, `color_hex`, `icon`, `branch_id`, `is_free_for_all`, `is_active`, `sla_threshold_seconds`, `work_hours_start`, `work_hours_end`

**Special field:** `assigned_user_ids` (list of user IDs — replaces the current list)

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "sla_threshold_seconds": 180,
    "assigned_user_ids": [7, 9, 12]
  }
}
```

**Response:** `{ "success": true, "data": { ...config_dict... } }`

---

### 4.4 Delete Channel Config (Soft)

```
POST /api/crm/channels/config/<config_id>/delete
```

**Response:** `{ "success": true }`

---

## 5. Chat Messages (Individual)

### 5.1 List Messages

```
POST /api/crm/channels/messages/list
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page` | int | 1 | |
| `per_page` | int | 50 | |
| `customer_id` | int | — | |
| `channel` | str | — | `whatsapp` / `instagram` / `telegram` / etc. |
| `status` | str | — | `pending` / `assigned` / `resolved` |
| `branch_id` | int | — | |
| `assigned_to_id` | int | — | |
| `sla_breached` | bool | — | `true` to see only breached messages |

**Message dict shape:**
```json
{
  "id": 201,
  "customer_id": 42,
  "customer_name": "Ahmed Al-Rashid",
  "channel": "whatsapp",
  "direction": "inbound",
  "channel_identity_id": 3,
  "content": "Hello, I need help with my order",
  "media_url": "",
  "sent_at": "2026-03-31T10:05:00",
  "read_at": null,
  "replied_by_agent_at": null,
  "assigned_to_id": null,
  "assigned_to_name": "",
  "owner_id": null,
  "owner_name": "",
  "conversation_id": "WA-42-20260331",
  "status": "pending",
  "sla_breached": false,
  "waiting_customer_response": false,
  "branch_id": 2
}
```

**Response:** `{ "success": true, "data": { "items": [...], "total": 120, "page": 1, "per_page": 50 } }`

---

### 5.2 Get Conversation Thread

```
POST /api/crm/channels/messages/conversation
```

Returns all messages in a conversation in chronological order.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `conversation_id` | str | ✓ | e.g. `"WA-42-20260331"` |

**Response:** `{ "success": true, "data": { "items": [...] } }` (sorted oldest → newest)

---

### 5.3 Create Message

```
POST /api/crm/channels/messages/create
```

Used by webhooks (inbound) and agent proactive outreach (outbound).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `customer_id` | int | ✓ | |
| `channel` | str | ✓ | |
| `content` | str | ✓ | Message text |
| `direction` | str | — | `inbound` (default) / `outbound` |
| `conversation_id` | str | — | Thread grouping key |
| `branch_id` | int | — | |
| `media_url` | str | — | Image/file URL |

**Side effects when `direction=outbound`:**
- Sets `assigned_to_id = current user`
- Sets `owner_id = current user`
- Sets `replied_by_agent_at = now` (FRT anchor)
- Sets `waiting_customer_response = true`
- Sets `status = assigned`

**Response:** `{ "success": true, "data": { ...message_dict... } }`

---

### 5.4 Assign Message

```
POST /api/crm/channels/messages/<message_id>/assign
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `assigned_to_id` | int | Agent to assign (defaults to current user) |

**Response:** `{ "success": true, "data": { ...message_dict... } }`

---

### 5.5 Reply to Message

```
POST /api/crm/channels/messages/<message_id>/reply
```

Creates a new **outbound** message in the same conversation.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `content` | str | ✓ | Reply text |
| `media_url` | str | — | Media attachment URL |

**Side effects:**
- Creates outbound message in same `conversation_id`
- Sets `owner_id` on original if not set
- Sets `replied_by_agent_at` on original (if first reply → FRT measurement)
- Sets `waiting_customer_response = true`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "content": "Hello Ahmed, your order #88 is dispatched and will arrive Thursday."
  }
}
```

**Response:** `{ "success": true, "data": { ...new_outbound_message_dict... } }`

---

### 5.6 Resolve Message/Conversation

```
POST /api/crm/channels/messages/<message_id>/resolve
```

Marks the message AND all messages in the same `conversation_id` as `resolved`.

**Response:** `{ "success": true }`

---

### 5.7 Transfer Conversation

```
POST /api/crm/channels/messages/<message_id>/transfer
```

Transfers ownership of the entire conversation to another agent.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `new_owner_id` | int | ✓ | User ID to transfer to |

**Side effects:** Sets `owner_id` and `assigned_to_id` on all messages in the conversation.

**Response:** `{ "success": true }`

---

## 6. Chat Sessions (Conversations)

Sessions group individual messages into managed conversations with lifecycle tracking (open → resolved → closed), SLA metrics, and unread counts.

### Session dict shape

```json
{
  "id": 10,
  "session_ref": "SESS-00010",
  "conversation_id": "WA-42-20260331",
  "customer_id": 42,
  "customer_name": "Ahmed Al-Rashid",
  "channel": "whatsapp",
  "status": "open",
  "branch_id": 2,
  "assigned_to_id": 7,
  "assigned_to_name": "Sara Hassan",
  "owner_id": 7,
  "owner_name": "Sara Hassan",
  "opened_at": "2026-03-31T10:05:00",
  "resolved_at": null,
  "closed_at": null,
  "last_message_at": "2026-03-31T10:22:00",
  "reopen_count": 0,
  "first_response_seconds": 120,
  "handle_time_seconds": 0,
  "sla_breached": false,
  "message_count": 4,
  "unread_count": 2
}
```

---

### 6.1 List Sessions

```
POST /api/crm/chat/sessions/list
```

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page` | int | 1 | |
| `per_page` | int | 30 | |
| `customer_id` | int | — | |
| `channel` | str | — | |
| `status` | str | — | `open` / `pending` / `resolved` / `closed` |
| `branch_id` | int | — | |
| `assigned_to_id` | int | — | |
| `sla_breached` | bool | — | |

**Response:** `{ "success": true, "data": { "total": 44, "page": 1, "per_page": 30, "items": [...] } }`

---

### 6.2 Get Session Detail

```
POST /api/crm/chat/sessions/<session_id>
```

Returns session + full message thread.

**Side effects:** Resets `unread_count` to 0.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 10,
    "session_ref": "SESS-00010",
    "...": "...all session fields...",
    "messages": [
      {
        "id": 201,
        "direction": "inbound",
        "content": "Hello, I need help",
        "media_url": "",
        "sent_at": "2026-03-31T10:05:00",
        "read_at": null,
        "agent_id": null,
        "agent_name": ""
      },
      {
        "id": 202,
        "direction": "outbound",
        "content": "Hello Ahmed, how can I help?",
        "sent_at": "2026-03-31T10:07:00",
        "agent_id": 7,
        "agent_name": "Sara Hassan"
      }
    ]
  }
}
```

---

### 6.3 Resolve Session

```
POST /api/crm/chat/sessions/<session_id>/resolve
```

**Side effects:**
- Sets `session.status = resolved`, `resolved_at = now`
- Resolves all open messages in `conversation_id`

**Response:** `{ "success": true, "data": { ...session_dict... } }`

---

### 6.4 Re-open Session

```
POST /api/crm/chat/sessions/<session_id>/reopen
```

Re-opens a resolved or closed session. Increments `reopen_count`.

**Response:** `{ "success": true, "data": { ...session_dict... } }`

---

### 6.5 Unread Counts (Badge)

```
POST /api/crm/chat/sessions/unread_counts
```

For the notification badge in the sidebar.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `branch_id` | int | Filter by branch |

**Response:**
```json
{
  "success": true,
  "data": {
    "by_channel": {
      "whatsapp": 5,
      "instagram": 2,
      "telegram": 0
    },
    "total": 7
  }
}
```

---

## 7. Agent Status

Controls agent availability for call routing and chat assignment.

**Valid status values:** `offline` | `online` | `busy` | `break`

**Valid transitions:**
```
offline → online
online  → busy | break | offline
busy    → online | break | offline
break   → online | offline
```

---

### 7.1 Get Agent Status

```
POST /api/crm/agent/status
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `agent_id` | int | User ID (defaults to current JWT user) |

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 3,
    "agent_id": 7,
    "agent_name": "Sara Hassan",
    "status": "online",
    "is_available": true,
    "open_chat_count": 2,
    "active_call_id": null,
    "branch_id": 2,
    "last_status_change": "2026-03-31T08:45:00"
  }
}
```

If no record exists: `{ "status": "offline", "agent_id": 7 }`

---

### 7.2 Set Agent Status

```
POST /api/crm/agent/set_status
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `status` | str | ✓ | `online` / `busy` / `break` / `offline` |
| `branch_id` | int | — | Update branch at same time |

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": { "status": "online", "branch_id": 2 }
}
```

**Response:**
```json
{ "success": true, "data": { "status": "online", "is_available": true } }
```

**Error (invalid transition):**
```json
{ "success": false, "error": "Invalid transition: busy → offline. Allowed: ['break', 'online']" }
```

---

## 8. Email — Customer Inbox

### 8.1 Get Customer Emails

```
POST /api/crm/email/customer/<customer_id>/messages
```

All emails linked to a CRM customer (covers typed and generic links).

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `folder` | str | — | `inbox` / `sent` / `drafts` / `trash` / `spam` / `archive` |
| `page` | int | 1 | |
| `per_page` | int | 30 | |

**Email list item shape:**
```json
{
  "id": 500,
  "subject": "Your order #88 is confirmed",
  "from_address": "orders@store.com",
  "from_name": "Store Orders",
  "preview": "Dear Ahmed, we are pleased to confirm...",
  "date": "2026-03-20T14:30:00",
  "folder": "inbox",
  "is_read": true,
  "is_starred": false,
  "attachment_count": 1,
  "has_link": true,
  "linked_record": {
    "model": "lugal.crm.customer",
    "id": 42,
    "name": "Ahmed Al-Rashid"
  },
  "crm_links": {
    "customer": { "id": 42, "name": "Ahmed Al-Rashid" },
    "ticket": null
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 42,
    "customer_name": "Ahmed Al-Rashid",
    "total": 12,
    "page": 1,
    "per_page": 30,
    "items": [...]
  }
}
```

---

### 8.2 Get Customer Email Threads

```
POST /api/crm/email/customer/<customer_id>/thread
```

Returns emails grouped by subject (strips Re:/Fwd: prefixes for grouping).

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `subject_contains` | str | Filter by subject keyword |

**Response:**
```json
{
  "success": true,
  "data": {
    "customer_id": 42,
    "threads": [
      {
        "subject": "Your order #88 is confirmed",
        "messages": [
          { "id": 500, "direction_hint": "inbox", "date": "2026-03-20T14:30:00", "..." : "..." },
          { "id": 501, "direction_hint": "sent",  "date": "2026-03-20T16:00:00", "..." : "..." }
        ]
      },
      {
        "subject": "Invoice for March purchases",
        "messages": [...]
      }
    ]
  }
}
```

---

## 9. Email — Message Operations

### 9.1 List Messages (Agent Inbox)

```
POST /api/crm/email/messages/list
```

Returns **current JWT user's** emails with optional CRM filters.

**Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `page` | int | 1 | |
| `per_page` | int | 30 | |
| `folder` | str | `inbox` | `inbox` / `sent` / `drafts` / `trash` / `spam` / `archive` |
| `customer_id` | int | — | Filter to emails linked to this customer |
| `ticket_id` | int | — | Filter to emails linked to this ticket |
| `is_read` | bool | — | `false` = unread only |

**Response:** `{ "success": true, "data": { "total": 45, "page": 1, "per_page": 30, "folder": "inbox", "items": [...] } }`

---

### 9.2 Get Message Detail

```
POST /api/crm/email/messages/<message_id>
```

Returns full detail including HTML body, plain text, addresses, and attachments.

**Side effects:** Marks message as `is_read = true`

**Full detail shape:**
```json
{
  "id": 500,
  "subject": "Your order #88 is confirmed",
  "from_address": "orders@store.com",
  "from_name": "Store Orders",
  "preview": "Dear Ahmed...",
  "date": "2026-03-20T14:30:00",
  "folder": "inbox",
  "is_read": true,
  "is_starred": false,
  "attachment_count": 1,
  "has_link": true,
  "linked_record": { "model": "lugal.crm.customer", "id": 42, "name": "Ahmed Al-Rashid" },
  "crm_links": { "customer": { "id": 42, "name": "Ahmed Al-Rashid" }, "ticket": null },
  "body_html": "<p>Dear Ahmed, we are pleased to confirm...</p>",
  "body_text": "Dear Ahmed, we are pleased to confirm...",
  "to_addresses": [{ "name": "Ahmed Al-Rashid", "email": "ahmed@example.com" }],
  "cc_addresses": [],
  "message_id": "<msg-abc123@store.com>",
  "in_reply_to": "",
  "attachments": [
    {
      "id": 77,
      "name": "invoice_88.pdf",
      "mimetype": "application/pdf",
      "url": "/web/content/77?download=true"
    }
  ]
}
```

---

### 9.3 Link Email to CRM Record

```
POST /api/crm/email/messages/<message_id>/link
```

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `model` | str | ✓ | Must be in allowed list (see below) |
| `record_id` | int | ✓ | Record ID |
| `record_name` | str | — | Auto-resolved if omitted |

**Allowed models:** `lugal.crm.customer`, `lugal.crm.ticket`, `lugal.crm.interaction`, `lugal.crm.supply.po`, `res.partner`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "model": "lugal.crm.ticket",
    "record_id": 55
  }
}
```

**Response:** `{ "success": true, "data": { ...email_list_dict... } }`

---

### 9.4 Unlink Email from CRM Record

```
POST /api/crm/email/messages/<message_id>/unlink
```

Removes all CRM associations (generic link + typed Many2one fields).

**Response:** `{ "success": true, "data": { ...email_list_dict... } }`

---

### 9.5 Mark Email as Read

```
POST /api/crm/email/messages/<message_id>/read
```

**Response:** `{ "success": true }`

---

### 9.6 Move Email to Trash

```
POST /api/crm/email/messages/<message_id>/trash
```

Moves to `trash` folder.

**Response:** `{ "success": true }`

---

### 9.7 Archive Email

```
POST /api/crm/email/messages/<message_id>/archive
```

Moves to `archive` folder.

**Response:** `{ "success": true }`

---

## 10. Email — Send

### 10.1 Send Email

```
POST /api/crm/email/send
```

Sends via SMTP, stores sent message, and optionally logs a CRM interaction.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `account_id` | int | ✓ | `lugal.email.account` ID (agent's email account) |
| `to_addresses` | list | ✓ | `[{"name": "Ahmed", "email": "ahmed@example.com"}]` |
| `subject` | str | ✓ | Email subject |
| `body_html` | str | — | HTML body |
| `body_text` | str | — | Plain text fallback |
| `cc_addresses` | list | — | Same format as `to_addresses` |
| `customer_id` | int | — | Links sent email to CRM customer |
| `ticket_id` | int | — | Links sent email to CRM ticket |
| `in_reply_to` | str | — | `Message-ID` of email being replied to |
| `attachment_ids` | list | — | `ir.attachment` ID list |

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "account_id": 3,
    "to_addresses": [{ "name": "Ahmed Al-Rashid", "email": "ahmed@example.com" }],
    "subject": "Re: Your order #88",
    "body_html": "<p>Dear Ahmed, your order will arrive Thursday.</p>",
    "body_text": "Dear Ahmed, your order will arrive Thursday.",
    "customer_id": 42,
    "ticket_id": 55
  }
}
```

**Response:**
```json
{ "success": true, "data": { "message_id": 501 } }
```

**Side effects:**
1. Sends email via SMTP using the account's credentials
2. Stores a `sent` folder `lugal.email.message` record
3. Links it to `customer_id` and `ticket_id` if provided (sets `linked_customer_id` + `linked_ticket_id`)
4. Creates a `lugal.crm.interaction` record with `type=email` if `customer_id` provided
5. Writes audit log `email_sent`

---

## Error Reference

| Error Message | Cause |
|---------------|-------|
| `Unauthorized` | JWT token missing, expired, or invalid |
| `Customer not found` | `customer_id` does not exist |
| `Call not found` | `call_id` does not exist or is soft-deleted |
| `Queue entry not found` | `queue_id` does not exist |
| `Config not found` | `config_id` does not exist or soft-deleted |
| `Message not found` | message ID invalid or soft-deleted |
| `Session not found` | session ID invalid or soft-deleted |
| `Email account not found` | `account_id` does not exist |
| `Model '...' is not an allowed link target` | Model not in `ALLOWED_LINK_MODELS` |
| `conversation_id required` | `conversation_id` was empty/null |
| `Invalid transition: X → Y. Allowed: [...]` | Invalid agent status change |

---

## Enumerations

### Call outcome
`resolved` | `callback` | `escalated` | `no_answer`

### Call queue status
`waiting` | `assigned` | `answered` | `abandoned`

### Chat channel
`whatsapp` | `instagram` | `telegram` | `tiktok` | `x` | `snapchat` | `email` | `website`

### Chat message status
`pending` | `assigned` | `resolved`

### Chat message direction
`inbound` | `outbound`

### Chat session status
`open` | `pending` | `resolved` | `closed`

### Agent status
`offline` | `online` | `busy` | `break`

### Email folder
`inbox` | `sent` | `drafts` | `trash` | `spam` | `archive`

### Call script category
`faq` | `guided_workflow` | `objection_handling`

### Message template channel
`whatsapp` | `telegram` | `email` | `any`

### Catalogue sent via
`whatsapp` | `email` | `telegram`

---

## 11. Supply Internal Messaging

> Base path: `/api/crm/supply/...`  
> All endpoints require JWT auth.

---

### 11.1 List Conversations

```
POST /api/crm/supply/conversations/list
```

Returns all conversations the current user participates in, sorted by most recent activity. The team channel always appears first.

**Parameters:** _(none)_

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "type": "team",
        "name": "Team Channel",
        "last_activity": "2026-03-27T10:00:00",
        "message_count": 120,
        "is_archived": false,
        "participants": [
          { "id": 3, "name": "Sara Ahmed", "avatar": "/web/image/res.users/3/avatar_128" }
        ]
      },
      {
        "id": 5,
        "type": "dm",
        "name": "Chat with Khalid",
        "last_activity": "2026-03-27T09:30:00",
        "message_count": 14,
        "is_archived": false,
        "participants": [
          { "id": 2, "name": "Khalid Hassan", "avatar": "/web/image/res.users/2/avatar_128" }
        ]
      }
    ]
  }
}
```

---

### 11.2 List Messages

```
POST /api/crm/supply/messages/list
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thread_id` | int | No | Filter by conversation ID |
| `page` | int | No | Default `1` |
| `per_page` | int | No | Default `20` |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 42,
    "page": 1,
    "per_page": 20,
    "thread_id": 5,
    "conversation_type": "dm",
    "items": [
      {
        "id": 101,
        "body": "Hello!",
        "created_at": "2026-03-27T09:30:00",
        "thread_id": 5,
        "conversation_type": "dm",
        "sender": { "id": 3, "name": "Sara Ahmed", "avatar": "/web/image/res.users/3/avatar_128" },
        "participants": [
          { "id": 3, "name": "Sara Ahmed" },
          { "id": 2, "name": "Khalid Hassan" }
        ]
      }
    ]
  }
}
```

---

### 11.3 Create Message

```
POST /api/crm/supply/messages/create
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `body`* | string | Yes | Message text |
| `thread_id` | int | No | Reply to existing conversation |
| `recipient_ids` | int[] | No | `[userId]` for DM, `[id1,id2]` for group |
| `group_name` | string | No | Display name for new group threads |

**Conversation resolution logic:**
- `thread_id` provided → use existing conversation
- `recipient_ids` has 1 user → find or create DM thread with that user
- `recipient_ids` has 2+ users → create new group thread
- Neither → post to team channel

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 102,
    "body": "Hello!",
    "thread_id": 5,
    "conversation_type": "dm",
    "created_at": "2026-03-27T10:01:00",
    "sender": { "id": 3, "name": "Sara Ahmed", "avatar": "/web/image/res.users/3/avatar_128" },
    "participants": [
      { "id": 3, "name": "Sara Ahmed" },
      { "id": 2, "name": "Khalid Hassan" }
    ]
  }
}
```

---

## 12. Projects

> Base path: `/api/crm/projects/...`  
> All endpoints require JWT auth.

---

### 12.1 List Projects

```
POST /api/crm/projects/list
```

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `search` | string | `""` | Filter by project name (case-insensitive) |
| `my` | bool | `false` | Return only projects where caller is manager or member |
| `page` | int | `1` | Page number |
| `per_page` | int | `20` | Results per page |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 5,
    "page": 1,
    "per_page": 20,
    "items": [
      {
        "id": 1,
        "name": "Website Redesign",
        "description": "Revamp the corporate site",
        "color": 3,
        "date_start": "2026-01-01",
        "date_end": "2026-06-30",
        "privacy": "employees",
        "is_favorite": false,
        "manager": { "id": 5, "name": "Rami Hassan", "avatar": "/web/image/res.users/5/avatar_128" },
        "stage": { "id": 2, "name": "In Progress" },
        "last_update_status": "on_track",
        "allow_milestones": true,
        "milestone_progress": 40.0,
        "tag_ids": [1, 3],
        "tags": [{ "id": 1, "name": "Frontend", "color": 2 }, { "id": 3, "name": "Design", "color": 5 }],
        "task_count": 18,
        "open_task_count": 12,
        "closed_task_count": 6,
        "task_completion_pct": 33.3,
        "milestone_count": 3,
        "milestone_count_reached": 1
      }
    ]
  }
}
```

---

### 12.2 Create Project

```
POST /api/crm/projects/create
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Project name |
| `description` | string | No | Rich text description |
| `manager_id` | int | No | User ID of project manager (defaults to caller) |
| `date_start` | string | No | `YYYY-MM-DD` |
| `date_end` | string | No | `YYYY-MM-DD` |
| `privacy` | string | No | `employees` \| `followers` \| `portal` \| `invited_users` |
| `tag_ids` | int[] | No | List of project tag IDs |
| `allow_milestones` | bool | No | Default `true` |

**Response:** Project object (same shape as list item above)

---

### 12.3 Get Project

```
POST /api/crm/projects/<id>/get
```

**Parameters:** _(none — ID in URL)_

**Response:** `{ "success": true, "data": { ...project with stats... } }`

---

### 12.4 Update Project

```
POST /api/crm/projects/<id>/update
```

**Accepted fields (all optional):**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New name |
| `description` | string | New description |
| `manager_id` | int | New manager user ID |
| `date_start` | string | `YYYY-MM-DD` |
| `date_end` | string | `YYYY-MM-DD` |
| `privacy` | string | Visibility level |
| `color` | int | Color index 0–11 |
| `tag_ids` | int[] | Replaces all tags |
| `allow_milestones` | bool | Enable milestones |
| `last_update_status` | string | `on_track` \| `at_risk` \| `off_track` \| `on_hold` \| `to_define` \| `done` |

**Response:** Updated project object

---

### 12.5 Archive Project

```
POST /api/crm/projects/<id>/archive
```

Soft-deletes the project (sets `active = false`). Recoverable from Odoo backend.

**Response:** `{ "success": true, "data": { "id": 1, "archived": true } }`

---

### 12.6 Kanban Board

```
POST /api/crm/projects/<id>/kanban
```

Returns the full board: all stages (columns) with their tasks grouped inside.

**Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `include_done` | bool | `false` | Include tasks with state `1_done` or `1_canceled` |

**Response:**
```json
{
  "success": true,
  "data": {
    "project": { ...project object... },
    "columns": [
      {
        "stage": { "id": 10, "name": "To Do", "sequence": 1, "color": 0, "fold": false },
        "task_count": 5,
        "tasks": [ ...task objects... ]
      },
      {
        "stage": { "id": 11, "name": "In Progress", "sequence": 2, "color": 2, "fold": false },
        "task_count": 3,
        "tasks": [ ...task objects... ]
      }
    ]
  }
}
```

---

### 12.7 Project Stats

```
POST /api/crm/projects/<id>/stats
```

Returns task and milestone counters for a project.

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "task_count": 18,
    "open_task_count": 12,
    "closed_task_count": 6,
    "task_completion_pct": 33.3,
    "milestone_count": 3,
    "milestone_count_reached": 1,
    "milestone_progress": 33.3,
    "last_update_status": "on_track"
  }
}
```

---

## 13. Kanban Stages

Stages are shared Kanban columns that can be linked to multiple projects.

---

### 13.1 List Stages for a Project

```
POST /api/crm/projects/<project_id>/stages/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 10, "name": "To Do", "sequence": 1, "color": 0, "fold": false },
      { "id": 11, "name": "In Progress", "sequence": 2, "color": 2, "fold": false },
      { "id": 12, "name": "Done", "sequence": 3, "color": 10, "fold": true }
    ]
  }
}
```

---

### 13.2 Create Stage

```
POST /api/crm/projects/stages/create
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `project_id`* | int | Yes | ID of the project to attach the stage to |
| `name`* | string | Yes | Stage name |
| `sequence` | int | No | Sort order (lower = leftmost column) |
| `color` | int | No | Color index 0–11 (default `0`) |

**Response:** Stage object

---

### 13.3 Update Stage

```
POST /api/crm/projects/stages/<stage_id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New label |
| `sequence` | int | New sort position |
| `color` | int | New color index |
| `fold` | bool | Collapse column in kanban |

**Response:** Updated stage object

---

### 13.4 Delete Stage

```
POST /api/crm/projects/stages/<stage_id>/delete
```

Permanently deletes the stage. Tasks that were in this stage become stageless.

**Response:** `{ "success": true, "data": { "id": 10, "deleted": true } }`

---

## 14. Project Tasks

> Prefix `ptasks` is used to avoid naming collisions with the existing CRM tasks API (`/api/crm/tasks/...`).

---

### Task Object Shape

```json
{
  "id": 55,
  "name": "Design homepage mockup",
  "description": "Figma file must be approved first.",
  "project_id": 1,
  "project_name": "Website Redesign",
  "stage": { "id": 11, "name": "In Progress" },
  "priority": "1",
  "priority_label": "High",
  "state": "01_in_progress",
  "state_label": "In Progress",
  "is_closed": false,
  "date_deadline": "2026-04-15",
  "assignees": [
    { "id": 5, "name": "Rami Hassan", "avatar": "/web/image/res.users/5/avatar_128" }
  ],
  "assignee_ids": [5],
  "tag_ids": [7],
  "tags": [{ "id": 7, "name": "Design" }],
  "milestone": { "id": 2, "name": "MVP Launch", "is_reached": false },
  "parent_task": null,
  "subtask_count": 3,
  "closed_subtask_count": 1,
  "color": 0,
  "created_at": "2026-02-01T08:00:00",
  "updated_at": "2026-03-20T14:22:00"
}
```

---

### 14.1 List Tasks

```
POST /api/crm/projects/ptasks/list
```

**Parameters (all optional):**

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | int | Restrict to a specific project |
| `stage_id` | int | Restrict to a specific stage |
| `assignee_id` | int | Tasks assigned to this user |
| `milestone_id` | int | Tasks linked to this milestone |
| `priority` | string | `"0"` (Normal) or `"1"` (High) |
| `state` | string | e.g. `"01_in_progress"`, `"1_done"` |
| `search` | string | Name filter (case-insensitive) |
| `page` | int | Default `1` |
| `per_page` | int | Default `30` |

**Response:** `{ total, page, per_page, items: [ ...task objects... ] }`

---

### 14.2 Create Task

```
POST /api/crm/projects/ptasks/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Task title |
| `project_id` | int | No | Parent project |
| `stage_id` | int | No | Initial kanban stage |
| `assignee_ids` | int[] | No | List of user IDs (defaults to caller) |
| `description` | string | No | |
| `priority` | string | No | `"0"` or `"1"` |
| `date_deadline` | string | No | `YYYY-MM-DD` |
| `milestone_id` | int | No | |
| `parent_id` | int | No | Create as subtask of this task |
| `tag_ids` | int[] | No | |

**Response:** Full task object including `checklists: []`

---

### 14.3 Get Task

```
POST /api/crm/projects/ptasks/<id>/get
```

Returns full task detail including checklists.

**Response:** `{ "success": true, "data": { ...task with checklists... } }`

---

### 14.4 Update Task

```
POST /api/crm/projects/ptasks/<id>/update
```

**Accepted fields:**

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | |
| `description` | string | |
| `priority` | string | `"0"` or `"1"` |
| `state` | string | See task state enum below |
| `date_deadline` | string | `YYYY-MM-DD` or `null` to clear |
| `stage_id` | int | Move to stage |
| `milestone_id` | int | or `null` to clear |
| `color` | int | 0–11 |
| `tag_ids` | int[] | Replaces all tags |
| `assignee_ids` | int[] | Replaces all assignees |

**Response:** Updated task object

---

### 14.5 Assign Task

```
POST /api/crm/projects/ptasks/<id>/assign
```

Replaces the full assignee list.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assignee_ids`* | int[] | Yes | New assignee list. Pass `[]` to unassign all. |

**Response:** Updated task object

---

### 14.6 Move Task (Change Stage)

```
POST /api/crm/projects/ptasks/<id>/move
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `stage_id`* | int | Yes | Target stage ID |

**Response:** Updated task object

---

### 14.7 Delete Task

```
POST /api/crm/projects/ptasks/<id>/delete
```

Soft-deletes the task (`active = false`).

**Response:** `{ "success": true, "data": { "id": 55, "archived": true } }`

---

### 14.8 List Subtasks

```
POST /api/crm/projects/ptasks/<id>/subtasks
```

Lists all direct child (sub)tasks of the given task.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | `1` | |
| `per_page` | int | `30` | |

**Response:**
```json
{
  "success": true,
  "data": {
    "parent_task_id": 55,
    "total": 3,
    "items": [ ...task objects... ]
  }
}
```

---

## 15. Milestones

---

### 15.1 List Milestones

```
POST /api/crm/projects/<project_id>/milestones/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 2,
        "name": "MVP Launch",
        "deadline": "2026-05-01",
        "is_reached": false,
        "reached_date": null,
        "task_count": 8,
        "done_task_count": 3,
        "is_deadline_exceeded": false
      }
    ]
  }
}
```

---

### 15.2 Create Milestone

```
POST /api/crm/projects/<project_id>/milestones/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Milestone name |
| `deadline` | string | No | `YYYY-MM-DD` |

**Response:** Milestone object

---

### 15.3 Update Milestone

```
POST /api/crm/projects/milestones/<id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New name |
| `deadline` | string | `YYYY-MM-DD` or `null` to clear |

**Response:** Updated milestone object

---

### 15.4 Toggle Milestone Reached

```
POST /api/crm/projects/milestones/<id>/toggle
```

Flips `is_reached` between `true` and `false`. Sets `reached_date` automatically.

**Response:** Updated milestone object

---

### 15.5 Delete Milestone

```
POST /api/crm/projects/milestones/<id>/delete
```

**Response:** `{ "success": true, "data": { "id": 2, "deleted": true } }`

---

## 16. Checklists

> Powered by the **Cybrosys projects_task_checklists** module.  
> Endpoints return `500` with a descriptive message if the module is not installed.

A **checklist** is a named group (e.g. "Acceptance Criteria") that belongs to a task.  
Each checklist contains ordered **items** (individual to-do lines).

---

### 16.1 List Checklists on Task

```
POST /api/crm/projects/ptasks/<task_id>/checklists/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "task_id": 55,
    "items": [
      {
        "id": 10,
        "name": "Acceptance Criteria",
        "description": "",
        "item_count": 3,
        "items": [
          { "id": 31, "name": "Mobile responsive", "description": "", "sequence": 1 },
          { "id": 32, "name": "Passes accessibility audit", "description": "", "sequence": 2 },
          { "id": 33, "name": "Approved by QA", "description": "", "sequence": 3 }
        ]
      }
    ]
  }
}
```

---

### 16.2 Create Checklist on Task

```
POST /api/crm/projects/ptasks/<task_id>/checklists/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Checklist group title |
| `description` | string | No | |

**Response:** New checklist object (with `items: []`)

---

### 16.3 Delete Checklist

```
POST /api/crm/projects/checklists/<checklist_id>/delete
```

Permanently deletes the checklist and all its items.

**Response:** `{ "success": true, "data": { "id": 10, "deleted": true } }`

---

### 16.4 Add Item to Checklist

```
POST /api/crm/projects/checklists/<checklist_id>/items/add
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Item label |
| `description` | string | No | |
| `sequence` | int | No | Sort order |

**Response:**
```json
{
  "success": true,
  "data": { "id": 34, "name": "Final sign-off", "description": "", "sequence": 4, "checklist_id": 10 }
}
```

---

### 16.5 Update Checklist Item

```
POST /api/crm/projects/checklists/items/<item_id>/update
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | New label |
| `description` | string | |
| `sequence` | int | New sort position |

**Response:** Updated item object

---

### 16.6 Delete Checklist Item

```
POST /api/crm/projects/checklists/items/<item_id>/delete
```

**Response:** `{ "success": true, "data": { "id": 34, "deleted": true } }`

---

## 17. Project Members

Project members are stored as **favourite users** on the project record.

---

### 17.1 List Members

```
POST /api/crm/projects/<project_id>/members/list
```

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": 1,
    "manager_id": 5,
    "items": [
      { "id": 5, "name": "Rami Hassan", "email": "rami@example.com", "avatar": "/web/image/res.users/5/avatar_128", "is_manager": true },
      { "id": 7, "name": "Lina Karim",  "email": "lina@example.com", "avatar": "/web/image/res.users/7/avatar_128", "is_manager": false }
    ]
  }
}
```

---

### 17.2 Add Members

```
POST /api/crm/projects/<project_id>/members/add
```

Adds users to the project's member list (non-destructive — existing members are kept).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids`* | int[] | Yes | List of user IDs to add |

**Response:** `{ "success": true, "data": { "project_id": 1, "added": [7, 8] } }`

---

### 17.3 Remove Members

```
POST /api/crm/projects/<project_id>/members/remove
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `user_ids`* | int[] | Yes | List of user IDs to remove |

**Response:** `{ "success": true, "data": { "project_id": 1, "removed": [7] } }`

---

## 18. Project Tags

Tags are global labels (shared across all projects).

---

### 18.1 List Tags

```
POST /api/crm/projects/tags/list
```

| Field | Type | Description |
|-------|------|-------------|
| `search` | string | Filter by name |

**Response:**
```json
{ "success": true, "data": { "items": [{ "id": 1, "name": "Frontend", "color": 2 }] } }
```

---

### 18.2 Create Tag

```
POST /api/crm/projects/tags/create
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name`* | string | Yes | Tag label |
| `color` | int | No | Color index 0–11 (default `0`) |

**Response:** `{ "success": true, "data": { "id": 9, "name": "Backend", "color": 3 } }`

---

## Enumerations (Extended)

### Task State
| Value | Label |
|-------|-------|
| `01_in_progress` | In Progress |
| `02_changes_requested` | Changes Requested |
| `03_approved` | Approved |
| `04_waiting_normal` | Waiting |
| `1_done` | Done |
| `1_canceled` | Canceled |

### Task Priority
| Value | Label |
|-------|-------|
| `0` | Normal |
| `1` | High |

### Project Status (`last_update_status`)
`on_track` | `at_risk` | `off_track` | `on_hold` | `to_define` | `done`

### Project Privacy (`privacy_visibility`)
`employees` | `followers` | `portal` | `invited_users`

### Supply Conversation Type
`team` | `dm` | `group`
