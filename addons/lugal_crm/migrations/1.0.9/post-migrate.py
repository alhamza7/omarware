# -*- coding: utf-8 -*-
"""exchange_rate is stored in extra_fields (computed Float); migrate legacy column if present."""

import json


def migrate(cr, version):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'lugal_crm_supply_po'
          AND column_name = 'exchange_rate'
        """
    )
    if not cr.fetchone():
        return

    cr.execute(
        """
        SELECT id, extra_fields, exchange_rate
        FROM lugal_crm_supply_po
        """
    )
    rows = cr.fetchall()
    for rid, ef, rate in rows:
        data = {}
        if isinstance(ef, dict):
            data = dict(ef)
        elif isinstance(ef, str):
            try:
                data = dict(json.loads(ef))
            except (TypeError, ValueError, json.JSONDecodeError):
                data = {}
        if rate is None:
            continue
        try:
            f_rate = float(rate)
        except (TypeError, ValueError):
            continue
        if 'exchange_rate' in data:
            continue
        data['exchange_rate'] = f_rate
        cr.execute(
            "UPDATE lugal_crm_supply_po SET extra_fields = %s::jsonb WHERE id = %s",
            (json.dumps(data), rid),
        )

    cr.execute("ALTER TABLE lugal_crm_supply_po DROP COLUMN IF EXISTS exchange_rate")
