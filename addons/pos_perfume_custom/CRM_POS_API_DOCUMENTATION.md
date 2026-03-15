# NBS CRM — POS API Documentation

**Version:** 1.1 — All endpoints tested ✅  
**Base URL:** `http://<your-odoo-host>:8070`  
**API Prefix:** `/api/pos_perfume/v1`  
**Content-Type:** `application/json`

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Common Response Format](#2-common-response-format)
3. [Customers](#3-customers)
4. [Products](#4-products)
5. [Categories](#5-categories)
6. [Pricelists](#6-pricelists)
7. [Warehouses](#7-warehouses)
8. [Orders — CRUD](#8-orders--crud)
9. [Order Line Operations](#9-order-line-operations)
10. [Order State Transitions](#10-order-state-transitions)
11. [Additional Order Actions](#11-additional-order-actions)
12. [Invoice Type Reference](#12-invoice-type-reference)
13. [Order State Machine](#13-order-state-machine)
14. [Error Reference](#14-error-reference)
15. [Quick Reference — All Endpoints](#15-quick-reference--all-endpoints)

---

## 1. Authentication

### Method A — Session Cookie (Recommended for browser/SPA)

```http
POST /web/session/authenticate
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

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "uid": 2,
    "name": "Administrator",
    "username": "admin"
  }
}
```

The server sets a `session_id` cookie automatically. Send it with every subsequent request.

---

### Method B — JWT Token (Mobile / external clients)

#### Login

```http
POST /lugal/auth/login
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "username": "admin",
    "password": "admin"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "result": {
    "success": true,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "user": {
        "id": 2,
        "name": "Administrator",
        "username": "admin"
      }
    }
  }
}
```

Use `access_token` in the header for all POS API endpoints:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

> **Note:** The POS API (`/api/pos_perfume/v1/*`) validates Bearer tokens against Odoo `res.users.apikeys`.  
> For browser apps use **session cookie** (Method A).  
> For Bearer, generate an API key: Odoo Settings → Technical → API Keys.

#### Refresh Token

```http
POST /lugal/auth/refresh
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "method": "call",
  "params": { "refresh_token": "<refresh_token>" }
}
```

#### Logout

```http
POST /lugal/auth/logout
Content-Type: application/json
{ "jsonrpc": "2.0", "method": "call", "params": {} }
```

#### Verify Token

```http
POST /lugal/auth/verify
Content-Type: application/json
{ "jsonrpc": "2.0", "method": "call", "params": { "token": "<access_token>" } }
```

---

## 2. Common Response Format

### Success
```json
{
  "success": true,
  "message": "OK",
  "data": { ... }
}
```

### Error
```json
{
  "success": false,
  "error": "Error message here"
}
```

### Paginated list
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 1670,
    "offset": 0,
    "limit": 20,
    "items": [ ... ]
  }
}
```

---

## 3. Customers

### 3.1 — List Customers

```http
GET /api/pos_perfume/v1/customers
```

| Parameter | Type    | Description                                    |
|-----------|---------|------------------------------------------------|
| `query`   | string  | Search by name, phone, mobile, or ref          |
| `limit`   | integer | Max per page (default: `20`)                   |
| `offset`  | integer | Pagination offset (default: `0`)               |

**Example:**
```http
GET /api/pos_perfume/v1/customers?query=ahmed&limit=20
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 1670,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 1765,
        "name": "Mukesh Dandia Ka dada",
        "ref": "IBG05751",
        "phone": "07006818904",
        "mobile": "",
        "email": "admin@admin.com",
        "street": "",
        "city": "Mosul",
        "country_id": { "id": 104, "name": "India" },
        "pricelist_id": { "id": 1, "name": "SAP Price List 1" }
      }
    ]
  }
}
```

---

### 3.2 — Get Customer by ID

```http
GET /api/pos_perfume/v1/customers/{id}
```

Returns a single customer object (same structure as list items).

---

## 4. Products

### 4.1 — List Products

```http
GET /api/pos_perfume/v1/products
```

| Parameter       | Type    | Description                                      |
|----------------|---------|--------------------------------------------------|
| `query`        | string  | Search by name, code (default_code), foreign name|
| `categ_id`     | integer | Filter by category ID                            |
| `pricelist_id` | integer | Pricelist ID — populates `available_uoms[].price`|
| `limit`        | integer | Max per page (default: `20`)                     |
| `offset`       | integer | Pagination offset (default: `0`)                 |

**Example:**
```http
GET /api/pos_perfume/v1/products?query=LOC&pricelist_id=1&limit=20
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 688,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 6951,
        "name": "لاكوسنت اسود ESS",
        "default_code": "LOC00362",
        "foreign_name": "555423491",
        "uom_id": { "id": 34, "name": "كغم" },
        "list_price": 0.0,
        "qty_available": 0.0,
        "color_class": "",
        "badge_text": "",
        "active": true,
        "sale_ok": true,
        "categ_id": { "id": 25, "name": "Local" },
        "items_group_code": 132,
        "items_group_name": "Local",
        "brand": { "key": "local", "name": "Local", "code": "LOC" },
        "category_type": {
          "type": "fragrances",
          "name": "Fragrances",
          "name_ar": "عطور",
          "properties": {
            "size_ml": null, "size_kg": null, "is_bulk": false,
            "concentration": null, "gender": "Unisex",
            "season": null, "longevity": null, "sillage": null
          }
        },
        "available_uoms": [
          { "id": 34, "name": "كغم",             "price": 75.0 },
          { "id": 35, "name": "50 غم",            "price": 4.75 },
          { "id": 36, "name": "100 غم",           "price": 8.5 },
          { "id": 37, "name": "125 غم",           "price": 10.38 },
          { "id": 38, "name": "0.5 كيلو",         "price": 38.5 },
          { "id": 39, "name": "0.25 كغم بلاستيك", "price": 20.75 }
        ],
        "warehouses": [
          { "id": 5, "name": "05", "code": "05", "quantity": 120.5 }
        ]
      }
    ]
  }
}
```

#### Product Fields

| Field               | Type    | Description                                             |
|--------------------|---------|---------------------------------------------------------|
| `id`               | integer | Product ID                                              |
| `name`             | string  | Product name                                            |
| `default_code`     | string  | SAP Item Code / SKU                                     |
| `foreign_name`     | string  | Alternative/foreign name                                |
| `uom_id`           | object  | Base unit of measure `{id, name}`                       |
| `list_price`       | float   | Base price (use `available_uoms[].price` from pricelist)|
| `qty_available`    | float   | Total available quantity                                |
| `categ_id`         | object  | Category `{id, name}`                                   |
| `items_group_code` | integer | SAP item group code                                     |
| `items_group_name` | string  | SAP item group name                                     |
| `brand`            | object  | `{key, name, code}`                                     |
| `category_type`    | object  | Detected type with properties (see below)               |
| `available_uoms`   | array   | All UoMs with pricelist prices `[{id, name, price}]`    |
| `warehouses`       | array   | Stock per warehouse `[{id, name, code, quantity}]`      |

#### category_type Types

| `type`       | Description       | Key Properties                              |
|-------------|-------------------|---------------------------------------------|
| `fragrances`| Perfumes & oils   | `size_ml`, `size_kg`, `is_bulk`, `gender`   |
| `glass`     | Glass bottles     | `glass_type`, `capacity_ml`, `cover_box`    |
| `packaging` | Boxes             | `box_type`, `is_luxury_box`, `units_per_box`|
| `samples`   | Sample products   | `size_ml`, `is_tester`                      |
| `pack`      | Sets & bundles    | `units_in_pack`, `pack_type`                |
| `alcohol`   | Alcohol           | `concentration_pct`, `volume_liters`        |
| `accessories`| Accessories      | `accessory_type`, `material`                |
| `incense`   | Incense           | `incense_type`, `weight_g`, `is_charcoal`   |
| `devices`   | Electric devices  | `device_type`, `power_type`, `coverage_area`|
| `other`     | Uncategorized     | —                                           |

---

### 4.2 — Get Product by ID

```http
GET /api/pos_perfume/v1/products/{id}?pricelist_id=1
```

Returns a single full product object (same structure as list items).

---

## 5. Categories

### 5.1 — List All Categories

```http
GET /api/pos_perfume/v1/categories
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "categories": [
      { "id": 22, "name": "AF Series",      "product_count": 16 },
      { "id": 18, "name": "Alcohol",         "product_count": 24 },
      { "id": 9,  "name": "Amour de Fleurs", "product_count": 1038 },
      { "id": 13, "name": "Box",             "product_count": 289 },
      { "id": 16, "name": "Crystal Glass",   "product_count": 635 }
    ]
  }
}
```

Use category `id` as `categ_id` filter on `/products`.

---

## 6. Pricelists

### 6.1 — List All Pricelists

```http
GET /api/pos_perfume/v1/pricelists
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "items": [
      { "id": 1, "name": "SAP Price List 1", "currency_id": 1, "currency_name": "USD" },
      { "id": 2, "name": "SAP Price List 2", "currency_id": 1, "currency_name": "USD" }
    ]
  }
}
```

---

## 7. Warehouses

### 7.1 — List All Warehouses

```http
GET /api/pos_perfume/v1/warehouses
```

**Response:**
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "items": [
      { "id": 1,  "name": "My Company", "code": "WH" },
      { "id": 2,  "name": "01",          "code": "01" },
      { "id": 3,  "name": "02",          "code": "02" }
    ]
  }
}
```

