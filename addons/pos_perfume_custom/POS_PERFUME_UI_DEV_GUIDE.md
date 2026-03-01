# POS Perfume — Frontend Developer Guide

> **Server IP:** `192.168.116.15`  
> **Port:** `8070`  
> **Base URL:** `http://192.168.116.15:8070/api/pos_perfume/v1`  
> **Last updated:** February 2026

---

## Table of Contents

1. [Quick Start](#1-quick-start)
2. [Authentication](#2-authentication)
3. [Standard Response Format](#3-standard-response-format)
4. [Bootstrap — Load Everything at Once](#4-bootstrap)
5. [Customers](#5-customers)
6. [Products](#6-products)
7. [Orders](#7-orders)
8. [Order Lines](#8-order-lines)
9. [Order Actions](#9-order-actions)
10. [WhatsApp](#10-whatsapp)
11. [PDF Report](#11-pdf-report)
12. [SAP Sync](#12-sap-sync)
13. [Settings & Exchange Rate](#13-settings--exchange-rate)
14. [Complete UI Flow](#14-complete-ui-flow)
15. [Data Models Reference](#15-data-models-reference)
16. [Error Handling](#16-error-handling)
17. [API Service Layer (TypeScript)](#17-api-service-layer-typescript)

---

## 1. Quick Start

```bash
# Test the server is reachable
curl http://192.168.116.15:8070/web/health

# Get an API key
# Odoo → Settings → Users → (your user) → API Keys tab → New
```

### Get your API key in 3 steps
1. Open browser → `http://192.168.116.15:8070`
2. Login → Settings → Users & Companies → Users → click your user
3. Tab **"API Keys"** → **New** → give it a name → copy the key

> **Keep the key safe — it is shown only once.**

---

## 2. Authentication

Every request **must** include one of:

### Option A — API Key (Recommended for external apps)

```http
Authorization: Bearer YOUR_API_KEY_HERE
```

### Option B — Session Cookie (Browser SPA)

First login:
```http
POST http://192.168.116.15:8070/web/session/authenticate
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "db": "lugal_local",
    "login": "admin",
    "password": "admin"
  }
}
```
The server sets a `session_id` cookie. Include it in all subsequent requests.

### JavaScript/TypeScript helper

```typescript
const BASE_URL = 'http://192.168.116.15:8070/api/pos_perfume/v1';
const API_KEY  = 'your_api_key_here'; // store in env variable

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json',
};

async function apiCall<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  path: string,
  body?: object,
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const json = await res.json();
  if (!json.success) throw new Error(json.error);
  return json.data as T;
}
```

---

## 3. Standard Response Format

**Every endpoint** returns the same envelope:

```jsonc
// Success
{
  "success": true,
  "message": "OK",
  "data": { ... }
}

// Error
{
  "success": false,
  "error": "Description of what went wrong"
}
```

| HTTP Status | Meaning |
|---|---|
| `200` | Success (also used for "feature not available" with `available: false`) |
| `400` | Bad request — missing/invalid field |
| `401` | Authentication required |
| `404` | Record not found |
| `500` | Server error |

---

## 4. Bootstrap

Load **all static data** in a single call when the app starts.

```http
GET /setup
```

### Response
```jsonc
{
  "success": true,
  "data": {
    "pricelists": [
      { "id": 1, "name": "Price list 1", "currency_id": 3 }
    ],
    "default_pricelist_id": 1,
    "warehouses": [
      { "id": 1, "name": "WH", "code": "WH" }
    ],
    "users": [
      { "id": 3, "name": "Administrator" }
    ],
    "invoice_types": [
      { "key": "1", "label": "زبون محل" },
      { "key": "2", "label": "شركات توصيل" },
      { "key": "3", "label": "نقليات" },
      { "key": "4", "label": "ديلفري" },
      { "key": "5", "label": "NBS" },
      { "key": "6", "label": "شورجة" },
      { "key": "7", "label": "NA" },
      { "key": "8", "label": "مكاتب الشورجة" }
    ],
    "exchange_rate": 1470.0,
    "currency": "USD",
    "secondary_currency": "IQD"
  }
}
```

### Usage
```typescript
// Call once on app load — cache the result
const setup = await apiCall('GET', '/setup');
const warehouses    = setup.warehouses;
const invoiceTypes  = setup.invoice_types;
const exchangeRate  = setup.exchange_rate;
```

---

## 5. Customers

### 5.1 List / Search Customers

```http
GET /customers?query=Ahmed&limit=50&offset=0
```

| Param | Type | Description |
|---|---|---|
| `query` | string | Search by name, phone, or ref |
| `limit` | int | Default: 50 |
| `offset` | int | Default: 0 (for pagination) |

**Response:**
```jsonc
{
  "data": {
    "total": 120,
    "offset": 0,
    "limit": 50,
    "items": [
      {
        "id": 42,
        "name": "Ahmed Al-Rashid",
        "ref": "C001",
        "phone": "+964 771 234 5678",
        "mobile": "+964 781 234 5678",
        "email": "ahmed@example.com",
        "street": "Al-Mansour St",
        "city": "Baghdad",
        "country_id": { "id": 103, "name": "Iraq" },
        "pricelist_id": { "id": 1, "name": "Price list 1" }
      }
    ]
  }
}
```

### 5.2 Get Single Customer

```http
GET /customers/42
```

### 5.3 Create Customer

```http
POST /customers
Content-Type: application/json

{
  "name": "Ahmed Al-Rashid",
  "phone": "+964 771 234 5678",
  "mobile": "+964 781 234 5678",
  "email": "ahmed@example.com",
  "street": "Al-Mansour St",
  "city": "Baghdad",
  "ref": "C001",
  "country_id": 103
}
```

> Only `name` is required. All other fields are optional.

### 5.4 Update Customer

```http
PUT /customers/42
Content-Type: application/json

{
  "phone": "+964 771 999 9999",
  "mobile": "+964 781 999 9999"
}
```

> Send only the fields you want to update.

---

## 6. Products

### 6.1 List / Search Products

```http
GET /products?query=oud&limit=80&offset=0
```

| Param | Type | Description |
|---|---|---|
| `query` | string | Search by name, code, or foreign name |
| `limit` | int | Default: 80 |
| `offset` | int | Default: 0 |
| `pricelist_id` | int | Optional — filter prices |

**Response:**
```jsonc
{
  "data": {
    "total": 350,
    "items": [
      {
        "id": 12,
        "name": "Oud Al-Shams",
        "default_code": "OUD-001",
        "foreign_name": "عود الشمس",
        "uom_id": { "id": 1, "name": "pcs" },
        "list_price": 25.0,
        "qty_available": 150.0,
        "color_class": "red",
        "badge_text": "HOT",
        "active": true,
        "sale_ok": true,
        "categ_id": { "id": 5, "name": "Perfumes" }
      }
    ]
  }
}
```

### 6.2 Get Full Product Data (UoMs + Prices + Stock per Warehouse)

Call this when the user **selects a product** to add to an order.

```http
POST /products/data
Content-Type: application/json

{
  "product_id": 12,
  "pricelist_id": 1
}
```

**Response:**
```jsonc
{
  "data": {
    "product_id": 12,
    "product_name": "Oud Al-Shams",
    "product_uom_id": 1,
    "product_uom_name": "pcs",
    "price_unit": 25.0,
    "available_qty": 150.0,
    "default_code": "OUD-001",
    "foreign_name": "عود الشمس",
    "color_class": "red",
    "badge_text": "HOT",
    "available_uoms": [
      { "id": 1,  "name": "pcs",   "price": 25.0 },
      { "id": 5,  "name": "dozen", "price": 280.0 },
      { "id": 8,  "name": "box",   "price": 600.0 }
    ],
    "warehouses": [
      { "id": 1, "name": "Main Warehouse", "code": "WH",  "qty": 120.0 },
      { "id": 2, "name": "Branch",         "code": "BR",  "qty": 30.0 }
    ]
  }
}
```

> **Use `available_uoms`** to populate the UoM dropdown when adding a line.  
> **Use `warehouses`** to show stock per location and let user pick a warehouse.

### 6.3 Get Price for a Specific UoM

Call this when user **changes the UoM** on an order line.

```http
POST /products/uom_price
Content-Type: application/json

{
  "product_id": 12,
  "pricelist_id": 1,
  "uom_id": 5
}
```

**Response:** `{ "data": { "price_unit": 280.0 } }`

### 6.4 Get Single Product

```http
GET /products/12?pricelist_id=1
```

Returns the same structure as `/products/data` including `available_uoms` and `warehouses`.

---

## 7. Orders

### 7.1 List Orders

```http
GET /orders?state=sale&limit=20&offset=0
```

| Param | Type | Description |
|---|---|---|
| `query` | string | Search by order name (e.g. `S00042`) |
| `state` | string | `draft` \| `quotation` \| `sale` \| `done` \| `cancel` |
| `partner_id` | int | Filter by customer ID |
| `user_id` | int | Filter by salesperson ID |
| `date_from` | string | `YYYY-MM-DD` |
| `date_to` | string | `YYYY-MM-DD` |
| `sap_synced` | string | `true` \| `false` |
| `limit` | int | Default: 50 |
| `offset` | int | Default: 0 |

**Response (lightweight — no order lines):**
```jsonc
{
  "data": {
    "total": 210,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 101,
        "name": "S00042",
        "date": "2026-02-25T10:30:00",
        "state": "sale",
        "partner_id": 42,
        "partner_name": "Ahmed Al-Rashid",
        "user_id": 3,
        "user_name": "Administrator",
        "invoice_type": "1",
        "amount_total": 250.0,
        "amount_total_iqd": 367500.0,
        "sap_synced": true,
        "sap_doc_num": "SAP-12345",
        "note": ""
      }
    ]
  }
}
```

### 7.2 Get Single Order (Full Details)

```http
GET /orders/101
```

**Response (full — includes all lines):**
```jsonc
{
  "data": {
    "id": 101,
    "name": "S00042",
    "date": "2026-02-25T10:30:00",
    "state": "sale",
    "user_id": { "id": 3, "name": "Administrator" },
    "partner_id": {
      "id": 42,
      "name": "Ahmed Al-Rashid",
      "phone": "+964 771 234 5678",
      "mobile": "+964 781 234 5678",
      "email": "ahmed@example.com"
    },
    "pricelist_id": { "id": 1, "name": "Price list 1" },
    "currency_id": { "id": 3, "name": "USD" },
    "exchange_rate": 1470.0,
    "amount_subtotal": 260.0,
    "amount_discount": 10.0,
    "amount_tax": 0.0,
    "amount_total": 250.0,
    "amount_total_iqd": 367500.0,
    "invoice_type": "1",
    "note": "Handle with care",
    "sale_order_id": { "id": 55, "name": "S00055", "state": "sale" },
    "sap_doc_num": "SAP-12345",
    "sap_doc_entry": 123,
    "sap_synced": true,
    "sap_error_message": "",
    "sap_last_sync_date": "2026-02-25T10:31:00",
    "order_lines": [
      {
        "id": 201,
        "sequence": 10,
        "product_id": {
          "id": 12,
          "name": "Oud Al-Shams",
          "default_code": "OUD-001",
          "foreign_name": "عود الشمس"
        },
        "product_uom_id": { "id": 1, "name": "pcs" },
        "warehouse_id": { "id": 1, "name": "Main Warehouse", "code": "WH" },
        "location_id": { "id": 8, "name": "WH/Stock" },
        "quantity": 10.0,
        "unit_price": 26.0,
        "discount_percent": 0.0,
        "price_after_discount": 26.0,
        "line_subtotal": 260.0,
        "discount_amount": 0.0,
        "line_total": 260.0,
        "available_qty": 150.0,
        "custom_product_name": ""
      }
    ]
  }
}
```

### 7.3 Create Order

```http
POST /orders
Content-Type: application/json

{
  "partner_id": 42,
  "pricelist_id": 1,
  "invoice_type": "1",
  "note": "Handle with care",
  "exchange_rate": 1470.0,
  "user_id": 3,
  "order_lines": [
    {
      "product_id": 12,
      "product_uom_id": 1,
      "warehouse_id": 1,
      "quantity": 10.0,
      "unit_price": 26.0,
      "discount_percent": 0.0,
      "custom_product_name": ""
    }
  ]
}
```

> - `partner_id` is the **only required** field.
> - `pricelist_id` defaults to system default if omitted.
> - `order_lines` is optional — you can add lines later via `/orders/:id/lines`.

**Response:** Full order object (same as GET /orders/:id).

### 7.4 Update Order Header

```http
PUT /orders/101
Content-Type: application/json

{
  "partner_id": 42,
  "pricelist_id": 1,
  "note": "Updated note",
  "invoice_type": "3",
  "exchange_rate": 1480.0,
  "user_id": 3
}
```

> Only allowed when state is `draft` or `quotation`.  
> Send only the fields you want to change.

### 7.5 Cancel Order (Soft Delete)

```http
DELETE /orders/101
```

Sets state to `cancel`. **Cannot be called on `done` orders.**

---

## 8. Order Lines

### 8.1 Add a Line

```http
POST /orders/101/lines
Content-Type: application/json

{
  "product_id": 12,
  "product_uom_id": 1,
  "warehouse_id": 1,
  "quantity": 5.0,
  "unit_price": 25.0,
  "discount_percent": 10.0,
  "custom_product_name": "Special Oud"
}
```

| Field | Required | Description |
|---|---|---|
| `product_id` | ✅ | Product ID |
| `warehouse_id` | ✅ | Warehouse ID |
| `product_uom_id` | ❌ | Defaults to product's base UoM |
| `quantity` | ❌ | Default: 1.0 |
| `unit_price` | ❌ | Default: product list price |
| `discount_percent` | ❌ | Default: 0.0 (0–100) |
| `custom_product_name` | ❌ | Override name on invoice/report |

**Response:** Single line object.

### 8.2 Update a Line

```http
PUT /orders/101/lines/201
Content-Type: application/json

{
  "quantity": 8.0,
  "discount_percent": 15.0,
  "custom_product_name": "Premium Oud"
}
```

> Send only the fields you want to change.  
> Can also update `product_id`, `product_uom_id`, `warehouse_id`, `location_id`, `sequence`.

### 8.3 Delete a Line

```http
DELETE /orders/101/lines/201
```

**Response:** `{ "deleted": true, "line_id": 201 }`

---

## 9. Order Actions

### Order State Machine

```
draft ──→ quotation ──→ sale ──→ done
  │           │            │
  └───────────┴────────────┴──→ cancel ──→ draft (reset)
```

| State | Description | Allowed Actions |
|---|---|---|
| `draft` | New order | Edit header, add/edit/delete lines, confirm, set quotation, cancel |
| `quotation` | Sent to customer | Edit header, add/edit/delete lines, confirm, cancel |
| `sale` | Confirmed sale order | View only, cancel |
| `done` | Completed | View only — **no actions** |
| `cancel` | Cancelled | Reset to draft only |

### 9.1 Confirm Order

Creates/updates the linked `sale.order` and triggers SAP sync.

```http
POST /orders/101/confirm
```

**Response:**
```jsonc
{
  "data": {
    "id": 101,
    "name": "S00042",
    "state": "sale",
    "sale_order_id": { "id": 55, "name": "S00055", "state": "sale" },
    "sap_synced": true,
    "sap_doc_num": "SAP-12345",
    "sap_doc_entry": 123,
    "sap_error_message": ""
  }
}
```

> If `sap_error_message` is not empty → SAP sync failed, but the POS order was confirmed.

### 9.2 Set to Quotation

```http
POST /orders/101/quotation
```

**Response:** `{ "id": 101, "state": "quotation" }`

### 9.3 Cancel Order

```http
POST /orders/101/cancel
```

**Response:** `{ "id": 101, "state": "cancel" }`

### 9.4 Reset to Draft

```http
POST /orders/101/draft
```

**Response:** `{ "id": 101, "state": "draft" }`

---

## 10. WhatsApp

### 10.1 Send Text Message

```http
POST /orders/101/send_whatsapp
```

**Response when ULTRAMSG is configured:**
```jsonc
{ "data": { "sent": true, "message_id": "msg_abc123" } }
```

**Response when ULTRAMSG is NOT configured:**
```jsonc
{
  "success": true,
  "message": "WhatsApp feature not configured",
  "data": {
    "sent": false,
    "available": false,
    "setup_required": "Configure ULTRAMSG in Odoo: Settings → Technical → ULTRAMSG Config → New"
  }
}
```

### 10.2 Send Invoice Image

```http
POST /orders/101/send_whatsapp_image
```

Same response pattern as above.  
Requires `wkhtmltopdf` to be installed on the server.

### Frontend handling

```typescript
const result = await apiCall('POST', `/orders/${orderId}/send_whatsapp`);

if (result.sent) {
  showSuccess('WhatsApp message sent!');
} else if (result.available === false) {
  showInfo('WhatsApp not configured on server. Contact admin.');
} else {
  showError('Failed to send');
}
```

---

## 11. PDF Report

```http
GET /orders/101/report
GET /orders/101/report?download=false   ← inline view in browser
```

**When wkhtmltopdf is installed:** Returns the PDF binary directly (`Content-Type: application/pdf`).

**When wkhtmltopdf is NOT installed:**
```jsonc
{
  "success": true,
  "data": { "pdf_available": false, "setup_required": "sudo apt-get install wkhtmltopdf" }
}
```

### Open PDF in new tab

```typescript
const pdfUrl = `${BASE_URL}/orders/${orderId}/report?download=false`;
const headers = { Authorization: `Bearer ${API_KEY}` };

// Method: fetch blob and open
const response = await fetch(pdfUrl, { headers });
const contentType = response.headers.get('content-type') || '';

if (contentType.includes('application/pdf')) {
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, '_blank');
} else {
  const json = await response.json();
  if (!json.data.pdf_available) {
    alert('PDF not available — server missing wkhtmltopdf');
  }
}
```

---

## 12. SAP Sync

Force re-sync an order to SAP (use after confirm or when sync failed):

```http
POST /orders/101/sync_sap
```

**Response:**
```jsonc
{
  "data": {
    "sap_synced": true,
    "sap_doc_num": "SAP-12345",
    "sap_doc_entry": 123,
    "sap_error_message": ""
  }
}
```

---

## 13. Settings & Exchange Rate

### 13.1 Get Settings

```http
GET /settings
```

**Response:** `{ "data": { "exchange_rate": 1470.0 } }`

### 13.2 Update Global Exchange Rate

```http
PUT /settings
Content-Type: application/json

{ "exchange_rate": 1490.0 }
```

### 13.3 Update Exchange Rate on Specific Order

```http
PUT /orders/101/exchange_rate
Content-Type: application/json

{ "exchange_rate": 1490.0 }
```

> Omit body `{}` to reset to current global default.

**Response:**
```jsonc
{
  "data": {
    "id": 101,
    "exchange_rate": 1490.0,
    "amount_total_iqd": 372500.0
  }
}
```

### 13.4 Get All Pricelists

```http
GET /pricelists
```

### 13.5 Get All Warehouses

```http
GET /warehouses
```

### 13.6 Get Current Session

```http
GET /session
```

**Response:**
```jsonc
{
  "data": {
    "user_id": 3,
    "user_name": "Administrator",
    "user_login": "admin",
    "company_id": 1,
    "company_name": "NBS Company",
    "uid": 3,
    "exchange_rate": 1470.0
  }
}
```

---

## 14. Complete UI Flow

### Screen 1 — App Startup

```
1. GET /session              → verify auth + get current user
2. GET /setup                → load pricelists, warehouses, invoice_types, exchange_rate
3. Cache results locally (no need to call again unless refresh)
```

### Screen 2 — New Order

```
1. User picks customer → GET /customers?query=...
2. User selects customer → store partner_id
3. POST /orders { partner_id, pricelist_id, invoice_type }
   → get back order.id to work with
```

### Screen 3 — Add Products to Order

```
For each product the user selects:
1. POST /products/data { product_id, pricelist_id }
   → show available UoMs + warehouses + price
2. User picks UoM → POST /products/uom_price { product_id, pricelist_id, uom_id }
   → update price field
3. User fills quantity + discount → POST /orders/:id/lines
   → line added, order totals updated
```

### Screen 4 — Edit Order Lines

```
Change quantity/price  → PUT  /orders/:id/lines/:lid
Remove a line          → DELETE /orders/:id/lines/:lid
Change order note      → PUT  /orders/:id { "note": "..." }
Change invoice type    → PUT  /orders/:id { "invoice_type": "3" }
```

### Screen 5 — Confirm & Send

```
1. POST /orders/:id/confirm
   → creates sale.order in Odoo + syncs to SAP
   → check sap_synced + sap_error_message in response
2. (Optional) POST /orders/:id/send_whatsapp
3. (Optional) GET  /orders/:id/report  → PDF download
```

### Screen 6 — Orders List

```
GET /orders?state=sale&limit=20&offset=0
→ paginated list with filter by state/date/customer
→ click order → GET /orders/:id (full details)
```

---

## 15. Data Models Reference

### Order States

| Value | Arabic | Meaning |
|---|---|---|
| `draft` | مسودة | Newly created, editable |
| `quotation` | عرض سعر | Sent to customer for review |
| `sale` | طلب مبيعات | Confirmed → linked to sale.order |
| `done` | مكتمل | Fully delivered/done |
| `cancel` | ملغي | Cancelled |

### Invoice Types

| Key | Arabic |
|---|---|
| `1` | زبون محل |
| `2` | شركات توصيل |
| `3` | نقليات |
| `4` | ديلفري |
| `5` | NBS |
| `6` | شورجة |
| `7` | NA |
| `8` | مكاتب الشورجة |

### Order Object Fields

| Field | Type | Description |
|---|---|---|
| `id` | int | Internal Odoo ID |
| `name` | string | Order reference e.g. `S00042` |
| `date` | ISO datetime | Order date |
| `state` | string | See states above |
| `user_id` | object | `{ id, name }` — salesperson |
| `partner_id` | object | `{ id, name, phone, mobile, email }` |
| `pricelist_id` | object | `{ id, name }` |
| `currency_id` | object | `{ id, name }` — always USD |
| `exchange_rate` | float | USD → IQD rate |
| `amount_subtotal` | float | Before discount (USD) |
| `amount_discount` | float | Total discount (USD) |
| `amount_tax` | float | Tax (USD) |
| `amount_total` | float | Final total (USD) |
| `amount_total_iqd` | float | Final total (IQD) |
| `invoice_type` | string | `"1"` to `"8"` |
| `note` | string | Notes field |
| `sale_order_id` | object | `{ id, name, state }` or `null` |
| `sap_doc_num` | string | SAP Document Number |
| `sap_doc_entry` | int | SAP Doc Entry |
| `sap_synced` | bool | SAP sync status |
| `sap_error_message` | string | Last SAP error (empty if synced) |
| `sap_last_sync_date` | ISO datetime | Last sync attempt |
| `order_lines` | array | Array of line objects |

### Order Line Object Fields

| Field | Type | Description |
|---|---|---|
| `id` | int | Line ID |
| `sequence` | int | Sort order |
| `product_id` | object | `{ id, name, default_code, foreign_name }` |
| `product_uom_id` | object | `{ id, name }` |
| `warehouse_id` | object | `{ id, name, code }` |
| `location_id` | object | `{ id, name }` |
| `quantity` | float | Quantity ordered |
| `unit_price` | float | Price per unit (USD) |
| `discount_percent` | float | Discount % (0–100) |
| `price_after_discount` | float | Unit price after discount |
| `line_subtotal` | float | qty × unit_price (before discount) |
| `discount_amount` | float | Total discount amount |
| `line_total` | float | qty × price_after_discount |
| `available_qty` | float | Stock available in selected warehouse |
| `custom_product_name` | string | Override name on printed invoice |

---

## 16. Error Handling

### Common Errors

| Error Message | Cause | Solution |
|---|---|---|
| `Authentication required` | Missing or invalid API key | Check Authorization header |
| `Invalid API key` | Wrong key | Regenerate key in Odoo |
| `Order not found` | Wrong order ID | Verify the ID |
| `Cannot edit an order in 'sale' state` | Order already confirmed | Only draft/quotation are editable |
| `Cannot confirm an order without lines` | Empty order | Add at least one line |
| `Cannot cancel a done order` | Order is done | Cannot be undone |
| `product_id is required` | Missing field in line body | Include product_id |
| `warehouse_id is required` | Missing field in line body | Include warehouse_id |

### Error Handling Pattern

```typescript
async function createOrder(data: CreateOrderInput) {
  try {
    const order = await apiCall('POST', '/orders', data);
    return { success: true, order };
  } catch (error) {
    if (error.message.includes('Customer not found')) {
      return { success: false, message: 'Customer does not exist' };
    }
    if (error.message.includes('Pricelist not found')) {
      return { success: false, message: 'Invalid pricelist' };
    }
    return { success: false, message: error.message };
  }
}
```

---

## 17. API Service Layer (TypeScript)

Complete ready-to-use service file:

```typescript
// src/services/posApi.ts

const BASE_URL = 'http://192.168.116.15:8070/api/pos_perfume/v1';

// Store API key in environment variable
const API_KEY = import.meta.env.VITE_POS_API_KEY || '';

const defaultHeaders = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json',
};

// ─── Core fetch wrapper ───────────────────────────────────────────────────────

async function api<T>(
  method: 'GET' | 'POST' | 'PUT' | 'DELETE',
  path: string,
  body?: object,
): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: defaultHeaders,
    body: body ? JSON.stringify(body) : undefined,
  });

  // Handle PDF binary responses
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/pdf')) {
    return response.blob() as unknown as T;
  }

  const json = await response.json();
  if (!json.success) {
    throw new Error(json.error || 'Unknown API error');
  }
  return json.data as T;
}

// ─── Session ──────────────────────────────────────────────────────────────────

export const posApi = {

  getSession: () => api('GET', '/session'),

  getSetup: () => api('GET', '/setup'),

  // ─── Settings ──────────────────────────────────────────────────────────────

  getSettings: () => api<{ exchange_rate: number }>('GET', '/settings'),

  updateSettings: (data: { exchange_rate: number }) =>
    api('PUT', '/settings', data),

  // ─── Customers ─────────────────────────────────────────────────────────────

  listCustomers: (query = '', limit = 50, offset = 0) =>
    api('GET', `/customers?query=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`),

  getCustomer: (id: number) =>
    api('GET', `/customers/${id}`),

  createCustomer: (data: {
    name: string;
    phone?: string;
    mobile?: string;
    email?: string;
    street?: string;
    city?: string;
    ref?: string;
    country_id?: number;
  }) => api('POST', '/customers', data),

  updateCustomer: (id: number, data: object) =>
    api('PUT', `/customers/${id}`, data),

  // ─── Products ──────────────────────────────────────────────────────────────

  listProducts: (query = '', limit = 80, offset = 0) =>
    api('GET', `/products?query=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}`),

  getProductData: (productId: number, pricelistId?: number) =>
    api('POST', '/products/data', { product_id: productId, pricelist_id: pricelistId }),

  getUomPrice: (productId: number, uomId: number, pricelistId?: number) =>
    api<{ price_unit: number }>('POST', '/products/uom_price', {
      product_id: productId,
      uom_id: uomId,
      pricelist_id: pricelistId,
    }),

  getProduct: (id: number, pricelistId?: number) =>
    api('GET', `/products/${id}${pricelistId ? `?pricelist_id=${pricelistId}` : ''}`),

  // ─── Orders ────────────────────────────────────────────────────────────────

  listOrders: (params: {
    query?: string;
    state?: string;
    partner_id?: number;
    user_id?: number;
    date_from?: string;
    date_to?: string;
    sap_synced?: boolean;
    limit?: number;
    offset?: number;
  } = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== '') q.set(k, String(v));
    });
    return api('GET', `/orders?${q.toString()}`);
  },

  getOrder: (id: number) =>
    api('GET', `/orders/${id}`),

  createOrder: (data: {
    partner_id: number;
    pricelist_id?: number;
    invoice_type?: string;
    note?: string;
    exchange_rate?: number;
    user_id?: number;
    order_lines?: object[];
  }) => api('POST', '/orders', data),

  updateOrder: (id: number, data: object) =>
    api('PUT', `/orders/${id}`, data),

  deleteOrder: (id: number) =>
    api('DELETE', `/orders/${id}`),

  // ─── Order Lines ───────────────────────────────────────────────────────────

  addLine: (orderId: number, data: {
    product_id: number;
    warehouse_id: number;
    product_uom_id?: number;
    quantity?: number;
    unit_price?: number;
    discount_percent?: number;
    custom_product_name?: string;
  }) => api('POST', `/orders/${orderId}/lines`, data),

  updateLine: (orderId: number, lineId: number, data: object) =>
    api('PUT', `/orders/${orderId}/lines/${lineId}`, data),

  deleteLine: (orderId: number, lineId: number) =>
    api('DELETE', `/orders/${orderId}/lines/${lineId}`),

  // ─── Order Actions ─────────────────────────────────────────────────────────

  confirmOrder: (id: number) =>
    api('POST', `/orders/${id}/confirm`),

  setQuotation: (id: number) =>
    api('POST', `/orders/${id}/quotation`),

  cancelOrder: (id: number) =>
    api('POST', `/orders/${id}/cancel`),

  resetToDraft: (id: number) =>
    api('POST', `/orders/${id}/draft`),

  updateExchangeRate: (orderId: number, rate?: number) =>
    api('PUT', `/orders/${orderId}/exchange_rate`, rate ? { exchange_rate: rate } : {}),

  // ─── WhatsApp ──────────────────────────────────────────────────────────────

  sendWhatsApp: (orderId: number) =>
    api('POST', `/orders/${orderId}/send_whatsapp`),

  sendWhatsAppImage: (orderId: number) =>
    api('POST', `/orders/${orderId}/send_whatsapp_image`),

  // ─── PDF Report ────────────────────────────────────────────────────────────

  getOrderReportUrl: (orderId: number, download = true): string =>
    `${BASE_URL}/orders/${orderId}/report?download=${download}`,

  downloadOrderReport: async (orderId: number): Promise<void> => {
    const url = `${BASE_URL}/orders/${orderId}/report`;
    const response = await fetch(url, { headers: defaultHeaders });
    const contentType = response.headers.get('content-type') || '';

    if (contentType.includes('application/pdf')) {
      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `order_${orderId}.pdf`;
      link.click();
    } else {
      const json = await response.json();
      if (!json.data?.pdf_available) {
        throw new Error('PDF not available — wkhtmltopdf not installed on server');
      }
    }
  },

  // ─── SAP ───────────────────────────────────────────────────────────────────

  syncSap: (orderId: number) =>
    api('POST', `/orders/${orderId}/sync_sap`),

};
```

### Usage example in a React component

```typescript
// components/NewOrderContainer.tsx

import { posApi } from '@/services/posApi';

async function handleConfirm(orderId: number) {
  const result = await posApi.confirmOrder(orderId);

  if (result.sap_synced) {
    toast.success(`Order confirmed! SAP Doc: ${result.sap_doc_num}`);
  } else if (result.sap_error_message) {
    toast.warning(`Order confirmed but SAP sync failed: ${result.sap_error_message}`);
  } else {
    toast.success('Order confirmed!');
  }
}
```

---

## Appendix — All Endpoints Summary

| Method | Path | Description |
|---|---|---|
| `GET` | `/session` | Current user info |
| `GET` | `/setup` | Bootstrap all POS data |
| `GET` | `/settings` | Get exchange rate |
| `PUT` | `/settings` | Update exchange rate |
| `GET` | `/pricelists` | All active pricelists |
| `GET` | `/warehouses` | All active warehouses |
| `GET` | `/customers` | List / search customers |
| `POST` | `/customers` | Create customer |
| `GET` | `/customers/:id` | Get single customer |
| `PUT` | `/customers/:id` | Update customer |
| `GET` | `/products` | List / search products |
| `POST` | `/products/data` | Full product data (UoMs + prices + stock) |
| `POST` | `/products/uom_price` | Price for a specific UoM |
| `GET` | `/products/:id` | Get single product |
| `GET` | `/orders` | List orders with filters |
| `POST` | `/orders` | Create order |
| `GET` | `/orders/:id` | Get full order with lines |
| `PUT` | `/orders/:id` | Update order header |
| `DELETE` | `/orders/:id` | Cancel order |
| `POST` | `/orders/:id/lines` | Add a line |
| `PUT` | `/orders/:id/lines/:lid` | Update a line |
| `DELETE` | `/orders/:id/lines/:lid` | Delete a line |
| `POST` | `/orders/:id/confirm` | Confirm order → creates sale.order + SAP |
| `POST` | `/orders/:id/quotation` | Set state to quotation |
| `POST` | `/orders/:id/cancel` | Cancel order |
| `POST` | `/orders/:id/draft` | Reset cancelled order to draft |
| `PUT` | `/orders/:id/exchange_rate` | Update IQD exchange rate |
| `POST` | `/orders/:id/send_whatsapp` | Send WhatsApp text message |
| `POST` | `/orders/:id/send_whatsapp_image` | Send WhatsApp image |
| `GET` | `/orders/:id/report` | Download PDF report |
| `POST` | `/orders/:id/sync_sap` | Force re-sync to SAP |
