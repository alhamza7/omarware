# SAP-Odoo Product Data Cleanup Log

**Executed:** 2026-04-29  
**Operator:** AI Agent (Cursor)  
**Purpose:** Align Odoo product data with SAP — archive duplicates from the March/April 2026 re-sync, fix one `sale_ok` mismatch, and archive 7 products not synced since Nov–Dec 2025.

---

## Summary of Changes

| Step | Action | Count |
|------|--------|-------|
| 1 | Archive duplicate product templates (newer re-sync records) | 28 archived (1 was already archived) |
| 2 | Set `sale_ok=False` on SAP `sales_item=False` mismatch | 1 |
| 3 | Archive stale products (not synced since Nov–Dec 2025) | 7 |
| **Total** | | **36 records changed** |

---

## Step 1 — Archive Duplicate Records

These are all `product.template` records created during the March–April 2026 SAP re-sync. Each SKU already had an original record (Nov 2025). The originals are kept; the newer duplicates are archived.

**Template IDs archived:** 22163, 22189, 22190, 22191, 22192, 22193, 22197, 22198, 22199, 22222, 22223, 22225, 22226, 22227, 22229, 22230, 22231, 22232, 22233, 22234, 22235, 22236, 22237, 22238, 22239, 22240, 22241, 22243

*(22194 was already `active=false`, no change needed)*

### Before State

| Template ID | SKU | Name | Was Active | Was sale_ok | Category | Created |
|-------------|-----|------|-----------|------------|----------|---------|
| 22163 | PRM00394 | رومانتك نايت R | true | false | Perfumes Raw Materials | 2026-03-05 |
| 22189 | S01348 | بطل فافون بنفسجي ربع كغم | true | true | Glass | 2026-03-08 |
| 22190 | S01417 | بطل فافون برونزي ربع كغم | true | true | Glass | 2026-03-08 |
| 22191 | S01349 | بطل فافون اسود طافي ربع كغم | true | true | Glass | 2026-03-08 |
| 22192 | S01415 | بطل فافون برونزي 1كغم | true | true | Glass | 2026-03-08 |
| 22193 | S01416 | بطل فافون برونزي نصف كغم | true | true | Glass | 2026-03-08 |
| 22194 | S00174 | S-226 ملغى | false | false | Glass | 2026-03-09 |
| 22197 | G00358 | عود باودر | true | true | GIVAUDAN | 2026-03-12 |
| 22198 | PRM00857 | عود باودر G | true | false | Perfumes Raw Materials | 2026-03-12 |
| 22199 | G01005 | ساكورا / ديور | true | true | GIVAUDAN | 2026-03-12 |
| 22222 | S00807 | S-776-300 | true | true | Glass | 2026-03-19 |
| 22223 | G00939 | مجتمع النبلاء /جفنجي | true | true | GIVAUDAN | 2026-03-19 |
| 22225 | AF00058 | ايفل بخاخ 500 مل | true | false | معطر جو | 2026-04-02 |
| 22226 | AF00077 | ملطف جو 300 مل طويل (لطافه) | true | false | معطر جو | 2026-04-02 |
| 22227 | B00163 | بخور بيت الاسرة ( خدلج ) | true | false | بخور | 2026-04-02 |
| 22229 | S01471 | BAG-15 | true | true | Glass | 2026-04-08 |
| 22230 | S01472 | BAG-15-1 | true | true | Glass | 2026-04-08 |
| 22231 | S01473 | BAG-15-2 | true | true | Glass | 2026-04-08 |
| 22232 | S01474 | BAG-15-3 | true | true | Glass | 2026-04-08 |
| 22233 | S01517 | علب مخمرية 20غم | true | true | Glass | 2026-04-08 |
| 22234 | S01518 | علب مخمرية 30غم | true | true | Glass | 2026-04-08 |
| 22235 | S01519 | علب مخمرية 50غم | true | true | Glass | 2026-04-08 |
| 22236 | S01526 | بطل بلاستك ملون 500مل+بخاخ اسود | true | true | Glass | 2026-04-08 |
| 22237 | S01520 | قلم تعبئة 5 مل صاجي | true | true | Glass | 2026-04-08 |
| 22238 | S01527 | قلم تعبئة 10مل | true | true | Glass | 2026-04-08 |
| 22239 | S01528 | قلم تعبئة 8مل | true | true | Glass | 2026-04-08 |
| 22240 | S01529 | قلم زجاج 5 مل بخاخ بلاستك | true | true | Glass | 2026-04-08 |
| 22241 | S01530 | بطل بلاستك جوزي مات350مل | true | true | Glass | 2026-04-08 |
| 22243 | ALC00004 | كحول صافي فرنسي 5 لتر فل | true | true | Alcohol | 2026-04-08 |

