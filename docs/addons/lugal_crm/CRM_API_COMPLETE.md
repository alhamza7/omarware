# Lugal CRM — Complete API Reference

> **Base URL:** `http://<server>:8070`
> **Protocol:** JSON-RPC 2.0 over HTTP POST
> **Auth:** `Authorization: Bearer <jwt_token>` (required on all endpoints)
> **Content-Type:** `application/json`

---

## Request Format

Every request body follows JSON-RPC 2.0:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    /* endpoint-specific parameters here */
  }
}
```

## Response Format

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { /* payload */ }
  }
}
```

### Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Error message here"
  }
}
```

---

## Authentication

All endpoints require a valid JWT token. Tokens are issued by the **`lugal_auth`** module
— a dedicated, standalone auth service that is completely independent of `nbs_archive`.

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Obtain a Token

```
POST /lugal/auth/login
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "username": "user@example.com",
    "password": "yourpassword"
  }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJ...",
      "refresh_token": "eyJ...",
      "token_type": "bearer",
      "user": { "id": 5, "name": "Ahmad", "username": "ahmad@nbs.com", "email": "ahmad@nbs.com" }
    }
  }
}
```

### Refresh a Token

```
POST /lugal/auth/refresh
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { "refresh_token": "eyJ..." }
}
```

### JWT Config Keys (ir.config_parameter)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `lugal_auth.jwt_secret_key` | `lugal-secret-change-in-production` | Access token secret |
| `lugal_auth.jwt_refresh_secret_key` | `lugal-refresh-secret-change-in-production` | Refresh secret |
| `lugal_auth.jwt_access_token_expire_minutes` | `480` (8 hours) | Access token TTL |
| `lugal_auth.jwt_refresh_token_expire_days` | `7` | Refresh token TTL |

> **Important:** Change the secret keys in production via Settings → Technical → System Parameters.

---

## 1. Customers (`/api/crm/customers/*`)

### 1.1 List Customers
```
POST /api/crm/customers/list
```
**Params:**
| Field | Type | Default | Description |
|-------|------|---------|-------------|
| page | int | 1 | Page number |
| per_page | int | 50 | Results per page |
| search | string | null | Search by name, phone, email |
| stage_id | int | null | Filter by stage |
| branch_id | int | null | Filter by branch |
| vip_only | bool | false | Show VIP customers only |

**Response `data`:**
```json
{
  "total": 250,
  "page": 1,
  "per_page": 50,
  "items": [
    {
      "id": 1,
      "name": "Ahmed Al-Rashidi",
      "name_ar": "أحمد الراشدي",
      "phone_1": "+9647701234567",
      "phone_2": null,
      "email": "ahmed@example.com",
      "city": "Baghdad",
      "vip_status": true,
      "is_enterprise": false,
      "stage_id": 2,
      "stage_name": "Active",
      "lifetime_value": 15000.00,
      "credit_debt": 500.00,
      "credit_limit": 2000.00,
      "days_since_purchase": 12,
      "last_purchase_date": "2026-02-10",
      "member_since": "2024-01-15",
      "account_manager_id": 5,
      "account_manager_name": "Sara",
      "tag_ids": [1, 3],
      "branch_ids": [1]
    }
  ]
}
```

---

### 1.2 Get Customer (360° Card)
```
POST /api/crm/customers/<customer_id>
```
**Response `data`:** Full customer object with all fields including:
- `most_purchased_item_ids` (array of product ids)
- `sample_version`, `sample_date`
- `open_invoice_status`, `delivery_status`
- `referral_source`, `loyalty_points`
- `preferred_contact_time`, `preferred_contact_channel`
- `shop_location`, `favorite_shipping_address`, `billing_address`
- `attachment_ids` (count of ID documents)

---

### 1.3 Create Customer
```
POST /api/crm/customers/create
```
**Params:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | ✅ | Customer full name |
| name_ar | string | — | Arabic name |
| phone_1 | string | — | Primary phone |
| phone_2 | string | — | Secondary phone |
| phone_3 | string | — | Third phone |
| email | string | — | Email address |
| address | string | — | Full address |
| city | string | — | City |
| country_id | int | — | `res.country` ID |
| stage_id | int | — | Pipeline stage ID |
| tag_ids | array[int] | — | Tag IDs |
| vip_status | bool | — | VIP flag |
| is_enterprise | bool | — | Enterprise customer |
| branch_ids | array[int] | — | Branch IDs |
| account_manager_id | int | — | Assigned manager (res.users) |
| referral_source | string | — | How acquired |
| shop_location | string | — | Shop location |

---

### 1.4 Update Customer
```
POST /api/crm/customers/<customer_id>/update
```
Pass only the fields to update (same list as create).

---

### 1.5 Delete Customer (Soft)
```
POST /api/crm/customers/<customer_id>/delete
```
Sets `is_deleted=True`, `active=False`.

---

### 1.6 Move Stage (Kanban)
```
POST /api/crm/customers/<customer_id>/kanban_move
```
**Params:** `stage_id` (int, required)

---

### 1.7 Search Customers
```
POST /api/crm/customers/search
```
**Params:** `query` (string, required), `limit` (int, default=50)

---

### 1.8 Activity Timeline
```
POST /api/crm/customers/<customer_id>/activity
```
Returns merged, time-sorted timeline of: calls + interactions + messages + tickets.

**Params:** `limit` (int, default=50), `offset` (int, default=0)

**Response `data`:** Array of timeline items, each with `type`, `date`, `summary`, `ref_id`.

---

### 1.9 Customer Calls
```
POST /api/crm/customers/<customer_id>/calls
```
**Params:** `page`, `per_page`

---

### 1.10 Customer Tickets
```
POST /api/crm/customers/<customer_id>/tickets
```
**Params:** `page`, `per_page`

---

### 1.11 Add Quick Note
```
POST /api/crm/customers/<customer_id>/note/add
```
**Params:** `note` (string, required) — Creates a sticky note interaction.

---

### 1.12 Add Channel Identity
```
POST /api/crm/customers/<customer_id>/channel_identity/add
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| channel | string | ✅ | e.g. `whatsapp`, `instagram` |
| handle | string | ✅ | Username / phone on that channel |
| is_primary | bool | — |

---

### 1.13 Update Channel Identity
```
POST /api/crm/customers/<customer_id>/channel_identity/<ci_id>/update
```

---

### 1.14 Delete Channel Identity
```
POST /api/crm/customers/<customer_id>/channel_identity/<ci_id>/delete
```

---

### 1.15 List Interactions
```
POST /api/crm/customers/<customer_id>/interactions
```
**Params:** `page`, `per_page`, `interaction_type` (call/note/email/whatsapp/task/ticket/purchase)

---

### 1.16 Create Standalone Interaction
```
POST /api/crm/interactions/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| customer_id | int | ✅ |
| interaction_type | string | ✅ |
| subject | string | — |
| body | string | — |
| channel | string | — |
| outcome | string | — |
| duration_seconds | int | — |
| interaction_date | string (ISO8601) | — |

---

## 2. Calls (`/api/crm/calls/*`)

### 2.1 List Calls
```
POST /api/crm/calls/list
```
**Params:** `page`, `per_page`, `customer_id`, `branch_id`, `agent_id`, `date_from`, `date_to`, `outcome`

**`outcome` values:** `resolved` | `callback` | `escalated` | `no_answer`

---

### 2.2 Get Call
```
POST /api/crm/calls/<call_id>
```
**Response `data`:**
```json
{
  "id": 10,
  "customer_id": 1,
  "customer_name": "Ahmed",
  "agent_id": 5,
  "agent_name": "Sara",
  "call_type": "inbound",
  "caller_number": "+9647701234567",
  "started_at": "2026-02-26T09:00:00",
  "ended_at": "2026-02-26T09:15:00",
  "duration_seconds": 900,
  "outcome": "resolved",
  "notes": "Customer asked about order #1234",
  "ai_summary": null,
  "qa_score": 87.5,
  "recording_url": "https://storage/.../call_10.mp3",
  "balance_at_call": 1500.00,
  "outstanding_at_call": 200.00,
  "credit_limit_at_call": 2000.00,
  "catalogue_sent": true,
  "catalogue_sent_via": "whatsapp",
  "pos_order_id": 55,
  "pos_order_name": "PO/2026/00055",
  "pos_order_total": 250.00,
  "pos_order_state": "done",
  "ticket_created_id": null
}
```

---

### 2.3 Create Call (Start)
```
POST /api/crm/calls/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| customer_id | int | ✅ |
| call_type | string | — | `inbound` (default) or `outbound` |
| channel | string | — | e.g. `phone`, `whatsapp` |
| caller_number | string | — |
| branch_id | int | — |
| balance_at_call | float | — | Snapshot of current balance |
| outstanding_at_call | float | — |
| credit_limit_at_call | float | — |

---

### 2.4 End Call
```
POST /api/crm/calls/<call_id>/end
```
**Params:** `duration_seconds`, `outcome`, `notes`, `catalogue_sent`, `catalogue_sent_via`, `recording_url`

---

### 2.5 Update Call
```
POST /api/crm/calls/<call_id>/update
```
Writable fields: `qa_score`, `issues_found`, `ai_summary`, `notes`, `recording_url`, `catalogue_sent`, `catalogue_sent_via`, `outcome`

---

### 2.6 Delete Call (Soft)
```
POST /api/crm/calls/<call_id>/delete
```

---

### 2.7 Attach Recording
```
POST /api/crm/calls/<call_id>/attach_recording
```
**Params:** `recording_url` (string, required)

---

### 2.8 Queue — List
```
POST /api/crm/calls/queue/list
```
**Params:** `status` (`waiting` default)

---

### 2.9 Queue — Add
```
POST /api/crm/calls/queue/add
```
**Params:** `customer_id`, `channel`, `caller_number`

---

### 2.10 Queue — Assign
```
POST /api/crm/calls/queue/<queue_id>/assign
```
Assigns queued call to current JWT user.

---

## 3. Tickets (`/api/crm/tickets/*`)

### 3.1 List Tickets
```
POST /api/crm/tickets/list
```
**Params:** `page`, `per_page`, `customer_id`, `branch_id`, `status`, `priority`, `assigned_to_id`

**`status` values:** `open` | `in_progress` | `resolved` | `closed` | `stale`
**`priority` values:** `low` | `medium` | `high` | `urgent`

---

### 3.2 Get Ticket
```
POST /api/crm/tickets/<ticket_id>
```
**Params:** `include_notes` (bool) — if true, includes internal notes array.

**Response `data`:**
```json
{
  "id": 5,
  "ticket_number": "TKT-00005",
  "customer_id": 1,
  "customer_name": "Ahmed",
  "title": "Wrong order delivered",
  "description": "Customer received wrong items",
  "status": "open",
  "priority": "high",
  "channel": "whatsapp",
  "ticket_type": "complaint",
  "assigned_to_id": 3,
  "assigned_to_name": "Ali",
  "escalated_to_id": null,
  "sla_deadline": "2026-02-27T09:00:00",
  "first_response_at": "2026-02-26T09:05:00",
  "resolved_at": null,
  "branch_id": 1
}
```

---

### 3.3 Search Tickets
```
POST /api/crm/tickets/search
```
**Params:** `query`, `branch_id`, `limit`

---

### 3.4 Create Ticket
```
POST /api/crm/tickets/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| customer_id | int | ✅ |
| title | string | ✅ |
| description | string | — |
| branch_id | int | — |
| ticket_type | string | — |
| channel | string | — |
| priority | string | — | default: `medium` |
| sla_deadline | string (ISO8601) | — |

**Note:** `ticket_number` is auto-generated (TKT-00001 format).

---

### 3.5 Update Ticket
```
POST /api/crm/tickets/<ticket_id>/update
```

---

### 3.6 Update Status
```
POST /api/crm/tickets/<ticket_id>/update_status
```
**Params:** `status` (required) — sets `resolved_at` automatically when `resolved`.

---

### 3.7 Assign Ticket
```
POST /api/crm/tickets/<ticket_id>/assign
```
**Params:** `assigned_to_id` (int, required) — sets `first_response_at` on first assignment.

---

### 3.8 Escalate Ticket
```
POST /api/crm/tickets/<ticket_id>/escalate
```
**Params:** `escalated_to_id` (int, required)

---

### 3.9 Delete Ticket (Soft)
```
POST /api/crm/tickets/<ticket_id>/delete
```

---

### 3.10 Add Note
```
POST /api/crm/tickets/<ticket_id>/note/add
```
**Params:** `body` (string, required) — stores as `lugal.crm.interaction`.

---

### 3.11 Get Notes
```
POST /api/crm/tickets/<ticket_id>/notes
```

---

## 4. Tasks (`/api/crm/tasks/*`)

### 4.1 List Tasks
```
POST /api/crm/tasks/list
```
**Params:** `page`, `per_page`, `customer_id`, `branch_id`, `assigned_to_id`, `status`, `priority`, `overdue_only`

**`status` values:** `open` | `in_progress` | `done` | `overdue`

---

### 4.2 Get Task
```
POST /api/crm/tasks/<task_id>
```

---

### 4.3 Create Task
```
POST /api/crm/tasks/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| title | string | ✅ |
| customer_id | int | — |
| assigned_to_id | int | — |
| branch_id | int | — |
| description | string | — |
| priority | string | — | default: `medium` |
| due_date | string (ISO8601) | — |
| reminder_date | string (ISO8601) | — |

---

### 4.4 Update Task
```
POST /api/crm/tasks/<task_id>/update
```

---

### 4.5 Update Status
```
POST /api/crm/tasks/<task_id>/update_status
```
**Params:** `status` (required)

---

### 4.6 Assign Task
```
POST /api/crm/tasks/<task_id>/assign
```
**Params:** `assigned_to_id` (int, required)

---

### 4.7 Delete Task (Soft)
```
POST /api/crm/tasks/<task_id>/delete
```

---

### 4.8 My Tasks (Current User)
```
POST /api/crm/tasks/my
```
**Params:** `page`, `per_page`, `status`

---

## 5. Omnichannel (`/api/crm/channels/*`)

### 5.1 List Channel Configs
```
POST /api/crm/channels/config_list
```
**Params:** `branch_id`

---

### 5.2 Create Channel Config
```
POST /api/crm/channels/config/create
```
**Params:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| channel | string | ✅ | — | `whatsapp` / `instagram` / etc. |
| branch_id | int | — | — |
| display_name | string | — | — |
| color_hex | string | — | — |
| is_free_for_all | bool | — | true |
| sla_threshold_seconds | int | — | 300 |
| work_hours_start | float | — | 8.0 |
| work_hours_end | float | — | 18.0 |

---

### 5.3 Update Channel Config
```
POST /api/crm/channels/config/<config_id>/update
```

---

### 5.4 Delete Channel Config
```
POST /api/crm/channels/config/<config_id>/delete
```

---

### 5.5 List Messages (Inbox)
```
POST /api/crm/channels/messages/list
```
**Params:** `page`, `per_page`, `customer_id`, `channel`, `status`, `branch_id`, `assigned_to_id`, `sla_breached`

**`status` values:** `pending` | `assigned` | `resolved`
**`channel` values:** `whatsapp` | `instagram` | `telegram` | `tiktok` | `x` | `snapchat` | `email` | `website`

---

### 5.6 Get Conversation Thread
```
POST /api/crm/channels/messages/conversation
```
**Params:** `conversation_id` (string, required)

---

### 5.7 Create Message
```
POST /api/crm/channels/messages/create
```
**Params:**
| Field | Type | Required | Default |
|-------|------|----------|---------|
| customer_id | int | ✅ | — |
| channel | string | ✅ | — |
| content | string | ✅ | — |
| direction | string | — | `inbound` |
| conversation_id | string | — | — |
| branch_id | int | — | — |
| media_url | string | — | — |

---

### 5.8 Assign Message
```
POST /api/crm/channels/messages/<message_id>/assign
```
**Params:** `assigned_to_id` (int) — defaults to current user.

---

### 5.9 Reply to Message
```
POST /api/crm/channels/messages/<message_id>/reply
```
**Params:** `content` (string, required), `media_url`

Sets `replied_by_agent_at`, `waiting_customer_response=True`, auto-assigns `owner_id`.

---

### 5.10 Resolve Message
```
POST /api/crm/channels/messages/<message_id>/resolve
```

---

### 5.11 Transfer Message
```
POST /api/crm/channels/messages/<message_id>/transfer
```
**Params:** `new_owner_id` (int, required)

---

## 6. Analytics & Reports (`/api/crm/analytics/*`)

### 6.1 Dashboard Stats
```
POST /api/crm/analytics/dashboard_stats
```
**Params:** `branch_id`, `date_from`, `date_to`

**Response `data`:**
```json
{
  "total_customers": 1200,
  "active_customers": 850,
  "vip_customers": 45,
  "open_tickets": 23,
  "resolved_tickets_today": 8,
  "calls_today": 127,
  "avg_call_duration_seconds": 342,
  "pending_messages": 14,
  "overdue_tasks": 5
}
```

---

### 6.2 Channel Report
```
POST /api/crm/analytics/channel_report
```
**Response `data`:**
```json
{
  "channels": [
    {"channel": "whatsapp", "total_messages": 450, "pending": 12, "resolved": 438},
    {"channel": "instagram", "total_messages": 120, "pending": 3, "resolved": 117}
  ]
}
```

---

### 6.3 Employee KPI
```
POST /api/crm/analytics/employee_kpi
```
**Params:** `employee_id`, `branch_id`, `period_start`, `period_end`, `live` (bool — compute on-the-fly vs stored snapshot)

**Response `data`:**
```json
{
  "employee_id": 3,
  "employee_name": "Ali Hassan",
  "period_start": "2026-02-01T00:00:00",
  "period_end": "2026-02-28T23:59:59",
  "total_calls": 245,
  "answered_calls": 230,
  "total_messages": 512,
  "answered_messages": 498,
  "avg_frt_seconds": 65,
  "avg_ttr_seconds": 720,
  "late_messages": 8,
  "late_calls": 3,
  "conversions_to_order": 42
}
```

---

### 6.4 Branch Report
```
POST /api/crm/analytics/branch_report
```
**Params:** `date_from`, `date_to`

---

### 6.5 All Employees KPI (Supervisor)
```
POST /api/crm/analytics/all_employees_kpi
```
**Params:** `branch_id`, `period_start`, `period_end`

Returns array of KPI objects for every employee in the branch.

---

### 6.6 Supervisor Dashboard
```
POST /api/crm/analytics/supervisor_dashboard
```
**Params:** `branch_id`

**Response `data`:**
```json
{
  "agents": [
    {
      "user_id": 3, "name": "Ali",
      "open_conversations": 4,
      "calls_today": 12,
      "last_response": "2026-02-26T09:30:00",
      "sla_breached_count": 1
    }
  ],
  "unassigned_pending": 5,
  "overdue_tasks": 3,
  "high_priority_tickets": 2,
  "vip_activity": [...]
}
```

---

### 6.7 AI vs Human Report
```
POST /api/crm/analytics/ai_vs_human
```
**Params:** `branch_id`, `date_from`, `date_to`

---

### 6.8 Export KPI CSV
```
POST /api/crm/analytics/export_kpi
```
Returns CSV file download. **Params:** `branch_id`, `period_start`, `period_end`.

---

### 6.9 Audit Log
```
POST /api/crm/analytics/audit_log
```
**Params:** `page`, `per_page`, `action`, `user_id`, `customer_id`, `branch_id`, `date_from`, `date_to`

**`action` values (45 total):**
`customer_created` | `customer_updated` | `customer_deleted` | `customer_stage_moved` |
`call_created` | `call_ended` | `call_deleted` | `call_recording_attached` |
`ticket_created` | `ticket_status_changed` | `ticket_assigned` | `ticket_escalated` | `ticket_deleted` |
`task_created` | `task_status_changed` | `task_assigned` | `task_deleted` |
`message_created` | `message_replied` | `message_resolved` | `message_transferred` |
`article_created` | `article_deleted` | `notification_pushed` |
`po_created` | `po_deleted` | `vendor_created` | `vendor_deleted` | `container_created` |
`tag_created` | `tag_updated` | `tag_deleted` |
`stage_created` | `stage_updated` | `stage_deleted` |
`script_created` | `script_updated` | `script_deleted` |
`branch_created` | `branch_updated` | `branch_deleted` |
`qa_review_created` | `qa_review_submitted`

---

## 7. Knowledge Base (`/api/crm/kb/*`)

### 7.1 List Articles
```
POST /api/crm/kb/articles/list
```
**Params:** `page`, `per_page`, `category`, `branch_id`, `published_only`

**`category` values:** `document` | `policy` | `faq` | `announcement` | `training`

---

### 7.2 Search Articles
```
POST /api/crm/kb/articles/search
```
**Params:** `query`, `branch_id`, `limit`

---

### 7.3 Get Article
```
POST /api/crm/kb/articles/<article_id>
```

---

### 7.4 Create Article
```
POST /api/crm/kb/articles/create
```
**Params:** `title`, `category`, `content`, `title_ar`, `content_ar`, `branch_id`, `is_published`

---

### 7.5 Update Article
```
POST /api/crm/kb/articles/<article_id>/update
```

---

### 7.6 Delete Article
```
POST /api/crm/kb/articles/<article_id>/delete
```

---

### 7.7 List Notifications
```
POST /api/crm/kb/notifications/list
```
**Params:** `page`, `per_page`, `branch_id`

---

### 7.8 Push Notification
```
POST /api/crm/kb/notifications/push
```
**Params:** `title`, `body`, `branch_ids` (array[int]), `notification_type`

**`notification_type` values:** `announcement` | `alert` | `update`

---

## 8. Config (`/api/crm/config/*`)

### 8.1 Tags

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crm/config/tags/list` | POST | List tags. Params: `tag_type` |
| `/api/crm/config/tags/create` | POST | Params: `name`, `name_ar`, `tag_type`, `color`, `sequence` |
| `/api/crm/config/tags/<id>/update` | POST | Update tag |
| `/api/crm/config/tags/<id>/delete` | POST | Soft-delete tag |

**`tag_type` values:** `vip` | `lead_quality` | `segment` | `custom`

### 8.2 Customer Stages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crm/config/stages/list` | POST | List all stages ordered by sequence |
| `/api/crm/config/stages/create` | POST | Params: `name`, `stage_type`, `name_ar`, `sequence` |
| `/api/crm/config/stages/<id>/update` | POST | Update stage |
| `/api/crm/config/stages/<id>/delete` | POST | Soft-delete stage |

**`stage_type` values:** `lead` | `active` | `vip` | `inactive` | `churned`

### 8.3 Call Scripts / FAQs

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/crm/config/scripts/list` | POST | Params: `category`, `branch_id`, `search` |
| `/api/crm/config/scripts/<id>` | POST | Get single script |
| `/api/crm/config/scripts/create` | POST | Params: `title`, `category`, `question`, `answer`, `branch_id`, `sequence` |
| `/api/crm/config/scripts/<id>/update` | POST | Update script |
| `/api/crm/config/scripts/<id>/delete` | POST | Soft-delete script |

**`category` values:** `faq` | `objection` | `greeting` | `closing` | `escalation`

---

## 9. Branches (`/api/crm/branches/*`)

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/branches/list` | — | List all active branches |
| `/api/crm/branches/<id>` | — | Get branch detail |
| `/api/crm/branches/create` | `name`, `name_ar`, `code`, `city`, `address`, `phone`, `email`, `manager_id` | Create branch |
| `/api/crm/branches/<id>/update` | any field | Update branch |
| `/api/crm/branches/<id>/user_assign` | `user_ids: array[int]` | Set authorized users |
| `/api/crm/branches/<id>/delete` | — | Soft-delete branch |

---

## 10. Supply Chain (`/api/crm/supply/*`)

### 10.1 Vendors

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/supply/vendors/list` | `page`, `per_page`, `search`, `division` | List vendors |
| `/api/crm/supply/vendors/<id>` | — | Get vendor card |
| `/api/crm/supply/vendors/create` | `name`, `division`, `contact_name`, `phone`, `email`, `whatsapp`, `wechat`, `telegram`, `country_id`, `payment_terms`, `currency_id`, `lead_time_days`, `notes` | Create vendor |
| `/api/crm/supply/vendors/<id>/update` | any field | Update vendor |
| `/api/crm/supply/vendors/<id>/delete` | — | Soft-delete vendor |

**`division` values:** `europe` | `china` | `other`

---

### 10.2 Purchase Orders

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/supply/po/list` | `page`, `per_page`, `status`, `vendor_id` | List POs |
| `/api/crm/supply/po/<id>` | — | Get PO with lines |
| `/api/crm/supply/po/create` | `name`, `vendor_id`*, `division`, `container_id`, `branch_id`, `currency_id` | Create PO |
| `/api/crm/supply/po/<id>/update` | any field | Update PO header |
| `/api/crm/supply/po/<id>/delete` | — | Soft-delete PO |
| `/api/crm/supply/po/suggested` | — | List suggested POs |

**`status` values:** `draft` | `confirmed` | `shipped` | `received` | `cancelled`

---

### 10.3 PO Lines

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/supply/po/<id>/lines` | — | List all lines |
| `/api/crm/supply/po/<id>/lines/add` | `product_name`, `item_code`, `uom`, `quantity`, `unit_price`, `currency_id`, `min_qty`, `max_qty` | Add line |
| `/api/crm/supply/po/<id>/lines/<line_id>/update` | any field | Update line |
| `/api/crm/supply/po/<id>/lines/<line_id>/delete` | — | Hard-delete line |

---

### 10.4 Containers

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/supply/containers/list` | `page`, `per_page`, `status`, `division` | List containers |
| `/api/crm/supply/containers/<id>` | — | Get container |
| `/api/crm/supply/containers/create` | `name`, `container_number`, `bl_number`, `status`, `division`, `clearance_company`, `origin_location`, `departure_date`, `eta`, `tracking_url`, `assigned_user_id`, `po_uploaded_by_id` | Create container |
| `/api/crm/supply/containers/<id>/update` | any field | Update container |
| `/api/crm/supply/containers/<id>/delete` | — | Soft-delete |
| `/api/crm/supply/containers/<id>/clearance_delivered` | — | Mark clearance info delivered (sets highlight flag + timestamp + who) |

**`status` values:** `waiting` | `active` | `at_port` | `completed`

**Container response includes:**
```json
{
  "id": 1,
  "name": "CNT-2026-001",
  "container_number": "MSCU1234567",
  "bl_number": "BL123456",
  "clearance_company": "Al-Fares Clearance",
  "origin_location": "Shanghai",
  "departure_date": "2026-01-15",
  "eta": "2026-02-20",
  "status": "at_port",
  "division": "china",
  "tracking_url": "https://searates.com/...",
  "clearance_info_delivered": true,
  "clearance_info_delivered_at": "2026-02-18T10:30:00",
  "clearance_info_delivered_by": "Mohammed",
  "assigned_user_name": "Ali Haider",
  "po_uploaded_by_name": "Maryam",
  "attachment_count": 3,
  "notes": ""
}
```

---

## 11. Workforce (`/api/crm/shifts/*` / `/api/crm/attendance/*` / `/api/crm/templates/*`)

### 11.1 Shifts

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/shifts/list` | `branch_id` | List shifts |
| `/api/crm/shifts/create` | `name`, `branch_id`*, `shift_type`, `start_time`, `end_time`, `user_ids`, `name_ar` | Create shift |
| `/api/crm/shifts/<id>/update` | any field | Update shift |
| `/api/crm/shifts/<id>/delete` | — | Soft-delete |

**`shift_type` values:** `morning` | `evening` | `night` | `split`

---

### 11.2 Attendance

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/attendance/check_in` | `branch_id`, `shift_id`, `work_type`, `ip_address`, `device_type`, `location_lat`, `location_lng`, `location_label` | Check in |
| `/api/crm/attendance/check_out` | `notes` | Check out (closes open record) |
| `/api/crm/attendance/list` | `page`, `per_page`, `branch_id`, `employee_id`, `date_from`, `date_to`, `work_type` | List records |
| `/api/crm/attendance/live_status` | `branch_id` | Who is currently checked in |

**`work_type` values:** `office` | `remote` | `field`

---

### 11.3 Message Templates

| Endpoint | Params | Description |
|----------|--------|-------------|
| `/api/crm/templates/list` | `channel`, `category`, `branch_id` | List templates |
| `/api/crm/templates/create` | `name`*, `channel`*, `body`*, `category`, `body_ar`, `branch_id`, `requires_approval` | Create template |
| `/api/crm/templates/<id>/update` | any field | Update |
| `/api/crm/templates/<id>/delete` | — | Soft-delete |
| `/api/crm/templates/<id>/render` | `customer_id` | Render with variable substitution (`{customer_name}`, `{agent_name}`, `{branch_name}`) |

---

## 12. Price List & Catalog (`/api/crm/pricelist/*`)

### 12.1 List Product Categories
```
POST /api/crm/pricelist/categories
```
Returns brand/category list for filter dropdowns.

---

### 12.2 List Products
```
POST /api/crm/pricelist/products
```
**Params:** `page`, `per_page`, `search`, `category_id`, `uom_id`, `pricelist_id`, `new_releases_only`, `discount_only`

---

### 12.3 Get Product Detail
```
POST /api/crm/pricelist/products/<product_id>
```
**Params:** `pricelist_id`

Returns: UoM prices, warehouse stock, default code, foreign name.

---

### 12.4 List Pricelists
```
POST /api/crm/pricelist/pricelists
```

---

### 12.5 Create Requested Item
```
POST /api/crm/pricelist/requested_items/create
```
**Params:** `customer_id`*, `product_name`*, `notes`

---

### 12.6 List Requested Items
```
POST /api/crm/pricelist/requested_items
```
**Params:** `page`, `per_page`, `customer_id`, `status`

**`status` values:** `pending` | `notified` | `fulfilled` | `cancelled`

---

### 12.7 Update Requested Item Status
```
POST /api/crm/pricelist/requested_items/<item_id>/update_status
```
**Params:** `status` (required)

---

### 12.8 Delete Requested Item
```
POST /api/crm/pricelist/requested_items/<item_id>/delete
```

---

## 13. POS Bridge (`/api/crm/pos/*`)

> Requires `pos_perfume_custom` module installed. All endpoints return `success: false` with error message if POS module is unavailable.

### 13.1 Invoice Context (Pre-fill Create Invoice)
```
POST /api/crm/pos/invoice_context
```
**Params:** `call_id`, `customer_id`

**Response `data`:**
```json
{
  "pricelists": [{"id": 1, "name": "Standard USD", "currency_id": 2}],
  "default_pricelist_id": 1,
  "warehouses": [{"id": 1, "name": "Main Warehouse", "code": "WH"}],
  "invoice_types": [
    {"key": "1", "label": "زبون محل"},
    {"key": "2", "label": "شركات توصيل"}
  ],
  "exchange_rate": 1470.0,
  "currency": "USD",
  "secondary_currency": "IQD",
  "partner_id": 45,
  "last_order": {
    "id": 55,
    "name": "PO/2026/00055",
    "date": "2026-02-10",
    "amount_total": 250.00,
    "state": "done"
  }
}
```

---

### 13.2 Product Search (POS)
```
POST /api/crm/pos/products
```
**Params:** `query`, `pricelist_id`, `limit`, `offset`

---

### 13.3 Product Detail (POS)
```
POST /api/crm/pos/product_detail
```
**Params:** `product_id`, `pricelist_id`

Returns: UoMs, warehouses with stock qty, price.

---

### 13.4 UoM Price
```
POST /api/crm/pos/uom_price
```
**Params:** `product_id`, `pricelist_id`, `uom_id`

---

### 13.5 Create Order (Invoice)
```
POST /api/crm/pos/orders/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| partner_id | int | ✅ |
| call_id | int | — | Links order to CRM call |
| pricelist_id | int | — |
| invoice_type | string | — | `1`–`8` |
| exchange_rate | float | — |
| order_lines | array | — | See below |

**`order_lines` item:**
```json
{
  "product_id": 10,
  "quantity": 2.0,
  "unit_price": 45.00,
  "product_uom_id": 1,
  "warehouse_id": 1,
  "discount_percent": 0.0,
  "custom_product_name": "",
  "sequence": 10
}
```

---

### 13.6 Get Order
```
POST /api/crm/pos/orders/<order_id>
```

---

### 13.7 Customer Order History
```
POST /api/crm/pos/customer_orders
```
**Params:** `partner_id`*, `limit`

---

## 14. Delivery (`/api/crm/delivery/*`)

### 14.1 Customer Orders
```
POST /api/crm/delivery/customer_orders
```
**Params:** `customer_id` or `partner_id`, `page`, `per_page`, `state`

---

### 14.2 Get Order Detail
```
POST /api/crm/delivery/order/<order_id>
```
Returns full POS order with lines and delivery status.

---

### 14.3 Search Orders
```
POST /api/crm/delivery/orders/search
```
**Params:** `query`, `limit`, `branch_id`

---

## 15. QA Reviews (`/api/crm/qa/*`)

### 15.1 List Reviews
```
POST /api/crm/qa/reviews
```
**Params:** `page`, `limit`, `review_type`, `agent_id`, `reviewer_id`, `status`, `branch_id`

**`status` values:** `draft` | `submitted` | `acknowledged`
**`review_type` values:** `call` | `message`

---

### 15.2 Get Review
```
POST /api/crm/qa/reviews/<review_id>
```

---

### 15.3 Create Review
```
POST /api/crm/qa/reviews/create
```
**Params:**
| Field | Type | Required |
|-------|------|----------|
| review_type | string | ✅ | `call` or `message` |
| call_id | int | — | For call reviews |
| conversation_id | string | — | For message reviews |
| customer_id | int | — |
| agent_id | int | — |
| branch_id | int | — |
| score | float | — | 0–100 |
| greeting_score | float | — | Sub-score 0–100 |
| product_knowledge_score | float | — | Sub-score 0–100 |
| problem_solving_score | float | — | Sub-score 0–100 |
| professionalism_score | float | — | Sub-score 0–100 |
| compliance_score | float | — | Sub-score 0–100 |
| issues_found | string | — |
| qa_notes | string | — |
| feedback_to_agent | string | — |
| listen_duration_seconds | int | — |

**Note:** `review_number` auto-generated (QA-00001 format).

---

### 15.4 Update Review (Draft Only)
```
POST /api/crm/qa/reviews/<review_id>/update
```

---

### 15.5 Submit Review
```
POST /api/crm/qa/reviews/<review_id>/submit
```
Locks the review from further editing.

---

### 15.6 QA Stats
```
POST /api/crm/qa/stats
```
**Params:** `reviewer_id`, `agent_id`, `branch_id`, `date_from`, `date_to`

**Response `data`:**
```json
{
  "total_reviews": 45,
  "avg_score": 84.3,
  "total_listen_seconds": 18000,
  "call_reviews": 30,
  "message_reviews": 15
}
```

---

## Appendix A — Common Response Codes

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Always returned for JSON-RPC (check `result.success` for logic errors) |
| 404 | Route not found |
| 405 | Wrong HTTP method |

| `success` | `error` | Meaning |
|-----------|---------|---------|
| true | — | Successful |
| false | "Unauthorized" | Missing or invalid JWT token |
| false | "Record not found" | ID doesn't exist or was soft-deleted |
| false | "field is required" | Missing required parameter |
| false | any string | Unexpected server error |

---

## Appendix B — Field Type Reference

| Type | JSON representation |
|------|---------------------|
| Char / Text | `"string"` |
| Integer | `123` |
| Float | `123.45` |
| Boolean | `true` / `false` |
| Date | `"2026-02-26"` |
| Datetime | `"2026-02-26T09:30:00"` (ISO 8601) |
| Many2one | `id: int` |
| Many2many | `[id1, id2, ...]` |
| Binary | Not returned in list — use dedicated endpoint |

---

## Appendix C — Sequence Numbers

| Model | Format | Example |
|-------|--------|---------|
| `lugal.crm.ticket` | `TKT-NNNNN` | `TKT-00042` |
| `lugal.crm.qa.review` | `QA-NNNNN` | `QA-00007` |

Sequences can be reset or reconfigured by Admin from **Settings → Technical → Sequences**.

---

## Appendix D — Security Groups

| Group | Description |
|-------|-------------|
| `CRM Agent` | Handle calls, messages, create tickets/tasks |
| `CRM Supervisor` | All Agent + view all agents data, assign, manage follow-ups |
| `CRM Manager` | All Supervisor + settings, branches, supply chain, full analytics |
| `CRM General Manager` | Full access including delete, export, audit log |
| `CRM QA Auditor` | Listen to recordings, review messages, score calls |
| `CRM QA Supervisor` | All QA + manage QA assignments, view QA productivity |
