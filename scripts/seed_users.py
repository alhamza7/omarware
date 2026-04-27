#!/usr/bin/env python3
"""
Lugal Users Seeder
==================
Migrates all internal users (with email accounts) from SOURCE_DB → TARGET_DB.

Usage:
    python3 scripts/seed_users.py [--source lugal_local] [--target lugal_ws_sandbox] [--dry-run]

What it migrates:
    1. res_partner  — user contact record (name, email, phone, avatar, lang, tz)
    2. res_users    — login, hashed password, active, settings
    3. res_groups_users_rel — roles/permissions (matched by group xml_id across DBs)
    4. lugal_email_account  — IMAP/SMTP email accounts linked to each user
"""

import argparse
import sys
import psycopg2
import psycopg2.extras

# ── default config ────────────────────────────────────────────────────────────
DEFAULT_SOURCE = "lugal_local"
DEFAULT_TARGET = "lugal_ws_sandbox"
DB_HOST        = None          # None → Unix socket (peer auth)
DB_PORT        = 5432
DB_USER        = None          # None → use OS user (peer auth)

SKIP_LOGINS    = {"__system__", "__public__"}   # never migrate system accounts


# ── helpers ───────────────────────────────────────────────────────────────────

def connect(dbname):
    kwargs = dict(dbname=dbname)
    if DB_HOST:
        kwargs["host"] = DB_HOST
        kwargs["port"] = DB_PORT
    if DB_USER:
        kwargs["user"] = DB_USER
    return psycopg2.connect(**kwargs)


def fetch_all(cur, sql, params=None):
    cur.execute(sql, params or ())
    return cur.fetchall()


def row_dict(cur, sql, params=None):
    cur2 = cur.connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur2.execute(sql, params or ())
    rows = cur2.fetchall()
    cur2.close()
    return [dict(r) for r in rows]


# ── colour output ─────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
CYAN   = "\033[96m"

def ok(msg):   print(f"  {GREEN}✓{RESET}  {msg}")
def skip(msg): print(f"  {YELLOW}→{RESET}  {msg}")
def err(msg):  print(f"  {RED}✗{RESET}  {msg}")
def info(msg): print(f"  {CYAN}•{RESET}  {msg}")


# ── core migration ─────────────────────────────────────────────────────────────

def build_group_xml_map(cur):
    """Returns {xml_id: group_id} for the given DB."""
    rows = fetch_all(cur, """
        SELECT imd.module || '.' || imd.name AS xml_id, imd.res_id
        FROM   ir_model_data imd
        WHERE  imd.model = 'res.groups'
    """)
    return {row[0]: row[1] for row in rows}


