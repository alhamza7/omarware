# Supply chain models — JSON-RPC API reference

Technical documentation for CRM supply APIs backed by custom Odoo models. All routes use **`type='jsonrpc'`** in Odoo: call them with **HTTP POST** and a **JSON-RPC 2.0** body. There are **no REST GET/PUT** variants for these paths.

| Model (technical) | Description |
|-------------------|-------------|
| `lugal.supply.item.request` | Item request |
| `lugal.supply.negotiation` | Negotiation |
| `lugal.crm.supply.po` | Extended supply purchase order |
| `lugal.supply.payment` | **Supply payment** (linked to the supply PO; **not** `account.move`) |
| `lugal.supply.container` | Shipment / container |

---

## 1. Common conventions

### 1.1 HTTP

- **Method:** `POST` only.
- **URL:** Base URL of the Odoo web server + route path (e.g. `https://your-odoo.example.com/api/crm/supply/item_requests/list`).
- **Headers:** `Content-Type: application/json`
- **Auth:** `Authorization: Bearer <access_token>` (JWT via `lugal_auth` / `ensure_jwt_user_id`).
- **Database:** If your deployment requires it, send `X-Odoo-Database: <dbname>` (or equivalent proxy header).

### 1.2 JSON-RPC envelope

Every request body:

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { },
  "id": 1
}
```

Route-specific fields go inside **`params`**. Odoo returns a JSON-RPC wrapper; business payloads are in **`result`** when using the standard client, or your HTTP client may unwrap to `result` directly depending on integration.

### 1.3 Application result shape

Controllers return a flat object (this is the **`result`** payload, not the full JSON-RPC envelope):

```json
{
  "success": true,
  "data": { }
}
```

or

```json
{
  "success": false,
  "error": "Human-readable message",
  "data": null
}
```

Pagination (where supported): `params` may include `page` (default `1`) and `per_page` (default `20`, max `200`).

### 1.4 Dynamic JSON: `extra_fields`

For **item request**, **negotiation**, and **supply PO**, optional `extra_fields` is a JSON object (merge on update). See [SUPPLY_EXTRA_FIELDS_JSON.md](./SUPPLY_EXTRA_FIELDS_JSON.md).

---

## 2. Attachments (all models with files)

### 2.1 Storage

Files are standard **`ir.attachment`** records. Document links use the **`attachment_ids`** many-to-many on each model. After link/create, the server sets **`res_model`** and **`res_id`** on those attachments where applicable.

### 2.2 Option A — Existing attachment IDs

Pass in **`params`**:

- `attachment_ids`: `[101, 102]` — list of integer `ir.attachment` IDs (e.g. from multipart upload endpoints such as `/api/crm/supply/chat/upload` or `/api/lugal/email/attachments/upload`).

Alias: `ids` (same meaning) in some link-only routes.

### 2.3 Option B — Base64 inline upload (create/update)

In **`params`** on supported create/update routes, pass either:

- `attachment_files`: array of objects, **or**
- `attachments_base64`: same shape (alias).

Each object:

| Field | Required | Description |
|-------|----------|-------------|
| `filename` or `name` | Recommended | Stored attachment name |
| `datas` or `data` or `base64` | Yes | Base64-encoded file bytes |
| `mimetype` | No | MIME type; guessed from filename if omitted |

Example:

```json
"attachment_files": [
  {
    "filename": "label.png",
    "mimetype": "image/png",
    "datas": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
  }
]
```

You may combine **`attachment_ids`** and **`attachment_files`** in one call; the server merges them into a single **`(6, 0, [...])`** write on `attachment_ids`.

### 2.4 Replace vs clear

- Sending **`attachment_ids: []`** (or **`ids: []`**) with **no** new base64 files **clears** all linked attachments on that record (for routes using `supply_build_attachment_m2m_write`).
- **`attachments/link`** routes: empty list sends **`(5,)`** (clear); non-empty sends **`(6, 0, ids)`** (replace set).

### 2.5 Attachment object in JSON responses

Supply-chain list/detail payloads expose a **single** `attachments` array (no duplicate `reference_images` / `reference_files` keys). Each element:

```json
{
  "id": 101,
  "name": "photo.jpg",
  "mimetype": "image/jpeg",
  "size": 24580,
  "url": "/web/content/101",
  "file_url": "/web/content/101?access_token=abc",
  "uploaded_by_name": "Admin",
  "created_at": "2026-05-01T12:00:00.123456"
}
```

- **`url`:** path only (no access token).
- **`file_url`:** same path with **`access_token`** when the attachment has a token; otherwise equal to **`url`**.

Responses also include **`attachment_ids`** (list of integers) and **`attachment_count`** where implemented.

Shipment/container views use **`attachments`** (not a separate `documents` list).

---

## 3. Item request (`lugal.supply.item.request`)

Base path: `/api/crm/supply/item_requests`

### 3.1 List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/list` |
| **Description** | Paginated list of active, non-deleted item requests. |

