#!/usr/bin/env python3
"""
Lugal Users Export
==================
Exports ALL user-related data from a source DB into a portable JSON file.
The exported file can then be imported into ANY target database using import_users.py.

Usage:
    python3 scripts/export_users.py --source lugal_ws_sandbox --out users_export.json

What is exported:
    • res_users        — login, hashed password, active, settings
    • res_partner      — name, email, phone, mobile, lang, tz, address
    • res_groups       — permissions (stored as xml_id for portability)
    • res_company      — company assignments (stored by company name)
    • lugal_email_account      — IMAP/SMTP accounts
    • res_users_settings       — Odoo discuss/notification settings
    • lugal_crm_user_preferences — CRM theme/dashboard/language prefs
    • lugal_push_subscription  — Web Push subscriptions
"""

import argparse
import json
import sys
from datetime import datetime
import psycopg2
import psycopg2.extras

DB_HOST    = None
DB_PORT    = 5432
DB_USER    = None
SKIP_LOGINS = {"__system__", "__public__"}

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; X = "\033[0m"


def connect(dbname):
    kw = dict(dbname=dbname)
    if DB_HOST: kw.update(host=DB_HOST, port=DB_PORT)
    if DB_USER: kw["user"] = DB_USER
    return psycopg2.connect(**kw)


