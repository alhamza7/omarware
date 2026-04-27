#!/usr/bin/env python3
"""
Lugal Complete Users Seeder
============================
Migrates ALL user-related data from SOURCE_DB → TARGET_DB.

Usage:
    python3 scripts/seed_users.py [--source lugal_local] [--target lugal_ws_sandbox] [--dry-run]

Tables migrated (in order):
    1.  res_partner              — contact record (name, email, phone, lang, tz, address)
    2.  res_users                — login, hashed password, active, settings
    3.  res_groups_users_rel     — roles & permissions (matched by xml_id)
    4.  res_company_users_rel    — multi-company access
    5.  lugal_email_account      — IMAP/SMTP email accounts
    6.  res_users_settings       — Odoo discuss / notification settings
    7.  lugal_crm_user_preferences — CRM theme, dashboard, notification prefs
    8.  lugal_push_subscription  — Web Push subscriptions
"""

import argparse
import sys
import psycopg2
import psycopg2.extras

# ── config ────────────────────────────────────────────────────────────────────
DEFAULT_SOURCE = "lugal_local"
DEFAULT_TARGET = "lugal_ws_sandbox"
DB_HOST        = None           # None → Unix socket (peer auth)
DB_PORT        = 5432
DB_USER        = None

SKIP_LOGINS    = {"__system__", "__public__"}

# ── colours ───────────────────────────────────────────────────────────────────
G = "\033[92m"; Y = "\033[93m"; R = "\033[91m"; C = "\033[96m"; X = "\033[0m"
def ok(m):   print(f"  {G}✓{X}  {m}")
def skip(m): print(f"  {Y}→{X}  {m}")
def err(m):  print(f"  {R}✗{X}  {m}")
def info(m): print(f"  {C}•{X}  {m}")


# ── helpers ───────────────────────────────────────────────────────────────────
def connect(dbname):
    kw = dict(dbname=dbname)
    if DB_HOST: kw.update(host=DB_HOST, port=DB_PORT)
    if DB_USER: kw["user"] = DB_USER
    return psycopg2.connect(**kw)


