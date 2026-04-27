# Supply Chain API Reference

**Base URL:** `http://localhost:8070`  
**Protocol:** JSON-RPC 2.0  
**Content-Type:** `application/json`  
**Auth:** JWT token in `Authorization: Bearer <token>` header

---

## Request Envelope

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": { /* endpoint-specific params */ }
}
```

## Success Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "data": { /* ... */ }
  }
}
```

## Error Response

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": false,
    "error": "Error message",
    "code": 404
  }
}
```

---

## Index

| # | Group | Endpoint | Method |
|---|-------|----------|--------|
| 1 | Containers | `/api/crm/supply/containers/list` | POST |
| 2 | Containers | `/api/crm/supply/containers/<id>/get` | POST |
| 3 | Containers | `/api/crm/supply/containers/create` | POST |
| 4 | Containers | `/api/crm/supply/containers/<id>/update` | POST |
| 5 | Containers | `/api/crm/supply/containers/<id>/delete` | POST |
| 6 | Containers | `/api/crm/supply/containers/<id>/clearance_delivered` | POST |
| 7 | Containers | `/api/crm/supply/containers/<id>/mark_arrived` | POST |
| 8 | Purchase Orders | `/api/crm/supply/po/list` | POST |
| 9 | Purchase Orders | `/api/crm/supply/po/<id>/get` | POST |
| 10 | Purchase Orders | `/api/crm/supply/po/create` | POST |
| 11 | Purchase Orders | `/api/crm/supply/po/<id>/update` | POST |
| 12 | Purchase Orders | `/api/crm/supply/po/<id>/delete` | POST |
| 13 | Purchase Orders | `/api/crm/supply/po/suggested` | POST |
| 14 | PO Lines | `/api/crm/supply/po/<id>/lines` | POST |
| 15 | PO Lines | `/api/crm/supply/po/<id>/lines/add` | POST |
| 16 | PO Lines | `/api/crm/supply/po/<id>/lines/<lid>/update` | POST |
| 17 | PO Lines | `/api/crm/supply/po/<id>/lines/<lid>/delete` | POST |
| 18 | Vendors | `/api/crm/supply/vendors/list` | POST |
| 19 | Vendors | `/api/crm/supply/vendors/<id>/get` | POST |
| 20 | Vendors | `/api/crm/supply/vendors/create` | POST |
| 21 | Vendors | `/api/crm/supply/vendors/<id>/update` | POST |
| 22 | Vendors | `/api/crm/supply/vendors/<id>/delete` | POST |
| 23 | Negotiations | `/api/crm/supply/negotiations/list` | POST |
| 24 | Negotiations | `/api/crm/supply/negotiations/<id>/get` | POST |
| 25 | Negotiations | `/api/crm/supply/negotiations/create` | POST |
| 26 | Negotiations | `/api/crm/supply/negotiations/<id>/update` | POST |
| 27 | Negotiations | `/api/crm/supply/negotiations/<id>/delete` | POST |
| 28 | Item Requests | `/api/crm/supply/item_requests/list` | POST |
| 29 | Item Requests | `/api/crm/supply/item_requests/<id>/get` | POST |
| 30 | Item Requests | `/api/crm/supply/item_requests/create` | POST |
| 31 | Item Requests | `/api/crm/supply/item_requests/<id>/update` | POST |
| 32 | Item Requests | `/api/crm/supply/item_requests/<id>/update_status` | POST |
| 33 | Item Requests | `/api/crm/supply/item_requests/<id>/delete` | POST |
| 34 | Clearance Companies | `/api/crm/supply/clearance_companies/list` | POST |
| 35 | Clearance Companies | `/api/crm/supply/clearance_companies/<id>/get` | POST |
| 36 | Clearance Companies | `/api/crm/supply/clearance_companies/create` | POST |
| 37 | Clearance Companies | `/api/crm/supply/clearance_companies/<id>/update` | POST |
| 38 | Clearance Companies | `/api/crm/supply/clearance_companies/<id>/delete` | POST |
| 39 | Inventory | `/api/crm/supply/inventory/minmax` | POST |
| 40 | Inventory | `/api/crm/supply/inventory/minmax/update` | POST |
| 41 | Inventory | `/api/crm/supply/inventory/minmax/delete` | POST |
| 42 | Conversations | `/api/crm/supply/conversations/list` | POST |
| 43 | Conversations | `/api/crm/supply/conversations/<id>/get` | POST |
| 44 | Conversations | `/api/crm/supply/conversations/<id>/archive` | POST |
| 45 | Conversations | `/api/crm/supply/conversations/<id>/rename` | POST |
| 46 | Messages | `/api/crm/supply/messages/list` | POST |
| 47 | Messages | `/api/crm/supply/messages/create` | POST |
| 48 | Messages | `/api/crm/supply/messages/<id>/delete` | POST |
| 49 | Users | `/api/crm/supply/users` | POST |
| 50 | Notifications | `/api/crm/supply/notifications/list` | POST |
| 51 | Notifications | `/api/crm/supply/notifications/create` | POST |
| 52 | Notifications | `/api/crm/supply/notifications/<id>/mark_read` | POST |
| 53 | Notifications | `/api/crm/supply/notifications/mark_all_read` | POST |
| 54 | Notifications | `/api/crm/supply/notifications/<id>/delete` | POST |

**Total: 54 endpoints**

---

## 1. Containers (حاويات الشحن)

---

### 1.1 List Containers

`POST /api/crm/supply/containers/list`

**Params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| page | int | No | Page number (default: 1) |
| per_page | int | No | Items per page (default: 50) |
| status | string | No | `waiting` \| `active` \| `at_port` \| `completed` |
| division | string | No | `europe` \| `china` |
| search | string | No | Search in name, container_number, bl_number |
| assigned_user_id | int | No | Filter by assigned user |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [ { /* container object */ } ],
    "total": 42,
    "page": 1,
    "per_page": 50
  }
}
```

