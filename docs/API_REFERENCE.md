# NBS — Complete API Reference
### For the Frontend Developer

---

## 🔌 Server Info

| Item | Value |
|------|-------|
| **Base URL** | `http://192.168.116.211:8070` |
| **Database Name** | `lugal_local` |
| **POS API Prefix** | `/api/pos_perfume/v1` |
| **Archive API Prefix** | `/api` |

> ⚠️ Replace `YOUR_SERVER_IP` with the actual server IP address.

---

## ═══════════════════════════════════════════════
## PART 1 — POS Perfume API  `/api/pos_perfume/v1`
## ═══════════════════════════════════════════════

### 🔐 Authentication — POS API

The POS API supports **two authentication methods**:

---

#### Method 1 — Login with Username & Password (Recommended for apps)

Use the standard Odoo session endpoint to authenticate and receive a **session token** (cookie-based).

```
POST /web/session/authenticate
Content-Type: application/json
```

**Body:**
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "id": 1,
  "params": {
    "db": "lugal_local",
    "login": "admin",
    "password": "admin"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "uid": 3,
    "name": "Administrator",
    "username": "admin",
    "session_id": "abc123xyz...",
    "db": "lugal_local",
    "company_id": 1,
    "company_name": "Nour Al-Nebras"
  }
}
```

> After login, the browser automatically sends the session cookie with every request.
> For non-browser clients (React Native, mobile apps, etc.), extract `session_id` from the response and send it manually:
>
> ```
> Cookie: session_id=abc123xyz...
> ```

**JavaScript Login Example:**
```javascript
const BASE = 'http://YOUR_SERVER_IP:8070';

async function login(username, password) {
  const response = await fetch(`${BASE}/web/session/authenticate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',   // important: allows cookies to be stored
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      id: 1,
      params: {
        db: 'lugal_local',
        login: username,
        password: password,
      }
    })
  });

  const data = await response.json();

  if (data.result?.uid) {
    console.log('Logged in as:', data.result.name);
    // Session cookie is now set automatically in the browser
    // For non-browser clients: store data.result.session_id
    return data.result;
  } else {
    throw new Error('Login failed');
  }
}
```

---

#### Method 2 — Odoo API Key (Stateless Bearer Token)

Suitable for server-to-server integrations or when you cannot use cookies.

```
Authorization: Bearer <ODOO_API_KEY>
Content-Type: application/json
```

**How to generate an API Key:**
1. Log into Odoo → Settings → Technical → API Keys → New
2. Create the key and copy it — it **will not be shown again**

**JavaScript Example:**
```javascript
const headers = {
  'Authorization': 'Bearer YOUR_API_KEY_HERE',
  'Content-Type': 'application/json',
};

const response = await fetch(`${BASE}/api/pos_perfume/v1/setup`, { headers });
```

---

> **Summary:**
>
> | Method | How | Best for |
> |--------|-----|----------|
> | Session (Login) | `POST /web/session/authenticate` → cookie | Browser apps |
> | API Key (Bearer) | `Authorization: Bearer <key>` header | Mobile / server apps |

---

### Standard Response Envelope

All endpoints return the same JSON structure.

**Success:**
```json
{
  "success": true,
  "message": "OK",
  "data": { ... }
}
```

**Error:**
```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

---

## ── Setup & Session ──────────────────────────────────────────────────────────

### GET /api/pos_perfume/v1/setup
> Single bootstrap call — returns everything needed to initialize the POS in one request.

**Headers:** `Authorization: Bearer <key>`

**Response:**
```json
{
  "success": true,
  "data": {
    "pricelists": [
      { "id": 1, "name": "USD Pricelist", "currency_id": 2 }
    ],
    "default_pricelist_id": 1,
    "warehouses": [
      { "id": 1, "name": "Main Warehouse", "code": "WH" }
    ],
    "users": [
      { "id": 3, "name": "Ahmed Al-Farsi" }
    ],
    "invoice_types": [
      { "key": "1", "label": "Shop Customer" },
      { "key": "2", "label": "Delivery Companies" },
      { "key": "3", "label": "Transport" },
      { "key": "4", "label": "Delivery" },
      { "key": "5", "label": "NBS" },
      { "key": "6", "label": "Shorja" },
      { "key": "7", "label": "NA" },
      { "key": "8", "label": "Shorja Offices" }
    ],
    "exchange_rate": 1470.0,
    "currency": "USD",
    "secondary_currency": "IQD"
  }
}
```

---

### GET /api/pos_perfume/v1/session
> Returns the current authenticated user info and the default exchange rate.

**Response:**
```json
{
  "success": true,
  "data": {
    "user_id": 3,
    "user_name": "Ahmed Al-Farsi",
    "user_login": "ahmed",
    "company_id": 1,
    "company_name": "Nour Al-Nebras",
    "uid": 3,
    "exchange_rate": 1470.0
  }
}
```

---

### GET /api/pos_perfume/v1/settings
> Returns the current exchange rate setting.

```json
{ "success": true, "data": { "exchange_rate": 1470.0 } }
```

---

### PUT /api/pos_perfume/v1/settings
> Updates the global exchange rate.

**Body:** `{ "exchange_rate": 1480.0 }`

---

### GET /api/pos_perfume/v1/pricelists
> Returns all active pricelists.

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "name": "USD Retail", "currency_id": 2, "currency_name": "USD" }
    ],
    "total": 3
  }
}
```

---

### GET /api/pos_perfume/v1/warehouses
> Returns all active warehouses.

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      { "id": 1, "name": "Main Warehouse", "code": "WH" }
    ],
    "total": 2
  }
}
```

---

## ── Products ─────────────────────────────────────────────────────────────────

### GET /api/pos_perfume/v1/products
> Search and list products.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | `""` | Searches name, internal code, and foreign name |
| `pricelist_id` | int | — | Calculates prices based on this pricelist |
| `limit` | int | `80` | Number of results |
| `offset` | int | `0` | Pagination offset |

**Example:** `GET /api/pos_perfume/v1/products?query=oud&limit=20&pricelist_id=1`

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 150,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 42,
        "name": "Royal Oud",
        "default_code": "OUD-001",
        "foreign_name": "Royal Oud",
        "uom_id": { "id": 1, "name": "Unit" },
        "list_price": 25.0,
        "qty_available": 100.0,
        "color_class": "gold",
        "badge_text": "VIP"
      }
    ]
  }
}
```

