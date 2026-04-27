# Frontend guide: products and pricelist (CRM ↔ Odoo)

This document describes how the **NBS CRM (16)** app talks to Odoo to load products and prices: request parameters, response shapes, and the shared client. Routes use **JSON-RPC** (see `src/shared/services/apiClient.ts`).

---

## 1. Authentication and generic calls

- Protected product endpoints require a **Bearer JWT** in the `Authorization` header (public routes such as login are exceptions).
- `apiPost(route, params)` sends `params` inside the JSON-RPC body under `params`, together with `db` (database name from `VITE_DB_NAME`).
- Odoo usually returns `{ success: true, data: { ... } }`; `apiPost` unwraps `data` into `result.data` for callers.

---

## 2. POS-style product search — `POST /api/crm/pos/products`

Use for pickers, type-ahead search, or bulk loads **without** full pricelist line pricing (response uses `list_price` on each row).

### Request body (JSON)

| Parameter | Type | Description |
|-----------|------|-------------|
| `search` or `query` | string | Search text; **both are accepted** (sending the same value on both is fine). Matches `name`, `default_code`, and `foreign_name` when that field exists. |
| `pricelist_id` | number \| null | Optional; does not change the basic row shape today (`list_price` is still the catalog list price). |
| `fetch_all` | boolean | If `true`, or with `limit: 0` / `per_page: 0`: returns **all matching products with no server-side row cap**. |
| `limit` / `offset` | number | Legacy paging: page size and offset (used when `page` / `per_page` are not sent). |
| `page` / `per_page` | number | Page-based paging; if either is present, it overrides the `limit` / `offset` path. |
| `category_id` | number \| null | Filter by `product.category`. |
| `include_inactive` | boolean | Default `false`; set `true` to include archived products. |
| `sale_ok` | boolean | Default `true`; set `false` to include items not marked for sale. |

### Response shape (`data`)

```json
{
  "total": 12345,
  "offset": 0,
  "limit": 80,
  "returned": 80,
  "items": [
    {
      "id": 1,
      "name": "...",
      "default_code": "...",
      "foreign_name": "...",
      "uom_id": { "id": 1, "name": "Unit" },
      "list_price": 10.0,
      "qty_available": 0
    }
  ]
}
```

- With **`fetch_all: true`** (or `per_page <= 0` / `limit <= 0`): response `limit` is `0`, and `returned` is the number of rows in `items` (typically equals `total` when not page-limited).

### Example via `productService`

```ts
// Typical Vite `src/` layout:
import { productService } from './features/products/services/productService';

// All active saleable products matching the filter (no server row cap)
const res = await productService.listProducts({
  search: 'rose',
  fetch_all: true,
});

if (res.success && res.data) {
  const { items, total } = res.data;
}

// Single page
const page = await productService.listProducts({
  search: '',
  fetch_all: false,
  page: 2,
  per_page: 100,
});
```

---

## 3. Pricelist product list — `POST /api/crm/pricelist/products`

Returns products with **pricelist-derived** main price and, when rules exist, multiple UoMs in **`available_uoms`** (fixed-price rules on the same pricelist).

### Request body

| Parameter | Type | Description |
|-----------|------|-------------|
| `pricelist_id` | number \| null | Pricelist; if omitted, the controller picks a default from configuration. |
| `search` / `query` | string | Text search (name, code, foreign name). |
| `category_id` | number \| null | Single category. |
| `category_ids` | number[] | Several categories (`categ_id in ...`). |
| `page` | number | Default `1`. |
| `per_page` | number | Page size; **`0` means fetch all rows** (typically used together with `fetch_all: true` on the client). |
| `fetch_all` | boolean | If `true` or `per_page === 0`: **all matching rows, no server row cap**. |
| `uom_id` | number \| null | Filter by Odoo UoM: see `uom_align_sap_sales_unit` below. |
| `uom_align_sap_sales_unit` | boolean | Default **`true`**. When `uom_id` is set: **aligned with SAP** — a variant is included if `sap.product.extended.sales_uom_id` matches, **or** template `uom_id` matches **and** there is no extended row **or** extended `sales_unit` (SAP `SalesUnit` text) is non-empty **or** SAP left `SalesUnit` blank but **inventory** evidence matches (``inventory_uom_id`` / ``inventory_uom`` text for kg-class filters). Set **`false`** for the legacy rule: `(template uom_id = X) OR (extended.sales_uom_id = X)` with no SAP-field checks. |
| `new_releases_only` | boolean | Products created within the last `new_within_days` days. |
| `new_within_days` | number | Default `60`. |
| `discount_only` | boolean | Only products that have a percentage discount on this `pricelist_id` (variant / template / category / global rules are resolved server-side). |
| `item_codes` | string[] | Restrict to listed `default_code` values (server enforces a reasonable max length). |
| `default_code_prefix` | string | Code prefix (`%` is appended for `ilike` when missing). |
| `product_ids` | number[] | Restrict to these `product.product` ids. |
| `include_inactive` | boolean | Default `false`. |
| `sale_ok` | boolean | Default `true`. |
| `branch_id` | any | Reserved for future branch → pricelist mapping; **currently ignored**. |