**Container Object:**
```json
{
  "id": 1,
  "name": "CONT-2026-001",
  "container_number": "MSCU1234567",
  "bl_number": "BL20260001",
  "clearance_company_id": 3,
  "clearance_company_name": "Al-Sharq Clearance",
  "clearance_company": {
    "id": 3,
    "name": "Al-Sharq Clearance",
    "contact_name": "Ahmad",
    "phone": "+966501234567",
    "whatsapp": "+966501234567",
    "email": "ahmad@alsharq.com"
  },
  "origin_location": "Shanghai, China",
  "destination_port": "Jeddah Port",
  "departure_date": "2026-03-01",
  "eta": "2026-04-15",
  "arrived_at": null,
  "status": "active",
  "division": "china",
  "tracking_url": "https://www.searates.com/container/MSCU1234567",
  "total_weight_kg": 12500.0,
  "total_cbm": 28.5,
  "assigned_user_id": 2,
  "assigned_user_name": "Mohammed Ali",
  "po_uploaded_by_id": 3,
  "clearance_info_delivered": false,
  "clearance_info_delivered_at": null,
  "clearance_info_delivered_by": "",
  "attachment_count": 4,
  "notes": "Handle with care",
  "created_at": "2026-03-01T08:00:00",
  "updated_at": "2026-03-20T14:00:00"
}
```

---

### 1.2 Get Container

`POST /api/crm/supply/containers/<id>/get`

Returns full container object **including attachments array**.

---

### 1.3 Create Container

`POST /api/crm/supply/containers/create`

**Params:**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | **Yes** | Container display name |
| container_number | string | No | ISO container number |
| bl_number | string | No | Bill of lading number |
| status | string | No | Default: `waiting` |
| division | string | No | `europe` \| `china` |
| clearance_company_id | int | No | ID from clearance companies |
| origin_location | string | No | Origin city/country |
| destination_port | string | No | Destination port name |
| departure_date | string | No | ISO date `YYYY-MM-DD` |
| eta | string | No | ISO date `YYYY-MM-DD` |
| tracking_url | string | No | Searates or similar URL |
| assigned_user_id | int | No | User ID |
| total_weight_kg | float | No | Total weight in kg |
| total_cbm | float | No | Total cubic meters |
| notes | string | No | Internal notes |

---

### 1.4 Update Container

`POST /api/crm/supply/containers/<id>/update`