**Request `params` example:**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "page": 1,
    "per_page": 20,
    "state": "draft",
    "priority": "high",
    "requested_by_id": 2,
    "search": "serum"
  },
  "id": 1
}
```

**Success `result` example:**

```json
{
  "success": true,
  "data": {
    "total": 1,
    "page": 1,
    "per_page": 20,
    "items": [
      {
        "id": 15,
        "request_id": "IR-00015",
        "name": "IR-00015",
        "item_name": "Hyaluronic serum 50ml",
        "item_description": "EU line",
        "description": "EU line",
        "quantity": 12000.0,
        "unit": "pcs",
        "uom": "pcs",
        "capacity": "50ml",
        "packing": 48.0,
        "packing_pcs_per_carton": 48.0,
        "attachments": [
          {
            "id": 101,
            "name": "ref.jpg",
            "mimetype": "image/jpeg",
            "size": 1200,
            "url": "/web/content/101",
            "file_url": "/web/content/101?access_token=abc",
            "uploaded_by_name": "User",
            "created_at": "2026-05-01T10:00:00"
          }
        ],
        "priority": "medium",
        "state": "draft",
        "status": "draft",
        "notes": "",
        "requested_by_id": 2,
        "requested_by_name": "Demo User",
        "request_date": "2026-05-03",
        "requester_confirm_user_id": null,
        "requester_confirm_date": null,
        "negotiation_count": 0,
        "negotiation_ids": [],
        "negotiations": [],
        "created_by_id": 2,
        "created_by_name": "Demo User",
        "created_at": "2026-05-03T08:00:00",
        "updated_at": "2026-05-03T08:00:00",
        "attachment_ids": [101],
        "attachment_count": 1,
        "extra_fields": { "fe.channel": "portal" }
      }
    ]
  }
}
```

**Error example:**

```json
{
  "success": false,
  "error": "Unauthorized",
  "data": null
}
```

---

### 3.2 Get

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/get` |
| **Description** | Single item request by database id. |

**Request `params`:** optional filters none required; `req_id` is in the URL.

**Success `result`:** same object shape as one element of `items` in §3.1.

**Error example:**

```json
{
  "success": false,
  "error": "Item request not found",
  "data": null
}
```

---

### 3.3 Create

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/create` |
| **Description** | Creates a request; `requested_by_id` is taken from JWT. |

**Request `params` example (fields + `extra_fields` + attachments):**

```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "item_name": "Hyaluronic serum 50ml",
    "description": "Private label",
    "notes": "Q2 showroom",
    "uom": "pcs",
    "quantity": 12000,
    "capacity": "50ml",
    "packing": 48,
    "packing_pcs_per_carton": 48,
    "priority": "medium",
    "request_date": "2026-05-15",
    "attachment_ids": [101, 102],
    "attachment_files": [
      {
        "filename": "extra.png",
        "mimetype": "image/png",
        "datas": "<base64>"
      }
    ],
    "extra_fields": {
      "fe.displaySku": "HS-50",
      "fe.tags": ["showroom", "q2"]
    }
  },
  "id": 1
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `item_name` | **Yes** | Non-empty string |
| `description`, `notes`, `uom`, `priority`, `capacity` | No | |
| `quantity` | No | number |
| `packing` / `packing_pcs_per_carton` | No | pcs per carton |
| `request_date` | No | `YYYY-MM-DD` |
| `attachment_ids`, `ids`, `attachment_files`, `attachments_base64` | No | See §2 |
| `extra_fields` | No | JSON object |