def dict_cursor(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def scalar(conn, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    return row[0] if row else None


def table_exists(conn, name):
    return scalar(conn,
        "SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s",
        (name,)) is not None


def column_exists(conn, table, col):
    return scalar(conn,
        "SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name=%s AND column_name=%s",
        (table, col)) is not None


# ── group xml_id maps ─────────────────────────────────────────────────────────
def build_group_map(conn):
    """Returns {xml_id: gid} for the DB."""
    cur = conn.cursor()
    cur.execute("""
        SELECT imd.module || '.' || imd.name, imd.res_id
        FROM   ir_model_data imd
        WHERE  imd.model = 'res.groups'
    """)
    return {r[0]: r[1] for r in cur.fetchall()}


# ── NOT NULL defaults for res_partner (differ between DB versions) ────────────
def partner_nn_defaults(conn):
    """Return dict of col→default for NOT NULL non-trivial partner columns."""
    defaults = {}
    nn_cols = ["autopost_bills", "group_rfq", "group_on"]
    for col in nn_cols:
        if column_exists(conn, "res_partner", col):
            val = scalar(conn, f"SELECT {col} FROM res_partner LIMIT 1")
            defaults[col] = val or "default"
    return defaults


# ══════════════════════════════════════════════════════════════════════════════
def migrate_users(src_conn, tgt_conn, dry_run=False):
    src = dict_cursor(src_conn)
    tgt = tgt_conn.cursor()

    # ── pre-load maps ─────────────────────────────────────────────────────────
    src_grp   = build_group_map(src_conn)           # xml_id → src_gid
    tgt_grp   = build_group_map(tgt_conn)           # xml_id → tgt_gid
    src_gid2x = {v: k for k, v in src_grp.items()} # src_gid → xml_id

    tgt_nn = partner_nn_defaults(tgt_conn)          # NOT NULL extras for target

    # company_id fallback
    tgt_company = scalar(tgt_conn, "SELECT id FROM res_company ORDER BY id LIMIT 1")

    # ── load all source users ─────────────────────────────────────────────────
    src.execute("""
        SELECT
            u.id            AS src_uid,
            u.login, u.password, u.active, u.share,
            u.notification_type, u.preferred_nbs_language,
            u.tour_enabled, u.signature, u.out_of_office_message,
            u.company_id    AS src_company_id,
            p.name, p.email, p.phone, p.mobile,
            p.lang, p.tz, p.street, p.street2,
            p.city, p.zip, p.comment AS partner_comment
        FROM res_users u
        JOIN res_partner p ON p.id = u.partner_id
        WHERE u.share = false
          AND u.login NOT IN %s
        ORDER BY u.id
    """, (tuple(SKIP_LOGINS),))
    users = src.fetchall()

    print(f"\n{C}Found {len(users)} users in source DB{X}\n")

    stats = {k: 0 for k in [
        "created", "updated",
        "emails_created", "emails_updated",
        "settings_created", "settings_updated",
        "prefs_created", "prefs_updated",
        "push_created",
        "companies_linked",
    ]}

    for u in users:
        login   = u["login"]
        src_uid = u["src_uid"]
        print(f"  {C}━━ {login} ({u['name']}){X}")

        # ── 1. res_partner + res_users ────────────────────────────────────────
        tgt.execute("SELECT id, partner_id FROM res_users WHERE login = %s", (login,))
        existing = tgt.fetchone()

        if dry_run:
            action = "UPDATE" if existing else "CREATE"
            (skip if existing else ok)(f"[DRY-RUN] would {action} user '{login}'")
            stats["updated" if existing else "created"] += 1
            continue

        if existing:
            tgt_uid, tgt_pid = existing
            # update partner
            tgt.execute("""
                UPDATE res_partner
                SET name=%s, email=%s, phone=%s, mobile=%s,
                    lang=%s, tz=%s, street=%s, street2=%s,
                    city=%s, zip=%s, comment=%s
                WHERE id=%s
            """, (u["name"], u["email"], u["phone"], u["mobile"],
                  u["lang"], u["tz"], u["street"], u["street2"],
                  u["city"], u["zip"], u["partner_comment"], tgt_pid))
            # update user
            tgt.execute("""
                UPDATE res_users
                SET password=%s, active=%s, notification_type=%s,
                    preferred_nbs_language=%s, tour_enabled=%s,
                    signature=%s, out_of_office_message=%s
                WHERE id=%s
            """, (u["password"], u["active"],
                  u["notification_type"] or "email",
                  u["preferred_nbs_language"], u["tour_enabled"],
                  u["signature"], u["out_of_office_message"], tgt_uid))
            skip(f"Updated user '{login}' (tgt_id={tgt_uid})")
            stats["updated"] += 1
        else:
            # build extra NOT NULL columns for partner
            nn_cols = list(tgt_nn.keys())
            nn_vals = [tgt_nn[c] for c in nn_cols]
            nn_ph   = ", ".join(["%s"] * len(nn_cols))
            nn_col_str = (", " + ", ".join(nn_cols)) if nn_cols else ""
            nn_ph_str  = (", " + nn_ph) if nn_ph else ""

            tgt.execute(f"""
                INSERT INTO res_partner
                    (name, email, phone, mobile, lang, tz, active,
                     street, street2, city, zip, comment,
                     customer_rank, supplier_rank, is_company, type
                     {nn_col_str})
                VALUES
                    (%s,%s,%s,%s,%s,%s,true,
                     %s,%s,%s,%s,%s,
                     0, 0, false, 'contact'
                     {nn_ph_str})
                RETURNING id
            """, (u["name"], u["email"], u["phone"], u["mobile"],
                  u["lang"] or "en_US", u["tz"],
                  u["street"], u["street2"], u["city"], u["zip"],
                  u["partner_comment"]) + tuple(nn_vals))
            tgt_pid = tgt.fetchone()[0]

            tgt.execute("""
                INSERT INTO res_users
                    (login, password, active, share, notification_type,
                     preferred_nbs_language, tour_enabled, signature,
                     out_of_office_message, partner_id, company_id)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """, (login, u["password"], u["active"], u["share"],
                  u["notification_type"] or "email",
                  u["preferred_nbs_language"], u["tour_enabled"],
                  u["signature"], u["out_of_office_message"],
                  tgt_pid, tgt_company))
            tgt_uid = tgt.fetchone()[0]
            ok(f"Created user '{login}' (tgt_id={tgt_uid})")
            stats["created"] += 1

        # ── 2. groups / permissions ───────────────────────────────────────────
        tgt.execute("SELECT id, login FROM res_users WHERE id = %s", (src_uid,))  # just validate
        src_cur2 = src_conn.cursor()
        src_cur2.execute("SELECT gid FROM res_groups_users_rel WHERE uid = %s", (src_uid,))
        src_gids = [r[0] for r in src_cur2.fetchall()]
        added = skipped = 0
        for gid in src_gids:
            xml_id = src_gid2x.get(gid)
            if not xml_id: skipped += 1; continue
            tgt_gid = tgt_grp.get(xml_id)
            if not tgt_gid: skipped += 1; continue
            tgt.execute("INSERT INTO res_groups_users_rel (uid, gid) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        (tgt_uid, tgt_gid))
            added += 1
        info(f"Groups: {added} synced" + (f", {skipped} skipped" if skipped else ""))

        # ── 3. multi-company access ───────────────────────────────────────────
        src_cur2.execute("SELECT cid FROM res_company_users_rel WHERE user_id = %s", (src_uid,))
        for (src_cid,) in src_cur2.fetchall():
            src_cur2.execute("SELECT name FROM res_company WHERE id = %s", (src_cid,))
            row = src_cur2.fetchone()
            if not row: continue
            tgt.execute("SELECT id FROM res_company WHERE name = %s", (row[0],))
            tgt_row = tgt.fetchone()
            if not tgt_row: continue
            tgt.execute(
                "INSERT INTO res_company_users_rel (cid, user_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
                (tgt_row[0], tgt_uid))
            stats["companies_linked"] += 1

        # ── 4. lugal_email_account ────────────────────────────────────────────
        src.execute("""
            SELECT email_address, display_name_field, name,
                   is_active, is_default, active, is_deleted,
                   imap_host, imap_port, imap_use_ssl,
                   smtp_host, smtp_port, smtp_use_tls,
                   username, password, sync_status
            FROM   lugal_email_account
            WHERE  user_id = %s AND (is_deleted IS NOT TRUE)
        """, (src_uid,))
        for ea in src.fetchall():
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
                """, (ea["display_name_field"], ea["name"],
                      ea["is_active"], ea["is_default"], ea["active"],
                      ea["imap_host"], ea["imap_port"], ea["imap_use_ssl"],
                      ea["smtp_host"], ea["smtp_port"], ea["smtp_use_tls"],
                      ea["username"], ea["password"], ea["sync_status"],
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
                """, (tgt_uid, ea["email_address"], ea["display_name_field"],
                      ea["name"], ea["is_active"], ea["is_default"],
                      ea["active"] if ea["active"] is not None else True,
                      ea["imap_host"], ea["imap_port"], ea["imap_use_ssl"],
                      ea["smtp_host"], ea["smtp_port"], ea["smtp_use_tls"],
                      ea["username"], ea["password"], ea["sync_status"]))
                info(f"Email created: {ea['email_address']}")
                stats["emails_created"] += 1

        # ── 5. res_users_settings ─────────────────────────────────────────────
        src.execute("SELECT * FROM res_users_settings WHERE user_id = %s", (src_uid,))
        rs = src.fetchone()
        if rs:
            tgt.execute("SELECT id FROM res_users_settings WHERE user_id = %s", (tgt_uid,))
            ex = tgt.fetchone()
            if ex:
                tgt.execute("""
                    UPDATE res_users_settings
                    SET voice_active_duration=%s, push_to_talk_key=%s,
                        channel_notifications=%s,
                        is_discuss_sidebar_category_channel_open=%s,
                        is_discuss_sidebar_category_chat_open=%s,
                        use_push_to_talk=%s
                    WHERE id=%s
                """, (rs["voice_active_duration"], rs["push_to_talk_key"],
                      rs["channel_notifications"],
                      rs["is_discuss_sidebar_category_channel_open"],
                      rs["is_discuss_sidebar_category_chat_open"],
                      rs["use_push_to_talk"], ex[0]))
                stats["settings_updated"] += 1
            else:
                tgt.execute("""
                    INSERT INTO res_users_settings
                        (user_id, voice_active_duration, push_to_talk_key,
                         channel_notifications,
                         is_discuss_sidebar_category_channel_open,
                         is_discuss_sidebar_category_chat_open,
                         use_push_to_talk)
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
                """, (tgt_uid, rs["voice_active_duration"], rs["push_to_talk_key"],
                      rs["channel_notifications"],
                      rs["is_discuss_sidebar_category_channel_open"],
                      rs["is_discuss_sidebar_category_chat_open"],
                      rs["use_push_to_talk"]))
                stats["settings_created"] += 1
            info("Odoo settings synced")

        # ── 6. lugal_crm_user_preferences ────────────────────────────────────
        if table_exists(src_conn, "lugal_crm_user_preferences"):
            src.execute("SELECT * FROM lugal_crm_user_preferences WHERE user_id = %s", (src_uid,))
            pr = src.fetchone()
            if pr and table_exists(tgt_conn, "lugal_crm_user_preferences"):
                tgt.execute("SELECT id FROM lugal_crm_user_preferences WHERE user_id = %s", (tgt_uid,))
                ex = tgt.fetchone()
                if ex:
                    tgt.execute("""
                        UPDATE lugal_crm_user_preferences
                        SET theme_data=%s, notification_data=%s,
                            dashboard_data=%s, language_data=%s
                        WHERE id=%s
                    """, (pr["theme_data"], pr["notification_data"],
                          pr["dashboard_data"], pr["language_data"], ex[0]))
                    stats["prefs_updated"] += 1
                else:
                    tgt.execute("""
                        INSERT INTO lugal_crm_user_preferences
                            (user_id, theme_data, notification_data,
                             dashboard_data, language_data)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (tgt_uid, pr["theme_data"], pr["notification_data"],
                          pr["dashboard_data"], pr["language_data"]))
                    stats["prefs_created"] += 1
                info("CRM preferences synced")

        # ── 7. lugal_push_subscription ────────────────────────────────────────
        if table_exists(src_conn, "lugal_push_subscription"):
            src.execute("""
                SELECT endpoint, auth_key, p256dh_key, user_agent, active
                FROM   lugal_push_subscription
                WHERE  user_id = %s AND active = true
            """, (src_uid,))
            for ps in src.fetchall():
                if not table_exists(tgt_conn, "lugal_push_subscription"): break
                tgt.execute("SELECT id FROM lugal_push_subscription WHERE user_id=%s AND endpoint=%s",
                            (tgt_uid, ps["endpoint"]))
                if not tgt.fetchone():
                    tgt.execute("""
                        INSERT INTO lugal_push_subscription
                            (user_id, endpoint, auth_key, p256dh_key,
                             user_agent, active)
                        VALUES (%s,%s,%s,%s,%s,%s)
                    """, (tgt_uid, ps["endpoint"], ps["auth_key"],
                          ps["p256dh_key"], ps["user_agent"],
                          ps["active"]))
                    stats["push_created"] += 1
                    info(f"Push subscription synced")

    tgt_conn.commit()
    return stats


# ── entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Lugal Complete Users Seeder")
    parser.add_argument("--source",  default=DEFAULT_SOURCE)
    parser.add_argument("--target",  default=DEFAULT_TARGET)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print(f"\n{C}Lugal Complete Users Seeder{X}")
    print(f"  Source : {G}{args.source}{X}")
    print(f"  Target : {G}{args.target}{X}")
    if args.dry_run:
        print(f"  Mode   : {Y}DRY RUN — no changes will be written{X}")

    try:
        src_conn = connect(args.source)
        tgt_conn = connect(args.target)
    except Exception as e:
        print(f"{R}Connection failed: {e}{X}"); sys.exit(1)

    try:
        stats = migrate_users(src_conn, tgt_conn, dry_run=args.dry_run)
    except Exception as e:
        tgt_conn.rollback()
        import traceback; traceback.print_exc()
        print(f"\n{R}Migration failed — rolled back: {e}{X}"); sys.exit(1)
    finally:
        src_conn.close(); tgt_conn.close()

    w = 30
    print(f"\n{G}{'━'*w} Complete {'━'*w}{X}")
    labels = [
        ("Users created",           "created"),
        ("Users updated",           "updated"),
        ("Email accounts created",  "emails_created"),
        ("Email accounts updated",  "emails_updated"),
        ("Odoo settings created",   "settings_created"),
        ("Odoo settings updated",   "settings_updated"),
        ("CRM prefs created",       "prefs_created"),
        ("CRM prefs updated",       "prefs_updated"),
        ("Push subscriptions",      "push_created"),
        ("Company links",           "companies_linked"),
    ]
    for label, key in labels:
        v = stats[key]
        colour = G if "created" in key or "linked" in key else Y
        print(f"  {label:<28}: {colour}{v}{X}")

    if args.dry_run:
        print(f"\n  {Y}Dry run — nothing was written.{X}")


if __name__ == "__main__":
    main()