Pass any field from the create params to update.

---

### 1.5 Delete Container (Soft)

`POST /api/crm/supply/containers/<id>/delete`

**Response:**
```json
{ "success": true, "data": { "id": 1, "deleted": true } }
```

---

### 1.6 Mark Clearance Delivered

`POST /api/crm/supply/containers/<id>/clearance_delivered`

Sets `clearance_info_delivered=true`, records `clearance_info_delivered_at` and `clearance_info_delivered_by`.

---

### 1.7 Mark Arrived at Port

`POST /api/crm/supply/containers/<id>/mark_arrived`

Sets `status=at_port` and `arrived_at=now()`.

---

## 2. Purchase Orders (أوامر الشراء)

---

### 2.1 List POs

`POST /api/crm/supply/po/list`

**Params:**

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 50 |
| status | string | `draft` \| `confirmed` \| `received` \| `cancelled` |
| vendor_id | int | Filter by vendor |
| container_id | int | Filter by container |
| branch_id | int | Filter by branch |
| division | string | `europe` \| `china` |

---

### 2.2 Get PO (with lines)

`POST /api/crm/supply/po/<id>/get`

**PO Object:**
```json
{
  "id": 10,
  "name": "PO-2026-010",
  "vendor_id": 5,
  "vendor_name": "Lattafa Trading",
  "division": "china",
  "currency_id": 114,
  "currency_name": "USD",
  "container_id": 1,
  "container_name": "CONT-2026-001",
  "branch_id": 2,
  "branch_name": "Riyadh Branch",
  "status": "confirmed",
  "is_suggested": false,
  "line_count": 3,
  "total_amount": 15000.00,
  "lines": [ { /* line object */ } ],
  "created_at": "2026-03-10T09:00:00",
  "updated_at": "2026-03-15T11:00:00"
}
```

---

### 2.3 Create PO

`POST /api/crm/supply/po/create`

| Param | Type | Required |
|-------|------|----------|
| name | string | **Yes** |
| vendor_id | int | **Yes** |
| division | string | No |
| container_id | int | No |
| branch_id | int | No |
| currency_id | int | No |

---

### 2.4 Update PO

`POST /api/crm/supply/po/<id>/update`

Allowed fields: `name`, `vendor_id`, `division`, `currency_id`, `container_id`, `branch_id`, `status`, `is_suggested`.

---

### 2.5 Delete PO (Soft)

`POST /api/crm/supply/po/<id>/delete`

---

### 2.6 List Suggested POs

`POST /api/crm/supply/po/suggested`

Returns POs with `is_suggested=true`.

---

### 2.7 List PO Lines

`POST /api/crm/supply/po/<id>/lines`

**Line Object:**
```json
{
  "id": 1,
  "sequence": 1,
  "product_name": "Oud Perfume 50ml",
  "item_code": "ADF00006",
  "uom": "Unit",
  "quantity": 100,
  "unit_price": 25.50,
  "total_price": 2550.00,
  "currency_id": 114,
  "currency_name": "USD",
  "last_purchase_price": 24.00,
  "last_purchase_date": "2025-12-01",
  "min_qty": 20,
  "max_qty": 200
}
```

---

### 2.8 Add PO Line

`POST /api/crm/supply/po/<id>/lines/add`

| Param | Type | Required |
|-------|------|----------|
| product_name | string | No |
| item_code | string | No |
| uom | string | No |
| quantity | float | No (default 1) |
| unit_price | float | No (default 0) |
| currency_id | int | No |
| min_qty | float | No |
| max_qty | float | No |

---

### 2.9 Update PO Line

`POST /api/crm/supply/po/<id>/lines/<line_id>/update`

Pass any field from add params.

---

### 2.10 Delete PO Line (Hard Delete)

`POST /api/crm/supply/po/<id>/lines/<line_id>/delete`

---

## 3. Vendors (موردون)

---

### 3.1 List Vendors

`POST /api/crm/supply/vendors/list`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 50 |
| search | string | Search name, name_ar, contact, phone |
| division | string | `europe` \| `china` \| `other` |