---

### GET /api/pos_perfume/v1/products/{product_id}
> Get a single product with full details (all UoMs with prices + stock per warehouse).

**Query Parameters:** `pricelist_id` (optional)

**Example:** `GET /api/pos_perfume/v1/products/42?pricelist_id=1`

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "Royal Oud",
    "default_code": "OUD-001",
    "foreign_name": "Royal Oud",
    "uom_id": { "id": 1, "name": "Unit" },
    "list_price": 25.0,
    "qty_available": 100.0,
    "available_uoms": [
      { "id": 1, "name": "Unit",   "price": 25.0 },
      { "id": 5, "name": "Tola",   "price": 12.0 },
      { "id": 6, "name": "Carton", "price": 250.0 }
    ],
    "warehouses": [
      { "id": 1, "name": "Main Warehouse", "code": "WH",  "quantity": 80.0 },
      { "id": 2, "name": "Warehouse 2",    "code": "WH2", "quantity": 20.0 }
    ],
    "color_class": "gold",
    "badge_text": "VIP"
  }
}
```

---

### POST /api/pos_perfume/v1/products/data
> Same as `GET /products/{id}` but via POST body — useful when you need to pass pricelist + uom together.

**Body:**
```json
{
  "product_id": 42,
  "pricelist_id": 1,
  "uom_id": 5
}
```

**Response:** Same as the GET endpoint above.

---

### POST /api/pos_perfume/v1/products/uom_price
> Get the price for a specific unit of measure — called when the user changes the UoM on an order line.

**Body:**
```json
{ "product_id": 42, "pricelist_id": 1, "uom_id": 5 }
```

**Response:**
```json
{ "success": true, "data": { "price_unit": 12.0 } }
```

---

## ── Customers ────────────────────────────────────────────────────────────────

### GET /api/pos_perfume/v1/customers
> Search and list customers (`res.partner`).

**Query Parameters:** `query`, `limit` (default 50), `offset` (default 0)

**Example:** `GET /api/pos_perfume/v1/customers?query=ali&limit=20`

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 200,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 10,
        "name": "Ali Mohammed",
        "ref": "C-001",
        "phone": "+9647801234567",
        "mobile": "+9647801234567",
        "email": "ali@example.com",
        "street": "Al-Rashid Street",
        "city": "Baghdad",
        "country_id": { "id": 106, "name": "Iraq" },
        "pricelist_id": { "id": 1, "name": "USD Retail" }
      }
    ]
  }
}
```

---

### POST /api/pos_perfume/v1/customers
> Create a new customer.

**Body:**
```json
{
  "name": "Ali Mohammed",
  "phone": "+9647801234567",
  "mobile": "+9647801234567",
  "email": "ali@example.com",
  "street": "Al-Rashid Street",
  "city": "Baghdad",
  "ref": "C-001",
  "country_id": 106
}
```

**Response:** `{ "success": true, "data": { ...customer object... } }`

---

### GET /api/pos_perfume/v1/customers/{customer_id}
> Get a single customer by ID.

---

### PUT /api/pos_perfume/v1/customers/{customer_id}
> Update a customer.

**Body:** Any of `name, phone, mobile, email, street, city, ref, country_id`

---

## ── Orders ───────────────────────────────────────────────────────────────────

### Order Object (Full Structure)

