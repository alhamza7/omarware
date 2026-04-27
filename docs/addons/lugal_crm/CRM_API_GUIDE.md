# Lugal CRM — Complete API Guide

> **Base URL:** `https://your-odoo-instance.com`
> **Auth:** JWT token sent in the **HTTP Header**: `Authorization: Bearer <token>`
> **Format:** All requests and responses are `Content-Type: application/json` (JSON-RPC style)
> **Request shape:** `{ "jsonrpc": "2.0", "method": "call", "params": { ...your params... } }`
> **Response shape:** `{ "result": { "success": true/false, "data": {...}, "error": "..." } }`

---

## Authentication

### 1. Login to get JWT token
```http
POST /api/auth/login
Content-Type: application/json
Body: { "jsonrpc": "2.0", "method": "call", "params": { "login": "user@example.com", "password": "pass" } }

Response: { "result": { "success": true, "data": { "access_token": "eyJ...", "refresh_token": "eyJ..." } } }
```

### 2. Use token in every subsequent request
```http
POST /api/crm/customers/list
Content-Type: application/json
Authorization: Bearer eyJ...

Body: { "jsonrpc": "2.0", "method": "call", "params": { "page": 1, "per_page": 50 } }
```

> ⚠️ **Important:** The token goes in the **Authorization header**, NOT in the request body params.

---

## 1. Customers — `/api/crm/customers/*`

### 1.1 List Customers
```http
POST /api/crm/customers/list
Params:
  page          int     (default 1)
  per_page      int     (default 50)
  search        string  (name / phone / email)
  stage_id      int
  branch_id     int
  vip_only      bool
  token         string  (required)

Response:
{
  "success": true,
  "data": {
    "items": [ { ...customer }, ... ],
    "total": 120,
    "page": 1,
    "per_page": 50
  }
}
```

### Customer Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Customer ID |
| `name` | string | Full name |
| `name_ar` | string | Arabic name |
| `phone_1/2/3` | string | Phone numbers |
| `email` | string | Email |
| `stage_id` | int | Pipeline stage |
| `stage_type` | string | `lead / interested / active / vip / dormant` |
| `vip_status` | bool | VIP flag |
| `lifetime_value` | float | Total purchases value |
| `credit_debt` | float | Outstanding balance |
| `loyalty_points` | int | Loyalty points |
| `last_call_date` | ISO datetime | |
| `last_purchase_date` | ISO datetime | |
| `branch_ids` | int[] | Branches |
| `channel_identities` | array | Social handles (on get only) |

### 1.2 Search Customers
```http
POST /api/crm/customers/search
Params: query (min 2 chars), limit
```

### 1.3 Get Customer
```http
POST /api/crm/customers/<id>
Response: customer object + channel_identities[]
```

### 1.4 Create Customer
```http
POST /api/crm/customers/create
Params: name (required), name_ar, phone_1, phone_2, email, address,
        stage_id, vip_status, branch_ids, tag_ids, referral_source...
```

### 1.5 Update Customer
```http
POST /api/crm/customers/<id>/update
Params: any writable field
```

### 1.6 Delete Customer
```http
POST /api/crm/customers/<id>/delete
```

### 1.7 Kanban Move
```http
POST /api/crm/customers/<id>/kanban_move
Params: stage_id (required)
```

### 1.8 360° Activity Timeline
```http
POST /api/crm/customers/<id>/activity
Params: limit (default 50), offset (default 0)

Response:
{
  "success": true,
  "data": {
    "items": [
      { "type": "call", "id": 1, "timestamp": "2025-01-01T10:00:00", "summary": "inbound — resolved", "recording_url": "", ... },
      { "type": "interaction", "id": 2, "timestamp": "...", "summary": "Quick Note", ... },
      { "type": "message", "id": 3, "timestamp": "...", "channel": "whatsapp", "direction": "inbound", ... },
      { "type": "ticket", "id": 4, "timestamp": "...", "title": "Complaint", "status": "open", ... }
    ],
    "total": 45
  }
}
```

