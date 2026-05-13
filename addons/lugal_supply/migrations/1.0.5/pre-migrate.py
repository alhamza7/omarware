# -*- coding: utf-8 -*-
"""Move negotiation e-sign from legacy columns into extra_fields JSON, then drop columns.

If a database was updated while ``e_sign_user_id`` / ``e_sign_date`` existed on
``lugal_supply_negotiation``, copy values into ``extra_fields`` before those
columns are removed from the ORM model.
"""


def migrate(cr, version):
    cr.execute(
        """
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name = 'lugal_supply_negotiation'
          AND column_name = 'e_sign_user_id'
        """
    )
    if not cr.fetchone():
        return
    cr.execute(
        """
        UPDATE lugal_supply_negotiation AS n
        SET extra_fields = COALESCE(n.extra_fields, '{}'::jsonb)
            || jsonb_build_object(
                'negotiation_e_sign_user_id', n.e_sign_user_id,
                'negotiation_e_sign_date',
                CASE
                    WHEN n.e_sign_date IS NULL THEN NULL::text
                    ELSE to_char(n.e_sign_date AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                END
            )
        WHERE n.e_sign_user_id IS NOT NULL
        """
    )
    cr.execute('ALTER TABLE lugal_supply_negotiation DROP COLUMN IF EXISTS e_sign_user_id')
    cr.execute('ALTER TABLE lugal_supply_negotiation DROP COLUMN IF EXISTS e_sign_date')
