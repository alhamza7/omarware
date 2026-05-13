# New Supply Chain APIs — Reference

**Version:** 1.1 — Updated 2026-05-07 (module upgrade `lugal_supply`, `lugal_crm`)  
**Base URL:** `http://localhost:8075`  
**Related (vendors, containers, PO, dashboard, attachments):** `docs/SUPPLY_CHAIN_API_COMPLETE.md`

---

## Global Rules

| Property | Value |
|---|---|
| Method | `POST` (all endpoints) |
| Content-Type | `application/json` |
| Auth Header | `Authorization: Bearer <access_token>` |
| Token Endpoint | `POST /lugal/auth/login` → `result.data.access_token` |

### JSON-RPC Envelope (required for every request)

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { }
}
```

### Standard Response Shape

```json
{ "result": { "success": true,  "data": { ... } } }
{ "result": { "success": false, "error": "Reason" } }
```

### `extra_fields` (JSON)

Item requests, negotiations, and supply POs inherit `lugal.supply.dynamic.extra.mixin`: an optional JSON object `extra_fields` for custom keys from the frontend. Send or update it via the same `params` as other writable fields where the controller passes kwargs through to `create` / `write` (see each endpoint in code if not listed below).

---

## 1. Container Tracking

### `POST /api/crm/supply/containers/tracking/view`

Returns container tracking fields and optional JSON snapshot (`tracking_data`).

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "container_id": 1 }
}
```

| Param | Required | Description |
|---|---|---|
| `container_id` | yes | Container record ID |

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1,
      "name": "Container #CONT-2026-001",
      "container_number": "MSCU1234567",
      "bl_number": "BL-2026-0042",
      "tracking_url": "https://track.msc.com/MSCU1234567",
      "status": "in_transit",
      "division": "china",
      "clearance_company": "Dubai Clearance Co.",
      "origin_location": "Guangzhou, China",
      "departure_date": "2026-03-10",
      "eta": "2026-04-05",
      "arrived_at": null,
      "assigned_user_id": 2,
      "assigned_user_name": "Admin",
      "tracking_data": {}
    }
  }
}
```

---

### `POST /api/crm/supply/containers/tracking/update`

Updates `tracking_url` and/or `tracking_data` JSON for a container.

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "container_id": 1,
    "tracking_url": "https://track.msc.com/MSCU9999999",
    "tracking_data": {
      "carrier": "MSC",
      "last_event": "Departed Port Said",
      "last_event_time": "2026-04-02T08:00:00"
    }
  }
}
```

| Param | Required | Description |
|---|---|---|
| `container_id` | yes | Container record ID |
| `tracking_url` | no | Public tracking URL |
| `tracking_data` | no | Free-form JSON snapshot from carrier API |

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "id": 1,
      "tracking_url": "https://track.msc.com/MSCU9999999",
      "tracking_data": {
        "carrier": "MSC",
        "last_event": "Departed Port Said",
        "last_event_time": "2026-04-02T08:00:00"
      }
    }
  }
}
```

---

## 2. Negotiations

> Model: `lugal.supply.negotiation` — linked to an item request and a vendor.

### `POST /api/crm/supply/negotiations/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "state": "ongoing",
    "vendor_id": 5,
    "item_request_id": 12
  }
}
```

| Param | Required | Description |
|---|---|---|
| `page` | no | Default `1` |
| `per_page` | no | Default `20`, max `200` |
| `state` | no | `ongoing` \| `finalized` \| `cancelled` |
| `vendor_id` | no | Filter by `lugal.supply.vendor` ID |
| `item_request_id` | no | Filter by item request ID |
| `search` | no | Search in `item_name` or negotiation reference |

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
          "name": "NEG-2026-001",
          "item_request_id": 12,
          "item_request_name": "REQ-2026-005",
          "vendor_id": 5,
          "vendor_name": "Armani Beauty EU",
          "item_name": "Acqua di Gio 200ml",
          "quantity": 500.0,
          "capacity": "200ml",
          "packing_pcs_per_carton": 12.0,
          "offered_price": 80.0,
          "final_agreed_price": 77.5,
          "currency_id": 1,
          "currency_name": "USD",
          "final_currency_id": 1,
          "final_currency_name": "USD",
          "terms": "FOB Guangzhou, NET30",
          "notes": "Q2 bulk order",
          "state": "ongoing",
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

### `POST /api/crm/supply/negotiations/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`  
**Response:** Single negotiation object under `data`.

---

### `POST /api/crm/supply/negotiations/create`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "item_request_id": 12,
    "vendor_id": 5,
    "item_name": "Acqua di Gio 200ml",
    "quantity": 500.0,
    "capacity": "200ml",
    "currency_id": 1,
    "terms": "FOB Guangzhou",
    "notes": "Awaiting counter-offer"
  }
}
```

