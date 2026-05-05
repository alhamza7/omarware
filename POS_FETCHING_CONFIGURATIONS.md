# POS Product Fetching — Backend Engineer's Golden Book

> **Audience:** New backend engineers onboarding to the POS + SAP integration.
> **Scope:** Everything you need to understand how POS product lists are fetched, filtered, and served — focused on the SAP ↔ Odoo data layer.

---

## PRIORITY — SAP fetch exceptions: لك · فل بلاستك · 0.25 كغم

> **Read this section first and commit it to memory.** Almost every POS vs SAP count mismatch traces back to how these three SAP UoM groups interact with `sap_uom_group_entry`, `uom_id`, and category-specific rules.

### The three groups (always know these numbers)

| `sap_abs_entry` | Arabic name | Role in POS |
|-----------------|-------------|-------------|
| **2** | **لك** | Standard bulk oils — the usual **1 kg** tab when FE sends `sap_uom_group_entry=2`. |
| **9** | **فل بلاستك** | Plastic / wide-range packaging — many kg SKUs live here instead of لك. |
| **8** | **0.25 كغم** | Quarter-kg oils — **primary Odoo UoM is `33`** (0.25 كغم); used for quarter tabs / `by_primary_sales_uom`. |

---

### Exception rule A — 1 kg fetch (`sap_uom_group_entry=2` + `uom_filter_catalog=1` + `uom_id=34`)

The frontend uses **`sap_uom_group_entry=2` to mean “the 1 kg section”**, but SAP does **not** store all 1 kg items under group لك only.

**What the backend does (must match production code):**

1. Build the normal domain (category, active, sale, **UoM filter**, …).
2. Collect all product IDs whose SAP group has **`sap_abs_entry = 2` (لك)**.
3. **Intersect** that set with the current domain **for this request only**.
   - **If the intersection is non-empty** → apply the **strict لك filter**. Only لك-group products are returned.  
     → Works for FLORCHIM, ADF (mostly), GIVAUDAN (partial لك), ROYAL (partial لك), etc.
   - **If the intersection is empty** (category has **no** لك products at all) → **automatic fallback**: restrict instead to **`sap_abs_entry = 9` (فل بلاستك)** **and** **`product.template.uom_id = requested uom_id`** (e.g. `34` for كغم).  
     → **Required for CPL (categ_id=16), MIX, Group 139** — otherwise the API returns **0** while SAP shows rows.

**Why this matters:** Categories like **CPL** put **all** their kg items in **فل بلاستك**, not لك. Sending `sap_uom_group_entry=2` without fallback would incorrectly return nothing.

**Mixed categories (لك + فل بلاستك both exist):** If **any** product in that category is in لك, step 3 finds a match → **strict لك only**. Items that exist only under فل بلاستك (e.g. **ADF `G00901`**) do **not** appear in that call — that is intentional unless the FE uses another tab / `sap_uom_group_entry=9`.

---

### Exception rule B — فل بلاستك vs لك for “same” kg (`uom_id=34`)

- **فل بلاستك** has a **wide** ladder of sizes in SAP; Odoo may still set **`uom_id=34` (كغم)** on the product row even though the group’s **first** row in `sap_uom_sync` is often **50 غم**, not كغم.
- Do **not** assume “all kg POS rows = لك”. Always check **`sap_product_extended` → `sap_uom_group_id` → `sap_uom_group.sap_abs_entry`** for the SKU.

---

### Exception rule C — 0.25 كغم (group **8**) and `/products/by_primary_sales_uom`

- Quarter tabs rely on **primary UoM**: the product’s **`uom_id` must equal** the **lowest `sap_uom_entry`** mapping for its SAP group (for group 8, typically **`33`** = 0.25 كغم).
- If SAP sync left **`uom_id = 1` (Units)** or wrong UoM, the item **vanishes** from `by_primary_sales_uom` **with no error** — fix **`product.template.uom_id`**, not the endpoint alone.

---

### One-line cheat sheet

