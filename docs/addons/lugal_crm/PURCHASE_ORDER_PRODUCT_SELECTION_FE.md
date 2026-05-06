# Purchase Order — Product Selection & API Integration (Frontend)

**Audience:** Supply Chain frontend developers  
**Priority:** High  
**Backend:** `lugal_crm` — REST product search + `POST /api/purchase-orders` (and enhanced JSON-RPC PO create).  
**Language:** This document is the single source of truth for FE behavior; align UI with it to avoid `product_id` vs code mismatches.

---

## 1. Problem summary (what to fix)

| Symptom | Likely cause |
|--------|----------------|
| "No product found for item no" (or similar) after a valid pick | Submitting **code** or free text instead of **`product_id`**, or validating against the wrong field |
| Item details not auto-filled | Not mapping **search response** fields into row state |
| Confusing dropdown | Showing **code** as value instead of **`display_name`**; mixing identifiers |
| Errors after selection | Client-side validation still tied to **item code** lookup |

**Rule:** Treat **`id` from `GET /api/products/search`** as the only line identifier for create/update flows. **`code`** is display/metadata only.

---

## 2. Identifier: `product_id` (mandatory)

- **`product_id`** = `product.product` database id (integer from API `data[].id`).
- **Never** send bare item code as the sole reference for create; the backend create API expects **`product_id`** on each line.
- **`code`** in the API response is **`default_code`** — use for labels only.

---

## 3. Product search API

### Request

| Item | Value |
|------|--------|
| Method | `GET` |
| URL | `/api/products/search` |
| Auth | `Authorization: Bearer <JWT>` (same token as other Supply CRM calls) |

### Query parameters

| Param | Required | Description |
|-------|----------|-------------|
| `search` | **Conditionally** | Substring match on **item code** (`default_code`) **or** **product name**. See §3.1. |
| `supplier_id` | Recommended | Integer **`lugal.supply.vendor` id** (same id as **Vendors** list / PO vendor in supply APIs — **not** necessarily `res.partner` id). |
| `limit` | No | Default `20`, max `100`. |

### When to call (important)

- **Do not call** search when `search` is **empty/whitespace** **and** `supplier_id` is **absent** — the backend returns **`[]`** (by design, to avoid loading the entire catalog).
- **Do call** with **only** `supplier_id` (and optional `limit`) when you want “catalog for this vendor” **without** a text filter (requires vendor links on products — see §3.2).
- **Always pass `supplier_id` when the PO vendor is already chosen** — narrows results to products linked to that vendor’s partner on the template (`seller_ids`), when supported.

### Success response

