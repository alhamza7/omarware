#!/usr/bin/env python3
"""
Lugal Config Apply
==================
Applies system config parameters from config_export.json into a target database.

Usage:
    python3 scripts/apply_config.py --target YOUR_DB [--server-url https://yourdomain.com] [--frontend-url https://yourfrontend.com] [--dry-run]

Arguments:
    --target        Target database name (required)
    --server-url    Override web.base.url  (e.g. https://api.yourdomain.com)
    --frontend-url  Override lugal.frontend.base.url (e.g. https://app.yourdomain.com)
    --dry-run       Preview changes without writing
"""

import argparse
import json
import os
import sys
import psycopg2

DB_HOST     = "localhost"
DB_PORT     = 5432
DB_USER     = "odoo_user"
DB_PASSWORD = "root"

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; X = "\033[0m"


def connect(dbname):
    kw = dict(dbname=dbname, host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASSWORD)
    return psycopg2.connect(**kw)


def main():
    parser = argparse.ArgumentParser(description="Apply Lugal config parameters to a database")
    parser.add_argument("--target",       required=True,  help="Target database name")
    parser.add_argument("--server-url",   default=None,   help="Override web.base.url")
    parser.add_argument("--frontend-url", default=None,   help="Override lugal.frontend.base.url")
    parser.add_argument("--file",         default=os.path.join(os.path.dirname(__file__), "config_export.json"),
                        help="Path to config_export.json (default: scripts/config_export.json)")
    parser.add_argument("--dry-run",      action="store_true")
    args = parser.parse_args()

    print(f"\n{C}Lugal Config Apply{X}")
    print(f"  Target  : {G}{args.target}{X}")
    print(f"  File    : {G}{args.file}{X}")
    if args.dry_run:
        print(f"  Mode    : {Y}DRY RUN{X}")

    try:
        with open(args.file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"{R}File not found: {args.file}{X}"); sys.exit(1)

    params = data.get("params", [])

    # apply CLI overrides
    for p in params:
        if p["key"] == "web.base.url" and args.server_url:
            p["value"] = args.server_url
        if p["key"] == "lugal.frontend.base.url" and args.frontend_url:
            p["value"] = args.frontend_url

    try:
        conn = connect(args.target)
    except Exception as e:
        print(f"{R}Connection failed: {e}{X}"); sys.exit(1)

    cur = conn.cursor()
    print(f"\n{C}Applying {len(params)} parameters...{X}\n")

    for p in params:
        key   = p["key"]
        value = p["value"]
        note  = p.get("note", "")

        # check current value
        cur.execute("SELECT value FROM ir_config_parameter WHERE key = %s", (key,))
        row = cur.fetchone()
        current = row[0] if row else None

        if dry_run := args.dry_run:
            status = f"[DRY-RUN] would {'UPDATE' if current else 'INSERT'}"
            colour = Y if current else G
            print(f"  {colour}{status}{X}  {key}")
            if note: print(f"           {C}→ {note}{X}")
            continue

        if current == value:
            print(f"  {C}={X}  {key}  {Y}(no change){X}")
            continue

        if current is not None:
            cur.execute("UPDATE ir_config_parameter SET value=%s WHERE key=%s", (value, key))
            print(f"  {Y}↑{X}  {key}")
        else:
            cur.execute("INSERT INTO ir_config_parameter (key, value) VALUES (%s, %s)", (key, value))
            print(f"  {G}+{X}  {key}")

        if note:
            print(f"     {C}→ {note}{X}")

    if not args.dry_run:
        conn.commit()
        print(f"\n{G}━━ Config Applied Successfully ━━{X}")
        print(f"\n{Y}Important — verify these values match your server:{X}")
        for p in params:
            if "CHANGE" in p.get("note", ""):
                print(f"  {Y}!{X}  {p['key']} = {G}{p['value']}{X}")
    else:
        print(f"\n{Y}Dry run complete — nothing written.{X}")

    conn.close()


if __name__ == "__main__":
    main()