**Success `result`:** `{ "success": true, "data": { ... } }` — same shape as §3.1 item.

**Error examples:**

```json
{
  "success": false,
  "error": "item_name is required",
  "data": null
}
```

```json
{
  "success": false,
  "error": "attachment_files must be a list",
  "data": null
}
```

---

### 3.4 Update

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/update` |
| **Description** | Partial update; `extra_fields` is **merged**. |

**Request `params` example:**

```json
{
  "item_name": "Hyaluronic serum 50ml (rev B)",
  "uom": "pcs",
  "description": "Updated notes",
  "notes": "Internal",
  "priority": "high",
  "state": "in_progress",
  "capacity": "50ml",
  "quantity": 15000,
  "packing": 48,
  "packing_pcs_per_carton": 48,
  "attachment_ids": [201],
  "attachment_files": [],
  "extra_fields": { "fe.channel": "email" }
}
```

**Success / errors:** same pattern as §3.3; not found returns `"Item request not found"`.

---

### 3.5 Update status

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/update_status` |
| **Description** | Sets `state` from `state` or `status` param. |

**Request `params`:**

```json
{ "state": "completed" }
```

---

### 3.6 Requester confirm (e-sign)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/requester_confirm` |
| **Description** | Records requester confirmation on the request. |

**Request `params`:** `{}` (optional).

**Success `result`:** full serialized item request.

---

### 3.7 Attachments link (IDs only)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/attachments/link` |
| **Description** | Replaces linked attachments with `attachment_ids` / `ids` (or clears if empty list). |

**Request `params`:**

```json
{ "attachment_ids": [101, 102] }
```

**Success `result`:** serialized item request (includes `attachment_ids`, `attachment_count`, and `attachments` as in §2.5).

**Error example:**

```json
{
  "success": false,
  "error": "attachment_ids must be a list",
  "data": null
}
```

---

### 3.8 Delete (soft)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/item_requests/<req_id>/delete` |
| **Description** | Soft delete (`is_deleted`, `active`). |

**Success `result`:**

```json
{
  "success": true,
  "data": { "id": 15, "deleted": true }
}
```

---

## 4. Negotiation (`lugal.supply.negotiation`)

Base path: `/api/crm/supply/negotiations`

### 4.1 List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/list` |
| **Description** | Paginated negotiations. |

**Request `params` example:**

```json
{
  "page": 1,
  "per_page": 20,
  "state": "ongoing",
  "vendor_id": 3,
  "item_request_id": 15,
  "search": "acid"
}
```

**Success `result`:** `{ "success": true, "data": { "total", "page", "per_page", "items": [ negotiation, ... ] } }`.

**Single negotiation object (illustrative):**

```json
{
  "id": 8,
  "negotiation_code": "NEG-00008",
  "negotiation_ref": "NEG-00008",
  "name": "NEG-00008",
  "item_request_id": 15,
  "item_request_name": "IR-00015",
  "item_request": {
    "id": 15,
    "name": "IR-00015",
    "item_name": "Hyaluronic serum 50ml",
    "state": "in_progress"
  },
  "vendor_id": 3,
  "vendor_name": "Supplier SA",
  "agent_id": null,
  "agent_name": "",
  "item_name": "Hyaluronic serum 50ml",
  "quantity": 12000.0,
  "capacity": "50ml",
  "packing": 48.0,
  "packing_pcs_per_carton": 48.0,
  "offered_price": 2.5,
  "final_agreed_price": 0.0,
  "currency_id": 1,
  "currency_name": "USD",
  "final_currency_id": null,
  "final_currency_name": "",
  "terms": "MOQ 5000",
  "notes": "",
  "state": "ongoing",
  "status": "ongoing",
  "approval_by_id": null,
  "approval_by_name": "",
  "finalized_date": null,
  "attachments": [],
  "attachment_ids": [],
  "attachment_count": 0,
  "created_by_id": 2,
  "created_by_name": "User",
  "created_date": "2026-05-03T09:00:00",
  "created_at": "2026-05-03T09:00:00",
  "updated_at": "2026-05-03T09:00:00",
  "extra_fields": {},
  "multiple_offers_history": [],
  "offer_ids": [],
  "order_ids": [],
  "linked_orders": []
}
```