### 1.9 Customer Call History
```http
POST /api/crm/customers/<id>/calls
Params: page, per_page
```

### 1.10 Customer Ticket History
```http
POST /api/crm/customers/<id>/tickets
Params: page, per_page
```

### 1.11 Add Quick Note
```http
POST /api/crm/customers/<id>/note/add
Params: note (required string)
```

### 1.12 Channel Identity — Add
```http
POST /api/crm/customers/<id>/channel_identity/add
Params: channel (whatsapp|instagram|telegram|tiktok|x|snapchat|email|website), handle, is_primary
```

### 1.13 Channel Identity — Update
```http
POST /api/crm/customers/<id>/channel_identity/<ci_id>/update
Params: channel, handle, is_primary, is_verified
```

### 1.14 Channel Identity — Delete
```http
POST /api/crm/customers/<id>/channel_identity/<ci_id>/delete
```

---

## 2. Calls — `/api/crm/calls/*`

### 2.1 List Calls
```http
POST /api/crm/calls/list
Params: page, per_page, customer_id, branch_id, agent_id,
        date_from (ISO), date_to (ISO), outcome
```

### Call Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | |
| `call_type` | string | `inbound / outbound` |
| `caller_number` | string | |
| `duration_seconds` | int | |
| `outcome` | string | `resolved / callback / escalated / no_answer` |
| `notes` | string | |
| `recording_url` | string | URL to audio file |
| `catalogue_sent` | bool | |
| `catalogue_sent_via` | string | `whatsapp / email / telegram` |
| `pos_order_name` | string | Linked POS order |
| `qa_score` | float | QA evaluation score |

### 2.2 Get Call
```http
POST /api/crm/calls/<call_id>
```

### 2.3 Create Call (Start)
```http
POST /api/crm/calls/create
Params: customer_id (required), call_type, channel, caller_number, branch_id
Response: call object (financial snapshot included)
```

### 2.4 End Call
```http
POST /api/crm/calls/<call_id>/end
Params: duration_seconds, outcome, notes, catalogue_sent,
        catalogue_sent_via, recording_url
```

### 2.5 Update Call
```http
POST /api/crm/calls/<call_id>/update
Params: notes, ai_summary, qa_score, issues_found, outcome,
        recording_url, catalogue_sent, catalogue_sent_via
```

### 2.6 Attach Recording
```http
POST /api/crm/calls/<call_id>/attach_recording
Params: recording_url (required)
```

### 2.7 Delete Call
```http
POST /api/crm/calls/<call_id>/delete
```

### 2.8 Queue — List
```http
POST /api/crm/calls/queue/list
Params: status (default: waiting)
```

### 2.9 Queue — Add
```http
POST /api/crm/calls/queue/add
Params: customer_id, channel, caller_number
Response: { id, queue_position }
```

### 2.10 Queue — Assign
```http
POST /api/crm/calls/queue/<queue_id>/assign
```

---

## 3. Tickets — `/api/crm/tickets/*`

### 3.1 List Tickets
```http
POST /api/crm/tickets/list
Params: page, per_page, customer_id, branch_id, status, priority, assigned_to_id
```

### Ticket Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `title` | string | |
| `status` | string | `open / in_progress / resolved / closed / stale` |
| `priority` | string | `low / medium / high / urgent` |
| `sla_deadline` | ISO datetime | |
| `first_response_at` | ISO datetime | Auto-set on first assign |
| `resolved_at` | ISO datetime | Auto-set on resolve |

### 3.2 Get Ticket
```http
POST /api/crm/tickets/<ticket_id>
Params: include_notes (bool, default false)
```

### 3.3 Search Tickets
```http
POST /api/crm/tickets/search
Params: query, branch_id, limit
```

