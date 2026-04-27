# Chat & Calling System — Complete Frontend Developer Guide

> **Version:** 1.0.0  
> **Date:** 2026-03-30  
> **Base URL:** `http://<SERVER>:8070`  
> **Protocol:** All endpoints use **JSON-RPC 2.0** (POST)  
> **Auth:** `Authorization: Bearer <jwt_token>` on every request

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Data Model — Key Concepts](#2-data-model--key-concepts)
3. [Chat System API](#3-chat-system-api)
   - 3.1 Channel Config CRUD
   - 3.2 Inbox — List Messages
   - 3.3 Conversation Thread
   - 3.4 Create Message (Inbound / Outbound)
   - 3.5 Reply to Message
   - 3.6 Assign Conversation
   - 3.7 Resolve Conversation
   - 3.8 Transfer Conversation
4. [Calling System API](#4-calling-system-api)
   - 4.1 List Calls
   - 4.2 Get Single Call
   - 4.3 Start a Call
   - 4.4 End a Call
   - 4.5 Update Call (QA, Notes, Recording)
   - 4.6 Attach Recording URL
   - 4.7 Delete Call
   - 4.8 Call Queue — List
   - 4.9 Call Queue — Add
   - 4.10 Call Queue — Assign
   - 4.11 Active Call Context (Screen Pop)
5. [Enumerations Reference](#5-enumerations-reference)
6. [TypeScript Type Definitions](#6-typescript-type-definitions)
7. [Real-World Usage Flows](#7-real-world-usage-flows)
8. [Error Handling Reference](#8-error-handling-reference)

---

## 1. System Overview

The system has **two independent communication modules** that share the same customer data:

```
┌─────────────────────────────────────────────────────────────┐
│                    lugal_crm Backend                        │
│                                                             │
│  ┌─────────────────────┐    ┌──────────────────────────┐   │
│  │   CHAT SYSTEM        │    │   CALLING SYSTEM          │   │
│  │                      │    │                          │   │
│  │  OmnichannelMessage  │    │  Call                    │   │
│  │  (WhatsApp/Instagram │    │  (Inbound/Outbound)      │   │
│  │   Telegram/TikTok    │    │                          │   │
│  │   Snapchat/X/Email)  │    │  CallQueue               │   │
│  │                      │    │  (Waiting room)          │   │
│  │  ChannelConfig       │    │                          │   │
│  │  (SLA, Work Hours)   │    │  CallScript              │   │
│  └─────────┬───────────┘    └──────────┬───────────────┘   │
│            │                           │                    │
│            └──────────┬────────────────┘                    │
│                       ▼                                     │
│              lugal.crm.customer                             │
│              (shared customer entity)                       │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions
- A **conversation** is a group of messages sharing the same `conversation_id` (string)
- A **call** is a discrete event with a start time, end time, outcome, and optional recording URL
- Both systems write audit logs automatically
- SLA breach detection runs as a **cron job every 5 minutes** — it sets `sla_breached: true` on pending inbound messages that exceeded the channel's `sla_threshold_seconds`

---

## 2. Data Model — Key Concepts

### Channels (Chat Sources)

| Value | Platform |
|-------|----------|
| `whatsapp` | WhatsApp Business API |
| `instagram` | Instagram DMs |
| `telegram` | Telegram Bot |
| `tiktok` | TikTok comments/DMs |
| `x` | X (Twitter) DMs |
| `snapchat` | Snapchat |
| `email` | Email (via lugal_email) |
| `website` | Website chat widget |

### Message Status Flow

```
inbound message arrives
        │
        ▼
   [pending]  ──── SLA cron ──→  sla_breached = true
        │
  agent assigns / replies
        │
        ▼
   [assigned]
        │
  agent marks resolved
        │
        ▼
   [resolved]
```

### Call Outcome Values

| Value | Meaning |
|-------|---------|
| `resolved` | Issue resolved during call |
| `callback` | Customer requested callback |
| `escalated` | Escalated to supervisor |
| `no_answer` | No answer / voicemail |

---

## 3. Chat System API

### JSON-RPC Request Template

```javascript
const crmPost = (url, params, token) =>
  fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params }),
  }).then(r => r.json()).then(r => r.result);
```

---

### 3.1 — List Channel Configs

Returns all configured channels (WhatsApp, Instagram, etc.) with their SLA rules and work hours.

```
POST /api/crm/channels/config_list
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "branch_id": 2
  }
}
```
> `branch_id` is optional — omit to get all branches.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "items": [
        {
          "id": 1,
          "channel": "whatsapp",
          "display_name": "WhatsApp Main",
          "color_hex": "#25D366",
          "icon": "fab fa-whatsapp",
          "branch_id": 2,
          "branch_name": "Riyadh Branch",
          "assigned_user_ids": [5, 8, 12],
          "assigned_user_names": ["Ahmed", "Sara", "Khalid"],
          "is_free_for_all": false,
          "is_active": true,
          "sla_threshold_seconds": 300,
          "work_hours_start": 8.0,
          "work_hours_end": 18.0
        }
      ]
    }
  }
}
```

> `work_hours_start/end` are **float hours**: `8.0` = 08:00, `13.5` = 13:30

---

### 3.2 — Create Channel Config

```
POST /api/crm/channels/config/create
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "channel": "whatsapp",
    "branch_id": 2,
    "display_name": "WhatsApp Sales",
    "color_hex": "#25D366",
    "is_free_for_all": false,
    "sla_threshold_seconds": 300,
    "work_hours_start": 8.0,
    "work_hours_end": 18.0
  }
}
```

**Response:** Returns the created config object (same shape as list item).

---

### 3.3 — Update Channel Config

```
POST /api/crm/channels/config/<id>/update
```

**Request (partial update):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "sla_threshold_seconds": 180,
    "work_hours_start": 9.0,
    "work_hours_end": 17.0,
    "assigned_user_ids": [5, 8, 15]
  }
}
```

> To update `assigned_user_ids`, send the **complete new list** — it replaces the existing list.

---

### 3.4 — Delete Channel Config

```
POST /api/crm/channels/config/<id>/delete
```

**Request:** `{ "params": {} }`  
**Response:** `{ "success": true }`

---

### 3.5 — Inbox: List Messages

Returns the omnichannel inbox with filtering, pagination, and SLA breach indicators.

```
POST /api/crm/channels/messages/list
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "page": 1,
    "per_page": 50,
    "customer_id": null,
    "channel": "whatsapp",
    "status": "pending",
    "branch_id": 2,
    "assigned_to_id": null,
    "sla_breached": true
  }
}
```

> All params optional. `sla_breached: true` returns only messages that breached SLA.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 147,
      "page": 1,
      "per_page": 50,
      "items": [
        {
          "id": 1042,
          "customer_id": 88,
          "customer_name": "Mohammed Al-Rashid",
          "channel": "whatsapp",
          "direction": "inbound",
          "channel_identity_id": 3,
          "content": "مرحبا، أريد الاستفسار عن منتج",
          "media_url": null,
          "sent_at": "2026-03-30T08:45:00",
          "read_at": null,
          "replied_by_agent_at": null,
          "assigned_to_id": null,
          "assigned_to_name": "",
          "owner_id": null,
          "owner_name": "",
          "conversation_id": "conv_wa_88_1711791900",
          "status": "pending",
          "sla_breached": true,
          "waiting_customer_response": false,
          "branch_id": 2
        }
      ]
    }
  }
}
```

