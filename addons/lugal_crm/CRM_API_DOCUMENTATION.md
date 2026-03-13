# Lugal CRM — API Documentation

**Version:** 1.0  
**Protocol:** JSON-RPC 2.0 (POST body) unless noted as HTTP  
**Base URL:** `https://<your-odoo-host>`  
**Authentication:** JWT Bearer token (see [Authentication](#authentication))

---

## Table of Contents

1. [Authentication](#authentication)
2. [Common Conventions](#common-conventions)
3. [Role & Permission Levels](#role--permission-levels)
4. [Customers](#customers)
5. [Calls](#calls)
6. [Tickets](#tickets)
7. [Channels & Messages (Omnichannel)](#channels--messages-omnichannel)
8. [Analytics & Reports](#analytics--reports)
9. [Knowledge Base](#knowledge-base)
10. [Branches](#branches)
11. [POS Bridge (Invoice Creation)](#pos-bridge-invoice-creation)
12. [Pricelist & Products](#pricelist--products)
13. [Delivery & Orders](#delivery--orders)
14. [Supply Chain (Containers & Purchase Orders)](#supply-chain-containers--purchase-orders)
15. [Workforce (Shifts & Attendance)](#workforce-shifts--attendance)
16. [Tasks & Follow-ups](#tasks--follow-ups)
17. [Configuration (Tags, Stages, Scripts)](#configuration-tags-stages-scripts)
18. [QA Reviews](#qa-reviews)
19. [File Uploads](#file-uploads)
20. [Error Reference](#error-reference)

---

## Authentication

All API endpoints (except CORS preflight `OPTIONS` requests) require a valid JWT access token.

### How to authenticate

Include the token in the JSON-RPC `params` body — the server reads it from the `Authorization` HTTP header:

```http
POST /api/crm/customers/list
Content-Type: application/json
Authorization: Bearer <access_token>

{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {}
}
```

### Token refresh

When the access token expires, use the refresh token endpoint provided by `lugal_auth`. On `401 Unauthorized`, the frontend should call the refresh endpoint and retry the original request.

### Unauthorized response

```json
{ "success": false, "error": "Unauthorized" }
```

---

## Common Conventions

### Request format

Every endpoint uses **JSON-RPC 2.0 POST** unless explicitly marked `[HTTP]`:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "key": "value"
  }
}
```

### Response format

**Success:**
```json
{
  "success": true,
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

**Paginated response:**
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "total": 250,
    "page": 1,
    "per_page": 20
  }
}
```

### Soft deletes

All delete endpoints set `is_deleted = true, active = false`. Records are **never permanently removed** unless explicitly stated.

### Date/time format

All date-time fields use **ISO 8601**: `"2024-03-15T09:30:00"`. Null dates are returned as `null`.

---

## Role & Permission Levels

Roles are hierarchical. A higher role implies all lower roles.

| Role | XML ID | Implied Access |
|---|---|---|
| `agent` | `group_lugal_crm_agent` | Basic CRM operations |
| `supervisor` | `group_lugal_crm_supervisor` | Agent + team management |
| `manager` | `group_lugal_crm_manager` | Supervisor + config management |
| `general_manager` | `group_lugal_crm_general_manager` | Full access |
| `qa_auditor` | `group_lugal_crm_qa_auditor` | QA review (independent) |
| `qa_supervisor` | `group_lugal_crm_qa_supervisor` | QA Auditor + QA management |

> **Note:** The permission required for each endpoint is listed in the endpoint table as `[Any]`, `[Supervisor+]`, `[Manager+]`, etc.

---

## Customers

### Customer Object

```json
{
  "id": 42,
  "name": "Ahmad Al-Rashidi",
  "name_ar": "أحمد الراشدي",
  "partner_id": 105,
  "phone_1": "+9647701234567",
  "phone_2": "",
  "phone_3": "",
  "email": "ahmad@example.com",
  "address": "Baghdad, Al-Mansour",
  "city": "Baghdad",
  "country_id": 103,
  "country_name": "Iraq",

  "stage_id": 3,
  "stage_name": "Active",
  "stage_type": "active",
  "tag_ids": [1, 4],
  "tag_names": ["Wholesale", "VIP"],
  "vip_status": true,
  "is_enterprise": false,

  "branch_ids": [1, 2],
  "account_manager_id": 7,
  "account_manager_name": "Sara Khalid",
  "referral_source": "instagram",

  "shop_name": "Al-Rashidi Perfumes",
  "shop_location": "Al-Mansour Market, Shop 12",

  "loyalty_points": 250,
  "preferred_contact_time": "morning",
  "preferred_contact_channel": "whatsapp",

  "credit_limit": 5000.0,
  "lifetime_value": 12000.0,
  "credit_debt": 800.0,

  "member_since": "2023-01-15",
  "last_call_date": "2024-03-10T14:22:00",
  "last_activity_date": "2024-03-10T14:22:00",
  "is_deleted": false,
  "active": true,
  "create_date": "2023-01-15T08:00:00",

  "social_handles": {
    "instagram": "@ahmad_perfume",
    "whatsapp": "+9647701234567",
    "tiktok": "",
    "snapchat": "",
    "twitter": "",
    "telegram": "@ahmadcrm",
    "pinterest": "",
    "youtube": ""
  },
  "channel_identities": [
    {
      "id": 10,
      "channel": "whatsapp",
      "handle": "+9647701234567",
      "is_active": true
    }
  ],
  "shop_images": ["https://host/web/content/123?access_token=abc"],
  "documents": [
    {
      "type": "national_id",
      "url": "https://host/web/content/124?access_token=xyz",
      "filename": "national_id.pdf"
    }
  ]
}
```

---

### `POST /api/crm/customers/list` `[Any]`

Paginated list of customers with optional filters.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `stage_id` | integer | No | Filter by stage |
| `branch_id` | integer | No | Filter by branch |
| `vip_only` | boolean | No | Return only VIP customers |
| `search` | string | No | Search by name, phone, or email |
| `page` | integer | No | Page number (default: `1`) |
| `per_page` | integer | No | Items per page (default: `20`) |

**Response:** Paginated list of [Customer Objects](#customer-object).

---

### `POST /api/crm/customers/<id>` `[Any]`

Get a single customer by CRM `id` or `partner_id`.

**Response:** Single [Customer Object](#customer-object).

---

### `POST /api/crm/customers/create` `[Any]`

Create a new customer.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Yes** | Customer full name (EN) |
| `name_ar` | string | No | Customer name in Arabic |
| `phone_1` | string | No | Primary phone |
| `phone_2` | string | No | Secondary phone |
| `phone_3` | string | No | Third phone |
| `email` | string | No | Email address |
| `address` | string | No | Full address |
| `city` | string | No | City |
| `country_id` | integer | No | Odoo country ID |
| `stage_id` | integer | No | Pipeline stage ID |
| `tag_ids` | integer[] | No | Tag IDs (M2M) |
| `branch_ids` | integer[] | No | Branch IDs (M2M) |
| `vip_status` | boolean | No | Mark as VIP |
| `is_enterprise` | boolean | No | Enterprise/B2B flag |
| `account_manager_id` | integer | No | User ID of account manager |
| `referral_source` | string | No | How customer was referred |
| `shop_name` | string | No | Shop or business name |
| `shop_location` | string | No | Physical shop location |
| `credit_limit` | float | No | Credit limit (USD) |
| `instagram_handle` | string | No | Instagram handle |
| `whatsapp_number` | string | No | WhatsApp number |
| `tiktok_handle` | string | No | TikTok handle |
| `snapchat_handle` | string | No | Snapchat handle |
| `twitter_handle` | string | No | X (Twitter) handle |
| `telegram_handle` | string | No | Telegram handle |

**Response:** `{ "success": true, "data": { "id": 42 } }`

---

### `POST /api/crm/customers/<id>/update` `[Any]`

Partial update of a customer. All fields are optional.

**Request params:** Same fields as `create`. Only provided fields are updated.

**Response:** `{ "success": true, "data": { "id": 42 } }`

---

### `POST /api/crm/customers/<id>/delete` `[Any]`

Soft-delete a customer (sets `is_deleted=true, active=false`). Also archives the linked `res.partner`.

**Response:** `{ "success": true }`

---

### `POST /api/crm/customers/<id>/kanban_move` `[Any]`

Move a customer to a different pipeline stage.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `stage_id` | integer | **Yes** | Target stage ID |

**Response:** `{ "success": true }`

---

### `POST /api/crm/customers/search` `[Any]`

Quick search by name, email, or phone. Minimum 2 characters.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `query` | string | **Yes** | Search string (min 2 chars) |

**Response:** `{ "success": true, "data": { "items": [ ... ] } }`

---

### `POST /api/crm/customers/<id>/activity` `[Any]`

360° customer timeline — merged and sorted list of calls, interactions, messages, and tickets.

**Response:**
```json
{
  "success": true,
  "data": {
    "timeline": [
      {
        "type": "call",
        "date": "2024-03-10T14:22:00",
        "summary": "Follow-up call, outcome: interested",
        "id": 12
      },
      {
        "type": "ticket",
        "date": "2024-03-08T10:00:00",
        "summary": "Return request — resolved",
        "id": 5
      }
    ]
  }
}
```

---

### `POST /api/crm/customers/<id>/calls` `[Any]`

Paginated call history for a customer.

**Request params:** `page`, `per_page`

**Response:** Paginated list of [Call Objects](#call-object).

---

### `POST /api/crm/customers/<id>/tickets` `[Any]`

Paginated ticket history for a customer.

**Request params:** `page`, `per_page`

**Response:** Paginated list of [Ticket Objects](#ticket-object).

---

### `POST /api/crm/customers/<id>/note/add` `[Any]`

Add a quick note to the customer timeline.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `note` | string | **Yes** | Note content |

**Response:** `{ "success": true, "data": { "id": 55 } }`

---

### `POST /api/crm/customers/<id>/interactions` `[Any]`

Paginated interaction log for a customer. Filterable by type.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `interaction_type` | string | No | `note`, `call`, `ticket`, `message` |
| `page` | integer | No | Default: `1` |
| `per_page` | integer | No | Default: `20` |

---

### `POST /api/crm/interactions/create` `[Any]`

Create a standalone interaction record.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `interaction_type` | string | **Yes** | Type of interaction |
| `content` | string | No | Interaction notes/body |
| `branch_id` | integer | No | Branch associated |

---

### `POST /api/crm/customers/<id>/channel_identity/add` `[Any]`

Add a new social handle / channel identity to a customer.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `channel` | string | **Yes** | `whatsapp`, `instagram`, `telegram`, `tiktok`, `snapchat`, `x`, `pinterest`, `youtube` |
| `handle` | string | **Yes** | The handle value (username or phone) |

---

### `POST /api/crm/customers/<id>/channel_identity/<ci_id>/update` `[Any]`

Update a channel identity entry.

**Request params:** `channel`, `handle` (both optional)

---

### `POST /api/crm/customers/<id>/channel_identity/<ci_id>/delete` `[Any]`

Soft-delete a channel identity entry.

---

### `POST /api/crm/customers/setup_stages` `[Any]`

Create the 5 default pipeline stages if none exist: `Lead → Interested → Active → VIP → Dormant`.

**Response:** `{ "success": true, "data": { "stages_created": 3 } }`

---

### `POST /api/crm/customers/sync_from_odoo` `[Any]`

One-time import: creates CRM records for all `res.partner` records with `customer_rank > 0` that do not yet have a CRM profile.

**Response:** `{ "success": true, "data": { "synced": 142 } }`

---

## Calls

### Call Object

```json
{
  "id": 12,
  "customer_id": 42,
  "customer_name": "Ahmad Al-Rashidi",
  "branch_id": 1,
  "branch_name": "Baghdad Branch",
  "agent_id": 7,
  "agent_name": "Sara Khalid",
  "started_at": "2024-03-10T14:00:00",
  "ended_at": "2024-03-10T14:22:00",
  "duration_seconds": 1320,
  "outcome": "interested",
  "notes": "Customer is interested in Amouage line",
  "recording_url": "https://cdn.example.com/recordings/call-12.mp3",
  "qa_score": 88,
  "pos_order_snapshot": {
    "order_id": 55,
    "total": 250.0
  },
  "credit_debt_snapshot": 800.0,
  "credit_limit_snapshot": 5000.0,
  "is_deleted": false
}
```

**Outcome values:** `interested`, `not_interested`, `callback`, `no_answer`, `completed`, `transferred`

---

### `POST /api/crm/calls/list` `[Any]`

List calls with optional filters.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `customer_id` | integer | Filter by customer |
| `branch_id` | integer | Filter by branch |
| `agent_id` | integer | Filter by agent user |
| `date_from` | string | ISO datetime lower bound |
| `date_to` | string | ISO datetime upper bound |
| `outcome` | string | Filter by outcome value |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/calls/<id>` `[Any]`

Get a single call record.

---

### `POST /api/crm/calls/create` `[Any]`

Start a new call. Automatically snapshots `credit_debt` and `credit_limit` from the customer.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `branch_id` | integer | No | Branch where call originates |

**Response:** `{ "success": true, "data": { "id": 12 } }`

---

### `POST /api/crm/calls/<id>/end` `[Any]`

End an active call.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `outcome` | string | **Yes** | Call outcome value |
| `notes` | string | No | Call summary notes |
| `recording_url` | string | No | URL of call recording |

---

### `POST /api/crm/calls/<id>/update` `[Any]`

Update writable fields on an existing call.

**Request params:** `notes`, `qa_score`, `outcome`, `pos_order_snapshot` (all optional)

---

### `POST /api/crm/calls/<id>/delete` `[Any]`

Soft-delete a call.

---

### `POST /api/crm/calls/<id>/attach_recording` `[Any]`

Attach or update a recording URL.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `recording_url` | string | **Yes** | Public URL to the recording file |

---

### `POST /api/crm/calls/queue/list` `[Any]`

List calls in the call queue. Optionally filter by `status`.

**Request params:** `status` (optional): `waiting`, `assigned`, `completed`

---

### `POST /api/crm/calls/queue/add` `[Any]`

Add an incoming call to the queue (auto-increments position).

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `branch_id` | integer | No | Branch |
| `priority` | integer | No | Queue priority (higher = first) |

---

### `POST /api/crm/calls/queue/<id>/assign` `[Any]`

Assign a queued call to the current authenticated user.

---

## Tickets

### Ticket Object

```json
{
  "id": 5,
  "title": "Wrong product delivered",
  "description": "Customer received Amouage instead of Creed",
  "customer_id": 42,
  "customer_name": "Ahmad Al-Rashidi",
  "branch_id": 1,
  "branch_name": "Baghdad Branch",
  "status": "in_progress",
  "priority": "high",
  "assigned_to_id": 7,
  "assigned_to_name": "Sara Khalid",
  "escalated_to_id": null,
  "first_response_at": "2024-03-08T10:15:00",
  "resolved_at": null,
  "is_deleted": false,
  "create_date": "2024-03-08T09:58:00"
}
```

**Status values:** `open`, `in_progress`, `resolved`, `closed`  
**Priority values:** `low`, `normal`, `high`, `urgent`

---

### `POST /api/crm/tickets/list` `[Any]`

List tickets with optional filters.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `customer_id` | integer | Filter by customer |
| `branch_id` | integer | Filter by branch |
| `status` | string | Filter by status |
| `priority` | string | Filter by priority |
| `assigned_to_id` | integer | Filter by assigned user |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/tickets/<id>` `[Any]`

Get a single ticket. Pass `include_notes: true` to embed internal notes.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `include_notes` | boolean | Include internal notes (default: `false`) |

---

### `POST /api/crm/tickets/search` `[Any]`

Search tickets by title or description.

**Request params:** `query` (string, required)

---

### `POST /api/crm/tickets/create` `[Any]`

Create a new support ticket.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `title` | string | **Yes** | Ticket title |
| `description` | string | No | Detailed description |
| `priority` | string | No | Default: `normal` |
| `branch_id` | integer | No | Associated branch |
| `assigned_to_id` | integer | No | Assign immediately |

---

### `POST /api/crm/tickets/<id>/update` `[Any]`

Update ticket fields. All fields are optional.

**Request params:** `title`, `description`, `priority`, `branch_id`, `assigned_to_id`

---

### `POST /api/crm/tickets/<id>/update_status` `[Any]`

Update ticket status. Automatically sets `resolved_at` when status becomes `resolved`.

**Request params:** `status` (string, required)

---

### `POST /api/crm/tickets/<id>/assign` `[Any]`

Assign ticket to a user. Sets `first_response_at` if this is the first assignment.

**Request params:** `user_id` (integer, required)

---

### `POST /api/crm/tickets/<id>/escalate` `[Any]`

Escalate ticket to another user (sets both `escalated_to_id` and `assigned_to_id`).

**Request params:** `user_id` (integer, required)

---

### `POST /api/crm/tickets/<id>/delete` `[Any]`

Soft-delete a ticket.

---

### `POST /api/crm/tickets/<id>/note/add` `[Any]`

Add an internal note to a ticket.

**Request params:** `note` (string, required)

---

### `POST /api/crm/tickets/<id>/notes` `[Any]`

Get all internal notes for a ticket.

---

## Channels & Messages (Omnichannel)

### Channel Config Object

```json
{
  "id": 3,
  "channel_type": "whatsapp",
  "branch_id": 1,
  "branch_name": "Baghdad Branch",
  "sla_threshold_hours": 2,
  "work_hours_start": "09:00",
  "work_hours_end": "18:00",
  "assigned_user_ids": [7, 9],
  "is_active": true
}
```

**Channel type values:** `whatsapp`, `instagram`, `telegram`, `facebook`, `tiktok`, `email`, `phone`

---

### Message Object

```json
{
  "id": 88,
  "conversation_id": "wa_+9647701234567",
  "channel": "whatsapp",
  "branch_id": 1,
  "direction": "inbound",
  "body": "Hello, I need help with my order",
  "sent_at": "2024-03-10T11:00:00",
  "status": "open",
  "owner_id": 7,
  "owner_name": "Sara Khalid",
  "customer_id": 42,
  "customer_name": "Ahmad Al-Rashidi",
  "first_response_time_seconds": 180,
  "sla_breached": false,
  "waiting_customer_response": false,
  "replied_by_agent_at": "2024-03-10T11:03:00"
}
```

---

### `POST /api/crm/channels/config_list` `[Any]`

List channel configurations, optionally filtered by `branch_id`.

---

### `POST /api/crm/channels/config/create` `[Supervisor+]`

Create a channel configuration.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `channel_type` | string | **Yes** | Channel type |
| `branch_id` | integer | **Yes** | Branch |
| `sla_threshold_hours` | float | No | SLA response threshold (hours) |
| `work_hours_start` | string | No | Work hours start `HH:MM` |
| `work_hours_end` | string | No | Work hours end `HH:MM` |
| `assigned_user_ids` | integer[] | No | Users assigned to this channel |

---

### `POST /api/crm/channels/config/<id>/update` `[Supervisor+]`

Update a channel config. `assigned_user_ids` replaces the full M2M list.

---

### `POST /api/crm/channels/config/<id>/delete` `[Supervisor+]`

Soft-delete a channel config.

---

### `POST /api/crm/channels/messages/list` `[Any]`

List omnichannel messages with filters.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `channel` | string | Filter by channel type |
| `status` | string | `open`, `resolved` |
| `branch_id` | integer | Filter by branch |
| `sla_breached` | boolean | Only SLA-breached messages |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/channels/messages/conversation` `[Any]`

Get the full conversation thread by `conversation_id`.

**Request params:** `conversation_id` (string, required)

---

### `POST /api/crm/channels/messages/create` `[Any]`

Create an inbound or outbound message. Setting `direction: "outbound"` automatically records first-response-time metadata.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `conversation_id` | string | **Yes** | Unique conversation identifier |
| `channel` | string | **Yes** | Channel type |
| `direction` | string | **Yes** | `inbound` or `outbound` |
| `body` | string | **Yes** | Message body |
| `branch_id` | integer | No | Branch |
| `customer_id` | integer | No | Link to a CRM customer |

---

### `POST /api/crm/channels/messages/<id>/assign` `[Any]`

Assign a conversation to a user.

**Request params:** `user_id` (integer, required)

---

### `POST /api/crm/channels/messages/<id>/reply` `[Any]`

Send an outbound reply. Sets `owner_id`, records `replied_by_agent_at`, and toggles `waiting_customer_response`.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `body` | string | **Yes** | Reply message body |

---

### `POST /api/crm/channels/messages/<id>/resolve` `[Any]`

Resolve a message and all others in the same `conversation_id`.

---

### `POST /api/crm/channels/messages/<id>/transfer` `[Any]`

Transfer conversation ownership to another agent.

**Request params:** `user_id` (integer, required)

---

## Analytics & Reports

### `POST /api/crm/analytics/dashboard_stats` `[Any]`

Aggregate stats for the main dashboard.

**Request params:** `branch_id` (optional), `date_from` (optional), `date_to` (optional)

**Response:**
```json
{
  "success": true,
  "data": {
    "customers": {
      "total": 1240,
      "vip": 85,
      "new_today": 3
    },
    "tickets": {
      "open": 14,
      "resolved": 302,
      "high_priority": 4
    },
    "calls": {
      "total": 58,
      "missed": 7
    },
    "messages": {
      "inbound": 120,
      "pending": 18,
      "sla_breached": 2
    },
    "tasks": {
      "overdue": 5
    }
  }
}
```

---

### `POST /api/crm/analytics/channel_report` `[Any]`

Message volume per channel with SLA metrics and call totals.

**Request params:** `branch_id` (optional), `date_from`, `date_to`

**Response:**
```json
{
  "success": true,
  "data": {
    "channels": [
      {
        "channel": "whatsapp",
        "total_messages": 80,
        "resolved": 65,
        "sla_breached": 2
      }
    ],
    "calls": {
      "total": 58,
      "missed": 7
    }
  }
}
```

---

### `POST /api/crm/analytics/branch_report` `[Any]`

Single SQL-aggregated report: customers, open tickets, calls, and messages per branch.

**Request params:** `date_from` (optional), `date_to` (optional)

---

### `POST /api/crm/analytics/employee_kpi` `[Any]`

KPI metrics for a single employee.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `user_id` | integer | **Yes** | Employee user ID |
| `live` | boolean | No | `true` = live computation, `false` = last snapshot (faster) |
| `date_from` | string | No | ISO datetime |
| `date_to` | string | No | ISO datetime |

---

### `POST /api/crm/analytics/all_employees_kpi` `[Supervisor+]`

Latest KPI snapshot for all employees.

---

### `POST /api/crm/analytics/supervisor_dashboard` `[Supervisor+]`

Real-time supervisor panel:
- Open conversations per agent
- Unassigned messages count
- Overdue tasks
- High-priority open tickets
- Dormant VIP customers

---

### `POST /api/crm/analytics/ai_vs_human` `[Any]`

AI vs human reply ratio for inbound messages.

**Request params:** `branch_id` (optional), `date_from`, `date_to`

---

### `POST /api/crm/analytics/export_kpi` `[Manager+]` `[HTTP]`

CSV download of KPI snapshots for all employees.

**Request:** Standard HTTP GET/POST (not JSON-RPC). Requires `Authorization: Bearer <token>` header.

**Response:** `Content-Type: text/csv` attachment.

---

### `POST /api/crm/analytics/audit_log` `[Any]`

Paginated audit log.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `action` | string | Filter by action type |
| `user_id` | integer | Filter by user |
| `customer_id` | integer | Filter by customer |
| `branch_id` | integer | Filter by branch |
| `date_from` | string | ISO datetime lower bound |
| `date_to` | string | ISO datetime upper bound |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `50` |

---

## Knowledge Base

### Article Object

```json
{
  "id": 7,
  "title_en": "How to process a return",
  "title_ar": "كيفية معالجة الإرجاع",
  "content": "Step 1: ...",
  "category": "returns",
  "branch_id": 1,
  "is_published": true,
  "published_at": "2024-01-10T08:00:00",
  "is_deleted": false
}
```

---

### `POST /api/crm/kb/articles/list` `[Any]`

List knowledge base articles.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `category` | string | Filter by article category |
| `branch_id` | integer | Filter by branch |
| `published_only` | boolean | Only published articles (default: `true`) |

---

### `POST /api/crm/kb/articles/search` `[Any]`

Full-text search on article title (AR/EN) and content body.

**Request params:** `query` (string, required)

---

### `POST /api/crm/kb/articles/<id>` `[Any]`

Get a single article.

---

### `POST /api/crm/kb/articles/create` `[Supervisor+]`

Create a new article.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title_en` | string | **Yes** | Title in English |
| `title_ar` | string | No | Title in Arabic |
| `content` | string | No | Article body (HTML or plain text) |
| `category` | string | No | Category key |
| `branch_id` | integer | No | Scope to a branch |
| `is_published` | boolean | No | Publish immediately |

---

### `POST /api/crm/kb/articles/<id>/update` `[Supervisor+]`

Update an article. Automatically sets `published_at` on first publish.

---

### `POST /api/crm/kb/articles/<id>/delete` `[Supervisor+]`

Soft-delete an article.

---

### `POST /api/crm/kb/notifications/list` `[Any]`

List pushed notifications, optionally filtered by `branch_id`.

---

### `POST /api/crm/kb/notifications/push` `[Supervisor+]`

Create and push a notification to one or more branches.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | **Yes** | Notification title |
| `body` | string | **Yes** | Notification body |
| `branch_ids` | integer[] | No | Target branches (empty = all) |

---

## Branches

### Branch Object

```json
{
  "id": 1,
  "name": "Baghdad Branch",
  "code": "BGD",
  "address": "Al-Mansour, Baghdad",
  "phone": "+9641234567",
  "is_active": true,
  "customer_count": 420
}
```

---

### `POST /api/crm/branches/list` `[Any]`

List all active branches.

---

### `POST /api/crm/branches/<id>` `[Any]`

Get a single branch.

---

### `POST /api/crm/branches/create` `[Manager+]`

Create a branch.

**Request params:** `name` (required), `code`, `address`, `phone`

---

### `POST /api/crm/branches/<id>/update` `[Supervisor+]`

Update a branch.

---

### `POST /api/crm/branches/<id>/user_assign` `[Manager+]`

Set the list of users authorized for a branch (replaces current list).

**Request params:** `user_ids` (integer[], required)

---

### `POST /api/crm/branches/<id>/delete` `[Manager+]`

Soft-delete a branch.

---

## POS Bridge (Invoice Creation)

Used to load context data (pricelists, warehouses, exchange rate) before opening the order form in a CRM call dialog.

> **Dependency:** Requires `pos_perfume_custom` addon to be installed.

---

### `POST /api/crm/pos/invoice_context` `[Any]`

Returns setup data to pre-fill the invoice form for a CRM call.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `call_id` | integer | CRM call ID (optional) |
| `customer_id` | integer | CRM customer ID (optional) |

**Response:**
```json
{
  "success": true,
  "data": {
    "pricelists": [
      { "id": 1, "name": "USD Pricelist", "currency_id": 2 }
    ],
    "default_pricelist_id": 1,
    "warehouses": [
      { "id": 1, "name": "Main Warehouse", "code": "WH" }
    ],
    "invoice_types": [
      { "key": "1", "label": "زبون محل" },
      { "key": "2", "label": "شركات توصيل" }
    ],
    "exchange_rate": 1470.0,
    "currency": "USD",
    "secondary_currency": "IQD",
    "partner_id": 105,
    "last_order": {}
  }
}
```

---

### `POST /api/crm/pos/products` `[Any]`

Search for products by name, code, or foreign name.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `search` | string | No | Search term |
| `pricelist_id` | integer | No | Pricelist for price calculation |
| `page` | integer | No | Default: `1` |
| `per_page` | integer | No | Default: `20` |

**Response includes:** `id`, `name`, `default_code`, `list_price`, `qty_available`

---

### `POST /api/crm/pos/product_detail` `[Any]`

Get full product detail: UoMs, per-warehouse stock, and pricelist prices.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | integer | **Yes** | `product.product` ID |
| `pricelist_id` | integer | No | Pricelist ID for pricing |

---

### `POST /api/crm/pos/uom_price` `[Any]`

Get the price for a specific product/pricelist/UoM combination.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | integer | **Yes** | Product ID |
| `pricelist_id` | integer | **Yes** | Pricelist ID |
| `uom_id` | integer | **Yes** | Unit of Measure ID |

---

### `POST /api/crm/pos/orders/<id>` `[Any]`

Get full POS order details (legacy CRM bridge endpoint).

---

### `POST /api/crm/pos/customer_orders` `[Any]`

Order history for a partner (legacy CRM bridge endpoint).

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `partner_id` | integer | **Yes** | Odoo `res.partner` ID |
| `page` | integer | No | Default: `1` |
| `per_page` | integer | No | Default: `10` |

---

## Orders API (Full CRUD + State Transitions)

The **Orders API** (`/api/pos_perfume/v1/...`) is the primary endpoint set for creating and managing POS orders end-to-end.  
It supports the full order lifecycle: **Draft → Quotation → Sale Order**, with line management and state transitions at every step.

> **Base URL:** `http://<host>:8070`  
> **Auth:** Session cookie (after `POST /web/session/authenticate`) **or** `Authorization: Bearer <api_key>` header.

---

### Order Object

Every order endpoint returns the same order object:

```json
{
  "id": 109,
  "name": "POS/2026/0109",
  "date": "2026-03-09T10:30:00",
  "state": "draft",
  "user_id": { "id": 3, "name": "Ahmad" },
  "partner_id": {
    "id": 54,
    "name": "Al-Rashid Trading",
    "phone": "+964 770 000 0000",
    "mobile": "",
    "email": "contact@alrashid.com"
  },
  "pricelist_id": { "id": 3, "name": "USD Pricelist" },
  "currency_id": { "id": 2, "name": "USD" },
  "exchange_rate": 1480.0,
  "invoice_type": "1",
  "note": "Deliver before noon",
  "amount_subtotal": 165.0,
  "amount_discount": 16.5,
  "amount_tax": 0.0,
  "amount_total": 148.5,
  "amount_total_iqd": 219780.0,
  "sale_order_id": { "id": 70, "name": "S00070", "state": "draft" },
  "sap_doc_num": "",
  "sap_doc_entry": 0,
  "sap_synced": false,
  "sap_error_message": "",
  "sap_last_sync_date": null,
  "order_lines": [
    {
      "id": 122,
      "sequence": 10,
      "product_id": {
        "id": 6,
        "name": "Rose Oud 100ml",
        "default_code": "ADF00006",
        "foreign_name": "Rose Oud"
      },
      "product_uom_id": { "id": 30, "name": "قطعه" },
      "warehouse_id": { "id": 1, "name": "Main Warehouse", "code": "WH" },
      "location_id": { "id": 12, "name": "WH/Stock" },
      "quantity": 2.0,
      "unit_price": 55.0,
      "discount_percent": 10.0,
      "price_after_discount": 49.5,
      "line_subtotal": 110.0,
      "discount_amount": 11.0,
      "line_total": 99.0,
      "available_qty": 50.0,
      "custom_product_name": ""
    }
  ]
}
```

**Order states:**

| State | Meaning |
|---|---|
| `draft` | New order, editable, not sent to anyone |
| `quotation` | Sent as quotation to customer |
| `sale` | Confirmed sale order (linked to `sale.order`) |
| `done` | Fully delivered/completed — **read-only** |
| `cancel` | Cancelled — **read-only** |

---

### Order Line Object

| Field | Type | Description |
|---|---|---|
| `id` | integer | Line ID |
| `sequence` | integer | Display order |
| `product_id` | object | `{ id, name, default_code, foreign_name }` |
| `product_uom_id` | object | `{ id, name }` — Unit of measure |
| `warehouse_id` | object | `{ id, name, code }` |
| `location_id` | object | `{ id, name }` — Stock location inside warehouse |
| `quantity` | float | Ordered quantity |
| `unit_price` | float | Price per unit (in pricelist currency) |
| `discount_percent` | float | Discount `%` |
| `price_after_discount` | float | `unit_price × (1 - discount/100)` |
| `line_subtotal` | float | `quantity × unit_price` (before discount) |
| `discount_amount` | float | Total discount amount |
| `line_total` | float | `quantity × price_after_discount` |
| `available_qty` | float | Current stock available in the warehouse |
| `custom_product_name` | string | Override label printed on invoice |

---

### `GET /api/pos_perfume/v1/orders` — List Orders

**Query parameters:**

| Param | Type | Description |
|---|---|---|
| `query` | string | Search by order name |
| `state` | string | `draft` \| `quotation` \| `sale` \| `done` \| `cancel` |
| `partner_id` | integer | Filter by customer ID |
| `user_id` | integer | Filter by salesperson ID |
| `date_from` | string | `YYYY-MM-DD` |
| `date_to` | string | `YYYY-MM-DD` |
| `sap_synced` | string | `true` \| `false` |
| `limit` | integer | Default: `50` |
| `offset` | integer | Default: `0` |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 75,
    "offset": 0,
    "limit": 50,
    "items": [
      {
        "id": 109,
        "name": "POS/2026/0109",
        "date": "2026-03-09T10:30:00",
        "state": "quotation",
        "partner_id": 54,
        "partner_name": "Al-Rashid Trading",
        "user_id": 3,
        "user_name": "Ahmad",
        "invoice_type": "1",
        "amount_total": 148.5,
        "amount_total_iqd": 219780.0,
        "sap_synced": false,
        "sap_doc_num": "",
        "note": "",
        "lines_count": 2
      }
    ]
  }
}
```

---

### `POST /api/pos_perfume/v1/orders` — Create Order

Creates a new order in **`draft`** state.  
You can include lines at creation time or add them later via the lines endpoint.

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `partner_id` | integer | **Yes** | Odoo `res.partner` ID |
| `pricelist_id` | integer | No | Pricelist ID (uses system default if omitted) |
| `invoice_type` | string | No | `"1"` – `"8"` |
| `note` | string | No | Order notes |
| `exchange_rate` | float | No | Override IQD exchange rate |
| `user_id` | integer | No | Salesperson ID |
| `order_lines` | object[] | No | Lines to create immediately (same format as line builder below) |

**Order line object (inside `order_lines`):**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | integer | **Yes** | `product.product` ID |
| `warehouse_id` | integer | **Yes** | Warehouse ID |
| `quantity` | float | No | Default: `1.0` |
| `unit_price` | float | No | Defaults to product list price |
| `product_uom_id` | integer | No | UoM ID — defaults to product sales UoM |
| `discount_percent` | float | No | Default: `0.0` |
| `custom_product_name` | string | No | Override product name on printed invoice |
| `sequence` | integer | No | Default: `10` |

**Example request:**
```json
{
  "partner_id": 54,
  "pricelist_id": 3,
  "invoice_type": "1",
  "note": "Urgent delivery",
  "order_lines": [
    {
      "product_id": 6,
      "warehouse_id": 1,
      "quantity": 2.0,
      "unit_price": 55.0,
      "discount_percent": 10.0
    }
  ]
}
```

**Response:** Full [Order Object](#order-object) with `state: "draft"`.

---

### `GET /api/pos_perfume/v1/orders/<id>` — Get Order

Returns the full order object including all lines.

**Response:** Full [Order Object](#order-object).

---

### `PUT /api/pos_perfume/v1/orders/<id>` — Update Order / Save Draft

Update order header fields and/or replace all lines.  
**Only allowed on `draft` or `quotation` orders.**

> This is also the **auto-save** endpoint. Pass `order_lines` to atomically replace all existing lines with the new set (useful for an auto-save feature that sends the full cart state on each change).

**Request body (all fields optional):**

| Field | Type | Description |
|---|---|---|
| `partner_id` | integer | Change customer |
| `pricelist_id` | integer | Change pricelist |
| `user_id` | integer | Change salesperson |
| `invoice_type` | string | `"1"` – `"8"` |
| `note` | string | Order notes |
| `exchange_rate` | float | IQD exchange rate override |
| `order_lines` | object[] | **Replaces ALL existing lines** when provided |

> If `order_lines` is **not** sent, existing lines are untouched (header-only update).  
> If `order_lines` is sent (even as `[]`), **all existing lines are deleted** and replaced with the new list.

**Example — header only:**
```json
{ "note": "Call again tomorrow", "invoice_type": "2" }
```

**Example — full save (header + lines):**
```json
{
  "note": "Auto-saved",
  "invoice_type": "1",
  "order_lines": [
    { "product_id": 6,  "warehouse_id": 1, "quantity": 2.0, "unit_price": 55.0 },
    { "product_id": 12, "warehouse_id": 1, "quantity": 1.0, "unit_price": 30.0 }
  ]
}
```

**Response:** Full [Order Object](#order-object) with updated data.

---

### `DELETE /api/pos_perfume/v1/orders/<id>` — Cancel Order

Cancels the order (sets state to `cancel`).  
Cannot cancel a `done` order.

**Response:**
```json
{ "success": true, "message": "Order cancelled", "data": { "id": 109, "state": "cancel" } }
```

---

### `POST /api/pos_perfume/v1/orders/<id>/lines` — Add Line

Add a single line to an existing order.  
**Not allowed on `done` or `cancel` orders.**

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | integer | **Yes** | `product.product` ID |
| `warehouse_id` | integer | **Yes** | Warehouse ID |
| `quantity` | float | No | Default: `1.0` |
| `unit_price` | float | No | Defaults to product list price |
| `product_uom_id` | integer | No | UoM ID |
| `discount_percent` | float | No | Default: `0.0` |
| `custom_product_name` | string | No | |
| `sequence` | integer | No | Default: `10` |

**Response:** The new [Order Line Object](#order-line-object).

---

### `PUT /api/pos_perfume/v1/orders/<id>/lines/<line_id>` — Update Line

Update a specific order line.  
**Not allowed on `done` or `cancel` orders.**

**Request body (all optional):**

| Field | Type | Description |
|---|---|---|
| `product_id` | integer | Change product |
| `product_uom_id` | integer | Change UoM |
| `warehouse_id` | integer | Change warehouse |
| `quantity` | float | New quantity |
| `unit_price` | float | New unit price |
| `discount_percent` | float | New discount % |
| `custom_product_name` | string | Override label |
| `sequence` | integer | Display order |

**Response:** Updated [Order Line Object](#order-line-object).

---

### `DELETE /api/pos_perfume/v1/orders/<id>/lines/<line_id>` — Delete Line

Permanently removes a line from the order.  
**Not allowed on `done` or `cancel` orders.**

**Response:**
```json
{ "success": true, "message": "Line deleted", "data": { "deleted": true, "line_id": 122 } }
```

---

### `POST /api/pos_perfume/v1/orders/<id>/confirm` — Confirm Order (→ Sale)

Confirms the order and creates a linked **Odoo `sale.order`**.  
**Source state must be `draft` or `quotation`.**

After confirmation:
- A `sale.order` is created and linked (`sale_order_id` is populated).
- The POS order state becomes `quotation` (pending SAP sync by the frontend) or `sale` once SAP is synced.

**Request body:** empty `{}`

**Response:** Full [Order Object](#order-object).

```json
{
  "success": true,
  "data": {
    "id": 109,
    "state": "quotation",
    "sale_order_id": { "id": 70, "name": "S00070", "state": "draft" }
  }
}
```

---

### `POST /api/pos_perfume/v1/orders/<id>/quotation` — Send as Quotation

Moves a `draft` order to `quotation` state.  
Use this when the order is shown to the customer but not yet confirmed.

**Request body:** empty `{}`

**Response:** Full [Order Object](#order-object) with `state: "quotation"`.

---

### `POST /api/pos_perfume/v1/orders/<id>/draft` — Reset to Draft

Moves a `quotation` order back to `draft`.

**Request body:** empty `{}`

**Response:** Full [Order Object](#order-object) with `state: "draft"`.

---

### `POST /api/pos_perfume/v1/orders/<id>/cancel` — Cancel Order (Action)

Cancels an order from any state except `done`.

**Request body:** empty `{}`

**Response:**
```json
{ "success": true, "data": { "id": 109, "state": "cancel" } }
```

---

### Order Lifecycle & State Machine

```
          ┌──────────────────────────────────────────────────┐
          │                   STATE FLOW                     │
          │                                                  │
          │  CREATE                                          │
          │    │                                             │
          │    ▼                                             │
          │  [draft] ──/quotation──► [quotation]             │
          │    │   ◄──/draft────────      │                  │
          │    │                          │                  │
          │    └─────────/confirm─────────┘                  │
          │                  │                               │
          │                  ▼                               │
          │              [sale] ──► [done]                   │
          │                                                  │
          │  Any state (except done) ──/cancel──► [cancel]   │
          └──────────────────────────────────────────────────┘
```

**Editable states** (can update header and lines): `draft`, `quotation`  
**Cancellable states**: `draft`, `quotation`, `sale`  
**Read-only states**: `done`, `cancel`

---

### Complete Workflow Example

**Step 1 — Create a draft order:**
```http
POST /api/pos_perfume/v1/orders
Content-Type: application/json

{
  "partner_id": 54,
  "pricelist_id": 3,
  "invoice_type": "1"
}
```

**Step 2 — Add lines one by one (or use PUT with order_lines):**
```http
POST /api/pos_perfume/v1/orders/109/lines
Content-Type: application/json

{
  "product_id": 6,
  "warehouse_id": 1,
  "quantity": 2.0,
  "unit_price": 55.0,
  "discount_percent": 10.0
}
```

**Step 3 — Auto-save the full cart state:**
```http
PUT /api/pos_perfume/v1/orders/109
Content-Type: application/json

{
  "note": "Customer wants weekend delivery",
  "order_lines": [
    { "product_id": 6,  "warehouse_id": 1, "quantity": 2.0, "unit_price": 55.0, "discount_percent": 10.0 },
    { "product_id": 12, "warehouse_id": 1, "quantity": 1.0, "unit_price": 30.0 }
  ]
}
```

**Step 4a — Send as quotation:**
```http
POST /api/pos_perfume/v1/orders/109/quotation
```

**Step 4b — Or confirm directly:**
```http
POST /api/pos_perfume/v1/orders/109/confirm
```

**Step 5 — Get final order:**
```http
GET /api/pos_perfume/v1/orders/109
```

---

### Invoice Types Reference

| Key | Label (AR) | Meaning |
|---|---|---|
| `1` | زبون محل | Walk-in customer |
| `2` | شركات توصيل | Delivery companies |
| `3` | تاجر جملة | Wholesale trader |
| `4` | عميل تجزئة | Retail customer |
| `5` | عميل مؤسسة | Corporate / Institution |
| `6` | تصدير | Export |
| `7` | هدية | Gift |
| `8` | أخرى | Other |

---

## Pricelist & Products

### `POST /api/crm/pricelist/categories` `[Any]`

List product categories that have at least one active saleable product.

**Response:**
```json
{
  "success": true,
  "data": {
    "categories": [
      { "id": 5, "name": "Amour de Fleurs", "product_count": 42 }
    ]
  }
}
```

---

### `POST /api/crm/pricelist/products` `[Any]`

Product list with pricelist pricing and UoM options.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `pricelist_id` | integer | Pricelist for price calculation |
| `category_id` | integer | Filter by product category |
| `search` | string | Search by name or code |
| `discount_only` | boolean | Only products with active discounts |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/pricelist/products/<id>` `[Any]`

Full product detail: all UoM prices and stock quantity.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `pricelist_id` | integer | Pricelist for pricing |

---

### `POST /api/crm/pricelist/pricelists` `[Any]`

List all available pricelists for dropdown selection.

**Response:**
```json
{
  "success": true,
  "data": {
    "pricelists": [
      { "id": 1, "name": "USD Pricelist", "currency": "USD" }
    ]
  }
}
```

---

### `POST /api/crm/pricelist/requested_items/create` `[Any]`

Create an out-of-catalog product request by a customer.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `product_name` | string | **Yes** | Name of the requested product |
| `notes` | string | No | Additional details |

---

### `POST /api/crm/pricelist/requested_items` `[Any]`

List requested items.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `customer_id` | integer | Filter by customer |
| `status` | string | `pending`, `notified`, `fulfilled`, `cancelled` |

---

### `POST /api/crm/pricelist/requested_items/<id>/update_status` `[Any]`

Update the status of a requested item.

**Request params:** `status` (string, required)

---

### `POST /api/crm/pricelist/requested_items/<id>/delete` `[Any]`

Soft-delete a requested item.

---

## Delivery & Orders

### `POST /api/crm/delivery/customer_orders` `[Any]`

Fetch POS orders for a CRM customer, including delivery/picking status.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `customer_id` | integer | **Yes** | CRM customer ID |
| `page` | integer | No | Default: `1` |
| `per_page` | integer | No | Default: `20` |

**Response includes:** Order lines with product name/code, delivery status, and stock pickings.

---

### `POST /api/crm/delivery/order/<id>` `[Any]`

Get a single order with full lines and stock picking/delivery info.

---

### `POST /api/crm/delivery/orders/search` `[Any]`

Search orders by name, customer name, or sale order reference.

**Request params:** `query` (string, required)

---

## Supply Chain (Containers & Purchase Orders)

> **Note:** These are CRM-level supply records, not standard Odoo `purchase.order` records.

---

### Container Object

```json
{
  "id": 3,
  "name": "CONT-2024-001",
  "status": "in_transit",
  "division": "perfume",
  "estimated_arrival": "2024-04-01",
  "clearance_delivered": false,
  "is_deleted": false
}
```

---

### `POST /api/crm/supply/containers/list` `[Any]`

List containers. Filterable by `status` and `division`.

---

### `POST /api/crm/supply/containers/<id>` `[Any]`

Get single container.

---

### `POST /api/crm/supply/containers/create` `[Any]`

Create a container.

---

### `POST /api/crm/supply/containers/<id>/update` `[Any]`

Update a container.

---

### `POST /api/crm/supply/containers/<id>/delete` `[Any]`

Soft-delete a container.

---

### `POST /api/crm/supply/containers/<id>/clearance_delivered` `[Any]`

Mark container clearance as delivered.

---

### Supply PO Object

```json
{
  "id": 8,
  "name": "SPO-2024-008",
  "vendor_id": 12,
  "vendor_name": "Al-Rashidi Trading Co.",
  "status": "open",
  "lines": [
    {
      "id": 44,
      "product_name": "Amouage Reflection 50ml",
      "quantity": 100,
      "unit_price": 45.0,
      "total": 4500.0
    }
  ],
  "is_deleted": false
}
```

---

### `POST /api/crm/supply/po/list` `[Any]`

List supply purchase orders.

---

### `POST /api/crm/supply/po/<id>` `[Any]`

Get a single PO with all lines.

---

### `POST /api/crm/supply/po/create` `[Any]`

Create a supply PO.

---

### `POST /api/crm/supply/po/<id>/update` `[Any]`

Update PO header fields.

---

### `POST /api/crm/supply/po/<id>/delete` `[Any]`

Soft-delete a PO.

---

### `POST /api/crm/supply/po/suggested` `[Any]`

List suggested POs (system-generated reorder suggestions).

---

### `POST /api/crm/supply/po/<id>/lines` `[Any]`

List all lines for a PO.

---

### `POST /api/crm/supply/po/<id>/lines/add` `[Any]`

Add a line to a PO.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `product_name` | string | **Yes** | Product name or description |
| `quantity` | float | **Yes** | Quantity |
| `unit_price` | float | No | Unit price |

---

### `POST /api/crm/supply/po/<id>/lines/<line_id>/update` `[Any]`

Update a PO line.

---

### `POST /api/crm/supply/po/<id>/lines/<line_id>/delete` `[Any]`

**Hard-delete** a PO line (permanent removal).

---

### Vendor Object

```json
{
  "id": 12,
  "name": "Al-Rashidi Trading Co.",
  "contact_person": "Mohammed Ali",
  "phone": "+9647701234567",
  "email": "vendor@example.com",
  "is_deleted": false
}
```

---

### `POST /api/crm/supply/vendors/list` `[Any]`

List vendors. Search by `name`, `contact_person`, or `phone`.

---

### `POST /api/crm/supply/vendors/<id>` `[Any]`

Get a single vendor.

---

### `POST /api/crm/supply/vendors/create` `[Any]`

Create a vendor.

---

### `POST /api/crm/supply/vendors/<id>/update` `[Any]`

Update a vendor.

---

### `POST /api/crm/supply/vendors/<id>/delete` `[Any]`

Soft-delete a vendor.

---

## Workforce (Shifts & Attendance)

### Shift Object

```json
{
  "id": 5,
  "name": "Morning Shift",
  "branch_id": 1,
  "branch_name": "Baghdad Branch",
  "start_time": "09:00",
  "end_time": "17:00",
  "user_ids": [7, 9],
  "is_deleted": false
}
```

---

### `POST /api/crm/shifts/list` `[Any]`

List shifts. Filterable by `branch_id`.

---

### `POST /api/crm/shifts/create` `[Supervisor+]`

Create a shift.

**Request params:** `name` (required), `branch_id`, `start_time`, `end_time`, `user_ids` (integer[])

---

### `POST /api/crm/shifts/<id>/update` `[Supervisor+]`

Update shift fields including `user_ids` (replaces full list).

---

### `POST /api/crm/shifts/<id>/delete` `[Supervisor+]`

Soft-delete a shift.

---

### Attendance Object

```json
{
  "id": 99,
  "employee_id": 7,
  "employee_name": "Sara Khalid",
  "branch_id": 1,
  "check_in": "2024-03-10T09:05:00",
  "check_out": "2024-03-10T17:10:00",
  "duration_hours": 8.08,
  "late_minutes": 5,
  "work_type": "office",
  "is_deleted": false
}
```

---

### `POST /api/crm/attendance/check_in` `[Any]`

Employee check-in. Detects late arrival (15-minute grace period from shift start).

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `branch_id` | integer | **Yes** | Branch where checking in |
| `work_type` | string | No | `office`, `remote`, `field` |

---

### `POST /api/crm/attendance/check_out` `[Any]`

Close an open check-in. Auto-computes `duration_hours`.

**Request params:** `branch_id` (integer, required)

---

### `POST /api/crm/attendance/list` `[Supervisor+]`

Paginated attendance records.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `branch_id` | integer | Filter by branch |
| `employee_id` | integer | Filter by employee user |
| `date_from` | string | ISO date lower bound |
| `date_to` | string | ISO date upper bound |
| `work_type` | string | Filter by work type |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/attendance/live_status` `[Supervisor+]`

Real-time view: who is currently checked in per branch.

---

### Message Template Object

```json
{
  "id": 3,
  "name": "Welcome Message",
  "channel": "whatsapp",
  "category": "onboarding",
  "body": "Hello {customer_name}, welcome to NBS! Your agent is {agent_name}.",
  "branch_id": 1,
  "is_deleted": false
}
```

**Template variables:** `{customer_name}`, `{agent_name}`, `{branch_name}`

---

### `POST /api/crm/templates/list` `[Any]`

List templates. Filterable by `channel`, `category`, `branch_id`.

---

### `POST /api/crm/templates/create` `[Supervisor+]`

Create a message template.

**Request params:** `name` (required), `channel`, `category`, `body` (required), `branch_id`

---

### `POST /api/crm/templates/<id>/update` `[Supervisor+]`

Update a template.

---

### `POST /api/crm/templates/<id>/delete` `[Supervisor+]`

Soft-delete a template.

---

### `POST /api/crm/templates/<id>/render` `[Any]`

Render a template with actual values substituted.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `customer_id` | integer | CRM customer (provides `{customer_name}`) |
| `agent_id` | integer | User (provides `{agent_name}`) |
| `branch_id` | integer | Branch (provides `{branch_name}`) |

**Response:**
```json
{
  "success": true,
  "data": {
    "rendered": "Hello Ahmad Al-Rashidi, welcome to NBS! Your agent is Sara Khalid."
  }
}
```

---

## Tasks & Follow-ups

### Task Object

```json
{
  "id": 20,
  "title": "Follow up about Creed order",
  "description": "Call customer to confirm delivery",
  "customer_id": 42,
  "customer_name": "Ahmad Al-Rashidi",
  "branch_id": 1,
  "assigned_to_id": 7,
  "assigned_to_name": "Sara Khalid",
  "status": "open",
  "priority": "high",
  "due_date": "2024-03-12",
  "is_overdue": false,
  "completed_at": null,
  "is_deleted": false
}
```

**Status values:** `open`, `in_progress`, `done`, `overdue`  
**Priority values:** `low`, `normal`, `high`, `urgent`

---

### `POST /api/crm/tasks/list` `[Any]`

List tasks with optional filters.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `customer_id` | integer | Filter by customer |
| `branch_id` | integer | Filter by branch |
| `assigned_to_id` | integer | Filter by assignee |
| `status` | string | Filter by status |
| `priority` | string | Filter by priority |
| `overdue_only` | boolean | Only overdue tasks |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/tasks/<id>` `[Any]`

Get a single task.

---

### `POST /api/crm/tasks/create` `[Any]`

Create a follow-up task. Defaults `assigned_to_id` to the current authenticated user.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | **Yes** | Task title |
| `customer_id` | integer | **Yes** | CRM customer ID |
| `description` | string | No | Task details |
| `branch_id` | integer | No | Associated branch |
| `assigned_to_id` | integer | No | Assignee user ID |
| `priority` | string | No | Default: `normal` |
| `due_date` | string | No | ISO date `YYYY-MM-DD` |

---

### `POST /api/crm/tasks/<id>/update` `[Any]`

Update task fields.

---

### `POST /api/crm/tasks/<id>/update_status` `[Any]`

Update task status.

**Request params:** `status` (string, required)

---

### `POST /api/crm/tasks/<id>/assign` `[Any]`

Re-assign a task. Resets status to `open`.

**Request params:** `user_id` (integer, required)

---

### `POST /api/crm/tasks/<id>/delete` `[Any]`

Soft-delete a task.

---

### `POST /api/crm/tasks/my` `[Any]`

List all tasks assigned to the currently authenticated user.

---

## Configuration (Tags, Stages, Scripts)

### `POST /api/crm/config/tags/list` `[Any]`

List active tags. Filterable by `tag_type`.

**Response:**
```json
{
  "success": true,
  "data": {
    "tags": [
      { "id": 1, "name": "Wholesale", "tag_type": "customer", "color": "#3498db" }
    ]
  }
}
```

---

### `POST /api/crm/config/tags/create` `[Supervisor+]`

Create a tag.

**Request params:** `name` (required), `tag_type`, `color`

---

### `POST /api/crm/config/tags/<id>/update` `[Supervisor+]`

Update a tag.

---

### `POST /api/crm/config/tags/<id>/delete` `[Supervisor+]`

Soft-delete a tag.

---

### `POST /api/crm/config/stages/list` `[Any]`

List pipeline stages ordered by `sequence`.

**Response:**
```json
{
  "success": true,
  "data": {
    "stages": [
      { "id": 1, "name": "Lead", "sequence": 10, "stage_type": "lead" },
      { "id": 2, "name": "Active", "sequence": 30, "stage_type": "active" }
    ]
  }
}
```

---

### `POST /api/crm/config/stages/create` `[Supervisor+]`

Create a pipeline stage.

**Request params:** `name` (required), `stage_type`, `sequence`

---

### `POST /api/crm/config/stages/<id>/update` `[Supervisor+]`

Update a stage.

---

### `POST /api/crm/config/stages/<id>/delete` `[Supervisor+]`

Soft-delete a stage.

---

### `POST /api/crm/config/scripts/list` `[Any]`

List call scripts and FAQs.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `category` | string | Filter by category |
| `branch_id` | integer | Filter by branch |
| `search` | string | Search by title |

---

### `POST /api/crm/config/scripts/<id>` `[Any]`

Get a single script.

---

### `POST /api/crm/config/scripts/create` `[Supervisor+]`

Create a call script.

**Request params:** `title` (required), `category`, `branch_id`, `content` (required)

---

### `POST /api/crm/config/scripts/<id>/update` `[Supervisor+]`

Update a script.

---

### `POST /api/crm/config/scripts/<id>/delete` `[Supervisor+]`

Soft-delete a script.

---

## QA Reviews

> All QA endpoints require at minimum the `qa_auditor` role.

### QA Review Object

```json
{
  "id": 15,
  "review_type": "call",
  "agent_id": 7,
  "agent_name": "Sara Khalid",
  "reviewer_id": 10,
  "reviewer_name": "QA Supervisor",
  "branch_id": 1,
  "status": "submitted",
  "scores": {
    "greeting": 90,
    "product_knowledge": 85,
    "problem_solving": 88,
    "professionalism": 92,
    "compliance": 95,
    "overall": 90
  },
  "total_score": 90,
  "listen_time_seconds": 1320,
  "notes": "Excellent product knowledge, minor compliance issue",
  "created_at": "2024-03-10T15:00:00"
}
```

---

### `POST /api/crm/qa/reviews` `[QA Auditor+]`

List reviews with optional filters.

**Request params:**

| Field | Type | Description |
|---|---|---|
| `review_type` | string | `call` or `message` |
| `agent_id` | integer | Filter by agent |
| `reviewer_id` | integer | Filter by reviewer |
| `status` | string | `draft`, `submitted` |
| `branch_id` | integer | Filter by branch |
| `page` | integer | Default: `1` |
| `per_page` | integer | Default: `20` |

---

### `POST /api/crm/qa/reviews/<id>` `[QA Auditor+]`

Get a single review.

---

### `POST /api/crm/qa/reviews/create` `[QA Auditor+]`

Create a QA review.

**Request params:**

| Field | Type | Required | Description |
|---|---|---|---|
| `review_type` | string | **Yes** | `call` or `message` |
| `agent_id` | integer | **Yes** | Agent being reviewed |
| `branch_id` | integer | No | Branch |
| `greeting` | integer | No | Score 0–100 |
| `product_knowledge` | integer | No | Score 0–100 |
| `problem_solving` | integer | No | Score 0–100 |
| `professionalism` | integer | No | Score 0–100 |
| `compliance` | integer | No | Score 0–100 |
| `overall` | integer | No | Score 0–100 |
| `listen_time_seconds` | integer | No | Call/message duration reviewed |
| `notes` | string | No | Reviewer comments |

---

### `POST /api/crm/qa/reviews/<id>/update` `[Any]`

Update a review. Only allowed while status is `draft`.

---

### `POST /api/crm/qa/reviews/<id>/submit` `[QA Auditor+]`

Lock and submit a review (changes status from `draft` to `submitted`).

---

### `POST /api/crm/qa/stats` `[QA Supervisor or Supervisor+]`

Aggregate QA statistics.

**Request params:** `branch_id` (optional), `date_from`, `date_to`

**Response:**
```json
{
  "success": true,
  "data": {
    "total_reviews": 140,
    "avg_score": 87.4,
    "call_reviews": 110,
    "message_reviews": 30,
    "total_listen_time_hours": 48.5
  }
}
```

---

## File Uploads

> Upload endpoints use `multipart/form-data` (HTTP), **not** JSON-RPC.

---

### `POST /api/crm/upload/image` `[HTTP]` `[Any]`

Upload one or more shop images.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `files[]` | file | **Yes** | One or more image files (also accepts `file` or `image` field name) |
| `customer_id` | integer | No | Link images to a specific customer |

**Constraints:**
- Max file size: **10 MB** per file
- Allowed types: `jpeg`, `png`, `gif`, `webp`, `svg`, `bmp`

**Response:**
```json
{
  "success": true,
  "data": {
    "files": [
      {
        "id": 123,
        "url": "https://host/web/content/123?access_token=abc",
        "filename": "shop_photo.jpg"
      }
    ]
  }
}
```

---

### `POST /api/crm/upload/document` `[HTTP]` `[Any]`

Upload a customer document with type metadata.

**Request:** `multipart/form-data`

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | file | **Yes** | Document file (also accepts `document` field name) |
| `type` | string | **Yes** | Document type (see values below) |
| `customer_id` | integer | No | Link document to a customer |

**Document type values:** `national_id`, `shop_license`, `tax_certificate`, `commerce_registration`, `residence_card`, `other`

**Constraints:**
- Max file size: **20 MB**
- Allowed types: `pdf`, `jpeg`, `png`, `webp`, `doc`, `docx`, `xls`, `xlsx`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 124,
    "url": "https://host/web/content/124?access_token=xyz",
    "filename": "national_id.pdf",
    "type": "national_id"
  }
}
```

---

## Error Reference

### Standard error response

```json
{
  "success": false,
  "error": "Human-readable error message"
}
```

### Common error messages

| Error | Cause |
|---|---|
| `"Unauthorized"` | Missing, expired, or invalid JWT token |
| `"Forbidden — Supervisor role required"` | Authenticated but insufficient role |
| `"Customer not found"` | Record with given ID does not exist |
| `"product_id is required for each order line"` | Missing required field in order line |
| `"Product not found"` | Product ID does not exist in Odoo |
| `"UoM not found"` | Unit of Measure ID does not exist |
| `"Warehouse not found"` | Warehouse ID does not exist |
| `"query must be at least 2 characters"` | Search query too short |
| `"File too large"` | Uploaded file exceeds size limit |
| `"File type not allowed"` | MIME type not in allowed list |
| `"type is required"` | Missing `type` param in document upload |

---

## Quick Reference — Endpoint Index

| Endpoint | Method | Auth |
|---|---|---|
| `/api/crm/customers/list` | POST | Any |
| `/api/crm/customers/<id>` | POST | Any |
| `/api/crm/customers/create` | POST | Any |
| `/api/crm/customers/<id>/update` | POST | Any |
| `/api/crm/customers/<id>/delete` | POST | Any |
| `/api/crm/customers/<id>/kanban_move` | POST | Any |
| `/api/crm/customers/search` | POST | Any |
| `/api/crm/customers/<id>/activity` | POST | Any |
| `/api/crm/customers/<id>/calls` | POST | Any |
| `/api/crm/customers/<id>/tickets` | POST | Any |
| `/api/crm/customers/<id>/note/add` | POST | Any |
| `/api/crm/customers/<id>/interactions` | POST | Any |
| `/api/crm/interactions/create` | POST | Any |
| `/api/crm/customers/<id>/channel_identity/add` | POST | Any |
| `/api/crm/customers/<id>/channel_identity/<ci_id>/update` | POST | Any |
| `/api/crm/customers/<id>/channel_identity/<ci_id>/delete` | POST | Any |
| `/api/crm/customers/setup_stages` | POST | Any |
| `/api/crm/customers/sync_from_odoo` | POST | Any |
| `/api/crm/calls/list` | POST | Any |
| `/api/crm/calls/<id>` | POST | Any |
| `/api/crm/calls/create` | POST | Any |
| `/api/crm/calls/<id>/end` | POST | Any |
| `/api/crm/calls/<id>/update` | POST | Any |
| `/api/crm/calls/<id>/delete` | POST | Any |
| `/api/crm/calls/<id>/attach_recording` | POST | Any |
| `/api/crm/calls/queue/list` | POST | Any |
| `/api/crm/calls/queue/add` | POST | Any |
| `/api/crm/calls/queue/<id>/assign` | POST | Any |
| `/api/crm/tickets/list` | POST | Any |
| `/api/crm/tickets/<id>` | POST | Any |
| `/api/crm/tickets/search` | POST | Any |
| `/api/crm/tickets/create` | POST | Any |
| `/api/crm/tickets/<id>/update` | POST | Any |
| `/api/crm/tickets/<id>/update_status` | POST | Any |
| `/api/crm/tickets/<id>/assign` | POST | Any |
| `/api/crm/tickets/<id>/escalate` | POST | Any |
| `/api/crm/tickets/<id>/delete` | POST | Any |
| `/api/crm/tickets/<id>/note/add` | POST | Any |
| `/api/crm/tickets/<id>/notes` | POST | Any |
| `/api/crm/channels/config_list` | POST | Any |
| `/api/crm/channels/config/create` | POST | Supervisor+ |
| `/api/crm/channels/config/<id>/update` | POST | Supervisor+ |
| `/api/crm/channels/config/<id>/delete` | POST | Supervisor+ |
| `/api/crm/channels/messages/list` | POST | Any |
| `/api/crm/channels/messages/conversation` | POST | Any |
| `/api/crm/channels/messages/create` | POST | Any |
| `/api/crm/channels/messages/<id>/assign` | POST | Any |
| `/api/crm/channels/messages/<id>/reply` | POST | Any |
| `/api/crm/channels/messages/<id>/resolve` | POST | Any |
| `/api/crm/channels/messages/<id>/transfer` | POST | Any |
| `/api/crm/analytics/dashboard_stats` | POST | Any |
| `/api/crm/analytics/channel_report` | POST | Any |
| `/api/crm/analytics/branch_report` | POST | Any |
| `/api/crm/analytics/employee_kpi` | POST | Any |
| `/api/crm/analytics/all_employees_kpi` | POST | Supervisor+ |
| `/api/crm/analytics/supervisor_dashboard` | POST | Supervisor+ |
| `/api/crm/analytics/ai_vs_human` | POST | Any |
| `/api/crm/analytics/export_kpi` | HTTP | Manager+ |
| `/api/crm/analytics/audit_log` | POST | Any |
| `/api/crm/kb/articles/list` | POST | Any |
| `/api/crm/kb/articles/search` | POST | Any |
| `/api/crm/kb/articles/<id>` | POST | Any |
| `/api/crm/kb/articles/create` | POST | Supervisor+ |
| `/api/crm/kb/articles/<id>/update` | POST | Supervisor+ |
| `/api/crm/kb/articles/<id>/delete` | POST | Supervisor+ |
| `/api/crm/kb/notifications/list` | POST | Any |
| `/api/crm/kb/notifications/push` | POST | Supervisor+ |
| `/api/crm/branches/list` | POST | Any |
| `/api/crm/branches/<id>` | POST | Any |
| `/api/crm/branches/create` | POST | Manager+ |
| `/api/crm/branches/<id>/update` | POST | Supervisor+ |
| `/api/crm/branches/<id>/user_assign` | POST | Manager+ |
| `/api/crm/branches/<id>/delete` | POST | Manager+ |
| `/api/crm/pos/invoice_context` | POST | Any |
| `/api/crm/pos/products` | POST | Any |
| `/api/crm/pos/product_detail` | POST | Any |
| `/api/crm/pos/uom_price` | POST | Any |
| `/api/crm/pos/orders/create` | POST | Any |
| `/api/crm/pos/orders/<id>` | POST | Any |
| `/api/crm/pos/customer_orders` | POST | Any |
| `/api/crm/pricelist/categories` | POST | Any |
| `/api/crm/pricelist/products` | POST | Any |
| `/api/crm/pricelist/products/<id>` | POST | Any |
| `/api/crm/pricelist/pricelists` | POST | Any |
| `/api/crm/pricelist/requested_items/create` | POST | Any |
| `/api/crm/pricelist/requested_items` | POST | Any |
| `/api/crm/pricelist/requested_items/<id>/update_status` | POST | Any |
| `/api/crm/pricelist/requested_items/<id>/delete` | POST | Any |
| `/api/crm/delivery/customer_orders` | POST | Any |
| `/api/crm/delivery/order/<id>` | POST | Any |
| `/api/crm/delivery/orders/search` | POST | Any |
| `/api/crm/supply/containers/list` | POST | Any |
| `/api/crm/supply/containers/<id>` | POST | Any |
| `/api/crm/supply/containers/create` | POST | Any |
| `/api/crm/supply/containers/<id>/update` | POST | Any |
| `/api/crm/supply/containers/<id>/delete` | POST | Any |
| `/api/crm/supply/containers/<id>/clearance_delivered` | POST | Any |
| `/api/crm/supply/po/list` | POST | Any |
| `/api/crm/supply/po/<id>` | POST | Any |
| `/api/crm/supply/po/create` | POST | Any |
| `/api/crm/supply/po/<id>/update` | POST | Any |
| `/api/crm/supply/po/<id>/delete` | POST | Any |
| `/api/crm/supply/po/suggested` | POST | Any |
| `/api/crm/supply/po/<id>/lines` | POST | Any |
| `/api/crm/supply/po/<id>/lines/add` | POST | Any |
| `/api/crm/supply/po/<id>/lines/<line_id>/update` | POST | Any |
| `/api/crm/supply/po/<id>/lines/<line_id>/delete` | POST | Any |
| `/api/crm/supply/vendors/list` | POST | Any |
| `/api/crm/supply/vendors/<id>` | POST | Any |
| `/api/crm/supply/vendors/create` | POST | Any |
| `/api/crm/supply/vendors/<id>/update` | POST | Any |
| `/api/crm/supply/vendors/<id>/delete` | POST | Any |
| `/api/crm/shifts/list` | POST | Any |
| `/api/crm/shifts/create` | POST | Supervisor+ |
| `/api/crm/shifts/<id>/update` | POST | Supervisor+ |
| `/api/crm/shifts/<id>/delete` | POST | Supervisor+ |
| `/api/crm/attendance/check_in` | POST | Any |
| `/api/crm/attendance/check_out` | POST | Any |
| `/api/crm/attendance/list` | POST | Supervisor+ |
| `/api/crm/attendance/live_status` | POST | Supervisor+ |
| `/api/crm/templates/list` | POST | Any |
| `/api/crm/templates/create` | POST | Supervisor+ |
| `/api/crm/templates/<id>/update` | POST | Supervisor+ |
| `/api/crm/templates/<id>/delete` | POST | Supervisor+ |
| `/api/crm/templates/<id>/render` | POST | Any |
| `/api/crm/tasks/list` | POST | Any |
| `/api/crm/tasks/<id>` | POST | Any |
| `/api/crm/tasks/create` | POST | Any |
| `/api/crm/tasks/<id>/update` | POST | Any |
| `/api/crm/tasks/<id>/update_status` | POST | Any |
| `/api/crm/tasks/<id>/assign` | POST | Any |
| `/api/crm/tasks/<id>/delete` | POST | Any |
| `/api/crm/tasks/my` | POST | Any |
| `/api/crm/config/tags/list` | POST | Any |
| `/api/crm/config/tags/create` | POST | Supervisor+ |
| `/api/crm/config/tags/<id>/update` | POST | Supervisor+ |
| `/api/crm/config/tags/<id>/delete` | POST | Supervisor+ |
| `/api/crm/config/stages/list` | POST | Any |
| `/api/crm/config/stages/create` | POST | Supervisor+ |
| `/api/crm/config/stages/<id>/update` | POST | Supervisor+ |
| `/api/crm/config/stages/<id>/delete` | POST | Supervisor+ |
| `/api/crm/config/scripts/list` | POST | Any |
| `/api/crm/config/scripts/<id>` | POST | Any |
| `/api/crm/config/scripts/create` | POST | Supervisor+ |
| `/api/crm/config/scripts/<id>/update` | POST | Supervisor+ |
| `/api/crm/config/scripts/<id>/delete` | POST | Supervisor+ |
| `/api/crm/qa/reviews` | POST | QA Auditor+ |
| `/api/crm/qa/reviews/<id>` | POST | QA Auditor+ |
| `/api/crm/qa/reviews/create` | POST | QA Auditor+ |
| `/api/crm/qa/reviews/<id>/update` | POST | Any |
| `/api/crm/qa/reviews/<id>/submit` | POST | QA Auditor+ |
| `/api/crm/qa/stats` | POST | QA Supervisor / Supervisor+ |
| `/api/crm/upload/image` | HTTP | Any |
| `/api/crm/upload/document` | HTTP | Any |

---

*Generated from source: `addons/lugal_crm/controllers/` — Lugal CRM v1.0*
