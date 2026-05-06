# -*- coding: utf-8 -*-
"""Allow lugal.email.message.folder to change from Selection to Char.

Odoo's post-upgrade cleanup of ir.model.fields.selection rows can crash with
AttributeError: 'Char' object has no attribute 'ondelete'.  Drop selection rows
before the field type changes.
"""


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