---

### 3.6 — Get Conversation Thread

Returns all messages in a conversation in chronological order (oldest first).

```
POST /api/crm/channels/messages/conversation
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "conversation_id": "conv_wa_88_1711791900"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "items": [
        {
          "id": 1042,
          "direction": "inbound",
          "content": "مرحبا، أريد الاستفسار عن منتج",
          "sent_at": "2026-03-30T08:45:00",
          "channel": "whatsapp",
          "customer_name": "Mohammed Al-Rashid",
          "status": "pending",
          "sla_breached": true
          /* ... all message fields ... */
        },
        {
          "id": 1043,
          "direction": "outbound",
          "content": "أهلاً! كيف يمكنني مساعدتك؟",
          "sent_at": "2026-03-30T08:50:00",
          "assigned_to_name": "Ahmed Ali"
          /* ... */
        }
      ]
    }
  }
}
```

---

### 3.7 — Create Message (Inbound / Outbound)

Use this to **inject** a new message into the system (e.g. from a webhook or manual input).

```
POST /api/crm/channels/messages/create
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "customer_id": 88,
    "channel": "whatsapp",
    "content": "مرحبا، أريد طلب جديد",
    "direction": "inbound",
    "conversation_id": "conv_wa_88_1711791900",
    "branch_id": 2,
    "media_url": null
  }
}
```

