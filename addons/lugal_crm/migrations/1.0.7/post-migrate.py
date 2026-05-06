# -*- coding: utf-8 -*-
"""Ensure lugal.crm.supply.po has exchange_rate column (see crm_supply_po_extend.exchange_rate)."""


def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE lugal_crm_supply_po
        ADD COLUMN IF NOT EXISTS exchange_rate DOUBLE PRECISION;
        """
    )