`warehouse_id` is **required** when adding order lines.

---

## 8. Orders — CRUD

### Full Order Object

```json
{
  "id": 120,
  "name": "POS00127",
  "date": "2026-03-15T14:00:00",
  "state": "sale",
  "user_id":    { "id": 2,    "name": "Administrator" },
  "partner_id": {
    "id": 1765,
    "name": "Mukesh Dandia Ka dada",
    "phone": "07006818904",
    "mobile": "",
    "email": "admin@admin.com"
  },
  "pricelist_id": { "id": 1, "name": "SAP Price List 1" },
  "currency_id":  { "id": 1, "name": "USD" },
  "exchange_rate": 1500.0,
  "amount_subtotal": 100.0,
  "amount_discount": 5.0,
  "amount_tax": 0.0,
  "amount_total": 95.0,
  "amount_total_iqd": 142500.0,
  "invoice_type": "1",
  "note": "Customer note",
  "sale_order_id": {
    "id": 80,
    "name": "S00080",
    "state": "sale"
  },
  "sap_doc_num": "",
  "sap_doc_entry": 0,
  "sap_synced": false,
  "sap_error_message": "",
  "sap_last_sync_date": null,
  "order_lines": [
    {
      "id": 140,
      "sequence": 10,
      "product_id": {
        "id": 1933,
        "name": "01 INGLOTكحل",
        "default_code": "CS00166",
        "foreign_name": ""
      },
      "product_uom_id": { "id": 30, "name": "قطعه" },
      "warehouse_id":   { "id": 1,  "name": "My Company", "code": "WH" },
      "location_id":    { "id": 5,  "name": "Stock" },
      "quantity": 2.0,
      "unit_price": 50.0,
      "discount_percent": 5.0,
      "price_after_discount": 47.5,
      "line_subtotal": 100.0,
      "discount_amount": 5.0,
      "line_total": 95.0,
      "available_qty": 0.0,
      "custom_product_name": ""
    }
  ]
}
```

