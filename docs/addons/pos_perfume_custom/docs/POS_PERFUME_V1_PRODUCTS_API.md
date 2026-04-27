# POS Perfume REST API — `GET/POST /api/pos_perfume/v1/products`

Base path: **`/api/pos_perfume/v1`**  
Controller: `addons/pos_perfume_custom/controllers/pos_perfume_rest_controller.py`

Authentication: session cookie, **`Authorization: Bearer <JWT>`** (when `lugal_auth` is installed), or **API key** (`rpc` scope). Without auth the endpoint returns **`401 Unauthorized`**.

Response envelope (all REST routes in this controller):

```json
{
  "success": true,
  "message": "OK",
  "data": { }
}
```

---

## List / search products

**`GET /api/pos_perfume/v1/products`** or **`POST /api/pos_perfume/v1/products`**  
`POST` may include a JSON body; keys in the body override query-string parameters with the same names.

### Query / body parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | `""` | Search in `name`, `default_code`, `barcode`, and `foreign_name` (if the field exists). |
| `pricelist_id` | int | *(POS default)* | Pricelist used to compute `list_price`, `available_uoms`, etc. |
| `limit` | int | `80` | Page size. **`0` means fetch all matching rows** (same as `fetch_all=true`). **There is no hard server cap** (the old `min(limit, 500)` limit was removed). |
| `offset` | int | `0` | Skip this many rows **after** SQL filters. When **`brand`**, **`category_type`**, or **`has_price_only`** is used, filtering is done in memory first; `offset` / `limit` then apply to that filtered list. |
| `fetch_all` | bool | `false` | If `true`, return every row matching the SQL domain (no `limit`). |
| `include_inactive` | bool | `false` | If `true`, archived products are included (`active` filter removed). |
| `include_non_sale` | bool | `false` | If `true`, products with `sale_ok = false` are included. |
| `categ_id` / `category_id` | int | — | Restrict to a category **and its children** (subtree). Invalid id → **404**. |
| `item_codes` | string or list | — | Comma-separated codes or JSON array; adds `default_code in (...)` (max 500 codes). |
| `default_code_prefix` | string | — | `ilike` prefix filter (`%` appended if missing). |
| `brand` | string | — | Brand filter (Python), aligned with POS rules: `adf`, `givaudan`, `royal` / `robertet`, `european` / `euro`, `florchem`, etc. |
| `category_type` | string | — | Loose match on category path + name (`fragrances`, `glass`, `packaging`, …). |
| `has_price_only` | `1` / `true` | `false` | Keep only rows where **`has_price`** is true (after pricelist resolution). |
| `strict_pricelist` | bool | `false` | Passed through to pricing logic (see controller). |
| `uom_id` / `uom` | — | Optional UoM hint for pricing. |

### Response `data` fields

| Field | Description |
|-------|-------------|
| `items` | Array of catalog rows (same shape as before: UoMs, warehouses, `brand`, `category_type`, `has_price`, …). |
| `total` | Total matching rows **for this request** (after in-memory filters when those filters are used). |
| `offset` | Offset applied to the returned page (see above). |
| `limit` | SQL or in-memory page size; **`0` when `fetch_all` / unlimited**. |
| `returned` | `items.length`. |
| `fetch_all` | Whether the response was built without a SQL row limit. |
| `pricelist_id` | Pricelist id used for pricing. |

### Examples

```http
# First page (80 rows), default behaviour
GET /api/pos_perfume/v1/products?query=&limit=80&offset=0&pricelist_id=2

# Full catalog (no row cap)
GET /api/pos_perfume/v1/products?fetch_all=1&pricelist_id=2

# Same as fetch_all=1
GET /api/pos_perfume/v1/products?limit=0&pricelist_id=2

# Brand + pricelist + page on filtered set
GET /api/pos_perfume/v1/products?brand=givaudan&pricelist_id=2&limit=40&offset=0
```

### Performance note

`fetch_all`, `limit=0`, or filters that require a **full scan** (`brand`, `category_type`, `has_price_only`) load **all** matching `product.product` rows into memory before serialization. Large databases may need higher Odoo **`limit_time_real`** / reverse-proxy timeouts.

---

*This document reflects the behaviour after the catalog endpoint upgrade in `pos_perfume_rest_controller.py`.*