> For `direction: "outbound"`: sets `replied_by_agent_at`, `owner_id`, `waiting_customer_response: true` automatically.

**Response:** Returns the created message object.

---

### 3.8 — Reply to Message

Send an outbound reply to an inbound message. Automatically:
- Creates a new **outbound** message in the same conversation
- Sets `owner_id` to current agent if not already set
- Sets `replied_by_agent_at` for FRT calculation
- Sets `waiting_customer_response: true` on the original message

```
POST /api/crm/channels/messages/<id>/reply
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "content": "أهلاً! سأساعدك الآن. ما هو المنتج الذي تريده؟",
    "media_url": null
  }
}
```

**Response:** Returns the new outbound message object.

---

### 3.9 — Assign Conversation

Assign a conversation to an agent (or to yourself if `assigned_to_id` is omitted).

```
POST /api/crm/channels/messages/<id>/assign
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "assigned_to_id": 8
  }
}
```

> Omit `assigned_to_id` to assign to the current user.  
> Sets `status: "assigned"` on the message.

---

### 3.10 — Resolve Conversation

Marks the conversation as resolved. All messages in the same `conversation_id` are resolved at once.

```
POST /api/crm/channels/messages/<id>/resolve
```

**Request:** `{ "params": {} }`  
**Response:** `{ "success": true }`

---

### 3.11 — Transfer Conversation

Transfer ownership of a conversation to another agent. All messages in the conversation are updated.

```
POST /api/crm/channels/messages/<id>/transfer
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "new_owner_id": 12
  }
}
```

**Response:** `{ "success": true }`

---

## 4. Calling System API

### 4.1 — List Calls

```
POST /api/crm/calls/list
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "page": 1,
    "per_page": 50,
    "customer_id": null,
    "branch_id": 2,
    "agent_id": 5,
    "date_from": "2026-03-01T00:00:00",
    "date_to": "2026-03-30T23:59:59",
    "outcome": "resolved"
  }
}
```