### Response shape (`data`)

```json
{
  "items": [ /* same fields as the CRM pricelist UI */ ],
  "total": 12345,
  "page": 1,
  "per_page": 50,
  "returned": 50
}
```

- **`total`**: count of records matching the filter (before UI slicing, if any).
- **`returned`**: length of `items` in this response.

### Example: prefix `G` + kilogram UoM (aligned with SAP counts)

Use your real `uom.uom` id for **كغم** (e.g. `34` in many DBs). Omit `uom_align_sap_sales_unit` to use the default (**SAP-aligned**).

```ts
const res = await productService.getPriceList({
  pricelistId: 1,
  fetchAll: true,
  defaultCodePrefix: 'G',
  uomId: 34,
  // uomAlignSapSalesUnit: true, // optional; default on server is true
});
```

Legacy behaviour (old OR-only UoM match):

```ts
const resLegacy = await productService.getPriceList({
  pricelistId: 1,
  fetchAll: true,
  defaultCodePrefix: 'G',
  uomId: 34,
  uomAlignSapSalesUnit: false,
});
```

Example JSON body for **`POST /api/crm/pricelist/products`** (with your CRM auth wrapper / JWT as already used in the app):

```json
{
  "pricelist_id": 1,
  "fetch_all": true,
  "per_page": 0,
  "default_code_prefix": "G",
  "uom_id": 34,
  "uom_align_sap_sales_unit": true
}
```

---

### استخدام الـ API (عربي) — فلتر الأكواد `G` ووحدة كغم

1. **نقطة النهاية:** `POST /api/crm/pricelist/products` مع توكن المستخدم كما في بقية واجهات CRM.  
2. **تصفية الأكواد التي تبدأ بـ G:** أرسل `default_code_prefix` بقيمة `G` (السيرفر يضيف `%` تلقائياً لـ `ilike`).  
3. **تصفية وحدة كغم:** أرسل `uom_id` = معرف وحدة **كغم** في Odoo (`uom.uom`)، مثلاً `34` إن كان اسم الوحدة «كغم».  
4. **محاذاة أعداد SAP (الافتراضي):** لا ترسل `uom_align_sap_sales_unit` أو أرسل `true` — يستبعد المنتجات التي عندها سجل `sap.product.extended` لكن **حقل مبيعات SAP `sales_unit` فارغ** بينما القالب فقط على كغم (هذا كان سبب فرق العدد عن SAP).  
5. **السلوك القديم:** أرسل `"uom_align_sap_sales_unit": false` إذا أردت نفس منطق الـ OR السابق بدون التحقق من `sales_unit`.  
6. **جلب الكامل:** `fetch_all: true` و `per_page: 0` (أو ما يعادلهما في العميل) لتحميل القائمة كاملة.

### More `getPriceList` examples (search, category, pagination)

```ts
const res = await productService.getPriceList({
  pricelistId: 1,
  search: 'GIV',
  categoryId: 22,
  fetchAll: true,
});

const resPaged = await productService.getPriceList({
  fetchAll: false,
  page: 1,
  perPage: 50,
  pricelistId: 1,
});
```

---

## 4. The `useProducts` hook

`src/features/products/hooks/useProducts.ts` calls:

- `listProducts` with `fetch_all: true`, the same search string, and a numeric category when the store holds one.
- `getPriceList` with `fetchAll: true` and the same filters.

`productStore` keeps `category` as a string: if it is **digits only**, it is parsed as **`category_id`**; otherwise it is not sent as an id (a future API could map category names).

---

## 5. Performance and stability

There is **no server-side row cap** when using `fetch_all` / `per_page = 0`. Very large catalogs may:

- Increase response time and memory use in the browser and Odoo.

For heavy UIs, prefer **paged** loads (`fetchAll: false` + `page` / `perPage`) or incremental search with a moderate `per_page`.

---

## 6. Related routes

| Route | Purpose |
|-------|---------|
| `POST /api/crm/pricelist/pricelists` | Active pricelists. |
| `POST /api/crm/pricelist/categories` | Categories that have active, saleable products. |
| `POST /api/crm/pricelist/products/<id>` | Single product + stock. |
| `POST /api/crm/pos/product_detail` | Invoice-oriented detail (UoMs, warehouses, price). |

---

## 7. Common pitfalls

1. **Missing token** → `401` / `Unauthorized`.
2. **UI used `search` but only `query` was sent** → `productService.listProducts` now sends both for compatibility.
3. **Expecting `truncated` or `max_fetch`** → removed from responses; use **`total`** and **`returned`**.

---

*Aligned with `price_list_controller.py` and `pos_bridge_controller.py` in the `lugal_crm` addon.*
