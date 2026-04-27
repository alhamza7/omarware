# POS Perfume API — Reference
### For the Frontend Developer

---

## 🔌 Server Info

| Item | Value |
|------|-------|
| **Base URL** | `http://YOUR_SERVER_IP:8070` |
| **Database Name** | `lugal_local` |
| **API Prefix** | `/api/pos_perfume/v1` |

---

## 🔐 Authentication

The POS API supports **two methods**:

---

### Method 1 — Login with Username & Password ✅ Recommended

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

After login the browser automatically attaches the session cookie to every request.
For non-browser clients (mobile, React Native) pass it manually:

```
Cookie: session_id=abc123xyz...
```

**JavaScript example:**
```javascript
const BASE = 'http://YOUR_SERVER_IP:8070';

async function login(username, password) {
  const res = await fetch(`${BASE}/web/session/authenticate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify({
      jsonrpc: '2.0',
      method: 'call',
      id: 1,
      params: { db: 'lugal_local', login: username, password }
    })
  });

  const data = await res.json();
  if (!data.result?.uid) throw new Error('Login failed');
  // session cookie is now set — or store data.result.session_id for mobile
  return data.result;
}
```

---

### Method 2 — API Key (Bearer Token)

Suitable for server-to-server or when cookies are not an option.

```
Authorization: Bearer <ODOO_API_KEY>
Content-Type: application/json
```

**How to generate a key:**
Go to Odoo → Settings → Technical → API Keys → New — copy the key, it will not be shown again.

---

### Auth Summary

| | Method | Best for |
|-|--------|----------|
| ✅ | `POST /web/session/authenticate` → cookie | Browser / web apps |
| ✅ | `Authorization: Bearer <key>` | Mobile / server apps |

---

## 📦 Standard Response Envelope

Every endpoint returns the same shape:

**Success:**
```json
{ "success": true, "message": "OK", "data": { ... } }
```

**Error:**
```json
{ "success": false, "error": "Descriptive error message" }
```

---

## ─────────────────────────────────────────────
## 1. Setup & Session
## ─────────────────────────────────────────────

### GET /api/pos_perfume/v1/setup
> Single bootstrap call — returns everything needed to initialize the POS.

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
> Current authenticated user info + default exchange rate.

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
> Get the current global exchange rate.

```json
{ "success": true, "data": { "exchange_rate": 1470.0 } }
```

---

### PUT /api/pos_perfume/v1/settings
> Update the global exchange rate.

**Body:** `{ "exchange_rate": 1480.0 }`

---

### GET /api/pos_perfume/v1/pricelists
> All active pricelists.

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
> All active warehouses.

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

## ─────────────────────────────────────────────
## 2. Products
## ─────────────────────────────────────────────

### GET /api/pos_perfume/v1/products
> Search and list products.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | `""` | Searches name, internal code, and foreign name |
| `pricelist_id` | int | — | Prices calculated against this pricelist |
| `limit` | int | `80` | Results per page |
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
> Single product with full details — all UoMs with prices + stock per warehouse.

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
> Same as `GET /products/{id}` but via POST body.

**Body:**
```json
{ "product_id": 42, "pricelist_id": 1, "uom_id": 5 }
```

**Response:** Same as above.

---

### POST /api/pos_perfume/v1/products/uom_price
> Get the price for a specific unit of measure — call this when the user changes the UoM on a line.

**Body:**
```json
{ "product_id": 42, "pricelist_id": 1, "uom_id": 5 }
```

**Response:**
```json
{ "success": true, "data": { "price_unit": 12.0 } }
```

---

## ─────────────────────────────────────────────
## 2.1 Units of Measure (UoMs) — Deep Dive
## ─────────────────────────────────────────────

> This is one of the most important features of the POS Perfume system.
> Every product can be sold in **multiple units** (e.g. Unit, Tola, Carton),
> each with its **own price** defined in the pricelist.

---

### How the UoM System Works

```
Product "Royal Oud"
    │
    ├── SAP UoM Group: "Perfume-Group-01"
    │       ├── Unit    → price: $25.00   (base unit)
    │       ├── Tola    → price: $12.00   (sub-unit — smaller)
    │       └── Carton  → price: $250.00  (bulk unit — larger)
    │
    └── Stock per Warehouse (from SAP sync):
            ├── Main Warehouse  → 80 units available
            └── Warehouse 2     → 20 units available