### 3.4 Create / Update / Delete / Update Status / Assign / Escalate
```http
POST /api/crm/tickets/create
POST /api/crm/tickets/<id>/update
POST /api/crm/tickets/<id>/delete
POST /api/crm/tickets/<id>/update_status   { status }
POST /api/crm/tickets/<id>/assign          { assigned_to_id }
POST /api/crm/tickets/<id>/escalate        { escalated_to_id }
```

### 3.5 Notes
```http
POST /api/crm/tickets/<id>/note/add   { body }
POST /api/crm/tickets/<id>/notes      → items[]
```

---

## 4. Omnichannel — `/api/crm/channels/*`

### 4.1 Channel Config List / Create / Update
```http
POST /api/crm/channels/config_list               { branch_id }
POST /api/crm/channels/config/create             { channel, branch_id, sla_threshold_seconds, work_hours_start, work_hours_end, ... }
POST /api/crm/channels/config/<id>/update        { sla_threshold_seconds, work_hours_start, work_hours_end, assigned_user_ids[], ... }
```

### Channel Config Fields
| Field | Type | Description |
|-------|------|-------------|
| `sla_threshold_seconds` | int | Seconds before SLA breach (default 300) |
| `work_hours_start` | float | E.g. `8.0` = 08:00 |
| `work_hours_end` | float | E.g. `18.0` = 18:00 |
| `is_free_for_all` | bool | Any agent can handle |

### 4.2 Message Inbox
```http
POST /api/crm/channels/messages/list
Params: page, per_page, customer_id, channel, status,
        branch_id, assigned_to_id, sla_breached (bool)
```

### Message Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `direction` | string | `inbound / outbound` |
| `replied_by_agent_at` | ISO datetime | First agent reply time (FRT) |
| `owner_id` | int | Conversation owner |
| `sla_breached` | bool | SLA exceeded |
| `waiting_customer_response` | bool | Agent replied, waiting customer |
| `status` | string | `pending / assigned / resolved` |

### 4.3 Full Conversation Thread
```http
POST /api/crm/channels/messages/conversation
Params: conversation_id (required)
Response: items[] sorted by sent_at ASC
```

### 4.4 Create / Reply / Assign / Resolve / Transfer
```http
POST /api/crm/channels/messages/create
  { customer_id, channel, content, direction, conversation_id, branch_id }

POST /api/crm/channels/messages/<id>/reply
  { content, media_url }
  → Creates outbound message, sets FRT, ownership, waiting_customer_response

POST /api/crm/channels/messages/<id>/assign
  { assigned_to_id }

POST /api/crm/channels/messages/<id>/resolve
  → Resolves all messages in same conversation

POST /api/crm/channels/messages/<id>/transfer
  { new_owner_id }
```

---

## 5. Analytics — `/api/crm/analytics/*`

### 5.1 Main Dashboard
```http
POST /api/crm/analytics/dashboard_stats
Params: branch_id, date_from, date_to

Response: {
  customers: { total, vip, new_today },
  tickets: { open, resolved, high_priority },
  calls: { total, missed },
  messages: { inbound, pending_reply, sla_breached },
  tasks: { overdue }
}
```

### 5.2 Channel Report
```http
POST /api/crm/analytics/channel_report
Params: branch_id, date_from, date_to

Response: {
  channels: [ { channel, messages, resolved, sla_breached }, ... ],
  calls: { total, inbound, outbound, missed }
}
```

### 5.3 Branch Report
```http
POST /api/crm/analytics/branch_report
Params: date_from, date_to

Response: { branches: [ { branch_id, branch_name, customers, open_tickets, calls, messages }, ... ] }
```

### 5.4 Employee KPI
```http
POST /api/crm/analytics/employee_kpi
Params: employee_id, branch_id, period_start, period_end, live (bool)
  live=false → last stored snapshot
  live=true  → computed in real-time from raw data
```

### 5.5 All Employees KPI (Supervisor)
```http
POST /api/crm/analytics/all_employees_kpi
Params: branch_id, period_start, period_end
Response: { items: [ ...kpi_per_employee ] }
```

