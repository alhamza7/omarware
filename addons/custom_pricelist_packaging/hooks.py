# -*- coding: utf-8 -*-

def post_init_hook(*args):
    """Normalize legacy product template type values after install/upgrade.

    Compat: support both signatures used by Odoo across versions:
    - post_init_hook(cr, registry)
    - post_init_hook(env)
    """
    if len(args) == 1:  # env
        cr = args[0].cr
    elif len(args) >= 2:  # cr, registry
        cr = args[0]
    else:
        return

    cr.execute("UPDATE product_template SET type = 'storable' WHERE type = 'product'")
    cr.execute("UPDATE product_template SET type = 'consumable' WHERE type = 'consu'")


