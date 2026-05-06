# -*- coding: utf-8 -*-
# File: addons/lugal_email/migrations/1.1.2/pre-clear_folder_selections.py
# Component: Lugal Email — pre-migration 1.1.2 (clear folder field selection rows)
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