```json
{
  "id": 123,
  "name": "POS/2026/00123",
  "date": "2026-02-27T10:30:00",
  "state": "sale",
  "user_id": { "id": 3, "name": "Ahmed" },
  "partner_id": {
    "id": 10,
    "name": "Ali Mohammed",
    "phone": "+9647801234567",
    "mobile": "",
    "email": ""
  },
  "pricelist_id": { "id": 1, "name": "USD Retail" },
  "currency_id": { "id": 2, "name": "USD" },
  "exchange_rate": 1470.0,
  "amount_subtotal": 100.0,
  "amount_discount": 5.0,
  "amount_tax": 0.0,
  "amount_total": 95.0,
  "amount_total_iqd": 139650.0,
  "invoice_type": "1",
  "note": "",
  "sale_order_id": {
    "id": 55,
    "name": "S00055",
    "state": "sale"
  },
  "sap_doc_num": "12345",
  "sap_doc_entry": 678,
  "sap_synced": true,
  "sap_error_message": "",
  "sap_last_sync_date": "2026-02-27T10:31:00",
  "order_lines": [
    {
      "id": 456,
      "sequence": 10,
      "product_id": {
        "id": 42,
        "name": "Royal Oud",
        "default_code": "OUD-001",
        "foreign_name": "Royal Oud"
      },
      "product_uom_id": { "id": 1, "name": "Unit" },
      "warehouse_id": { "id": 1, "name": "Main Warehouse", "code": "WH" },
      "location_id": { "id": 8, "name": "Stock" },
      "quantity": 2.0,
      "unit_price": 25.0,
      "discount_percent": 10.0,
      "price_after_discount": 22.5,
      "discount_amount": 2.5,
      "line_subtotal": 50.0,
      "line_total": 45.0,
      "available_qty": 80.0,
      "custom_product_name": ""
    }
  ]
}
```

**Order States:**

| State | Description |
|-------|-------------|
| `draft` | Draft — editable |
| `quotation` | Sent as quotation |
| `sale` | Confirmed — `sale.order` created and synced to SAP |
| `done` | Completed |
| `cancel` | Cancelled |

---

### GET /api/pos_perfume/v1/orders
> List orders with optional filters.

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `query` | string | Search by order name |
| `state` | string | `draft` / `quotation` / `sale` / `done` / `cancel` |
| `partner_id` | int | Filter by customer ID |
| `user_id` | int | Filter by salesperson ID |
| `date_from` | string | `YYYY-MM-DD` |
| `date_to` | string | `YYYY-MM-DD` |
| `sap_synced` | bool | `true` / `false` |
| `limit` | int | Default 50 |
| `offset` | int | Default 0 |

**Response:**
```json
{
  "success": true,
  "data": {
    "total": 500,
    "offset": 0,
    "limit": 50,
    "items": [
      {
        "id": 123,
        "name": "POS/2026/00123",
        "date": "2026-02-27T10:30:00",
        "state": "sale",
        "partner_id": 10,
        "partner_name": "Ali Mohammed",
        "user_id": 3,
        "user_name": "Ahmed",
        "invoice_type": "1",
        "amount_total": 95.0,
        "amount_total_iqd": 139650.0,
        "sap_synced": true,
        "sap_doc_num": "12345",
        "note": ""
      }
    ]
  }
}
```

> ⚠️ The list response does **not** include `order_lines` for performance. Use `GET /orders/{id}` to retrieve a full order with its lines.

---

### POST /api/pos_perfume/v1/orders
> Create a new order.

**Body:**
```json
{
  "partner_id": 10,
  "pricelist_id": 1,
  "invoice_type": "1",
  "note": "Optional note",
  "exchange_rate": 1480.0,
  "user_id": 3,
  "order_lines": [
    {
      "product_id": 42,
      "product_uom_id": 1,
      "warehouse_id": 1,
      "quantity": 2.0,
      "unit_price": 25.0,
      "discount_percent": 10.0,
      "custom_product_name": ""
    }
  ]
}
```

> `partner_id` is required. `order_lines` is optional — lines can be added later.
> If `pricelist_id` is omitted, the system default pricelist is used.

**Response:** Full Order Object

---

### GET /api/pos_perfume/v1/orders/{order_id}
> Get full order details including all lines.

**Response:** Full Order Object

---

### PUT /api/pos_perfume/v1/orders/{order_id}
> Update the order header (not lines).
> ⚠️ Only allowed on `draft` and `quotation` orders.

**Body:** Any of `partner_id, pricelist_id, note, invoice_type, exchange_rate, user_id`

---

### DELETE /api/pos_perfume/v1/orders/{order_id}
> Cancel the order (soft cancel — sets `state` to `cancel`).
> ⚠️ Not allowed on `done` orders.

---

## ── Order Lines ──────────────────────────────────────────────────────────────

### POST /api/pos_perfume/v1/orders/{order_id}/lines
> Add a new line to an existing order.
> ⚠️ Not allowed on `done` or `cancel` orders.

**Body:**
```json
{
  "product_id": 42,
  "product_uom_id": 1,
  "warehouse_id": 1,
  "quantity": 3.0,
  "unit_price": 25.0,
  "discount_percent": 5.0,
  "custom_product_name": ""
}
```

> `product_id` and `warehouse_id` are required.

**Response:** The created Line Object.

---

