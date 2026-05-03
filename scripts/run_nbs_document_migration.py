#!/usr/bin/env python3
"""Run nbs_document column migration using Odoo's DB connection (no server)."""
import sys
import os

# Bootstrap Odoo (load config, no server)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import odoo
from odoo.tools import config

# Load config
config.parse_config(['-c', 'odoo_local.conf', '-d', 'lugal_local'])
odoo.tools.config.parse_config(['-c', 'odoo_local.conf', '-d', 'lugal_local'])

import odoo.sql_db

db_name = config['db_name']
if isinstance(db_name, list):
    db_name = db_name[0] if db_name else 'lugal_local'

print(f"Connecting to database: {db_name}")

try:
    db = odoo.sql_db.db_connect(db_name)
    cr = db.cursor()
except Exception as e:
    print(f"Connection error: {e}")
    sys.exit(1)

statements = [
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deleted_by_id INTEGER REFERENCES res_users(id)",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS deletion_reason TEXT",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS restore_deadline TIMESTAMP",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS state_before_trash VARCHAR",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS folder_role VARCHAR",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS is_attachment BOOLEAN DEFAULT FALSE",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS parent_document_id INTEGER REFERENCES nbs_document(id)",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS indexed_in_search BOOLEAN DEFAULT FALSE",
    "ALTER TABLE nbs_document ADD COLUMN IF NOT EXISTS last_indexed_date TIMESTAMP",
]

for sql in statements:
    try:
        cr.execute(sql)
        print("  OK:", sql[:60] + "..." if len(sql) > 60 else sql)
    except Exception as e:
        print("  Skip:", e)

try:
    cr.execute("CREATE INDEX IF NOT EXISTS idx_nbs_document_is_deleted ON nbs_document(is_deleted)")
    print("  OK: index idx_nbs_document_is_deleted")
except Exception as e:
    print("  Skip index:", e)

try:
    cr.execute("CREATE INDEX IF NOT EXISTS idx_nbs_document_folder_role ON nbs_document(folder_role)")
    print("  OK: index idx_nbs_document_folder_role")
except Exception as e:
    print("  Skip index:", e)

# nbs_document_version (approval_status, is_major, etc. from nbs_advanced_version)
print("\nnbs_document_version:")
version_stmts = [
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS approval_status VARCHAR",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS is_major BOOLEAN DEFAULT FALSE",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS approved_by_id INTEGER REFERENCES res_users(id)",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS rejection_reason TEXT",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS version_tag VARCHAR",
    "ALTER TABLE nbs_document_version ADD COLUMN IF NOT EXISTS diff_content TEXT",
]
for sql in version_stmts:
    try:
        cr.execute(sql)
        print("  OK:", sql[:55] + "..." if len(sql) > 55 else sql)
    except Exception as e:
        print("  Skip:", e)

cr.commit()
cr.close()
print("\nMigration done successfully.")
