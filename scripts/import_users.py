#!/usr/bin/env python3
"""
Lugal Users Import
==================
Imports user data from a JSON file (produced by export_users.py) into ANY target database.

Usage:
    python3 scripts/import_users.py --file users_export.json --target my_new_db [--dry-run]

What is imported:
    • res_partner               — contact record
    • res_users                 — login, hashed password, active, settings
    • res_groups_users_rel      — permissions (matched by xml_id)
    • res_company_users_rel     — company assignments (matched by name)
    • lugal_email_account       — IMAP/SMTP email accounts
    • res_users_settings        — Odoo discuss/notification settings
    • lugal_crm_user_preferences — CRM theme/dashboard/language prefs
    • lugal_push_subscription   — Web Push subscriptions
"""

import argparse
import json
import sys
import psycopg2
import psycopg2.extras

DB_HOST    = None
DB_PORT    = 5432
DB_USER    = None

C = "\033[96m"; G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; X = "\033[0m"
def ok(m):   print(f"  {G}✓{X}  {m}")
def skip(m): print(f"  {Y}→{X}  {m}")
def info(m): print(f"  {C}•{X}  {m}")


def connect(dbname):
    kw = dict(dbname=dbname)
    if DB_HOST: kw.update(host=DB_HOST, port=DB_PORT)
    if DB_USER: kw["user"] = DB_USER
    return psycopg2.connect(**kw)


def table_exists(conn, name):
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s", (name,))
    return cur.fetchone() is not None


def column_exists(conn, table, col):
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name=%s",
        (table, col))
    return cur.fetchone() is not None


def build_group_xml_map(conn):
    """Returns {xml_id: gid}"""
    cur = conn.cursor()
    cur.execute("""
        SELECT imd.module || '.' || imd.name, imd.res_id
        FROM   ir_model_data imd
        WHERE  imd.model = 'res.groups'
    """)
    return {r[0]: r[1] for r in cur.fetchall()}


def get_partner_nn_defaults(conn):
    """Return {col: default_value} for NOT NULL partner columns that need defaults."""
    defaults = {}
    for col in ["autopost_bills", "group_rfq", "group_on"]:
        if column_exists(conn, "res_partner", col):
            cur = conn.cursor()
            cur.execute(f"SELECT {col} FROM res_partner LIMIT 1")
            row = cur.fetchone()
            defaults[col] = row[0] if row else "default"
    return defaults


