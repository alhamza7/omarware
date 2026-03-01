# POS Perfume — Frontend API Guide
> **Odoo Server:** `http://localhost:8070`  
> **API Base:** `/api/pos_perfume/v1` (relative — via Vite proxy)  
> **Auth:** `Authorization: Bearer <your_api_key>`  

---

## ⚡ Setup in 3 Steps

### Step 1 — Configure `.env`
```env
# 44/.env
VITE_ODOO_URL=          # leave empty when using Vite proxy (recommended)
VITE_API_KEY=paste_your_api_key_here
```

### Step 2 — `vite.config.ts` already has proxy ✅
```ts
server: {
  proxy: {
    '/api': { target: 'http://localhost:8070', changeOrigin: true },
    '/web': { target: 'http://localhost:8070', changeOrigin: true },
  }
}
```
> This forwards `localhost:5175/api/...` → `localhost:8070/api/...`  
> **Without this proxy, ALL requests return 500.**

### Step 3 — Use the service
```ts
import api from '@/services/posPerfumeApi';

const setup = await api.getSetup();
// setup.data → { pricelists, warehouses, invoice_types, exchange_rate, ... }
```

---

## 🔑 Generate API Key
`Odoo → Settings → Users → (your user) → API Keys tab → New API Key`  
Paste the key in `.env` as `VITE_API_KEY=...`

---

## ❌ Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `500` on all endpoints | Requests hitting Vite (5175) not Odoo (8070) | Add proxy to `vite.config.ts` ✅ done |
| `401 Unauthorized` | Wrong or missing API key | Check `VITE_API_KEY` in `.env` |
| `404 Not found` | Wrong record ID | Verify ID exists in Odoo |
| `400 partner_id required` | Missing required field | Check request body |
| Network Error | Odoo server not running | Run `./start_local.sh` |

---

---

## 🧪 API Testing Guide

### ⚠️ Critical Rule: Never Use Hardcoded IDs

Every test run **must create its own fresh records** and chain IDs from the responses.
Using a hardcoded `order_id` that belongs to a cancelled/confirmed/done order will
cause 400 errors — this is **correct API behaviour**, not a bug.

---

### Test Prerequisites

| Test Group | Prerequisite |
|------------|-------------|
| All endpoints | Valid `API Key` from Odoo |
| Order lines / confirm / quotation | Order must be in `draft` or `quotation` state |
| `send_whatsapp` / `send_whatsapp_image` | ULTRAMSG configured in Odoo Settings |
| `GET /orders/:id/report` | `wkhtmltopdf` installed: `sudo apt-get install wkhtmltopdf` |
| `POST /orders/:id/sync_sap` | SAP connection configured + customer has a CardCode |

---

### Order State Rules

```
draft ──► quotation ──► sale ──► done   (terminal, cannot change)
  ▲              │
  │   cancel ◄──┘
  └── draftOrder()
```

| State | Can edit lines? | Can confirm? | Can add lines? |
|-------|----------------|--------------|----------------|
| `draft` | ✅ Yes | ✅ Yes | ✅ Yes |
| `quotation` | ✅ Yes | ✅ Yes | ✅ Yes |
| `sale` | ❌ No | ❌ Already confirmed | ❌ No |
| `done` | ❌ No | ❌ No | ❌ No |
| `cancel` | ❌ No | ❌ No | ❌ No → use `draftOrder()` first |

---

### Correct Test Order (IDs must be chained)

```
Step 1:  GET  /warehouses              → save warehouse_id from response
Step 2:  GET  /products?limit=10       → save product_id  from response
Step 3:  POST /customers               → save customer_id from response
Step 4:  POST /orders  {partner_id: customer_id}   → save order_id  (state: DRAFT)
Step 5:  PUT  /orders/:order_id                     → update note    (state: DRAFT) ✅
Step 6:  POST /orders/:order_id/lines  {product_id, warehouse_id, quantity:1}
                                       → save line_id from response  (state: DRAFT) ✅
Step 7:  PUT  /orders/:order_id/lines/:line_id  {quantity:2}          (state: DRAFT) ✅
Step 8:  DELETE /orders/:order_id/lines/:line_id                      (state: DRAFT) ✅
Step 9:  POST /orders/:order_id/quotation     → state becomes QUOTATION ✅
Step 10: POST /orders/:order_id/cancel        → state becomes CANCEL   ✅
Step 11: POST /orders/:order_id/draft         → state back to DRAFT     ✅
Step 12: POST /orders/:order_id/lines  {re-add line} → save line_id    (state: DRAFT) ✅
Step 13: POST /orders/:order_id/confirm                                 (state: DRAFT) ✅
         (note: requires at least one line)
Step 14: POST /orders/:order_id/sync_sap     → optional, needs SAP config
Step 15: POST /orders/:order_id/send_whatsapp      → optional, needs ULTRAMSG
Step 16: POST /orders/:order_id/send_whatsapp_image → optional, needs wkhtmltopdf
Step 17: GET  /orders/:order_id/report              → optional, needs wkhtmltopdf
Step 18: DELETE /orders/:order_id              → cleanup ✅
```

---

### Node.js Test Runner

Save as `test_pos_api.mjs` and run with `node test_pos_api.mjs`:

```js
/**
 * POS Perfume API — Standalone Test Runner
 * Run: node test_pos_api.mjs
 * Requires Node.js 18+ (native fetch)
 */

const BASE    = 'http://localhost:8070/api/pos_perfume/v1';
const API_KEY = 'YOUR_API_KEY_HERE';   // ← paste your key here

const HEADERS = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type':  'application/json',
};

// ── fetch wrapper ──────────────────────────────────────────────
async function call(method, path, body = null) {
  const opts = { method, headers: HEADERS };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  const ct  = res.headers.get('content-type') ?? '';
  const response = ct.includes('application/json')
    ? await res.json()
    : { _binary: true, status: res.status, ok: res.ok };
  return { httpStatus: res.status, response };
}

// ── test runner ────────────────────────────────────────────────
const results = {};
async function t(label, method, path, body = null, optional = false) {
  const { httpStatus, response } = await call(method, path, body);
  const ok = httpStatus >= 200 && httpStatus < 300 && response?.success !== false;
  const status  = ok ? 'success' : optional ? 'expected' : 'failed';
  const message = ok
    ? 'successfully fetched : data'
    : `${optional ? 'expected' : 'failed'} to fetch : ${label} -> ${response?.error ?? response}`;
  results[label] = { api: label, payload: body, httpStatus, response, status, message };
  const icon = ok ? '✔' : optional ? '~' : '✘';
  console.log(`  ${icon} ${method.padEnd(7)} ${path.padEnd(45)} [${httpStatus}]`);
  if (!ok) console.log(`      → ${response?.error ?? JSON.stringify(response).slice(0,100)}`);
  return results[label];
}

// ── run ────────────────────────────────────────────────────────
async function run() {
  console.log('\n══ POS Perfume API Test Runner ══\n');

  // 1. Session & Setup
  await t('GET /session',  'GET', '/session');
  await t('GET /setup',    'GET', '/setup');
  await t('GET /settings', 'GET', '/settings');
  await t('PUT /settings', 'PUT', '/settings', { exchange_rate: 1500 });

  // 2. Warehouses & Products  (save IDs for later)
  const whs  = await t('GET /warehouses', 'GET', '/warehouses');
  const prds = await t('GET /products',   'GET', '/products?limit=10');
  await t('GET /pricelists', 'GET', '/pricelists');

  const warehouseId = whs.response?.data?.items?.[0]?.id ?? 1;
  const productId   = prds.response?.data?.items?.[0]?.id ?? 1;

  await t('GET /products/:id',        'GET',  `/products/${productId}`);
  await t('POST /products/data',      'POST', '/products/data',      { product_id: productId });
  await t('POST /products/uom_price', 'POST', '/products/uom_price', { product_id: productId, pricelist_id: 1, uom_id: 1 });

  // 3. Customers  (save ID)
  await t('GET /customers', 'GET', '/customers?limit=10');
  const nc = await t('POST /customers', 'POST', '/customers', { name: 'API Test Customer', phone: '07700000000' });
  const customerId = nc.response?.data?.id;
  if (customerId) {
    await t('GET /customers/:id', 'GET', `/customers/${customerId}`);
    await t('PUT /customers/:id', 'PUT', `/customers/${customerId}`, { name: 'API Test Customer Updated' });
  }

  // 4. Orders  (ALWAYS create fresh — never use hardcoded IDs)
  await t('GET /orders', 'GET', '/orders?limit=10');
  const no = await t('POST /orders', 'POST', '/orders', { partner_id: customerId ?? 1 });
  const orderId = no.response?.data?.id;

  if (!orderId) {
    console.log('\n✘ Order creation failed — skipping order tests');
  } else {
    console.log(`  → order_id = ${orderId} (state: draft)\n`);

    // 5. Order CRUD  (order is in DRAFT — all must pass)
    await t('GET /orders/:id', 'GET', `/orders/${orderId}`);
    await t('PUT /orders/:id', 'PUT', `/orders/${orderId}`, { note: 'API test update' });

    // 6. Lines  (order in DRAFT — all must pass)
    const nl = await t('POST /orders/:id/lines', 'POST', `/orders/${orderId}/lines`,
      { product_id: productId, warehouse_id: warehouseId, quantity: 1 });
    const lineId = nl.response?.data?.id;
    if (lineId) {
      await t('PUT /orders/:id/lines/:lid',    'PUT',    `/orders/${orderId}/lines/${lineId}`, { quantity: 2 });
      await t('DELETE /orders/:id/lines/:lid', 'DELETE', `/orders/${orderId}/lines/${lineId}`);
    }

    // 7. State transitions  (draft → quotation → cancel → draft)
    await t('PUT /orders/:id/exchange_rate', 'PUT',  `/orders/${orderId}/exchange_rate`, { exchange_rate: 1500 });
    await t('POST /orders/:id/quotation',   'POST', `/orders/${orderId}/quotation`);
    await t('POST /orders/:id/cancel',      'POST', `/orders/${orderId}/cancel`);
    await t('POST /orders/:id/draft',       'POST', `/orders/${orderId}/draft`);

    // 8. Re-add line, then confirm  (order back in DRAFT)
    await t('POST /orders/:id/lines (re-add)', 'POST', `/orders/${orderId}/lines`,
      { product_id: productId, warehouse_id: warehouseId, quantity: 1 });
    await t('POST /orders/:id/confirm', 'POST', `/orders/${orderId}/confirm`);

    // 9. Optional — infrastructure dependent (failures are expected)
    await t('POST /orders/:id/sync_sap',            'POST', `/orders/${orderId}/sync_sap`,            null, true);
    await t('POST /orders/:id/send_whatsapp',        'POST', `/orders/${orderId}/send_whatsapp`,       null, true);
    await t('POST /orders/:id/send_whatsapp_image',  'POST', `/orders/${orderId}/send_whatsapp_image`, null, true);
    await t('GET /orders/:id/report',                'GET',  `/orders/${orderId}/report`,              null, true);

    // 10. Cleanup
    await t('DELETE /orders/:id', 'DELETE', `/orders/${orderId}`);
  }

  // Summary
  const all      = Object.values(results);
  const passed   = all.filter(r => r.status === 'success').length;
  const failed   = all.filter(r => r.status === 'failed').length;
  const expected = all.filter(r => r.status === 'expected').length;
  console.log(`\n══ Results: ${passed} passed  ${failed} failed  ${expected} expected (infra) ══`);
  if (failed) {
    console.log('\nFailed:');
    all.filter(r => r.status === 'failed').forEach(r =>
      console.log(`  ✘ ${r.api}  [${r.httpStatus}] ${r.response?.error ?? ''}`)
    );
  }
  if (expected) {
    console.log('\nExpected (requires infrastructure setup):');
    all.filter(r => r.status === 'expected').forEach(r =>
      console.log(`  ~ ${r.api}  [${r.httpStatus}] ${r.response?.error ?? ''}`)
    );
  }

  console.log('\n--- JSON RESULTS ---');
  console.log(JSON.stringify(results, null, 2));
}

run().catch(console.error);
```