**Vendor Object:**
```json
{
  "id": 5,
  "name": "Lattafa Trading Co.",
  "name_ar": "شركة لطافة للتجارة",
  "division": "china",
  "contact_name": "Mr. Zhang Wei",
  "phone": "+8613812345678",
  "email": "zhang@lattafa.cn",
  "website": "https://lattafa.cn",
  "whatsapp": "+8613812345678",
  "wechat": "zhang_wei_lattafa",
  "telegram": "@zhang_lattafa",
  "country_id": 44,
  "country_name": "China",
  "city": "Guangzhou",
  "address": "Room 502, Trade Tower, Guangzhou",
  "payment_terms": "30% advance, 70% on BL",
  "currency_id": 114,
  "currency_name": "USD",
  "lead_time_days": 45,
  "min_order_value": 5000.00,
  "partner_id": null,
  "partner_name": "",
  "notes": "Preferred supplier for oud",
  "created_at": "2026-01-15T10:00:00"
}
```

---

### 3.2 Get Vendor

`POST /api/crm/supply/vendors/<id>/get`

---

### 3.3 Create Vendor

`POST /api/crm/supply/vendors/create`

| Param | Type | Required |
|-------|------|----------|
| name | string | **Yes** |
| name_ar | string | No |
| division | string | No |
| contact_name | string | No |
| phone | string | No |
| email | string | No |
| website | string | No |
| whatsapp | string | No |
| wechat | string | No |
| telegram | string | No |
| country_id | int | No |
| city | string | No |
| address | string | No |
| payment_terms | string | No |
| currency_id | int | No |
| lead_time_days | int | No |
| min_order_value | float | No |
| notes | string | No |

---

### 3.4 Update Vendor

`POST /api/crm/supply/vendors/<id>/update`

Pass any field from create.

---

### 3.5 Delete Vendor (Soft)

`POST /api/crm/supply/vendors/<id>/delete`

---

## 4. Negotiations (تفاوضات)

---

### 4.1 List Negotiations

`POST /api/crm/supply/negotiations/list`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 20 |
| status | string | `open` \| `pending` \| `closed` |
| supply_vendor_id | int | Filter by supply vendor |
| vendor_id | int | Filter by Odoo partner |
| product_id | int | Filter by product |

**Negotiation Object:**
```json
{
  "id": 1,
  "supply_vendor_id": 5,
  "supply_vendor_name": "Lattafa Trading Co.",
  "vendor_id": null,
  "vendor_name": "",
  "product_id": 102,
  "product_name": "Oud Noir 100ml",
  "title": "Q2 2026 Bulk Purchase Negotiation",
  "description": "Negotiating bulk price for summer season",
  "quantity": 500.0,
  "expected_price": 22.50,
  "agreed_price": 21.00,
  "currency_id": 114,
  "currency_name": "USD",
  "status": "open",
  "due_date": "2026-04-30",
  "notes": "Discussed 3% discount on 500+ units",
  "created_by_id": 2,
  "created_by_name": "Mohammed Ali",
  "created_at": "2026-03-01T10:00:00",
  "updated_at": "2026-03-15T14:00:00"
}
```

---

### 4.2 Get Negotiation

`POST /api/crm/supply/negotiations/<id>/get`

---

### 4.3 Create Negotiation

`POST /api/crm/supply/negotiations/create`

| Param | Type | Required |
|-------|------|----------|
| title | string | **Yes** |
| supply_vendor_id | int | No (recommended) |
| vendor_id | int | No |
| product_id | int | No |
| description | string | No |
| quantity | float | No |
| expected_price | float | No |
| currency_id | int | No |
| due_date | string | No (YYYY-MM-DD) |
| notes | string | No |

---

### 4.4 Update Negotiation

`POST /api/crm/supply/negotiations/<id>/update`

Allowed: `title`, `description`, `quantity`, `expected_price`, `agreed_price`, `status`, `due_date`, `notes`, `vendor_id`, `supply_vendor_id`, `product_id`, `currency_id`.

---

### 4.5 Delete Negotiation (Soft)

`POST /api/crm/supply/negotiations/<id>/delete`

---

## 5. Item Requests (طلبات أصناف)

---

### 5.1 List Item Requests

