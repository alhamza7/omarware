# -*- coding: utf-8 -*-
"""Add extra_fields (Json) column when DB predates lugal.supply.dynamic.extra.mixin on models."""


def migrate(cr, version):
    tables = ('lugal_supply_item_request', 'lugal_supply_negotiation')
    for table in tables:
        cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = 'extra_fields'
            """,
            (table,),
        )
        if cr.fetchone():
            continue
        cr.execute(
            """
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'public'
              AND table_name = %s
            """,
            (table,),
        )
        if not cr.fetchone():
            continue
        cr.execute(
            'ALTER TABLE "%s" ADD COLUMN extra_fields jsonb DEFAULT \'{}\'::jsonb' % table
        )
        cr.execute(
            'UPDATE "%s" SET extra_fields = \'{}\'::jsonb WHERE extra_fields IS NULL' % table
        )