---

### Expected Test Results

| Test | Expected Status | Notes |
|------|----------------|-------|
| All `GET` endpoints | ✅ `success` | |
| `POST /customers`, `PUT /customers/:id` | ✅ `success` | |
| `POST /orders` | ✅ `success` | Creates fresh draft order |
| `PUT /orders/:id` | ✅ `success` | Order is in draft |
| `POST /orders/:id/lines` | ✅ `success` | Order is in draft |
| `PUT /orders/:id/lines/:lid` | ✅ `success` | Order is in draft |
| `DELETE /orders/:id/lines/:lid` | ✅ `success` | Order is in draft |
| `POST /orders/:id/quotation` | ✅ `success` | draft → quotation |
| `POST /orders/:id/cancel` | ✅ `success` | quotation → cancel |
| `POST /orders/:id/draft` | ✅ `success` | cancel → draft |
| `POST /orders/:id/confirm` | ✅ `success` | Requires at least 1 line |
| `POST /orders/:id/send_whatsapp` | ⚠️ `expected` | Needs ULTRAMSG config |
| `POST /orders/:id/send_whatsapp_image` | ⚠️ `expected` | Needs `wkhtmltopdf` installed |
| `GET /orders/:id/report` | ⚠️ `expected` | Needs `wkhtmltopdf` installed |
| `POST /orders/:id/sync_sap` | ⚠️ `expected` | Needs SAP + customer CardCode |

---

### Infrastructure Setup (for optional tests)

```bash
# Fix: GET /orders/:id/report  +  send_whatsapp_image
sudo apt-get install wkhtmltopdf

# Fix: send_whatsapp  +  send_whatsapp_image
# Odoo → Settings → Technical → ULTRAMSG Config → New → fill token + instance
```

---

## Response Format

Every endpoint returns the **same wrapper**:

```ts
// SUCCESS
{
  "success": true,
  "message": "OK",
  "data": { ... }        // payload — shape varies per endpoint
}

// ERROR
{
  "success": false,
  "error": "Error description"
}
```

**HTTP status codes used:**
| Code | Meaning |
|------|---------|
| 200  | OK |
| 400  | Bad request / validation error |
| 404  | Record not found |
| 401  | Not authenticated |
| 500  | Server error |

---

## TypeScript Interfaces