| Param | Required | Description |
|---|---|---|
| `item_request_id` | yes | Linked item request ID |
| `vendor_id` | yes | `lugal.supply.vendor` ID |
| `item_name` | no | Item description |
| `quantity` | no | Negotiated quantity |
| `capacity` | no | Bottle/pack capacity string |
| `packing_pcs_per_carton` | no | Packing count |
| `currency_id` | no | Currency ID |
| `final_agreed_price` | no | Agreed price (set when finalizing) |
| `final_currency_id` | no | Currency for final price |
| `terms` | no | MOQ, lead time, etc. |
| `notes` | no | Discussion notes |

**Response:** Single negotiation object under `data`.

---

### `POST /api/crm/supply/negotiations/<id>/update`

Send only the fields you want to change.

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "state": "finalized",
    "final_agreed_price": 77.5,
    "final_currency_id": 1
  }
}
```

> `state` values: `ongoing` | `finalized` | `cancelled`

---

### `POST /api/crm/supply/negotiations/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 3. Item Requests

> Model: `lugal.supply.item.request` — internal procurement requests.

### `POST /api/crm/supply/item_requests/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "state": "draft",
    "priority": "high",
    "requested_by_id": 5,
    "search": "acqua"
  }
}
```

| Param | Required | Description |
|---|---|---|
| `page` | no | Default `1` |
| `per_page` | no | Default `20`, max `200` |
| `state` | no | `draft` \| `in_progress` \| `completed` |
| `priority` | no | `low` \| `medium` \| `high` |
| `requested_by_id` | no | Filter by requester user ID |
| `search` | no | Search in `item_name` or reference |

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
          "name": "REQ-2026-001",
          "item_name": "Acqua di Gio 200ml",
          "description": "Urgent restock for Dubai branch",
          "quantity": 50.0,
          "uom": "PCS",
          "capacity": "200ml",
          "packing_pcs_per_carton": 12.0,
          "priority": "high",
          "state": "draft",
          "notes": "Check min stock before ordering",
          "requested_by_id": 5,
          "requested_by_name": "Sara Ahmed",
          "request_date": "2026-03-30",
          "negotiation_count": 2,
          "created_at": "2026-03-30T09:00:00",
          "updated_at": "2026-03-30T09:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/item_requests/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`  
**Response:** Single item request object under `data`.

---

### `POST /api/crm/supply/item_requests/create`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "item_name": "Acqua di Gio 200ml",
    "quantity": 50.0,
    "uom": "PCS",
    "capacity": "200ml",
    "priority": "high",
    "notes": "Urgent — stock nearly out"
  }
}
```

| Param | Required | Description |
|---|---|---|
| `item_name` | yes | Product/item name |
| `quantity` | no | Requested quantity (default `1`) |
| `uom` | no | Unit label: pcs, carton, etc. |
| `capacity` | no | e.g. `50ml`, `100ml` |
| `packing_pcs_per_carton` | no | Pieces per carton |
| `priority` | no | `low` \| `medium` (default) \| `high` |
| `description` | no | Detailed description |
| `notes` | no | Additional notes |
| `request_date` | no | `YYYY-MM-DD`, defaults to today |

---

### `POST /api/crm/supply/item_requests/<id>/update`

Send only fields to change:
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "quantity": 75.0, "priority": "medium" }
}
```

---

### `POST /api/crm/supply/item_requests/<id>/update_status`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "state": "in_progress" }
}
```

> `state` values: `draft` | `in_progress` | `completed`

---

### `POST /api/crm/supply/item_requests/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 4. Clearance Companies

> Model: `lugal.supply.clearance.company`