### 5.6 Supervisor Real-Time Dashboard
```http
POST /api/crm/analytics/supervisor_dashboard
Params: branch_id

Response: {
  agent_conversations: [ { agent_id, agent_name, open_conversations } ],
  unassigned_messages: [ { id, channel, customer_name, content, sent_at, sla_breached } ],
  unassigned_count: int,
  overdue_tasks: [ { id, title, due_date, assigned_to, customer_name } ],
  overdue_count: int,
  high_priority_tickets: [ { id, title, status, priority, sla_deadline } ],
  dormant_vip_customers: [ { id, name, last_call_date, account_manager } ]
}
```

### 5.7 AI vs Human Report
```http
POST /api/crm/analytics/ai_vs_human
Params: branch_id, date_from, date_to

Response: {
  total_inbound: int,
  human_replied: int,
  ai_resolved: int,
  unresolved: int,
  human_pct: float,
  ai_pct: float
}
```

### 5.8 Export KPI (CSV)
```http
POST /api/crm/analytics/export_kpi
Note: Returns CSV file (Content-Type: text/csv), NOT JSON
Params (form): branch_id, period_start, period_end
```

---

## 6. Knowledge Base — `/api/crm/kb/*`

### 6.1 Articles
```http
POST /api/crm/kb/articles/list      { page, per_page, category, branch_id, published_only }
POST /api/crm/kb/articles/search    { query, branch_id, limit }
POST /api/crm/kb/articles/<id>
POST /api/crm/kb/articles/create    { title, title_ar, category, content, content_ar, branch_id, is_published }
POST /api/crm/kb/articles/<id>/update
POST /api/crm/kb/articles/<id>/delete
```

**Categories:** `policy / journal / event / faq / idea / circular / training / document`

### 6.2 Notifications
```http
POST /api/crm/kb/notifications/list    { page, per_page, branch_id }
POST /api/crm/kb/notifications/push    { title, body, branch_ids[], notification_type }
```

---

## 7. Branches — `/api/crm/branches/*`

```http
POST /api/crm/branches/list
POST /api/crm/branches/<id>
POST /api/crm/branches/create       { name, name_ar, code, city, address, phone, email, manager_id }
POST /api/crm/branches/<id>/update
POST /api/crm/branches/<id>/user_assign   { user_ids[] }
```

---

## 8. Supply Chain — `/api/crm/supply/*`

### 8.1 Containers
```http
POST /api/crm/supply/containers/list        { page, per_page, status, division }
POST /api/crm/supply/containers/create      { name, container_number, bl_number, status, division, ... }
POST /api/crm/supply/containers/<id>
POST /api/crm/supply/containers/<id>/update
```

**Container statuses:** `waiting / active / at_port / completed`

### 8.2 Purchase Orders
```http
POST /api/crm/supply/po/list                { page, per_page, status, vendor_id }
POST /api/crm/supply/po/create              { name, vendor_id, division, container_id, branch_id, currency_id }
POST /api/crm/supply/po/<id>                → includes lines[]
POST /api/crm/supply/po/<id>/update
POST /api/crm/supply/po/<id>/delete
POST /api/crm/supply/po/suggested
```

### 8.3 PO Lines
```http
POST /api/crm/supply/po/<id>/lines
POST /api/crm/supply/po/<id>/lines/add           { product_name, item_code, uom, quantity, unit_price, currency_id, min_qty, max_qty }
POST /api/crm/supply/po/<id>/lines/<line_id>/update
POST /api/crm/supply/po/<id>/lines/<line_id>/delete
```

### 8.4 Vendors
```http
POST /api/crm/supply/vendors/list           { page, per_page, search, division }
POST /api/crm/supply/vendors/create         { name, division, phone, email, whatsapp, wechat, telegram, ... }
POST /api/crm/supply/vendors/<id>
POST /api/crm/supply/vendors/<id>/update
POST /api/crm/supply/vendors/<id>/delete
```