---

### 4.2 Get

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/get` |
| **Description** | One negotiation; includes offer history when serializer sets `include_offers` (default). |

**Success:** full object as above, typically with `multiple_offers_history` populated.

---

### 4.3 Create

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/create` |
| **Description** | Creates negotiation; optional first offer if `offered_price` set. |

**Request `params` example:**

```json
{
  "item_request_id": 15,
  "vendor_id": 3,
  "agent_id": 12,
  "item_name": "Hyaluronic serum 50ml",
  "notes": "Trial batch",
  "terms": "Net 30",
  "capacity": "50ml",
  "quantity": 12000,
  "packing": 48,
  "packing_pcs_per_carton": 48,
  "currency_id": 1,
  "final_agreed_price": 0,
  "final_currency_id": 1,
  "offered_price": 2.55,
  "offer_notes": "Opening quote",
  "attachment_ids": [301],
  "attachment_files": [],
  "extra_fields": { "fe.incoterm": "FOB" }
}
```

| Field | Required |
|-------|----------|
| `item_request_id` | **Yes** |
| `vendor_id` | **Yes** |

**Errors:**

```json
{ "success": false, "error": "item_request_id is required", "data": null }
```

```json
{ "success": false, "error": "vendor_id is required", "data": null }
```

---

### 4.4 Update

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/update` |
| **Description** | Partial update; `extra_fields` merged; supports attachment keys per §2. |

---

### 4.5 Delete (soft)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/delete` |

**Success:** `{ "success": true, "data": { "id": 8, "deleted": true } }`

---

### 4.6 Confirm / e-sign approve

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/confirm` |
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/e_sign_approve` |
| **Description** | Finalizes negotiation (`action_finalize`). |

**Success:** serialized negotiation.  
**Business error:**

```json
{
  "success": false,
  "error": "Only ongoing negotiations can be finalized.",
  "data": null
}
```

---

### 4.7 Offers add

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/offers/add` |

**Request `params`:**

```json
{
  "price": 2.45,
  "currency_id": 1,
  "notes": "Counter offer"
}
```

`price` is required.

**Success `data`:** one offer object:

```json
{
  "id": 44,
  "sequence": 10,
  "price": 2.45,
  "currency_id": 1,
  "currency_name": "USD",
  "notes": "Counter offer",
  "user_id": 2,
  "user_name": "User",
  "offer_date": "2026-05-03T10:00:00"
}
```

---

### 4.8 Offers list

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/offers/list` |

**Success:**

```json
{
  "success": true,
  "data": {
    "total": 3,
    "page": 1,
    "per_page": 20,
    "items": []
  }
}
```

(`items` entries match §4.7 response shape.)

---

### 4.9 Comments (chatter)

| Endpoint | Description |
|----------|-------------|
| `POST .../negotiations/<neg_id>/comments/list` | Paginated `mail.message` comments |
| `POST .../negotiations/<neg_id>/comments/add` | `body` or `message` required |
| `POST .../negotiations/<neg_id>/comments/<msg_id>/delete` | Deletes message if owned by record |

**Add request:**

```json
{ "body": "Please confirm lead time." }
```

---

### 4.10 Attachments link

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/negotiations/<neg_id>/attachments/link` |
| **Description** | Same semantics as item request §3.7 (IDs only; replace or clear). |

---

## 5. Supply purchase order (`lugal.crm.supply.po`)

Base path: `/api/crm/supply/po`

Vendor is resolved with **`vendor_customer_id`** = `res.partner` id that is linked to a `lugal.supply.vendor`.

### 5.1 List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/po/list` |

**Request `params` example:**

```json
{
  "page": 1,
  "per_page": 20,
  "status": "draft",
  "division": "europe",
  "vendor_customer_id": 45,
  "search": "PO-"
}
```

**PO object (illustrative success item):**