### After State

All 28 records: `active = false`, `sale_ok` unchanged (no longer visible in POS/Sales).

---

## Step 2 — Fix `sale_ok` Mismatch (PRM01893)

SAP marks this product as `sales_item=False` but Odoo had `sale_ok=True`.

| Template ID | Variant ID | SKU | Name | Category |
|-------------|-----------|-----|------|----------|
| 10560 | 10560 | PRM01893 | موصوف جوزي-ارض الزعفران | Perfumes Raw Materials |

**Change:** `sale_ok: true → false`  
**Template still active:** yes (product remains in inventory, just not saleable)

---

## Step 3 — Archive Stale Products (Not synced since Nov–Dec 2025)

These products have had no SAP sync update for 4–5 months, suggesting they were removed from SAP. All were previously `active=true, sale_ok=true`.

| Template ID | Variant ID | SKU | Name | Last Synced | Category |
|-------------|-----------|-----|------|-------------|----------|
| 6513 | 6513 | G01441 | موصوف جوزي-ارض الزعفران | 2025-11-19 | GIVAUDAN |
| 6514 | 6514 | G01442 | موصوف جوزي-ارض الزعفران | 2025-11-19 | GIVAUDAN |
| 8371 | 8371 | N100273 | ماي وي N1 | 2025-11-19 | EUROPEAN |
| 8372 | 8372 | N100274 | مكس فروت N1 | 2025-11-19 | EUROPEAN |
| 8482 | 8482 | P00107 | ملغى | 2025-11-19 | Group 135 |
| 14065 | 14065 | G01525 | عود كادينزا – ميزون كريفيلي | 2025-12-04 | GIVAUDAN |
| 16473 | 16473 | PRM01955 | تايغر (بولغاري) G | 2025-12-19 | Perfumes Raw Materials |

**Change:** `active: true → false` on all 7 templates and their variants.

---

## Verification Query Results (Post-Execution)

```
DUPLICATE_CHECK  | archived=29 | still_active=0  ✅
SALE_OK_CHECK    | sale_ok=false=1 | sale_ok=true=0  ✅
STALE_CHECK      | archived=7  | still_active=0  ✅
```

---

## What Was NOT Changed

- 2679 products with `sales_item=False` in SAP that already have `sale_ok=False` in Odoo — already correct ✅
- 1938 products already fully archived in both SAP and Odoo — already correct ✅
- FLORCHIM FL00090, FL00115 (`sale_ok=False`) — already correct ✅
- 9 Odoo-only products (no SAP extended record) — left as-is (may be manually entered) ✅

---

## Reversal Instructions (if needed)

```sql
-- Undo Step 1 (un-archive duplicates)
UPDATE product_template SET active = true WHERE id IN (
  22163,22189,22190,22191,22192,22193,22197,22198,22199,22222,22223,
  22225,22226,22227,22229,22230,22231,22232,22233,22234,22235,22236,
  22237,22238,22239,22240,22241,22243
);
UPDATE product_product SET active = true WHERE product_tmpl_id IN (
  22163,22189,22190,22191,22192,22193,22197,22198,22199,22222,22223,
  22225,22226,22227,22229,22230,22231,22232,22233,22234,22235,22236,
  22237,22238,22239,22240,22241,22243
);

-- Undo Step 2 (restore sale_ok)
UPDATE product_template SET sale_ok = true WHERE id = 10560;

-- Undo Step 3 (un-archive stale products)
UPDATE product_template SET active = true WHERE id IN (6513,6514,8371,8372,14065,8482,16473);
UPDATE product_product SET active = true WHERE product_tmpl_id IN (6513,6514,8371,8372,14065,8482,16473);
```