def dcur(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def table_exists(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (name,))
    return cur.fetchone() is not None


def build_group_xml_map(conn):
    """Returns {gid: xml_id}"""
    cur = conn.cursor()
    cur.execute("""
        SELECT imd.res_id, imd.module || '.' || imd.name
        FROM   ir_model_data imd
        WHERE  imd.model = 'res.groups'
    """)
    return {r[0]: r[1] for r in cur.fetchall()}


def serialize(obj):
    """Make psycopg2 types JSON-serializable."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, memoryview):
        return None   # skip binary blobs
    return str(obj)


def export_users(conn, source_db):
    cur = dcur(conn)
    gid_to_xml = build_group_xml_map(conn)

    # load all users
    cur.execute("""
        SELECT
            u.id            AS src_uid,
            u.login, u.password, u.active, u.share,
            u.notification_type, u.preferred_nbs_language,
            u.tour_enabled, u.signature, u.out_of_office_message,
            p.name, p.email, p.phone, p.mobile,
            p.lang, p.tz, p.street, p.street2,
            p.city, p.zip, p.comment AS partner_comment
        FROM res_users u
        JOIN res_partner p ON p.id = u.partner_id
        WHERE u.share = false
          AND u.login NOT IN %s
        ORDER BY u.id
    """, (tuple(SKIP_LOGINS),))
    users_raw = cur.fetchall()

    print(f"\n{C}Exporting {len(users_raw)} users from '{source_db}'...{X}\n")

    export = {
        "meta": {
            "source_db":    source_db,
            "exported_at":  datetime.now().isoformat(),
            "user_count":   len(users_raw),
            "version":      "2.0",
        },
        "users": []
    }

    for u in users_raw:
        uid     = u["src_uid"]
        login   = u["login"]

        user_rec = {
            # ── identity ──────────────────────────────────────────────────────
            "login":                  u["login"],
            "password":               u["password"],
            "active":                 u["active"],
            "share":                  u["share"],
            "notification_type":      u["notification_type"],
            "preferred_nbs_language": u["preferred_nbs_language"],
            "tour_enabled":           u["tour_enabled"],
            "signature":              u["signature"],
            "out_of_office_message":  u["out_of_office_message"],

            # ── partner ───────────────────────────────────────────────────────
            "partner": {
                "name":    u["name"],
                "email":   u["email"],
                "phone":   u["phone"],
                "mobile":  u["mobile"],
                "lang":    u["lang"],
                "tz":      u["tz"],
                "street":  u["street"],
                "street2": u["street2"],
                "city":    u["city"],
                "zip":     u["zip"],
                "comment": u["partner_comment"],
            },

            # ── groups / permissions ──────────────────────────────────────────
            "groups": [],

            # ── companies ─────────────────────────────────────────────────────
            "companies": [],

            # ── email accounts ────────────────────────────────────────────────
            "email_accounts": [],

            # ── odoo settings ─────────────────────────────────────────────────
            "odoo_settings": None,

            # ── crm preferences ───────────────────────────────────────────────
            "crm_preferences": None,

            # ── push subscriptions ────────────────────────────────────────────
            "push_subscriptions": [],
        }

        # groups
        cur.execute("SELECT gid FROM res_groups_users_rel WHERE uid = %s", (uid,))
        for row in cur.fetchall():
            xml_id = gid_to_xml.get(row["gid"])
            if xml_id:
                user_rec["groups"].append(xml_id)

        # companies
        cur.execute("""
            SELECT rc.name
            FROM   res_company_users_rel rcur
            JOIN   res_company rc ON rc.id = rcur.cid
            WHERE  rcur.user_id = %s
        """, (uid,))
        user_rec["companies"] = [r["name"] for r in cur.fetchall()]

        # email accounts
        cur.execute("""
            SELECT email_address, display_name_field, name,
                   is_active, is_default, active,
                   imap_host, imap_port, imap_use_ssl,
                   smtp_host, smtp_port, smtp_use_tls,
                   username, password, sync_status
            FROM   lugal_email_account
            WHERE  user_id = %s AND (is_deleted IS NOT TRUE)
            ORDER BY id
        """, (uid,))
        user_rec["email_accounts"] = [dict(r) for r in cur.fetchall()]

        # odoo settings
        cur.execute("SELECT * FROM res_users_settings WHERE user_id = %s", (uid,))
        rs = cur.fetchone()
        if rs:
            user_rec["odoo_settings"] = {
                "voice_active_duration":                    rs["voice_active_duration"],
                "push_to_talk_key":                         rs["push_to_talk_key"],
                "channel_notifications":                    rs["channel_notifications"],
                "is_discuss_sidebar_category_channel_open": rs["is_discuss_sidebar_category_channel_open"],
                "is_discuss_sidebar_category_chat_open":    rs["is_discuss_sidebar_category_chat_open"],
                "use_push_to_talk":                         rs["use_push_to_talk"],
            }

        # crm preferences
        if table_exists(conn, "lugal_crm_user_preferences"):
            cur.execute("SELECT * FROM lugal_crm_user_preferences WHERE user_id = %s", (uid,))
            pr = cur.fetchone()
            if pr:
                user_rec["crm_preferences"] = {
                    "theme_data":        pr["theme_data"],
                    "notification_data": pr["notification_data"],
                    "dashboard_data":    pr["dashboard_data"],
                    "language_data":     pr["language_data"],
                }

        # push subscriptions
        if table_exists(conn, "lugal_push_subscription"):
            cur.execute("""
                SELECT endpoint, auth_key, p256dh_key, user_agent
                FROM   lugal_push_subscription
                WHERE  user_id = %s AND active = true
            """, (uid,))
            user_rec["push_subscriptions"] = [dict(r) for r in cur.fetchall()]

        export["users"].append(user_rec)

        grp_count   = len(user_rec["groups"])
        email_count = len(user_rec["email_accounts"])
        print(f"  {G}✓{X}  {login:<35} groups={grp_count}  emails={email_count}")

    return export


def main():
    parser = argparse.ArgumentParser(description="Export Lugal users to JSON")
    parser.add_argument("--source", default="lugal_ws_sandbox")
    parser.add_argument("--out",    default="users_export.json",
                        help="Output JSON file path (default: users_export.json)")
    args = parser.parse_args()

    print(f"\n{C}Lugal Users Export{X}")
    print(f"  Source : {G}{args.source}{X}")
    print(f"  Output : {G}{args.out}{X}")

    try:
        conn = connect(args.source)
    except Exception as e:
        print(f"{R}Connection failed: {e}{X}"); sys.exit(1)

    try:
        data = export_users(conn, args.source)
    finally:
        conn.close()

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=serialize)

    print(f"\n{G}━━ Export Complete ━━{X}")
    print(f"  Users exported : {G}{data['meta']['user_count']}{X}")
    print(f"  File           : {G}{args.out}{X}")
    import os
    size_kb = os.path.getsize(args.out) / 1024
    print(f"  Size           : {G}{size_kb:.1f} KB{X}")


if __name__ == "__main__":
    main()
