# -*- coding: utf-8 -*-
"""Ensure lugal.crm.supply.po.exchange_rate column exists (redundant with init + post_init_hook)."""


def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE lugal_crm_supply_po
        ADD COLUMN IF NOT EXISTS exchange_rate DOUBLE PRECISION;
        """
    )