```ts
// ─── Shared ─────────────────────────────────────────────
interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error?: string;
}

interface PaginatedResponse<T> {
  total: number;
  offset: number;
  limit: number;
  items: T[];
}

// ─── Setup ──────────────────────────────────────────────
interface PosSetup {
  pricelists:          Pricelist[];
  default_pricelist_id: number;
  warehouses:          Warehouse[];
  users:               User[];
  invoice_types:       InvoiceType[];
  exchange_rate:       number;
  currency:            string;   // "USD"
  secondary_currency:  string;   // "IQD"
}

interface Pricelist  { id: number; name: string; currency_id: number; }
interface Warehouse  { id: number; name: string; code: string; }
interface User       { id: number; name: string; }
interface InvoiceType { key: string; label: string; }

// ─── Customer ───────────────────────────────────────────
interface Customer {
  id:          number;
  name:        string;
  ref:         string;
  phone:       string;
  mobile:      string;
  email:       string;
  street:      string;
  city:        string;
  country_id:  { id: number; name: string } | null;
  pricelist_id:{ id: number; name: string } | null;
}

interface CreateCustomerBody {
  name:       string;        // required
  phone?:     string;
  mobile?:    string;
  email?:     string;
  street?:    string;
  city?:      string;
  ref?:       string;
  country_id?: number;
}

// ─── Product ────────────────────────────────────────────
interface Product {
  id:           number;
  name:         string;
  default_code: string;
  foreign_name: string;
  uom_id:       { id: number; name: string };
  list_price:   number;
  qty_available:number;
  color_class:  string;
  badge_text:   string;
  active:       boolean;
  sale_ok:      boolean;
  categ_id:     { id: number; name: string } | null;
  // present when fetched via GET /products/:id or POST /products/data
  available_uoms?: ProductUom[];
  warehouses?:     ProductWarehouse[];
}

interface ProductUom {
  id:    number;
  name:  string;
  price: number;
}

interface ProductWarehouse {
  id:       number;
  name:     string;
  code:     string;
  quantity: number;
}

interface ProductDataBody {
  product_id:   number;
  pricelist_id?: number | null;
  uom_id?:      number | null;
  warehouse_id?: number | null;
}

interface UomPriceBody {
  product_id:   number;
  pricelist_id: number;
  uom_id:       number;
}

// ─── Order ──────────────────────────────────────────────
type OrderState = 'draft' | 'quotation' | 'sale' | 'done' | 'cancel';
type InvoiceTypeKey = '1' | '2' | '3' | '4' | '5' | '6' | '7' | '8';

interface Order {
  id:              number;
  name:            string;
  date:            string;          // ISO 8601
  state:           OrderState;
  user_id:         { id: number; name: string } | null;
  partner_id:      { id: number; name: string; phone: string; mobile: string; email: string } | null;
  pricelist_id:    { id: number; name: string } | null;
  currency_id:     { id: number; name: string } | null;
  exchange_rate:   number;
  amount_subtotal: number;
  amount_discount: number;
  amount_tax:      number;
  amount_total:    number;
  amount_total_iqd:number;
  invoice_type:    InvoiceTypeKey | '';
  note:            string;
  sale_order_id:   { id: number; name: string; state: string } | null;
  sap_doc_num:     string;
  sap_doc_entry:   number;
  sap_synced:      boolean;
  order_lines:     OrderLine[];
}

interface OrderSummary {
  id:               number;
  name:             string;
  date:             string;
  state:            OrderState;
  partner_name:     string;
  amount_total:     number;
  amount_total_iqd: number;
  sap_synced:       boolean;
  sap_doc_num:      string;
}

interface CreateOrderBody {
  partner_id:    number;           // required
  pricelist_id?: number;           // optional — uses default if omitted
  invoice_type?: InvoiceTypeKey;
  note?:         string;
  exchange_rate?: number;
  user_id?:      number;
  order_lines?:  CreateOrderLineBody[];
}

interface UpdateOrderBody {
  partner_id?:    number;
  pricelist_id?:  number;
  note?:          string;
  invoice_type?:  InvoiceTypeKey;
  exchange_rate?: number;
  user_id?:       number;
}

// ─── Order Line ─────────────────────────────────────────
interface OrderLine {
  id:                  number;
  sequence:            number;
  product_id:          { id: number; name: string; default_code: string; foreign_name: string } | null;
  product_uom_id:      { id: number; name: string } | null;
  warehouse_id:        { id: number; name: string; code: string } | null;
  location_id:         { id: number; name: string } | null;
  quantity:            number;
  unit_price:          number;
  discount_percent:    number;
  price_after_discount:number;
  line_subtotal:       number;
  discount_amount:     number;
  line_total:          number;
  available_qty:       number;
  custom_product_name: string;
}

interface CreateOrderLineBody {
  product_id:          number;   // required
  warehouse_id:        number;   // required
  product_uom_id?:     number;   // optional — uses product default
  quantity?:           number;   // default 1
  unit_price?:         number;   // default product list_price
  discount_percent?:   number;   // default 0
  custom_product_name?:string;
  location_id?:        number;
  sequence?:           number;
}

interface UpdateOrderLineBody {
  product_id?:          number;
  product_uom_id?:      number;
  warehouse_id?:        number;
  location_id?:         number | null;
  quantity?:            number;
  unit_price?:          number;
  discount_percent?:    number;
  custom_product_name?: string | null;
  sequence?:            number;
}

// ─── Confirm result ─────────────────────────────────────
interface ConfirmResult {
  id:           number;
  name:         string;
  state:        OrderState;
  sale_order_id:{ id: number; name: string; state: string } | null;
  sap_synced:   boolean;
  sap_doc_num:  string;
  sap_doc_entry:number;
}

// ─── SAP sync result ────────────────────────────────────
interface SapSyncResult {
  sap_synced:        boolean;
  sap_doc_num:       string;
  sap_doc_entry:     number;
  sap_error_message: string;
}

// ─── Exchange rate ──────────────────────────────────────
interface ExchangeRateResult {
  id:               number;
  exchange_rate:    number;
  amount_total_iqd: number;
}
```

---

## API Client (Ready to Use)

Copy this file as `src/services/posPerfumeApi.ts`:

```ts
// src/services/posPerfumeApi.ts
// ============================================================
// POS Perfume API Client — v1
// ============================================================

const BASE_URL = 'http://localhost:8070/api/pos_perfume/v1';
const API_KEY  = 'YOUR_API_KEY_HERE';   // ← replace with your key

// ── Internal fetch helper ────────────────────────────────────
async function call<T>(
  endpoint: string,
  method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
  body?: unknown,
  raw = false
): Promise<ApiResponse<T>> {
  const headers: Record<string, string> = {
    Authorization: `Bearer ${API_KEY}`,
  };

  if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }

  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  // PDF / binary endpoints return raw Response — handled separately
  if (raw) return res as unknown as ApiResponse<T>;

  const json = await res.json() as ApiResponse<T>;

  if (!json.success) {
    console.error(`[POS API] ${method} ${endpoint} →`, json.error);
  }

  return json;
}

// ============================================================
// 1. SESSION
// ============================================================

/** Get current authenticated user info + exchange rate */
export const getSession = () =>
  call<{
    user_id: number; user_name: string; user_login: string;
    company_id: number; company_name: string;
    exchange_rate: number;
  }>('/session');

// ============================================================
// 2. SETUP  (call this once on POS boot)
// ============================================================

/** Get ALL data needed to boot the POS in one request */
export const getSetup = () => call<PosSetup>('/setup');

// ============================================================
// 3. SETTINGS
// ============================================================

export const getSettings  = () =>
  call<{ exchange_rate: number }>('/settings');

export const updateSettings = (exchange_rate: number) =>
  call<{ exchange_rate: number }>('/settings', 'PUT', { exchange_rate });

// ============================================================
// 4. CUSTOMERS
// ============================================================

export const listCustomers = (params?: {
  query?: string; limit?: number; offset?: number;
}) => {
  const q = new URLSearchParams();
  if (params?.query)  q.set('query',  params.query);
  if (params?.limit)  q.set('limit',  String(params.limit));
  if (params?.offset) q.set('offset', String(params.offset));
  return call<PaginatedResponse<Customer>>(`/customers?${q}`);
};

export const getCustomer    = (id: number) =>
  call<Customer>(`/customers/${id}`);

export const createCustomer = (body: CreateCustomerBody) =>
  call<Customer>('/customers', 'POST', body);

export const updateCustomer = (id: number, body: Partial<CreateCustomerBody>) =>
  call<Customer>(`/customers/${id}`, 'PUT', body);

// ============================================================
// 5. PRODUCTS
// ============================================================

export const listProducts = (params?: {
  query?: string; limit?: number; offset?: number; pricelist_id?: number;
}) => {
  const q = new URLSearchParams();
  if (params?.query)        q.set('query',        params.query);
  if (params?.limit)        q.set('limit',        String(params.limit));
  if (params?.offset)       q.set('offset',       String(params.offset));
  if (params?.pricelist_id) q.set('pricelist_id', String(params.pricelist_id));
  return call<PaginatedResponse<Product>>(`/products?${q}`);
};

/** Get single product with UoMs + warehouses */
export const getProduct = (id: number, pricelist_id?: number) => {
  const q = pricelist_id ? `?pricelist_id=${pricelist_id}` : '';
  return call<Product>(`/products/${id}${q}`);
};

/** Full product data: UoMs, prices, warehouses, stock */
export const getProductData = (body: ProductDataBody) =>
  call<Product & { available_uoms: ProductUom[]; warehouses: ProductWarehouse[] }>(
    '/products/data', 'POST', body
  );

/** Get price when UoM changes */
export const getUomPrice = (body: UomPriceBody) =>
  call<{ price_unit: number }>('/products/uom_price', 'POST', body);

// ============================================================
// 6. ORDERS — List & Create
// ============================================================

export const listOrders = (params?: {
  query?: string; state?: OrderState; partner_id?: number;
  date_from?: string; date_to?: string;
  limit?: number; offset?: number;
}) => {
  const q = new URLSearchParams();
  if (params?.query)      q.set('query',      params.query);
  if (params?.state)      q.set('state',      params.state);
  if (params?.partner_id) q.set('partner_id', String(params.partner_id));
  if (params?.date_from)  q.set('date_from',  params.date_from);
  if (params?.date_to)    q.set('date_to',    params.date_to);
  if (params?.limit)      q.set('limit',      String(params.limit));
  if (params?.offset)     q.set('offset',     String(params.offset));
  return call<PaginatedResponse<OrderSummary>>(`/orders?${q}`);
};

export const createOrder = (body: CreateOrderBody) =>
  call<Order>('/orders', 'POST', body);

// ============================================================
// 7. ORDERS — Get / Update / Delete
// ============================================================

export const getOrder    = (id: number) => call<Order>(`/orders/${id}`);

export const updateOrder = (id: number, body: UpdateOrderBody) =>
  call<Order>(`/orders/${id}`, 'PUT', body);

/** Soft-delete: sets state to 'cancel' */
export const deleteOrder = (id: number) =>
  call<{ id: number; state: 'cancel' }>(`/orders/${id}`, 'DELETE');

// ============================================================
// 8. ORDER LINES
// ============================================================

export const addOrderLine = (orderId: number, body: CreateOrderLineBody) =>
  call<OrderLine>(`/orders/${orderId}/lines`, 'POST', body);

export const updateOrderLine = (
  orderId: number, lineId: number, body: UpdateOrderLineBody
) =>
  call<OrderLine>(`/orders/${orderId}/lines/${lineId}`, 'PUT', body);

export const deleteOrderLine = (orderId: number, lineId: number) =>
  call<{ deleted: boolean; line_id: number }>(
    `/orders/${orderId}/lines/${lineId}`, 'DELETE'
  );

// ============================================================
// 9. ORDER ACTIONS
// ============================================================

/** Confirm order → creates sale.order + SAP sync */
export const confirmOrder   = (id: number) =>
  call<ConfirmResult>(`/orders/${id}/confirm`, 'POST');

/** Set order to quotation state */
export const quotationOrder = (id: number) =>
  call<{ id: number; state: OrderState }>(`/orders/${id}/quotation`, 'POST');

/** Cancel order */
export const cancelOrder    = (id: number) =>
  call<{ id: number; state: 'cancel' }>(`/orders/${id}/cancel`, 'POST');

/** Reset cancelled order back to draft */
export const draftOrder     = (id: number) =>
  call<{ id: number; state: OrderState }>(`/orders/${id}/draft`, 'POST');

// ============================================================
// 10. WHATSAPP
// ============================================================

export const sendWhatsApp      = (id: number) =>
  call<{ message_id: number }>(`/orders/${id}/send_whatsapp`, 'POST');

export const sendWhatsAppImage = (id: number) =>
  call<{ message_id: number }>(`/orders/${id}/send_whatsapp_image`, 'POST');

// ============================================================
// 11. PDF REPORT
// ============================================================

/**
 * Get PDF report URL (for <a href> or window.open)
 * The URL already includes the auth header via Bearer.
 * For direct download use fetchOrderReport() below.
 */
export const orderReportUrl = (id: number, download = true) =>
  `${BASE_URL}/orders/${id}/report?download=${download}`;

/** Fetch PDF as a Blob (for programmatic handling) */
export const fetchOrderReport = async (id: number): Promise<Blob> => {
  const res = await fetch(`${BASE_URL}/orders/${id}/report`, {
    headers: { Authorization: `Bearer ${API_KEY}` },
  });
  return res.blob();
};

// ============================================================
// 12. SAP
// ============================================================

export const syncSap = (id: number) =>
  call<SapSyncResult>(`/orders/${id}/sync_sap`, 'POST');

// ============================================================
// 13. EXCHANGE RATE ON ORDER
// ============================================================

export const updateOrderExchangeRate = (id: number, exchange_rate?: number) =>
  call<ExchangeRateResult>(
    `/orders/${id}/exchange_rate`, 'PUT',
    exchange_rate !== undefined ? { exchange_rate } : {}
  );

// ============================================================
// 14. CONVENIENCE LISTS
// ============================================================

export const listPricelists = () =>
  call<{ items: (Pricelist & { currency_name: string })[]; total: number }>(
    '/pricelists'
  );

export const listWarehouses = () =>
  call<{ items: Warehouse[]; total: number }>('/warehouses');

// ── Export grouped namespace ─────────────────────────────────
const api = {
  getSession,
  getSetup,
  getSettings, updateSettings,
  listCustomers, getCustomer, createCustomer, updateCustomer,
  listProducts, getProduct, getProductData, getUomPrice,
  listOrders, createOrder,
  getOrder, updateOrder, deleteOrder,
  addOrderLine, updateOrderLine, deleteOrderLine,
  confirmOrder, quotationOrder, cancelOrder, draftOrder,
  sendWhatsApp, sendWhatsAppImage,
  orderReportUrl, fetchOrderReport,
  syncSap,
  updateOrderExchangeRate,
  listPricelists, listWarehouses,
};

export default api;
```

