# `/api/crm/supply` — Complete API Reference
**Version:** 2.0 — Updated 2026-04-04
**Base URL:** `http://localhost:8070`

---

## Global Rules

| Property | Value |
|---|---|
| Method | `POST` (all endpoints) |
| Content-Type | `application/json` |
| Auth Header | `Authorization: Bearer <access_token>` |
| Token Endpoint | `POST /lugal/auth/login` → `result.data.access_token` |
| Login Params | `{ "username": "admin", "password": "admin" }` |

---

## JSON-RPC Envelope (required for every request)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { /* your params here */ }
}
```

## Standard Response Shape

```json
{ "result": { "success": true,  "data": { ... } } }
{ "result": { "success": false, "error": "Reason" } }
```

---

## 🏗️ ARCHITECTURE NOTE — Vendors = Contacts

Vendors and Customers share **one model** (`lugal.crm.customer`).
They are distinguished by the `contact_type` field:

| `contact_type` | Meaning |
|---|---|
| `customer` | CRM customer only |
| `vendor` | Supply vendor only |
| `both` | Customer AND vendor |

The vendor endpoints (`/api/crm/supply/vendors/...`) filter contacts where
`contact_type IN ('vendor', 'both')` automatically.

---

## 📦 SECTION 1 — VENDORS (Contacts)

### `POST /api/crm/supply/vendors/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "search": "armani",
    "division": "europe"
  }
}
```

> `division`: `europe` | `china` | `other`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3,
      "page": 1,
      "per_page": 20,
      "items": [
        {
          "id": 1913,
          "name": "Armani Beauty EU",
          "name_ar": "أرماني بيوتي أوروبا",
          "contact_type": "vendor",
          "division": "europe",
          "contact_name": "Armani Beauty EU",
          "phone": "+39-02-1234",
          "email": "eu@armani.com",
          "website": "",
          "whatsapp": "+39-347-9999",
          "wechat": "",
          "telegram": "",
          "country_id": null,
          "country_name": "",
          "city": "Milan",
          "address": "",
          "payment_terms": "NET30",
          "currency_id": null,
          "currency_name": "",
          "lead_time_days": 20,
          "min_order_value": 0.0,
          "partner_id": 1916,
          "partner_name": "Armani Beauty EU",
          "notes": "",
          "created_at": "2026-04-04T10:28:31.661291"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/vendors/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** Single vendor object under `data`.

---

### `POST /api/crm/supply/vendors/create`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name": "Chanel Fragrances",
    "name_ar": "شانيل للعطور",
    "division": "europe",
    "phone": "+33-1-4056-7890",
    "email": "pierre@chanel.com",
    "whatsapp": "+33-6-4056-7890",
    "wechat": "",
    "telegram": "",
    "website": "https://chanel.com",
    "country_id": 76,
    "city": "Paris",
    "address": "22 Rue Cambon, Paris",
    "payment_terms": "NET30",
    "lead_time_days": 20,
    "min_order_value": 5000.0,
    "notes": "Premium European supplier"
  }
}
```

> Only `name` is **required**. `contact_type` auto-set to `vendor`.

**Response:** Single vendor object under `data`.

---

