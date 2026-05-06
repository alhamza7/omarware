# -*- coding: utf-8 -*-
"""Idempotent: remove folder Selection rows if any remain (failed 1.1.1 upgrades)."""


def migrate(cr, version):
    cr.execute(
        """
        DELETE FROM ir_model_fields_selection
        WHERE field_id IN (
            SELECT id FROM ir_model_fields
            WHERE model = 'lugal.email.message' AND name = 'folder'
        )
        """
    )