---

## All Endpoints Reference

### Base URL: `http://localhost:8070/api/pos_perfume/v1`

| # | Method | Endpoint | Service Function | Description |
|---|--------|----------|-----------------|-------------|
| 1 | GET | `/session` | `getSession()` | Current user info |
| 2 | GET | `/setup` | `getSetup()` | All POS boot data |
| 3 | GET | `/settings` | `getSettings()` | Exchange rate |
| 4 | PUT | `/settings` | `updateSettings(rate)` | Update exchange rate |
| 5 | GET | `/customers` | `listCustomers(params)` | Search customers |
| 6 | GET | `/customers/:id` | `getCustomer(id)` | Get customer |
| 7 | POST | `/customers` | `createCustomer(body)` | Create customer |
| 8 | PUT | `/customers/:id` | `updateCustomer(id, body)` | Update customer |
| 9 | GET | `/products` | `listProducts(params)` | Search products |
| 10 | GET | `/products/:id` | `getProduct(id, plId?)` | Product + UoMs + stock |
| 11 | POST | `/products/data` | `getProductData(body)` | Full product data |
| 12 | POST | `/products/uom_price` | `getUomPrice(body)` | Price for UoM |
| 13 | GET | `/orders` | `listOrders(params)` | List orders (lightweight) |
| 14 | POST | `/orders` | `createOrder(body)` | Create order |
| 15 | GET | `/orders/:id` | `getOrder(id)` | Full order + lines |
| 16 | PUT | `/orders/:id` | `updateOrder(id, body)` | Update header |
| 17 | DELETE | `/orders/:id` | `deleteOrder(id)` | Cancel order |
| 18 | POST | `/orders/:id/lines` | `addOrderLine(oid, body)` | Add line |
| 19 | PUT | `/orders/:id/lines/:lid` | `updateOrderLine(oid, lid, body)` | Update line |
| 20 | DELETE | `/orders/:id/lines/:lid` | `deleteOrderLine(oid, lid)` | Delete line |
| 21 | POST | `/orders/:id/confirm` | `confirmOrder(id)` | Confirm → SAP |
| 22 | POST | `/orders/:id/quotation` | `quotationOrder(id)` | Set quotation |
| 23 | POST | `/orders/:id/cancel` | `cancelOrder(id)` | Cancel |
| 24 | POST | `/orders/:id/draft` | `draftOrder(id)` | Reset to draft |
| 25 | POST | `/orders/:id/send_whatsapp` | `sendWhatsApp(id)` | WhatsApp text |
| 26 | POST | `/orders/:id/send_whatsapp_image` | `sendWhatsAppImage(id)` | WhatsApp image |
| 27 | GET | `/orders/:id/report` | `orderReportUrl(id)` / `fetchOrderReport(id)` | PDF |
| 28 | POST | `/orders/:id/sync_sap` | `syncSap(id)` | Re-sync SAP |
| 29 | PUT | `/orders/:id/exchange_rate` | `updateOrderExchangeRate(id, rate)` | Update rate |
| 30 | GET | `/pricelists` | `listPricelists()` | All pricelists |
| 31 | GET | `/warehouses` | `listWarehouses()` | All warehouses |