### PUT /api/pos_perfume/v1/orders/{order_id}/lines/{line_id}
> Update an existing order line.

**Body:** Any of `product_id, product_uom_id, warehouse_id, location_id, quantity, unit_price, discount_percent, custom_product_name, sequence`

---

### DELETE /api/pos_perfume/v1/orders/{order_id}/lines/{line_id}
> Delete a line from the order.

---

## ── Order Actions ────────────────────────────────────────────────────────────

### POST /api/pos_perfume/v1/orders/{order_id}/confirm
> **Confirm the order** → creates a `sale.order` in Odoo and automatically syncs to SAP.

**Requirements:** Order must have at least one line and must not be `done` or `cancel`.

**Response:**
```json
{
  "success": true,
  "message": "Order confirmed",
  "data": {
    "id": 123,
    "name": "POS/2026/00123",
    "state": "sale",
    "sale_order_id": { "id": 55, "name": "S00055", "state": "sale" },
    "sap_synced": true,
    "sap_doc_num": "12345",
    "sap_doc_entry": 678,
    "sap_error_message": ""
  }
}
```

---

### POST /api/pos_perfume/v1/orders/{order_id}/quotation
> Set the order state to `quotation`.

---

### POST /api/pos_perfume/v1/orders/{order_id}/cancel
> Cancel the order (uses `action_cancel`).

---

### POST /api/pos_perfume/v1/orders/{order_id}/draft
> Reset a cancelled order back to `draft`.

---

### POST /api/pos_perfume/v1/orders/{order_id}/sync_sap
> Force re-sync the linked sale order to SAP.
> Requires the order to already have a `sale_order_id` (i.e., must be confirmed first).

**Response:**
```json
{
  "success": true,
  "data": {
    "sap_synced": true,
    "sap_doc_num": "12345",
    "sap_doc_entry": 678,
    "sap_error_message": ""
  }
}
```

---

### GET /api/pos_perfume/v1/orders/{order_id}/report
> Download the order PDF invoice.

**Query Parameters:** `download=true` (default, triggers file download) or `download=false` (inline in browser)

**Response:** Binary PDF with `Content-Type: application/pdf`

> If `wkhtmltopdf` is not installed on the server:
> ```json
> {
>   "success": true,
>   "data": { "pdf_available": false, "setup_required": "sudo apt-get install wkhtmltopdf" }
> }
> ```

---

### POST /api/pos_perfume/v1/orders/{order_id}/send_whatsapp
> Send the invoice as a WhatsApp text message.
> Requires ULTRAMSG to be configured in Odoo.

**Success Response:**
```json
{ "success": true, "data": { "sent": true, "message_id": "MSG123" } }
```

**When ULTRAMSG is not configured:**
```json
{ "success": true, "data": { "sent": false, "available": false, "setup_required": "..." } }
```

---

### POST /api/pos_perfume/v1/orders/{order_id}/send_whatsapp_image
> Send the invoice as a WhatsApp image.
> Requires `wkhtmltoimage` + ULTRAMSG to be configured.

---

### PUT /api/pos_perfume/v1/orders/{order_id}/exchange_rate
> Update the IQD exchange rate on a specific order.

