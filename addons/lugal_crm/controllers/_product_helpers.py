# -*- coding: utf-8 -*-
"""product.product helpers for CRM controllers (ORM-safe across Odoo versions)."""


def safe_product_purchase_uom(product):
    """Purchase UoM when ``uom_po_id`` exists on the model; else sale ``uom_id``.

    Do not use ``getattr(record, 'uom_po_id', ...)`` on recordsets: Odoo's ``__getattr__``
    resolves field names and raises if the field is not declared (e.g. no Purchase app).
    """
    if not product:
        return False
    if 'uom_po_id' in product._fields:
        try:
            u = product.uom_po_id
            return u or product.uom_id
        except AttributeError:
            return product.uom_id
    return product.uom_id
