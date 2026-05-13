# -*- coding: utf-8 -*-
"""Standard attachment M2M: count + sync ir.attachment res_model/res_id after link."""

from odoo import api, fields, models


class LugalSupplyAttachmentSyncMixin(models.AbstractModel):
    _name = 'lugal.supply.attachment.sync.mixin'
    _description = 'Attachment M2M res sync + count (supply documents)'

    attachment_count = fields.Integer(
        string='Attachment count',
        compute='_compute_attachment_count',
    )

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    def _lugal_sync_linked_attachments_res(self):
        """Point linked ir.attachment rows at this record (API/email uploads)."""
        for rec in self:
            if 'attachment_ids' not in rec._fields:
                continue
            for att in rec.attachment_ids:
                if att.res_model != rec._name or att.res_id != rec.id:
                    att.sudo().write({'res_model': rec._name, 'res_id': rec.id})

    def write(self, vals):
        res = super().write(vals)
        if 'attachment_ids' in vals:
            self._lugal_sync_linked_attachments_res()
        return res
