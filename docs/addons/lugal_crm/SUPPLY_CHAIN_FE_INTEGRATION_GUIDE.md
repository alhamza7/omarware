# Supply Chain APIs — Frontend Integration Guide

Single source of truth for **`/api/crm/supply/*`** used by the Supply Chain module.  
All technical content is **English**.

**Backend sources (Odoo `lugal_crm`):**  
`supply_chain_api_controller.py`, `supply_controller.py`, `supply_extra_api_controller.py`, `supply_chat_controller.py`, `supply_stories_controller.py`

---

## How to share this with the FE team

| Channel | Action |
|--------|--------|
| **Repository** | `docs/addons/lugal_crm/SUPPLY_CHAIN_FE_INTEGRATION_GUIDE.md` (same branch as deployed Odoo). |
| **Pin version** | Git **commit** or **release tag**; run **`-u lugal_crm`** when new routes ship. |

---

## Quick reference — all routes under `/api/crm/supply/*`

| Route | Transport |
|-------|-----------|
| `/vendors/list` | JSON-RPC |
| `/vendors/<id>/get` | JSON-RPC |
| `/vendors/create` | JSON-RPC |
| `/vendors/<id>/update` | JSON-RPC |
| `/vendors/<id>/delete` | JSON-RPC |
| `/suppliers/<id>/update` | JSON-RPC |
| `/suppliers/<id>/delete` | JSON-RPC |
| `/containers/list` | JSON-RPC |
| `/containers/<id>/get` | JSON-RPC |
| `/containers/create` | JSON-RPC |
| `/containers/<id>/update` | JSON-RPC |
| `/containers/<id>/delete` | JSON-RPC |
| `/containers/<id>/mark_arrived` | JSON-RPC |
| `/containers/<id>/clearance_delivered` | JSON-RPC |
| `/containers/<id>/assign_driver` | JSON-RPC |
| `/containers/<id>/unassign_driver` | JSON-RPC |
| `/containers/<id>/set_reminder` | JSON-RPC |
| `/containers/<id>/reminder` | HTTP GET/DELETE |
| `/containers/<id>/attachments/list` | JSON-RPC |
| `/containers/<id>/attachments/upload` | HTTP multipart |
| `/containers/<id>/attachments/<att_id>/delete` | JSON-RPC |
| `/containers/<id>/penalties/list` | JSON-RPC |
| `/containers/<id>/add_penalty` | JSON-RPC |
| `/containers/<id>/penalties/<penalty_id>/delete` | JSON-RPC |
| `/containers/tracking/view` | HTTP GET **or** JSON-RPC POST (duplicate handlers) |
| `/containers/tracking/update` | JSON-RPC |
| `/containers/<id>/comments/list` | JSON-RPC (stub) |
| `/containers/<id>/comments/add` | JSON-RPC (stub) |
| `/containers/<id>/comments/<msg_id>/delete` | JSON-RPC (stub) |
| `/shipments/list` | JSON-RPC |
| `/shipments/<id>/get` | JSON-RPC |
| `/shipments/create` | JSON-RPC |
| `/shipments/<id>/update` | JSON-RPC |
| `/shipments/<id>/delete` | JSON-RPC |
| `/shipments/<id>/link_orders` | JSON-RPC |
| `/po/list` | JSON-RPC |
| `/po/suggested` | JSON-RPC |
| `/po/create` | JSON-RPC |
| `/po/<id>/get` | JSON-RPC |
| `/po/<id>/update` | JSON-RPC |
| `/po/<id>/delete` | JSON-RPC |
| `/po/<id>/confirm` | JSON-RPC |
| `/po/<id>/submit` | JSON-RPC |
| `/po/<id>/ship` | JSON-RPC |
| `/po/<id>/receive` | JSON-RPC |
| `/po/<id>/cancel` | JSON-RPC |
| `/po/<id>/reopen` | JSON-RPC |
| `/po/<id>/order_e_sign` | JSON-RPC |
| `/po/<id>/lines/add` | JSON-RPC |
| `/po/<id>/lines/<line_id>/update` | JSON-RPC |
| `/po/<id>/lines/<line_id>/delete` | JSON-RPC |
| `/po/<id>/attachments/list` | JSON-RPC |
| `/po/<id>/attachments/upload` | HTTP multipart |
| `/po/<id>/attachments/link` | JSON-RPC |
| `/po/<id>/packing-list/share` | JSON-RPC |
| `/po/<id>/packing-list/pdf` | JSON-RPC |
| `/po/<id>/comments/list` | JSON-RPC (stub) |
| `/po/<id>/comments/add` | JSON-RPC (stub) |
| `/po/<id>/comments/<msg_id>/delete` | JSON-RPC (stub) |
| `/dashboard/summary` | JSON-RPC |
| `/negotiations/list` | JSON-RPC |
| `/negotiations/<id>/get` | JSON-RPC |
| `/negotiations/create` | JSON-RPC |
| `/negotiations/<id>/update` | JSON-RPC |
| `/negotiations/<id>/delete` | JSON-RPC |
| `/negotiations/<id>/confirm` | JSON-RPC |
| `/negotiations/<id>/e_sign_approve` | JSON-RPC |
| `/negotiations/<id>/offers/add` | JSON-RPC |
| `/negotiations/<id>/offers/list` | JSON-RPC |
| `/negotiations/<id>/comments/list` | JSON-RPC |
| `/negotiations/<id>/comments/add` | JSON-RPC |
| `/negotiations/<id>/comments/<msg_id>/delete` | JSON-RPC |
| `/negotiations/<id>/attachments/link` | JSON-RPC |
| `/item_requests/list` | JSON-RPC |
| `/item_requests/<id>/get` | JSON-RPC |
| `/item_requests/create` | JSON-RPC |
| `/item_requests/<id>/update` | JSON-RPC |
| `/item_requests/<id>/delete` | JSON-RPC |
| `/item_requests/<id>/update_status` | JSON-RPC |
| `/item_requests/<id>/requester_confirm` | JSON-RPC |
| `/item_requests/<id>/attachments/link` | JSON-RPC |
| `/clearance_companies/list` | JSON-RPC |
| `/clearance_companies/<id>/get` | JSON-RPC |
| `/clearance_companies/create` | JSON-RPC |
| `/clearance_companies/<id>/update` | JSON-RPC |
| `/clearance_companies/<id>/delete` | JSON-RPC |
| `/inventory/minmax` | JSON-RPC |
| `/inventory/minmax/update` | JSON-RPC |
| `/inventory/minmax/delete` | JSON-RPC |
| `/notifications/list` | JSON-RPC |
| `/notifications/create` | JSON-RPC |
| `/notifications/<id>/mark_read` | JSON-RPC |
| `/notifications/mark_all_read` | JSON-RPC |
| `/notifications/<id>/delete` | JSON-RPC |
| `/payments/list` | JSON-RPC |
| `/payments/<id>/get` | JSON-RPC |
| `/payments/po/list` | JSON-RPC |
| `/payments/create` | JSON-RPC |
| `/payments/<id>/update` | JSON-RPC |
| `/payments/<id>/delete` | JSON-RPC |
| `/payments/<id>/attachments/link` | JSON-RPC |
| `/conversations/list` | JSON-RPC |
| `/conversations/create` | JSON-RPC |
| `/conversations/<id>/get` | JSON-RPC |
| `/conversations/<id>/rename` | JSON-RPC |
| `/conversations/<id>/archive` | JSON-RPC |
| `/conversations/<id>/leave` | JSON-RPC |
| `/conversations/<id>/update` | JSON-RPC |
| `/conversations/<id>/mark_read` | JSON-RPC |
| `/conversations/<id>/typing` | JSON-RPC |
| `/conversations/<id>/members/list` | JSON-RPC |
| `/conversations/<id>/members/add` | JSON-RPC |
| `/conversations/<id>/members/remove` | JSON-RPC |
| `/conversations/<id>/members/role` | JSON-RPC (stub) |
| `/conversations/<id>/pinned` | JSON-RPC |
| `/messages/list` | JSON-RPC |
| `/messages/create` | JSON-RPC |
| `/messages/<id>/edit` | JSON-RPC |
| `/messages/<id>/pin` | JSON-RPC |
| `/messages/<id>/react` | JSON-RPC |
| `/messages/<id>/delivered` | JSON-RPC |
| `/messages/<id>/read` | JSON-RPC |
| `/messages/forward` | JSON-RPC |
| `/messages/search` | JSON-RPC |
| `/messages/<id>/delete` | JSON-RPC |
| `/chat/upload` | HTTP multipart |
| `/chat/bus_channels` | JSON-RPC |
| `/stories/feed` | JSON-RPC |
| `/stories/create` | JSON-RPC |
| `/stories/<id>/view` | JSON-RPC |
| `/stories/<id>/viewers` | JSON-RPC |
| `/stories/<id>/delete` | JSON-RPC |
| `/stories/upload` | HTTP multipart |