`POST /api/crm/supply/item_requests/list`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 20 |
| status | string | `pending` \| `approved` \| `rejected` \| `fulfilled` |
| branch_id | int | Filter by branch |
| product_id | int | Filter by product |

**Item Request Object:**
```json
{
  "id": 7,
  "product_id": 102,
  "product_name": "Oud Noir 100ml",
  "product_sku": "ADF00429",
  "quantity": 50.0,
  "uom": "Unit",
  "branch_id": 2,
  "branch_name": "Riyadh Branch",
  "requested_by_id": 4,
  "requested_by_name": "Sara Ahmed",
  "status": "pending",
  "note": "Urgent — running low",
  "created_at": "2026-03-25T08:00:00",
  "updated_at": "2026-03-25T08:00:00"
}
```

---

### 5.2 Get Item Request

`POST /api/crm/supply/item_requests/<id>/get`

---

### 5.3 Create Item Request

`POST /api/crm/supply/item_requests/create`

| Param | Type | Required |
|-------|------|----------|
| product_id | int | **Yes** |
| quantity | float | No (default 1) |
| uom | string | No |
| branch_id | int | No |
| note | string | No |

---

### 5.4 Full Update

`POST /api/crm/supply/item_requests/<id>/update`

Allowed: `product_id`, `quantity`, `uom`, `branch_id`, `note`, `status`.

---

### 5.5 Update Status

`POST /api/crm/supply/item_requests/<id>/update_status`

| Param | Type | Required | Values |
|-------|------|----------|--------|
| status | string | **Yes** | `pending` \| `approved` \| `rejected` \| `fulfilled` |

> Automatically notifies the requester when status changes.

---

### 5.6 Delete (Soft)

`POST /api/crm/supply/item_requests/<id>/delete`

---

## 6. Clearance Companies (شركات التخليص)

---

### 6.1 List Clearance Companies

`POST /api/crm/supply/clearance_companies/list`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 20 |
| search | string | Search name or contact |
| is_active | bool | Filter active/inactive |

**Clearance Company Object:**
```json
{
  "id": 3,
  "name": "Al-Sharq Clearance",
  "contact_name": "Ahmad Khalil",
  "phone": "+966501234567",
  "email": "ahmad@alsharq.com",
  "whatsapp": "+966501234567",
  "telegram": "@ahmad_alsharq",
  "country_id": 187,
  "country_name": "Saudi Arabia",
  "city": "Jeddah",
  "address": "Port Area, Warehouse 12",
  "license_number": "SAC-2024-00123",
  "license_expiry": "2027-01-01",
  "notes": "",
  "is_active": true
}
```

---

### 6.2 Get Clearance Company

`POST /api/crm/supply/clearance_companies/<id>/get`

---

### 6.3 Create Clearance Company

`POST /api/crm/supply/clearance_companies/create`

| Param | Type | Required |
|-------|------|----------|
| name | string | **Yes** |
| contact_name | string | No |
| phone | string | No |
| email | string | No |
| whatsapp | string | No |
| telegram | string | No |
| country_id | int | No |
| city | string | No |
| address | string | No |
| license_number | string | No |
| license_expiry | string | No (YYYY-MM-DD) |
| notes | string | No |

---

### 6.4 Update Clearance Company

`POST /api/crm/supply/clearance_companies/<id>/update`

Pass any field from create + `is_active`.

---

### 6.5 Delete (Soft)

`POST /api/crm/supply/clearance_companies/<id>/delete`

---

## 7. Min/Max Inventory (حدود المخزون)

---

### 7.1 List Min/Max Records

`POST /api/crm/supply/inventory/minmax`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 50 |
| branch_id | int | Filter by branch |
| category_id | int | Filter by product category |
| search | string | Search product name |
| needs_reorder | bool | Filter items below min_qty |

**Min/Max Object:**
```json
{
  "id": 12,
  "product_id": 102,
  "product_name": "Oud Noir 100ml",
  "sku": "ADF00429",
  "category": "Perfumes",
  "uom": "Unit",
  "current_stock": 15.0,
  "min_qty": 20.0,
  "max_qty": 200.0,
  "branch_id": 2,
  "branch_name": "Riyadh Branch",
  "needs_reorder": true
}
```