**Vendor special fields:** `whatsapp`, `wechat`, `telegram`, `lead_time_days`, `payment_terms`

---

## 9. Price List — `/api/crm/pricelist/*`

### 9.1 Categories (Brands)
```http
POST /api/crm/pricelist/categories
Response: { items: [ { id, name, parent_id } ] }
```

### 9.2 Pricelists
```http
POST /api/crm/pricelist/pricelists
Response: { items: [ { id, name, currency } ] }
```

### 9.3 Products
```http
POST /api/crm/pricelist/products
Params: page, per_page, search, category_id, uom_id,
        pricelist_id, discount_only (bool)

Response: {
  items: [
    {
      id, name, foreign_name, item_code,
      category_id, category_name,
      uom_name, price, currency,
      image_url,
      available_uoms: [ { uom_id, uom_name, price } ]
    }
  ]
}
```

### 9.4 Product Detail
```http
POST /api/crm/pricelist/products/<id>
Params: pricelist_id
Response: product + qty_on_hand + qty_reserved + all UoM prices
```

### 9.5 Requested Items (Out of Catalog)
```http
POST /api/crm/pricelist/requested_items
  Params: page, per_page, customer_id, status

POST /api/crm/pricelist/requested_items/create
  Params: customer_id, product_name, notes
```

**Requested item statuses:** `pending → in_stock → notified → fulfilled`

---

## 10. Delivery Tracking — `/api/crm/delivery/*`

```http
POST /api/crm/delivery/customer_orders
  Params: customer_id OR partner_id, page, per_page, state

POST /api/crm/delivery/order/<order_id>
  Response: order + lines[] + deliveries[] (stock.picking)

POST /api/crm/delivery/orders/search
  Params: query, limit
```

---

## 11. POS Bridge — `/api/crm/pos/*`

> Requires `pos_perfume_custom` module installed.

```http
POST /api/crm/pos/invoice_context
  Params: customer_id (CRM), branch_id
  Response: { partner, warehouses[], pricelists[], currencies[] }

POST /api/crm/pos/products
  Params: pricelist_id, warehouse_id, search, page, per_page

POST /api/crm/pos/product_detail
  Params: product_id, pricelist_id, warehouse_id

POST /api/crm/pos/uom_price
  Params: product_id, uom_id, pricelist_id

POST /api/crm/pos/orders/create
  Params: customer_id, pricelist_id, warehouse_id, lines[]
          line: { product_id, uom_id, quantity, unit_price, discount_percent }

POST /api/crm/pos/order_get
  Params: order_id

POST /api/crm/pos/customer_orders
  Params: customer_id, page, per_page
```

---

## 12. Workforce — `/api/crm/shifts/*` , `/api/crm/attendance/*` , `/api/crm/templates/*`

### 12.1 Shifts
```http
POST /api/crm/shifts/list                   { branch_id }
POST /api/crm/shifts/create                 { name, branch_id, shift_type, start_time, end_time, user_ids[] }
POST /api/crm/shifts/<id>/update
POST /api/crm/shifts/<id>/delete
```
**shift_types:** `morning / evening / night / custom`

### 12.2 Attendance
```http
POST /api/crm/attendance/check_in
  Params: branch_id, shift_id, work_type (office/remote/field),
          ip_address, device_type, location_lat, location_lng, location_label

POST /api/crm/attendance/check_out
  Params: notes

POST /api/crm/attendance/list
  Params: page, per_page, branch_id, employee_id, date_from, date_to, work_type

POST /api/crm/attendance/live_status
  Params: branch_id
  Response: { online: [ { employee_id, employee_name, check_in, work_type, location_label } ], count }
```