Prefix every path with **`POST /api/crm/supply`** except where **GET** or **DELETE** is stated for HTTP routes.

---

## Shared conventions

### Base URL

| Mode | Base | Notes |
|------|------|--------|
| Vite dev | SPA origin (e.g. `http://localhost:5174`) | Empty `VITE_ODOO_URL`; proxy `/api`, `/web`, `/lugal` to Odoo. |
| Direct Odoo | `https://host:port` | Set `VITE_ODOO_URL`; mind CORS. |

### Authentication

- Header: **`Authorization: Bearer <access_token>`** (typical login: `POST /lugal/auth/login` with JSON-RPC body).
- On **401**, refresh token or send user to login.

### JSON-RPC request envelope

**HTTP:** `POST`  
**Headers:** `Content-Type: application/json`, plus `Authorization` when logged in.

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {}
}
```

Put route-specific fields inside **`params`** (flat object). Read **`result`** from the response (`result.success`, `result.data`, `result.error`).

### Response envelope

```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {},
    "error": "optional when success is false"
  }
}
```

### Multipart (`type=http`)

- Send **`Authorization`** header; body is **`multipart/form-data`** (not JSON-RPC).
- Response is usually plain JSON: `{ "success": true, "data": { ... } }`.

### Workflow map (high level)

| Step | Concept | Main prefixes |
|------|---------|----------------|
| 1 | Item request | `item_requests/*` |
| 2 | Negotiation | `negotiations/*` |
| 3 | Purchase order | `po/*` |
| 4 | Payment | `payments/*` |
| 5 | Shipment / container | `shipments/*`, `containers/*` |

Supporting: `vendors/*`, `suppliers/*`, `clearance_companies/*`, `inventory/minmax`, `notifications/*`, tracking, chat, stories.

### Attachments pattern (many modules)

1. Upload binary via **`/chat/upload`**, **`/po/.../attachments/upload`**, **`/containers/.../attachments/upload`**, or **`/stories/upload`** as applicable.
2. Call the matching **`.../attachments/link`** route with **`attachment_ids`: `[id, ...]`** in JSON-RPC `params` when the domain supports linking.

### Related (not under `/api/crm/supply/`)

- Product search / REST PO create: **`docs/addons/lugal_crm/SUPPLY_PO_REST_FE_INTEGRATION.md`**
- Deeper model reference: **`SUPPLY_CHAIN_MODELS_API.md`**

---

## TypeScript client

Many paths are wrapped in **`frontends/44/src/services/supplyApi.ts`**. Add new `rpc()` helpers following the same pattern.

---

# Endpoint catalogue

Each entry uses the same structure: **Route**, **Transport**, **Purpose**, **Request body** (JSON-RPC `params` unless noted).

---

## List vendors

### Route

`POST` `/api/crm/supply/vendors/list`

### Transport

JSON-RPC

### Purpose

Paginated list of active, non-deleted `lugal.supply.vendor` records.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "search": "",
  "division": "europe"
}
```

---

## Get vendor

### Route

`POST` `/api/crm/supply/vendors/<vendor_id>/get`

### Transport

JSON-RPC

### Purpose

Return one vendor card.

### Request body

```json
{}
```

---

## Create vendor

### Route

`POST` `/api/crm/supply/vendors/create`

### Transport

JSON-RPC

### Purpose

Create a vendor; **`name`** required.

### Request body

```json
{
  "name": "ACME",
  "name_ar": "",
  "phone": "",
  "email": "",
  "website": "",
  "whatsapp": "",
  "telegram": "",
  "wechat": "",
  "city": "",
  "address": "",
  "payment_terms": "",
  "notes": "",
  "contact_name": "",
  "division": "europe",
  "lead_time_days": 0,
  "min_order_value": 0,
  "currency_id": 1
}
```

---

## Update vendor

### Route

`POST` `/api/crm/supply/vendors/<vendor_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update; only sent keys are written.

### Request body

```json
{
  "name": "ACME",
  "contact_name": "",
  "phone": "",
  "email": "",
  "country_id": 104,
  "currency_id": 1,
  "division": "china",
  "notes": ""
}
```

---

## Delete vendor

### Route

`POST` `/api/crm/supply/vendors/<vendor_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete (`is_deleted`, `active`).

### Request body

```json
{}
```

---

## Update supplier (alias)

### Route

`POST` `/api/crm/supply/suppliers/<supplier_id>/update`

### Transport

JSON-RPC

### Purpose

Same model as vendor; accepts **`contact_person`** → `contact_name`, string **`country`** → `country_id` resolution.

### Request body

```json
{
  "name": "ABC Supplier",
  "contact_person": "John Doe",
  "email": "john@example.com",
  "phone": "+91 9999999999",
  "whatsapp": "+91 9999999999",
  "country": "India",
  "city": "Ahmedabad",
  "currency_id": 1,
  "notes": ""
}
```

---

## Delete supplier (alias)

### Route

`POST` `/api/crm/supply/suppliers/<supplier_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete vendor record; fails if already deleted.

### Request body

```json
{}
```

---

## List containers (legacy CRM list)

### Route

`POST` `/api/crm/supply/containers/list`

### Transport

JSON-RPC

### Purpose

List containers (older SPA path; shipments list is preferred for many UIs).

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "status": "waiting",
  "division": "europe",
  "search": ""
}
```

---

## Get container

### Route

`POST` `/api/crm/supply/containers/<container_id>/get`

### Transport

JSON-RPC

### Purpose

Single container by id.

### Request body

```json
{}
```

---

## Create container

### Route

`POST` `/api/crm/supply/containers/create`

### Transport

JSON-RPC

### Purpose

Create `lugal.supply.container` (fields per controller validation).

### Request body

```json
{
  "name": "CNT-001",
  "container_number": "",
  "bl_number": "",
  "division": "europe",
  "origin_location": "",
  "destination_port": "",
  "departure_date": "2026-05-01",
  "eta": "2026-06-01",
  "tracking_url": "",
  "notes": ""
}
```

---

## Update container

### Route

`POST` `/api/crm/supply/containers/<container_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update of container header fields.

### Request body

```json
{
  "name": "CNT-001",
  "status": "active",
  "notes": ""
}
```

---

## Delete container

### Route

`POST` `/api/crm/supply/containers/<container_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete.

### Request body

```json
{}
```

---

## Mark container arrived

### Route

`POST` `/api/crm/supply/containers/<container_id>/mark_arrived`

### Transport

JSON-RPC

### Purpose

Workflow: mark container arrived (`arrived_at`, status).

### Request body

```json
{}
```

---

## Container clearance delivered

### Route

`POST` `/api/crm/supply/containers/<container_id>/clearance_delivered`

### Transport

JSON-RPC

### Purpose

Set clearance info delivered flags.

### Request body

```json
{}
```

---

## Assign driver to container

### Route

`POST` `/api/crm/supply/containers/<container_id>/assign_driver`

### Transport

JSON-RPC

### Purpose

Assign driver to container.

### Request body

```json
{
  "driver_id": 0,
  "driver_name": "",
  "driver_phone": ""
}
```

---

## Unassign driver from container

### Route

`POST` `/api/crm/supply/containers/<container_id>/unassign_driver`

### Transport

JSON-RPC

### Purpose

Clear driver assignment.

### Request body

```json
{}
```

---

## Set container reminder (JSON-RPC)

### Route

`POST` `/api/crm/supply/containers/<container_id>/set_reminder`

### Transport

JSON-RPC

### Purpose

Set or update reminder date/note; supports clearing via controller rules.

### Request body

```json
{
  "reminder_date": "2026-05-10T12:00:00",
  "reminder_note": "",
  "clear_reminder": false
}
```

---

## Get or delete container reminder (HTTP)

### Route

`GET` `/api/crm/supply/containers/<container_id>/reminder`  
`DELETE` `/api/crm/supply/containers/<container_id>/reminder`

### Transport

HTTP (not JSON-RPC); **`Authorization: Bearer`**

### Purpose

**GET:** reminder payload for UI. **DELETE:** clear reminder.

### Request body

Query/path only; no JSON body.

---

## List container attachments

### Route

`POST` `/api/crm/supply/containers/<container_id>/attachments/list`

### Transport

JSON-RPC

### Purpose

List `ir.attachment` rows linked to the container.

### Request body

```json
{}
```

---

## Upload container attachments

### Route

`POST` `/api/crm/supply/containers/<container_id>/attachments/upload`

### Transport

HTTP **multipart** (`file`, `files`, or `files[]`)

### Purpose

Upload files and link to container `attachment_ids`.

### Request body

Multipart form fields only (plus `Authorization` header).

---

## Delete container attachment

### Route

`POST` `/api/crm/supply/containers/<container_id>/attachments/<attachment_id>/delete`

### Transport

JSON-RPC

### Purpose

Remove link and delete `ir.attachment`.

### Request body

```json
{}
```

---

## List container penalties

### Route

`POST` `/api/crm/supply/containers/<container_id>/penalties/list`

### Transport

JSON-RPC

### Purpose

List penalty lines for the container.

### Request body

```json
{}
```

---

## Add container penalty

### Route

`POST` `/api/crm/supply/containers/<container_id>/add_penalty`

### Transport

JSON-RPC

### Purpose

Create `lugal.supply.container.penalty`.

### Request body

```json
{
  "penalty_type": "storage",
  "amount": 100.0,
  "reason": "",
  "penalty_date": "2026-05-09",
  "currency_id": 1
}
```

---

## Delete container penalty

### Route

`POST` `/api/crm/supply/containers/<container_id>/penalties/<penalty_id>/delete`

### Transport

JSON-RPC

### Purpose

Remove penalty line.

### Request body

```json
{}
```

---

## Container tracking view (GET)

### Route

`GET` `/api/crm/supply/containers/tracking/view?container_id=<id>`

### Transport

HTTP GET; **`Authorization: Bearer`**

### Purpose

Read tracking URL + `tracking_data` snapshot for a container.

### Request body

Query: **`container_id`** (required).

---

## Container tracking view (POST)

### Route

`POST` `/api/crm/supply/containers/tracking/view`

### Transport

JSON-RPC (alternate to GET)

### Purpose

Same data as GET; **`container_id`** in `params`.

### Request body

```json
{
  "container_id": 17
}
```

---

## Container tracking update

### Route

`POST` `/api/crm/supply/containers/tracking/update`

### Transport

JSON-RPC

### Purpose

Update **`tracking_url`** and/or **`tracking_data`**.

### Request body

```json
{
  "container_id": 17,
  "tracking_url": "https://...",
  "tracking_data": {}
}
```

---

## List container comments (stub)

### Route

`POST` `/api/crm/supply/containers/<container_id>/comments/list`

### Transport

JSON-RPC

### Purpose

Returns empty list until mail-thread comments are enabled.

### Request body

```json
{
  "page": 1
}
```

---

## Add container comment (stub)

### Route

`POST` `/api/crm/supply/containers/<container_id>/comments/add`

### Transport

JSON-RPC

### Purpose

Returns error: container comments API not enabled.

### Request body

```json
{
  "body": "",
  "is_note": false
}
```

---

## Delete container comment (stub)

### Route

`POST` `/api/crm/supply/containers/<container_id>/comments/<msg_id>/delete`

### Transport

JSON-RPC

### Purpose

Returns error: container comments API not enabled.

### Request body

```json
{}
```

---

## List shipments

### Route

`POST` `/api/crm/supply/shipments/list`

### Transport

JSON-RPC

### Purpose

Paginated shipments (backed by `lugal.supply.container`).

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "status": "waiting",
  "division": "europe",
  "search": ""
}
```

---

## Get shipment

### Route

`POST` `/api/crm/supply/shipments/<shipment_id>/get`

### Transport

JSON-RPC

### Purpose

**`shipment_id`** is the container record id.

### Request body

```json
{}
```

---

## Create shipment

### Route

`POST` `/api/crm/supply/shipments/create`

### Transport

JSON-RPC

### Purpose

Create container/shipment; field names follow extra API (e.g. `origin`, `destination`, `etd` aliases may apply — see controller).

### Request body

```json
{
  "name": "SHP-001",
  "container_number": "",
  "bl_number": "",
  "origin": "",
  "destination": "",
  "etd": "2026-05-01",
  "eta": "2026-06-01",
  "division": "europe",
  "tracking_url": "",
  "notes": ""
}
```

---

## Update shipment

### Route

`POST` `/api/crm/supply/shipments/<shipment_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update.

### Request body

```json
{
  "name": "SHP-001",
  "notes": ""
}
```

---

## Delete shipment

### Route

`POST` `/api/crm/supply/shipments/<shipment_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete container.

### Request body

```json
{}
```

---

## Link orders to shipment

### Route

`POST` `/api/crm/supply/shipments/<shipment_id>/link_orders`

### Transport

JSON-RPC

### Purpose

Attach PO ids to the shipment/container.

### Request body

```json
{
  "order_ids": [1, 2, 3],
  "po_ids": [1, 2, 3]
}
```

(Use **`order_ids`** or **`po_ids`** per backend acceptance.)

---

## List purchase orders

### Route

`POST` `/api/crm/supply/po/list`

### Transport

JSON-RPC

### Purpose

Paginated PO list for supply CRM POs.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "status": "draft",
  "division": "europe",
  "search": "",
  "vendor_customer_id": 0
}
```

---

## List suggested purchase orders

### Route

`POST` `/api/crm/supply/po/suggested`

### Transport

JSON-RPC

### Purpose

POs with **`is_suggested`** flag.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "division": "europe"
}
```

---

## Create purchase order

### Route

`POST` `/api/crm/supply/po/create`

### Transport

JSON-RPC

### Purpose

Create PO; vendor via **`vendor_customer_id`** (partner linked to supply vendor). Optional **`item_request_id`**, **`negotiation_id`**, **`container_id`**, **`lines`**.

### Request body

```json
{
  "name": "PO-2026-001",
  "vendor_customer_id": 10,
  "division": "europe",
  "currency_id": 1,
  "container_id": null,
  "branch_id": null,
  "lines": [
    {
      "product_name": "Item",
      "item_code": "",
      "uom": "pcs",
      "quantity": 1,
      "unit_price": 0
    }
  ]
}
```

---

## Get purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/get`

### Transport

JSON-RPC

### Purpose

PO detail with lines and extended fields.

### Request body

```json
{}
```

---

## Update purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/update`

### Transport

JSON-RPC

### Purpose

Partial header/line workflow update per controller.

### Request body

```json
{
  "name": "PO-2026-001",
  "notes": "",
  "division": "europe"
}
```

---

## Delete purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete.

### Request body

```json
{}
```

---

## Purchase order e-sign / order confirmation

### Route

`POST` `/api/crm/supply/po/<po_id>/order_e_sign`

### Transport

JSON-RPC

### Purpose

Record order confirmation signature (PO extension fields).

### Request body

```json
{}
```

---

## Confirm purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/confirm`

### Transport

JSON-RPC

### Purpose

Transition PO toward confirmed state.

### Request body

```json
{}
```

---

## Submit purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/submit`

### Transport

JSON-RPC

### Purpose

Submit workflow (implementation may align with confirm).

### Request body

```json
{}
```

---

## Ship purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/ship`

### Transport

JSON-RPC

### Purpose

Status transition (maps per model).

### Request body

```json
{}
```

---

## Receive purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/receive`

### Transport

JSON-RPC

### Purpose

Status transition.

### Request body

```json
{}
```

---

## Cancel purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/cancel`

### Transport

JSON-RPC

### Purpose

Cancel PO.

### Request body

```json
{}
```

---

## Reopen purchase order

### Route

`POST` `/api/crm/supply/po/<po_id>/reopen`

### Transport

JSON-RPC

### Purpose

Return to draft where allowed.

### Request body

```json
{}
```

---

## Add PO line

### Route

`POST` `/api/crm/supply/po/<po_id>/lines/add`

### Transport

JSON-RPC

### Purpose

Append order line.

### Request body

```json
{
  "product_name": "",
  "item_code": "",
  "uom": "pcs",
  "quantity": 1,
  "unit_price": 0,
  "product_id": null
}
```

---

## Update PO line

### Route

`POST` `/api/crm/supply/po/<po_id>/lines/<line_id>/update`

### Transport

JSON-RPC

### Purpose

Update line fields.

### Request body

```json
{
  "quantity": 2,
  "unit_price": 10.5
}
```

---

## Delete PO line

### Route

`POST` `/api/crm/supply/po/<po_id>/lines/<line_id>/delete`

### Transport

JSON-RPC

### Purpose

Remove line.

### Request body

```json
{}
```

---

## List PO attachments

### Route

`POST` `/api/crm/supply/po/<po_id>/attachments/list`

### Transport

JSON-RPC

### Purpose

List files linked to PO.

### Request body

```json
{}
```

---

## Upload PO attachments

### Route

`POST` `/api/crm/supply/po/<po_id>/attachments/upload`

### Transport

HTTP **multipart** (`file` / `files` / `files[]`)

### Purpose

Upload and link to PO.

### Request body

Multipart only.

---

## Link PO attachments

### Route

`POST` `/api/crm/supply/po/<po_id>/attachments/link`

### Transport

JSON-RPC

### Purpose

Set/replace linked **`ir.attachment`** ids.

### Request body

```json
{
  "attachment_ids": [101, 102]
}
```

---

## PO packing list share text

### Route

`POST` `/api/crm/supply/po/<po_id>/packing-list/share`

### Transport

JSON-RPC

### Purpose

Plain text for Web Share / clipboard (no prices).

### Request body

```json
{}
```

---

## PO packing list PDF

### Route

`POST` `/api/crm/supply/po/<po_id>/packing-list/pdf`

### Transport

JSON-RPC

### Purpose

Returns PDF as **base64** for client download.

### Request body

```json
{}
```

---

## List PO comments (stub)

### Route

`POST` `/api/crm/supply/po/<po_id>/comments/list`

### Transport

JSON-RPC

### Purpose

Empty list until PO mail comments enabled.

### Request body

```json
{
  "page": 1
}
```

---

## Add PO comment (stub)

### Route

`POST` `/api/crm/supply/po/<po_id>/comments/add`

### Transport

JSON-RPC

### Purpose

Returns error: PO comments API not enabled.

### Request body

```json
{
  "body": "",
  "is_note": false
}
```

---

## Delete PO comment (stub)

### Route

`POST` `/api/crm/supply/po/<po_id>/comments/<msg_id>/delete`

### Transport

JSON-RPC

### Purpose

Returns error: PO comments API not enabled.

### Request body

```json
{}
```

---

## Supply dashboard summary

### Route

`POST` `/api/crm/supply/dashboard/summary`

### Transport

JSON-RPC

### Purpose

Aggregated KPIs for supply dashboard (shape per controller).

### Request body

```json
{}
```

---

## List negotiations

### Route

`POST` `/api/crm/supply/negotiations/list`

### Transport

JSON-RPC

### Purpose

Paginated negotiations with filters.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "state": "",
  "vendor_id": 0,
  "item_request_id": 0,
  "search": ""
}
```

---

## Get negotiation

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/get`

### Transport

JSON-RPC

### Purpose

Negotiation detail.

### Request body

```json
{}
```

---

## Create negotiation

### Route

`POST` `/api/crm/supply/negotiations/create`

### Transport

JSON-RPC

### Purpose

**`item_request_id`** and **`vendor_id`** typically required; optional **`agent_id`**, **`offered_price`**, etc.

### Request body

```json
{
  "item_request_id": 1,
  "vendor_id": 2,
  "agent_id": null,
  "offered_price": 0
}
```

---

## Update negotiation

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update.

### Request body

```json
{
  "notes": ""
}
```

---

## Delete negotiation

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete.

### Request body

```json
{}
```

---

## Confirm negotiation

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/confirm`

### Transport

JSON-RPC

### Purpose

Finalize negotiation.

### Request body

```json
{}
```

---

## Negotiation e-sign approve

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/e_sign_approve`

### Transport

JSON-RPC

### Purpose

E-sign approval step (aligned with confirm in many flows).

### Request body

```json
{}
```

---

## Add negotiation offer

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/offers/add`

### Transport

JSON-RPC

### Purpose

Append offer row; **`price`** required.

### Request body

```json
{
  "price": 100.0,
  "notes": "",
  "currency_id": 1
}
```

---

## List negotiation offers

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/offers/list`

### Transport

JSON-RPC

### Purpose

Offer history.

### Request body

```json
{
  "page": 1,
  "per_page": 50
}
```

---

## List negotiation comments

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/comments/list`

### Transport

JSON-RPC

### Purpose

Thread comments for negotiation.

### Request body

```json
{
  "page": 1,
  "per_page": 50
}
```

---

## Add negotiation comment

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/comments/add`

### Transport

JSON-RPC

### Purpose

Post comment.

### Request body

```json
{
  "body": "Comment text"
}
```

---

## Delete negotiation comment

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/comments/<msg_id>/delete`

### Transport

JSON-RPC

### Purpose

Remove comment.

### Request body

```json
{}
```

---

## Link negotiation attachments

### Route

`POST` `/api/crm/supply/negotiations/<neg_id>/attachments/link`

### Transport

JSON-RPC

### Purpose

Attach **`ir.attachment`** ids to negotiation.

### Request body

```json
{
  "attachment_ids": [1, 2]
}
```

---

## List item requests

### Route

`POST` `/api/crm/supply/item_requests/list`

### Transport

JSON-RPC

### Purpose

Paginated item requests with filters.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "state": "",
  "priority": "",
  "search": ""
}
```

---

## Get item request

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/get`

### Transport

JSON-RPC

### Purpose

Detail.

### Request body

```json
{}
```

---

## Create item request

### Route

`POST` `/api/crm/supply/item_requests/create`

### Transport

JSON-RPC

### Purpose

**`item_name`** required; optional **`packing`** alias and commercial fields per controller.

### Request body

```json
{
  "item_name": "Bottle 100ml",
  "description": "",
  "priority": "normal",
  "target_qty": 0
}
```

---

## Update item request

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update.

### Request body

```json
{
  "item_name": "Bottle 100ml",
  "notes": ""
}
```

---

## Delete item request

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft delete.

### Request body

```json
{}
```

---

## Update item request status

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/update_status`

### Transport

JSON-RPC

### Purpose

Set **`state`**.

### Request body

```json
{
  "state": "approved"
}
```

---

## Item requester confirm

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/requester_confirm`

### Transport

JSON-RPC

### Purpose

Requester confirmation / e-sign on request.

### Request body

```json
{}
```

---

## Link item request attachments

### Route

`POST` `/api/crm/supply/item_requests/<req_id>/attachments/link`

### Transport

JSON-RPC

### Purpose

Set **`attachment_ids`**.

### Request body

```json
{
  "attachment_ids": [1, 2]
}
```

---

## List clearance companies

### Route

`POST` `/api/crm/supply/clearance_companies/list`

### Transport

JSON-RPC

### Purpose

Customs clearance company directory.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "search": ""
}
```

---

## Get clearance company

### Route

`POST` `/api/crm/supply/clearance_companies/<cc_id>/get`

### Transport

JSON-RPC

### Purpose

Single record.

### Request body

```json
{}
```

---

## Create clearance company

### Route

`POST` `/api/crm/supply/clearance_companies/create`

### Transport

JSON-RPC

### Purpose

Create clearance partner record (fields per model/controller).

### Request body

```json
{
  "name": "Clearance Co",
  "phone": "",
  "email": ""
}
```

---

## Update clearance company

### Route

`POST` `/api/crm/supply/clearance_companies/<cc_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update.

### Request body

```json
{
  "name": "Clearance Co",
  "notes": ""
}
```

---

## Delete clearance company

### Route

`POST` `/api/crm/supply/clearance_companies/<cc_id>/delete`

### Transport

JSON-RPC

### Purpose

Delete or archive per backend rules.

### Request body

```json
{}
```

---

## List inventory min/max

### Route

`POST` `/api/crm/supply/inventory/minmax`

### Transport

JSON-RPC

### Purpose

List min/max rows (product-level supply rules).

### Request body

```json
{
  "page": 1,
  "per_page": 50,
  "search": ""
}
```

---

## Upsert inventory min/max

### Route

`POST` `/api/crm/supply/inventory/minmax/update`

### Transport

JSON-RPC

### Purpose

Create or update min/max for a product.

### Request body

```json
{
  "product_id": 1,
  "min_qty": 10,
  "max_qty": 100
}
```

---

## Delete inventory min/max

### Route

`POST` `/api/crm/supply/inventory/minmax/delete`

### Transport

JSON-RPC

### Purpose

Remove min/max row (params per controller, often **`id`** or **`product_id`**).

### Request body

```json
{
  "id": 1
}
```

---

## List notifications

### Route

`POST` `/api/crm/supply/notifications/list`

### Transport

JSON-RPC

### Purpose

User supply notifications inbox.

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "unread_only": false
}
```

---

## Create notification

### Route

`POST` `/api/crm/supply/notifications/create`

### Transport

JSON-RPC

### Purpose

Create in-app notification (admin/system use).

### Request body

```json
{
  "title": "",
  "body": "",
  "user_id": 2,
  "related_type": "",
  "related_id": 0
}
```

---

## Mark notification read

### Route

`POST` `/api/crm/supply/notifications/<notif_id>/mark_read`

### Transport

JSON-RPC

### Purpose

Mark one notification read.

### Request body

```json
{}
```

---

## Mark all notifications read

### Route

`POST` `/api/crm/supply/notifications/mark_all_read`

### Transport

JSON-RPC

### Purpose

Mark all for current user.

### Request body

```json
{}
```

---

## Delete notification

### Route

`POST` `/api/crm/supply/notifications/<notif_id>/delete`

### Transport

JSON-RPC

### Purpose

Remove notification.

### Request body

```json
{}
```

---

## List payments

### Route

`POST` `/api/crm/supply/payments/list`

### Transport

JSON-RPC

### Purpose

Paginated payments with filters (**`po_id`**, **`payment_type`**, etc.).

### Request body

```json
{
  "page": 1,
  "per_page": 20,
  "po_id": 0,
  "payment_type": "installment"
}
```

---

## Get payment

### Route

`POST` `/api/crm/supply/payments/<payment_id>/get`

### Transport

JSON-RPC

### Purpose

Payment detail.

### Request body

```json
{}
```

---

## List POs for payment dropdown

### Route

`POST` `/api/crm/supply/payments/po/list`

### Transport

JSON-RPC

### Purpose

Lightweight searchable PO list; item **`id`** is **`po_id`** for **`payments/create`**.

### Request body

```json
{
  "page": 1,
  "per_page": 25,
  "search": "",
  "status": "",
  "division": "europe"
}
```

---

## Create payment

### Route

`POST` `/api/crm/supply/payments/create`

### Transport

JSON-RPC

### Purpose

Create `lugal.supply.payment`; **`po_id`** (or **`linked_order_id`**) and **`amount`** required.

### Request body

```json
{
  "po_id": 12,
  "amount": 1000.0,
  "payment_type": "installment",
  "notes": "",
  "payment_date": "2026-05-09",
  "currency_id": 1,
  "payment_method": "",
  "paid_to": "",
  "payee_partner_id": null
}
```

---

## Update payment

### Route

`POST` `/api/crm/supply/payments/<payment_id>/update`

### Transport

JSON-RPC

### Purpose

Partial update.

### Request body

```json
{
  "amount": 1000.0,
  "notes": ""
}
```

---

## Delete payment

### Route

`POST` `/api/crm/supply/payments/<payment_id>/delete`

### Transport

JSON-RPC

### Purpose

Unlink payment record.

### Request body

```json
{}
```

---

## Link payment attachments

### Route

`POST` `/api/crm/supply/payments/<payment_id>/attachments/link`

### Transport

JSON-RPC

### Purpose

Receipt / proof files.

### Request body

```json
{
  "attachment_ids": [1, 2]
}
```

---

## List conversations

### Route

`POST` `/api/crm/supply/conversations/list`

### Transport

JSON-RPC

### Purpose

Supply chat conversation list for current user.

### Request body

```json
{
  "page": 1,
  "per_page": 30,
  "include_archived": false
}
```

---

## Create conversation

### Route

`POST` `/api/crm/supply/conversations/create`

### Transport

JSON-RPC

### Purpose

Start DM / group / team conversation (params per controller).

### Request body

```json
{
  "type": "direct",
  "participant_ids": [2, 3],
  "name": ""
}
```

---

## Get conversation

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/get`

### Transport

JSON-RPC

### Purpose

Conversation metadata.

### Request body

```json
{}
```

---

## Rename conversation

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/rename`

### Transport

JSON-RPC

### Purpose

Rename group/team chat.

### Request body

```json
{
  "name": "New title"
}
```

---

## Archive conversation

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/archive`

### Transport

JSON-RPC

### Purpose

Archive for current user or conversation.

### Request body

```json
{}
```

---

## Leave conversation

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/leave`

### Transport

JSON-RPC

### Purpose

Remove self from participants.

### Request body

```json
{}
```

---

## Update conversation

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/update`

### Transport

JSON-RPC

### Purpose

Update conversation settings (fields per model).

### Request body

```json
{
  "only_admins_can_send": false
}
```

---

## Mark conversation read

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/mark_read`

### Transport

JSON-RPC

### Purpose

Clear unread / set last read pointer.

### Request body

```json
{
  "last_read_message_id": 0
}
```

---

## Typing indicator

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/typing`

### Transport

JSON-RPC

### Purpose

Publish typing state to bus channel.

### Request body

```json
{
  "typing": true
}
```

---

## List conversation members

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/members/list`

### Transport

JSON-RPC

### Purpose

Participants for the conversation.

### Request body

```json
{}
```

---

## Add conversation member

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/members/add`

### Transport

JSON-RPC

### Purpose

Add user to group.

### Request body

```json
{
  "user_id": 5
}
```

---

## Remove conversation member

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/members/remove`

### Transport

JSON-RPC

### Purpose

Remove participant.

### Request body

```json
{
  "user_id": 5
}
```

---

## Set member role (stub)

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/members/role`

### Transport

JSON-RPC

### Purpose

Stub until role field is fully implemented.

### Request body

```json
{
  "user_id": 5,
  "role": "admin"
}
```

---

## List pinned messages

### Route

`POST` `/api/crm/supply/conversations/<conv_id>/pinned`

### Transport

JSON-RPC

### Purpose

Pinned messages in conversation.

### Request body

```json
{}
```

---

## List messages

### Route

`POST` `/api/crm/supply/messages/list`

### Transport

JSON-RPC

### Purpose

Cursor/history pagination for messages. Use **`conversation_id`** or **`thread_id`**.

### Request body

```json
{
  "conversation_id": 1,
  "before_id": null,
  "per_page": 20,
  "limit": 20
}
```

---

## Create message

### Route

`POST` `/api/crm/supply/messages/create`

### Transport

JSON-RPC

### Purpose

Send text/media message; **`attachment_ids`** from prior upload.

### Request body

```json
{
  "conversation_id": 1,
  "content": "Hello",
  "attachment_ids": [],
  "reply_to_id": null,
  "client_message_id": "uuid",
  "kind": "text",
  "duration_seconds": 0
}
```

---

## Edit message

### Route

`POST` `/api/crm/supply/messages/<message_id>/edit`

### Transport

JSON-RPC

### Purpose

Edit message content (within policy).

### Request body

```json
{
  "content": "Updated text"
}
```

---

## Pin message

### Route

`POST` `/api/crm/supply/messages/<message_id>/pin`

### Transport

JSON-RPC

### Purpose

Pin/unpin in conversation.

### Request body

```json
{
  "pinned": true
}
```

---

## React to message

### Route

`POST` `/api/crm/supply/messages/<message_id>/react`

### Transport

JSON-RPC

### Purpose

Add/remove emoji reaction.

### Request body

```json
{
  "emoji": "👍",
  "add": true
}
```

---

## Message delivered receipt

### Route

`POST` `/api/crm/supply/messages/<message_id>/delivered`

### Transport

JSON-RPC

### Purpose

Mark delivered for recipients.

### Request body

```json
{}
```

---

## Message read receipt

### Route

`POST` `/api/crm/supply/messages/<message_id>/read`

### Transport

JSON-RPC

### Purpose

Mark read.

### Request body

```json
{}
```

---

## Forward message

### Route

`POST` `/api/crm/supply/messages/forward`

### Transport

JSON-RPC

### Purpose

Copy message to another thread.

### Request body

```json
{
  "message_id": 1,
  "thread_id": 2
}
```

---

## Search messages

### Route

`POST` `/api/crm/supply/messages/search`

### Transport

JSON-RPC

### Purpose

Full-text style search across allowed conversations.

### Request body

```json
{
  "query": "invoice",
  "thread_id": null,
  "page": 1,
  "per_page": 20
}
```

---

## Delete message

### Route

`POST` `/api/crm/supply/messages/<message_id>/delete`

### Transport

JSON-RPC

### Purpose

Delete for me / for everyone (params **`for_me`**, **`for_everyone`**, **`mode`**).

### Request body

```json
{
  "for_everyone": false,
  "mode": "for_me"
}
```

---

## Supply chat file upload

### Route

`POST` `/api/crm/supply/chat/upload`

### Transport

HTTP **multipart** (`file` / `files` / `files[]`); optional **`conversation_id`**, **`kind`**, **`duration_seconds`**

### Purpose

Upload chat media; returns **`files`** with **`id`** for **`attachment_ids`** on **`messages/create`**.

### Request body

Multipart form only.

---

## Chat bus channels

### Route

`POST` `/api/crm/supply/chat/bus_channels`

### Transport

JSON-RPC

### Purpose

Return bus channel names for **`/web/bus/poll`** (e.g. `supply_chat.<conv_id>`).

### Request body

```json
{}
```

---

## Stories feed

### Route

`POST` `/api/crm/supply/stories/feed`

### Transport

JSON-RPC

### Purpose

Active supply stories grouped/list for UI.

### Request body

```json
{
  "include_mine": true,
  "limit": 100
}
```

---

## Create story

### Route

`POST` `/api/crm/supply/stories/create`

### Transport

JSON-RPC

### Purpose

Post story after optional **`/stories/upload`**.

### Request body

```json
{
  "kind": "text",
  "content": "",
  "caption": "",
  "attachment_id": null
}
```

---

## Mark story viewed

### Route

`POST` `/api/crm/supply/stories/<story_id>/view`

### Transport

JSON-RPC

### Purpose

Record view for current user.

### Request body

```json
{}
```

---

## List story viewers

### Route

`POST` `/api/crm/supply/stories/<story_id>/viewers`

### Transport

JSON-RPC

### Purpose

Who viewed the story.

### Request body

```json
{}
```

---

## Delete story

### Route

`POST` `/api/crm/supply/stories/<story_id>/delete`

### Transport

JSON-RPC

### Purpose

Soft-expire story (author rules apply).

### Request body

```json
{}
```

---

## Upload story media

### Route

`POST` `/api/crm/supply/stories/upload`

### Transport

HTTP **multipart** — fields **`file`**, optional **`kind`**, **`duration_seconds`**

### Purpose

Upload media; returns **`attachment_id`** for **`stories/create`**.

### Request body

Multipart only.

---

## FE checklist before go-live

- [ ] Base URL and proxy env match deployed Odoo.
- [ ] JWT on every supply call; handle **401**.
- [ ] Parse **`result.success`**; show **`result.error`**.
- [ ] Use **`shipments/*`** for main container UI where aligned with `frontends/44`.
- [ ] Multipart routes: no JSON-RPC wrapper on the HTTP body.