| Situation | Remember |
|-----------|----------|
| CPL / MIX / Group 139 + `sap_uom_group_entry=2` | Fallback to **فل بلاستك + uom_id** when category has **zero** لك rows. |
| ADF + strict لك list | **فل بلاستك-only** SKUs (e.g. **G00901**) excluded from that response — expected. |
| EUROPEAN + `sap_uom_group_entry=2` | Only **لك** subset unless FE uses **`sap_uom_group_entry=9`** or omits group filter. |
| Quarter counts vs SAP | Check **`uom_id` matches primary** for group **8** (0.25 كغم). |

*(Full tables and step-by-step flowcharts follow in §5 and §7.)*

---

## Table of Contents

**0.** [PRIORITY — SAP fetch exceptions (لك · فل بلاستك · 0.25 كغم)](#priority--sap-fetch-exceptions-لك--فل-بلاستك--025-كغم)

1. [System Overview](#1-system-overview)
2. [API Endpoints](#2-api-endpoints)
3. [SAP UoM Groups — The Core Concept](#3-sap-uom-groups--the-core-concept)
4. [Key UoM Groups in Detail](#4-key-uom-groups-in-detail)
5. [Category Fetch Modes & Exception Rules](#5-category-fetch-modes--exception-rules) *(expanded detail; summary above)*
6. [API Parameters Reference](#6-api-parameters-reference)
7. [The `sap_uom_group_entry` Filter — Full Logic](#7-the-sap_uom_group_entry-filter--full-logic)
8. [The `by_primary_sales_uom` Endpoint](#8-the-by_primary_sales_uom-endpoint)
9. [Common Gotchas & Known Quirks](#9-common-gotchas--known-quirks)
10. [Data Model Quick Reference](#10-data-model-quick-reference)
11. [Useful Debug Queries](#11-useful-debug-queries)

---

## 1. System Overview

The POS frontend fetches products from Odoo via a custom REST API. Odoo in turn mirrors product data from **SAP Business One** (synced via the `sap_integration` addon). Understanding how SAP structures its product catalog is essential before touching any POS fetch logic.

```
SAP Business One
     │  (sync via cron job)
     ▼
sap_product_extended   ←── per-product SAP metadata (UoM group, sales_item, sync date …)
sap_uom_group          ←── the SAP UoM group a product belongs to (e.g. "لك", "0.25 كغم")
sap_uom_sync           ←── maps each SAP group entry to an Odoo UoM
product.template       ←── the Odoo product (uom_id = the variant's sell UoM)
     │
     ▼
REST API  /api/pos_perfume/v1/products
REST API  /api/pos_perfume/v1/products/by_primary_sales_uom
     │
     ▼
POS Frontend (React SPA)
```

**Authentication:** Every API call requires either a session cookie (logged-in Odoo user) or a `Bearer` JWT token issued by the `lugal_auth` addon.

---

## 2. API Endpoints

### `GET /api/pos_perfume/v1/products`

The main product list endpoint. Used by the POS for every section/tab: 1 kg items, half-kg, quarter-kg, glass, etc.

**File:** `addons/pos_perfume_custom/controllers/pos_perfume_rest_controller.py`
→ method `products()`

### `GET /api/pos_perfume/v1/products/by_primary_sales_uom`

Groups products by their **primary** (smallest SAP UoM entry) UoM. Used for the quarter-kg tabs where the POS shows products grouped by their 0.25 kg/0.25 kg plastic variants.

**File:** same file → method `products_by_primary_sales_uom()`

---

## 3. SAP UoM Groups — The Core Concept

Every product synced from SAP belongs to exactly one **SAP UoM Group** (`sap_uom_group`). A group defines all the sell sizes available for products in that group. Think of it as SAP's packaging tier definition.

### Why groups matter for POS fetching

The POS frontend says _"give me the 1 kg items for category X."_ But many categories have products with `uom_id = كغم (34)` across **multiple** SAP groups. Without filtering by group, you'd get cross-contamination — e.g., a product that has a kg size in a large-format group (25 kg drums) would appear in the 1 kg POS tab.

The parameter `sap_uom_group_entry` locks the fetch to the correct SAP group for the requested size tier.

### The three groups you will deal with most

| `sap_abs_entry` | Group Name | Meaning |
|----------------|------------|---------|
| **2** | **لك** | Standard fragrance oil bulk — 1 kg, 0.5 kg, قطعه (piece) |
| **8** | **0.25 كغم** | Quarter-kg fragrance oils (glass or plastic bottle) |
| **9** | **فل بلاستك** | Plastic-container products — 50 g through 1000 kg range |

These three account for the vast majority of POS product fetches.

---

## 4. Key UoM Groups in Detail

### Group 2 — "لك" (Standard Bulk)

```
sap_uom_entry  Odoo UoM ID  UoM Name
─────────────────────────────────────
2              30           قطعه    ← PRIMARY (the "catalog unit")
6              34           كغم
10             38           0.5 كيلو
```

- **Primary UoM** = قطعه (piece) — but most products in this group are sold by weight, so their `product.template.uom_id` is `كغم (34)`.
- When FE sends `sap_uom_group_entry=2 & uom=kg & uom_id=34`, it wants the **1 kg fragrance oils** in this group.
- Categories that use this as their **sole** 1 kg group: FLORCHIM, Expression, ALGEX, Alcohol (partial).

### Group 8 — "0.25 كغم" (Quarter-Kg)

```
sap_uom_entry  Odoo UoM ID  UoM Name
─────────────────────────────────────
5              33           0.25 كغم       ← PRIMARY
11             39           0.25 كغم بلاستك
```

- **Primary UoM** = 0.25 كغم (id=33).
- Products in this group have `product.template.uom_id = 33`.
- The `by_primary_sales_uom` endpoint uses this primary to group/filter results.
- Categories: ADF (506 items), GIVAUDAN (411 items), ROYAL (382 items).

### Group 9 — "فل بلاستك" (Plastic Full-Range)

```
sap_uom_entry  Odoo UoM ID  UoM Name
────────────────────────────────────────
7              35           50 غم          ← PRIMARY
8              36           100 غم
9              37           125 غم
10             38           0.5 كيلو
13             41           25 كغم
14             42           100 كغم
15             43           500 كغم
16             44           1000 كغم
29             54           250 كغم
```

- **Primary UoM** = 50 غم (id=35) — the smallest package.
- This group spans an extremely wide size range (50 g → 1000 kg) and is used by multiple categories.
- **Critical:** The `sap_abs_entry=9` group does NOT have a direct `كغم (34)` entry in `sap_uom_sync`. Products in this group that Odoo records as `uom_id=34` have that set via direct product-level sync, NOT via the group's entry table.
- When FE sends `sap_uom_group_entry=2` for a category whose products are ALL in this group, the backend **falls back** to this group + `uom_id` match.

---

## 5. Category Fetch Modes & Exception Rules

> **Start with [PRIORITY — SAP fetch exceptions](#priority--sap-fetch-exceptions-لك--فل-بلاستك--025-كغم)** at the top of this doc — this section adds **tables and examples** for the same rules.

This section supports day-to-day debugging. Each POS category falls into one of three fetch modes when the FE requests `sap_uom_group_entry=2` (1 kg section):

### Mode A — PRIMARY ONLY (strict "لك" filter)

All 1 kg items for this category are in the "لك" group. The `sap_uom_group_entry=2` filter works exactly as you'd expect.

| categ_id | Category | Active 1 kg items |
|----------|----------|-------------------|
| 21 | FLORCHIM | 141 |
| 19 | Expression | 65 |
| 13 | ALGEX | 6 |
| 11 | Alcohol | 2 (partial; also has liter/drum groups) |
| 26 | Group 137 | 1 |
| 33 | Group 138 | 1 |

### Mode B — FALLBACK (all items in "فل بلاستك", none in "لك")

These categories have **zero** products in the "لك" group. When `sap_uom_group_entry=2` is received, the backend detects this and automatically falls back to "فل بلاستك" + `uom_id` match.

> ⚠️ **Exception rule — no backend config needed.** The fallback is fully automatic (see §7).

| categ_id | Category | Active items in فل بلاستك | Notes |
|----------|----------|--------------------------|-------|
| **16** | **CPL** | **11** | All kg items are in فل بلاستك |
| 27 | MIX | 24 | Mixed kg items in فل بلاستك |
| 10 | Group 139 | 26 | Mixed items in فل بلاستك |

### Mode C — MIXED ("لك" AND "فل بلاستك" both present)

These categories have products in **both** groups. The current behavior applies a **strict "لك" filter** (Mode A logic) because "لك" products exist. The "فل بلاستك" sub-population represents a different size/format and is fetched separately by the FE using a different tab/query.

| categ_id | Category | In لك | In فل بلاستك | In 0.25 كغم |
|----------|----------|--------|--------------|-------------|
| 7 | **ADF** | 542 | 1 ⚠️ | 506 |
| 22 | **GIVAUDAN** | 447 | 200 | 411 |
| 32 | **ROYAL** | 424 | 218 | 382 |
| 28 | **EUROPEAN** | 5 | 199 | — |
| 12 | Group 132 | 655 | 1 ⚠️ | — |
| 14 | بخور | 2 | 15 | — |

> ⚠️ **ADF exception (G00901):** ADF has exactly 1 product (`G00901 — انترلود الازرق/امواج M`) in the "فل بلاستك" group with `uom_id=34`. SAP counts it in a *different* section (not the "لك" 1 kg section). The strict "لك" filter correctly excludes it. **Do not move G00901 to "لك"** without confirming with SAP.

> ⚠️ **EUROPEAN note:** European has 199 items in "فل بلاستك" and only 5 in "لك". With `sap_uom_group_entry=2`, the API returns 5 (only "لك"). If the FE needs all 204 kg items for European at once, it should either omit `sap_uom_group_entry` or send `sap_uom_group_entry=9`.

---

## 6. API Parameters Reference

### `/products` — key parameters

| Parameter | Type | Effect |
|-----------|------|--------|
| `categ_id` / `category_id` | int | Filter by Odoo category (uses `child_of`, so subcategories included) |
| `pricelist_id` | int | Attach price info from this pricelist |
| `uom_filter_catalog` | bool (0/1) | When `1`, restrict to products whose UoM matches the requested size |
| `uom` | string | UoM name alias (`kg`, `half`, `quarter`, etc.) |
| `uom_id` | int | Odoo `uom.uom` ID (e.g. `34` = كغم, `33` = 0.25 كغم) |
| `sap_uom_group_entry` | int | **SAP group `sap_abs_entry` value.** Restricts to products in that SAP group. Key values: `2`=لك, `8`=0.25 كغم, `9`=فل بلاستك |
| `fetch_all` | bool (0/1) | Return all records (no pagination) |
| `limit` / `offset` | int | Pagination controls (default limit=80) |
| `query` | string | Search by name, default_code, or barcode |

### `/products/by_primary_sales_uom` — key parameters

Same as above plus:

| Parameter | Type | Effect |
|-----------|------|--------|
| (no `sap_uom_group_entry`) | — | This endpoint does its own primary-UoM filtering internally |

This endpoint only returns products whose `uom_id` matches the **lowest `sap_uom_entry`** in their SAP group. It groups results by UoM for display.

---

## 7. The `sap_uom_group_entry` Filter — Full Logic

This is the most complex piece of the backend. Read this carefully.

**Location in code:** `pos_perfume_rest_controller.py` → `products()`, after the `uom_filter_catalog` block.

### Step-by-step flow

```
1. FE sends: sap_uom_group_entry=2, categ_id=X, uom_id=34
   │
2. Backend queries: all product IDs whose SAP group has sap_abs_entry=2 ("لك")
   → group_pids = [list of all product IDs in "لك" group, across ALL categories]
   │
3. Backend checks: does the CURRENT DOMAIN (already filtered by category, UoM, etc.)
   intersect with group_pids?
   │
   ├─► YES (≥1 match) → apply strict filter: domain += ("id", "in", group_pids)
   │       ▲
   │       └── This is the normal path for FLORCHIM, ADF, GIVAUDAN, ROYAL, etc.
   │
   └─► NO (0 matches) → FALLBACK path
           │
           Check: sap_group_entry_raw == 2 AND uom_id_raw is not None
           │
           Query: all product IDs in "فل بلاستك" (sap_abs_entry=9)
                  WHERE pt.uom_id = uom_id_raw (=34 for kg)
           → fallback_pids
           │
           Apply: domain += ("id", "in", fallback_pids)
           │
           └── This fires for CPL, MIX, Group 139, etc.
```

### Why this design?

The key insight: **we check intersection with the already-filtered domain, not globally.** This means:

- For ADF: domain already has `categ_id=7`. ADF has 542 products in "لك" → intersection is non-empty → strict filter → G00901 (in "فل بلاستك") stays excluded ✓
- For CPL: domain already has `categ_id=16`. CPL has 0 products in "لك" → intersection is empty → fallback → "فل بلاستك" with uom=34 → 11 items returned ✓

---

## 8. The `by_primary_sales_uom` Endpoint

Used for the quarter-kg sections. It returns products grouped by UoM.

### How "primary UoM" is determined

```sql
SELECT DISTINCT pt.uom_id
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN sap_product_extended spe ON spe.product_id = pp.id
JOIN LATERAL (
    SELECT sus.odoo_uom_id
    FROM sap_uom_sync sus
    WHERE sus.sap_group_id = spe.sap_uom_group_id
    ORDER BY sus.sap_uom_entry ASC      -- ← lowest entry = primary
    LIMIT 1
) primary_uom ON true
WHERE pp.id = ANY(candidate_ids)
  AND pt.uom_id = primary_uom.odoo_uom_id   -- ← product's UoM must match
```

A product is included only if its `product.template.uom_id` equals the **lowest-entry UoM** in its SAP group.

### Example for GIVAUDAN (categ_id=22)

- SAP group 8 ("0.25 كغم"): lowest entry = 5 → Odoo UoM 33 (0.25 كغم)
- GIVAUDAN products with `uom_id=33` → included (408 items)
- GIVAUDAN products with `uom_id=34` (كغم) → excluded from this endpoint (they belong in the 1 kg tab)

### Critical data quality rule

**If a product is in the correct SAP group but has the wrong `uom_id` in Odoo, it will be silently excluded from this endpoint.** This has happened before:

- `G01478` (GIVAUDAN): was in group 8 ("0.25 كغم") but had `uom_id=1` (Units) → excluded
- `R01249`, `R01458` (ROYAL): same issue

**Fix:** Update `product_template.uom_id` to match the primary UoM of the SAP group. Run the diagnostic query in §11 to find others.

---

## 9. Common Gotchas & Known Quirks

### 1. Products with `uom_id = Units (1)` in a size-based SAP group

The SAP sync occasionally creates products with `uom_id=1` (generic "Units") even when the SAP group clearly maps to a specific size (e.g., 0.25 كغم). These products will:
- **Fail** the `by_primary_sales_uom` filter silently
- **Fail** `uom_filter_catalog=1` filters
- Appear in plain searches only

**Detection query:** See §11.

### 2. Duplicate SKUs from re-syncs

The April 2026 SAP re-sync created duplicate product records (e.g., G00358 existed twice with IDs 5439 and 22197). The newer duplicates were archived. If you see a SKU count mismatch vs SAP, check for duplicates with:

```sql
SELECT default_code, COUNT(*) as cnt
FROM product_template
WHERE default_code IS NOT NULL
GROUP BY default_code
HAVING COUNT(*) > 1;
```

### 3. Stale "last_sync_date" ≠ deleted from SAP

If `spe.last_sync_date` is months old while other products were synced recently, it means the SAP sync job stopped touching that product (likely removed from SAP). The `sales_item` flag in SAP may still be `true` in the local DB even though SAP no longer sends it.

**Rule of thumb:** If `last_sync_date < (most recent global sync - 30 days)` AND `sales_item=true`, the product was probably removed from SAP.

### 4. `sap_uom_group_entry=2` does NOT equal `uom=kg`

These are different filters:
- `uom=kg` / `uom_id=34` + `uom_filter_catalog=1` → filter by Odoo `uom_id`
- `sap_uom_group_entry=2` → filter by SAP group membership

A product can have `uom_id=34` but be in group 9 ("فل بلاستك"), not group 2 ("لك"). This is exactly the source of the CPL/MIX issue described above.

### 5. EUROPEAN category — partial "لك" membership

EUROPEAN has 5 products in "لك" and 199 in "فل بلاستك". With `sap_uom_group_entry=2`, the API returns only the 5 "لك" items. If the FE ever needs all EUROPEAN kg items in one call, it must omit `sap_uom_group_entry` and rely on `uom_filter_catalog=1` alone.

### 6. The `categ_id` filter uses `child_of`

The API resolves `categ_id` using Odoo's `child_of` search, so subcategories are included. If a parent category is passed, all children's products are returned too. This is intentional.

### 7. `auth='none'` on the route, but auth IS enforced

The Odoo route decorator says `auth='none'`, but `_pos_rest_auth()` is called at the top of every handler. Without a valid session cookie or JWT Bearer token, you get `401 Unauthorized`. This is by design to avoid Odoo's built-in auth middleware interfering with JWT.

---

## 10. Data Model Quick Reference

### Tables you'll query most

| Table | Purpose |
|-------|---------|
| `product_template` | Core product (name, uom_id, active, sale_ok, categ_id, default_code) |
| `product_product` | Product variant (usually 1:1 with template in this setup) |
| `sap_product_extended` | SAP-sourced metadata: `sap_item_code`, `sales_item`, `last_sync_date`, `sap_uom_group_id`, `sap_uom_group_entry`, `sync_status` |
| `sap_uom_group` | SAP UoM group definitions: `sap_abs_entry` (the number in `sap_uom_group_entry`), `name` |
| `sap_uom_sync` | Maps each SAP group entry (`sap_uom_entry`) to an Odoo `uom_uom` (`odoo_uom_id`) |
| `uom_uom` | Odoo Units of Measure |
| `product_category` | Odoo product categories |
| `product_pricelist_item` | Pricing rules |

### Key UoM IDs

| ID | Name | Used for |
|----|------|---------|
| 1 | Units | Generic fallback (data quality issue if product should have a real UoM) |
| 30 | قطعه | Piece (catalog/display unit for لك group) |
| 33 | 0.25 كغم | Quarter kg glass bottle |
| 34 | كغم | 1 kg |
| 35 | 50 غم | 50-gram plastic |
| 36 | 100 غم | 100-gram plastic |
| 37 | 125 غم | 125-gram plastic |
| 38 | 0.5 كيلو | Half kg |
| 39 | 0.25 كغم بلاستك | Quarter kg plastic |

### Key SAP Groups (the ones POS cares about)

| `sap_abs_entry` | Name | Primary Odoo UoM | FE uses it via |
|----------------|------|-----------------|----------------|
| 2 | لك | قطعه (30) | `sap_uom_group_entry=2` |
| 8 | 0.25 كغم | 0.25 كغم (33) | `sap_uom_group_entry=8` or `by_primary_sales_uom` |
| 9 | فل بلاستك | 50 غم (35) | fallback when sap_uom_group_entry=2 has no matches, or `sap_uom_group_entry=9` |

---

## 11. Useful Debug Queries

### Find products with wrong UoM for their SAP group (invisible to `by_primary_sales_uom`)

```sql
SELECT pt.default_code, pt.name->>'en_US' as name,
       pc.name as category,
       pt.uom_id as current_uom, cu.name->>'en_US' as current_uom_name,
       primary_uom.odoo_uom_id as correct_uom, pu.name->>'en_US' as correct_uom_name,
       sug.name as sap_group
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN product_category pc ON pc.id = pt.categ_id
JOIN uom_uom cu ON cu.id = pt.uom_id
JOIN sap_product_extended spe ON spe.product_id = pp.id
JOIN LATERAL (
    SELECT sus.odoo_uom_id
    FROM sap_uom_sync sus
    WHERE sus.sap_group_id = spe.sap_uom_group_id
    ORDER BY sus.sap_uom_entry ASC LIMIT 1
) primary_uom ON true
JOIN uom_uom pu ON pu.id = primary_uom.odoo_uom_id
JOIN sap_uom_group sug ON sug.id = spe.sap_uom_group_id
WHERE pt.active = true AND pp.active = true AND pt.sale_ok = true
  AND pt.uom_id != primary_uom.odoo_uom_id
  AND pt.uom_id = 1   -- only the worst offenders (generic Units)
ORDER BY pc.name, pt.default_code;
```

### Count active products per category per SAP group

```sql
SELECT pc.id, pc.name,
       sug.sap_abs_entry, sug.name as sap_group,
       COUNT(*) as active_items
FROM product_category pc
JOIN product_template pt ON pt.categ_id = pc.id
JOIN product_product pp ON pp.product_tmpl_id = pt.id
JOIN sap_product_extended spe ON spe.product_id = pp.id
JOIN sap_uom_group sug ON sug.id = spe.sap_uom_group_id
WHERE pt.active = true AND pp.active = true AND pt.sale_ok = true
GROUP BY pc.id, pc.name, sug.sap_abs_entry, sug.name
ORDER BY pc.name, sug.sap_abs_entry;
```

### Find duplicate SKUs

```sql
SELECT pt.default_code, COUNT(*) as cnt,
       ARRAY_AGG(pp.id ORDER BY pp.id) as variant_ids,
       ARRAY_AGG(pt.active::text ORDER BY pp.id) as active_flags
FROM product_template pt
JOIN product_product pp ON pp.product_tmpl_id = pt.id
WHERE pt.default_code IS NOT NULL
GROUP BY pt.default_code
HAVING COUNT(*) > 1
ORDER BY cnt DESC;
```

### Find products SAP says are active but Odoo has excluded

```sql
SELECT spe.sap_item_code, spe.last_sync_date::date,
       pt.default_code, pt.active, pt.sale_ok, pp.active as v_active,
       pc.name as category
FROM sap_product_extended spe
JOIN product_product pp ON pp.id = spe.product_id
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN product_category pc ON pc.id = pt.categ_id
WHERE spe.sales_item = true
  AND (pt.active = false OR pp.active = false OR pt.sale_ok = false)
ORDER BY spe.last_sync_date DESC, pt.default_code;
```

### Simulate what `by_primary_sales_uom` would return for a category

```sql
SELECT pt.default_code, pt.name->>'en_US' as name, COUNT(*) as total
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN sap_product_extended spe ON spe.product_id = pp.id
JOIN LATERAL (
    SELECT sus.odoo_uom_id
    FROM sap_uom_sync sus
    WHERE sus.sap_group_id = spe.sap_uom_group_id
    ORDER BY sus.sap_uom_entry ASC LIMIT 1
) primary_uom ON true
WHERE pt.categ_id = 22               -- ← change this
  AND pt.active = true AND pp.active = true AND pt.sale_ok = true
  AND pt.uom_id = primary_uom.odoo_uom_id
GROUP BY pt.default_code, pt.name
ORDER BY pt.default_code;
```

### Verify a category's fetch mode (لك vs فل بلاستك vs mixed)

```sql
SELECT
  SUM(CASE WHEN sug.sap_abs_entry = 2 THEN 1 ELSE 0 END) as in_lak,
  SUM(CASE WHEN sug.sap_abs_entry = 9 AND pt.uom_id = 34 THEN 1 ELSE 0 END) as in_ful_plastic_kg,
  SUM(CASE WHEN sug.sap_abs_entry = 8 THEN 1 ELSE 0 END) as in_quarter_kg
FROM product_product pp
JOIN product_template pt ON pt.id = pp.product_tmpl_id
JOIN sap_product_extended spe ON spe.product_id = pp.id
JOIN sap_uom_group sug ON sug.id = spe.sap_uom_group_id
WHERE pt.categ_id = 16               -- ← change this
  AND pt.active = true AND pp.active = true AND pt.sale_ok = true;
```

---

## Appendix — SAP Sync Caveats

1. **Sync runs on a cron schedule.** New SAP items may not appear in Odoo for hours. If a product exists in SAP but is missing from the API, check the sync date of recently created products and trigger a manual sync if urgent.

2. **`sales_item = false` in SAP** → Odoo should set `sale_ok = false` on the product template. If you see a mismatch (SAP says not for sale, Odoo shows `sale_ok=true`), the sync may have missed the update. Fix manually via SQL with `UPDATE product_template SET sale_ok=false WHERE id=...`.

3. **Placeholder names** (`Product G01xxx`): The SAP sync can create a product record with a placeholder name if the item name was missing or failed to import. These products are usually archived, but if they're active they'll appear with generic names in the POS.

4. **The `sap_product_extended` table is source of truth** for SAP-side status. The `product.template`/`product.product` tables reflect the Odoo-side status. Discrepancies between the two are the #1 source of count mismatches.

5. **Never delete a product that has `sap_product_extended` records** — archive it instead (`active=false`). Deletion would break the SAP sync's ability to recognize the product on the next run.