### `POST /api/crm/supply/vendors/<id>/update`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "phone": "+33-1-9999-0000",
    "lead_time_days": 18,
    "payment_terms": "NET45",
    "contact_type": "both"
  }
}
```

> Send only changed fields. Use `contact_type: "both"` to mark as Customer+Vendor.

**Response:** Updated vendor object under `data`.

---

### `POST /api/crm/supply/vendors/<id>/delete`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** `{ "result": { "success": true, "data": { "id": 1913, "deleted": true } } }`

---

## 🚢 SECTION 2 — CONTAINERS

### `POST /api/crm/supply/containers/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "status": "in_transit",
    "division": "china",
    "search": "MSCU1234",
    "assigned_user_id": 2
  }
}
```

> `status`: `waiting` | `loading` | `in_transit` | `at_port` | `cleared` | `delivered`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 1, "page": 1, "per_page": 20,
      "items": [
        {
          "id": 1,
          "name": "Container #CONT-2026-001",
          "container_number": "MSCU1234567",
          "bl_number": "BL-2026-0042",
          "clearance_company_id": 1,
          "clearance_company_name": "Dubai Clearance Co.",
          "clearance_company": {
            "id": 1,
            "name": "Dubai Clearance Co.",
            "contact_name": "Ali Hassan",
            "phone": "+971-4-111-2222",
            "whatsapp": "+971-50-111-2222",
            "email": "ali@dubaicc.ae"
          },
          "origin_location": "Guangzhou, China",
          "destination_port": "Jebel Ali, Dubai",
          "departure_date": "2026-03-10T00:00:00",
          "eta": "2026-04-05T00:00:00",
          "arrived_at": null,
          "status": "in_transit",
          "division": "china",
          "tracking_url": "https://track.msc.com/MSCU1234567",
          "total_weight_kg": 12500.0,
          "total_cbm": 38.5,
          "assigned_user_id": 2,
          "assigned_user_name": "Admin",
          "po_uploaded_by_id": null,
          "clearance_info_delivered": false,
          "clearance_info_delivered_at": null,
          "clearance_info_delivered_by": "",
          "attachment_count": 2,
          "notes": "",
          "created_at": "2026-03-01T10:00:00",
          "updated_at": "2026-03-28T14:22:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/containers/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`

Response adds `attachments` array:
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1,
      "attachments": [
        {
          "id": 101,
          "name": "BL_document.pdf",
          "mimetype": "application/pdf",
          "url": "http://localhost:8070/web/content/101?access_token=abc123"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/containers/create`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name": "Container #CONT-2026-002",
    "container_number": "MSCU9876543",
    "bl_number": "BL-2026-0043",
    "status": "loading",
    "division": "china",
    "clearance_company_id": 1,
    "origin_location": "Shanghai, China",
    "destination_port": "Jebel Ali, Dubai",
    "departure_date": "2026-04-15",
    "eta": "2026-05-10",
    "tracking_url": "https://track.msc.com/MSCU9876543",
    "assigned_user_id": 2,
    "total_weight_kg": 8000.0,
    "total_cbm": 25.0,
    "notes": "Priority shipment"
  }
}
```

> Only `name` is **required**.

---

### `POST /api/crm/supply/containers/<id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "status": "at_port", "eta": "2026-04-03" }
}
```

---

### `POST /api/crm/supply/containers/<id>/mark_arrived`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
> Sets `status = at_port` + stamps `arrived_at` timestamp.

---

### `POST /api/crm/supply/containers/<id>/clearance_delivered`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
> Sets `clearance_info_delivered = true` + stamps who/when.

---

### `POST /api/crm/supply/containers/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

### `POST /api/crm/supply/containers/<id>/comments/list`

**Request:**
```json
{ "jsonrpc": "2.0", "method": "call", "params": { "page": 1, "per_page": 50 } }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 2, "page": 1, "per_page": 50,
      "items": [
        {
          "id": 55404,
          "body": "Container docs received from supplier ✅",
          "body_html": "<p>Container docs received from supplier ✅</p>",
          "author_id": 3,
          "author_name": "Admin",
          "author_avatar": "/web/image/res.users/2/avatar_128",
          "message_type": "comment",
          "subtype": "Discussions",
          "is_note": false,
          "created_at": "2026-04-04T08:57:04"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/containers/<id>/comments/add`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "body": "Customs clearance approved",
    "is_note": false
  }
}
```

> `is_note: true` = internal note | `false` = public comment. `body` is **required**.

---

### `POST /api/crm/supply/containers/<id>/comments/<msg_id>/delete`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
> Only the author can delete.

**Response:** `{ "result": { "success": true, "data": { "id": 55404, "deleted": true } } }`

---

## 📋 SECTION 3 — PURCHASE ORDERS (PO)

### `POST /api/crm/supply/po/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1, "per_page": 20,
    "status": "pending",
    "vendor_id": 1913,
    "container_id": 1,
    "branch_id": 3,
    "division": "china"
  }
}
```

> `status`: `draft` | `pending` | `confirmed` | `received` | `cancelled`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 2, "page": 1, "per_page": 20,
      "items": [
        {
          "id": 1,
          "name": "PO-2026-0001",
          "vendor_id": 1913,
          "vendor_name": "Armani Beauty EU",
          "division": "europe",
          "currency_id": 1,
          "currency_name": "USD",
          "container_id": 1,
          "container_name": "Container #CONT-2026-001",
          "branch_id": null,
          "branch_name": "",
          "status": "confirmed",
          "is_suggested": false,
          "line_count": 5,
          "total_amount": 48500.0,
          "created_at": "2026-03-05T09:00:00",
          "updated_at": "2026-03-20T11:30:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/po/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`

