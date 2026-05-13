# -*- coding: utf-8 -*-
"""Ensure container reminder columns exist (CRM extension on lugal.supply.container)."""


def migrate(cr, version):
    table = 'lugal_supply_container'
    cr.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (table,),
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        ALTER TABLE lugal_supply_container
        ADD COLUMN IF NOT EXISTS reminder_date timestamp without time zone;
        """
    )
    cr.execute(
        """
        ALTER TABLE lugal_supply_container
        ADD COLUMN IF NOT EXISTS reminder_note text;
        """
    )