---

## Order State Machine

```
           ┌──────────────────────────────────────────────┐
           │                                              │
    ┌──────▼──────┐   quotationOrder()   ┌─────────────┐ │
    │    draft    │ ──────────────────►  │  quotation  │ │
    └──────┬──────┘                      └──────┬──────┘ │
           │                                    │        │
           │  confirmOrder()          confirmOrder()     │
           │                                    │        │
           ▼                                    ▼        │
    ┌─────────────┐                      ┌────────────┐  │
    │    sale     │◄─────────────────────│    sale    │  │
    └──────┬──────┘                      └─────┬──────┘  │
           │                                   │         │
           │  (manual)                         │         │
           ▼                                   ▼         │
    ┌─────────────┐                     ┌────────────┐   │
    │    done     │                     │   cancel   │───┘
    └─────────────┘                     └────────────┘
                                          draftOrder() ──► draft
```

**Rules:**
- `done` → cannot be changed
- `cancel` → only `draftOrder()` can revert it to `draft`
- Lines can only be edited in `draft` or `quotation` state

---

## Invoice Types

| Key | Label |
|-----|-------|
| `"1"` | زبون محل |
| `"2"` | شركات توصيل |
| `"3"` | نقليات |
| `"4"` | ديلفري |
| `"5"` | NBS |
| `"6"` | شورجة |
| `"7"` | NA |
| `"8"` | مكاتب الشورجة |

---

## Complete POS Workflow Example

```ts
import api from './services/posPerfumeApi';

async function runFullPosWorkflow() {

  // ── Step 1: Boot ─────────────────────────────────────────
  const setup = await api.getSetup();
  const { pricelists, warehouses, exchange_rate } = setup.data;
  const defaultPricelistId = setup.data.default_pricelist_id;

  // ── Step 2: Search customer ──────────────────────────────
  const customers = await api.listCustomers({ query: 'Ahmed', limit: 10 });
  const customer = customers.data.items[0];

  // ── Step 3: Create new customer if not found ─────────────
  const newCustomer = await api.createCustomer({
    name: 'Ali Hassan',
    phone: '07701234567',
    mobile: '07901234567',
  });

  // ── Step 4: Search products ──────────────────────────────
  const products = await api.listProducts({
    query: 'oud',
    pricelist_id: defaultPricelistId,
    limit: 20,
  });

  // ── Step 5: Get full product data (UoMs + prices + stock) ─
  const productData = await api.getProductData({
    product_id:   products.data.items[0].id,
    pricelist_id: defaultPricelistId,
  });
  const { available_uoms, warehouses: productWarehouses } = productData.data;

  // ── Step 6: Get price when user changes UoM ──────────────
  const uomPrice = await api.getUomPrice({
    product_id:   products.data.items[0].id,
    pricelist_id: defaultPricelistId,
    uom_id:       available_uoms[1].id,
  });
  console.log('New price:', uomPrice.data.price_unit);

  // ── Step 7: Create order ─────────────────────────────────
  const order = await api.createOrder({
    partner_id:   customer.id,
    pricelist_id: defaultPricelistId,
    invoice_type: '1',
    note:         'Cash customer',
    order_lines: [
      {
        product_id:    products.data.items[0].id,
        product_uom_id: available_uoms[0].id,
        warehouse_id:  productWarehouses[0].id,
        quantity:      2,
        unit_price:    available_uoms[0].price,
        discount_percent: 0,
      }
    ]
  });
  const orderId = order.data.id;

  // ── Step 8: Add another line ─────────────────────────────
  await api.addOrderLine(orderId, {
    product_id:   products.data.items[1].id,
    warehouse_id: warehouses[0].id,
    quantity:     1,
    unit_price:   35.0,
  });

  // ── Step 9: Update a line ────────────────────────────────
  const lineId = order.data.order_lines[0].id;
  await api.updateOrderLine(orderId, lineId, {
    quantity:      3,
    discount_percent: 5,
    custom_product_name: 'Premium Oud',
  });

  // ── Step 10: Update order header ─────────────────────────
  await api.updateOrder(orderId, {
    invoice_type:  '2',
    exchange_rate: 1490,
    note:          'Updated note',
  });

  // ── Step 11: Confirm → sale.order + SAP ──────────────────
  const confirmed = await api.confirmOrder(orderId);
  if (confirmed.data.sap_synced) {
    console.log('SAP Doc:', confirmed.data.sap_doc_num);
  } else {
    // Manual re-sync if needed
    const sap = await api.syncSap(orderId);
    console.log('SAP sync:', sap.data.sap_synced);
  }

  // ── Step 12: Print PDF ───────────────────────────────────
  const pdfBlob = await api.fetchOrderReport(orderId);
  const pdfUrl  = URL.createObjectURL(pdfBlob);
  window.open(pdfUrl);

  // ── Step 13: Send WhatsApp ───────────────────────────────
  await api.sendWhatsApp(orderId);
}
```