Response includes full `lines` array:
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1, "name": "PO-2026-0001",
      "vendor_id": 1913, "vendor_name": "Armani Beauty EU",
      "status": "confirmed", "total_amount": 48500.0,
      "lines": [
        {
          "id": 10,
          "sequence": 1,
          "product_name": "Acqua di Gio 200ml",
          "item_code": "ADG-200",
          "uom": "PCS",
          "quantity": 100.0,
          "unit_price": 85.0,
          "total_price": 8500.0,
          "currency_id": 1,
          "currency_name": "USD",
          "last_purchase_price": 82.0,
          "last_purchase_date": "2025-11-01",
          "min_qty": 50.0,
          "max_qty": 500.0
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/po/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name": "PO-2026-0002",
    "vendor_id": 1913,
    "division": "europe",
    "container_id": 1,
    "currency_id": 1
  }
}
```

> `name` and `vendor_id` are **required**. Returns PO with empty `lines: []`.

---

### `POST /api/crm/supply/po/<id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "status": "confirmed", "container_id": 2 }
}
```

---

### `POST /api/crm/supply/po/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

### `POST /api/crm/supply/po/suggested`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** Same list shape as po/list items.

---

### `POST /api/crm/supply/po/<id>/lines`

**Response:**
```json
{ "result": { "success": true, "data": { "po_id": 1, "items": [ /* line objects */ ] } } }
```

---

### `POST /api/crm/supply/po/<id>/lines/add`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "product_name": "Acqua di Gio 100ml",
    "item_code": "ADG-100",
    "uom": "PCS",
    "quantity": 200.0,
    "unit_price": 55.0,
    "currency_id": 1,
    "min_qty": 100.0,
    "max_qty": 1000.0
  }
}
```

---

### `POST /api/crm/supply/po/<id>/lines/<line_id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "quantity": 250.0, "unit_price": 52.0 }
}
```

---

### `POST /api/crm/supply/po/<id>/lines/<line_id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 10, "deleted": true } } }`

---

### `POST /api/crm/supply/po/<id>/comments/list`
### `POST /api/crm/supply/po/<id>/comments/add`
### `POST /api/crm/supply/po/<id>/comments/<msg_id>/delete`

Same shape as container comments above.

---

## 🤝 SECTION 4 — NEGOTIATIONS

### `POST /api/crm/supply/negotiations/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1, "per_page": 20,
    "status": "in_progress",
    "supply_vendor_id": 1913,
    "product_id": 45
  }
}
```

> `status`: `draft` | `in_progress` | `agreed` | `rejected` | `cancelled`
> `supply_vendor_id` = `lugal.crm.customer` id (vendor contact)

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 3, "page": 1, "per_page": 20,
      "items": [
        {
          "id": 1,
          "supply_vendor_id": 1913,
          "supply_vendor_name": "Armani Beauty EU",
          "vendor_id": null,
          "vendor_name": "",
          "product_id": 45,
          "product_name": "Acqua di Gio 200ml",
          "title": "Q2 2026 Bulk Order Negotiation",
          "description": "Negotiating 500+ units at reduced price",
          "quantity": 500.0,
          "expected_price": 80.0,
          "agreed_price": 0.0,
          "currency_id": 1,
          "currency_name": "USD",
          "status": "in_progress",
          "due_date": "2026-04-15",
          "notes": "Awaiting counter-offer",
          "created_by_id": 2,
          "created_by_name": "Admin",
          "created_at": "2026-03-20T08:00:00",
          "updated_at": "2026-03-28T14:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/negotiations/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "title": "Q3 2026 Perfume Order",
    "supply_vendor_id": 1913,
    "product_id": 45,
    "description": "Looking to negotiate 1000 units",
    "quantity": 1000.0,
    "expected_price": 75.0,
    "currency_id": 1,
    "due_date": "2026-05-01"
  }
}
```

> Only `title` is **required**.

---

