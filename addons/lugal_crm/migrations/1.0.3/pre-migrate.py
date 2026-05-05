# -*- coding: utf-8 -*-
"""Add CRM extension columns on lugal.supply.container when table predates the fields."""


def migrate(cr, version):
    table = 'lugal_supply_container'
    cr.execute(
        """
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table,),
    )
    if not cr.fetchone():
        return

    columns = (
        ('planned_gate_in_date', 'date'),
        ('actual_gate_in_at', 'timestamp without time zone'),
    )
    for col_name, col_type in columns:
        cr.execute(
            """
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = %s
              AND column_name = %s
            """,
            (table, col_name),
        )
        if cr.fetchone():
            continue
        cr.execute(
            'ALTER TABLE "%s" ADD COLUMN "%s" %s'
            % (table, col_name, col_type)
        )