#### Order Fields

| Field                | Type     | Description                                              |
|---------------------|----------|----------------------------------------------------------|
| `id`                | integer  | Order ID                                                 |
| `name`              | string   | Auto-generated sequence number (e.g. `POS00127`)        |
| `date`              | datetime | Creation date (ISO 8601)                                 |
| `state`             | string   | `draft` / `quotation` / `sale` / `done` / `cancel`      |
| `user_id`           | object   | Sales rep `{id, name}`                                   |
| `partner_id`        | object   | Customer `{id, name, phone, mobile, email}`              |
| `pricelist_id`      | object   | Pricelist `{id, name}`                                   |
| `currency_id`       | object   | Currency `{id, name}`                                    |
| `exchange_rate`     | float    | IQD exchange rate                                        |
| `amount_subtotal`   | float    | Sum before discount (USD)                                |
| `amount_discount`   | float    | Total discount (USD)                                     |
| `amount_tax`        | float    | Tax amount (USD)                                         |
| `amount_total`      | float    | Final total (USD)                                        |
| `amount_total_iqd`  | float    | Final total in IQD                                       |
| `invoice_type`      | string   | Type code `"1"`–`"8"` (see [Section 12](#12-invoice-type-reference)) |
| `note`              | string   | Order note                                               |
| `sale_order_id`     | object   | Linked Odoo Sale Order `{id, name, state}` or `null`    |
| `sap_doc_num`       | string   | SAP document number                                      |
| `sap_doc_entry`     | integer  | SAP doc entry                                            |
| `sap_synced`        | boolean  | Successfully synced to SAP                               |
| `sap_error_message` | string   | Last SAP sync error                                      |
| `sap_last_sync_date`| datetime | Last SAP sync attempt                                    |
| `order_lines`       | array    | List of line objects                                     |

---

### 8.1 — List Orders

```http
GET /api/pos_perfume/v1/orders
```

| Parameter    | Type    | Description                                   |
|-------------|---------|-----------------------------------------------|
| `state`     | string  | Filter: `draft`, `quotation`, `sale`, `cancel` |
| `partner_id`| integer | Filter by customer ID                          |
| `limit`     | integer | Max per page (default: `20`)                   |
| `offset`    | integer | Pagination offset (default: `0`)               |

**Response** (summary objects — use `GET /orders/{id}` for full details):
```json
{
  "success": true,
  "message": "OK",
  "data": {
    "total": 82,
    "offset": 0,
    "limit": 20,
    "items": [
      {
        "id": 120,
        "name": "POS00127",
        "date": "2026-03-15T14:00:00",
        "state": "sale",
        "partner_id": 1765,
        "partner_name": "Mukesh Dandia Ka dada",
        "user_id": 2,
        "user_name": "Administrator",
        "invoice_type": "1",
        "amount_total": 95.0,
        "amount_total_iqd": 142500.0,
        "sap_synced": false,
        "sap_doc_num": "",
        "note": "",
        "lines_count": 1
      }
    ]
  }
}
```

---

### 8.2 — Get Order by ID

```http
GET /api/pos_perfume/v1/orders/{id}
```

Returns the full order object including all `order_lines`.

---

### 8.3 — Create Order

```http
POST /api/pos_perfume/v1/orders
Content-Type: application/json
```

| Field           | Type    | Required | Description                                     |
|----------------|---------|----------|-------------------------------------------------|
| `partner_id`   | integer | **Yes**  | Customer ID                                     |
| `pricelist_id` | integer | No       | Pricelist ID                                    |
| `invoice_type` | string  | No       | Type code `"1"`–`"8"` (default: `"1"`)          |
| `note`         | string  | No       | Order note                                      |
| `order_lines`  | array   | No       | Initial lines (see line fields below)           |

**Example:**
```json
{
  "partner_id": 1765,
  "pricelist_id": 1,
  "invoice_type": "1",
  "note": "Express delivery",
  "order_lines": [
    {
      "product_id": 6951,
      "warehouse_id": 2,
      "product_uom_id": 34,
      "quantity": 5.0,
      "unit_price": 75.0,
      "discount_percent": 10.0
    }
  ]
}
```

**Response:** Full order object with `state: "draft"`.

> Orders are always created in **`draft`** state. Use `/confirm` or `/quotation` to advance.

---

### 8.4 — Update Order

```http
PUT /api/pos_perfume/v1/orders/{id}
Content-Type: application/json
```

| Field           | Type    | Description                                                          |
|----------------|---------|----------------------------------------------------------------------|
| `partner_id`   | integer | New customer                                                         |
| `pricelist_id` | integer | New pricelist                                                        |
| `invoice_type` | string  | New type code                                                        |
| `note`         | string  | Updated note                                                         |
| `order_lines`  | array   | **Replaces ALL lines** with new list. Omit to keep existing lines.  |

> **Warning:** Providing `order_lines` in the body **deletes all current lines** and replaces them with the new ones.

**Response:** Full order object.

---

### 8.5 — Delete Order (Soft Cancel)

```http
DELETE /api/pos_perfume/v1/orders/{id}
```

Sets `state = "cancel"`. The record is kept (not deleted).

**Response:**
```json
{ "success": true, "message": "Order cancelled" }
```

---

## 9. Order Line Operations

### Order Line Fields

| Field                  | Type    | Description                                      |
|-----------------------|---------|--------------------------------------------------|
| `id`                  | integer | Line ID                                          |
| `sequence`            | integer | Display order (default: 10)                      |
| `product_id`          | object  | `{id, name, default_code, foreign_name}`         |
| `product_uom_id`      | object  | Unit of measure `{id, name}`                     |
| `warehouse_id`        | object  | Warehouse `{id, name, code}`                     |
| `location_id`         | object  | Stock location `{id, name}`                      |
| `quantity`            | float   | Ordered quantity                                 |
| `unit_price`          | float   | Price per unit (USD)                             |
| `discount_percent`    | float   | Discount % (0–100)                               |
| `price_after_discount`| float   | `unit_price × (1 - discount_percent/100)`        |
| `line_subtotal`       | float   | `unit_price × quantity`                          |
| `discount_amount`     | float   | `line_subtotal × discount_percent/100`           |
| `line_total`          | float   | `line_subtotal - discount_amount`                |
| `available_qty`       | float   | Available stock in selected warehouse            |
| `custom_product_name` | string  | Override product display name                    |

---

### 9.1 — Add Line

```http
POST /api/pos_perfume/v1/orders/{id}/lines
Content-Type: application/json
```

| Field                 | Type    | Required | Description                                      |
|----------------------|---------|----------|--------------------------------------------------|
| `product_id`         | integer | **Yes**  | Product ID                                       |
| `warehouse_id`       | integer | **Yes**  | Warehouse ID                                     |
| `product_uom_id`     | integer | No       | UoM ID (defaults to product's base UoM)          |
| `quantity`           | float   | No       | Quantity (default: `1.0`)                        |
| `unit_price`         | float   | No       | Unit price (defaults to `list_price`)            |
| `discount_percent`   | float   | No       | Discount % (default: `0.0`)                      |
| `sequence`           | integer | No       | Display order (default: `10`)                    |
| `custom_product_name`| string  | No       | Override display name                            |
| `location_id`        | integer | No       | Stock location (defaults to warehouse's stock)   |

**Response:** The new line object.

---

### 9.2 — Update Line

```http
PUT /api/pos_perfume/v1/orders/{id}/lines/{line_id}
Content-Type: application/json
```

All fields are optional. Only provided fields are updated.

**Example:**
```json
{ "quantity": 10, "discount_percent": 15.0 }
```

**Response:** The updated line object.

---

### 9.3 — Delete Line

```http
DELETE /api/pos_perfume/v1/orders/{id}/lines/{line_id}
```

**Response:**
```json
{ "success": true, "message": "Line deleted" }
```

---

## 10. Order State Transitions

### State Overview

| State       | Meaning                          | Odoo Sale Order state |
|-------------|----------------------------------|-----------------------|
| `draft`     | Saved, not yet sent              | None                  |
| `quotation` | Sent as Quotation                | `draft` (Quotation)   |
| `sale`      | Confirmed as Sale Order          | `sale` (Sales Order)  |
| `done`      | Closed / completed (system only) | `done`                |
| `cancel`    | Cancelled                        | Cancelled / None      |

---

### 10.1 — Create Quotation

```http
POST /api/pos_perfume/v1/orders/{id}/quotation
```

- Requires at least one order line
- Creates an Odoo Sale Order in **`draft`** state (appears as a Quotation in Odoo/SAP)
- Sets POS order state to **`quotation`**

**Response:** Full order object

```json
{
  "success": true,
  "message": "Quotation created",
  "data": {
    "id": 120,
    "state": "quotation",
    "sale_order_id": {
      "id": 80,
      "name": "S00080",
      "state": "draft"
    },
    ...
  }
}
```

---

### 10.2 — Confirm as Sale Order

```http
POST /api/pos_perfume/v1/orders/{id}/confirm
```

- Requires at least one order line
- Allowed from **`draft`** or **`quotation`** state
- Creates or updates the Odoo Sale Order in **`sale`** state
- Sets POS order state to **`sale`**

**Response:** Full order object

```json
{
  "success": true,
  "message": "Order confirmed",
  "data": {
    "id": 120,
    "state": "sale",
    "sale_order_id": {
      "id": 80,
      "name": "S00080",
      "state": "sale"
    },
    ...
  }
}
```

---

### 10.3 — Revert to Draft

```http
POST /api/pos_perfume/v1/orders/{id}/draft
```

- Works from **any** state including `cancel`
- Sets POS order state to **`draft`**
- Does **not** cancel or delete the linked Sale Order

**Response:** Full order object with `state: "draft"`

---

### 10.4 — Cancel Order

```http
POST /api/pos_perfume/v1/orders/{id}/cancel
```

- Not allowed on `done` orders
- Sets POS order state to **`cancel`**

**Response:** Full order object with `state: "cancel"`

---

## 11. Additional Order Actions

### 11.1 — Update Exchange Rate

```http
PUT /api/pos_perfume/v1/orders/{id}/exchange_rate
Content-Type: application/json

{ "exchange_rate": 1490.0 }
```

Omit body (or send `{}`) to reset to the current system default rate.

**Response:**
```json
{
  "success": true,
  "message": "Exchange rate updated",
  "data": {
    "id": 120,
    "exchange_rate": 1490.0,
    "amount_total_iqd": 141550.0
  }
}
```

---

### 11.2 — Force SAP Sync

```http
POST /api/pos_perfume/v1/orders/{id}/sync_sap
```

Forces re-sync of the linked Sale Order to SAP. Requires a confirmed order.

**Response:**
```json
{
  "success": true,
  "message": "SAP sync completed",
  "data": {
    "sap_synced": true,
    "sap_doc_num": "12345",
    "sap_doc_entry": 456,
    "sap_error_message": ""
  }
}
```

---

### 11.3 — Download PDF Report

```http
GET /api/pos_perfume/v1/orders/{id}/report
GET /api/pos_perfume/v1/orders/{id}/report?download=false
```

Returns the order PDF binary.  
`download=false` → opens inline. `download=true` (default) → triggers download.

If `wkhtmltopdf` is not installed:
```json
{
  "success": true,
  "message": "PDF report not available",
  "data": { "pdf_available": false, "setup_required": "sudo apt-get install wkhtmltopdf" }
}
```

---

### 11.4 — Send WhatsApp Text

```http
POST /api/pos_perfume/v1/orders/{id}/send_whatsapp
```

Sends the order invoice as a WhatsApp text message via ULTRAMSG.

**Response (success):**
```json
{
  "success": true,
  "message": "Sent",
  "data": { "sent": true, "message_id": "..." }
}
```

**Response (ULTRAMSG not configured):**
```json
{
  "success": true,
  "message": "WhatsApp feature not configured",
  "data": { "sent": false, "available": false, "setup_required": "..." }
}
```

---

### 11.5 — Send WhatsApp Image

```http
POST /api/pos_perfume/v1/orders/{id}/send_whatsapp_image
```

Sends the order invoice as a WhatsApp image. Requires `wkhtmltoimage` and ULTRAMSG.

---

## 12. Invoice Type Reference

The `invoice_type` field uses numeric string codes:

| Code | Arabic Label       | English Description      |
|------|--------------------|--------------------------|
| `"1"` | زبون محل          | Shop Customer            |
| `"2"` | شركات توصيل       | Delivery Companies       |
| `"3"` | نقليات            | Freight / Transport      |
| `"4"` | ديلفري            | Delivery                 |
| `"5"` | NBS               | NBS Internal             |
| `"6"` | شورجة             | Shourja Market           |
| `"7"` | NA                | Not Applicable           |
| `"8"` | مكاتب الشورجة     | Shourja Offices          |

---

## 13. Order State Machine

```
                   POST /orders
                       │
                       ▼
              ┌─────────────────┐
              │      DRAFT      │◄──────────── POST /draft (from any state)
              │   state=draft   │
              └───────┬─────────┘
                      │
          ┌───────────┴──────────────┐
          │                          │
   POST /quotation            POST /confirm
          │                          │
          ▼                          ▼
 ┌─────────────────┐       ┌─────────────────┐
 │    QUOTATION    │       │      SALE       │
 │ state=quotation │       │   state=sale    │
 │  SO state=draft │       │  SO state=sale  │
 └───────┬─────────┘       └────────┬────────┘
         │                          │
  POST /confirm              POST /draft
  (upgrades to sale)               │
         │                          │
         └──────────┬───────────────┘
                    │
                    ▼
           ┌─────────────────┐
           │      SALE       │
           │   state=sale    │
           │  SO state=sale  │
           └─────────────────┘


POST /cancel (from draft, quotation, or sale)
           │
           ▼
  ┌─────────────────┐
  │     CANCEL      │
  │  state=cancel   │
  └─────────────────┘
```

### State Transition Table

| From State   | Action           | POS state → | Sale Order state → |
|-------------|------------------|-------------|---------------------|
| `draft`     | `/quotation`     | `quotation` | `draft` (Quotation) |
| `draft`     | `/confirm`       | `sale`      | `sale` (Sales Order)|
| `quotation` | `/confirm`       | `sale`      | `sale` (upgraded)   |
| `sale`      | `/draft`         | `draft`     | unchanged           |
| `quotation` | `/draft`         | `draft`     | unchanged           |
| `cancel`    | `/draft`         | `draft`     | unchanged           |
| any         | `/cancel`        | `cancel`    | unchanged           |

---

## 14. Error Reference

### HTTP Status Codes

| Status | Meaning               |
|--------|-----------------------|
| `200`  | Success               |
| `400`  | Bad Request           |
| `401`  | Unauthorized          |
| `403`  | Forbidden             |
| `404`  | Not Found             |
| `500`  | Internal Server Error |

### Common Errors

| Error                                              | Cause                                          |
|---------------------------------------------------|------------------------------------------------|
| `Authentication required`                         | Missing or expired session / token             |
| `Invalid API key`                                 | Bearer token not a valid Odoo API key          |
| `Order not found`                                 | Order ID doesn't exist                         |
| `Order line not found`                            | Line ID doesn't belong to the order            |
| `Cannot confirm an order without lines`           | Order has no lines                             |
| `Cannot create a quotation without order lines`   | Order has no lines                             |
| `Cannot confirm an order in 'cancel' state`       | Order is cancelled                             |
| `Cannot cancel a done order`                      | Order is done                                  |
| `product_id is required for each order line`      | Missing product in line                        |
| `warehouse_id is required for each order line`    | Missing warehouse in line                      |
| `Product {id} not found`                          | Product ID doesn't exist                       |
| `Warehouse {id} not found`                        | Warehouse ID doesn't exist                     |
| `Wrong value for pos.perfume.order.invoice_type`  | Use codes `"1"` to `"8"` only                  |

---

## Complete Usage Example

```http
# 1. Authenticate
POST /web/session/authenticate
{ "db": "lugal_local", "login": "admin", "password": "admin" }

# 2. Load reference data
GET /api/pos_perfume/v1/pricelists
GET /api/pos_perfume/v1/warehouses
GET /api/pos_perfume/v1/categories

# 3. Search customer
GET /api/pos_perfume/v1/customers?query=ahmed

# 4. Search products
GET /api/pos_perfume/v1/products?query=LOC&pricelist_id=1&limit=20

# 5. Create draft order
POST /api/pos_perfume/v1/orders
{
  "partner_id": 1765,
  "pricelist_id": 1,
  "invoice_type": "1",
  "order_lines": [
    { "product_id": 6951, "warehouse_id": 2,
      "product_uom_id": 34, "quantity": 5, "unit_price": 75.0 }
  ]
}
# → { "data": { "id": 120, "state": "draft", ... } }

# 6. Add another line
POST /api/pos_perfume/v1/orders/120/lines
{ "product_id": 1933, "warehouse_id": 1, "quantity": 2, "unit_price": 50.0 }

# 7. Update a line
PUT /api/pos_perfume/v1/orders/120/lines/140
{ "quantity": 10, "discount_percent": 15.0 }

# --- FLOW A: Save as Quotation ---
POST /api/pos_perfume/v1/orders/120/quotation
# → POS state: "quotation" | SO state: "draft"

# Later upgrade quotation to sale order:
POST /api/pos_perfume/v1/orders/120/confirm
# → POS state: "sale" | SO state: "sale"

# --- FLOW B: Confirm directly as Sale Order ---
POST /api/pos_perfume/v1/orders/120/confirm
# → POS state: "sale" | SO state: "sale"

# 8. Force SAP sync (if needed)
POST /api/pos_perfume/v1/orders/120/sync_sap

# 9. Download invoice PDF
GET /api/pos_perfume/v1/orders/120/report

# 10. Send via WhatsApp
POST /api/pos_perfume/v1/orders/120/send_whatsapp
```

---

## 15. Quick Reference — All Endpoints

| Method   | Endpoint                                           | Description                           |
|---------|----------------------------------------------------|---------------------------------------|
| `POST`  | `/lugal/auth/login`                                | JWT login                             |
| `POST`  | `/lugal/auth/refresh`                              | Refresh JWT token                     |
| `POST`  | `/lugal/auth/logout`                               | Logout                                |
| `POST`  | `/lugal/auth/verify`                               | Verify JWT token                      |
| `POST`  | `/web/session/authenticate`                        | Session cookie login                  |
| —       | —                                                  | —                                     |
| `GET`   | `/api/pos_perfume/v1/customers`                    | List customers                        |
| `GET`   | `/api/pos_perfume/v1/customers/{id}`               | Get customer                          |
| —       | —                                                  | —                                     |
| `GET`   | `/api/pos_perfume/v1/products`                     | List products                         |
| `GET`   | `/api/pos_perfume/v1/products/{id}`                | Get product                           |
| —       | —                                                  | —                                     |
| `GET`   | `/api/pos_perfume/v1/categories`                   | List categories                       |
| `GET`   | `/api/pos_perfume/v1/pricelists`                   | List pricelists                       |
| `GET`   | `/api/pos_perfume/v1/warehouses`                   | List warehouses                       |
| —       | —                                                  | —                                     |
| `GET`   | `/api/pos_perfume/v1/orders`                       | List orders (filterable)              |
| `POST`  | `/api/pos_perfume/v1/orders`                       | Create order → `draft`                |
| `GET`   | `/api/pos_perfume/v1/orders/{id}`                  | Get order (full)                      |
| `PUT`   | `/api/pos_perfume/v1/orders/{id}`                  | Update order / replace lines          |
| `DELETE`| `/api/pos_perfume/v1/orders/{id}`                  | Cancel order (soft delete)            |
| —       | —                                                  | —                                     |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/lines`            | Add line                              |
| `PUT`   | `/api/pos_perfume/v1/orders/{id}/lines/{lid}`      | Update line                           |
| `DELETE`| `/api/pos_perfume/v1/orders/{id}/lines/{lid}`      | Delete line                           |
| —       | —                                                  | —                                     |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/quotation`        | `draft` → `quotation` (SO=draft)      |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/confirm`          | any → `sale` (SO=sale)                |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/draft`            | any → `draft`                         |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/cancel`           | any → `cancel`                        |
| —       | —                                                  | —                                     |
| `PUT`   | `/api/pos_perfume/v1/orders/{id}/exchange_rate`    | Update IQD exchange rate              |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/sync_sap`         | Force SAP sync                        |
| `GET`   | `/api/pos_perfume/v1/orders/{id}/report`           | Download PDF invoice                  |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/send_whatsapp`    | Send WhatsApp text                    |
| `POST`  | `/api/pos_perfume/v1/orders/{id}/send_whatsapp_image` | Send WhatsApp image               |
