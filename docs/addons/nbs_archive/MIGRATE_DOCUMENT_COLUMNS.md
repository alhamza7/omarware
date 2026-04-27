# Fix: column "is_deleted" of relation "nbs_document" does not exist

This error means the database table `nbs_document` is missing columns that the module expects (e.g. after adding soft-delete or folder fields). Apply **one** of the following.

## Option 1: Upgrade the module (recommended)

Stop Odoo, then run (use another port if Odoo usually runs on 8070):

```bash
cd /path/to/Lugal-ai
./venv/bin/python odoo-bin -c odoo_local.conf -d lugal_local -u nbs_archive --stop-after-init -p 8079
```

Then start Odoo again. The ORM will add any missing columns.

## Option 2: Run the Python migration script

From the repo root, with DB password set:

```bash
export PGPASSWORD=your_db_password
./venv/bin/python addons/nbs_archive/scripts/add_missing_nbs_document_columns.py -d lugal_local -U capo7amzah
```

Or with Odoo config file (reads `db_name`, `db_user`, etc.):

```bash
export PGPASSWORD=your_db_password
./venv/bin/python addons/nbs_archive/scripts/add_missing_nbs_document_columns.py -c odoo_local.conf
```

## Option 3: Run the SQL file manually

```bash
psql -U capo7amzah -d lugal_local -f addons/nbs_archive/data/migrate_nbs_document_columns.sql
```

After any option, try uploading a document again.