def migrate_users(src_conn, tgt_conn, dry_run=False):
    src = src_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    tgt = tgt_conn.cursor()

    # ── load source users ─────────────────────────────────────────────────────
    src.execute("""
        SELECT
            u.id            AS src_uid,
            u.login,
            u.password,
            u.active,
            u.share,
            u.notification_type,
            u.preferred_nbs_language,
            u.tour_enabled,
            u.signature,
            u.out_of_office_message,
            -- partner fields
            p.name,
            p.email,
            p.phone,
            p.mobile,
            p.lang,
            p.tz,
            p.street,
            p.street2,
            p.city,
            p.zip,
            p.comment       AS partner_comment
        FROM res_users u
        JOIN res_partner p ON p.id = u.partner_id
        WHERE u.share = false
          AND u.login NOT IN %s
        ORDER BY u.id
    """, (tuple(SKIP_LOGINS),))

    users = src.fetchall()
    print(f"\n{CYAN}Found {len(users)} users to migrate from source DB{RESET}\n")

    # ── build group xml_id maps for both DBs ──────────────────────────────────
    src_group_map = build_group_xml_map(src_conn.cursor())   # xml_id → src_gid
    tgt_group_map = build_group_xml_map(tgt_conn.cursor())   # xml_id → tgt_gid
    src_gid_to_xml = {v: k for k, v in src_group_map.items()}

    stats = {"created": 0, "updated": 0, "skipped": 0, "emails_created": 0, "emails_updated": 0}

    for u in users:
        login   = u["login"]
        src_uid = u["src_uid"]

        print(f"  {CYAN}━━ {login} ({u['name']}){RESET}")

        # ── check if user exists in target ────────────────────────────────────
        tgt.execute("SELECT id, partner_id FROM res_users WHERE login = %s", (login,))
        existing = tgt.fetchone()

        if dry_run:
            if existing:
                skip(f"[DRY-RUN] would UPDATE user '{login}' (id={existing[0]})")
            else:
                ok(f"[DRY-RUN] would CREATE user '{login}'")
            stats["created" if not existing else "updated"] += 1
            continue

        if existing:
            tgt_uid, tgt_pid = existing

            # Update partner
            tgt.execute("""
                UPDATE res_partner SET
                    name         = %s,
                    email        = %s,
                    phone        = %s,
                    mobile       = %s,
                    lang         = %s,
                    tz           = %s,
                    street       = %s,
                    street2      = %s,
                    city         = %s,
                    zip          = %s,
                    comment      = %s
                WHERE id = %s
            """, (
                u["name"], u["email"], u["phone"], u["mobile"],
                u["lang"], u["tz"],
                u["street"], u["street2"], u["city"], u["zip"],
                u["partner_comment"], tgt_pid
            ))

            # Update user
            tgt.execute("""
                UPDATE res_users SET
                    password               = %s,
                    active                 = %s,
                    notification_type      = %s,
                    preferred_nbs_language = %s,
                    tour_enabled           = %s,
                    signature              = %s,
                    out_of_office_message  = %s
                WHERE id = %s
            """, (
                u["password"], u["active"], u["notification_type"],
                u["preferred_nbs_language"], u["tour_enabled"],
                u["signature"], u["out_of_office_message"], tgt_uid
            ))

            skip(f"Updated existing user '{login}' (tgt_id={tgt_uid})")
            stats["updated"] += 1

        else:
            # Create partner first
            tgt.execute("""
                INSERT INTO res_partner
                    (name, email, phone, mobile, lang, tz, active,
                     street, street2, city, zip, comment,
                     customer_rank, supplier_rank, is_company,
                     type, autopost_bills, group_rfq, group_on)
                VALUES
                    (%s,%s,%s,%s,%s,%s,true,
                     %s,%s,%s,%s,%s,
                     0, 0, false,
                     'contact', 'ask', 'default', 'default')
                RETURNING id
            """, (
                u["name"], u["email"], u["phone"], u["mobile"],
                u["lang"] or "en_US", u["tz"],
                u["street"], u["street2"], u["city"], u["zip"],
                u["partner_comment"]
            ))
            tgt_pid = tgt.fetchone()[0]

            # Get default company_id from target
            tgt.execute("SELECT id FROM res_company ORDER BY id LIMIT 1")
            company_id = tgt.fetchone()[0]

            tgt.execute("""
                INSERT INTO res_users
                    (login, password, active, share, notification_type,
                     preferred_nbs_language, tour_enabled, signature,
                     out_of_office_message, partner_id, company_id)
                VALUES
                    (%s,%s,%s,%s,%s,
                     %s,%s,%s,
                     %s,%s,%s)
                RETURNING id
            """, (
                login, u["password"], u["active"], u["share"],
                u["notification_type"] or "email",
                u["preferred_nbs_language"], u["tour_enabled"],
                u["signature"], u["out_of_office_message"],
                tgt_pid, company_id
            ))
            tgt_uid = tgt.fetchone()[0]

            ok(f"Created user '{login}' (tgt_id={tgt_uid}, partner_id={tgt_pid})")
            stats["created"] += 1

        # ── sync groups ───────────────────────────────────────────────────────
        src.execute("SELECT gid FROM res_groups_users_rel WHERE uid = %s", (src_uid,))
        src_gids = [r["gid"] for r in src.fetchall()]

        groups_added = 0
        groups_skipped = 0
        for src_gid in src_gids:
            xml_id = src_gid_to_xml.get(src_gid)
            if not xml_id:
                continue
            tgt_gid = tgt_group_map.get(xml_id)
            if not tgt_gid:
                groups_skipped += 1
                continue
            tgt.execute("""
                INSERT INTO res_groups_users_rel (uid, gid)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (tgt_uid, tgt_gid))
            groups_added += 1

        info(f"Groups: {groups_added} synced, {groups_skipped} xml_ids not found in target")

        # ── sync email accounts ───────────────────────────────────────────────
        src.execute("""
            SELECT email_address, display_name_field, name, is_active, is_default,
                   imap_host, imap_port, imap_use_ssl, imap_inbox_max_uid,
                   smtp_host, smtp_port, smtp_use_tls,
                   username, password, sync_status, active
            FROM   lugal_email_account
            WHERE  user_id = %s AND is_deleted IS NOT TRUE
            ORDER BY id
        """, (src_uid,))
        email_accounts = src.fetchall()

        for ea in email_accounts:
            email_address      = ea["email_address"]
            display_name_field = ea["display_name_field"]
            acc_name           = ea["name"]
            is_active          = ea["is_active"]
            is_default         = ea["is_default"]
            imap_host          = ea["imap_host"]
            imap_port          = ea["imap_port"]
            imap_use_ssl       = ea["imap_use_ssl"]
            imap_inbox_max_uid = ea["imap_inbox_max_uid"]
            smtp_host          = ea["smtp_host"]
            smtp_port          = ea["smtp_port"]
            smtp_use_tls       = ea["smtp_use_tls"]
            username           = ea["username"]
            pwd                = ea["password"]
            sync_status        = ea["sync_status"]
            ea_active          = ea["active"]

            # Check if account exists in target for this user
            tgt.execute("""
                SELECT id FROM lugal_email_account
                WHERE user_id = %s AND email_address = %s
            """, (tgt_uid, email_address))
            existing_ea = tgt.fetchone()

            if existing_ea:
                tgt.execute("""
                    UPDATE lugal_email_account SET
                        display_name_field  = %s,
                        name                = %s,
                        is_active           = %s,
                        is_default          = %s,
                        imap_host           = %s,
                        imap_port           = %s,
                        imap_use_ssl        = %s,
                        smtp_host           = %s,
                        smtp_port           = %s,
                        smtp_use_tls        = %s,
                        username            = %s,
                        password            = %s,
                        sync_status         = %s,
                        active              = %s
                    WHERE id = %s
                """, (
                    display_name_field, acc_name, is_active, is_default,
                    imap_host, imap_port, imap_use_ssl,
                    smtp_host, smtp_port, smtp_use_tls,
                    username, pwd, sync_status, ea_active,
                    existing_ea[0]
                ))
                info(f"Email account updated: {email_address}")
                stats["emails_updated"] += 1
            else:
                tgt.execute("""
                    INSERT INTO lugal_email_account
                        (user_id, email_address, display_name_field, name,
                         is_active, is_default,
                         imap_host, imap_port, imap_use_ssl,
                         smtp_host, smtp_port, smtp_use_tls,
                         username, password,
                         sync_status, active, is_deleted,
                         unread_count)
                    VALUES
                        (%s,%s,%s,%s,
                         %s,%s,
                         %s,%s,%s,
                         %s,%s,%s,
                         %s,%s,
                         %s,%s,false,
                         0)
                """, (
                    tgt_uid, email_address, display_name_field, acc_name,
                    is_active, is_default,
                    imap_host, imap_port, imap_use_ssl,
                    smtp_host, smtp_port, smtp_use_tls,
                    username, pwd,
                    sync_status, ea_active
                ))
                info(f"Email account created: {email_address}")
                stats["emails_created"] += 1

    tgt_conn.commit()
    return stats


# ── entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Migrate Odoo users between databases")
    parser.add_argument("--source",  default=DEFAULT_SOURCE, help=f"Source DB name (default: {DEFAULT_SOURCE})")
    parser.add_argument("--target",  default=DEFAULT_TARGET, help=f"Target DB name (default: {DEFAULT_TARGET})")
    parser.add_argument("--dry-run", action="store_true",   help="Preview only — no writes")
    args = parser.parse_args()

    print(f"\n{CYAN}Lugal Users Seeder{RESET}")
    print(f"  Source : {GREEN}{args.source}{RESET}")
    print(f"  Target : {GREEN}{args.target}{RESET}")
    if args.dry_run:
        print(f"  Mode   : {YELLOW}DRY RUN (no changes will be written){RESET}")
    print()

    try:
        src_conn = connect(args.source)
        tgt_conn = connect(args.target)
    except Exception as e:
        print(f"{RED}Failed to connect: {e}{RESET}")
        sys.exit(1)

    try:
        stats = migrate_users(src_conn, tgt_conn, dry_run=args.dry_run)
    except Exception as e:
        tgt_conn.rollback()
        print(f"\n{RED}Error during migration — rolled back: {e}{RESET}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        src_conn.close()
        tgt_conn.close()

    print(f"\n{GREEN}━━ Migration Complete ━━{RESET}")
    print(f"  Users created   : {GREEN}{stats['created']}{RESET}")
    print(f"  Users updated   : {YELLOW}{stats['updated']}{RESET}")
    print(f"  Email accounts created : {GREEN}{stats['emails_created']}{RESET}")
    print(f"  Email accounts updated : {YELLOW}{stats['emails_updated']}{RESET}")
    if args.dry_run:
        print(f"\n  {YELLOW}Dry run — nothing was written to the database.{RESET}")


if __name__ == "__main__":
    main()
