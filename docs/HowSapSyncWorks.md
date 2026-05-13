# How SAP ↔ Odoo Sync Works
**A complete reference for backend developers**

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture Diagram](#2-architecture-diagram)
3. [SAP Service Layer — What It Is](#3-sap-service-layer--what-it-is)
4. [How Authentication Works](#4-how-authentication-works)
5. [The Database — What Lives Where](#5-the-database--what-lives-where)
6. [Sync Direction — SAP → Odoo Only](#6-sync-direction--sap--odoo-only)
7. [The Six Scheduled Jobs (Crons)](#7-the-six-scheduled-jobs-crons)
8. [The 2-Minute Realtime Sync — Deep Dive](#8-the-2-minute-realtime-sync--deep-dive)
9. [The Daily Full Sync](#9-the-daily-full-sync)
10. [The Commercial Flags Sync (Every 6 Hours)](#10-the-commercial-flags-sync-every-6-hours)
11. [The Exchange Rate Sync (Every 30 Minutes)](#11-the-exchange-rate-sync-every-30-minutes)
12. [Key Odoo Models and Their Roles](#12-key-odoo-models-and-their-roles)
13. [Key Database Tables](#13-key-database-tables)
14. [How Products Are Matched Between SAP and Odoo](#14-how-products-are-matched-between-sap-and-odoo)
15. [How Stock (Warehouse Quantities) Are Synced](#15-how-stock-warehouse-quantities-are-synced)
16. [How Prices Are Synced](#16-how-prices-are-synced)
17. [How Customers Are Synced](#17-how-customers-are-synced)
18. [How the Exchange Rate Is Synced](#18-how-the-exchange-rate-is-synced)
19. [Known Gap — The Stock Sync Blind Spot](#19-known-gap--the-stock-sync-blind-spot)
20. [Proposed Fix for the Stock Blind Spot](#20-proposed-fix-for-the-stock-blind-spot)
21. [SAP OData Quirks You Must Know](#21-sap-odata-quirks-you-must-know)
22. [How to Debug a Sync Issue](#22-how-to-debug-a-sync-issue)
23. [Important Config Values](#23-important-config-values)
24. [Glossary](#24-glossary)

---

## 1. System Overview

This system is an **Odoo 19** installation that integrates with **SAP Business One** (SAP B1).

- **SAP B1** is the source of truth for: products, prices, warehouse stock, customers, and the IQD/USD exchange rate.
- **Odoo** is the operational platform for: POS sales, CRM, supply chain operations, and order management.
- Sync is **one-directional in most areas**: SAP → Odoo. Odoo does not write back to SAP automatically except for specific configured actions (quotation export, order export — currently not in active use).
- The SAP server is at `https://192.168.15.50:50000/b1s/v1` (internal network).
- The Odoo database is `nbs_lugalai` (PostgreSQL, user `odoo_user`, password in `odoo_simple.conf`).

---

## 2. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        SAP Business One                          │
│                                                                  │
│  Items (products)    ItemWarehouseInfoCollection (stock)         │
│  ItemPrices          BusinessPartners (customers)                │
│  GoodsReceipts       InventoryGenEntries  StockTransfers         │
│  DocRate (IQD rate)  Quotations           Orders                 │
│                                                                  │
│           ↑↓  SAP B1 Service Layer (OData REST API)             │
│           https://192.168.15.50:50000/b1s/v1                    │
└─────────────────────────────────────────────────────────────────┘
         ↓ (pulled every 2 min / 6h / 30 min / 1 day)
┌─────────────────────────────────────────────────────────────────┐
│                    sap_integration Odoo Addon                    │
│                                                                  │
│  sap.backend          → connection config + session management   │
│  sap.realtime.sync    → 2-min delta cron (main workhorse)        │
│  sap.auto.sync        → daily full sync + 6h commercial flags    │
│  sap.exchange.rate.sync → 30-min IQD/USD rate                   │
│  sap.product.warehouse.info → per-warehouse stock mirror        │
│  sap.product.pricelist.sync → pricelist management              │
└─────────────────────────────────────────────────────────────────┘
         ↓ (writes to)
┌─────────────────────────────────────────────────────────────────┐
│                    Odoo / PostgreSQL (nbs_lugalai)               │
│                                                                  │
│  product.product / product.template  (SAP Items)                │
│  product.pricelist / product.pricelist.item  (SAP prices)       │
│  stock.quant  (actual quantities Odoo uses)                     │
│  sap.product.warehouse.info  (SAP stock mirror per warehouse)   │
│  res.partner  (SAP BusinessPartners)                            │
│  res.currency.rate  (IQD/USD rate)                              │
│  ir.config_parameter  (pos_perfume.default_exchange_rate...)    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. SAP Service Layer — What It Is

SAP B1 exposes its data via an **OData v4 REST API** called the **Service Layer**, running on port `50000`. Every request is HTTP/HTTPS JSON.

Key endpoints used by this integration:

| Endpoint | What it returns |
|----------|----------------|
| `POST /Login` | Authenticate, get `SessionId` cookie |
| `GET /Items` | Product master records |
| `GET /Items('{code}')` | Single product by ItemCode |
| `GET /ItemWarehouseInfoCollection` | Per-warehouse stock for items |
| `GET /ItemPrices` | Price lists per item |
| `GET /BusinessPartners` | Customers and suppliers |
| `GET /GoodsReceipts` | Inbound stock documents |
| `GET /InventoryGenEntries` | Manual inventory adjustment documents |
| `GET /StockTransfers` | Warehouse-to-warehouse transfers |
| `GET /GoodsIssues` | Stock consumption documents |
| `GET /Deliveries` | Sales delivery documents |

All list queries support OData filter syntax:
```
$filter=UpdateDate gt datetime'2026-05-01T00:00:00'
$top=500
$skip=0
$select=ItemCode,ItemName
```

**Important SAP limitation**: `$expand` (joining related data inline) is often not supported or returns 400 errors. When you need nested data (e.g. ItemPrices inside Items), you must make a separate request.

---

## 4. How Authentication Works

File: `addons/sap_integration/models/sap_service_layer.py`

1. On first use, Odoo POSTs credentials to `/b1s/v1/Login`:
   ```json
   { "UserName": "...", "Password": "...", "CompanyDB": "..." }
   ```
2. SAP returns a `SessionId` cookie. This session lives for ~30 minutes.
3. A connection pool (`_connection_pool`) caches the session object for up to 5 minutes (300 seconds) to avoid re-authenticating every 2-minute cron run.
4. If a request returns 401, the session is automatically renewed.
5. SAP B1 uses legacy TLS cipher suites incompatible with OpenSSL 3+. A custom `_LegacyTLSAdapter` is mounted that lowers TLS security level to `SECLEVEL=1` — this is expected and necessary for this SAP version.
6. SSL certificate verification is **disabled** (`verify_ssl = False`) because SAP uses a self-signed certificate on the internal network.

**Retry logic**: Authentication attempts up to 3 times with a 2-second delay between attempts.

---

## 5. The Database — What Lives Where

### Odoo side (source of truth for operations)

| Table | What it stores |
|-------|---------------|
| `product_template` | Product master (name, category, flags, list_price) |
| `product_product` | Product variants (`default_code` = SAP `ItemCode`) |
| `product_pricelist` | Named pricelists (e.g. "SAP Price List 1") |
| `product_pricelist_item` | Individual price rows per product per pricelist |
| `stock_quant` | **Actual stock quantities Odoo uses** (location-based) |
| `stock_location` | Physical locations (warehouses, shelves, etc.) |
| `stock_warehouse` | Warehouse records |
| `res_partner` | Customers/suppliers (`ref` field = SAP `CardCode`) |
| `res_currency_rate` | Currency exchange rates |
| `ir_config_parameter` | Key-value system settings |

### SAP mirror side (sync metadata, not authoritative for operations)

| Table | What it stores |
|-------|---------------|
| `sap_product_warehouse_info` | SAP warehouse quantities mirrored per product per warehouse, with `last_sync_date` |
| `sap_realtime_sync` | Realtime sync config + last run status + logs |
| `sap_auto_sync` | Daily full sync config |
| `sap_exchange_rate_sync` | Exchange rate sync config + last fetched rate |
| `sap_backend` | SAP connection config (URL, credentials, SSL settings) |
| `sap_sync_log` | Per-operation sync audit log |
| `sap_warehouse` | SAP warehouse ↔ Odoo warehouse mapping |

---

## 6. Sync Direction — SAP → Odoo Only

The system is designed **SAP → Odoo** for the following data:

| Data | Direction | Frequency |
|------|-----------|-----------|
| Product master (name, flags, UoM) | SAP → Odoo | Every 2 min (delta) + daily (full) |
| Prices (ItemPrices) | SAP → Odoo | Every 2 min (delta) |
| Warehouse stock quantities | SAP → Odoo | Every 2 min (delta) — **see known gap** |
| Customers (BusinessPartners) | SAP → Odoo | Every 2 min (delta) |
| IQD/USD exchange rate | SAP → Odoo | Every 30 min |
| Commercial flags (sale_ok, POS) | SAP → Odoo | Every 6 hours |

**Odoo → SAP** (configured but verify active state before using):
- Quotation export to SAP Quotations
- Sale order export to SAP Orders
- New partner auto-export (flag: `auto_export_partners` on `sap.backend`)

---

## 7. The Six Scheduled Jobs (Crons)

All defined in `addons/sap_integration/data/sap_cron_data.xml`.

| Cron Name | Interval | Model | Method | Priority |
|-----------|----------|-------|--------|---------|
| SAP Realtime Sync | **Every 2 min** | `sap.realtime.sync` | `cron_run_fast_sync()` | 10 |
| SAP Commercial Flags Sync | Every 6 hours | `sap.auto.sync` | `run_commercial_flags_sync()` | 15 |
| SAP Exchange Rate Sync | Every 30 min | `sap.exchange.rate.sync` | `cron_sync_exchange_rate()` | 10 |
| SAP Daily Auto-Sync | Every 1 day at 2 AM | `sap.auto.sync` | `run_daily_sync()` | 5 |
| SAP Alert Check | Every 5 min | `sap.alert.rule` | `check_all_rules()` | — |
| SAP Performance Cleanup | Every 1 day | `sap.performance.metrics` | (inline delete) | — |
| SAP Sync Log Cleanup | Every 1 day | `sap.sync.log` | `cleanup_old_logs(days=30)` | — |
| SAP Health Check | Every 1 hour | `sap.dashboard.enhanced` | `run_health_check()` | — |

**Total runs of the realtime cron as of 2026-05-13:** 37,612 (healthy, running every 2 minutes without gaps).

---

## 8. The 2-Minute Realtime Sync — Deep Dive

File: `addons/sap_integration/models/sap_realtime_sync.py`

This is the **main workhorse**. It runs every 2 minutes and syncs only what changed since the last run.

### How it decides what changed

It uses a **delta window** approach with a 30-second overlap buffer:

```
since_dt = last_sync_at - 30 seconds
```

On first ever run (no `last_sync_at`), it goes back 24 hours.

### Step 1 — Fetch changed Items from SAP

Two parallel OData queries are made and their results merged:

**Query A — Items where `UpdateDate/UpdateTime` changed:**
```
GET /Items?$filter=(UpdateDate gt datetime'YYYY-MM-DDT00:00:00')
          or (UpdateDate eq datetime'YYYY-MM-DDT00:00:00' and UpdateTime ge 'HH:MM:SS')
&$top=500
```

**Query B — Items created since since_dt:**
```
GET /Items?$filter=CreateDate ge datetime'YYYY-MM-DDT00:00:00'
&$top=500
```

Both queries paginate in batches of 500 using `$skip`. Results are merged and deduplicated by `ItemCode`.

Why two queries? SAP does not always update `UpdateDate` when a new item is created. The dual query ensures newly added items are not missed.

### Step 2 — Fetch changed BusinessPartners from SAP

Same `UpdateDate` + `CreateDate` dual-query logic against `/BusinessPartners`.

### Step 3 — For each changed item, sync 4 things

| Sub-step | What it does | SAP Endpoint |
|----------|-------------|-------------|
| `_sync_product_data()` | Upsert product name, sale_ok, active, available_in_pos | Uses data already in Items response |
| `_sync_prices()` | Update pricelist items from `ItemPrices` | Refetches single item if ItemPrices missing |
| `_sync_stock()` | Update per-warehouse quantities from `ItemWarehouseInfoCollection` | Uses data already in Items response |
| `_sync_barcodes()` | Update alternative barcodes from `ItemBarCodeCollection` | Refetches single item individually |

### Step 4 — For each changed BusinessPartner

`_sync_customers()` creates or updates `res.partner` matched by `ref = CardCode`.

### Step 5 — Record the result

Writes `last_sync_at`, `last_sync_status`, `last_sync_log`, `last_items_changed`, `total_runs` to the `sap.realtime.sync` record. Commits after each full run.

### What a successful log entry looks like

```
Delta sync from: 2026-05-13 08:26:00
Changed items found in SAP: 24
Changed BusinessPartners found in SAP: 6
  Products updated: 0
  Price records updated: 48
  Stock records updated: 432
  Customers updated: 0
```

---

## 9. The Daily Full Sync

File: `addons/sap_integration/models/sap_auto_sync.py`, method `run_daily_sync()`

Runs at 2:00 AM every day. Calls `execute_sync()` for each active `sap.auto.sync` config record.

**Stages:**
1. **UoM Groups** (if `sync_uom_groups = True`) — imports SAP unit-of-measure group definitions
2. **Products** (if `sync_products = True`) — full product import via `sap.product.complete.migration` wizard
3. **Pricelists** (if `sync_pricelists = True`) — full pricelist import via `sap.product.pricelist.sync`
4. **Warehouse Info** (if `sync_warehouse = True`) — full per-warehouse stock refresh

This is a safety net for anything the 2-minute delta might have missed. It is slower and heavier but ensures full consistency at least once a day.

---

## 10. The Commercial Flags Sync (Every 6 Hours)

File: `addons/sap_integration/models/sap_auto_sync.py`, method `run_commercial_flags_sync()`

Specifically syncs these SAP Item flags to Odoo product fields:

| SAP Field | Odoo Field | Meaning |
|-----------|-----------|---------|
| `Frozen = tYES` | `active = False` | Item is frozen in SAP → archived in Odoo |
| `Valid = tNO` | `active = False` | Item cancelled in SAP → archived in Odoo |
| `SalesItem = tYES` | `sale_ok = True`, `available_in_pos = True` | Sellable in SAP → visible in Odoo Sales + POS |
| `SalesItem = tNO` | `sale_ok = False`, `available_in_pos = False` | Not sellable in SAP → hidden in Odoo |
| `PurchaseItem = tYES` | `purchase_ok = True` | Purchasable in SAP |

Config option `force_enable_sales_pos = True` overrides the SAP `SalesItem` check and forces all active items to be sale_ok and POS-visible (useful if SAP has incorrect SalesItem flags).

Config option `deactivate_odoo_not_in_sap = True` archives any Odoo product whose `default_code` is not found in SAP — **use with caution**, this will archive products created locally in Odoo.

---

## 11. The Exchange Rate Sync (Every 30 Minutes)

File: `addons/sap_integration/models/sap_exchange_rate_sync.py`

Pulls the IQD/USD rate from SAP by reading `DocRate` from the most recent IQD-denominated document. Writes it to two places:

1. **`ir.config_parameter`** key `pos_perfume.default_exchange_rate_usd_iqd` — used by POS Perfume module
2. **`res.currency.rate`** — Odoo's standard accounting exchange rate for IQD

Sanity bounds: rate must be between 100 and 10,000. If SAP returns a value outside this range, it is rejected and the fallback rate (1560.0) is used.

---

## 12. Key Odoo Models and Their Roles

| Model | `_name` | Role in SAP sync |
|-------|---------|-----------------|
| SAP Backend | `sap.backend` | Holds connection URL, credentials, SSL settings. Call `backend.get_connection()` to get an authenticated session. |
| Realtime Sync Config | `sap.realtime.sync` | One record per backend. Tracks `last_sync_at`, logs, run counts. The 2-min cron iterates all active records. |
| Auto Sync Config | `sap.auto.sync` | Daily full sync settings per backend. |
| Warehouse Info | `sap.product.warehouse.info` | Per-product per-warehouse mirror of SAP quantities. One row per (product, warehouse, backend) combination. |
| Pricelist Sync | `sap.product.pricelist.sync` | Manages creation and update of Odoo pricelists from SAP `ItemPrices`. |
| Exchange Rate Sync | `sap.exchange.rate.sync` | Tracks last fetched IQD/USD rate. |
| Product Extended | `sap.product.extended` | Additional SAP-specific product metadata (brand, dimensions, SAP ItemCode cross-ref). |

---

## 13. Key Database Tables

### `sap_product_warehouse_info`

The most important table for stock sync. Columns you will use frequently:

| Column | Meaning |
|--------|---------|
| `product_code` | SAP ItemCode (denormalized from `product_product.default_code`) |
| `sap_warehouse_code` | SAP warehouse number (e.g. `'01'`, `'18'`) |
| `last_in_stock` | Quantity in stock as of last SAP sync |
| `last_committed` | Committed (reserved) quantity from SAP |
| `last_available` | `last_in_stock - last_committed` (computed) |
| `last_sync_date` | When this row was last updated from SAP |
| `write_date` | When Odoo last wrote this row |
| `sync_status` | `'synced'` / `'pending'` / `'error'` |

**Important**: This table is a **mirror**. The quantities Odoo actually uses for order allocation are in `stock.quant`, not here. This table is for reporting and the FE to show SAP warehouse breakdown.

### `sap_realtime_sync`

| Column | Meaning |
|--------|---------|
| `last_sync_at` | Timestamp of last successful run |
| `last_sync_status` | `'success'` / `'failed'` / `'running'` |
| `last_sync_log` | Full text log of last run |
| `last_items_changed` | How many records were changed in last run |
| `total_runs` | Lifetime run count (healthy = tens of thousands) |
| `total_errors` | Lifetime error count |

---

## 14. How Products Are Matched Between SAP and Odoo

**Match key**: `product_product.default_code` = SAP `ItemCode`

This is the **only** match key. If a product in Odoo has `default_code = 'G00087'` it is the same product as SAP `ItemCode = 'G00087'`.

When the realtime sync encounters a SAP item:
1. It searches `product_product` for `default_code = ItemCode`
2. If found → **update** the existing product
3. If not found and `auto_create_products = True` → **create** a new product template + variant
4. If not found and `auto_create_products = False` → **skip**

New products are created as `type = 'consu'` (Consumable / Storable) with `is_storable = True`.

---

## 15. How Stock (Warehouse Quantities) Are Synced

### What SAP provides

SAP's `Items` response includes `ItemWarehouseInfoCollection`, an array like:
```json
[
  { "WarehouseCode": "01", "InStock": 15.0, "Committed": 2.0, "Ordered": 0.0 },
  { "WarehouseCode": "18", "InStock": 8.5, "Committed": 0.0, "Ordered": 3.0 }
]
```

### What `_sync_stock()` does

For each changed item, it passes `ItemWarehouseInfoCollection` to `sap.product.warehouse.info.sync_warehouse_info_from_sap()`, which:
1. Creates or updates one `sap_product_warehouse_info` row per warehouse per product
2. Writes `last_in_stock`, `last_committed`, `last_available`, `last_sync_date`
3. Also creates or updates an Odoo `stock.quant` for each warehouse location

### The critical gap (see section 19)

`_sync_stock()` only runs for items that appeared in `_fetch_changed_items()` — items whose SAP `UpdateDate` changed. If warehouse quantities change via a goods receipt or inventory adjustment, SAP updates the stock but **does not change `UpdateDate` on the item master record**. Those stock changes are invisible to the 2-minute delta cron.

---

## 16. How Prices Are Synced

SAP provides `ItemPrices` inside the Items response — but in bulk queries this array is often empty. The sync detects this and re-fetches the single item individually:

```
GET /Items?$filter=ItemCode eq 'G00087'&$top=1
```

The `ItemPrices` array contains one entry per SAP price list:
```json
[
  { "PriceList": 1, "Price": 85.0, "Currency": "IQD" },
  { "PriceList": 2, "Price": 0.0, "Currency": "IQD" }
]
```

`sap.product.pricelist.sync.sync_product_prices_from_sap()` maps these to Odoo `product.pricelist.item` rows.

Odoo pricelists are named "SAP Price List 1", "SAP Price List 2", etc., created automatically on first import.

---

## 17. How Customers Are Synced

**Match key**: `res.partner.ref` = SAP `CardCode`

The `_sync_customers()` method:
1. Searches `res.partner` for `ref = CardCode`
2. If found → updates name, email, phone, address, city, zip, country if changed
3. If not found and `auto_create_customers = True` → creates new partner with `customer_rank = 1`

Only customers (`CardType = 'cCustomer'`) are created. Suppliers are fetched but treated differently.

---

## 18. How the Exchange Rate Is Synced

The cron calls `cron_sync_exchange_rate()` every 30 minutes. It:
1. Queries the most recent IQD document from SAP to read `DocRate`
2. Validates: must be between 100 and 10,000
3. Writes to `ir.config_parameter` (for POS use)
4. Writes to `res.currency.rate` (for accounting use)
5. Logs the rate and change delta

Fallback rate: **1560 IQD/USD** (used when SAP is unreachable).

---

## 19. Known Gap — The Stock Sync Blind Spot

### The problem

The 2-minute realtime sync uses `Items.UpdateDate` as its change detector. SAP only updates `Items.UpdateDate` when the **item master record itself changes** (name, flags, UoM, etc.).

When stock moves via these SAP documents, the warehouse quantities change but `Items.UpdateDate` does **not** update:

| SAP Document | Moves stock? | Updates Items.UpdateDate? |
|-------------|------------|--------------------------|
| GoodsReceipts | ✅ Yes | ❌ No |
| InventoryGenEntries | ✅ Yes | ❌ No |
| StockTransfers | ✅ Yes | ❌ No |
| GoodsIssues | ✅ Yes | ❌ No |
| Deliveries | ✅ Yes | ❌ No |
| Returns | ✅ Yes | ❌ No |

**Result**: If a warehouse operator in SAP does a goods receipt for G00087 into warehouse 01 and 18, the stock appears in SAP immediately, but Odoo's `sap_product_warehouse_info` and `stock_quant` will **not update** until the next daily full sync at 2 AM (or until the item master itself is edited in SAP for another reason).

### Real example observed (2026-05-13)

Product G00087 (جادور, 1 كغم):
- SAP shows stock in warehouse 01 and warehouse 18
- Odoo `sap_product_warehouse_info` shows 0.00 for all 18 warehouses
- Last sync date for G00087: **2026-04-27** (16 days stale)
- The 2-min cron ran successfully 37,612+ times but never picked up G00087 because its `Items.UpdateDate` stayed at April 27

---

## 20. Proposed Fix for the Stock Blind Spot

### The wrong approach (do not use)

Simply querying `GoodsReceipts` and `InventoryGenEntries` by `DocDate` has four problems:
1. **`DocDate` is user-entered** — operators can backdate documents. A receipt posted today with `DocDate = last week` would be missed.
2. **`ItemCode` is in document lines**, not the header — `$select=ItemCode` returns nothing. You must parse `DocumentLines[].ItemCode`.
3. **Only covers 2 of 6+ stock movement types** — misses StockTransfers, GoodsIssues, Deliveries, Returns.
4. **`DocTime` is not reliably filterable** in all SAP B1 Service Layer versions.

### The correct approach (recommended)

Add a two-layer fix:

#### Layer 1 (fast, 2-min): Document-delta pass inside existing cron

Add a second step inside `_run_delta_sync()` after `_fetch_changed_items()`:

```python
# NEW: fetch stock movement documents by CreateDate since last sync
stock_item_codes = self._fetch_stock_movement_item_codes(connection, since_dt)

# Merge with changed_items for stock sync
# (items already in changed_items will just be re-synced — safe)
extra_items = self._fetch_warehouse_info_for_codes(connection, stock_item_codes)
all_stock_items = changed_items + extra_items
```

Documents to query:
```
GET /GoodsReceipts?$filter=CreateDate ge datetime'...'     → DocumentLines[].ItemCode
GET /InventoryGenEntries?$filter=CreateDate ge datetime'...'
GET /StockTransfers?$filter=CreateDate ge datetime'...'
GET /GoodsIssues?$filter=CreateDate ge datetime'...'
GET /Deliveries?$filter=CreateDate ge datetime'...'
```

Use `CreateDate` (when SAP created the document) not `DocDate` (user-typed date).

For each document, read `DocumentLines` array and extract `ItemCode` values.

Then for each unique ItemCode found this way, fetch current `ItemWarehouseInfoCollection` and call `_sync_stock()`.

#### Layer 2 (safety net, daily): Stale stock sweep

A separate daily cron that finds all products with `sap_product_warehouse_info.last_sync_date < NOW() - 24h` and force-refreshes their warehouse quantities. This catches anything Layer 1 misses.

---

## 21. SAP OData Quirks You Must Know

These are hard-learned lessons already baked into the existing code:

### 1. `UpdateDate` vs `UpdateTime` — the same-day problem
`UpdateDate` is a date-at-midnight field. If you filter only `UpdateDate eq today AND UpdateTime >= HH:MM`, you miss items updated earlier today on the same calendar day. The correct filter:
```
(UpdateDate gt datetime'DATE_T00:00:00') OR
(UpdateDate eq datetime'DATE_T00:00:00' AND UpdateTime ge 'HH:MM:SS')
```

### 2. `$expand` usually doesn't work
`GET /Items?$expand=ItemPrices` often returns 400. Fetch item prices separately via `GET /Items('CODE')`.

### 3. `$select` with expanded collections fails
Don't combine `$select` and `$expand` — SAP B1 returns 400. Omit `$select` when you need nested collections.

### 4. `ItemPrices` is empty in bulk responses
When fetching multiple items, `ItemPrices` is usually `[]` in the response. The sync code handles this by re-fetching the single item by `ItemCode` when `ItemPrices` is empty.

### 5. `ItemWarehouseInfoCollection` is at the item level
You cannot filter `ItemWarehouseInfoCollection` by `UpdateDate` — there is no such field. You must either fetch it from the item record or query the standalone endpoint:
```
GET /ItemWarehouseInfoCollection?$filter=ItemCode eq 'G00087'
```

### 6. Pagination
SAP limits page size. Always paginate with `$top=500` and `$skip=N` until a page returns fewer than 500 results.

### 7. Legacy TLS
SAP B1 uses old cipher suites. The `_LegacyTLSAdapter` in `sap_service_layer.py` is required. Without it, Python's `requests` library will fail with SSL handshake errors on modern Linux systems.

### 8. Session expiry
SAP sessions expire after ~30 minutes. The connection pool caches for 5 minutes max. If a cron run takes longer than 30 minutes (e.g. full sync), the session may expire mid-run. The code has auto-renew logic for 401 responses.

---

## 22. How to Debug a Sync Issue

### Step 1 — Check if cron is running at all
```sql
SELECT last_sync_at, last_sync_status, last_items_changed, total_runs, total_errors, last_sync_log
FROM sap_realtime_sync;
```
- `last_sync_at` should be within the last 2–3 minutes.
- `total_errors / total_runs` > 5% is a problem.

### Step 2 — Check when a specific product was last synced
```sql
SELECT sap_warehouse_code, last_in_stock, last_available, last_sync_date, write_date
FROM sap_product_warehouse_info
WHERE product_code = 'G00087'
ORDER BY sap_warehouse_code;
```

### Step 3 — Check if the cron is updating other products (prove cron works)
```sql
SELECT product_code, sap_warehouse_code, last_in_stock, last_sync_date
FROM sap_product_warehouse_info
WHERE sap_warehouse_code = '01'
  AND last_in_stock > 0
  AND last_sync_date >= NOW() - INTERVAL '1 hour'
ORDER BY last_sync_date DESC
LIMIT 10;
```

### Step 4 — Check the last sync log for errors
```sql
SELECT last_sync_log, last_sync_status, last_sync_at FROM sap_realtime_sync;
```

### Step 5 — Check the sync log table for specific product errors
```sql
SELECT external_id, operation, status, error_type, message, create_date
FROM sap_sync_log
WHERE external_id = 'G00087'
ORDER BY create_date DESC LIMIT 10;
```

### Step 6 — If a product is stale, force trigger from Odoo UI
Go to **Settings → Technical → Scheduled Actions → SAP Realtime Sync → Run Manually**.

Or in the SAP Realtime Sync view, click **"Run Now"** button.

To force a full backfill (sync everything from past 24h): click **"Reset Timestamp"** on the sync record, then run manually.

---

## 23. Important Config Values

| Key | Location | Value | Meaning |
|-----|----------|-------|---------|
| SAP Service Layer URL | `sap.backend.base_url` | `https://192.168.15.50:50000/b1s/v1` | SAP server address |
| SAP Company DB | `sap.backend.company_db` | (set in Odoo backend config) | SAP company identifier |
| Odoo DB | `odoo_simple.conf` → `db_name` | `nbs_lugalai` | PostgreSQL database name |
| DB User | `odoo_simple.conf` → `db_user` | `odoo_user` | PostgreSQL username |
| DB Password | `odoo_simple.conf` → `db_password` | `root` | PostgreSQL password |
| DB Host | `odoo_simple.conf` → `db_host` | `localhost` | PostgreSQL host |
| Exchange Rate Fallback | `sap_exchange_rate_sync.py` `_FALLBACK_RATE` | `1560.0` | IQD/USD when SAP unreachable |
| Overlap buffer | `sap_realtime_sync.py` `OVERLAP_SECONDS` | `30` | Seconds subtracted from last_sync_at to avoid clock skew gaps |
| Session pool max age | `sap_service_layer.py` `_pool_max_age` | `300` (5 min) | How long to reuse a SAP session object |
| Session timeout | `sap_config.py` `session_timeout_minutes` | `28` | SAP session considered stale after 28 min |
| Default batch size | `sap_config.py` `default_batch_size` | `100` | Records per batch in full sync |

---

## 24. Glossary

| Term | Meaning |
|------|---------|
| **SAP B1** | SAP Business One — the ERP used as source of truth |
| **Service Layer** | SAP B1's REST/OData API on port 50000 |
| **ItemCode** | SAP's unique product identifier. Maps to `product_product.default_code` in Odoo |
| **CardCode** | SAP's unique customer/supplier identifier. Maps to `res.partner.ref` in Odoo |
| **ItemWarehouseInfoCollection** | SAP's per-warehouse stock data for an item |
| **ItemPrices** | SAP's pricelist prices for an item |
| **UpdateDate/UpdateTime** | When the SAP record (item master) was last modified |
| **CreateDate** | When the SAP record was first created |
| **DocDate** | User-entered date on a SAP document — can be backdated, NOT reliable for delta filtering |
| **Delta sync** | Only fetching records that changed since last run (vs full sync of everything) |
| **Overlap buffer** | Subtracting 30 seconds from `last_sync_at` to catch records that might have been written during the previous run's processing time |
| **sap_product_warehouse_info** | Odoo model mirroring SAP per-warehouse quantities — NOT authoritative for Odoo order allocation |
| **stock.quant** | Odoo's authoritative stock quantity table used for order allocation and POS |
| **Inventory Adjustment location** | A special Odoo stock location used for manual quantity adjustments — stock here is NOT warehouse stock |
| **Commercial flags** | SAP's `SalesItem`, `PurchaseItem`, `Valid`, `Frozen` flags that control product visibility |
| **SalesItem=tYES** | Product is sellable in SAP → `sale_ok=True`, `available_in_pos=True` in Odoo |
| **Frozen=tYES** | Product is frozen in SAP → `active=False` in Odoo (archived) |
| **OData** | Open Data Protocol — REST-based query standard used by SAP Service Layer |
| **`$filter`** | OData query operator to filter records |
| **`$top` / `$skip`** | OData pagination — max records per page / offset |
| **`$select`** | OData field selection — do NOT use with `$expand` in SAP B1 |
| **`$expand`** | OData relationship expansion — often unsupported in SAP B1, avoid |
| **SessionId** | SAP authentication token returned by `/Login`, stored as a cookie, valid ~30 min |
| **SECLEVEL=1** | OpenSSL TLS security level required for SAP B1's legacy cipher suites |