---

## React Hooks Example

```tsx
// src/hooks/usePosSetup.ts
import { useState, useEffect } from 'react';
import api from '../services/posPerfumeApi';
import type { PosSetup } from '../types/pos';

export function usePosSetup() {
  const [setup, setSetup]     = useState<PosSetup | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    api.getSetup()
      .then(res => {
        if (res.success) setSetup(res.data);
        else setError(res.error ?? 'Failed to load setup');
      })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { setup, loading, error };
}
```

```tsx
// src/hooks/useProductSearch.ts
import { useState, useCallback } from 'react';
import api from '../services/posPerfumeApi';
import type { Product } from '../types/pos';

export function useProductSearch(pricelistId: number) {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading]   = useState(false);

  const search = useCallback(async (query: string) => {
    setLoading(true);
    const res = await api.listProducts({ query, pricelist_id: pricelistId, limit: 50 });
    if (res.success) setProducts(res.data.items);
    setLoading(false);
  }, [pricelistId]);

  return { products, loading, search };
}
```

```tsx
// src/hooks/useOrder.ts
import { useState } from 'react';
import api from '../services/posPerfumeApi';
import type { Order, CreateOrderBody, CreateOrderLineBody } from '../types/pos';

export function useOrder() {
  const [order, setOrder]     = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  const createOrder = async (body: CreateOrderBody) => {
    setLoading(true);
    const res = await api.createOrder(body);
    if (res.success) setOrder(res.data);
    else setError(res.error ?? 'Failed to create order');
    setLoading(false);
    return res;
  };

  const addLine = async (lineBody: CreateOrderLineBody) => {
    if (!order) return;
    setLoading(true);
    const res = await api.addOrderLine(order.id, lineBody);
    if (res.success) {
      // Refresh full order to get updated totals
      const refreshed = await api.getOrder(order.id);
      if (refreshed.success) setOrder(refreshed.data);
    } else {
      setError(res.error ?? 'Failed to add line');
    }
    setLoading(false);
    return res;
  };

  const confirm = async () => {
    if (!order) return;
    setLoading(true);
    const res = await api.confirmOrder(order.id);
    if (res.success) {
      const refreshed = await api.getOrder(order.id);
      if (refreshed.success) setOrder(refreshed.data);
    } else {
      setError(res.error ?? 'Failed to confirm order');
    }
    setLoading(false);
    return res;
  };

  return { order, loading, error, createOrder, addLine, confirm };
}
```

---

## Error Handling Pattern

```ts
async function safeApiCall<T>(fn: () => Promise<ApiResponse<T>>): Promise<T | null> {
  try {
    const res = await fn();
    if (!res.success) {
      // Show toast/notification
      console.error('[API Error]', res.error);
      return null;
    }
    return res.data;
  } catch (err) {
    // Network error
    console.error('[Network Error]', err);
    return null;
  }
}

// Usage:
const order = await safeApiCall(() => api.getOrder(123));
if (order) {
  console.log('Order:', order.name);
}
```

---

## Pagination Pattern

```ts
async function loadAllOrders(state: OrderState = 'sale') {
  const PAGE_SIZE = 50;
  let offset = 0;
  let allOrders: OrderSummary[] = [];

  while (true) {
    const res = await api.listOrders({ state, limit: PAGE_SIZE, offset });
    if (!res.success) break;

    allOrders = [...allOrders, ...res.data.items];

    if (allOrders.length >= res.data.total) break;
    offset += PAGE_SIZE;
  }

  return allOrders;
}
```

---

## Notes for Frontend Developers

| Topic | Detail |
|-------|--------|
| **IQD calculation** | `amount_total_iqd = amount_total × exchange_rate` (done server-side) |
| **PDF download** | Use `fetchOrderReport()` for Blob, or open `orderReportUrl()` in new tab |
| **Order lines** | Always refresh full order after adding/updating lines to get new totals |
| **SAP sync** | Happens automatically on `confirmOrder()` — check `sap_synced` in response |
| **Custom name** | `custom_product_name` on order line overrides product name in invoice/SAP |
| **Pricelist** | If omitted on create, server uses "Price list 1" as default |
| **UoM default** | If `product_uom_id` omitted on line create, uses product's base UoM |
| **Warehouse location** | If `location_id` omitted, uses warehouse's main stock location |
| **CORS** | All endpoints allow `*` — no proxy needed in dev |
| **Stateless** | API Key auth is stateless — no session management needed |