### `POST /api/crm/supply/clearance_companies/list`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "search": "dubai",
    "is_active": true
  }
}
```

| Param | Required | Description |
|---|---|---|
| `page` | no | Default `1` |
| `per_page` | no | Default `20`, max `200` |
| `search` | no | Search in `name`, `city`, `contact_name` |
| `is_active` | no | `true` = active only \| `false` = inactive only |

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

### `POST /api/crm/supply/clearance_companies/<id>/get`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`  
**Response:** Single clearance company object under `data`.

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
    "telegram": "@adcs_customs",
    "country_id": 234,
    "city": "Abu Dhabi",
    "address": "Mina Zayed, Abu Dhabi",
    "license_number": "ADBC-2024-001",
    "license_expiry": "2026-12-31",
    "notes": "Secondary clearance agent"
  }
}
```

| Param | Required | Description |
|---|---|---|
| `name` | yes | Company name |
| `contact_name` | no | Primary contact person |
| `phone` | no | |
| `email` | no | |
| `whatsapp` | no | |
| `telegram` | no | |
| `country_id` | no | `res.country` ID |
| `city` | no | |
| `address` | no | Full address |
| `license_number` | no | Trade/customs license number |
| `license_expiry` | no | `YYYY-MM-DD` |
| `notes` | no | |
| `is_active` | no | Default `true` |

---

### `POST /api/crm/supply/clearance_companies/<id>/update`

Send only changed fields:
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "is_active": false, "license_expiry": "2028-12-31" }
}
```

---

### `POST /api/crm/supply/clearance_companies/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 5. Inventory Min/Max

> Model: `lugal.supply.inventory.minmax` — one rule per product+branch combination.

### `POST /api/crm/supply/inventory/minmax`

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 50,
    "branch_id": 3,
    "product_id": 45,
    "search": "acqua",
    "needs_reorder": true
  }
}
```

| Param | Required | Description |
|---|---|---|
| `page` | no | Default `1` |
| `per_page` | no | Default `20`, max `200` |
| `branch_id` | no | Filter by `lugal.crm.branch` ID |
| `product_id` | no | Filter by `product.product` ID |
| `search` | no | Search in product name or SKU |
| `needs_reorder` | no | `true` = only items below minimum |

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

Creates the rule if it doesn't exist; updates it if it does.

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

| Param | Required | Description |
|---|---|---|
| `product_id` | yes | `product.product` ID |
| `min_qty` | yes | Minimum stock level |
| `max_qty` | yes | Maximum stock level |
| `branch_id` | no | Scope to a specific branch |

**Response:** Single minmax record object under `data`.

---

### `POST /api/crm/supply/inventory/minmax/delete`

```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": { "product_id": 45, "branch_id": 3 }
}
```

| Param | Required | Description |
|---|---|---|
| `product_id` | yes | `product.product` ID |
| `branch_id` | no | If omitted, deletes the rule with no branch set |

**Response:** `{ "result": { "success": true, "data": { "deleted": true, "count": 1 } } }`

---

## 6. Supply Notifications

> Model: `lugal.supply.notification` — per-user supply-chain push notifications.

### `POST /api/crm/supply/notifications/list`

Returns notifications for the **authenticated user** (from JWT token).

**Request:**
```json
{
  "jsonrpc": "2.0", "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "is_read": false
  }
}
```

| Param | Required | Description |
|---|---|---|
| `page` | no | Default `1` |
| `per_page` | no | Default `20`, max `200` |
| `is_read` | no | `false` = unread only, `true` = read only, omit = all |

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
          "read_at": null,
          "created_at": "2026-05-03T08:00:00"
        }
      ]
    }
  }
}
```

---

### `POST /api/crm/supply/notifications/create`

Push a notification to a specific user (internal/server use).

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

| Param | Required | Description |
|---|---|---|
| `user_id` | yes | Target `res.users` ID |
| `notif_type` | yes | Free-form type string (e.g. `low_stock`, `container_arrived`, `item_request_approved`) |
| `title` | yes | Short notification title |
| `body` | no | Full notification message |
| `related_id` | no | ID of the related record |
| `related_type` | no | Model name of the related record |

**Response:** Single notification object under `data`.

---