```json
{
  "id": 100,
  "name": "PO-00100",
  "order_id": "PO-00100",
  "vendor_customer_id": 45,
  "vendor_customer_name": "ACME Vendor",
  "vendor_customer_phone": "+123456789",
  "vendor_id": 3,
  "vendor_name": "ACME Vendor",
  "division": "europe",
  "currency_id": 1,
  "currency_name": "USD",
  "container_id": 5,
  "container_name": "CNT-001",
  "branch_id": 1,
  "branch_name": "Main",
  "status": "draft",
  "order_status": "draft",
  "status_label": "Draft",
  "is_suggested": false,
  "line_count": 1,
  "total_amount": 12500.5,
  "attachment_ids": [401],
  "attachment_count": 1,
  "attachments": [
    {
      "id": 401,
      "name": "order.pdf",
      "mimetype": "application/pdf",
      "size": 8800,
      "url": "/web/content/401?access_token=...",
      "file_url": "/web/content/401?access_token=...",
      "uploaded_by_name": "User",
      "created_at": "2026-05-03T11:00:00"
    }
  ],
  "item_request_id": 15,
  "item_request_name": "IR-00015",
  "item_request_item_name": "Hyaluronic serum 50ml",
  "item_request": { "id": 15, "name": "IR-00015", "item_name": "Hyaluronic serum 50ml", "state": "in_progress" },
  "negotiation_id": 8,
  "negotiation_name": "NEG-00008",
  "negotiation": { "id": 8, "name": "NEG-00008", "state": "ongoing", "final_agreed_price": 0.0 },
  "agent_id": null,
  "agent_name": "",
  "order_date": "2026-05-03",
  "production_completion_date": null,
  "payment_term": "deposit",
  "shipping_method": "sea",
  "notes": "",
  "order_e_sign_user_id": null,
  "order_e_sign_date": null,
  "payment_state": "pending",
  "amount_paid_total": 0.0,
  "balance_remaining": 12500.5,
  "linked_payments": [],
  "extra_fields": {},
  "created_by_id": 2,
  "created_by_name": "User",
  "created_at": "2026-05-03T11:00:00",
  "updated_at": "2026-05-03T11:00:00",
  "lines": [
    {
      "id": 500,
      "sequence": 10,
      "product_name": "Serum 50ml",
      "item_code": "SKU-1",
      "uom": "pcs",
      "quantity_pcs": 0.0,
      "quantity_carton": 0.0,
      "quantity": 1000.0,
      "size": "",
      "capacity": "",
      "packing_pcs_per_carton": 0.0,
      "unit_price": 12.5,
      "total_price": 12500.0,
      "currency_id": 1,
      "currency_name": "USD",
      "last_purchase_price": 0.0,
      "last_purchase_date": null,
      "min_qty": 0.0,
      "max_qty": 0.0
    }
  ]
}
```

---

### 5.2 Get

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/po/<po_id>/get` |

---

### 5.3 Create

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/po/create` |

**Request `params` example:**

```json
{
  "vendor_customer_id": 45,
  "name": "PO-CUSTOM-001",
  "division": "europe",
  "currency_id": 1,
  "container_id": 5,
  "branch_id": 1,
  "item_request_id": 15,
  "negotiation_id": 8,
  "agent_id": 12,
  "order_date": "2026-05-03",
  "production_completion_date": "2026-07-01",
  "payment_term": "deposit",
  "shipping_method": "sea",
  "notes": "Urgent",
  "extra_fields": { "fe.costCenter": "EU-01" },
  "attachment_ids": [401],
  "attachment_files": [],
  "lines": [
    {
      "product_name": "Serum 50ml",
      "item_code": "SKU-1",
      "uom": "pcs",
      "quantity": 1000,
      "unit_price": 12.5,
      "currency_id": 1,
      "min_qty": 0,
      "max_qty": 0
    }
  ]
}
```

**Error:**

```json
{
  "success": false,
  "error": "vendor_customer_id must reference a vendor-linked partner",
  "data": null
}
```

---

