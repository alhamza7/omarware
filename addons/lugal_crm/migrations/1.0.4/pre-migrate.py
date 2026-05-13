# -*- coding: utf-8 -*-
"""Map legacy lugal.supply.payment.payment_type values to the FE-aligned selection.

Old keys: partial, full (and any stray values) → installment, final.
"""


def migrate(cr, version):
    table = 'lugal_supply_payment'
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

    cr.execute(
        """
        UPDATE lugal_supply_payment
        SET payment_type = 'installment'
        WHERE payment_type = 'partial'
        """
    )
    cr.execute(
        """
        UPDATE lugal_supply_payment
        SET payment_type = 'final'
        WHERE payment_type = 'full'
        """
    )