### `POST /api/crm/supply/negotiations/<id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "agreed_price": 77.5, "status": "agreed" }
}
```

---

### `POST /api/crm/supply/negotiations/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

### `POST /api/crm/supply/negotiations/<id>/comments/list`
### `POST /api/crm/supply/negotiations/<id>/comments/add`
### `POST /api/crm/supply/negotiations/<id>/comments/<msg_id>/delete`

Same shape as container comments above.

---

## 📝 SECTION 5 — ITEM REQUESTS

### `POST /api/crm/supply/item_requests/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1, "per_page": 20,
    "status": "pending",
    "branch_id": 3,
    "product_id": 45
  }
}
```

> `status`: `pending` | `approved` | `rejected` | `fulfilled`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 4, "page": 1, "per_page": 20,
      "items": [
        {
          "id": 1,
          "product_id": 45,
          "product_name": "Acqua di Gio 200ml",
          "product_sku": "ADG-200",
          "quantity": 50.0,
          "uom": "PCS",
          "branch_id": 3,
          "branch_name": "Dubai Branch",
          "requested_by_id": 5,
          "requested_by_name": "Sara Ahmed",
          "status": "pending",
          "note": "Urgent — stock nearly out",
          "created_at": "2026-03-30T09:00:00",
          "updated_at": "2026-03-30T09:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/item_requests/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "product_id": 45,
    "quantity": 50.0,
    "uom": "PCS",
    "branch_id": 3,
    "note": "Urgent — stock nearly out"
  }
}
```

> `product_id` is **required**.

---

### `POST /api/crm/supply/item_requests/<id>/update_status`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "status": "approved" }
}
```

> Auto-notifies the requester via notification system.

---

### `POST /api/crm/supply/item_requests/<id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "quantity": 75.0, "note": "Revised quantity" }
}
```

---

### `POST /api/crm/supply/item_requests/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** Single item request object under `data`.

---

### `POST /api/crm/supply/item_requests/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 🏢 SECTION 6 — CLEARANCE COMPANIES

### `POST /api/crm/supply/clearance_companies/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "page": 1, "per_page": 20, "search": "dubai", "is_active": true }
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 1, "page": 1, "per_page": 20,
      "items": [
        {
          "id": 1,
          "name": "Dubai Express Clearance LLC",
          "contact_name": "Mohammed Al-Rashidi",
          "phone": "+971-4-333-4444",
          "email": "info@dubaiexpress.ae",
          "whatsapp": "+971-50-333-4444",
          "telegram": "@dubaiexpress",
          "country_id": 234,
          "country_name": "United Arab Emirates",
          "city": "Dubai",
          "address": "Port Saeed, Deira",
          "license_number": "DED-2023-112233",
          "license_expiry": "2027-12-31",
          "notes": "Preferred for Jebel Ali clearance",
          "is_active": true
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/clearance_companies/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "name": "Abu Dhabi Customs Services",
    "contact_name": "Khalid Al-Mansouri",
    "phone": "+971-2-555-6666",
    "email": "khalid@adcs.ae",
    "whatsapp": "+971-55-555-6666",
    "country_id": 234,
    "city": "Abu Dhabi",
    "license_number": "ADBC-2024-001",
    "license_expiry": "2026-12-31"
  }
}
```

> Only `name` is **required**.

---

### `POST /api/crm/supply/clearance_companies/<id>/update`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "is_active": false, "license_expiry": "2028-12-31" }
}
```

---

### `POST /api/crm/supply/clearance_companies/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`

---

### `POST /api/crm/supply/clearance_companies/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 📊 SECTION 7 — MIN/MAX INVENTORY

### `POST /api/crm/supply/inventory/minmax`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1, "per_page": 50,
    "branch_id": 3,
    "category_id": 12,
    "search": "acqua",
    "needs_reorder": true
  }
}
```

> `needs_reorder: true` = only items below minimum stock level.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 10, "page": 1, "per_page": 50,
      "items": [
        {
          "id": 1,
          "product_id": 45,
          "product_name": "Acqua di Gio 200ml",
          "sku": "ADG-200",
          "category": "Perfumes",
          "uom": "PCS",
          "current_stock": 18.0,
          "min_qty": 50.0,
          "max_qty": 500.0,
          "branch_id": 3,
          "branch_name": "Dubai Branch",
          "needs_reorder": true
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/inventory/minmax/update` (upsert)

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "product_id": 45,
    "min_qty": 50.0,
    "max_qty": 500.0,
    "branch_id": 3
  }
}
```

> Creates if not exists, updates if exists. `product_id`, `min_qty`, `max_qty` **required**.

---

### `POST /api/crm/supply/inventory/minmax/delete`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "product_id": 45, "branch_id": 3 }
}
```