def import_users(data, tgt_conn, dry_run=False):
    tgt = tgt_conn.cursor()
    grp_map  = build_group_xml_map(tgt_conn)   # xml_id → gid
    nn_extra = get_partner_nn_defaults(tgt_conn)
    tgt_company = None
    cur = tgt_conn.cursor()
    cur.execute("SELECT id FROM res_company ORDER BY id LIMIT 1")
    row = cur.fetchone()
    if row: tgt_company = row[0]

    users = data.get("users", [])
    print(f"\n{C}Importing {len(users)} users into target DB...{X}\n")

    stats = {k: 0 for k in [
        "created", "updated",
        "emails_created", "emails_updated",
        "settings_synced",
        "prefs_synced",
        "push_synced",
        "companies_linked",
        "groups_synced",
    ]}

    for u in users:
        login = u["login"]
        p     = u.get("partner", {})
        print(f"  {C}━━ {login} ({p.get('name','')}){X}")

        if dry_run:
            tgt.execute("SELECT id FROM res_users WHERE login = %s", (login,))
            action = "UPDATE" if tgt.fetchone() else "CREATE"
            (skip if action == "UPDATE" else ok)(f"[DRY-RUN] would {action} '{login}'")
            stats["updated" if action == "UPDATE" else "created"] += 1
            continue

        # ── 1. res_partner + res_users ────────────────────────────────────────
        tgt.execute("SELECT id, partner_id FROM res_users WHERE login = %s", (login,))
        existing = tgt.fetchone()

        if existing:
            tgt_uid, tgt_pid = existing
            tgt.execute("""
                UPDATE res_partner
                SET name=%s, email=%s, phone=%s, mobile=%s,
                    lang=%s, tz=%s, street=%s, street2=%s,
                    city=%s, zip=%s, comment=%s
                WHERE id=%s
            """, (p.get("name"), p.get("email"), p.get("phone"), p.get("mobile"),
                  p.get("lang"), p.get("tz"), p.get("street"), p.get("street2"),
                  p.get("city"), p.get("zip"), p.get("comment"), tgt_pid))
            tgt.execute("""
                UPDATE res_users
                SET password=%s, active=%s, notification_type=%s,
                    preferred_nbs_language=%s, tour_enabled=%s,
                    signature=%s, out_of_office_message=%s
                WHERE id=%s
            """, (u.get("password"), u.get("active"),
                  u.get("notification_type") or "email",
                  u.get("preferred_nbs_language"), u.get("tour_enabled"),
                  u.get("signature"), u.get("out_of_office_message"), tgt_uid))
            skip(f"Updated '{login}' (id={tgt_uid})")
            stats["updated"] += 1
        else:
            # build NOT NULL extras
            nn_cols = list(nn_extra.keys())
            nn_vals = [nn_extra[c] for c in nn_cols]
            nn_col_s = (", " + ", ".join(nn_cols)) if nn_cols else ""
            nn_ph_s  = (", " + ", ".join(["%s"]*len(nn_cols))) if nn_cols else ""

            tgt.execute(f"""
                INSERT INTO res_partner
                    (name, email, phone, mobile, lang, tz, active,
                     street, street2, city, zip, comment,
                     customer_rank, supplier_rank, is_company, type
                     {nn_col_s})
                VALUES (%s,%s,%s,%s,%s,%s,true,%s,%s,%s,%s,%s,0,0,false,'contact'{nn_ph_s})
                RETURNING id
            """, (p.get("name"), p.get("email"), p.get("phone"), p.get("mobile"),
                  p.get("lang") or "en_US", p.get("tz"),
                  p.get("street"), p.get("street2"), p.get("city"), p.get("zip"),
                  p.get("comment")) + tuple(nn_vals))
            tgt_pid = tgt.fetchone()[0]

            tgt.execute("""
                INSERT INTO res_users
                    (login, password, active, share, notification_type,
                     preferred_nbs_language, tour_enabled, signature,
                     out_of_office_message, partner_id, company_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (login, u.get("password"), u.get("active"), u.get("share", False),
                  u.get("notification_type") or "email",
                  u.get("preferred_nbs_language"), u.get("tour_enabled"),
                  u.get("signature"), u.get("out_of_office_message"),
                  tgt_pid, tgt_company))
            tgt_uid = tgt.fetchone()[0]
            ok(f"Created '{login}' (id={tgt_uid})")
            stats["created"] += 1

        # ── 2. groups ─────────────────────────────────────────────────────────
        added = 0
        for xml_id in u.get("groups", []):
            gid = grp_map.get(xml_id)
            if gid:
                tgt.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                            (tgt_uid, gid))
                added += 1
        stats["groups_synced"] += added
        info(f"Groups: {added} synced")

        # ── 3. companies ──────────────────────────────────────────────────────
        for company_name in u.get("companies", []):
            tgt.execute("SELECT id FROM res_company WHERE name = %s", (company_name,))
            row = tgt.fetchone()
            if row:
                tgt.execute(
                    "INSERT INTO res_company_users_rel (cid, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                    (row[0], tgt_uid))
                stats["companies_linked"] += 1

        # ── 4. email accounts ─────────────────────────────────────────────────
        for ea in u.get("email_accounts", []):
            tgt.execute("SELECT id FROM lugal_email_account WHERE user_id=%s AND email_address=%s",
                        (tgt_uid, ea["email_address"]))
            ex = tgt.fetchone()
            if ex:
                tgt.execute("""
                    UPDATE lugal_email_account
                    SET display_name_field=%s, name=%s,
                        is_active=%s, is_default=%s, active=%s,
                        imap_host=%s, imap_port=%s, imap_use_ssl=%s,
                        smtp_host=%s, smtp_port=%s, smtp_use_tls=%s,
                        username=%s, password=%s, sync_status=%s
                    WHERE id=%s
                """, (ea.get("display_name_field"), ea.get("name"),
                      ea.get("is_active"), ea.get("is_default"),
                      ea.get("active", True),
                      ea.get("imap_host"), ea.get("imap_port"), ea.get("imap_use_ssl"),
                      ea.get("smtp_host"), ea.get("smtp_port"), ea.get("smtp_use_tls"),
                      ea.get("username"), ea.get("password"), ea.get("sync_status"),
                      ex[0]))
                info(f"Email updated: {ea['email_address']}")
                stats["emails_updated"] += 1
            else:
                tgt.execute("""
                    INSERT INTO lugal_email_account
                        (user_id, email_address, display_name_field, name,
                         is_active, is_default, active, is_deleted,
                         imap_host, imap_port, imap_use_ssl,
                         smtp_host, smtp_port, smtp_use_tls,
                         username, password, sync_status, unread_count)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,false,%s,%s,%s,%s,%s,%s,%s,%s,%s,0)
                """, (tgt_uid, ea["email_address"], ea.get("display_name_field"),
                      ea.get("name"), ea.get("is_active"), ea.get("is_default"),
                      ea.get("active", True),
                      ea.get("imap_host"), ea.get("imap_port"), ea.get("imap_use_ssl"),
                      ea.get("smtp_host"), ea.get("smtp_port"), ea.get("smtp_use_tls"),
                      ea.get("username"), ea.get("password"), ea.get("sync_status")))
                info(f"Email created: {ea['email_address']}")
                stats["emails_created"] += 1

        # ── 5. odoo settings ──────────────────────────────────────────────────
        rs = u.get("odoo_settings")
        if rs and table_exists(tgt_conn, "res_users_settings"):
            tgt.execute("SELECT id FROM res_users_settings WHERE user_id = %s", (tgt_uid,))
            ex = tgt.fetchone()
            fields = ("voice_active_duration", "push_to_talk_key", "channel_notifications",
                      "is_discuss_sidebar_category_channel_open",
                      "is_discuss_sidebar_category_chat_open", "use_push_to_talk")
            vals = tuple(rs.get(f) for f in fields)
            if ex:
                set_clause = ", ".join(f"{f}=%s" for f in fields)
                tgt.execute(f"UPDATE res_users_settings SET {set_clause} WHERE id=%s",
                            vals + (ex[0],))
            else:
                cols = ", ".join(fields)
                phs  = ", ".join(["%s"] * len(fields))
                tgt.execute(f"INSERT INTO res_users_settings (user_id, {cols}) VALUES (%s, {phs})",
                            (tgt_uid,) + vals)
            stats["settings_synced"] += 1
            info("Odoo settings synced")

        # ── 6. crm preferences ────────────────────────────────────────────────
        pr = u.get("crm_preferences")
        if pr and table_exists(tgt_conn, "lugal_crm_user_preferences"):
            tgt.execute("SELECT id FROM lugal_crm_user_preferences WHERE user_id = %s", (tgt_uid,))
            ex = tgt.fetchone()
            if ex:
                tgt.execute("""
                    UPDATE lugal_crm_user_preferences
                    SET theme_data=%s, notification_data=%s,
                        dashboard_data=%s, language_data=%s
                    WHERE id=%s
                """, (pr.get("theme_data"), pr.get("notification_data"),
                      pr.get("dashboard_data"), pr.get("language_data"), ex[0]))
            else:
                tgt.execute("""
                    INSERT INTO lugal_crm_user_preferences
                        (user_id, theme_data, notification_data, dashboard_data, language_data)
                    VALUES (%s,%s,%s,%s,%s)
                """, (tgt_uid, pr.get("theme_data"), pr.get("notification_data"),
                      pr.get("dashboard_data"), pr.get("language_data")))
            stats["prefs_synced"] += 1
            info("CRM preferences synced")

        # ── 7. push subscriptions ─────────────────────────────────────────────
        for ps in u.get("push_subscriptions", []):
            if not table_exists(tgt_conn, "lugal_push_subscription"): break
            tgt.execute("SELECT id FROM lugal_push_subscription WHERE user_id=%s AND endpoint=%s",
                        (tgt_uid, ps["endpoint"]))
            if not tgt.fetchone():
                tgt.execute("""
                    INSERT INTO lugal_push_subscription
                        (user_id, endpoint, auth_key, p256dh_key, user_agent, active)
                    VALUES (%s,%s,%s,%s,%s,true)
                """, (tgt_uid, ps["endpoint"], ps.get("auth_key"),
                      ps.get("p256dh_key"), ps.get("user_agent")))
                stats["push_synced"] += 1
                info("Push subscription synced")

    tgt_conn.commit()
    return stats


def main():
    parser = argparse.ArgumentParser(description="Import Lugal users from JSON file")
    parser.add_argument("--file",    required=True,             help="Path to users_export.json")
    parser.add_argument("--target",  default="lugal_ws_sandbox", help="Target database name")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n{C}Lugal Users Import{X}")
    print(f"  File   : {G}{args.file}{X}")
    print(f"  Target : {G}{args.target}{X}")
    if args.dry_run:
        print(f"  Mode   : {Y}DRY RUN — no changes will be written{X}")

    try:
        with open(args.file, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"{R}File not found: {args.file}{X}"); sys.exit(1)

    meta = data.get("meta", {})
    print(f"\n  Exported from : {C}{meta.get('source_db','?')}{X}")
    print(f"  Exported at   : {C}{meta.get('exported_at','?')}{X}")
    print(f"  Users in file : {C}{meta.get('user_count','?')}{X}")

    try:
        tgt_conn = connect(args.target)
    except Exception as e:
        print(f"{R}Connection failed: {e}{X}"); sys.exit(1)

    try:
        stats = import_users(data, tgt_conn, dry_run=args.dry_run)
    except Exception as e:
        tgt_conn.rollback()
        import traceback; traceback.print_exc()
        print(f"\n{R}Import failed — rolled back: {e}{X}"); sys.exit(1)
    finally:
        tgt_conn.close()

    w = 28
    print(f"\n{G}{'━'*w} Import Complete {'━'*w}{X}")
    rows = [
        ("Users created",          "created"),
        ("Users updated",          "updated"),
        ("Group assignments",      "groups_synced"),
        ("Company links",          "companies_linked"),
        ("Email accounts created", "emails_created"),
        ("Email accounts updated", "emails_updated"),
        ("Odoo settings synced",   "settings_synced"),
        ("CRM prefs synced",       "prefs_synced"),
        ("Push subscriptions",     "push_synced"),
    ]
    for label, key in rows:
        v = stats[key]
        colour = G if v > 0 else X
        print(f"  {label:<28}: {colour}{v}{X}")

    if args.dry_run:
        print(f"\n  {Y}Dry run — nothing was written.{X}")


if __name__ == "__main__":
    main()
