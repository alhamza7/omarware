# -*- coding: utf-8 -*-


def post_init_hook(env):
    """Ensure DB column for ``exchange_rate`` (``crm_supply_po_extend``) exists after install/upgrade."""
    env.cr.execute(
        """
        ALTER TABLE lugal_crm_supply_po
        ADD COLUMN IF NOT EXISTS exchange_rate DOUBLE PRECISION;
        """
    )


from . import models
from . import controllers