**Response:** `{ "result": { "success": true, "data": { "deleted": true } } }`

---

## 💬 SECTION 8 — CONVERSATIONS

### `POST /api/crm/supply/conversations/list`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "items": [
        {
          "id": 1,
          "type": "team",
          "name": "Supply Team",
          "last_activity": "2026-04-04T14:00:00",
          "is_archived": false,
          "unread_count": 3,
          "participants": [
            { "id": 2, "name": "Admin", "avatar": "/web/image/res.users/2/avatar_128" },
            { "id": 5, "name": "Sara Ahmed", "avatar": "/web/image/res.users/5/avatar_128" }
          ]
        },
        {
          "id": 2,
          "type": "dm",
          "name": "Sara Ahmed",
          "last_activity": "2026-04-04T10:30:00",
          "is_archived": false,
          "unread_count": 0,
          "participants": [
            { "id": 2, "name": "Admin", "avatar": "/web/image/res.users/2/avatar_128" },
            { "id": 5, "name": "Sara Ahmed", "avatar": "/web/image/res.users/5/avatar_128" }
          ]
        }
      ]
    }
  }
}
```

> `type`: `team` | `dm` | `group`

---

### `POST /api/crm/supply/conversations/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** Single conversation object.

---

### `POST /api/crm/supply/conversations/<id>/archive`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
> Cannot archive the team channel.

---

### `POST /api/crm/supply/conversations/<id>/rename`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "name": "Container Operations Team" }
}
```

> Only `group` type can be renamed.

---

## ✉️ SECTION 9 — MESSAGES

### `POST /api/crm/supply/messages/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "page": 1, "per_page": 30, "thread_id": 1 }
}
```

> `thread_id: 0` or omit = team channel.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 42, "page": 1, "per_page": 30,
      "thread_id": 1,
      "conversation_type": "team",
      "items": [
        {
          "id": 101,
          "thread_id": 1,
          "conversation_type": "team",
          "sender_id": 2,
          "sender_name": "Admin",
          "sender_avatar": "/web/image/res.users/2/avatar_128",
          "recipient_ids": [],
          "participant_ids": [2, 5, 7],
          "participants": [
            { "id": 2, "name": "Admin", "avatar": "/web/image/res.users/2/avatar_128" }
          ],
          "content": "Container MSCU1234567 is now at Jebel Ali port 🚢",
          "attachments": [],
          "created_at": "2026-04-04T09:15:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/messages/create`

**Team channel (no recipients):**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "content": "New PO submitted for review" }
}
```

**DM to one user:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "content": "Please approve the item request", "recipient_ids": [5] }
}
```

**Group (2+ recipients):**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "content": "Team meeting at 3pm",
    "recipient_ids": [5, 7, 9],
    "group_name": "Container Operations Team"
  }
}
```

**Reply to existing conversation:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "content": "Reply here", "thread_id": 2 }
}
```

> `content` is **required**.

**Response:** Single message object under `data`.

---

### `POST /api/crm/supply/messages/<id>/delete`

> Only the original sender can delete.

**Response:** `{ "result": { "success": true, "data": { "id": 101, "deleted": true } } }`

---

## 👤 SECTION 10 — USERS

### `POST /api/crm/supply/users`

**Request:**
```json
{ "jsonrpc": "2.0", "method": "call", "params": { "search": "sara" } }
```

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 1,
      "items": [
        {
          "id": 5,
          "name": "Sara Ahmed",
          "email": "sara@company.com",
          "job_position": "Supply Chain Manager",
          "avatar": "/web/image/res.users/5/avatar_128"
        }
      ]
    }
  }
}
```

---

## 🔔 SECTION 11 — NOTIFICATIONS

### `POST /api/crm/supply/notifications/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "page": 1, "per_page": 20, "is_read": false }
}
```

> `is_read: false` = unread only. Omit for all.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total": 5,
      "unread_count": 3,
      "page": 1,
      "per_page": 20,
      "items": [
        {
          "id": 1,
          "type": "container_arrived",
          "title": "Container Arrived at Port",
          "body": "Container MSCU1234567 has arrived at Jebel Ali.",
          "related_id": 1,
          "related_type": "lugal.supply.container",
          "is_read": false,
          "created_at": "2026-04-04T08:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/notifications/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "user_id": 5,
    "notif_type": "low_stock",
    "title": "Low Stock Alert",
    "body": "Acqua di Gio 200ml is below minimum (18 < 50).",
    "related_id": 45,
    "related_type": "product.product"
  }
}
```