> All params optional. Dates are ISO 8601 strings.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 312,
      "page": 1,
      "per_page": 50,
      "items": [
        {
          "id": 501,
          "customer_id": 88,
          "customer_name": "Mohammed Al-Rashid",
          "agent_id": 5,
          "agent_name": "Ahmed Ali",
          "branch_id": 2,
          "call_type": "inbound",
          "channel": "phone",
          "caller_number": "+9647701234567",
          "duration_seconds": 245,
          "started_at": "2026-03-30T09:15:00",
          "ended_at": "2026-03-30T09:19:05",
          "outcome": "resolved",
          "notes": "العميل طلب إعادة ترتيب طلب سابق",
          "ai_summary": "Customer requested reorder of previous ADF order",
          "qa_score": 4.5,
          "issues_found": "",
          "balance_at_call": 1500.0,
          "outstanding_at_call": 0.0,
          "credit_limit_at_call": 5000.0,
          "catalogue_sent": true,
          "catalogue_sent_via": "whatsapp",
          "recording_url": "https://storage.example.com/recordings/501.mp3",
          "pos_order_id": 2210,
          "pos_order_name": "S02210",
          "pos_order_total": 320.0,
          "pos_order_state": "done",
          "created_at": "2026-03-30T09:15:00"
        }
      ]
    }
  }
}
```

---

### 4.2 — Get Single Call

```
POST /api/crm/calls/<id>
```

**Request:** `{ "params": {} }`  
**Response:** Single call object (same shape as list item).

---

### 4.3 — Start a Call

Creates a call record when an agent picks up or dials out. **Automatically snapshots** the customer's financial data at the time of the call.

```
POST /api/crm/calls/create
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "customer_id": 88,
    "call_type": "inbound",
    "channel": "phone",
    "caller_number": "+9647701234567",
    "branch_id": 2
  }
}
```

**Fields:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| `customer_id` | int | ✅ | — |
| `call_type` | `inbound` or `outbound` | ❌ | `inbound` |
| `channel` | string | ❌ | `""` |
| `caller_number` | string | ❌ | `""` |
| `branch_id` | int | ❌ | `null` |

**Response:** Returns the created call with `started_at` set to now and financial snapshot populated.

---

### 4.4 — End a Call

```
POST /api/crm/calls/<id>/end
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "duration_seconds": 245,
    "outcome": "resolved",
    "notes": "العميل طلب إعادة الطلب",
    "catalogue_sent": true,
    "catalogue_sent_via": "whatsapp",
    "recording_url": "https://storage.example.com/recordings/501.mp3"
  }
}
```

> All params optional — sets `ended_at` to now automatically.

**Response:** Returns the updated call object.

---

### 4.5 — Update Call

Update any writable field after the call. Used for QA scoring, attaching POS order links, etc.

```
POST /api/crm/calls/<id>/update
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "qa_score": 4.5,
    "issues_found": "Agent was slow to identify product",
    "ai_summary": "Customer requested reorder of ADF00429",
    "pos_order_id": 2210,
    "pos_order_name": "S02210",
    "pos_order_total": 320.0,
    "pos_order_state": "done"
  }
}
```

**All updatable fields:**

| Field | Type | Description |
|-------|------|-------------|
| `notes` | string | Agent's call notes |
| `ai_summary` | string | AI-generated summary |
| `qa_score` | float | QA score (0–5) |
| `issues_found` | string | QA reviewer notes |
| `outcome` | string | resolved / callback / escalated / no_answer |
| `recording_url` | string | Link to audio recording |
| `catalogue_sent` | bool | Was catalogue sent? |
| `catalogue_sent_via` | string | whatsapp / email / telegram |
| `pos_order_id` | int | Linked POS order ID |
| `pos_order_name` | string | POS order name (e.g. S02210) |
| `pos_order_total` | float | Order total in USD |
| `pos_order_state` | string | Order state |

---

### 4.6 — Attach Recording URL

```
POST /api/crm/calls/<id>/attach_recording
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "recording_url": "https://storage.example.com/recordings/501.mp3"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 501, "recording_url": "https://storage.example.com/recordings/501.mp3" }
  }
}
```

---

### 4.7 — Delete Call (Soft Delete)

```
POST /api/crm/calls/<id>/delete
```

**Request:** `{ "params": {} }`  
**Response:** `{ "success": true }`

---

### 4.8 — Call Queue — List

Returns all calls currently waiting in the queue.

```
POST /api/crm/calls/queue/list
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "status": "waiting"
  }
}
```

**`status` values:** `waiting`, `assigned`, `answered`, `missed`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "items": [
        {
          "id": 15,
          "customer_id": 88,
          "customer_name": "Mohammed Al-Rashid",
          "channel": "phone",
          "caller_number": "+9647701234567",
          "queue_position": 1,
          "queued_at": "2026-03-30T09:10:00",
          "status": "waiting"
        }
      ]
    }
  }
}
```

---

### 4.9 — Call Queue — Add

Add an incoming call to the queue.

```
POST /api/crm/calls/queue/add
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "customer_id": 88,
    "channel": "phone",
    "caller_number": "+9647701234567"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": { "id": 15, "queue_position": 3 }
  }
}
```

---

### 4.10 — Call Queue — Assign

Assign the next queued call to the current agent (picks it from the waiting room).

```
POST /api/crm/calls/queue/<id>/assign
```

**Request:** `{ "params": {} }`  
**Response:** `{ "success": true }`

---

### 4.11 — Active Call Context (Screen Pop)