```

**Two sources for UoM prices:**

| Source | When used |
|--------|-----------|
| **SAP UoM Group** | If the product has a linked SAP UoM Group → only those UoMs are returned |
| **Pricelist items** | If no SAP UoM Group → all pricelist entries for that product are used |

> If NO pricelist is passed to the API → only the base UoM with `list_price` is returned.

---

### Product Fields — Full Reference

The `GET /products/{id}` and `POST /products/data` responses contain:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Odoo product.product ID |
| `name` | string | Arabic product name |
| `default_code` | string | SAP internal code / barcode reference |
| `foreign_name` | string | English / secondary name |
| `uom_id` | object | **Base unit** `{ id, name }` — the default UoM |
| `list_price` | float | Base price before pricelist |
| `qty_available` | float | Total available stock (all warehouses combined) |
| `available_uoms` | array | **All sellable UoMs with prices** (see below) |
| `warehouses` | array | **Stock per warehouse** (see below) |
| `color_class` | string | Visual badge color: `gold` / `silver` / `bronze` / `default` |
| `badge_text` | string | Badge label: `VIP` / `A` / `B` / etc. — derived from SAP product code prefix |
| `categ_id` | object | Product category `{ id, name }` |

---

### `available_uoms` — Array Structure

Each item in `available_uoms`:

```json
{ "id": 5, "name": "Tola", "price": 12.0 }
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | `uom.uom` Odoo ID — **use this as `product_uom_id` when creating an order line** |
| `name` | string | Unit name to display in UI |
| `price` | float | Price in USD for this unit (from pricelist) |

> ⚠️ Always use `available_uoms[i].id` as the `product_uom_id` in order lines.
> Never hardcode UoM IDs — they vary per environment.

---

### `warehouses` — Array Structure

Each item in `warehouses`:

```json
{ "id": 1, "name": "Main Warehouse", "code": "WH", "quantity": 80.0 }
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | `stock.warehouse` Odoo ID — **use this as `warehouse_id` in order lines** |
| `name` | string | Warehouse display name |
| `code` | string | Short code (SAP warehouse code if available, else Odoo code) |
| `quantity` | float | Available quantity (from SAP sync → fallback to Odoo stock) |

> ⚠️ Only warehouses with `quantity > 0` are returned.
> If a product has no stock anywhere, `warehouses` will be an empty array `[]`.

---

### Complete UoM Flow — Step by Step

**Step 1: User opens product selector**
```
GET /api/pos_perfume/v1/products?query=oud&pricelist_id=1
→ Returns list with basic info (no UoMs yet — for performance)
```

**Step 2: User selects a product**
```
GET /api/pos_perfume/v1/products/42?pricelist_id=1
→ Returns full product with available_uoms and warehouses
→ Pre-select: available_uoms[0] as default UoM
→ Pre-select: warehouses[0] as default warehouse
→ Pre-fill: price = available_uoms[0].price
```

**Step 3: User changes the UoM (e.g. switches from Unit → Tola)**
```
POST /api/pos_perfume/v1/products/uom_price
Body: { "product_id": 42, "pricelist_id": 1, "uom_id": 5 }
→ Returns: { "price_unit": 12.0 }
→ Update the price field in the UI with this new price
```

**Step 4: User confirms and adds the line to the order**
```
order_lines: [{
  "product_id":      42,   ← from product.id
  "product_uom_id":  5,    ← from the selected available_uoms[i].id
  "warehouse_id":    1,    ← from the selected warehouses[i].id
  "quantity":        3.0,
  "unit_price":      12.0, ← from uom_price response
  "discount_percent": 0.0,
  "custom_product_name": ""
}]
```

---

### `custom_product_name` Field

Used when the salesperson wants to override the displayed product name on the invoice (e.g. a custom blend or special label).

| Value | Behavior |
|-------|----------|
| `""` or `null` | Use the actual product name |
| `"Special Blend #5"` | This text appears instead of product name on the printed invoice and SAP order |

---

### `color_class` and `badge_text` — Visual Badges

These are **UI-only fields** derived automatically from the SAP product code prefix.

| `color_class` | `badge_text` | Meaning |
|---------------|--------------|---------|
| `gold` | `VIP` | Premium product |
| `silver` | `A` | Grade A |
| `bronze` | `B` | Grade B |
| `default` | `—` | Standard |

> Use `color_class` to style the product card border/background.
> Use `badge_text` as a label overlay on the product image.

---

### `location_id` — Auto-set, Optionally Overridable

When you send `warehouse_id` in an order line, the system automatically assigns `location_id` to the main stock location of that warehouse (`warehouse.lot_stock_id`).

You can override it explicitly:
```json
{
  "product_id": 42,
  "warehouse_id": 1,
  "location_id": 8,   ← explicit location inside the warehouse
  ...
}
```

> Most of the time you do NOT need to set `location_id` — let it auto-set.

---

### `sequence` — Line Ordering

Controls the display order of lines in the order and on the printed invoice.

```json
{ "product_id": 42, ..., "sequence": 10 }
```

Default is `10`. Lines are sorted ascending by `sequence`.

---

### Order Line — Full Response Object

```json
{
  "id": 456,
  "sequence": 10,
  "product_id": {
    "id": 42,
    "name": "Royal Oud",
    "default_code": "OUD-001",
    "foreign_name": "Royal Oud"
  },
  "product_uom_id": { "id": 5, "name": "Tola" },
  "warehouse_id":   { "id": 1, "name": "Main Warehouse", "code": "WH" },
  "location_id":    { "id": 8, "name": "Stock" },
  "quantity": 3.0,
  "unit_price": 12.0,
  "discount_percent": 10.0,
  "price_after_discount": 10.8,
  "discount_amount": 1.2,
  "line_subtotal": 36.0,
  "line_total": 32.4,
  "available_qty": 80.0,
  "custom_product_name": ""
}
```

**Line calculation fields:**

| Field | Formula |
|-------|---------|
| `price_after_discount` | `unit_price × (1 - discount_percent / 100)` |
| `discount_amount` | `unit_price × (discount_percent / 100)` |
| `line_subtotal` | `unit_price × quantity` |
| `line_total` | `price_after_discount × quantity` |
| `available_qty` | Stock available at time of line creation |

---

## ─────────────────────────────────────────────
## 3. Customers
## ─────────────────────────────────────────────

### GET /api/pos_perfume/v1/customers
> Search and list customers.

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

> `name` is required. All other fields are optional.

**Response:** `{ "success": true, "data": { ...customer object... } }`

---

### GET /api/pos_perfume/v1/customers/{customer_id}
> Get a single customer by ID.

---

### PUT /api/pos_perfume/v1/customers/{customer_id}
> Update a customer.

**Body:** Any of `name, phone, mobile, email, street, city, ref, country_id`

---

## ─────────────────────────────────────────────
## 4. Orders
## ─────────────────────────────────────────────

### Order States

| State | Description |
|-------|-------------|
| `draft` | Draft — editable |
| `quotation` | Sent as quotation |
| `sale` | Confirmed — `sale.order` created and synced to SAP |
| `done` | Completed |
| `cancel` | Cancelled |

---

### Full Order Object

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
  "sale_order_id": { "id": 55, "name": "S00055", "state": "sale" },
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

---

### GET /api/pos_perfume/v1/orders
> List orders with optional filters.
> ⚠️ List response does **not** include `order_lines` — use `GET /orders/{id}` for the full object.

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

---

### GET /api/pos_perfume/v1/orders/{order_id}
> Full order details including all lines.

**Response:** Full Order Object (see above)

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

> `partner_id` is required. `order_lines` is optional — lines can be added later via the lines endpoint.
> If `pricelist_id` is omitted the system default is used.

**Response:** Full Order Object

---

### PUT /api/pos_perfume/v1/orders/{order_id}
> Update the order header (not lines).
> ⚠️ Only allowed when state is `draft` or `quotation`.

**Body:** Any of `partner_id, pricelist_id, note, invoice_type, exchange_rate, user_id`

---

### DELETE /api/pos_perfume/v1/orders/{order_id}
> Cancel the order (soft cancel — state becomes `cancel`).
> ⚠️ Not allowed on `done` orders.

---

## ─────────────────────────────────────────────
## 5. Order Lines
## ─────────────────────────────────────────────

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
> Remove a line from the order.

---

## ─────────────────────────────────────────────
## 6. Order Actions
## ─────────────────────────────────────────────

### POST /api/pos_perfume/v1/orders/{order_id}/confirm
> **Confirm the order** → creates a `sale.order` in Odoo and automatically syncs to SAP.

> Requirements: order must have at least one line and must not be in `done` or `cancel` state.

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
> Set order state to `quotation`.

---

### POST /api/pos_perfume/v1/orders/{order_id}/cancel
> Cancel the order.

---

### POST /api/pos_perfume/v1/orders/{order_id}/draft
> Reset a cancelled order back to `draft`.

---

### POST /api/pos_perfume/v1/orders/{order_id}/sync_sap
> Force re-sync the order to SAP.
> Order must already be confirmed (must have a `sale_order_id`).

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

**Query Parameters:** `download=true` (default) or `download=false` (open inline in browser)

**Response:** Binary PDF — `Content-Type: application/pdf`

> If `wkhtmltopdf` is not installed:
> ```json
> { "success": true, "data": { "pdf_available": false, "setup_required": "sudo apt-get install wkhtmltopdf" } }
> ```

---

### POST /api/pos_perfume/v1/orders/{order_id}/send_whatsapp
> Send the invoice as a WhatsApp text message (requires ULTRAMSG configured in Odoo).

**Success Response:**
```json
{ "success": true, "data": { "sent": true, "message_id": "MSG123" } }
```

**When not configured:**
```json
{ "success": true, "data": { "sent": false, "available": false, "setup_required": "..." } }
```

---

### POST /api/pos_perfume/v1/orders/{order_id}/send_whatsapp_image
> Send the invoice as a WhatsApp image (requires `wkhtmltoimage` + ULTRAMSG).

---

### PUT /api/pos_perfume/v1/orders/{order_id}/exchange_rate
> Update the IQD exchange rate on a specific order.

**Body:** `{ "exchange_rate": 1490.0 }` — send `{}` to reset to the current system default.

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

## ─────────────────────────────────────────────
## HTTP Status Codes
## ─────────────────────────────────────────────

| Status | Meaning |
|--------|---------|
| `200` | Success |
| `400` | Bad request — missing or invalid data |
| `401` | Unauthorized — invalid or missing credentials |
| `403` | Forbidden — insufficient permissions |
| `404` | Record not found |
| `500` | Internal server error |

---

## ─────────────────────────────────────────────
## Quick Start — Full Flow Example
## ─────────────────────────────────────────────

```javascript
const BASE = 'http://YOUR_SERVER_IP:8070';