---

### 7.2 Create or Update Min/Max (Upsert)

`POST /api/crm/supply/inventory/minmax/update`

| Param | Type | Required |
|-------|------|----------|
| product_id | int | **Yes** |
| min_qty | float | **Yes** |
| max_qty | float | **Yes** |
| branch_id | int | No (use 0 for global) |

Creates a new record if none exists for `(product_id, branch_id)`, otherwise updates it.

---

### 7.3 Delete Min/Max Record

`POST /api/crm/supply/inventory/minmax/delete`

| Param | Type | Required |
|-------|------|----------|
| product_id | int | **Yes** |
| branch_id | int | No |

---

## 8. Conversations (محادثات داخلية)

The messaging system has three conversation types:

| Type | Description |
|------|-------------|
| `team` | Main/broadcast channel — visible to all users |
| `dm` | Direct message between 2 users |
| `group` | Group chat with 3+ participants |

---

### 8.1 List My Conversations

`POST /api/crm/supply/conversations/list`

Returns team channel first (always pinned), then DMs and groups sorted by `last_activity` desc.

**Conversation Object:**
```json
{
  "id": 1,
  "type": "team",
  "name": "Team Channel",
  "participant_ids": [2, 3, 4],
  "participants": [
    { "id": 2, "name": "Mohammed Ali", "avatar": "/web/image/res.users/2/avatar_128" }
  ],
  "message_count": 42,
  "last_activity": "2026-03-27T10:00:00",
  "is_archived": false
}
```

---

### 8.2 Get Conversation

`POST /api/crm/supply/conversations/<id>/get`

---

### 8.3 Archive Conversation

`POST /api/crm/supply/conversations/<id>/archive`

Only DM and group conversations can be archived. Team channel cannot be archived.

---

### 8.4 Rename Group

`POST /api/crm/supply/conversations/<id>/rename`

| Param | Type | Required |
|-------|------|----------|
| name | string | **Yes** |

Only `group` type conversations can be renamed.

---

## 9. Messages (رسائل)

---

### 9.1 List Messages

`POST /api/crm/supply/messages/list`

| Param | Type | Description |
|-------|------|-------------|
| thread_id | int | Conversation ID. `0` or omit → team channel |
| page | int | Default 1 |
| per_page | int | Default 30 |

Messages are returned in chronological order (`asc`).

**Message Object:**
```json
{
  "id": 55,
  "thread_id": 1,
  "conversation_type": "team",
  "sender_id": 2,
  "sender_name": "Mohammed Ali",
  "sender_avatar": "/web/image/res.users/2/avatar_128",
  "recipient_ids": [],
  "participant_ids": [2, 3, 4],
  "participants": [ { "id": 2, "name": "Mohammed Ali", "avatar": "..." } ],
  "content": "The container has arrived at port.",
  "attachments": [],
  "created_at": "2026-03-27T10:00:00"
}
```

---

### 9.2 Send Message

`POST /api/crm/supply/messages/create`

| Param | Type | Description |
|-------|------|-------------|
| content | string | **Required** — message text |
| thread_id | int | Use existing conversation ID |
| recipient_ids | array | User IDs. Empty → team; 1 → DM; 2+ → group |
| group_name | string | Name for new group (optional) |
| attachments | array | List of attachment metadata objects |

**Conversation resolution:**
- `thread_id` provided → post to that conversation
- No `thread_id`, no `recipient_ids` → team channel
- No `thread_id`, 1 `recipient_id` → DM (finds or creates)
- No `thread_id`, 2+ `recipient_ids` → create new group

```json
// Team message
{ "content": "Hello team!" }

// DM
{ "content": "Hi Sara!", "recipient_ids": [4] }

// Group
{ "content": "Q2 planning", "recipient_ids": [3, 4, 5], "group_name": "Q2 Group" }

// Reply in existing thread
{ "content": "Got it!", "thread_id": 7 }
```

---

### 9.3 Delete Message

`POST /api/crm/supply/messages/<id>/delete`

Only the sender can delete their own message.

---

## 10. Users (للتعيين والرسائل)

---

### 10.1 List Users