### `POST /api/crm/supply/notifications/<id>/mark_read`

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`  
**Response:** Updated notification object with `is_read: true` and `read_at` timestamp.

---

### `POST /api/crm/supply/notifications/mark_all_read`

Marks all unread notifications for the authenticated user as read.

**Request:** `{ "jsonrpc": "2.0", "method": "call", "params": {} }`  
**Response:** `{ "result": { "success": true, "data": { "marked": 3 } } }`

---

### `POST /api/crm/supply/notifications/<id>/delete`

**Response:** `{ "result": { "success": true, "data": { "id": 1, "deleted": true } } }`

---

## 7. Negotiation — confirm, offers, comments, attachments

| Endpoint | Description |
|---|---|
| `POST /api/crm/supply/negotiations/<id>/confirm` | Finalize negotiation (`action_finalize`); sets state to finalized. |
| `POST /api/crm/supply/negotiations/<id>/e_sign_approve` | Same as confirm (approval / e-sign step). |
| `POST /api/crm/supply/negotiations/<id>/offers/add` | **Params:** `price` (required), `notes`, `currency_id`. Adds a row to `lugal.supply.negotiation.offer`. |
| `POST /api/crm/supply/negotiations/<id>/offers/list` | Paginated list of offers (`page`, `per_page`). |
| `POST /api/crm/supply/negotiations/<id>/comments/list` | Chatter comments (`mail.message`), paginated. |
| `POST /api/crm/supply/negotiations/<id>/comments/add` | **Params:** `body` or `message` (required). |
| `POST /api/crm/supply/negotiations/<id>/comments/<msg_id>/delete` | Deletes one comment on this negotiation. |
| `POST /api/crm/supply/negotiations/<id>/attachments/link` | **Params:** `attachment_ids` (list of `ir.attachment` ids) or `ids`. Replaces M2M; empty list clears. |

---

## 8. Item requests — attachments

| Endpoint | Description |
|---|---|
| `POST /api/crm/supply/item_requests/<id>/attachments/link` | **Params:** `attachment_ids` or `ids` (list). Links attachments to the request M2M. |

List/get responses for item requests may also include attachment metadata when implemented in the serializer (see controller).

---

## 9. Payments (`lugal.supply.payment`)

All require JWT. `payment_type` is normalized server-side (e.g. deposit / partial / full — see `_normalize_payment_type` in `supply_extra_api_controller.py`).

| Endpoint | Description |
|---|---|
| `POST /api/crm/supply/payments/list` | **Params:** `page`, `per_page`, `po_id`, `payment_status`, `payment_type`. |
| `POST /api/crm/supply/payments/<id>/get` | Single payment. |
| `POST /api/crm/supply/payments/po/list` | Lightweight PO list for dropdowns (`search`, `status`, `division`, pagination). |
| `POST /api/crm/supply/payments/create` | **Params:** `po_id` (or `linked_order_id`), `amount` (required); optional `payment_type`, `paid_to`, `payee_partner_id`, `currency_id`, `payment_date`, `payment_method`, `notes`, attachment payloads per shared supply attachment helpers. |
| `POST /api/crm/supply/payments/<id>/update` | Partial update; supports attachment updates when provided. |
| `POST /api/crm/supply/payments/<id>/delete` | Deletes the payment record. |
| `POST /api/crm/supply/payments/<id>/attachments/link` | **Params:** `attachment_ids` or `ids`. |

---

## 10. Shipments (backed by `lugal.supply.container`)

Shipment APIs are aliases over containers: `shipment_id` is the container id.

| Endpoint | Description |
|---|---|
| `POST /api/crm/supply/shipments/list` | **Params:** `status` (e.g. `waiting`, `active`, `at_port`, `completed`, or a `shipment_tracking_state` value), `division`, `supplier_id`, `search`, pagination. |
| `POST /api/crm/supply/shipments/<id>/get` | Single shipment view. |
| `POST /api/crm/supply/shipments/create` | **Params:** `name` or `container_number` (required); maps `shipping_method`→`transport_mode`, `origin`→`origin_location`, `destination`→`destination_location`, `etd`/`eta`→dates, etc. Supports attachments. |
| `POST /api/crm/supply/shipments/<id>/update` | Partial update; supports attachments. |
| `POST /api/crm/supply/shipments/<id>/delete` | Soft-deletes container (`is_deleted`, `active`). |
| `POST /api/crm/supply/shipments/<id>/link_orders` | **Params:** `order_ids` or `po_ids` (list of PO ids). Requires `purchase_order_ids` on the container model. |

---

## Quick Reference — All New Endpoints

| # | Endpoint | Description |
|---|---|---|
| 1 | `POST /api/crm/supply/containers/tracking/view` | Get container tracking data (POST JSON-RPC) |
| 2 | `POST /api/crm/supply/containers/tracking/update` | Update tracking URL and/or tracking_data JSON |
| 3 | `POST /api/crm/supply/negotiations/list` | List negotiations |
| 4 | `POST /api/crm/supply/negotiations/<id>/get` | Get single negotiation |
| 5 | `POST /api/crm/supply/negotiations/create` | Create negotiation |
| 6 | `POST /api/crm/supply/negotiations/<id>/update` | Update negotiation |
| 7 | `POST /api/crm/supply/negotiations/<id>/delete` | Delete negotiation |
| 8 | `POST /api/crm/supply/item_requests/list` | List item requests |
| 9 | `POST /api/crm/supply/item_requests/<id>/get` | Get single item request |
| 10 | `POST /api/crm/supply/item_requests/create` | Create item request |
| 11 | `POST /api/crm/supply/item_requests/<id>/update` | Update item request |
| 12 | `POST /api/crm/supply/item_requests/<id>/update_status` | Change item request state |
| 13 | `POST /api/crm/supply/item_requests/<id>/delete` | Delete item request |
| 14 | `POST /api/crm/supply/clearance_companies/list` | List clearance companies |
| 15 | `POST /api/crm/supply/clearance_companies/<id>/get` | Get single clearance company |
| 16 | `POST /api/crm/supply/clearance_companies/create` | Create clearance company |
| 17 | `POST /api/crm/supply/clearance_companies/<id>/update` | Update clearance company |
| 18 | `POST /api/crm/supply/clearance_companies/<id>/delete` | Delete clearance company |
| 19 | `POST /api/crm/supply/inventory/minmax` | List min/max rules |
| 20 | `POST /api/crm/supply/inventory/minmax/update` | Upsert min/max rule |
| 21 | `POST /api/crm/supply/inventory/minmax/delete` | Delete min/max rule |
| 22 | `POST /api/crm/supply/notifications/list` | List user notifications |
| 23 | `POST /api/crm/supply/notifications/create` | Push notification to user |
| 24 | `POST /api/crm/supply/notifications/<id>/mark_read` | Mark notification as read |
| 25 | `POST /api/crm/supply/notifications/mark_all_read` | Mark all notifications as read |
| 26 | `POST /api/crm/supply/notifications/<id>/delete` | Delete notification |
| 27 | `POST /api/crm/supply/negotiations/<id>/confirm` | Finalize negotiation |
| 28 | `POST /api/crm/supply/negotiations/<id>/e_sign_approve` | E-sign / approve (finalize) |
| 29 | `POST /api/crm/supply/negotiations/<id>/offers/add` | Add price offer row |
| 30 | `POST /api/crm/supply/negotiations/<id>/offers/list` | List offer rows |
| 31 | `POST /api/crm/supply/negotiations/<id>/comments/list` | List chatter comments |
| 32 | `POST /api/crm/supply/negotiations/<id>/comments/add` | Post comment |
| 33 | `POST /api/crm/supply/negotiations/<id>/comments/<msg_id>/delete` | Delete comment |
| 34 | `POST /api/crm/supply/negotiations/<id>/attachments/link` | Set linked `ir.attachment` ids |
| 35 | `POST /api/crm/supply/item_requests/<id>/attachments/link` | Set linked attachments on item request |
| 36 | `POST /api/crm/supply/payments/list` | List payments |
| 37 | `POST /api/crm/supply/payments/<id>/get` | Get payment |
| 38 | `POST /api/crm/supply/payments/po/list` | PO dropdown for payments UI |
| 39 | `POST /api/crm/supply/payments/create` | Create payment |
| 40 | `POST /api/crm/supply/payments/<id>/update` | Update payment |
| 41 | `POST /api/crm/supply/payments/<id>/delete` | Delete payment |
| 42 | `POST /api/crm/supply/payments/<id>/attachments/link` | Link attachments on payment |
| 43 | `POST /api/crm/supply/shipments/list` | List shipments (containers) |
| 44 | `POST /api/crm/supply/shipments/<id>/get` | Get shipment |
| 45 | `POST /api/crm/supply/shipments/create` | Create shipment / container |
| 46 | `POST /api/crm/supply/shipments/<id>/update` | Update shipment |
| 47 | `POST /api/crm/supply/shipments/<id>/delete` | Soft-delete shipment |
| 48 | `POST /api/crm/supply/shipments/<id>/link_orders` | Link POs to shipment |

**Core supply JSON-RPC** (same auth envelope): vendors, containers CRUD, PO CRUD, lines, dashboard, workflow attachments — see **`docs/SUPPLY_CHAIN_API_COMPLETE.md`**. Chat and stories: **`docs/SUPPLY_CHAT_API.md`** and stories routes under `/api/crm/supply/stories/`.

---

## Notes on Model Differences vs. Old Documentation

The real Odoo models differ slightly from the placeholder docs (`SUPPLY_CHAIN_API_COMPLETE.md`):

| API | Doc Schema | Actual Schema |
|---|---|---|
| **negotiations** | `supply_vendor_id`, `product_id`, `title`, `status` | `vendor_id` (lugal.supply.vendor), `item_request_id`, `item_name`, `state` (`ongoing`/`finalized`/`cancelled`) |
| **item_requests** | `product_id`, `branch_id`, `status` | `item_name` (Char), `state` (`draft`/`in_progress`/`completed`), `priority` |
| **notifications** | `notif_type` as enum | `notif_type` as free-form Char string |