**Body:** `{ "exchange_rate": 1490.0 }` — Send an empty body `{}` to reset to the current system default.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 123,
    "exchange_rate": 1490.0,
    "amount_total_iqd": 141550.0
  }
}
```

---

## ═══════════════════════════════════════════════
## PART 2 — NBS Archive API  `/api`
## ═══════════════════════════════════════════════

### 🔐 Authentication — Archive API

The Archive API uses **JWT Tokens**.

---

### POST /api/auth/login

**Body:**
```json
{
  "username": "admin",
  "password": "admin",
  "database": "lugal_local"
}
```

**Response:**
```json
{
  "success": true,
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "Bearer",
  "user": {
    "id": 3,
    "name": "Admin User",
    "login": "admin",
    "groups": ["manager"]
  }
}
```

> Use the `access_token` in all subsequent requests:
> ```
> Authorization: Bearer eyJ...
> Content-Type: application/json
> ```

---

### POST /api/auth/refresh
> Get a new access token using the refresh token.

**Body:** `{ "refresh_token": "eyJ..." }`

**Response:** `{ "access_token": "eyJ..." }`

---

### POST /api/auth/logout

**Body:** `{ "refresh_token": "eyJ..." }`

---

### POST /api/auth/me
> Returns the current user's profile.

---

> ### ⚠️ Important: JSON-RPC vs Plain HTTP
>
> Most Archive endpoints use **JSON-RPC format**. The correct request body is:
>
> ```json
> {
>   "jsonrpc": "2.0",
>   "method": "call",
>   "id": 1,
>   "params": {
>     "db": "lugal_local",
>     ... other params here ...
>   }
> }
> ```
>
> Endpoints that use **plain HTTP** (not JSON-RPC) are explicitly noted below.
> Auth endpoints (`/api/auth/*`) and file upload endpoints always use plain HTTP.

---

## ── Departments ──────────────────────────────────────────────────────────────

### POST /api/departments
> List all departments.

**Params (inside `params` key):** `search` (string), `limit` (int)

**Response:**
```json
{
  "result": {
    "success": true,
    "data": [
      { "id": 1, "name": "Accounting", "document_count": 50 }
    ]
  }
}
```

---

### POST /api/departments/{department_id}
> Get a single department by ID.

---

### POST /api/departments/create
> Create a new department.

**Params:** `name` (required), `description`

---

### POST /api/departments/{id}/update
> Update a department.

**Params:** `name`, `description`

---

### DELETE /api/departments/{id}
> Delete a department (soft delete).

---

## ── Document Types ───────────────────────────────────────────────────────────

### POST /api/document-types
> List all document types.

**Params:** `search`, `department_id`, `limit`

---

### POST /api/document-types/create
> Create a new document type.

**Params:** `name` (required), `department_id` (required), `description`

---

### POST /api/document-types/{id}/update
**Params:** `name`, `description`

---

### DELETE /api/document-types/{id}

---

## ── Folders ──────────────────────────────────────────────────────────────────

### POST /api/folders
> List folders with optional filters.

**Params:**
```json
{
  "department_id": 1,
  "document_type_id": 2,
  "search": "contracts",
  "company_id": 3,
  "limit": 50,
  "offset": 0
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "total": 100,
    "data": [
      {
        "id": 10,
        "name": "Contracts 2026",
        "department_id": 1,
        "department_name": "Accounting",
        "document_type_id": 2,
        "document_type_name": "Contract",
        "company_id": 3,
        "company_name": "Nour Al-Nebras",
        "document_count": 15,
        "created_at": "2026-01-01T00:00:00",
        "last_modified": "2026-02-20T14:30:00"
      }
    ]
  }
}
```

---

### POST /api/folders/{folder_id}
> Get a single folder with its document list.

---

### POST /api/folders/create
> Create a new folder.

**Params:**
```json
{
  "name": "Contracts 2026",
  "department_id": 1,
  "document_type_id": 2,
  "company_id": 3
}
```

---

### POST /api/folders/{id}/update
**Params:** `name`, `department_id`, `document_type_id`, `company_id`

---

### DELETE /api/folders/{id}
> Delete a folder.

---

### POST /api/folders/{id}/move
> Move a folder to a different department.

**Params:** `department_id` (required)

---

### POST /api/folders/tree
> Get the full folder structure as a tree.

---

### POST /api/folders/{id}/documents
> List all documents inside a specific folder.

---

### POST /api/folders/{id}/add-document
> Add an existing document to a folder.

**Params:** `document_id` (required)

---

### POST /api/folders/{folder_id}/workflow
> Get the current workflow assigned to a folder.

### POST /api/folders/{folder_id}/workflow/set
> Assign a workflow to a folder.

**Params:** `workflow_id`

### POST /api/folders/{folder_id}/workflow/transition
> Move the folder to the next workflow stage.

**Params:** `action` (string — transition name)

---

## ── Documents ────────────────────────────────────────────────────────────────

### POST /api/documents
> List documents with optional filters.

**Params:**
```json
{
  "folder_id": 10,
  "department_id": 1,
  "document_type_id": 2,
  "company_id": 3,
  "search": "contract",
  "status": "active",
  "limit": 50,
  "offset": 0
}
```

**Response:**
```json
{
  "result": {
    "success": true,
    "total": 200,
    "data": [
      {
        "id": 100,
        "name": "Lease Contract 2026",
        "folder_id": 10,
        "folder_name": "Contracts 2026",
        "department_id": 1,
        "department_name": "Accounting",
        "document_type_id": 2,
        "document_type_name": "Contract",
        "company_id": 3,
        "company_name": "Nour Al-Nebras",
        "file_name": "contract_2026.pdf",
        "file_size": 204800,
        "mime_type": "application/pdf",
        "status": "active",
        "version": 2,
        "confidentiality_level": "internal",
        "created_at": "2026-01-15T09:00:00",
        "created_by": "Ahmed",
        "tags": ["important", "contract"]
      }
    ]
  }
}
```

---

### POST /api/documents/{document_id}
> Get a single document with full details.

---

### POST /api/documents/upload
> **Upload a new document** — uses `multipart/form-data`, NOT JSON-RPC.

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | File | ✅ | The file to upload |
| `folder_id` | int | ✅ | Target folder ID |
| `name` | string | ❌ | Document name (defaults to file name) |
| `document_type_id` | int | ❌ | |
| `tags` | JSON string | ❌ | e.g. `'["important","contract"]'` |
| `confidentiality_level` | string | ❌ | `public` / `internal` / `confidential` / `top_secret` |

**Example (JavaScript):**
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('folder_id', '10');
formData.append('name', 'Lease Contract 2026');
formData.append('confidentiality_level', 'internal');

const response = await fetch('http://YOUR_SERVER_IP:8070/api/documents/upload', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer eyJ...' },
  body: formData
});
```

---

### GET /api/documents/{document_id}/download
> Download the document file — plain GET request, returns binary content.

```
GET /api/documents/100/download
Authorization: Bearer eyJ...
```

**Response:** Binary file with appropriate `Content-Type` and `Content-Disposition` headers.

---

### POST /api/documents/{id}/update
> Update document metadata or upload a new version — uses `multipart/form-data`.

**Form Fields:** `name`, `document_type_id`, `tags`, `file` (to upload a new version), `confidentiality_level`

---

### POST /api/documents/{id}/versions
> Get the version history of a document.

---

### POST /api/documents/{id}/archive
> Archive a document (soft delete, keeps it accessible).

---

### POST /api/documents/{id}/unarchive
> Restore an archived document.

---

### POST /api/documents/{id}/trash
> Move a document to the trash.

---

### POST /api/documents/{id}/restore
> Restore a document from the trash.

---

### DELETE /api/documents/{id}
**or** POST /api/documents/{id}/permanent
> Permanently delete a document. This action is irreversible.

---

### POST /api/documents/trash
> List all documents currently in the trash.

---

### POST /api/documents/restore
> Restore multiple documents from trash in a single call.

**Params:** `document_ids: [100, 101, 102]`

---

### POST /api/documents/permanent-delete
> Permanently delete multiple documents at once.

**Params:** `document_ids: [100, 101]`

---

### POST /api/documents/{document_id}/set-parent
> Set or change the parent document (document hierarchy).

**Params:** `parent_id`

---

## ── Document Attachments ─────────────────────────────────────────────────────

### POST /api/documents/{document_id}/attachments
> List all attachments (secondary documents) of a document.

---

### POST /api/documents/{document_id}/add-attachment
> Add an attachment to a document — uses `multipart/form-data`.

**Form Fields:** `file` (required), `name`

---

### GET /api/documents/{document_id}/attachments/{attachment_id}/download
> Download a specific attachment.

---

### POST /api/documents/{document_id}/attachments/{attachment_id}/update
**Params:** `name`

---

### DELETE /api/documents/{document_id}/attachments/{attachment_id}
> Delete an attachment.

---

### POST /api/documents/{document_id}/attachments/{attachment_id}/restore
> Restore a deleted attachment.

---

### POST /api/documents/{document_id}/attachments/{attachment_id}/permanent
> Permanently delete an attachment.

---

### POST /api/documents/{document_id}/attachments/multiple
> Add multiple attachments in a single call — uses `multipart/form-data`.

---

## ── Document Relations ───────────────────────────────────────────────────────

### POST /api/documents/{document_id}/relations
> Get all documents related to this document.

---

### POST /api/documents/{document_id}/add-relation
> Link two documents together.

**Params:** `related_document_id` (required), `relation_type` (optional)

---

## ── Edit Requests ────────────────────────────────────────────────────────────

### POST /api/edit-requests
> List all edit requests.

### POST /api/edit-requests/create
> Request permission to edit a document.

**Params:** `document_id` (required), `reason` (required)

### POST /api/edit-requests/{id}/approve
> Approve an edit request (managers only).

### POST /api/edit-requests/{id}/reject
> Reject an edit request.

**Params:** `reason`

### POST /api/edit-requests/pending-approvals
> List all edit requests awaiting manager approval.

### POST /api/documents/{document_id}/upload-version
> Upload a new document version after an edit request has been approved.

---

## ── Batch Operations ──────────────────────────────────────────────────────────

### POST /api/documents/batch/archive
**Params:** `document_ids: [1, 2, 3]`

### POST /api/documents/batch/unarchive
**Params:** `document_ids: [1, 2, 3]`

### POST /api/documents/batch/trash
**Params:** `document_ids: [1, 2, 3]`

### POST /api/documents/batch/move-folder
**Params:** `document_ids: [1, 2, 3]`, `folder_id: 10`

---

## ── Bulk Upload ──────────────────────────────────────────────────────────────

### POST /api/documents/bulk-upload/start
> Start a bulk upload job — uses `multipart/form-data`.

**Form Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `department_id` | int | ✅ | |
| `document_type_id` | int | ✅ | |
| `folder_id` | int | ❌ | If omitted, a folder is auto-created per file |
| `create_folder_per_file` | bool | ❌ | `true` to auto-create a folder for each file |
| `company_id` | int | ❌ | Applied to all auto-created folders |
| `confidentiality_level` | string | ❌ | |

**Response:**
```json
{ "success": true, "data": { "job_id": "abc123", "status": "started" } }
```

---

### POST /api/documents/bulk-upload/{job_id}/upload
> Upload a single file as part of a bulk job — `multipart/form-data`.

**Form Fields:** `file` (required)

---

### POST /api/documents/bulk-upload/{job_id}/progress
> Check the progress of a bulk upload job.

**Response:**
```json
{
  "success": true,
  "data": {
    "job_id": "abc123",
    "status": "running",
    "total_files": 10,
    "processed_files": 6,
    "failed_files": 0
  }
}
```

---

### POST /api/documents/bulk-upload/{job_id}/cancel
> Cancel a running bulk upload job.

---

### POST /api/documents/bulk-upload/jobs
> List all bulk upload jobs for the current user.

---

## ── Search ───────────────────────────────────────────────────────────────────

### POST /api/search
> Search documents with standard filters.

**Params:**
```json
{
  "query": "contract",
  "department_id": 1,
  "document_type_id": 2,
  "folder_id": 10,
  "company_id": 3,
  "limit": 20,
  "offset": 0
}
```

---

### POST /api/search/global
> Global search across documents, folders, and tags.

**Params:** `query` (required), `limit`, `offset`

---

### POST /api/search/barcode
> Search by barcode.

**Params:** `barcode` (required)

---

### POST /api/search/advanced
> Advanced search with detailed filters.

**Params:** `query`, `date_from`, `date_to`, `department_ids` (array), `document_type_ids` (array), `tags` (array), `status`, `confidentiality_level`

---

## ── Notes ────────────────────────────────────────────────────────────────────

### POST /api/notes
> List notes for a document or folder.

**Params:** `document_id` (optional), `folder_id` (optional), `limit`, `offset`

---

### POST /api/notes/create
> Create a note — plain HTTP (not JSON-RPC).

**Body:**
```json
{
  "content": "Note text here",
  "document_id": 100,
  "folder_id": null,
  "note_type": "general"
}
```

---

### POST /api/notes/{note_id}/update
> Update a note — plain HTTP.

**Body:** `{ "content": "Updated text" }`

---

### DELETE /api/notes/{note_id}
> Delete a note.

---

## ── Companies (Brands) ───────────────────────────────────────────────────────

### POST /api/companies
> List all companies / brands.

**Params:** `search`, `limit`

**Response:**
```json
{
  "result": {
    "success": true,
    "count": 5,
    "data": [
      {
        "id": 1,
        "name": "Nour Al-Nebras",
        "phone": "+9647800000000",
        "email": "info@nour.com",
        "vat": "1234567",
        "street": "Al-Rashid Street",
        "city": "Baghdad",
        "country_id": 106,
        "country_name": "Iraq"
      }
    ]
  }
}
```

---

### POST /api/companies/{company_id}
> Get a single company by ID.

---

### POST /api/companies/create
> Create a new company — plain HTTP (not JSON-RPC).

**Body:**
```json
{
  "name": "Nour Al-Nebras",
  "phone": "+9647800000000",
  "email": "info@nour.com",
  "vat": "1234567",
  "street": "Al-Rashid Street",
  "city": "Baghdad",
  "country_name": "Iraq"
}
```

> Use either `country_id` (int) OR `country_name` (string), not both.
> If `country_name` is provided and doesn't exist, it will be created automatically.

---

### POST /api/companies/{id}/update
> Update a company — plain HTTP.

**Body:** Any of the company fields above.

---

### DELETE /api/companies/{id}
> Delete a company (soft delete / archive).
>
> ⚠️ Returns `400` if the company has folders attached:
> ```json
> {
>   "success": false,
>   "code": "COMPANY_HAS_FOLDERS",
>   "folder_count": 5,
>   "message": "Cannot delete company with linked folders. Remove or reassign them first."
> }
> ```

---

### POST /api/companies/{id}/stats
> Get company statistics (folder count, document count, etc.)

---

### POST /api/countries
> List countries — useful for autocomplete dropdowns.

**Params:** `search: "iraq"`, `limit: 100`

**Response:**
```json
{
  "result": {
    "success": true,
    "count": 1,
    "data": [
      { "id": 106, "name": "Iraq", "code": "IQ", "phone_code": 964 }
    ]
  }
}
```

---

## ── Tags ─────────────────────────────────────────────────────────────────────

### POST /api/tags
> List all tags.

**Params:** `search`, `limit`

---

## ── Dashboard Stats ──────────────────────────────────────────────────────────

### POST /api/stats/dashboard
> Get aggregate dashboard statistics.

**Response:**
```json
{
  "result": {
    "success": true,
    "data": {
      "total_documents": 1500,
      "total_folders": 200,
      "total_departments": 10,
      "recent_uploads": [...],
      "documents_by_type": { "Contract": 300, "Invoice": 450 },
      "documents_by_department": { "Accounting": 500, "Legal": 200 }
    }
  }
}
```

---

## ── Audit Logs ───────────────────────────────────────────────────────────────

### POST /api/audit-logs
> Get the audit trail of operations.

**Params:** `document_id`, `user_id`, `action_type`, `date_from`, `date_to`, `limit`, `offset`

---

## ── Notifications ────────────────────────────────────────────────────────────

### POST /api/notifications
> List all notifications for the current user.

### POST /api/notifications/{id}/mark-read
> Mark a notification as read.

### POST /api/notifications/mark-all-read
> Mark all notifications as read.

### POST /api/notifications/unread-count
> Get the count of unread notifications.

**Response:** `{ "success": true, "data": { "count": 7 } }`

---

## ── Polling (Real-time Updates) ─────────────────────────────────────────────

### POST /api/ws/poll
> Long-polling endpoint for real-time notifications (WebSocket alternative).

**Params:** `last_id` — the last received notification ID

---

## ── Signatures ───────────────────────────────────────────────────────────────

### POST /api/signatures
> List signature requests.

### POST /api/signatures/create
**Params:** `document_id`, `signers: [user_id_1, user_id_2]`

### POST /api/signatures/{id}/approve
### POST /api/signatures/{id}/reject
### POST /api/signatures/{id}/upload-signed
> Upload the signed document after approval.

---

## ── Workflows ────────────────────────────────────────────────────────────────

### POST /api/workflows
> List all available workflows.

### POST /api/workflows/{id}/detail
> Get workflow details including stages and transitions.

---

## ── Templates ────────────────────────────────────────────────────────────────

### POST /api/templates
> List document templates.

### POST /api/templates/{template_id}/create-document
> Create a document from a template.

**Params:** `folder_id` (required), `name`

---

## ── User Management ──────────────────────────────────────────────────────────

### POST /api/users/managers
> List all users with manager role.

### POST /api/nbs/admin/users
> List all users — admin only.

### POST /api/nbs/admin/users/{user_id}/update
> Update user permissions — admin only.

---

## ── OCR ──────────────────────────────────────────────────────────────────────

### POST /api/ocr/test
> Test if OCR is available on the server.

### POST /api/ocr/run/{document_id}
> Run OCR on a document to extract text.

---

## ── Health ───────────────────────────────────────────────────────────────────

### GET /api/health
> Check API health — no authentication required.

**Response:** `{ "status": "ok", "timestamp": "2026-02-27T10:00:00" }`

---

## ═══════════════════════════════════════════════
## HTTP Status Codes Reference
## ═══════════════════════════════════════════════

| HTTP Status | Meaning |
|-------------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid data |
| `401` | Unauthorized — invalid or missing API Key / JWT Token |
| `403` | Forbidden — insufficient permissions |
| `404` | Record not found |
| `500` | Internal server error |

---

## ═══════════════════════════════════════════════
## Quick Start Code Examples
## ═══════════════════════════════════════════════

### POS API — Create and Confirm an Order

```javascript
const BASE = 'http://YOUR_SERVER_IP:8070';
const API_KEY = 'your_odoo_api_key';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json',
};

// Step 1: Bootstrap data
const setup = await fetch(`${BASE}/api/pos_perfume/v1/setup`, { headers })
  .then(r => r.json());

// Step 2: Create order
const order = await fetch(`${BASE}/api/pos_perfume/v1/orders`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    partner_id: 10,
    pricelist_id: setup.data.default_pricelist_id,
    invoice_type: '1',
    order_lines: [
      {
        product_id: 42,
        product_uom_id: 1,
        warehouse_id: 1,
        quantity: 2,
        unit_price: 25.0,
        discount_percent: 0,
      }
    ]
  })
}).then(r => r.json());

// Step 3: Confirm → creates sale.order + syncs to SAP
const confirmed = await fetch(
  `${BASE}/api/pos_perfume/v1/orders/${order.data.id}/confirm`,
  { method: 'POST', headers }
).then(r => r.json());

console.log('SAP Doc Number:', confirmed.data.sap_doc_num);
```

---

### Archive API — Login and Upload a Document

```javascript
const BASE = 'http://YOUR_SERVER_IP:8070';

// Step 1: Login
const auth = await fetch(`${BASE}/api/auth/login`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'admin',
    password: 'admin',
    database: 'lugal_local'
  })
}).then(r => r.json());

const TOKEN = auth.access_token;

// Step 2: Upload a document
const formData = new FormData();
formData.append('file', myFile);         // File object
formData.append('folder_id', '10');
formData.append('name', 'Lease Contract 2026');
formData.append('confidentiality_level', 'internal');

const uploaded = await fetch(`${BASE}/api/documents/upload`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${TOKEN}` },
  body: formData
}).then(r => r.json());

// Step 3: Download a document
const blob = await fetch(`${BASE}/api/documents/${uploaded.data.id}/download`, {
  headers: { 'Authorization': `Bearer ${TOKEN}` }
}).then(r => r.blob());

const url = URL.createObjectURL(blob);
window.open(url);
```

---

### Archive API — Reusable JSON-RPC Helper

```javascript
// Reusable helper for all JSON-RPC Archive endpoints
async function archivePost(route, params = {}) {
  const response = await fetch(`http://YOUR_SERVER_IP:8070${route}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${TOKEN}`,
    },
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      id: Date.now(),
      params: {
        db: 'lugal_local',
        ...params
      }
    })
  });
  const json = await response.json();
  return json.result; // { success, data, total, ... }
}

// Usage examples
const folders   = await archivePost('/api/folders', { department_id: 1, limit: 50 });
const documents = await archivePost('/api/documents', { folder_id: 10 });
const results   = await archivePost('/api/search/global', { query: 'contract' });
const companies = await archivePost('/api/companies', { search: 'nour' });
```

---

*Last updated: 2026-02-27 — Generated from source code*