**The most powerful endpoint.** When a call comes in, call this immediately to get full customer context — their profile, recent tickets, and recent POS orders — shown as a "screen pop" to the agent.

```
POST /api/crm/calls/active_context
```

**Request (by phone number — for inbound calls):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "phone_number": "+9647701234567"
  }
}
```

**Request (by call ID — after call is created):**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "call_id": 501
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "customer": {
        "id": 88,
        "name": "Mohammed Al-Rashid",
        "phone": "+9647701234567",
        "email": "mohammed@example.com",
        "tier": "vip",
        "avatar": null,
        "total_orders": 45,
        "total_spent": 12500.0,
        "last_order_date": "2026-03-25",
        "open_tickets": 2,
        "notes": "عميل مميز، يفضل التواصل عبر الواتساب"
      },
      "recent_tickets": [
        { "id": 312, "title": "مشكلة في الشحنة", "status": "in_progress", "created_at": "2026-03-28T10:00:00" },
        { "id": 298, "title": "استفسار عن منتج", "status": "resolved", "created_at": "2026-03-20T09:00:00" }
      ],
      "recent_orders": [
        { "id": 2150, "total": 450.0, "status": "done",  "date": "2026-03-25" },
        { "id": 2090, "total": 280.0, "status": "paid",  "date": "2026-03-18" }
      ]
    }
  }
}
```

**If customer not found:**
```json
{
  "result": {
    "success": true,
    "data": { "customer": null, "recent_tickets": [], "recent_orders": [] }
  }
}
```

> Phone lookup checks `phone_1`, `phone_2`, `phone_3`, and `whatsapp_number` fields simultaneously.

---

## 5. Enumerations Reference

### Channels
```typescript
type Channel = 'whatsapp' | 'instagram' | 'telegram' | 'tiktok' | 'x' | 'snapchat' | 'email' | 'website';
```

### Message Status
```typescript
type MessageStatus = 'pending' | 'assigned' | 'resolved';
```

### Message Direction
```typescript
type MessageDirection = 'inbound' | 'outbound';
```

### Call Type
```typescript
type CallType = 'inbound' | 'outbound';
```

### Call Outcome
```typescript
type CallOutcome = 'resolved' | 'callback' | 'escalated' | 'no_answer';
```

### Catalogue Sent Via
```typescript
type CatalogueSentVia = 'whatsapp' | 'email' | 'telegram';
```

---

## 6. TypeScript Type Definitions

```typescript
// ── Chat ──────────────────────────────────────────────────────────────────

export interface ChannelConfig {
  id:                    number;
  channel:               Channel;
  display_name:          string;
  color_hex:             string;
  icon:                  string;
  branch_id:             number | null;
  branch_name:           string;
  assigned_user_ids:     number[];
  assigned_user_names:   string[];
  is_free_for_all:       boolean;
  is_active:             boolean;
  sla_threshold_seconds: number;   // e.g. 300 = 5 minutes
  work_hours_start:      number;   // float hours, e.g. 8.0 = 08:00
  work_hours_end:        number;
}

export interface OmnichannelMessage {
  id:                       number;
  customer_id:              number | null;
  customer_name:            string;
  channel:                  Channel;
  direction:                MessageDirection;
  channel_identity_id:      number | null;
  content:                  string;
  media_url:                string | null;
  sent_at:                  string;         // ISO 8601
  read_at:                  string | null;
  replied_by_agent_at:      string | null;  // for FRT calculation
  assigned_to_id:           number | null;
  assigned_to_name:         string;
  owner_id:                 number | null;
  owner_name:               string;
  conversation_id:          string | null;
  status:                   MessageStatus;
  sla_breached:             boolean;
  waiting_customer_response: boolean;
  branch_id:                number | null;
}

// ── Calling ────────────────────────────────────────────────────────────────

export interface CrmCall {
  id:                    number;
  customer_id:           number | null;
  customer_name:         string;
  agent_id:              number | null;
  agent_name:            string;
  branch_id:             number | null;
  call_type:             CallType;
  channel:               string;
  caller_number:         string;
  duration_seconds:      number;
  started_at:            string | null;
  ended_at:              string | null;
  outcome:               CallOutcome | null;
  notes:                 string;
  ai_summary:            string;
  qa_score:              number;
  issues_found:          string;
  balance_at_call:       number;       // customer balance snapshot
  outstanding_at_call:   number;
  credit_limit_at_call:  number;
  catalogue_sent:        boolean;
  catalogue_sent_via:    CatalogueSentVia | null;
  recording_url:         string | null;
  pos_order_id:          number | null;
  pos_order_name:        string;
  pos_order_total:       number;       // USD
  pos_order_state:       string;
  created_at:            string | null;
}

export interface CallQueueItem {
  id:             number;
  customer_id:    number | null;
  customer_name:  string;
  channel:        string;
  caller_number:  string;
  queue_position: number;
  queued_at:      string | null;
  status:         string;
}

export interface ActiveCallContext {
  customer: {
    id:              number;
    name:            string;
    phone:           string;
    email:           string;
    tier:            'vip' | 'regular';
    avatar:          string | null;
    total_orders:    number;
    total_spent:     number;
    last_order_date: string | null;
    open_tickets:    number;
    notes:           string;
  } | null;
  recent_tickets: Array<{
    id:         number;
    title:      string;
    status:     string;
    created_at: string;
  }>;
  recent_orders: Array<{
    id:     number;
    total:  number;
    status: string;
    date:   string;
  }>;
}
```

