# API Changes & Documentation

> **Last updated:** 2026-03-24  
> This document covers all backend API changes made recently — updated request bodies, new fields, and full response type contracts.  
> All endpoints use **JSON-RPC 2.0** (CRM) or **REST** (POS / Inventory) over HTTP.

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [CRM — Customers](#2-crm--customers)
3. [CRM — Tickets](#3-crm--tickets)
4. [POS Perfume — Products](#4-pos-perfume--products)
5. [POS Perfume — Orders](#5-pos-perfume--orders)
6. [Inventory](#6-inventory)

---

## 1. Authentication

### All CRM Endpoints (JSON-RPC)

Send the `lugal_auth` JWT in every request header:

```
Authorization: Bearer <access_token>
```

> Obtained from `POST /lugal/auth/login`  
> Token payload: `{ jti, user_id, username, exp, iat, type: "access" }`

### POS Perfume Endpoints (REST)

**Now accepts the same `lugal_auth` JWT** (previously required an Odoo API key).

Priority order:
1. `lugal_auth` JWT → verified via `lugal.jwt.service`
2. Odoo API key → verified via `res.users.apikeys`
3. Session cookie → browser fallback

---

## 2. CRM — Customers

Base URL: `/api/crm/customers`  
Protocol: `POST` with JSON-RPC 2.0 body

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "call",
  "params": { ...fields... }
}
```

---

### `POST /api/crm/customers/list` — List / Search Customers

#### ✅ What Changed
- Now accepts `query`, `limit`, `offset` **in addition to** the old `search`, `per_page`, `page`
- `query` searches: `name`, `name_ar`, `phone_1`, `email`
- If `query` is a **pure integer string** (e.g. `"42"`), also searches by customer `id`

#### Request Body `params`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | `string` | No | Search term (name / phone / email / id) |
| `limit` | `number` | No | Items per page (default: `50`) |
| `offset` | `number` | No | Records to skip (default: `0`) |
| `stage_id` | `number` | No | Filter by CRM stage ID |
| `branch_id` | `number` | No | Filter by branch ID |
| `vip_only` | `boolean` | No | Only return VIP customers |
| `search` | `string` | No | *(legacy alias for `query`)* |
| `page` | `number` | No | *(legacy — use `offset` instead)* |
| `per_page` | `number` | No | *(legacy alias for `limit`)* |

#### Response

```json
{
  "success": true,
  "data": {
    "items": [ <Customer> ],
    "total": 120,
    "limit": 20,
    "offset": 0,
    "page": 1,
    "per_page": 20
  }
}
```

#### Customer Object

```typescript
interface Customer {
  id: number;
  name: string;
  name_ar: string;
  partner_id: number | null;
  phone_1: string;
  phone_2: string;
  phone_3: string;
  email: string;
  address: string;
  city: string;
  state: string;
  district: string;
  building: string;
  postal_code: string;
  country_id: number | null;
  country_name: string;
  shipping_address: string;
  billing_address: string;
  billing_method: string;
  stage_id: number | null;
  stage_name: string;
  stage_type: string;
  tag_ids: number[];
  tag_names: string[];
  vip_status: boolean;
  is_enterprise: boolean;
  account_manager_id: number | null;
  account_manager_name: string;
  account_manager_phone: string;
  branch_ids: number[];
  branches: Branch[];
  referral_source: string;
  shop_name: string;
  shop_location: string;
  loyalty_points: number;
  preferred_contact_time: string;
  preferred_contact_channel: string;
  credit_limit: number;
  lifetime_value: number;
  credit_debt: number;
  member_since: string | null;      // ISO 8601
  last_call_date: string | null;
  last_purchase_date: string | null;
  days_since_purchase: number;
  open_invoice_status: string;
  delivery_status: string;
  created_at: string | null;
  updated_at: string | null;
  // Social handles
  instagram_handle: string;
  tiktok_handle: string;
  whatsapp_number: string;
  snapchat_handle: string;
  twitter_handle: string;
  telegram_handle: string;
  pinterest_handle: string;
  youtube_handle: string;
  channel_identities: ChannelIdentity[];
  // Extended
  activity_type: string;
  customer_strength: string;
  dealing_method: string;
  customer_rating: number;
  assigned_agent: string;
  notes: string;
  shop_images: string[];
  customer_docs: object[];
  attachments: Attachment[];
  samples: Sample[];
  favorite_fragrance: string;
  // Populated only in get_customer detail call
  total_orders: number;
  activity_timeline: TimelineItem[];
  call_log: CallLog[];
  payments: Payment[];
  tickets: TicketSummary[];
  follow_ups: FollowUp[];
  internal_notes: InternalNote[];
  top_products: TopProduct[];
}
```

---

## 3. CRM — Tickets

Base URL: `/api/crm/tickets`

---

### `POST /api/crm/tickets/list` — List Tickets

#### ✅ What Changed
- Now uses `.sudo()` — `assigned_to_id` and `assigned_to_name` are **always populated** correctly

#### Request Body `params`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `page` | `number` | No | Page number (default: `1`) |
| `per_page` | `number` | No | Items per page (default: `50`) |
| `customer_id` | `number` | No | Filter by customer |
| `branch_id` | `number` | No | Filter by branch |
| `status` | `string` | No | `open` \| `in_progress` \| `resolved` \| `closed` \| `stale` |
| `priority` | `string` | No | `low` \| `medium` \| `high` \| `urgent` |
| `assigned_to_id` | `number` | No | Filter by assigned agent |

#### Response

```json
{
  "success": true,
  "data": {
    "items": [ <Ticket> ],
    "total": 15,
    "page": 1,
    "per_page": 50
  }
}
```

---

### `POST /api/crm/tickets/create` — Create Ticket

#### ✅ What Changed
- `assigned_to_id` now **saves correctly** (was silently ignored before)
- Added `classification` field (new)

#### Request Body `params`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `customer_id` | `number` | **Yes** | CRM customer ID |
| `title` | `string` | **Yes** | Ticket title |
| `description` | `string` | No | Ticket description |
| `branch_id` | `number` | No | Branch ID |
| `ticket_type` | `string` | No | e.g. `complaint`, `inquiry` |
| `channel` | `string` | No | `whatsapp` \| `instagram` \| `phone` \| `email` \| etc. |
| `classification` | `string` | No | e.g. `general`, `complaint`, `billing`, etc. |
| `assigned_to_id` | `number` | No | `res.users` ID of agent to assign |
| `priority` | `string` | No | `low` \| `medium` (default) \| `high` \| `urgent` |
| `sla_deadline` | `string` | No | ISO 8601 datetime |

#### Response

```json
{
  "success": true,
  "data": <Ticket>
}
```

---

### `POST /api/crm/tickets/<id>/assign` — Assign Ticket

#### ✅ What Changed
- `assigned_to_id` was a **required positional argument** causing a 500 error when not passed
- Now optional with default `null` — returns a clear `400` error if missing

#### Request Body `params`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `assigned_to_id` | `number` | **Yes** | `res.users` ID of agent |

#### Response

```json
{
  "success": true,
  "data": <Ticket>
}
```

---

### `POST /api/crm/tickets/<id>/update` — Update Ticket

#### ✅ What Changed
- Added `classification` to allowed update fields
- Added `assigned_to_id` to allowed update fields

#### Request Body `params`  
*(all fields optional)*

| Field | Type | Description |
|-------|------|-------------|
| `title` | `string` | |
| `description` | `string` | |
| `ticket_type` | `string` | |
| `channel` | `string` | |
| `classification` | `string` | **New** |
| `priority` | `string` | |
| `sla_deadline` | `string` | ISO 8601 |
| `branch_id` | `number` | |
| `assigned_to_id` | `number` | **New** |

---

### Ticket Object (Full Response Contract)

```typescript
interface Ticket {
  id: number;
  customer_id: number | null;
  customer_name: string;
  branch_id: number | null;
  assigned_to_id: number | null;     // ✅ now always populated
  assigned_to_name: string;           // ✅ now always populated
  escalated_to_id: number | null;
  escalated_to_name: string;
  title: string;
  description: string;
  ticket_type: string;
  channel: string;                    // ✅ included in create
  classification: string;             // ✅ NEW field
  status: 'open' | 'in_progress' | 'resolved' | 'closed' | 'stale';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  sla_deadline: string | null;        // ISO 8601
  first_response_at: string | null;
  resolved_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}
```

---

## 4. POS Perfume — Products

Base URL: `/api/pos_perfume/v1`  
Protocol: REST (GET / POST)

---

### `GET /api/pos_perfume/v1/products` — List / Search Products

#### ✅ What Changed
- Now accepts **`categ_id`** query param (frontend-facing name) in addition to `category_id`
- Filter applies **exact category match** only (no child category expansion)

#### Query Parameters

| Param | Type | Description |
|-------|------|-------------|
| `query` | `string` | Search by name, default_code, or foreign_name |
| `limit` | `number` | Items per page (default: `80`) |
| `offset` | `number` | Records to skip (default: `0`) |
| `pricelist_id` | `number` | Pricelist ID for prices |
| `categ_id` | `number` | **New** — Filter by exact `product.category` ID |
| `category_id` | `number` | *(legacy alias for `categ_id`)* |
| `brand` | `string` | Brand key — see Brand Keys table below |
| `category_type` | `string` | Section key (e.g. `fragrances`, `glass`, `packaging`) |
| `has_price_only` | `1` \| `0` | Only return products with price > 0 |

#### Brand Keys Reference

| `brand` param value | Display Name | Notes |
|---------------------|-------------|-------|
| `adf` or `amour_de_fleurs` | Amour de Fleurs | |
| `royal` | Royal (Robertet) | ✅ اسم جديد — `robertet` لا يزال يعمل كـ alias |
| `robertet` | Robertet | *(legacy alias لـ `royal`)* |
| `givaudan` | Givaudan | |
| `european` or `euro` | European / Euro | |
| `florchem` | Florchem | |
| `firmenic` | Firmenic | |
| `premium` | Premium | |
| `maison` | Maison | |
| `local` | Local | |
| `mix` | Mix | |
| `samples` | Samples | |
| `crystal_glass` | Crystal / Glass | |
| `pack` | Pack / Set | |
| `packaging` | Box Packaging | |
| `alcohol` | Alcohol | |

#### Category Type Keys Reference

| `category_type` param value | Display Name |
|-----------------------------|-------------|
| `fragrances` | Fragrances |
| `glass` | Glass |
| `samples` | Samples |
| `pack` | Pack / Set |
| `packaging` | Box Packaging |
| `alcohol` | Alcohol |
| `accessories` | Accessories |
| `devices` | Devices |
| `incense` | Incense |

#### Example Requests

```
GET /api/pos_perfume/v1/products?brand=robertet&pricelist_id=1&limit=20
GET /api/pos_perfume/v1/products?brand=givaudan&limit=20&offset=0
GET /api/pos_perfume/v1/products?category_type=fragrances&pricelist_id=1
GET /api/pos_perfume/v1/products?categ_id=16&limit=20
GET /api/pos_perfume/v1/products?brand=adf&categ_id=16&pricelist_id=1
```

#### Response

```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 45,
    "offset": 0,
    "limit": 20,
    "items": [ <Product> ]
  }
}
```

#### Product Object

```typescript
interface Product {
  id: number;
  name: string;
  default_code: string;
  foreign_name: string;
  uom_id: { id: number; name: string };
  list_price: number;
  qty_available: number;
  color_class: string;
  badge_text: string;
  active: boolean;
  sale_ok: boolean;
  categ_id: { id: number; name: string };
  items_group_code: number;
  items_group_name: string;
  brand: {
    key: string;
    name: string;
    code: string;
  };
  category_type: {
    type: string;
    name: string;
    name_ar: string;
    properties: object;
  };
  available_uoms: Array<{
    id: number;
    name: string;
    price: number;
  }>;
  has_price: boolean;
  warehouses: Array<{
    id: number;
    name: string;
    code: string;
    quantity: number;
  }>;
}
```

---

## 5. POS Perfume — Orders

Base URL: `/api/pos_perfume/v1/orders`  
Protocol: REST

### Authentication Fix

`GET /api/pos_perfume/v1/orders` (and all `/api/pos_perfume/v1/*` endpoints) now accept the **`lugal_auth` JWT Bearer token** directly.

Previously returned `{"success": false, "error": "Invalid API key"}` when a JWT was passed.

---

## 6. Inventory

Base URL: `/api/inventory/v1`  
Protocol: REST with JWT Bearer auth (from `/api/inventory/v1/auth/login`)

> No breaking changes. Fields added/fixed:

### Users — `POST /api/inventory/v1/users`

#### ✅ What Changed
- Creating a new user no longer fails with `"Invalid field 'groups_id' in res.users"` (Odoo 17 fix)
- Two-step creation: user created first, then `base.group_user` granted via `write()`

#### Request Body

```json
{
  "username": "john_doe",
  "full_name": "John Doe",
  "password": "secure123",
  "role": "user",
  "warehouse_id": 5
}
```

Or to import an existing Odoo user:

```json
{
  "odoo_user_id": 12,
  "full_name": "John Doe",
  "role": "admin",
  "warehouse_id": 5
}
```

---

## Common Error Responses

All APIs return errors in a consistent envelope:

### CRM (JSON-RPC)
```json
{
  "success": false,
  "error": "Error message here"
}
```

### POS / Inventory (REST)
```json
{
  "success": false,
  "error": "Error message here"
}
```

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| `200` | Success |
| `400` | Bad request / validation error |
| `401` | Unauthorized — missing or invalid token |
| `404` | Record not found |
| `500` | Internal server error |

---

## Shared Type Definitions

```typescript
interface Branch {
  id: number;
  name: string;
  name_ar: string;
  code: string;
  city: string;
  branch_location: string;
  branch_phone: string;
  branch_manager: string;
}

interface ChannelIdentity {
  channel: string;   // instagram | tiktok | whatsapp | snapchat | x | telegram | pinterest | youtube
  handle: string;
  verified: boolean;
  is_primary: boolean;
}

interface Attachment {
  id: number;
  name: string;
  mimetype: string;
  url: string;        // /web/content/<id>?download=true
  uploaded_by: string;
}

interface Sample {
  id: string;
  name: string;
  version: string;
  dateSent: string | null;
  image: string;
}

interface TimelineItem {
  type: 'call' | 'interaction' | 'ticket' | 'message';
  id: number;
  timestamp: string | null;
  description: string;
  date: string | null;
  user: string;
}

interface CallLog {
  id: number;
  date: string | null;
  time: string;
  duration: string;
  agent: string;
  type: string;
  notes: string;
  action: string;
  aiSummary: string;
}

interface TopProduct {
  name: string;
  quantity: number;
  totalSpent: number;
  lastPurchase: string | null;
}

interface FollowUp {
  id: number;
  title: string;
  description: string;
  dueDate: string | null;
  assignedTo: string;
  assignedBy: string;
  priority: string;
  status: string;
}

interface InternalNote {
  id: number;
  body: string;
  date: string | null;
  internal_note_author: string;
  note_author: string;
}
```