`POST /api/crm/supply/users`

| Param | Type | Description |
|-------|------|-------------|
| search | string | Filter by name |

**User Object:**
```json
{
  "id": 2,
  "name": "Mohammed Ali",
  "email": "m.ali@company.com",
  "job_position": "Supply Manager",
  "avatar": "/web/image/res.users/2/avatar_128"
}
```

---

## 11. Notifications (إشعارات)

---

### 11.1 List Notifications

`POST /api/crm/supply/notifications/list`

| Param | Type | Description |
|-------|------|-------------|
| page | int | Default 1 |
| per_page | int | Default 20 |
| is_read | bool | Filter read/unread |

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [ { /* notification object */ } ],
    "total": 15,
    "unread_count": 3,
    "page": 1,
    "per_page": 20
  }
}
```

**Notification Object:**
```json
{
  "id": 10,
  "type": "container_arrived",
  "title": "Container Arrived",
  "body": "CONT-2026-001 has arrived at Jeddah Port.",
  "related_id": 1,
  "related_type": "lugal.supply.container",
  "is_read": false,
  "created_at": "2026-03-27T09:00:00"
}
```

**Notification Types:**

| Type | Trigger |
|------|---------|
| `po_created` | New PO was created |
| `container_arrived` | Container marked at_port |
| `clearance_done` | Clearance info delivered |
| `low_stock` | Product below min_qty |
| `negotiation_update` | Negotiation status changed |
| `item_request_update` | Item request approved/rejected |
| `general` | Manual/custom notification |

---

### 11.2 Create (Push) Notification

`POST /api/crm/supply/notifications/create`

| Param | Type | Required |
|-------|------|----------|
| user_id | int | **Yes** |
| notif_type | string | **Yes** (see types above) |
| title | string | **Yes** |
| body | string | No |
| related_id | int | No |
| related_type | string | No (e.g. `lugal.supply.container`) |

---

### 11.3 Mark Single Read

`POST /api/crm/supply/notifications/<id>/mark_read`

---

### 11.4 Mark All Read

`POST /api/crm/supply/notifications/mark_all_read`

**Response:**
```json
{ "success": true, "data": { "marked": 5 } }
```

---

### 11.5 Delete Notification

`POST /api/crm/supply/notifications/<id>/delete`

---

## Full Request Examples

### Create container and link clearance company

```json
POST /api/crm/supply/containers/create
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "name": "CONT-Q2-001",
    "container_number": "MSCU9876543",
    "bl_number": "BL20260050",
    "division": "china",
    "clearance_company_id": 3,
    "origin_location": "Guangzhou",
    "destination_port": "Jeddah",
    "departure_date": "2026-04-01",
    "eta": "2026-05-10",
    "total_weight_kg": 14000,
    "total_cbm": 32
  }
}
```

### Start a DM conversation

```json
POST /api/crm/supply/messages/create
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "content": "Can you check the latest ETA for CONT-Q2-001?",
    "recipient_ids": [3]
  }
}
```

Response:
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 88,
      "thread_id": 14,
      "conversation_type": "dm",
      "sender_id": 2,
      "sender_name": "Mohammed Ali",
      "recipient_ids": [3],
      "participant_ids": [2, 3],
      "content": "Can you check the latest ETA for CONT-Q2-001?",
      "created_at": "2026-03-27T11:30:00"
    }
  }
}
```

### Negotiate with a supply vendor

```json
POST /api/crm/supply/negotiations/create
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "title": "Q3 Bulk Discount — Oud Line",
    "supply_vendor_id": 5,
    "product_id": 102,
    "quantity": 1000,
    "expected_price": 20.00,
    "due_date": "2026-05-01",
    "notes": "Targeting 10% off for 1000+ units"
  }
}
```

### Low stock alert notification

```json
POST /api/crm/supply/notifications/create
{
  "jsonrpc": "2.0", "method": "call", "id": 1,
  "params": {
    "user_id": 2,
    "notif_type": "low_stock",
    "title": "Low Stock Alert",
    "body": "Oud Noir 100ml is below minimum (current: 15, min: 20)",
    "related_id": 102,
    "related_type": "product.product"
  }
}
```
