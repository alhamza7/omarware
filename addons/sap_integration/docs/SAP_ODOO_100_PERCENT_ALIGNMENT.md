# SAP ↔ Odoo: 100% catalog alignment

Odoo is aligned with SAP **Item master** when every `product.template` / `product.product` with a `default_code` matches SAP **Items** (`ItemCode`) and uses the same **Valid**, **Frozen**, **SalesItem**, and **PurchaseItem** semantics as `sap_product_complete_migration._sap_commercial_flags_from_item`.

## 1. Always run: commercial flags from SAP

**UI:** *SAP Integration → Complete Product Migration* → enable backend →  
**“Sync SAP commercial flags only”** (no full migration).

This walks all SAP `Items` and, for each `ItemCode` that exists in Odoo as `default_code`, writes:

- `active`, `sale_ok`, `purchase_ok`, `available_in_pos` on the **product template**

Same logic runs on the **cron** when *SAP Auto Sync* has **Sync Sales/Purchase/POS flags** enabled.

## 2. Optional: remove Odoo-only rows (true 1:1 with SAP)

Enable **“Deactivate Odoo-only products (no SAP Item)”** on the migration wizard or on *SAP Auto Sync*.

After the SAP pass, every template whose `default_code` is **not** in the SAP `Items` list is archived (`active=False`, sales/purchase/POS off).

**Warning:** legitimate Odoo-only SKUs (services, local stock, tests) will be archived. Use only when the catalog must be **exactly** the SAP item list.

## 3. SAP items not yet in Odoo

The flag sync reports `not_in_odoo` (SAP `ItemCode` with no matching Odoo product). To mirror SAP completely, **import products** (wizard *Stage 2: Import Products*, or your import pipeline), then run **Sync SAP commercial flags only** again.

## 4. Reconciliation script

`scripts/sap_odoo_item_reconcile.py` (requires `PGPASSWORD`) compares live Service Layer `Items` with PostgreSQL and writes CSV diffs under `data/sap_odoo_diff/`.

After steps 1–3, re-run the script; remaining differences should be zero (or only timing if SAP/Odoo change between runs).