### 5.4 Update

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/po/<po_id>/update` |

Supports scalar header fields, `extra_fields` (merge), and attachment keys per §2.

---

### 5.5 Lines add / update / delete

| Endpoint | Description |
|----------|-------------|
| `POST .../po/<po_id>/lines/add` | Creates a line |
| `POST .../po/<po_id>/lines/<line_id>/update` | Updates line fields |
| `POST .../po/<po_id>/lines/<line_id>/delete` | Deletes line |

**Lines add `params` example:**

```json
{
  "product_name": "Serum 50ml",
  "item_code": "SKU-1",
  "uom": "pcs",
  "quantity": 1000,
  "unit_price": 12.5,
  "currency_id": 1,
  "min_qty": 0,
  "max_qty": 0
}
```

**Lines update:** optional `product_name`, `item_code`, `uom`, `quantity`, `unit_price`, `currency_id`, `sequence`, `size`, `capacity`, `min_qty`, `max_qty`, `last_purchase_price`, `last_purchase_date` (`YYYY-MM-DD`).

---

### 5.6 Workflow / status actions

| Endpoint | Effect |
|----------|--------|
| `POST .../po/<po_id>/confirm` | `status` → `confirmed` |
| `POST .../po/<po_id>/ship` | `status` → `confirmed` (compat) |
| `POST .../po/<po_id>/receive` | `status` → `confirmed` (compat) |
| `POST .../po/<po_id>/cancel` | `status` → `cancelled` |
| `POST .../po/<po_id>/reopen` | `status` → `draft` |
| `POST .../po/<po_id>/order_e_sign` | Records order e-sign on extended PO |

---

### 5.7 Delete (soft)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/po/<po_id>/delete` |

---

### 5.8 Attachments list / link

| Endpoint | Description |
|----------|-------------|
| `POST .../po/<po_id>/attachments/list` | `{ "po_id", "attachments": [ ... ] }` |
| `POST .../po/<po_id>/attachments/link` | `attachment_ids` or `ids`; empty list clears |

**Link `params`:**

```json
{ "attachment_ids": [401, 402] }
```

**Success (link):** full PO object (includes `attachment_ids`, `attachments`, `lines`, etc.).

---

### 5.9 PO comments (stub)

`comments/list` returns empty items; `comments/add` / `comments/<id>/delete` return not enabled errors.

---

## 6. Supply payment (`lugal.supply.payment`)

**This is not Odoo Accounting `account.move`.** It is a supply-chain payment row linked to **`lugal.crm.supply.po`** (`po_id`).

Base path: `/api/crm/supply/payments`

### 6.1 List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/list` |

**Request `params`:**

```json
{
  "page": 1,
  "per_page": 20,
  "po_id": 100,
  "payment_status": "partial",
  "payment_type": "deposit"
}
```

**Payment object example:**

```json
{
  "id": 20,
  "payment_id": "PAY-00020",
  "name": "PAY-00020",
  "po_id": 100,
  "linked_order_id": 100,
  "order_name": "PO-00100",
  "item_request_id": 15,
  "item_request_name": "IR-00015",
  "negotiation_id": 8,
  "negotiation_name": "NEG-00008",
  "container_id": 5,
  "container_name": "CNT-001",
  "paid_to": "supplier",
  "payee_partner_id": 45,
  "payee_name": "ACME Vendor",
  "payment_type": "deposit",
  "amount": 5000.0,
  "currency_id": 1,
  "currency_name": "USD",
  "payment_date": "2026-05-03",
  "payment_method": "bank",
  "remaining_balance": 7500.5,
  "payment_status": "partial",
  "notes": "30% deposit",
  "attachments": [
    {
      "id": 501,
      "name": "receipt.pdf",
      "mimetype": "application/pdf",
      "size": 4000,
      "url": "/web/content/501?access_token=...",
      "file_url": "/web/content/501?access_token=...",
      "uploaded_by_name": "User",
      "created_at": "2026-05-03T12:00:00"
    }
  ],
  "attachment_ids": [501],
  "attachment_count": 1,
  "created_at": "2026-05-03T12:00:00",
  "updated_at": "2026-05-03T12:00:00"
}
```

---

### 6.2 Get

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/<payment_id>/get` |

---

### 6.3 Create

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/create` |

**Request `params` example:**

