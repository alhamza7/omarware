# NBS-CRM — New API Endpoints Reference
> **Date:** 2026-03-27  
> **Prepared by:** Backend Team  
> **Base URL:** `http://192.168.116.15:8070`  
> **Status:** ✅ Live on `main` branch

---

## Table of Contents

1. [Authentication Patterns](#authentication-patterns)
2. [Supply Chain — 20 New Endpoints](#supply-chain--20-new-endpoints)
3. [Supply Chain — Modified Endpoint](#supply-chain--modified-endpoint)
4. [CRM Users](#crm-users)
5. [Call Centre — Active Context](#call-centre--active-context)
6. [Analytics — Supervisor Dashboard](#analytics--supervisor-dashboard-enhanced)
7. [Settings — Rules Engine](#settings--rules-engine)
8. [Auth — Register](#auth--register)
9. [POS — Inventory Forecasting](#pos--inventory-forecasting)
10. [User Profile & Settings](#user-profile--settings)
11. [Email Account Management](#email-account-management)
12. [Supply Chain — Email Linking](#supply-chain--email-linking)
13. [TypeScript Interfaces](#typescript-interfaces)
14. [Quick Reference Table](#quick-reference-table)

---

## Authentication Patterns

### CRM Endpoints (JSON-RPC 2.0)

All `POST /api/crm/*` and `/lugal/auth/*` endpoints use this wrapper:

```typescript
const crmPost = async (path: string, params: object) => {
  const res = await fetch(`http://192.168.116.15:8070${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'call', params }),
  });
  const json = await res.json();
  return json.result; // { success: true, data: T } | { success: false, error: string }
};
```

### POS & Email Endpoints (REST)

```typescript
const restGet = async (path: string, params?: Record<string, string>) => {
  const url = new URL(`http://192.168.116.15:8070${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json(); // { success: true, data: T }
};

const restPost = async (path: string, body: object, method = 'POST') => {
  const res = await fetch(`http://192.168.116.15:8070${path}`, {
    method,
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify(body),
  });
  return res.json();
};
```

---

## Supply Chain — 20 New Endpoints

> Protocol: **JSON-RPC 2.0**  
> All params go inside `"params": { ... }`

---

### Negotiations

#### `POST /api/crm/supply/negotiations/list`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `page` | number | No | Default `1` |
| `per_page` | number | No | Default `20` |
| `status` | string | No | `open` \| `pending` \| `closed` |
| `vendor_id` | number | No | Filter by vendor |

```json
// Request
{ "params": { "page": 1, "per_page": 20, "status": "open" } }

// Response data
{
  "items": [
    {
      "id": 1,
      "vendor_id": 5,
      "vendor_name": "Global Suppliers Ltd",
      "product_id": 10,
      "product_name": "Rose Perfume 100ml",
      "title": "Price negotiation for shipment",
      "description": "Description text",
      "quantity": 500,
      "expected_price": 12000.00,
      "agreed_price": 0,
      "status": "open",
      "due_date": "2026-04-15",
      "notes": "",
      "created_by_id": 3,
      "created_by_name": "Ahmed Ali",
      "created_at": "2026-03-01T10:00:00",
      "updated_at": "2026-03-10T08:30:00"
    }
  ],
  "total": 45
}
```

---

#### `POST /api/crm/supply/negotiations/create`

| Param | Type | Required |
|-------|------|----------|
| `title` | string | **Yes** |
| `vendor_id` | number | No |
| `product_id` | number | No |
| `description` | string | No |
| `quantity` | number | No |
| `expected_price` | number | No |
| `due_date` | string | No | `YYYY-MM-DD` |

```json
// Response data
{ "id": 12 }
```

---

#### `POST /api/crm/supply/negotiations/{id}/update`

All fields optional (partial update):

```json
// Request params
{
  "title": "Updated title",
  "status": "closed",
  "agreed_price": 11500.00,
  "notes": "Agreement reached"
}
// Response data: null
```

---

#### `POST /api/crm/supply/negotiations/{id}/delete`

```json
// Request params: {}
// Response data: null
```

---

### Item Requests

#### `POST /api/crm/supply/item_requests/list`

| Param | Type | Notes |
|-------|------|-------|
| `page` | number | Default `1` |
| `per_page` | number | Default `20` |
| `status` | string | `pending` \| `approved` \| `rejected` \| `fulfilled` |
| `branch_id` | number | Filter by branch |

```json
// Response data
{
  "items": [
    {
      "id": 1,
      "product_id": 10,
      "product_name": "Rose Perfume",
      "quantity": 100,
      "uom": "bottle",
      "branch_id": 2,
      "branch_name": "Riyadh Branch",
      "requested_by_id": 4,
      "requested_by_name": "Mohammed Salem",
      "status": "pending",
      "note": "Low stock",
      "created_at": "2026-03-20T09:00:00"
    }
  ],
  "total": 30
}
```

---

#### `POST /api/crm/supply/item_requests/create`

| Param | Type | Required |
|-------|------|----------|
| `product_id` | number | **Yes** |
| `quantity` | number | No (default `1`) |
| `uom` | string | No |
| `branch_id` | number | No |
| `note` | string | No |

```json
// Response data
{ "id": 8 }
```

---

#### `POST /api/crm/supply/item_requests/{id}/update_status`

| Param | Type | Required | Values |
|-------|------|----------|--------|
| `status` | string | **Yes** | `approved` \| `rejected` \| `fulfilled` |

```json
// Response data: null
```

---

#### `POST /api/crm/supply/item_requests/{id}/delete`

```json
// Request params: {}
// Response data: null
```

---

### Clearance Companies

#### `POST /api/crm/supply/clearance_companies/list`

```json
// Request params
{ "page": 1, "per_page": 20 }

// Response data
{
  "items": [
    {
      "id": 1,
      "name": "Fast Clearance Co.",
      "contact_name": "Khaled Mahmoud",
      "phone": "+966501234567",
      "email": "info@clearance.com",
      "country": "SA",
      "is_active": true
    }
  ],
  "total": 10
}
```

---

#### `POST /api/crm/supply/clearance_companies/create`

| Param | Type | Required |
|-------|------|----------|
| `name` | string | **Yes** |
| `contact_name` | string | No |
| `phone` | string | No |
| `email` | string | No |
| `country` | string | No | ISO 2-letter code |

```json
// Response data
{ "id": 3 }
```

---

#### `POST /api/crm/supply/clearance_companies/{id}/update`

All fields from create are optional. Additional field: `is_active: boolean`

```json
// Response data: null
```

---

#### `POST /api/crm/supply/clearance_companies/{id}/delete`

```json
// Request params: {}
// Response data: null
```

---

### Min/Max Inventory

#### `POST /api/crm/supply/inventory/minmax`

| Param | Type | Notes |
|-------|------|-------|
| `page` | number | Default `1` |
| `per_page` | number | Default `50` |
| `branch_id` | number | Filter by branch |
| `category_id` | number | Filter by product category |

```json
// Response data
{
  "items": [
    {
      "product_id": 10,
      "product_name": "Rose Perfume 100ml",
      "sku": "PRF-001",
      "category": "Women's Fragrances",
      "uom": "bottle",
      "current_stock": 45,
      "min_qty": 50,
      "max_qty": 300,
      "branch_id": 2,
      "branch_name": "Riyadh Branch"
    }
  ],
  "total": 120
}
```

> `current_stock` is computed live from `stock.quant`.

---

#### `POST /api/crm/supply/inventory/minmax/update`

> **Upsert** — creates or updates the record for `(product_id, branch_id)`.

| Param | Type | Required |
|-------|------|----------|
| `product_id` | number | **Yes** |
| `min_qty` | number | **Yes** |
| `max_qty` | number | **Yes** |
| `branch_id` | number | No |

```json
// Response data: null
```

---

### Internal Messaging

#### `POST /api/crm/supply/messages/list`

| Param | Type | Notes |
|-------|------|-------|
| `page` | number | Default `1` |
| `per_page` | number | Default `30` |
| `thread_id` | number | Filter by thread (0 = all) |

```json
// Response data — sorted oldest-first (chat order)
{
  "items": [
    {
      "id": 1,
      "thread_id": 7,
      "sender_id": 3,
      "sender_name": "Ahmed Ali",
      "sender_avatar": "/web/image/res.users/3/avatar_128",
      "content": "Message text",
      "attachments": [
        { "name": "file.pdf", "url": "https://..." }
      ],
      "created_at": "2026-03-20T10:00:00"
    }
  ],
  "total": 50
}
```

---

#### `POST /api/crm/supply/messages/create`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `content` | string | **Yes** | — |
| `recipient_ids` | number[] | No | List of `res.users` IDs |
| `thread_id` | number | No | Omit or `0` for new thread |
| `attachments` | `{name: string, url: string}[]` | No | Pre-uploaded URLs |

```json
// Response data
{ "id": 22 }
```

---

### Supply Users

#### `POST /api/crm/supply/users`

Returns all active internal users for messaging user-picker.

```json
// Request params: {}

// Response data
{
  "items": [
    {
      "id": 3,
      "name": "Ahmed Ali",
      "avatar": "/web/image/res.users/3/avatar_128",
      "department": ""
    }
  ]
}
```

---

### Supply Notifications

#### `POST /api/crm/supply/notifications/list`

| Param | Type | Notes |
|-------|------|-------|
| `page` | number | Default `1` |
| `per_page` | number | Default `20` |
| `is_read` | boolean | `false` = unread only |

```json
// Response data
{
  "items": [
    {
      "id": 1,
      "type": "container_arrived",
      "title": "New container arrived",
      "body": "Container CNT-2026-001 has been registered",
      "related_id": 15,
      "related_type": "lugal.supply.container",
      "is_read": false,
      "created_at": "2026-03-20T08:00:00"
    }
  ],
  "unread_count": 5,
  "total": 40
}
```

> `type` values: `po_created` | `container_arrived` | `clearance_done` | `low_stock` | `negotiation_update`

---

#### `POST /api/crm/supply/notifications/{id}/mark_read`

```json
// Request params: {}
// Response data: null
```

---

#### `POST /api/crm/supply/notifications/mark_all_read`

```json
// Request params: {}
// Response data: null
```

---

## Supply Chain — Modified Endpoint

### `POST /api/crm/supply/po/list` — New `container_id` filter

> **Existing endpoint** — one new optional parameter added.

```json
// Request params — new field: container_id
{
  "page": 1,
  "per_page": 50,
  "status": "confirmed",
  "vendor_id": 5,
  "container_id": 15
}
```

All other params (`status`, `vendor_id`, pagination) unchanged.

---

## CRM Users

### `POST /api/crm/users/list`

| Param | Type | Notes |
|-------|------|-------|
| `branch_id` | number | Filter users in this branch |
| `role` | string | `agent` \| `supervisor` \| `admin` |
| `is_active` | boolean | Default `true` |
| `page` | number | Default `1` |
| `per_page` | number | Default `100` |

```json
// Response data
{
  "items": [
    {
      "id": 4,
      "name": "Sara Ahmed",
      "email": "sara@company.com",
      "phone": "+966501234567",
      "avatar": "/web/image/res.users/4/avatar_128",
      "role": "agent",
      "branch_id": 2,
      "branch_name": "Riyadh Branch",
      "is_active": true,
      "status": "online"
    }
  ],
  "total": 25
}
```

> `status`: `online` (active within last 5 min) | `busy` (online + has open threads) | `offline`  
> `avatar`: prepend base URL → `http://192.168.116.15:8070/web/image/res.users/{id}/avatar_128`

---

### `POST /api/crm/users/available_agents`

Returns online/busy agents only, sorted: **online → busy → least threads**.

| Param | Type | Notes |
|-------|------|-------|
| `branch_id` | number | Filter by branch |
| `channel_type` | string | `whatsapp` \| `email` \| `phone` — counts threads for this channel only |

```json
// Response data
{
  "items": [
    {
      "id": 4,
      "name": "Sara Ahmed",
      "avatar": "/web/image/res.users/4/avatar_128",
      "status": "online",
      "active_threads": 3,
      "queue_count": 2
    }
  ]
}
```

---

## Call Centre — Active Context

### `POST /api/crm/calls/active_context`

Resolves a customer from an active call and returns enriched context.

| Param | Type | Notes |
|-------|------|-------|
| `call_id` | number | ID of active `lugal.crm.call` record |
| `phone_number` | string | Caller's phone — searches phone_1/2/3 + whatsapp |

> At least one of `call_id` or `phone_number` is required.

```json
// Request params
{ "phone_number": "+966501234567" }

// Response data
{
  "customer": {
    "id": 12,
    "name": "Abdullah Mohammed",
    "phone": "+966501234567",
    "email": "abdullah@email.com",
    "tier": "vip",
    "avatar": null,
    "total_orders": 24,
    "total_spent": 45000.00,
    "last_order_date": "2026-03-10",
    "open_tickets": 2,
    "notes": "VIP customer — prefers Arabic"
  },
  "recent_tickets": [
    {
      "id": 80,
      "title": "Delivery issue",
      "status": "open",
      "created_at": "2026-03-18T09:00:00"
    }
  ],
  "recent_orders": [
    {
      "id": 310,
      "total": 1200.00,
      "status": "paid",
      "date": "2026-03-10"
    }
  ]
}
```

> If phone not found: `{ "customer": null, "recent_tickets": [], "recent_orders": [] }` — show new customer form.

---

## Analytics — Supervisor Dashboard (Enhanced)

### `POST /api/crm/analytics/supervisor_dashboard`

> **Existing endpoint** — 9 new fields added to the response.

```json
// Request params
{ "branch_id": 2 }
```

**New fields in response `data`:**

```json
{
  // ... existing fields unchanged ...

  "total_sales_today":    85000.00,
  "total_customers":      1240,
  "products_sold_today":  340,
  "average_order_value":  250.00,

  "sales_series": {
    "daily": [
      { "label": "2026-03-01", "value": 72000 },
      { "label": "2026-03-02", "value": 85000 }
    ],
    "monthly": [
      { "label": "January", "value": 2100000 },
      { "label": "February", "value": 1950000 }
    ],
    "yearly": [
      { "label": "2024", "value": 22000000 },
      { "label": "2025", "value": 25000000 }
    ]
  },

  "recent_interactions": [
    {
      "id": 501,
      "customer_name": "Abdullah Mohammed",
      "type": "whatsapp",
      "status": "open",
      "created_at": "2026-03-27T09:00:00"
    }
  ],

  "alerts": [
    {
      "id": 1,
      "type": "sla_breach",
      "message": "Ticket #80 — Delivery issue exceeded response time",
      "severity": "high",
      "created_at": "2026-03-27T08:45:00"
    }
  ],

  "customers_summary": {
    "new_today": 12,
    "active":    980,
    "vip":       145,
    "at_risk":   30
  },

  "recent_orders": [
    {
      "id": 310,
      "customer_name": "Abdullah Mohammed",
      "total": 1200.00,
      "status": "paid",
      "created_at": "2026-03-27T10:00:00"
    }
  ]
}
```

> `alerts.type`: `sla_breach` | `vip_inactivity` | `overdue_task`  
> `alerts.severity`: `high` | `medium` | `low`  
> Sales fields return `0` / `[]` if no POS orders exist — never throws an error.

---

## Settings — Rules Engine

> **Requires `supervisor` role or above.**  
> Rules are now persisted in the database (previously localStorage only).

---

### Routing Rules

```
POST /api/crm/config/routing_rules/list
POST /api/crm/config/routing_rules/create
POST /api/crm/config/routing_rules/{id}/update
POST /api/crm/config/routing_rules/{id}/delete
```

**List** — params: `{}`

```json
// Response data
{
  "items": [
    {
      "id": 1,
      "name": "VIP Routing",
      "conditions": [
        { "field": "customer_tier", "operator": "equals", "value": "vip" }
      ],
      "action": { "type": "assign_to", "value": "4" },
      "is_active": true,
      "priority_order": 1
    }
  ],
  "total": 5
}
```

**Create** params:

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Yes** | — |
| `conditions` | `Condition[]` | No | JSON array |
| `action` | `{ type, value }` | No | JSON object |
| `is_active` | boolean | No | Default `true` |
| `priority_order` | number | No | Default `10` — lower = higher priority |

```json
// Create response data
{ "id": 2 }
```

---

### SLA Rules

```
POST /api/crm/config/sla_rules/list
POST /api/crm/config/sla_rules/create
POST /api/crm/config/sla_rules/{id}/update
POST /api/crm/config/sla_rules/{id}/delete
```

**List** response item shape:

```json
{
  "id": 1,
  "name": "Urgent Tickets SLA",
  "ticket_priority": "urgent",
  "first_response_minutes": 30,
  "resolution_minutes": 240,
  "escalate_to_user_id": 5,
  "is_active": true
}
```

**Create** params:

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Yes** | — |
| `ticket_priority` | string | **Yes** | `urgent` \| `high` \| `medium` \| `low` |
| `first_response_minutes` | number | No | Default `30` |
| `resolution_minutes` | number | No | Default `240` |
| `escalate_to_user_id` | number | No | `res.users` ID |
| `is_active` | boolean | No | Default `true` |

---

### VIP Rules

```
POST /api/crm/config/vip_rules/list
POST /api/crm/config/vip_rules/create
POST /api/crm/config/vip_rules/{id}/update
```

> No delete — deactivate via `is_active: false`.

**List** response item shape:

```json
{
  "id": 1,
  "name": "VIP Classification",
  "condition_type": "total_spent",
  "threshold_value": 50000,
  "tier": "vip",
  "is_active": true
}
```

**Create** params:

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Yes** | — |
| `condition_type` | string | **Yes** | `total_spent` \| `order_count` \| `manual` |
| `tier` | string | **Yes** | `vip` \| `gold` \| `silver` |
| `threshold_value` | number | No | Default `0` |
| `is_active` | boolean | No | Default `true` |

---

### Assignment Rules

```
POST /api/crm/config/assignment_rules/list
POST /api/crm/config/assignment_rules/create
POST /api/crm/config/assignment_rules/{id}/update
POST /api/crm/config/assignment_rules/{id}/delete
```

**List** response item shape:

```json
{
  "id": 1,
  "name": "Auto-assign Agent",
  "strategy": "round_robin",
  "conditions": [
    { "field": "channel", "operator": "equals", "value": "whatsapp" }
  ],
  "team_ids": [2, 3],
  "is_active": true
}
```

**Create** params:

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Yes** | — |
| `strategy` | string | No | `round_robin` \| `least_busy` \| `skill_based` |
| `conditions` | `Condition[]` | No | — |
| `team_ids` | number[] | No | Branch IDs |
| `is_active` | boolean | No | Default `true` |

---

### AI Settings (Singleton)

```
POST /api/crm/config/ai_settings        → GET current settings
POST /api/crm/config/ai_settings/update → partial update
```

**GET** params: `{}`

```json
// Response data
{
  "auto_reply_enabled": true,
  "auto_reply_confidence_threshold": 0.85,
  "sentiment_analysis_enabled": true,
  "auto_categorize_tickets": true,
  "suggested_replies_enabled": true,
  "language": "ar",
  "model_version": "gpt-4"
}
```

**Update** params — all optional:

| Param | Type |
|-------|------|
| `auto_reply_enabled` | boolean |
| `auto_reply_confidence_threshold` | number `0.0–1.0` |
| `sentiment_analysis_enabled` | boolean |
| `auto_categorize_tickets` | boolean |
| `suggested_replies_enabled` | boolean |
| `language` | `'ar'` \| `'en'` \| `'auto'` |
| `model_version` | string |

```json
// Update response data: null
```

---

## Auth — Register

### `POST /lugal/auth/register`

> No token required. Requires either:
> - Admin JWT in `Authorization: Bearer` header, **or**
> - Registration token in `X-Registration-Token` header (configured in Odoo system params as `lugal_auth.registration_token`)

```json
// Request
POST /lugal/auth/register
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": {
    "name":       "Sara Ahmed",
    "email":      "sara@company.com",
    "password":   "Pass1234",
    "role":       "agent",
    "branch_id":  2
  }
}
```

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | string | **Yes** | Display name |
| `email` | string | **Yes** | Used as login — must be unique |
| `password` | string | **Yes** | Min 8 chars, letters + digits |
| `role` | string | No | `agent` \| `supervisor` (default `agent`) |
| `branch_id` | number | No | Auto-assigns to branch |

```json
// Response data
{
  "user_id":       45,
  "access_token":  "eyJ...",
  "refresh_token": "eyJ..."
}
```

**Error cases:**
- Email already exists → `{ "success": false, "error": "A user with this email already exists" }`
- Weak password → `{ "success": false, "error": "password must be at least 8 characters..." }`
- Unauthorized → `{ "success": false, "error": "Unauthorized: admin token or registration token required" }`

---

## POS — Inventory Forecasting

> Protocol: **REST**  
> Base path: `/api/pos_perfume/v1`

---

### `GET /api/pos_perfume/v1/inventory/forecast`

| Query Param | Type | Default | Notes |
|-------------|------|---------|-------|
| `category_id` | number | — | Filter by product category |
| `branch_id` | number | — | For min/max reorder_point lookup |
| `limit` | number | `100` | Max `500` |

```http
GET /api/pos_perfume/v1/inventory/forecast?branch_id=2&limit=200
Authorization: Bearer {token}
```

```json
// Response
{
  "success": true,
  "data": {
    "items": [
      {
        "product_id":      10,
        "product_name":    "Rose Perfume 100ml",
        "sku":             "PRF-001",
        "category":        "Women's Fragrances",
        "current_stock":   45,
        "avg_daily_sales": 8.5,
        "days_remaining":  5.3,
        "reorder_point":   50,
        "urgency":         "critical",
        "last_reorder_date": null
      }
    ]
  }
}
```

**Urgency calculation:**

| Condition | Value |
|-----------|-------|
| `days_remaining <= 3` | `critical` |
| `days_remaining <= 7` OR `current_stock <= reorder_point` | `warning` |
| Otherwise | `ok` |

> Results are sorted: **critical → warning → ok**, then by `days_remaining` ascending.

---

### `POST /api/pos_perfume/v1/inventory/reorder`

Creates a **suggested purchase order** (`is_suggested: true`).

```json
// Request body (JSON — not JSON-RPC)
POST /api/pos_perfume/v1/inventory/reorder
Authorization: Bearer {token}
Content-Type: application/json

{
  "product_id": 10,
  "quantity":   200,
  "branch_id":  2
}
```

| Field | Type | Required |
|-------|------|----------|
| `product_id` | number | **Yes** |
| `quantity` | number | No (default `1`) |
| `branch_id` | number | No |

```json
// Response
{
  "success": true,
  "data": { "po_id": 88 }
}
```

---

## User Profile & Settings

> Protocol: **JSON-RPC 2.0**  
> Base path: `/api/crm/users/me`

---

### `POST /api/crm/users/me` — Get Profile

Returns the authenticated user's full profile including all email accounts.

```json
// Request params: {}

// Response data
{
  "id":          4,
  "name":        "Ahmed Ali",
  "login":       "ahmed@company.com",
  "email":       "ahmed@company.com",
  "phone":       "+966501234567",
  "mobile":      "",
  "job_title":   "Sales Agent",
  "avatar_url":  "/web/image/res.users/4/avatar_128",
  "role":        "agent",
  "branch_id":   2,
  "branch_name": "Riyadh Branch",
  "is_active":   true,
  "lang":        "ar_001",
  "tz":          "Asia/Riyadh",
  "email_accounts": [
    {
      "id":             1,
      "name":           "Work Gmail",
      "email_address":  "ahmed@company.com",
      "display_name":   "Ahmed Ali",
      "imap_host":      "imap.gmail.com",
      "imap_port":      993,
      "imap_use_ssl":   true,
      "smtp_host":      "smtp.gmail.com",
      "smtp_port":      587,
      "smtp_use_tls":   true,
      "username":       "ahmed@company.com",
      "is_active":      true,
      "is_default":     true,
      "sync_status":    "ok",
      "last_sync_date": "2026-03-27T09:00:00",
      "unread_count":   5
    }
  ]
}
```

> `avatar_url` is a relative path — prepend: `http://192.168.116.15:8070{avatar_url}`  
> `password` is **never** returned.

---

### `POST /api/crm/users/me/update` — Update Profile

All fields optional (partial update).

| Param | Type | Notes |
|-------|------|-------|
| `name` | string | Display name |
| `phone` | string | — |
| `mobile` | string | — |
| `job_title` | string | — |
| `lang` | string | `ar_001` \| `en_US` \| ... |
| `tz` | string | `Asia/Riyadh` \| `UTC` \| ... |
| `avatar_128` | string | Base64-encoded PNG/JPG |

```json
// Example request params
{
  "name":      "Ahmed Ali Mohammed",
  "phone":     "+966501234567",
  "job_title": "Senior Sales Agent",
  "lang":      "ar_001"
}

// Response data — same shape as /me with updated values
```

**Avatar upload:**
```typescript
const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

const avatarB64 = await fileToBase64(selectedFile);
await crmPost('/api/crm/users/me/update', { avatar_128: avatarB64 });
```

---

### `POST /api/crm/users/me/change_password`

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `current_password` | string | **Yes** | Must match existing password |
| `new_password` | string | **Yes** | Min 8 chars, letters + digits |

```json
// Request params
{
  "current_password": "OldPass123",
  "new_password":     "NewPass456"
}

// Success response data
{ "message": "Password changed successfully" }

// Error responses
{ "success": false, "error": "Current password is incorrect" }
{ "success": false, "error": "new_password must be at least 8 characters and contain letters and digits" }
```

---

## Email Account Management

> Protocol: **REST** (not JSON-RPC)  
> Base path: `/api/lugal/email`

---

### `GET /api/lugal/email/accounts`

```http
GET /api/lugal/email/accounts
Authorization: Bearer {token}
```

Returns all email accounts for the current user (same shape as `email_accounts` in `/me`).

---

### `POST /api/lugal/email/accounts` — Add Account

```json
POST /api/lugal/email/accounts
Authorization: Bearer {token}
Content-Type: application/json

{
  "name":           "Work Gmail",
  "email_address":  "ahmed@company.com",
  "display_name":   "Ahmed Ali",
  "username":       "ahmed@company.com",
  "password":       "app-password-here",
  "imap_host":      "imap.gmail.com",
  "imap_port":      993,
  "imap_use_ssl":   true,
  "smtp_host":      "smtp.gmail.com",
  "smtp_port":      587,
  "smtp_use_tls":   true,
  "is_default":     false
}
```

**Required:** `name`, `email_address`  
**Response:** `{ "success": true, "data": { ...EmailAccount } }`

---

### `PATCH /api/lugal/email/accounts/{id}` — Update Account

```json
PATCH /api/lugal/email/accounts/1
Authorization: Bearer {token}
Content-Type: application/json

{
  "name":     "Work Outlook",
  "password": "new-app-password",
  "is_active": true
}
```

All fields optional. **Note:** `password` field updates IMAP/SMTP credentials.  
**Response:** `{ "success": true, "data": { ...EmailAccount } }`

---

### `DELETE /api/lugal/email/accounts/{id}` — Delete Account

```http
DELETE /api/lugal/email/accounts/1
Authorization: Bearer {token}
```

**Response:** `{ "success": true, "data": { "deleted": true, "id": 1 } }`

---

### `POST /api/lugal/email/accounts/{id}/test` — Test Connection

```http
POST /api/lugal/email/accounts/1/test
Authorization: Bearer {token}
```

**Success:** `{ "success": true, "data": { "status": "ok" } }`  
**Failure:** `{ "success": false, "error": "IMAP connection failed: ..." }`

---

### `POST /api/lugal/email/accounts/{id}/sync` — Trigger Sync

Incremental IMAP sync — fetches only new UIDs since last sync.

```http
POST /api/lugal/email/accounts/1/sync
Authorization: Bearer {token}
```

**Response:** `{ "success": true, "data": { "synced": 12, "account_id": 1 } }`

---

### `POST /api/lugal/email/accounts/{id}/set_default` — Set as Default

```http
POST /api/lugal/email/accounts/1/set_default
Authorization: Bearer {token}
```

**Response:** `{ "success": true, "data": { ...EmailAccount, "is_default": true } }`

---

## Supply Chain — Email Linking

### `POST /api/lugal/email/messages/{id}/link`

Links an email message to a supply chain record.

```json
POST /api/lugal/email/messages/201/link
Authorization: Bearer {token}
Content-Type: application/json

{
  "model":       "lugal.supply.negotiation",
  "record_id":   42,
  "record_name": "Price negotiation for shipment"
}
```

**Supported `model` values:**

| Model | Links to |
|-------|----------|
| `lugal.supply.negotiation` | Negotiation |
| `lugal.supply.container` | Shipping container |
| `lugal.crm.supply.po` | Purchase order |
| `lugal.crm.customer` | CRM customer |
| `lugal.crm.ticket` | Support ticket |

**Response:** `{ "success": true, "data": { "linked": true } }`

---

### `POST /api/lugal/email/messages/{id}/unlink`

```http
POST /api/lugal/email/messages/201/unlink
Authorization: Bearer {token}
```

**Response:** `{ "success": true, "data": { "unlinked": true } }`

---

### `supply_links` Field in Every Message Response

Every email message fetched via `GET /api/lugal/email/messages` now includes:

```json
{
  "id":           201,
  "subject":      "Shipment price offer",
  "from_address": "vendor@supplier.com",
  "supply_links": {
    "negotiation": { "id": 42, "title": "Price negotiation for shipment" },
    "container":   null,
    "po":          null
  },
  "crm_links": {
    "customer": null,
    "ticket":   null
  }
}
```

---

### Auto-Link (Server-side)

When a new email arrives from a vendor email address that matches an **open negotiation** (`status = open`), the server **automatically** links it to that negotiation — no frontend action required.

---

## TypeScript Interfaces

```typescript
// ── Supply Chain ──────────────────────────────────────────────────────────────

interface Negotiation {
  id: number;
  vendor_id: number | null;
  vendor_name: string;
  product_id: number | null;
  product_name: string;
  title: string;
  description: string;
  quantity: number;
  expected_price: number;
  agreed_price: number;
  status: 'open' | 'pending' | 'closed';
  due_date: string | null;
  notes: string;
  created_by_id: number | null;
  created_by_name: string;
  created_at: string | null;
  updated_at: string | null;
}

interface ItemRequest {
  id: number;
  product_id: number | null;
  product_name: string;
  quantity: number;
  uom: string;
  branch_id: number | null;
  branch_name: string;
  requested_by_id: number | null;
  requested_by_name: string;
  status: 'pending' | 'approved' | 'rejected' | 'fulfilled';
  note: string;
  created_at: string | null;
}

interface ClearanceCompany {
  id: number;
  name: string;
  contact_name: string;
  phone: string;
  email: string;
  country: string;
  is_active: boolean;
}

interface MinMaxRecord {
  product_id: number;
  product_name: string;
  sku: string;
  category: string;
  uom: string;
  current_stock: number;
  min_qty: number;
  max_qty: number;
  branch_id: number | null;
  branch_name: string;
}

interface SupplyMessage {
  id: number;
  thread_id: number;
  sender_id: number | null;
  sender_name: string;
  sender_avatar: string | null;
  content: string;
  attachments: Array<{ name: string; url: string }>;
  created_at: string | null;
}

interface SupplyNotification {
  id: number;
  type: 'po_created' | 'container_arrived' | 'clearance_done' | 'low_stock' | 'negotiation_update';
  title: string;
  body: string;
  related_id: number;
  related_type: string;
  is_read: boolean;
  created_at: string | null;
}

// ── CRM Users ─────────────────────────────────────────────────────────────────

interface CrmUser {
  id: number;
  name: string;
  email: string;
  phone: string;
  avatar: string | null;
  role: 'agent' | 'supervisor' | 'admin';
  branch_id: number | null;
  branch_name: string;
  is_active: boolean;
  status: 'online' | 'busy' | 'offline';
}

interface AvailableAgent {
  id: number;
  name: string;
  avatar: string | null;
  status: 'online' | 'busy' | 'offline';
  active_threads: number;
  queue_count: number;
}

// ── Call Centre ───────────────────────────────────────────────────────────────

interface ActiveCallContext {
  customer: {
    id: number;
    name: string;
    phone: string;
    email: string;
    tier: 'vip' | 'regular';
    avatar: string | null;
    total_orders: number;
    total_spent: number;
    last_order_date: string | null;
    open_tickets: number;
    notes: string;
  } | null;
  recent_tickets: Array<{ id: number; title: string; status: string; created_at: string | null }>;
  recent_orders: Array<{ id: number; total: number; status: string; date: string | null }>;
}

// ── Rules Engine ──────────────────────────────────────────────────────────────

interface RuleCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'contains' | 'greater_than' | 'less_than';
  value: string;
}

interface RoutingRule {
  id: number;
  name: string;
  conditions: RuleCondition[];
  action: { type: string; value: string };
  is_active: boolean;
  priority_order: number;
}

interface SLARule {
  id: number;
  name: string;
  ticket_priority: 'urgent' | 'high' | 'medium' | 'low';
  first_response_minutes: number;
  resolution_minutes: number;
  escalate_to_user_id: number | null;
  is_active: boolean;
}

interface VIPRule {
  id: number;
  name: string;
  condition_type: 'total_spent' | 'order_count' | 'manual';
  threshold_value: number;
  tier: 'vip' | 'gold' | 'silver';
  is_active: boolean;
}

interface AssignmentRule {
  id: number;
  name: string;
  strategy: 'round_robin' | 'least_busy' | 'skill_based';
  conditions: RuleCondition[];
  team_ids: number[];
  is_active: boolean;
}

interface AISettings {
  auto_reply_enabled: boolean;
  auto_reply_confidence_threshold: number;
  sentiment_analysis_enabled: boolean;
  auto_categorize_tickets: boolean;
  suggested_replies_enabled: boolean;
  language: 'ar' | 'en' | 'auto';
  model_version: string;
}

// ── POS Inventory ─────────────────────────────────────────────────────────────

interface ForecastItem {
  product_id: number;
  product_name: string;
  sku: string;
  category: string;
  current_stock: number;
  avg_daily_sales: number;
  days_remaining: number | null;
  reorder_point: number;
  urgency: 'critical' | 'warning' | 'ok';
  last_reorder_date: string | null;
}

// ── User Profile ──────────────────────────────────────────────────────────────

interface EmailAccount {
  id: number;
  name: string;
  email_address: string;
  display_name: string;
  imap_host: string;
  imap_port: number;
  imap_use_ssl: boolean;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
  username: string;
  is_active: boolean;
  is_default: boolean;
  sync_status: 'ok' | 'error' | 'never';
  last_sync_date: string | null;
  unread_count: number;
}

interface UserProfile {
  id: number;
  name: string;
  login: string;
  email: string;
  phone: string;
  mobile: string;
  job_title: string;
  avatar_url: string;
  role: 'agent' | 'supervisor' | 'admin';
  branch_id: number | null;
  branch_name: string;
  is_active: boolean;
  lang: string;
  tz: string;
  email_accounts: EmailAccount[];
}

// ── Email Links ───────────────────────────────────────────────────────────────

interface EmailSupplyLinks {
  negotiation: { id: number; title: string } | null;
  container:   { id: number; name: string }  | null;
  po:          { id: number; name: string }  | null;
}

interface EmailCrmLinks {
  customer: { id: number; name: string } | null;
  ticket:   { id: number; name: string } | null;
}
```

---

## Quick Reference Table

| # | Endpoint | Method | Protocol | Module |
|---|----------|--------|----------|--------|
| 1 | `/api/crm/supply/negotiations/list` | POST | JSON-RPC | lugal_crm |
| 2 | `/api/crm/supply/negotiations/create` | POST | JSON-RPC | lugal_crm |
| 3 | `/api/crm/supply/negotiations/{id}/update` | POST | JSON-RPC | lugal_crm |
| 4 | `/api/crm/supply/negotiations/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 5 | `/api/crm/supply/item_requests/list` | POST | JSON-RPC | lugal_crm |
| 6 | `/api/crm/supply/item_requests/create` | POST | JSON-RPC | lugal_crm |
| 7 | `/api/crm/supply/item_requests/{id}/update_status` | POST | JSON-RPC | lugal_crm |
| 8 | `/api/crm/supply/item_requests/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 9 | `/api/crm/supply/clearance_companies/list` | POST | JSON-RPC | lugal_crm |
| 10 | `/api/crm/supply/clearance_companies/create` | POST | JSON-RPC | lugal_crm |
| 11 | `/api/crm/supply/clearance_companies/{id}/update` | POST | JSON-RPC | lugal_crm |
| 12 | `/api/crm/supply/clearance_companies/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 13 | `/api/crm/supply/inventory/minmax` | POST | JSON-RPC | lugal_crm |
| 14 | `/api/crm/supply/inventory/minmax/update` | POST | JSON-RPC | lugal_crm |
| 15 | `/api/crm/supply/messages/list` | POST | JSON-RPC | lugal_crm |
| 16 | `/api/crm/supply/messages/create` | POST | JSON-RPC | lugal_crm |
| 17 | `/api/crm/supply/users` | POST | JSON-RPC | lugal_crm |
| 18 | `/api/crm/supply/notifications/list` | POST | JSON-RPC | lugal_crm |
| 19 | `/api/crm/supply/notifications/{id}/mark_read` | POST | JSON-RPC | lugal_crm |
| 20 | `/api/crm/supply/notifications/mark_all_read` | POST | JSON-RPC | lugal_crm |
| 21 | `/api/crm/supply/po/list` ⚠️ Modified | POST | JSON-RPC | lugal_crm |
| 22 | `/api/crm/users/list` | POST | JSON-RPC | lugal_crm |
| 23 | `/api/crm/users/available_agents` | POST | JSON-RPC | lugal_crm |
| 24 | `/api/crm/calls/active_context` | POST | JSON-RPC | lugal_crm |
| 25 | `/api/crm/analytics/supervisor_dashboard` ⚠️ Enhanced | POST | JSON-RPC | lugal_crm |
| 26 | `/api/crm/config/routing_rules/list` | POST | JSON-RPC | lugal_crm |
| 27 | `/api/crm/config/routing_rules/create` | POST | JSON-RPC | lugal_crm |
| 28 | `/api/crm/config/routing_rules/{id}/update` | POST | JSON-RPC | lugal_crm |
| 29 | `/api/crm/config/routing_rules/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 30 | `/api/crm/config/sla_rules/list` | POST | JSON-RPC | lugal_crm |
| 31 | `/api/crm/config/sla_rules/create` | POST | JSON-RPC | lugal_crm |
| 32 | `/api/crm/config/sla_rules/{id}/update` | POST | JSON-RPC | lugal_crm |
| 33 | `/api/crm/config/sla_rules/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 34 | `/api/crm/config/vip_rules/list` | POST | JSON-RPC | lugal_crm |
| 35 | `/api/crm/config/vip_rules/create` | POST | JSON-RPC | lugal_crm |
| 36 | `/api/crm/config/vip_rules/{id}/update` | POST | JSON-RPC | lugal_crm |
| 37 | `/api/crm/config/assignment_rules/list` | POST | JSON-RPC | lugal_crm |
| 38 | `/api/crm/config/assignment_rules/create` | POST | JSON-RPC | lugal_crm |
| 39 | `/api/crm/config/assignment_rules/{id}/update` | POST | JSON-RPC | lugal_crm |
| 40 | `/api/crm/config/assignment_rules/{id}/delete` | POST | JSON-RPC | lugal_crm |
| 41 | `/api/crm/config/ai_settings` | POST | JSON-RPC | lugal_crm |
| 42 | `/api/crm/config/ai_settings/update` | POST | JSON-RPC | lugal_crm |
| 43 | `/lugal/auth/register` | POST | JSON-RPC | lugal_auth |
| 44 | `/api/pos_perfume/v1/inventory/forecast` | GET | REST | pos_perfume |
| 45 | `/api/pos_perfume/v1/inventory/reorder` | POST | REST | pos_perfume |
| 46 | `/api/crm/users/me` | POST | JSON-RPC | lugal_crm |
| 47 | `/api/crm/users/me/update` | POST | JSON-RPC | lugal_crm |
| 48 | `/api/crm/users/me/change_password` | POST | JSON-RPC | lugal_crm |
| 49 | `/api/lugal/email/accounts` | GET | REST | lugal_email |
| 50 | `/api/lugal/email/accounts` | POST | REST | lugal_email |
| 51 | `/api/lugal/email/accounts/{id}` | PATCH | REST | lugal_email |
| 52 | `/api/lugal/email/accounts/{id}` | DELETE | REST | lugal_email |
| 53 | `/api/lugal/email/accounts/{id}/test` | POST | REST | lugal_email |
| 54 | `/api/lugal/email/accounts/{id}/sync` | POST | REST | lugal_email |
| 55 | `/api/lugal/email/accounts/{id}/set_default` | POST | REST | lugal_email |
| 56 | `/api/lugal/email/messages/{id}/link` | POST | REST | lugal_email |
| 57 | `/api/lugal/email/messages/{id}/unlink` | POST | REST | lugal_email |

---

*Last updated: 2026-03-27 — Backend Team, NBS-CRM*
