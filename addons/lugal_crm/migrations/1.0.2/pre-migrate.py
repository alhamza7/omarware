# -*- coding: utf-8 -*-
"""Rename attachment M2M fields to attachment_ids (keep relation tables)."""


def migrate(cr, version):
    cr.execute(
        """
        UPDATE ir_model_fields AS imf
        SET name = 'attachment_ids'
        FROM ir_model AS im
        WHERE imf.model_id = im.id
          AND im.model = 'lugal.supply.payment'
          AND imf.name = 'receipt_attachment_ids'
        """
    )
    cr.execute(
        """
        UPDATE ir_model_fields AS imf
        SET name = 'attachment_ids'
        FROM ir_model AS im
        WHERE imf.model_id = im.id
          AND im.model = 'lugal.crm.supply.po'
          AND imf.name = 'order_attachment_ids'
        """
    )