```json
{
  "po_id": 100,
  "linked_order_id": 100,
  "amount": 5000,
  "payment_type": "deposit",
  "paid_to": "supplier",
  "payee_partner_id": 45,
  "currency_id": 1,
  "payment_date": "2026-05-03",
  "payment_method": "bank transfer",
  "notes": "Deposit",
  "attachment_ids": [501],
  "attachment_files": []
}
```

| Field | Required |
|-------|----------|
| `po_id` or `linked_order_id` | **Yes** |
| `amount` | **Yes** |

**Errors:**

```json
{ "success": false, "error": "po_id and amount are required", "data": null }
```

---

### 6.4 Update

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/<payment_id>/update` |

Updatable: `paid_to`, `payment_type`, `payment_method`, `notes`, `amount`, `currency_id`, `payee_partner_id`, `payment_date`, plus attachment keys §2.

---

### 6.5 Delete

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/<payment_id>/delete` |

Hard **`unlink`** on the payment record.

---

### 6.6 Attachments link

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/payments/<payment_id>/attachments/link` |

Same ID list semantics as other `attachments/link` routes.

---

## 7. Shipment / container (`lugal.supply.container`)

Two route families target the **same** model:

1. **`/api/crm/supply/containers/...`** — older “container” naming (supply chain controller).
2. **`/api/crm/supply/shipments/...`** — “shipment” naming (extra controller); supports **`attachment_ids` / `attachment_files`** on create/update.

### 7.1 Containers API (supply_chain)

#### List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/containers/list` |

**`params`:** `page`, `per_page`, `status` (legacy `lugal.supply.container` status: `waiting` / `active` / `at_port` / `completed`), `division`, `search`.

#### Get

`POST /api/crm/supply/containers/<container_id>/get`

#### Create

`POST /api/crm/supply/containers/create`

**`params` example:**

```json
{
  "name": "Shipment May",
  "container_number": "MSCU1234567",
  "bl_number": "BL-8899",
  "clearance_company": "ClearCo",
  "origin_location": "Shanghai",
  "destination_port": "Rotterdam",
  "departure_date": "2026-05-10",
  "eta": "2026-06-01",
  "division": "china",
  "tracking_url": "https://tracking.example/track",
  "notes": ""
}
```

`name` is required. **No** `attachment_files` on this route (use shipments create or separate attachment flow).

#### Update

`POST /api/crm/supply/containers/<container_id>/update`

Accepts `name`, `container_number`, `bl_number`, `clearance_company`, `origin_location`, `destination_port` (maps to `destination_location`), `status`, `division`, `departure_date`, `eta`, `tracking_url`, `notes`, `shipping_line`.

#### Delete (soft)

`POST /api/crm/supply/containers/<container_id>/delete`

#### Mark arrived

`POST /api/crm/supply/containers/<container_id>/mark_arrived` — sets arrived timestamps and tracking state.

#### Clearance delivered

`POST /api/crm/supply/containers/<container_id>/clearance_delivered`

#### Driver / reminder (no-op or stub)

`assign_driver`, `unassign_driver`, `set_reminder` — return success with current serialized container where applicable.

**Serialized container (supply_chain list/get) example:**

```json
{
  "id": 5,
  "name": "Shipment May",
  "container_number": "MSCU1234567",
  "bl_number": "BL-8899",
  "clearance_company_id": null,
  "clearance_company_name": "ClearCo",
  "origin_location": "Shanghai",
  "destination_port": "Rotterdam",
  "departure_date": "2026-05-10",
  "eta": "2026-06-01",
  "arrived_at": null,
  "status": "waiting",
  "division": "china",
  "tracking_url": "https://tracking.example/track",
  "total_weight_kg": 0.0,
  "total_cbm": 0.0,
  "driver_id": null,
  "driver_name": "",
  "driver_phone": "",
  "driver_assigned_at": null,
  "driver_assigned_by": "",
  "clearance_info_delivered": false,
  "clearance_info_delivered_at": null,
  "clearance_info_delivered_by": "",
  "attachment_count": 0,
  "penalty_count": 0,
  "vendor_id": 3,
  "vendor_name": "Supplier SA",
  "reminder_date": null,
  "reminder_note": "",
  "notes": "",
  "created_at": "2026-05-03T08:00:00",
  "updated_at": "2026-05-03T08:00:00"
}
```