### 12.3 Message Templates
```http
POST /api/crm/templates/list
  Params: channel, category, branch_id
  → Returns active templates for given channel (also returns channel='any')

POST /api/crm/templates/create
  Params: name, channel, body, body_ar, category, branch_id, requires_approval

POST /api/crm/templates/<id>/update
POST /api/crm/templates/<id>/delete

POST /api/crm/templates/<id>/render
  Params: customer_id (optional)
  Response: { rendered, rendered_ar }
  Variables in body: {customer_name}, {agent_name}, {branch_name}
```

**Template channels:** `whatsapp / telegram / email / any`
**Template categories:** `greeting / followup / catalogue / pricing / support / closing / other`
**Approval statuses:** `draft / pending / approved / rejected`

---

## 13. Tasks — `/api/crm/tasks/*`

Model: `lugal.crm.task` — Follow-up tasks assigned to agents by supervisors.

```http
POST /api/crm/tasks/list
  Params: page, per_page, customer_id, branch_id, assigned_to_id,
          status (open/in_progress/done/overdue), priority (low/medium/high/urgent),
          overdue_only (bool)
  Response: { items: [...tasks], total, page, per_page }

POST /api/crm/tasks/<id>
  Response: { ...task }

POST /api/crm/tasks/create
  Params: title (required), customer_id, assigned_to_id, branch_id,
          description, priority, due_date, reminder_date

POST /api/crm/tasks/<id>/update
  Params: title, description, priority, due_date, reminder_date,
          assigned_to_id, branch_id, customer_id

POST /api/crm/tasks/<id>/update_status
  Params: status (open / in_progress / done / overdue)

POST /api/crm/tasks/<id>/assign
  Params: assigned_to_id

POST /api/crm/tasks/<id>/delete

POST /api/crm/tasks/my
  Params: page, per_page, status
  → Returns tasks assigned to the authenticated user
```

### Task Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | |
| `title` | string | |
| `description` | string | |
| `customer_id` / `customer_name` | int/string | Linked customer |
| `assigned_to_id` / `assigned_to_name` | int/string | |
| `created_by_id` / `created_by_name` | int/string | |
| `branch_id` / `branch_name` | int/string | |
| `status` | string | `open` `in_progress` `done` `overdue` |
| `priority` | string | `low` `medium` `high` `urgent` |
| `due_date` | datetime ISO | |
| `reminder_date` | datetime ISO | |

---

## 14. Config / Lookup Data — `/api/crm/config/*`

### 14.1 Tags — `/api/crm/config/tags/*`

Model: `lugal.crm.tag` — Customer tags (VIP, Lead, Loyal, etc.)

```http
POST /api/crm/config/tags/list
  Params: tag_type (vip/enterprise/lead/loyal/stale/active/custom)

POST /api/crm/config/tags/create
  Params: name (required), name_ar, tag_type, color, sequence

POST /api/crm/config/tags/<id>/update
  Params: name, name_ar, tag_type, color, sequence

POST /api/crm/config/tags/<id>/delete
```

**Tag types:** `vip / enterprise / lead / loyal / stale / active / custom`

### 14.2 Customer Pipeline Stages — `/api/crm/config/stages/*`

Model: `lugal.crm.customer.stage` — Configurable pipeline stages.

```http
POST /api/crm/config/stages/list
  Response: [ { id, name, name_ar, stage_type, sequence }, ... ]

POST /api/crm/config/stages/create
  Params: name (required), name_ar, stage_type, sequence

POST /api/crm/config/stages/<id>/update
  Params: name, name_ar, stage_type, sequence

POST /api/crm/config/stages/<id>/delete
```

**Stage types:** `lead / interested / active / vip / dormant`

### 14.3 Call Scripts / FAQ — `/api/crm/config/scripts/*`

Model: `lugal.crm.call.script` — Agent guidance during calls.

```http
POST /api/crm/config/scripts/list
  Params: category (faq/guided_workflow/objection_handling), branch_id, search
  → branch_id returns scripts for that branch + global scripts (no branch)

POST /api/crm/config/scripts/<id>

POST /api/crm/config/scripts/create
  Params: title (required), category, question, answer, branch_id, sequence

POST /api/crm/config/scripts/<id>/update
  Params: title, category, question, answer, branch_id, sequence, is_active

POST /api/crm/config/scripts/<id>/delete
```

