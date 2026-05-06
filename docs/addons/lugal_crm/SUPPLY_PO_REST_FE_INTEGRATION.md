# Supply PO — Frontend integration (REST)

Short guide to wire **product search** and **create purchase order** in your SPA.  
Use the same **base URL** and **JWT** as the rest of the Supply CRM app.

---

## 1. Authentication

| Header | Value |
|--------|--------|
| `Authorization` | `Bearer <access_token>` |

Same token as `POST /api/crm/supply/po/list` (JSON-RPC) or other supply routes.

---

## 2. Product dropdown — `GET /api/products/search`

Use this to populate the line-item product selector. **Do not** ask users to type a numeric `product_id`; they pick a row — you store the returned **`id`**.

### Request

```
GET /api/products/search?search=<keyword>&supplier_id=<vendor_id>&limit=20
```

| Query | Required | Notes |
|-------|----------|--------|
| `search` | No* | Filter by product **code** or **name** (substring). |
| `supplier_id` | Recommended | `lugal.supply.vendor` **id** (same as vendors list). Narrows to that vendor’s catalog when products have vendor links. |
| `limit` | No | Default `20`, max `100`. |

\* If `search` is empty **and** `supplier_id` is missing, the API returns an **empty list** (by design).

### Response (`200`)

```json
{
  "status": true,
  "data": [
    {
      "id": 101,
      "code": "CS00973",
      "name": "Milano Perfume",
      "display_name": "CS00973 | Milano Perfume (pcs)",
      "unit": "pcs",
      "price": 25.5,
      "description": "...",
      "is_available": true
    }
  ]
}
```

### FE binding

| UI | Use |
|----|-----|
| Option **label** | `display_name` |
| Option **value** (saved in state) | **`id`** → this is **`product_id`** for create |

### Errors

| HTTP | Body |
|------|------|
| `401` | `{ "status": false, "error": "Unauthorized" }` |
| `501` | Vendor filter not available on server — show `error` text to user |

---

## 3. Create purchase order — `POST /api/purchase-orders`

Creates one **Supply PO** with lines. **`product_id`** on each line must be an **`id`** from the search response (or from `GET /api/products/<id>` if you use it).

### Request

```
POST /api/purchase-orders
Content-Type: application/json
Authorization: Bearer <token>
```

```json
{
  "supplier_id": 12,
  "division": "europe",
  "exchange_rate": 1500,
  "items": [
    {
      "product_id": 101,
      "qty": 10,
      "price": 25.5,
      "discount": 0
    }
  ]
}
```

| Field | Required | Notes |
|-------|----------|--------|
| `supplier_id` | Yes | **`lugal.supply.vendor` id** (not `res.partner` id). |
| `items` | Yes | Non-empty array. |
| `items[].product_id` | Yes | Integer = `data[].id` from product search. |
| `items[].qty` | Yes | Number **> 0**. |
| `items[].price` | Yes | Unit price before discount; **≥ 0**. |
| `items[].discount` | No | Percent **0–100**; stored line price = `price * (1 - discount/100)`. |
| `division` | No | `europe` / `china` (aliases accepted server-side). |
| `exchange_rate` | No | Number; stored on PO when supported. |

### Response (`200`)

```json
{
  "status": true,
  "data": { }
}
```

`data` is the full PO object (same shape family as supply PO **get**): use **`data.id`** as the numeric PO key and **`data.name`** as the human reference (e.g. sequence).

### Errors (`4xx` / `5xx`)

```json
{ "status": false, "error": "Human-readable message" }
```

Show `error` in the UI (toast / inline).

---

## 4. What the FE should **not** do

| Don’t | Do instead |
|-------|------------|
| Let users type **`product_id`** or “item number” as the only input | **Search → select row → use `id`** as `product_id` |
| Invent / guess `product_id` from SKU string without API | Always resolve via **search** (or product **GET** by id if you already stored a valid id) |
| Send create body **`name`** / **`po_id`** for **this** REST create | PO **id** and **name** are assigned by the server; read them from **`data`** after success |
| Call search with empty `search` and no `supplier_id` | Pass **`supplier_id`** once vendor is chosen, and/or a non-empty **`search`** |

---

## 5. Optional — product detail

```
GET /api/products/<product_id>
```

Same auth. Use only if you need extra fields beyond search (e.g. barcode). **`product_id`** here is still the same integer as search `id`.

---

## 6. CORS & dev proxy

If the SPA is on another origin, ensure the Odoo deployment allows your frontend origin (this controller sets permissive CORS for these routes). In local dev, prefer **proxying** `/api` to Odoo (e.g. Vite `proxy`) so the browser calls same-origin `/api/...`.

---

*End of integration guide.*