#### Container attachments (detailed list)

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/containers/<container_id>/attachments/list` |

Returns `{ "container_id", "attachments": [ full _serialize_attachment, ... ] }` (see `supply_controller`).

---

### 7.2 Shipments API (extra — recommended for attachments on create/update)

#### List

| Item | Value |
|------|--------|
| **Endpoint** | `POST /api/crm/supply/shipments/list` |

**`params`:** `page`, `per_page`, `status` (filters `shipment_tracking_state`: `pending` / `in_transit` / `transshipment` / `arrived`), `supplier_id`, `search`.

#### Get

`POST /api/crm/supply/shipments/<shipment_id>/get`

#### Create

`POST /api/crm/supply/shipments/create`

**`params` example:**

```json
{
  "name": "Shipment May",
  "container_number": "MSCU1234567",
  "supplier_id": 3,
  "agent_id": 12,
  "shipping_method": "sea",
  "origin": "Shanghai",
  "destination": "Rotterdam",
  "etd": "2026-05-10",
  "eta": "2026-06-01",
  "status": "in_transit",
  "shipping_line": "MSC",
  "attachment_ids": [601],
  "attachment_files": []
}
```

`name` **or** `container_number` required (at least one non-empty).

#### Update

`POST /api/crm/supply/shipments/<shipment_id>/update` — same field names as create where supported; supports §2 attachment keys.

#### Delete (soft)

`POST /api/crm/supply/shipments/<shipment_id>/delete`

#### Link orders

`POST /api/crm/supply/shipments/<shipment_id>/link_orders`

**`params`:**

```json
{ "order_ids": [100, 101] }
```

Alias: `po_ids`.

**Success `data`:** `_serialize_shipment_container` payload, e.g.:

```json
{
  "id": 5,
  "shipment_id": "SHP-00005",
  "name": "Shipment May",
  "container_number": "MSCU1234567",
  "supplier_id": 3,
  "supplier_name": "Supplier SA",
  "agent_id": null,
  "agent_name": "",
  "linked_orders": [
    {
      "id": 100,
      "name": "PO-00100",
      "total_amount": 12500.5,
      "status": "draft",
      "currency_id": 1,
      "currency_name": "USD",
      "item_request_id": 15,
      "item_request_name": "IR-00015",
      "negotiation_id": 8,
      "negotiation_name": "NEG-00008"
    }
  ],
  "shipping_method": "sea",
  "origin": "Shanghai",
  "destination": "Rotterdam",
  "etd": "2026-05-10",
  "eta": "2026-06-01",
  "status": "in_transit",
  "shipment_tracking_state": "in_transit",
  "shipping_line": "MSC",
  "attachments": [],
  "attachment_ids": [],
  "attachment_count": 0,
  "tracking_url": "",
  "created_at": "2026-05-03T08:00:00",
  "updated_at": "2026-05-03T08:00:00"
}
```

---

## 8. Generic error patterns

| Situation | Example `error` |
|-----------|-----------------|
| Missing / invalid JWT | `"Unauthorized"` |
| Not found | `"Item request not found"`, `"Negotiation not found"`, `"PO not found"`, `"Payment not found"`, `"Shipment not found"`, `"Container not found"` |
| Validation | `"item_name is required"`, `"price is required"`, `"body is required"` |
| Wrong type | `"attachment_ids must be a list"`, `"order_ids must be a list of PO ids"` |
| Base64 | `"Invalid base64 in attachment_files"` |
| Server / DB after rollback | `"<exception message>"` via `crm_error` |

---

## 9. Related docs

- [SUPPLY_EXTRA_FIELDS_JSON.md](./SUPPLY_EXTRA_FIELDS_JSON.md) — `extra_fields` rules for item request, negotiation, supply PO.
- Multipart uploads used to obtain `ir.attachment` ids: `/api/crm/supply/chat/upload`, `/api/lugal/email/attachments/upload` (see main CRM / email integration docs).