// ── 1. Login ───────────────────────────────────────────────────────────────
const auth = await fetch(`${BASE}/web/session/authenticate`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({
    jsonrpc: '2.0', method: 'call', id: 1,
    params: { db: 'lugal_local', login: 'admin', password: 'admin' }
  })
}).then(r => r.json());

if (!auth.result?.uid) throw new Error('Login failed');

const SESSION = auth.result.session_id; // store for non-browser clients

const headers = {
  'Content-Type': 'application/json',
  'Cookie': `session_id=${SESSION}`,   // omit this line for browser apps (auto)
};

// ── 2. Bootstrap data ─────────────────────────────────────────────────────
const setup = await fetch(`${BASE}/api/pos_perfume/v1/setup`, { headers })
  .then(r => r.json());

const defaultPricelist = setup.data.default_pricelist_id;
const warehouses       = setup.data.warehouses;
const invoiceTypes     = setup.data.invoice_types;

// ── 3. Search products ────────────────────────────────────────────────────
const products = await fetch(
  `${BASE}/api/pos_perfume/v1/products?query=oud&pricelist_id=${defaultPricelist}`,
  { headers }
).then(r => r.json());

// ── 4. Get product details + UoM prices ───────────────────────────────────
const product = await fetch(
  `${BASE}/api/pos_perfume/v1/products/42?pricelist_id=${defaultPricelist}`,
  { headers }
).then(r => r.json());

// ── 5. Create order ───────────────────────────────────────────────────────
const order = await fetch(`${BASE}/api/pos_perfume/v1/orders`, {
  method: 'POST',
  headers,
  body: JSON.stringify({
    partner_id: 10,
    pricelist_id: defaultPricelist,
    invoice_type: '1',
    order_lines: [
      {
        product_id: 42,
        product_uom_id: 1,
        warehouse_id: warehouses[0].id,
        quantity: 2,
        unit_price: 25.0,
        discount_percent: 0,
      }
    ]
  })
}).then(r => r.json());

// ── 6. Confirm order → creates sale.order + SAP sync ─────────────────────
const confirmed = await fetch(
  `${BASE}/api/pos_perfume/v1/orders/${order.data.id}/confirm`,
  { method: 'POST', headers }
).then(r => r.json());

console.log('Order name:   ', confirmed.data.name);
console.log('SAP Doc Num:  ', confirmed.data.sap_doc_num);
console.log('SAP Synced:   ', confirmed.data.sap_synced);

// ── 7. Download PDF ───────────────────────────────────────────────────────
window.open(
  `${BASE}/api/pos_perfume/v1/orders/${order.data.id}/report?download=true`
);
```

---

*Last updated: 2026-02-27 — Generated from source code*