HTTP `200`, body:

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
      "description": "Premium fragrance",
      "is_available": true
    }
  ]
}
```

### Error responses

| HTTP | Meaning |
|------|--------|
| `401` | Missing/invalid JWT — body `{ "status": false, "error": "Unauthorized" }` |
| `400` | Bad `supplier_id` type, etc. |
| `501` | `supplier_id` was sent but **`seller_ids` is not available** on product templates (e.g. Purchase app / vendor links not installed). Message explains the fix. |

### 3.1 `is_available` (dropdown filtering)

- Backend sets **`is_available: true`** when **`qty_available > 0`**.
- **Purchasable products with zero on-hand are still returned** with `is_available: false`.
- **FE choice:**
  - **Strict:** show only rows where `is_available === true` (hides out-of-stock).
  - **Recommended for PO:** show all results, use **badge** or style for “out of stock” — backend **allows** PO lines for `is_available: false` if `product_id` is valid and `purchase_ok` is true.

### 3.2 Vendor catalog prerequisite

Filtering by **`supplier_id`** requires each product template to have **vendor / `seller_ids`** pointing at that vendor’s **`partner_id`**. If the server returns **501**, FE should show the backend **`error`** string; do not treat it as “no products”.

---

## 4. Dropdown UX (binding)

| UI | Source field |
|----|----------------|
| Label shown to user | **`display_name`** (fallback: `code` + `name`) |
| Value stored in form state | **`id`** → stored as **`product_id`** |
| Debounced search input | Sends as query param **`search`** |

After the user selects a row:

| Field in your row model | API source |
|-------------------------|------------|
| Product identifier | `id` → **`product_id`** |
| Name / line description | `name`, `description` |
| Unit | `unit` |
| Default unit price | `price` (user may edit before submit) |

**Do not** re-resolve the line by code after selection; if the user picked from the list, **`product_id`** is authoritative.

---

## 5. Optional: product detail

| Method | `GET` |
| URL | `/api/products/<id>` |
| Auth | Same JWT |

Use **only** if you need extra fields (e.g. `barcode`, `categ_name`) beyond search. Not required for basic PO lines.

---

## 6. Create purchase order (REST)

### Request

| Item | Value |
|------|--------|
| Method | `POST` |
| URL | `/api/purchase-orders` |
| Headers | `Authorization: Bearer <JWT>`, `Content-Type: application/json` |
| Body | JSON object below |

### Body schema

```json
{
  "supplier_id": 12,
  "exchange_rate": 1500,
  "division": "europe",
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

| Field | Rules |
|-------|--------|
| `supplier_id` | **Required.** **`lugal.supply.vendor` id** (integer). Must exist and not be deleted. |
| `exchange_rate` | Optional. Number. Stored on PO when the field exists (module ≥ 1.0.5). |
| `division` | Optional. Case-insensitive: `europe` / `eu` → `europe`; `china` / `cn` → `china`. **Unknown values are ignored** (not an error). |
| `items` | **Required**, non-empty array. |
| `items[].product_id` | **Required.** Must be active, **`purchase_ok`**. |
| `items[].qty` | **Required.** Must be **> 0**. |
| `items[].price` | Required for pricing logic; must be **≥ 0**. |
| `items[].discount` | Optional, **0–100** (percent). Line **`unit_price`** stored as `price * (1 - discount/100)`. |

### Success response

HTTP `200`:

```json
{
  "status": true,
  "data": { }
}
```

`data` is the **full Supply PO payload** (same family as `POST /api/crm/supply/po/<id>/get`): header fields, **`lines`** with **`product_id`**, totals, etc. Use it to refresh UI or redirect to detail.

### Error response

```json
{ "status": false, "error": "Human-readable message" }
```

Map **`error`** to toasts / inline messages. Examples: invalid `supplier_id`, invalid `product_id`, `qty <= 0`, bad JSON.

---

## 7. Legacy / alternate: JSON-RPC PO create

Existing flow remains available:

- **`POST /api/crm/supply/po/create`** (JSON-RPC) with **`vendor_customer_id`** = **`res.partner`** id of the vendor’s contact, and **`lines`** (or alias **`items`**).
- Lines may include **`product_id`** plus **`quantity`** / **`qty`**, **`unit_price`** / **`price`**, optional **`discount`** — same validation idea as REST.

**Do not mix up:**

- REST **`POST /api/purchase-orders`** → **`supplier_id`** = **vendor record id**.
- JSON-RPC **`po/create`** → **`vendor_customer_id`** = **partner id**.

Pick one integration path per screen unless you explicitly map partner ↔ vendor.

---

## 8. Frontend validation (before submit)

- Every line must have a selected **`product_id`** (integer from search/detail).
- **`qty` > 0** for every line.
- If the user typed free text but never selected a row, **do not** submit; show: **“Please select a valid item from the list.”**
- After a valid dropdown selection, **do not** show generic “product not found” errors unless the **API** returned an error for that request.

---

## 9. Table UX (recommended)

- Start with **one** empty row; placeholder **“Search or select item…”** on the selector.
- Add row control for additional lines.
- Keep columns minimal until a product is selected (avoid many empty inputs).

---

## 10. Checklist for developers

- [ ] Dropdown option **value** = **`id`**; **label** = **`display_name`**.
- [ ] Create payload uses **`items[].product_id`**, not code.
- [ ] Search debounced; **no request** when `search` empty and no **`supplier_id`**.
- [ ] **`supplier_id`** passed on search when PO vendor is known.
- [ ] Handle **`501`** on search (vendor links / Purchase).
- [ ] Client validation: **`product_id` + qty** before **`POST /api/purchase-orders`**.
- [ ] Display backend **`error`** from `{ status: false }` on failure.

---

## 11. Summary

| Topic | Correct approach |
|-------|-------------------|
| Line identity | **`product_id`** from search `id` |
| Display | **`display_name`** |
| Search | `GET /api/products/search` + JWT |
| Create | `POST /api/purchase-orders` + **`supplier_id` (vendor id)** + **`items` with `product_id`** |
| `is_available` | Informational; optional FE filter — does not block backend PO line creation |

---

*End of document.*