**Script categories:** `faq / guided_workflow / objection_handling`

---

## 15. Interactions — `/api/crm/interactions/*`

Model: `lugal.crm.interaction` — Full activity log per customer.

```http
POST /api/crm/customers/<customer_id>/interactions
  Params: page, per_page, interaction_type (call/message/email/visit/note)
  Response: { items: [...interactions], total, page, per_page }

POST /api/crm/interactions/create
  Params: customer_id (required), interaction_type (required),
          subject, body, channel, outcome, duration_seconds, interaction_date
```

### Interaction Object Fields
| Field | Type | Description |
|-------|------|-------------|
| `id` | int | |
| `interaction_type` | string | `call` `message` `email` `visit` `note` |
| `channel` | string | `whatsapp`, `phone`, etc. |
| `subject` | string | |
| `body` | string | Full content / notes |
| `outcome` | string | Result of interaction |
| `duration_seconds` | int | For calls |
| `user_id` / `user_name` | int/string | Agent who logged it |
| `interaction_date` | datetime ISO | |

---

## Error Response Format
```json
{ "success": false, "error": "Descriptive error message" }
```

## Common HTTP Status Codes
| Code | Meaning |
|------|---------|
| `200` | Success |
| `401` | Missing / expired JWT token |
| `404` | Resource not found |
| `500` | Server error (check Odoo logs) |

---

## Cron Jobs (Auto-running)
| Job | Interval | Action |
|-----|----------|--------|
| Auto-notify requested items | Every 1 hour | Sets `in_stock` when product qty > 0 |
| Flag SLA breaches | Every 5 min | Sets `sla_breached=true` on overdue messages |
| Daily KPI snapshot | Daily | Computes and stores employee KPI for previous day |

---

## Module Structure
```
lugal_crm/        22 models, 16 controllers, 3 crons
lugal_supply/     2 models (container, vendor)
```

## Complete Endpoint Summary

| Controller | Endpoints | Model(s) |
|-----------|-----------|---------|
| customer_controller | list, get, create, update, delete, kanban_move, activity, calls, tickets, note, interactions, channel_identity CRUD | lugal.crm.customer |
| task_controller | list, get, create, update, update_status, assign, delete, my | lugal.crm.task |
| ticket_controller | list, get, search, create, update, update_status, assign, escalate, delete, notes | lugal.crm.ticket |
| call_controller | list, get, create, end, update, delete, attach_recording, queue list/add/assign | lugal.crm.call + queue |
| channel_controller | config list/create/update/delete, messages list/create/assign/reply/resolve/transfer/conversation | lugal.crm.omnichannel.message + channel.config |
| analytics_controller | dashboard, channel_report, branch_report, employee_kpi, all_kpi, supervisor_dashboard, ai_vs_human, export_kpi | lugal.crm.employee.kpi |
| knowledge_controller | articles list/search/get/create/update/delete, notifications list/push | lugal.crm.kb.article + notification |
| config_controller | tags CRUD, stages CRUD, scripts CRUD | lugal.crm.tag + customer.stage + call.script |
| supply_controller | po CRUD + lines CRUD + suggested, vendors CRUD, containers CRUD | lugal.crm.supply.po + lugal.supply.* |
| branch_controller | list, get, create, update, user_assign, delete | lugal.crm.branch |
| workforce_controller | shifts CRUD, attendance check_in/out/list/live, templates CRUD + render | lugal.crm.shift + attendance + message.template |
| price_list_controller | categories, products list/get, pricelists, requested_items CRUD + update_status | lugal.crm.requested.item |
| pos_bridge_controller | invoice_context, products, product_detail, uom_price, orders create/get/customer | pos_perfume_custom ORM |
| delivery_controller | customer_orders, order detail, orders search | pos_perfume_custom ORM |