> `user_id`, `notif_type`, `title` are **required**.

---

### `POST /api/crm/supply/notifications/<id>/mark_read`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** Updated notification object.

---

### `POST /api/crm/supply/notifications/mark_all_read`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`
**Response:** `{ "result": { "success": true, "data": { "marked": 3 } } }`

---

### `POST /api/crm/supply/notifications/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 📌 ALL ENDPOINTS — QUICK REFERENCE (57 total)

### Authentication
| # | Endpoint | Description |
|---|---|---|
| — | `POST /lugal/auth/login` | Get `access_token` (params: `username`, `password`) |

### Vendors
| # | Endpoint | Description |
|---|---|---|
| 1 | `POST /api/crm/supply/vendors/list` | List vendor contacts |
| 2 | `POST /api/crm/supply/vendors/<id>/get` | Get vendor detail |
| 3 | `POST /api/crm/supply/vendors/create` | Create vendor contact |
| 4 | `POST /api/crm/supply/vendors/<id>/update` | Update vendor |
| 5 | `POST /api/crm/supply/vendors/<id>/delete` | Soft-delete vendor |

### Containers
| # | Endpoint | Description |
|---|---|---|
| 6 | `POST /api/crm/supply/containers/list` | List containers |
| 7 | `POST /api/crm/supply/containers/<id>/get` | Get container + attachments |
| 8 | `POST /api/crm/supply/containers/create` | Create container |
| 9 | `POST /api/crm/supply/containers/<id>/update` | Update container |
| 10 | `POST /api/crm/supply/containers/<id>/mark_arrived` | Set at_port + arrived_at |
| 11 | `POST /api/crm/supply/containers/<id>/clearance_delivered` | Mark clearance sent |
| 12 | `POST /api/crm/supply/containers/<id>/delete` | Soft-delete container |
| 13 | `POST /api/crm/supply/containers/<id>/comments/list` | List comments |
| 14 | `POST /api/crm/supply/containers/<id>/comments/add` | Add comment / note |
| 15 | `POST /api/crm/supply/containers/<id>/comments/<msg_id>/delete` | Delete comment |

### Purchase Orders
| # | Endpoint | Description |
|---|---|---|
| 16 | `POST /api/crm/supply/po/list` | List POs |
| 17 | `POST /api/crm/supply/po/<id>/get` | Get PO + lines |
| 18 | `POST /api/crm/supply/po/create` | Create PO |
| 19 | `POST /api/crm/supply/po/<id>/update` | Update PO |
| 20 | `POST /api/crm/supply/po/<id>/delete` | Soft-delete PO |
| 21 | `POST /api/crm/supply/po/suggested` | List suggested POs |
| 22 | `POST /api/crm/supply/po/<id>/lines` | List PO lines |
| 23 | `POST /api/crm/supply/po/<id>/lines/add` | Add line to PO |
| 24 | `POST /api/crm/supply/po/<id>/lines/<line_id>/update` | Update PO line |
| 25 | `POST /api/crm/supply/po/<id>/lines/<line_id>/delete` | Delete PO line |
| 26 | `POST /api/crm/supply/po/<id>/comments/list` | List PO comments |
| 27 | `POST /api/crm/supply/po/<id>/comments/add` | Add PO comment |
| 28 | `POST /api/crm/supply/po/<id>/comments/<msg_id>/delete` | Delete PO comment |

