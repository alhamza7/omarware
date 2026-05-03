#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
One-off script to fix perfume_* tables:
- Convert JSONB translation fields (name/country/description/...) to plain text/varchar
  by extracting the 'en_US' value.

Safe to run multiple times; if a column is already varchar/text it will raise and be skipped.
"""

import configparser

import psycopg2


def main() -> None:
    cfg = configparser.ConfigParser()
    cfg.read("odoo.conf")

    opts = cfg["options"]
    dbname = "lugal"
    user = opts.get("db_user")
    password = opts.get("db_password")
    host = opts.get("db_host", "localhost")
    port = opts.get("db_port", "5432")

    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port,
    )
    cur = conn.cursor()

    statements = [
        # perfume_brand
        "ALTER TABLE perfume_brand "
        "ALTER COLUMN name    TYPE varchar USING name->>'en_US', "
        "ALTER COLUMN country TYPE varchar USING country->>'en_US'",
        # perfume_perfume
        "ALTER TABLE perfume_perfume "
        "ALTER COLUMN name        TYPE varchar USING name->>'en_US', "
        "ALTER COLUMN brand_name  TYPE varchar USING brand_name->>'en_US', "
        "ALTER COLUMN description TYPE text    USING description->>'en_US', "
        "ALTER COLUMN longevity   TYPE varchar USING longevity->>'en_US', "
        "ALTER COLUMN sillage     TYPE varchar USING sillage->>'en_US'",
        # perfume_note
        "ALTER TABLE perfume_note "
        "ALTER COLUMN name TYPE varchar USING name->>'en_US'",
        # perfume_season
        "ALTER TABLE perfume_season "
        "ALTER COLUMN name TYPE varchar USING name->>'en_US'",
        # perfume_occasion
        "ALTER TABLE perfume_occasion "
        "ALTER COLUMN name TYPE varchar USING name->>'en_US'",
    ]

    for sql in statements:
        print("EXEC:", sql)
        try:
            cur.execute(sql)
        except Exception as e:  # noqa: BLE001
            # If the column is already varchar/text, just log and continue
            print("  -> ERROR (ignored):", e)

    conn.commit()
    cur.close()
    conn.close()
    print("Done fixing perfume_* text columns.")


if __name__ == "__main__":
    main()


