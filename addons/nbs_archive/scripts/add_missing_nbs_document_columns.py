#!/usr/bin/env python3
"""
Add missing columns to nbs_document table (is_deleted, folder_role, etc.).
Run from repo root: python addons/nbs_archive/scripts/add_missing_nbs_document_columns.py
Or with Odoo config: python addons/nbs_archive/scripts/add_missing_nbs_document_columns.py -c odoo_local.conf -d lugal_local
"""
import sys
import os

# Allow running from repo root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

def run_migration(db_name=None, db_user=None, db_host=None, db_port=None, db_password=None):
    try:
        import psycopg2
    except ImportError:
        print("Install psycopg2: pip install psycopg2-binary")
        return False

    db_name = db_name or os.environ.get('PGDATABASE', 'lugal_local')
    db_user = db_user or os.environ.get('PGUSER', 'capo7amzah')
    db_host = db_host or os.environ.get('PGHOST', 'localhost')
    db_port = db_port or os.environ.get('PGPORT', '5432')
    db_password = db_password or os.environ.get('PGPASSWORD', '')

    conn = psycopg2.connect(
        dbname=db_name,
        user=db_user,
        host=db_host,
        port=db_port,
        password=db_password or None,
    )
    conn.autocommit = True
    cur = conn.cursor()

    steps = [
        ("is_deleted", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE"),
        ("deleted_at", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP"),
        ("deleted_by_id", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES res_users(id)"),
        ("deletion_reason", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deletion_reason TEXT"),
        ("restore_deadline", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS restore_deadline TIMESTAMP"),
        ("state_before_trash", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS state_before_trash VARCHAR"),
        ("folder_role", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS folder_role VARCHAR"),
        ("is_attachment", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_attachment BOOLEAN DEFAULT FALSE"),
        ("parent_document_id", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS parent_document_id INTEGER REFERENCES nbs_document(id)"),
        ("indexed_in_search", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS indexed_in_search BOOLEAN DEFAULT FALSE"),
        ("last_indexed_date", "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS last_indexed_date TIMESTAMP"),
    ]

    for name, sql in steps:
        try:
            cur.execute(sql)
            print(f"  OK: {name}")
        except Exception as e:
            print(f"  Skip {name}: {e}")

    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_nbs_document_is_deleted ON nbs_document(is_deleted)")
        print("  OK: index idx_nbs_document_is_deleted")
    except Exception as e:
        print(f"  Skip index: {e}")

    try:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_nbs_document_folder_role ON nbs_document(folder_role)")
        print("  OK: index idx_nbs_document_folder_role")
    except Exception as e:
        print(f"  Skip index: {e}")

    cur.close()
    conn.close()
    print("Migration done.")
    return True


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Add missing nbs_document columns (is_deleted, folder_role, etc.)')
    p.add_argument('-c', '--config', help='Odoo config file (e.g. odoo_local.conf) to read db_* from')
    p.add_argument('-d', '--database', default='lugal_local', help='Database name')
    p.add_argument('-U', '--user', default='capo7amzah', help='DB user')
    p.add_argument('-H', '--host', default='localhost', help='DB host')
    p.add_argument('-p', '--port', default='5432', help='DB port')
    p.add_argument('-W', '--password', default='', help='DB password (or set PGPASSWORD)')
    args = p.parse_args()

    if args.config and os.path.isfile(args.config):
        with open(args.config) as f:
            for line in f:
                line = line.strip()
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    k, v = k.strip(), v.strip()
                    if k == 'db_name' and v: args.database = v
                    elif k == 'db_user' and v: args.user = v
                    elif k == 'db_host' and v: args.host = v
                    elif k == 'db_port' and v: args.port = v
                    elif k == 'db_password' and v: args.password = v

    run_migration(db_name=args.database, db_user=args.user, db_host=args.host, db_port=args.port, db_password=args.password or os.environ.get('PGPASSWORD', ''))