### Negotiations
| # | Endpoint | Description |
|---|---|---|
| 29 | `POST /api/crm/supply/negotiations/list` | List negotiations |
| 30 | `POST /api/crm/supply/negotiations/<id>/get` | Get negotiation |
| 31 | `POST /api/crm/supply/negotiations/create` | Create negotiation |
| 32 | `POST /api/crm/supply/negotiations/<id>/update` | Update negotiation |
| 33 | `POST /api/crm/supply/negotiations/<id>/delete` | Delete negotiation |
| 34 | `POST /api/crm/supply/negotiations/<id>/comments/list` | List negotiation comments |
| 35 | `POST /api/crm/supply/negotiations/<id>/comments/add` | Add negotiation comment |
| 36 | `POST /api/crm/supply/negotiations/<id>/comments/<msg_id>/delete` | Delete negotiation comment |

### Item Requests
| # | Endpoint | Description |
|---|---|---|
| 37 | `POST /api/crm/supply/item_requests/list` | List item requests |
| 38 | `POST /api/crm/supply/item_requests/<id>/get` | Get item request |
| 39 | `POST /api/crm/supply/item_requests/create` | Create item request |
| 40 | `POST /api/crm/supply/item_requests/<id>/update` | Update item request |
| 41 | `POST /api/crm/supply/item_requests/<id>/update_status` | Change status + notify |
| 42 | `POST /api/crm/supply/item_requests/<id>/delete` | Soft-delete request |

### Clearance Companies
| # | Endpoint | Description |
|---|---|---|
| 43 | `POST /api/crm/supply/clearance_companies/list` | List clearance companies |
| 44 | `POST /api/crm/supply/clearance_companies/<id>/get` | Get company |
| 45 | `POST /api/crm/supply/clearance_companies/create` | Create company |
| 46 | `POST /api/crm/supply/clearance_companies/<id>/update` | Update company |
| 47 | `POST /api/crm/supply/clearance_companies/<id>/delete` | Delete company |

### Inventory
| # | Endpoint | Description |
|---|---|---|
| 48 | `POST /api/crm/supply/inventory/minmax` | List min/max records |
| 49 | `POST /api/crm/supply/inventory/minmax/update` | Upsert min/max |
| 50 | `POST /api/crm/supply/inventory/minmax/delete` | Delete min/max |

### Conversations & Messages
| # | Endpoint | Description |
|---|---|---|
| 51 | `POST /api/crm/supply/conversations/list` | List conversations |
| 52 | `POST /api/crm/supply/conversations/<id>/get` | Get conversation |
| 53 | `POST /api/crm/supply/conversations/<id>/archive` | Archive conversation |
| 54 | `POST /api/crm/supply/conversations/<id>/rename` | Rename group |
| 55 | `POST /api/crm/supply/messages/list` | List messages |
| 56 | `POST /api/crm/supply/messages/create` | Send message |
| 57 | `POST /api/crm/supply/messages/<id>/delete` | Delete message |

### Users & Notifications
| # | Endpoint | Description |
|---|---|---|
| 58 | `POST /api/crm/supply/users` | List internal users |
| 59 | `POST /api/crm/supply/notifications/list` | List notifications |
| 60 | `POST /api/crm/supply/notifications/create` | Push notification |
| 61 | `POST /api/crm/supply/notifications/<id>/mark_read` | Mark read |
| 62 | `POST /api/crm/supply/notifications/mark_all_read` | Mark all read |
| 63 | `POST /api/crm/supply/notifications/<id>/delete` | Delete notification |

---

## ⚠️ ENUMS CHEAT SHEET

| Field | Where Used | Allowed Values |
|---|---|---|
| `contact_type` | vendor/contact | `customer` \| `vendor` \| `both` |
| `division` | vendor, container, PO | `europe` \| `china` \| `other` |
| `status` | container | `waiting` \| `loading` \| `in_transit` \| `at_port` \| `cleared` \| `delivered` |
| `status` | PO | `draft` \| `pending` \| `confirmed` \| `received` \| `cancelled` |
| `status` | negotiation | `draft` \| `in_progress` \| `agreed` \| `rejected` \| `cancelled` |
| `status` | item request | `pending` \| `approved` \| `rejected` \| `fulfilled` |
| `type` | conversation | `team` \| `dm` \| `group` |
| `notif_type` | notification | `po_created` \| `container_arrived` \| `clearance_done` \| `low_stock` \| `negotiation_update` \| `item_request_update` \| `general` |
| `is_note` | comments | `false` = public comment \| `true` = internal note |