---

## 7. Real-World Usage Flows

### Flow A — Inbound WhatsApp Message (Webhook)

```typescript
// 1. WhatsApp webhook arrives on your server
// 2. POST to Odoo to create the inbound message
const message = await crmPost('/api/crm/channels/messages/create', {
  customer_id: resolvedCustomerId,  // look up by phone first
  channel: 'whatsapp',
  content: webhookPayload.text,
  direction: 'inbound',
  conversation_id: `conv_wa_${customerId}_${Date.now()}`,
  branch_id: 2,
}, token);

// 3. Show in inbox — sla_breached will be set by cron if not replied in time
```

### Flow B — Agent Replies in Chat Window

```typescript
// Agent types a reply in the chat UI
const reply = await crmPost(`/api/crm/channels/messages/${messageId}/reply`, {
  content: 'أهلاً بك! سأساعدك الآن.',
}, token);

// FRT is now recorded (replied_by_agent_at is set)
// waiting_customer_response is true
// Update your local conversation state
```

### Flow C — Inbound Call (Screen Pop)

```typescript
// PBX/telephony system notifies frontend of incoming call
// Immediately fetch customer context
const context = await crmPost('/api/crm/calls/active_context', {
  phone_number: incomingPhoneNumber,
}, token);

// Show context panel to agent
showCallContextPanel(context.data);

// When agent picks up — create the call record
const call = await crmPost('/api/crm/calls/create', {
  customer_id: context.data.customer?.id,
  call_type: 'inbound',
  caller_number: incomingPhoneNumber,
  branch_id: currentBranchId,
}, token);

// Store call.data.id for use in end_call
```

### Flow D — End Call with Notes

```typescript
// Agent finishes the call
const updatedCall = await crmPost(`/api/crm/calls/${callId}/end`, {
  duration_seconds: callDurationSeconds,
  outcome: 'resolved',
  notes: agentNotes,
  catalogue_sent: catalogueSent,
  catalogue_sent_via: 'whatsapp',
}, token);

// If recording was uploaded to storage:
if (recordingUrl) {
  await crmPost(`/api/crm/calls/${callId}/attach_recording`, {
    recording_url: recordingUrl,
  }, token);
}
```

---

## 8. Error Handling Reference

| Error | Cause | Action |
|-------|-------|--------|
| `"Unauthorized"` | No / expired token | Redirect to login |
| `"Customer not found"` | Invalid customer_id | Show validation error |
| `"Call not found"` | Wrong call_id | Show 404 state |
| `"Message not found"` | Wrong message_id | Show 404 state |
| `"Config not found"` | Wrong config_id | Show 404 state |
| `"conversation_id required"` | Missing required param | Validate before submit |

---

*For API issues, check `odoo_local.log` on the server or contact the backend team.*
