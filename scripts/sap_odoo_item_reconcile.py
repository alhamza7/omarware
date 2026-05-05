#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconcile SAP Business One Service Layer Items with Odoo product.product.

Reads active sap.backend from PostgreSQL (same DB as Odoo). Writes CSV reports
under data/sap_odoo_diff/ — no credentials in this file.

Usage:
  PGPASSWORD=... python3 scripts/sap_odoo_item_reconcile.py
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path

import psycopg2
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "sap_odoo_diff"
BATCH = 500


def sap_bool(value, default_true=True):
    if value is None or value == "":
        return bool(default_true)
    if isinstance(value, bool):
        return value
    v = str(value).strip().upper()
    return v in ("Y", "YES", "TYES", "1", "TRUE", "T")


def sap_frozen(item):
    v = item.get("Frozen")
    if v is True:
        return True
    if v is False:
        return False
    if v is None or v == "":
        return False
    sv = str(v).strip().upper()
    return sv in ("TYES", "YES", "Y", "1", "TRUE", "T")


def sap_active_for_odoo(item):
    if sap_frozen(item):
        return False
    if "Valid" in item and item.get("Valid") is not None and item.get("Valid") != "":
        return sap_bool(item.get("Valid"), default_true=True)
    return True


def sap_sale_ok_equivalent(item, force_enable_sales_pos=False):
    """Match sap_product_complete_migration._sap_commercial_flags_from_item (no force)."""
    is_active = sap_active_for_odoo(item)
    is_sales_item = sap_bool(item.get("SalesItem"), default_true=True)
    if force_enable_sales_pos:
        enable_sales = is_active
    else:
        enable_sales = is_active and is_sales_item
    return enable_sales


def load_backend(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, base_url, username, password, company_db, COALESCE(verify_ssl, false)
        FROM sap_backend
        WHERE active = true
        ORDER BY id
        LIMIT 1
        """
    )
    row = cur.fetchone()
    cur.close()
    if not row:
        sys.stderr.write("No active sap.backend in database.\n")
        sys.exit(2)
    return {
        "id": row[0],
        "base_url": row[1].rstrip("/"),
        "username": row[2],
        "password": row[3],
        "company_db": row[4],
        "verify_ssl": row[5],
    }


def sap_login(cfg):
    s = requests.Session()
    s.verify = cfg["verify_ssl"]
    url = f"{cfg['base_url']}/Login"
    r = s.post(
        url,
        json={
            "UserName": cfg["username"],
            "Password": cfg["password"],
            "CompanyDB": cfg["company_db"],
        },
        timeout=60,
    )
    r.raise_for_status()
    sid = r.json().get("SessionId")
    if not sid:
        raise RuntimeError("SAP login: no SessionId")
    s.headers.update({"B1S-SessionId": sid, "Content-Type": "application/json"})
    return s


def fetch_all_items(session, base_url):
    """ItemCode + flags for every row (paginated)."""
    skip = 0
    rows = []
    while True:
        params = {
            "$select": "ItemCode,Frozen,Valid,SalesItem",
            "$orderby": "ItemCode",
            "$top": BATCH,
            "$skip": skip,
        }
        r = session.get(f"{base_url}/Items", params=params, timeout=120)
        r.raise_for_status()
        data = r.json()
        batch = data.get("value") or []
        if not batch:
            break
        rows.extend(batch)
        skip += len(batch)
        if not batch:
            break
    return rows


def load_odoo_sets(conn):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT pp.default_code, pp.active, pt.active AS tmpl_active, pt.sale_ok
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE NULLIF(TRIM(pp.default_code), '') IS NOT NULL
        """
    )
    by_code = {}
    for code, pa, ta, sk in cur.fetchall():
        c = (code or "").strip()
        if not c:
            continue
        by_code[c] = {"pp_active": pa, "tmpl_active": ta, "sale_ok": sk}
    cur.close()
    return by_code


def main():
    pg_host = os.environ.get("PGHOST", "localhost")
    pg_port = os.environ.get("PGPORT", "5432")
    pg_user = os.environ.get("PGUSER", "odoo_user")
    pg_db = os.environ.get("PGDATABASE", "nbs_lugalai")
    if not os.environ.get("PGPASSWORD"):
        sys.stderr.write("Set PGPASSWORD (or use .pgpass).\n")
        sys.exit(1)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    conn = psycopg2.connect(host=pg_host, port=pg_port, user=pg_user, dbname=pg_db)
    cfg = load_backend(conn)
    odoo = load_odoo_sets(conn)
    conn.close()

    session = sap_login(cfg)
    base = cfg["base_url"]
    items = fetch_all_items(session, base)

    sap_codes = set()
    sap_active = set()
    sap_sale = set()
    for it in items:
        code = (it.get("ItemCode") or "").strip()
        if not code:
            continue
        sap_codes.add(code)
        if sap_active_for_odoo(it):
            sap_active.add(code)
        if sap_sale_ok_equivalent(it, force_enable_sales_pos=False):
            sap_sale.add(code)

    odoo_active = {c for c, v in odoo.items() if v["pp_active"]}
    odoo_sale = {
        c
        for c, v in odoo.items()
        if v["pp_active"] and v["tmpl_active"] and v["sale_ok"]
    }

    # --- write summary ---
    summary_path = OUT_DIR / "summary.txt"
    lines = [
        f"SAP backend id={cfg['id']} base={cfg['base_url']}",
        f"SAP Items rows fetched: {len(items)} (distinct ItemCode: {len(sap_codes)})",
        f"SAP 'active_for_odoo' (not Frozen, Valid): {len(sap_active)}",
        f"SAP 'sale_ok_equivalent' (active + SalesItem): {len(sap_sale)}",
        f"Odoo distinct default_code (any variant row): {len(odoo)}",
        f"Odoo active variant (default_code set): {len(odoo_active)}",
        f"Odoo active + tmpl active + sale_ok: {len(odoo_sale)}",
        "",
        "Symmetric differences (by ItemCode = default_code):",
        f"  SAP_active \\ Odoo_active: {len(sap_active - odoo_active)}",
        f"  Odoo_active \\ SAP_active: {len(odoo_active - sap_active)}",
        f"  SAP_sale \\ Odoo_sale: {len(sap_sale - odoo_sale)}",
        f"  Odoo_sale \\ SAP_sale: {len(odoo_sale - sap_sale)}",
        f"  SAP_any \\ Odoo_any_code: {len(sap_codes - set(odoo))}",
        f"  Odoo_any_code \\ SAP_any: {len(set(odoo) - sap_codes)}",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def dump_csv(name, codes):
        path = OUT_DIR / name
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["item_code"])
            for c in sorted(codes):
                w.writerow([c])

    dump_csv("only_sap_active_not_odoo_active.csv", sap_active - odoo_active)
    dump_csv("only_odoo_active_not_sap_active.csv", odoo_active - sap_active)
    dump_csv("only_sap_sale_not_odoo_sale.csv", sap_sale - odoo_sale)
    dump_csv("only_odoo_sale_not_sap_sale.csv", odoo_sale - sap_sale)
    dump_csv("only_sap_no_odoo_product.csv", sap_codes - set(odoo))
    dump_csv("only_odoo_no_sap_item.csv", set(odoo) - sap_codes)

    print(summary_path.read_text(encoding="utf-8"))
    print(f"CSV files written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
