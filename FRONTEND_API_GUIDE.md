# NBS-CRM — Frontend API Guide
## New & Updated Endpoints — 2026-03-27

> **Prepared by:** Backend Team  
> **For:** Frontend Developers  
> **Base URL:** `http://192.168.116.15:8070`  
> **Status:** ✅ All endpoints live on `main` branch

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request Patterns](#request-patterns)
3. [TypeScript Interfaces](#typescript-interfaces)
4. [Supply Chain — New Endpoints](#supply-chain--new-endpoints)
   - [Negotiations](#1-negotiations)
   - [Item Requests](#2-item-requests)
   - [Clearance Companies](#3-clearance-companies)
   - [Min/Max Inventory](#4-minmax-inventory)
   - [Internal Messaging](#5-internal-messaging)
   - [Supply Users](#6-supply-users)
   - [Supply Notifications](#7-supply-notifications)
5. [Supply Chain — Modified Endpoint](#supply-chain--modified-endpoint)
   - [PO List — container_id filter](#8-po-list--container_id-filter)
6. [CRM Users](#crm-users)
   - [Users List](#9-users-list)
   - [Available Agents](#10-available-agents)
7. [Call Centre](#call-centre)
   - [Active Call Context](#11-active-call-context)
8. [Analytics — Supervisor Dashboard](#analytics--supervisor-dashboard)
9. [Settings — Rules Engine](#settings--rules-engine)
   - [Routing Rules](#14-routing-rules)
   - [SLA Rules](#15-sla-rules)
   - [VIP Rules](#16-vip-rules)
   - [Assignment Rules](#17-assignment-rules)
   - [AI Settings](#18-ai-settings)
10. [Auth — Register](#auth--register)
11. [POS — Inventory Forecasting](#pos--inventory-forecasting)
    - [Forecast](#20-inventory-forecast)
    - [Reorder](#21-create-reorder)

---

## Authentication

All CRM endpoints require a JWT token issued by `/lugal/auth/login`.

```http
Authorization: Bearer {access_token}
```

**Token refresh:**
```http
POST /lugal/auth/refresh
{ "refresh_token": "eyJ..." }
```

**Token expiry:** Access tokens are short-lived. On `401` response, refresh immediately and retry.

---

## Request Patterns

### CRM Endpoints (JSON-RPC 2.0)

```typescript
// All POST /api/crm/* endpoints use this wrapper
const crmPost = async (path: string, params: object) => {
  const res = await fetch(`http://192.168.116.15:8070${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      id: 1,
      method: 'call',
      params,
    }),
  });
  const json = await res.json();
  // Unwrap: json.result === { success: true, data: {...} }
  return json.result;
};
```

### POS Endpoints (REST)

```typescript
const posGet = async (path: string, params?: Record<string, string>) => {
  const url = new URL(`http://192.168.116.15:8070${path}`);
  if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  const res = await fetch(url.toString(), {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json(); // { success: true, data: {...} }
};

const posPost = async (path: string, body: object) => {
  const res = await fetch(`http://192.168.116.15:8070${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  return res.json();
};
```

### Auth Endpoints (JSON-RPC 2.0, No Auth required)

```typescript
const authPost = async (path: string, params: object) => {
  const res = await fetch(`http://192.168.116.15:8070${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'call', params }),
  });
  const json = await res.json();
  return json.result;
};
```

### Unified Response Format

```typescript
// Success
{ success: true, data: T }

// Error
{ success: false, error: "رسالة الخطأ" }
```

---

## TypeScript Interfaces

```typescript
// ── Shared ────────────────────────────────────────────────────────────────────

interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

type NegotiationStatus = 'open' | 'pending' | 'closed';
type ItemRequestStatus = 'pending' | 'approved' | 'rejected' | 'fulfilled';
type PresenceStatus = 'online' | 'busy' | 'offline';
type UserRole = 'agent' | 'supervisor' | 'admin';
type Urgency = 'critical' | 'warning' | 'ok';
type TicketPriority = 'urgent' | 'high' | 'medium' | 'low';
type Tier = 'vip' | 'gold' | 'silver';
type AssignmentStrategy = 'round_robin' | 'least_busy' | 'skill_based';
type AILanguage = 'ar' | 'en' | 'auto';

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
  status: NegotiationStatus;
  due_date: string | null;        // YYYY-MM-DD
  notes: string;
  created_by_id: number | null;
  created_by_name: string;
  created_at: string | null;      // ISO 8601
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
  status: ItemRequestStatus;
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

interface SupplyUser {
  id: number;
  name: string;
  avatar: string | null;
  department: string;
}

// ── CRM Users ─────────────────────────────────────────────────────────────────

interface CrmUser {
  id: number;
  name: string;
  email: string;
  phone: string;
  avatar: string | null;
  role: UserRole;
  branch_id: number | null;
  branch_name: string;
  is_active: boolean;
  status: PresenceStatus;
}

interface AvailableAgent {
  id: number;
  name: string;
  avatar: string | null;
  status: PresenceStatus;
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
  recent_tickets: Array<{
    id: number;
    title: string;
    status: string;
    created_at: string | null;
  }>;
  recent_orders: Array<{
    id: number;
    total: number;
    status: string;
    date: string | null;
  }>;
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
  ticket_priority: TicketPriority;
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
  tier: Tier;
  is_active: boolean;
}

interface AssignmentRule {
  id: number;
  name: string;
  strategy: AssignmentStrategy;
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
  language: AILanguage;
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
  urgency: Urgency;
  last_reorder_date: string | null;
}
```

---

## Supply Chain — New Endpoints

> **Base path:** `POST /api/crm/supply/...`  
> All params sent inside `"params": { ... }` of the JSON-RPC wrapper.

---

### 1. Negotiations

#### List Negotiations

```http
POST /api/crm/supply/negotiations/list
```

| Param | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `page` | `number` | No | `1` | — |
| `per_page` | `number` | No | `20` | — |
| `status` | `string` | No | — | `open` \| `pending` \| `closed` |
| `vendor_id` | `number` | No | — | Filter by vendor |

**Response `data`:**
```typescript
{ items: Negotiation[]; total: number }
```

---

#### Create Negotiation

```http
POST /api/crm/supply/negotiations/create
```

| Param | Type | Required |
|-------|------|----------|
| `title` | `string` | **Yes** |
| `vendor_id` | `number` | No |
| `product_id` | `number` | No |
| `description` | `string` | No |
| `quantity` | `number` | No |
| `expected_price` | `number` | No |
| `due_date` | `string` | No | `YYYY-MM-DD` |

**Response `data`:** `{ id: number }`

---

#### Update Negotiation

```http
POST /api/crm/supply/negotiations/{id}/update
```

All fields optional (partial update):

| Param | Type |
|-------|------|
| `title` | `string` |
| `description` | `string` |
| `quantity` | `number` |
| `expected_price` | `number` |
| `agreed_price` | `number` |
| `status` | `'open' \| 'pending' \| 'closed'` |
| `due_date` | `string` |
| `notes` | `string` |
| `vendor_id` | `number` |
| `product_id` | `number` |

**Response `data`:** `null`

---

#### Delete Negotiation

```http
POST /api/crm/supply/negotiations/{id}/delete
```

**Params:** `{}`  
**Response `data`:** `null`

---

### 2. Item Requests

#### List Item Requests

```http
POST /api/crm/supply/item_requests/list
```

| Param | Type | Notes |
|-------|------|-------|
| `page` | `number` | Default `1` |
| `per_page` | `number` | Default `20` |
| `status` | `string` | `pending \| approved \| rejected \| fulfilled` |
| `branch_id` | `number` | — |

**Response `data`:** `{ items: ItemRequest[]; total: number }`

---

#### Create Item Request

```http
POST /api/crm/supply/item_requests/create
```

| Param | Type | Required |
|-------|------|----------|
| `product_id` | `number` | **Yes** |
| `quantity` | `number` | No (default `1`) |
| `uom` | `string` | No |
| `branch_id` | `number` | No |
| `note` | `string` | No |

**Response `data`:** `{ id: number }`

---

#### Update Item Request Status

```http
POST /api/crm/supply/item_requests/{id}/update_status
```

| Param | Type | Required | Values |
|-------|------|----------|--------|
| `status` | `string` | **Yes** | `approved \| rejected \| fulfilled` |

**Response `data`:** `null`

---

#### Delete Item Request

```http
POST /api/crm/supply/item_requests/{id}/delete
```

**Params:** `{}`  
**Response `data`:** `null`

---

### 3. Clearance Companies

#### List Clearance Companies

```http
POST /api/crm/supply/clearance_companies/list
```

| Param | Type | Default |
|-------|------|---------|
| `page` | `number` | `1` |
| `per_page` | `number` | `20` |

**Response `data`:** `{ items: ClearanceCompany[]; total: number }`

---

#### Create Clearance Company

```http
POST /api/crm/supply/clearance_companies/create
```

| Param | Type | Required |
|-------|------|----------|
| `name` | `string` | **Yes** |
| `contact_name` | `string` | No |
| `phone` | `string` | No |
| `email` | `string` | No |
| `country` | `string` | No | ISO 2-letter code e.g. `SA` |

**Response `data`:** `{ id: number }`

---

#### Update Clearance Company

```http
POST /api/crm/supply/clearance_companies/{id}/update
```

All fields optional. Same fields as create + `is_active: boolean`.

**Response `data`:** `null`

---

#### Delete Clearance Company

```http
POST /api/crm/supply/clearance_companies/{id}/delete
```

**Params:** `{}`  
**Response `data`:** `null`

---

### 4. Min/Max Inventory

#### List Min/Max Records

```http
POST /api/crm/supply/inventory/minmax
```

| Param | Type | Notes |
|-------|------|-------|
| `page` | `number` | Default `1` |
| `per_page` | `number` | Default `50` |
| `branch_id` | `number` | Filter by branch |
| `category_id` | `number` | Filter by product category |

**Response `data`:** `{ items: MinMaxRecord[]; total: number }`

> `current_stock` is computed live from `stock.quant`.

---

#### Upsert Min/Max

```http
POST /api/crm/supply/inventory/minmax/update
```

> Creates or updates the record for `(product_id, branch_id)` pair.

| Param | Type | Required |
|-------|------|----------|
| `product_id` | `number` | **Yes** |
| `min_qty` | `number` | **Yes** |
| `max_qty` | `number` | **Yes** |
| `branch_id` | `number` | No |

**Response `data`:** `null`

---

### 5. Internal Messaging

#### List Messages

```http
POST /api/crm/supply/messages/list
```

| Param | Type | Notes |
|-------|------|-------|
| `page` | `number` | Default `1` |
| `per_page` | `number` | Default `30` |
| `thread_id` | `number` | Filter by thread |

**Response `data`:** `{ items: SupplyMessage[]; total: number }`

> Messages are sorted ascending by `created_at` (oldest first — for chat UI).

---

#### Send Message

```http
POST /api/crm/supply/messages/create
```

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `content` | `string` | **Yes** | — |
| `recipient_ids` | `number[]` | No | List of `res.users` IDs |
| `thread_id` | `number` | No | Pass `0` or omit for new thread |
| `attachments` | `Array<{name:string; url:string}>` | No | Pre-uploaded URLs |

**Response `data`:** `{ id: number }`

---

### 6. Supply Users

```http
POST /api/crm/supply/users
```

**Params:** `{}`

Returns all active internal users for the messaging user-picker.

**Response `data`:**
```typescript
{ items: SupplyUser[] }
```

---

### 7. Supply Notifications

#### List Notifications

```http
POST /api/crm/supply/notifications/list
```

| Param | Type | Notes |
|-------|------|-------|
| `page` | `number` | Default `1` |
| `per_page` | `number` | Default `20` |
| `is_read` | `boolean` | `false` = unread only |

**Response `data`:**
```typescript
{
  items: SupplyNotification[];
  unread_count: number;
  total: number;
}
```

---

#### Mark One as Read

```http
POST /api/crm/supply/notifications/{id}/mark_read
```

**Params:** `{}`  
**Response `data`:** `null`

---

#### Mark All as Read

```http
POST /api/crm/supply/notifications/mark_all_read
```

**Params:** `{}`  
**Response `data`:** `null`

---

## Supply Chain — Modified Endpoint

### 8. PO List — `container_id` filter

> **Existing endpoint** — new optional parameter added.

```http
POST /api/crm/supply/po/list
```

**New parameter:**

| Param | Type | Notes |
|-------|------|-------|
| `container_id` | `number` | Filter POs belonging to a specific container |

**Example:**
```json
{
  "page": 1,
  "per_page": 50,
  "container_id": 15
}
```

All other params (`status`, `vendor_id`, pagination) unchanged.

---

## CRM Users

### 9. Users List

```http
POST /api/crm/users/list
```

| Param | Type | Notes |
|-------|------|-------|
| `branch_id` | `number` | Filter users assigned to this branch |
| `role` | `string` | `agent \| supervisor \| admin` |
| `is_active` | `boolean` | Default `true` |
| `page` | `number` | Default `1` |
| `per_page` | `number` | Default `100` |

**Response `data`:**
```typescript
{ items: CrmUser[]; total: number }
```

> **`avatar`** is a relative URL — prepend base URL: `http://192.168.116.15:8070/web/image/res.users/{id}/avatar_128`  
> **`status`** is live: `online` (active in last 5 min) \| `busy` (online + has open threads) \| `offline`

---

### 10. Available Agents

```http
POST /api/crm/users/available_agents
```

Returns only agents that are currently **online or busy**, sorted: online first, then by `active_threads` ascending (least busy first).

| Param | Type | Notes |
|-------|------|-------|
| `branch_id` | `number` | Filter by branch |
| `channel_type` | `string` | `whatsapp \| email \| phone` — counts threads for this channel only |

**Response `data`:**
```typescript
{ items: AvailableAgent[] }
```

**Usage — Transfer Dialog:**
```typescript
// Load agents available for WhatsApp transfer
const { data } = await crmPost('/api/crm/users/available_agents', {
  branch_id: currentBranchId,
  channel_type: 'whatsapp',
});
// Sort already applied: online+leastBusy first
setAgentList(data.items);
```

---

## Call Centre

### 11. Active Call Context

```http
POST /api/crm/calls/active_context
```

Resolves the customer from an active call and returns enriched context for the agent screen.

| Param | Type | Notes |
|-------|------|-------|
| `call_id` | `number` | ID of an active `lugal.crm.call` record |
| `phone_number` | `string` | Caller's phone — searches `phone_1`, `phone_2`, `phone_3`, `whatsapp_number` |

> At least one of `call_id` or `phone_number` must be provided. `call_id` takes priority.

**Response `data`:** `ActiveCallContext`

```typescript
// Example usage — when call connects:
const { data } = await crmPost('/api/crm/calls/active_context', {
  phone_number: incomingPhoneNumber,
});

if (data.customer) {
  showCustomerPanel(data.customer);
  showRecentTickets(data.recent_tickets);
  showRecentOrders(data.recent_orders);
} else {
  showNewCustomerForm();
}
```

> If the phone number is not found in any customer record, `customer` is `null` — show the "create new customer" flow.

---

## Analytics — Supervisor Dashboard

### 12. Supervisor Dashboard (Enhanced)

> **Existing endpoint** — response now includes 9 additional fields.

```http
POST /api/crm/analytics/supervisor_dashboard
```

**Params:** `{ branch_id?: number }`

**Response `data` — New Fields Added:**

```typescript
interface SupervisorDashboardData {
  // ── Existing fields (unchanged) ──────────────────────────────────────────
  agent_conversations: Array<{
    agent_id: number;
    agent_name: string;
    open_conversations: number;
  }>;
  unassigned_messages: Array<{
    id: number; channel: string; customer_id: number | null;
    customer_name: string; content: string; sent_at: string | null;
    sla_breached: boolean;
  }>;
  unassigned_count: number;
  overdue_tasks: Array<{
    id: number; title: string; due_date: string | null;
    assigned_to: string; customer_name: string;
  }>;
  overdue_count: number;
  high_priority_tickets: Array<{
    id: number; title: string; status: string; priority: string;
    assigned_to: string; customer_name: string; sla_deadline: string | null;
  }>;
  dormant_vip_customers: Array<{
    id: number; name: string; last_call_date: string | null; account_manager: string;
  }>;

  // ── NEW: Sales KPIs ───────────────────────────────────────────────────────
  total_sales_today: number;
  total_customers: number;
  products_sold_today: number;
  average_order_value: number;

  // ── NEW: Sales Time Series ────────────────────────────────────────────────
  sales_series: {
    daily: Array<{ label: string; value: number }>;    // last 30 days (YYYY-MM-DD)
    monthly: Array<{ label: string; value: number }>;  // last 12 months (Arabic names)
    yearly: Array<{ label: string; value: number }>;   // last 3 years
  };

  // ── NEW: Recent Interactions ──────────────────────────────────────────────
  recent_interactions: Array<{
    id: number;
    customer_name: string;
    type: string;         // channel name e.g. "whatsapp"
    status: string;
    created_at: string | null;
  }>;

  // ── NEW: Alerts ───────────────────────────────────────────────────────────
  alerts: Array<{
    id: number;
    type: 'sla_breach' | 'vip_inactivity' | 'overdue_task';
    message: string;
    severity: 'high' | 'medium' | 'low';
    created_at: string;
  }>;

  // ── NEW: Customer Summary ─────────────────────────────────────────────────
  customers_summary: {
    new_today: number;
    active: number;     // active in last 30 days
    vip: number;
    at_risk: number;    // no activity in 30+ days, non-VIP
  };

  // ── NEW: Recent Orders ────────────────────────────────────────────────────
  recent_orders: Array<{
    id: number;
    customer_name: string;
    total: number;
    status: string;
    created_at: string | null;
  }>;
}
```

> **Note:** `sales_series`, `total_sales_today`, `products_sold_today`, and `recent_orders` are sourced from `pos.order`. If there are no POS orders yet, all sales fields will return `0` / empty arrays — they will **never** throw an error.

---

## Settings — Rules Engine

> **Requires `supervisor` role or above.**  
> All rules are now persisted in the database (previously only in localStorage).

---

### 14. Routing Rules

```http
POST /api/crm/config/routing_rules/list
POST /api/crm/config/routing_rules/create
POST /api/crm/config/routing_rules/{id}/update
POST /api/crm/config/routing_rules/{id}/delete
```

**List params:** `{}`  
**Response `data`:** `{ items: RoutingRule[]; total: number }`

**Create params:**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `string` | **Yes** | — |
| `conditions` | `RuleCondition[]` | No | JSON array |
| `action` | `{ type: string; value: string }` | No | JSON object |
| `is_active` | `boolean` | No | Default `true` |
| `priority_order` | `number` | No | Default `10` (lower = higher priority) |

**Response `data`:** `{ id: number }`

**Update params:** All fields from Create (all optional).

**Delete params:** `{}`

---

### 15. SLA Rules

```http
POST /api/crm/config/sla_rules/list
POST /api/crm/config/sla_rules/create
POST /api/crm/config/sla_rules/{id}/update
POST /api/crm/config/sla_rules/{id}/delete
```

**List params:** `{}`  
**Response `data`:** `{ items: SLARule[]; total: number }`

**Create params:**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `string` | **Yes** | — |
| `ticket_priority` | `string` | **Yes** | `urgent \| high \| medium \| low` |
| `first_response_minutes` | `number` | No | Default `30` |
| `resolution_minutes` | `number` | No | Default `240` |
| `escalate_to_user_id` | `number` | No | `res.users` ID |
| `is_active` | `boolean` | No | Default `true` |

**Response `data`:** `{ id: number }`

---

### 16. VIP Rules

```http
POST /api/crm/config/vip_rules/list
POST /api/crm/config/vip_rules/create
POST /api/crm/config/vip_rules/{id}/update
```

> No delete endpoint — VIP rules are permanent (deactivate via `is_active: false`).

**List params:** `{}`  
**Response `data`:** `{ items: VIPRule[]; total: number }`

**Create params:**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `string` | **Yes** | — |
| `condition_type` | `string` | **Yes** | `total_spent \| order_count \| manual` |
| `tier` | `string` | **Yes** | `vip \| gold \| silver` |
| `threshold_value` | `number` | No | Default `0` |
| `is_active` | `boolean` | No | Default `true` |

**Response `data`:** `{ id: number }`

---

### 17. Assignment Rules

```http
POST /api/crm/config/assignment_rules/list
POST /api/crm/config/assignment_rules/create
POST /api/crm/config/assignment_rules/{id}/update
POST /api/crm/config/assignment_rules/{id}/delete
```

**List params:** `{}`  
**Response `data`:** `{ items: AssignmentRule[]; total: number }`

**Create params:**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `string` | **Yes** | — |
| `strategy` | `string` | No | `round_robin \| least_busy \| skill_based` (default `round_robin`) |
| `conditions` | `RuleCondition[]` | No | JSON array |
| `team_ids` | `number[]` | No | List of `lugal.crm.branch` IDs |
| `is_active` | `boolean` | No | Default `true` |

**Response `data`:** `{ id: number }`

---

### 18. AI Settings

```http
# GET current settings (also accepts POST — JSON-RPC wrapper)
POST /api/crm/config/ai_settings

# Update (partial — only provided fields are changed)
POST /api/crm/config/ai_settings/update
```

**GET params:** `{}`  
**Response `data`:** `AISettings`

**Update params** (all optional):

| Param | Type |
|-------|------|
| `auto_reply_enabled` | `boolean` |
| `auto_reply_confidence_threshold` | `number` | `0.0 – 1.0` |
| `sentiment_analysis_enabled` | `boolean` |
| `auto_categorize_tickets` | `boolean` |
| `suggested_replies_enabled` | `boolean` |
| `language` | `'ar' \| 'en' \| 'auto'` |
| `model_version` | `string` |

**Response `data`:** `null`

**Example — load and update:**
```typescript
// Load
const { data: aiSettings } = await crmPost('/api/crm/config/ai_settings', {});

// Toggle auto-reply
await crmPost('/api/crm/config/ai_settings/update', {
  auto_reply_enabled: !aiSettings.auto_reply_enabled,
});
```

---

## Auth — Register

### 19. Register New User

```http
POST /lugal/auth/register
```

> No auth token required. Requires either:
> - A logged-in **admin** JWT in `Authorization: Bearer` header, **OR**
> - A registration token in `X-Registration-Token` header (configured in Odoo system parameters as `lugal_auth.registration_token`)

**Params:**

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `name` | `string` | **Yes** | Display name |
| `email` | `string` | **Yes** | Used as login — must be unique |
| `password` | `string` | **Yes** | Min 8 chars, must include letters + digits |
| `role` | `string` | No | `agent \| supervisor` (default `agent`) |
| `branch_id` | `number` | No | Auto-assigns user to branch |

**Response `data`:**
```typescript
{
  user_id: number;
  access_token: string;
  refresh_token: string;
}
```

**Error cases:**
- `400` — missing/invalid fields
- `409` — email already exists → `{ success: false, error: "A user with this email already exists" }`
- `401` — missing admin token

**Example:**
```typescript
// Typically called from an admin-protected "Add User" form
const { success, data, error } = await authPost('/lugal/auth/register', {
  name: 'سارة أحمد',
  email: 'sara@company.com',
  password: 'Pass1234',
  role: 'agent',
  branch_id: 2,
});

if (success) {
  // Store tokens and redirect to dashboard
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
}
```

---

## POS — Inventory Forecasting

> **Base path:** `/api/pos_perfume/v1/`  
> **Protocol:** REST (not JSON-RPC)  
> **Auth:** `Authorization: Bearer {token}`

---

### 20. Inventory Forecast

```http
GET /api/pos_perfume/v1/inventory/forecast
```

**Query Params:**

| Param | Type | Default | Notes |
|-------|------|---------|-------|
| `category_id` | `number` | — | Filter by product category |
| `branch_id` | `number` | — | Used for min/max reorder_point lookup |
| `limit` | `number` | `100` | Max 500 |

**Response:**
```typescript
{
  success: true;
  data: {
    items: ForecastItem[];   // sorted: critical → warning → ok, then by days_remaining asc
  };
}
```

**`urgency` calculation:**
| Condition | Value |
|-----------|-------|
| `days_remaining <= 3` | `critical` |
| `days_remaining <= 7` OR `current_stock <= reorder_point` | `warning` |
| Otherwise | `ok` |

**Example:**
```typescript
const { data } = await posGet('/api/pos_perfume/v1/inventory/forecast', {
  branch_id: '2',
  limit: '200',
});

const critical = data.items.filter(i => i.urgency === 'critical');
// Show alert banner for critical items
```

---

### 21. Create Reorder

```http
POST /api/pos_perfume/v1/inventory/reorder
```

Creates a **suggested purchase order** (`lugal.crm.supply.po` with `is_suggested: true`) and a PO line for the requested product.

**Body (JSON — not JSON-RPC):**
```json
{
  "product_id": 10,
  "quantity": 200,
  "branch_id": 2
}
```

| Field | Type | Required |
|-------|------|----------|
| `product_id` | `number` | **Yes** |
| `quantity` | `number` | No (default `1`) |
| `branch_id` | `number` | No |

**Response:**
```json
{
  "success": true,
  "data": { "po_id": 88 }
}
```

**Example:**
```typescript
const { data } = await posPost('/api/pos_perfume/v1/inventory/reorder', {
  product_id: item.product_id,
  quantity: item.max_qty - item.current_stock,
  branch_id: currentBranchId,
});

// Navigate to supply chain → PO with id = data.po_id
navigate(`/supply/po/${data.po_id}`);
```

---

## Error Handling

All endpoints follow the same error pattern:

```typescript
// Unified error handler
const callApi = async (path: string, params: object) => {
  const result = await crmPost(path, params);

  if (!result.success) {
    // Show error to user
    showToast(result.error || 'حدث خطأ غير متوقع');
    throw new Error(result.error);
  }

  return result.data;
};
```

**Common error codes:**

| HTTP | `result.error` | Cause |
|------|----------------|-------|
| `200` with `success: false` | `'Unauthorized'` | Missing or expired token |
| `200` with `success: false` | `'Supervisor role required'` | Endpoint requires supervisor |
| `200` with `success: false` | `'X not found'` | Record doesn't exist or is deleted |
| `200` with `success: false` | `'X is required'` | Missing required parameter |

---

## Migrating localStorage Rules to Backend

If you have existing rules stored in `localStorage` from the old implementation, migrate them **once** on app startup:

```typescript
const migrateRules = async () => {
  const migrated = localStorage.getItem('rules_migrated');
  if (migrated) return;

  const localRoutingRules = JSON.parse(localStorage.getItem('routing_rules') || '[]');
  for (const rule of localRoutingRules) {
    await crmPost('/api/crm/config/routing_rules/create', {
      name: rule.name,
      conditions: rule.conditions,
      action: rule.action,
      is_active: rule.is_active,
      priority_order: rule.priority_order,
    });
  }

  // Repeat for sla_rules, vip_rules, assignment_rules ...
  
  localStorage.setItem('rules_migrated', 'true');
  localStorage.removeItem('routing_rules');
};
```

---

## Quick Reference

| # | Endpoint | Method |
|---|----------|--------|
| 1 | `/api/crm/supply/negotiations/list` | POST |
| 2 | `/api/crm/supply/negotiations/create` | POST |
| 3 | `/api/crm/supply/negotiations/{id}/update` | POST |
| 4 | `/api/crm/supply/negotiations/{id}/delete` | POST |
| 5 | `/api/crm/supply/item_requests/list` | POST |
| 6 | `/api/crm/supply/item_requests/create` | POST |
| 7 | `/api/crm/supply/item_requests/{id}/update_status` | POST |
| 8 | `/api/crm/supply/item_requests/{id}/delete` | POST |
| 9 | `/api/crm/supply/clearance_companies/list` | POST |
| 10 | `/api/crm/supply/clearance_companies/create` | POST |
| 11 | `/api/crm/supply/clearance_companies/{id}/update` | POST |
| 12 | `/api/crm/supply/clearance_companies/{id}/delete` | POST |
| 13 | `/api/crm/supply/inventory/minmax` | POST |
| 14 | `/api/crm/supply/inventory/minmax/update` | POST |
| 15 | `/api/crm/supply/messages/list` | POST |
| 16 | `/api/crm/supply/messages/create` | POST |
| 17 | `/api/crm/supply/users` | POST |
| 18 | `/api/crm/supply/notifications/list` | POST |
| 19 | `/api/crm/supply/notifications/{id}/mark_read` | POST |
| 20 | `/api/crm/supply/notifications/mark_all_read` | POST |
| 21 | `/api/crm/users/list` | POST |
| 22 | `/api/crm/users/available_agents` | POST |
| 23 | `/api/crm/calls/active_context` | POST |
| 24 | `/api/crm/analytics/supervisor_dashboard` ⚠️ Enhanced | POST |
| 25 | `/api/crm/supply/po/list` ⚠️ Modified | POST |
| 26 | `/api/crm/config/routing_rules/list` | POST |
| 27 | `/api/crm/config/routing_rules/create` | POST |
| 28 | `/api/crm/config/routing_rules/{id}/update` | POST |
| 29 | `/api/crm/config/routing_rules/{id}/delete` | POST |
| 30 | `/api/crm/config/sla_rules/list` | POST |
| 31 | `/api/crm/config/sla_rules/create` | POST |
| 32 | `/api/crm/config/sla_rules/{id}/update` | POST |
| 33 | `/api/crm/config/sla_rules/{id}/delete` | POST |
| 34 | `/api/crm/config/vip_rules/list` | POST |
| 35 | `/api/crm/config/vip_rules/create` | POST |
| 36 | `/api/crm/config/vip_rules/{id}/update` | POST |
| 37 | `/api/crm/config/assignment_rules/list` | POST |
| 38 | `/api/crm/config/assignment_rules/create` | POST |
| 39 | `/api/crm/config/assignment_rules/{id}/update` | POST |
| 40 | `/api/crm/config/assignment_rules/{id}/delete` | POST |
| 41 | `/api/crm/config/ai_settings` | POST/GET |
| 42 | `/api/crm/config/ai_settings/update` | POST |
| 43 | `/lugal/auth/register` | POST |
| 44 | `/api/pos_perfume/v1/inventory/forecast` | GET |
| 45 | `/api/pos_perfume/v1/inventory/reorder` | POST |

---

*Last updated: 2026-03-27 — Backend Team, NBS-CRM*

---

## User Profile & Settings

> **Base path:** `POST /api/crm/users/me*`  
> **Protocol:** JSON-RPC 2.0 (same `crmPost` wrapper)  
> **Auth:** Bearer JWT required

---

### `GET /api/crm/users/me` — Current User Profile

Returns the authenticated user's full profile **including all configured email accounts**.

```http
POST /api/crm/users/me
params: {}
```

**Response `data`:**
```typescript
interface UserProfile {
  // ── Identity ──────────────────────────────────────────────────────────
  id:           number;
  name:         string;
  login:        string;           // email used as login
  email:        string;
  phone:        string;
  mobile:       string;
  job_title:    string;
  avatar_url:   string;           // e.g. /web/image/res.users/4/avatar_128

  // ── Role & Branch ─────────────────────────────────────────────────────
  role:         'agent' | 'supervisor' | 'admin';
  branch_id:    number | null;
  branch_name:  string;

  // ── Preferences ───────────────────────────────────────────────────────
  is_active:    boolean;
  lang:         string;           // e.g. 'ar_001', 'en_US'
  tz:           string;           // e.g. 'Asia/Riyadh'

  // ── Email accounts (from lugal_email module) ──────────────────────────
  email_accounts: EmailAccount[];
}

interface EmailAccount {
  id:             number;
  name:           string;         // label e.g. "Work Gmail"
  email_address:  string;
  display_name:   string;         // shown in From: header
  imap_host:      string;
  imap_port:      number;
  imap_use_ssl:   boolean;
  smtp_host:      string;
  smtp_port:      number;
  smtp_use_tls:   boolean;
  username:       string;
  is_active:      boolean;
  is_default:     boolean;
  sync_status:    'ok' | 'error' | 'never';
  last_sync_date: string | null;
  unread_count:   number;
  // NOTE: password is NEVER returned
}
```

**Example — load settings screen:**
```typescript
const { data: profile } = await crmPost('/api/crm/users/me', {});

// Show profile card
setUserName(profile.name);
setAvatarUrl(`http://192.168.116.15:8070${profile.avatar_url}`);

// Show email accounts list
setEmailAccounts(profile.email_accounts);
```

---

### `POST /api/crm/users/me/update` — Update Profile

All fields are optional (partial update).

| Param | Type | Notes |
|-------|------|-------|
| `name` | `string` | Display name |
| `phone` | `string` | — |
| `mobile` | `string` | — |
| `job_title` | `string` | Shown in profile |
| `lang` | `string` | `ar_001` \| `en_US` \| ... |
| `tz` | `string` | `Asia/Riyadh` \| `UTC` \| ... |
| `avatar_128` | `string` | Base64-encoded PNG/JPG |

**Response `data`:** Full `UserProfile` (same as `/me`) — reflecting the new values.

**Example — save profile form:**
```typescript
const { data: updatedProfile } = await crmPost('/api/crm/users/me/update', {
  name:      formData.name,
  phone:     formData.phone,
  job_title: formData.jobTitle,
  lang:      'ar_001',
});
```

**Avatar upload — example:**
```typescript
const fileToBase64 = (file: File): Promise<string> =>
  new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve((reader.result as string).split(',')[1]);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });

const avatarB64 = await fileToBase64(avatarFile);
await crmPost('/api/crm/users/me/update', { avatar_128: avatarB64 });
```

---

### `POST /api/crm/users/me/change_password` — Change Password

| Param | Type | Required | Notes |
|-------|------|----------|-------|
| `current_password` | `string` | **Yes** | Must match existing password |
| `new_password` | `string` | **Yes** | Min 8 chars, must include letters + digits |

**Response `data`:** `{ message: "Password changed successfully" }`

**Error cases:**
- `current_password` wrong → `{ success: false, error: "Current password is incorrect" }`
- Weak password → `{ success: false, error: "new_password must be at least 8 characters..." }`

**Example:**
```typescript
const { success, error } = await crmPost('/api/crm/users/me/change_password', {
  current_password: form.currentPassword,
  new_password:     form.newPassword,
});

if (!success) showError(error);
else showSuccess('تم تغيير كلمة المرور بنجاح');
```

---

## Email Account Management (IMAP/SMTP)

> **Base path:** `/api/lugal/email/accounts`  
> **Protocol:** REST (not JSON-RPC)  
> **Auth:** `Authorization: Bearer {token}`

Managed by the `lugal_email` module. Each user can have **multiple** email accounts.

---

### List Accounts

```http
GET /api/lugal/email/accounts
```

Returns same `EmailAccount[]` as in `/api/crm/users/me` — use either.

---

### Add New Account

```http
POST /api/lugal/email/accounts
Content-Type: application/json

{
  "name":            "Work Gmail",
  "email_address":   "ahmed@company.com",
  "display_name":    "أحمد علي",
  "username":        "ahmed@company.com",
  "password":        "app-password-here",
  "imap_host":       "imap.gmail.com",
  "imap_port":       993,
  "imap_use_ssl":    true,
  "smtp_host":       "smtp.gmail.com",
  "smtp_port":       587,
  "smtp_use_tls":    true,
  "is_default":      false
}
```

**Required:** `name`, `email_address`  
**Response:** `{ success: true, data: EmailAccount }`

---

### Update Account

```http
PATCH /api/lugal/email/accounts/{id}
Content-Type: application/json

{ "name": "New Label", "is_active": false }
```

All fields optional. **Note:** `password` can be updated here to change IMAP/SMTP credentials.  
**Response:** `{ success: true, data: EmailAccount }`

---

### Delete Account

```http
DELETE /api/lugal/email/accounts/{id}
```

Deletes the account and all its synced messages.  
**Response:** `{ success: true, data: { deleted: true, id: number } }`

---

### Test IMAP Connection

```http
POST /api/lugal/email/accounts/{id}/test
```

Tests the IMAP connection with the stored credentials.  
**Response (success):** `{ success: true, data: { status: "ok" } }`  
**Response (fail):** `{ success: false, error: "IMAP connection failed: ..." }`

---

### Trigger Sync

```http
POST /api/lugal/email/accounts/{id}/sync
```

Triggers an incremental IMAP sync (only fetches new UIDs since last sync).  
**Response:** `{ success: true, data: { synced: number, account_id: number } }`

---

### Set as Default

```http
POST /api/lugal/email/accounts/{id}/set_default
```

Marks this account as the default for outgoing mail (unsets others).  
**Response:** `{ success: true, data: EmailAccount }`

---

### Full Settings Screen Flow

```typescript
// 1. Load profile + email accounts in one call
const { data: profile } = await crmPost('/api/crm/users/me', {});

// 2. Display profile section
renderProfileForm(profile);

// 3. Display email accounts section
renderEmailAccountsList(profile.email_accounts);

// 4. Add new account button
const addAccount = async (formData) => {
  const res = await posPost('/api/lugal/email/accounts', formData);
  if (res.success) {
    refreshEmailAccounts();
    showToast('تم إضافة الحساب بنجاح');
  }
};

// 5. Test connection
const testAccount = async (accountId: number) => {
  const res = await posPost(`/api/lugal/email/accounts/${accountId}/test`, {});
  showToast(res.success ? '✅ الاتصال ناجح' : `❌ ${res.error}`);
};

// 6. Sync account
const syncAccount = async (accountId: number) => {
  const res = await posPost(`/api/lugal/email/accounts/${accountId}/sync`, {});
  if (res.success) showToast(`تمت المزامنة — ${res.data.synced} رسالة جديدة`);
};
```

---

## Supply Chain — Email Linking

When an email in the inbox is related to a supply chain record, it can be linked to it. The link appears in `supply_links` on each email message.

### Link an Email to a Supply Record

```http
POST /api/lugal/email/messages/{id}/link

{
  "model":       "lugal.supply.negotiation",
  "record_id":   42,
  "record_name": "تفاوض على سعر الشحنة"
}
```

**Supported `model` values for supply chain:**
| Model | Description |
|-------|-------------|
| `lugal.supply.negotiation` | Link to a negotiation |
| `lugal.supply.container` | Link to a shipping container |
| `lugal.crm.supply.po` | Link to a purchase order |

**Response:** `{ success: true, data: { linked: true } }`

### Unlink

```http
POST /api/lugal/email/messages/{id}/unlink
```

**Response:** `{ success: true, data: { unlinked: true } }`

### `supply_links` in Message Response

When fetching messages, each message now includes:
```typescript
interface EmailMessage {
  // ... existing fields ...
  supply_links: {
    negotiation: { id: number; title: string } | null;
    container:   { id: number; name: string }  | null;
    po:          { id: number; name: string }  | null;
  };
  crm_links: {
    customer: { id: number; name: string } | null;
    ticket:   { id: number; name: string } | null;
  };
}
```

### Auto-link (Server-side)

When a new email arrives in the inbox from a vendor email address that matches an **open negotiation** (`status = open`), the server **automatically** links that email to the negotiation. No frontend action required.

---

## Updated Quick Reference

| # | Endpoint | Method | Module |
|---|----------|--------|--------|
| 46 | `/api/crm/users/me` | POST | lugal_crm |
| 47 | `/api/crm/users/me/update` | POST | lugal_crm |
| 48 | `/api/crm/users/me/change_password` | POST | lugal_crm |
| 49 | `/api/lugal/email/accounts` | GET | lugal_email |
| 50 | `/api/lugal/email/accounts` | POST | lugal_email |
| 51 | `/api/lugal/email/accounts/{id}` | PATCH | lugal_email |
| 52 | `/api/lugal/email/accounts/{id}` | DELETE | lugal_email |
| 53 | `/api/lugal/email/accounts/{id}/test` | POST | lugal_email |
| 54 | `/api/lugal/email/accounts/{id}/sync` | POST | lugal_email |
| 55 | `/api/lugal/email/accounts/{id}/set_default` | POST | lugal_email |
| 56 | `/api/lugal/email/messages/{id}/link` | POST | lugal_email |
| 57 | `/api/lugal/email/messages/{id}/unlink` | POST | lugal_email |

---

*Last updated: 2026-03-27 — Backend Team, NBS-CRM*
