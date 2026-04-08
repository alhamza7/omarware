# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class EditRequestWizard(models.TransientModel):
    _name = 'nbs.edit.request.wizard'
    _description = 'Edit Request Wizard'

    document_id = fields.Many2one('nbs.document', string='Document', required=True)
    reason = fields.Text(string='Reason for Edit', required=True)
    
    def action_submit_request(self):
        """Submit edit request"""
        self.ensure_one()
        
        # Create edit request
        edit_request = self.env['nbs.edit.request'].create({
            'document_id': self.document_id.id,
            'reason': self.reason,
            'requester_id': self.env.user.id,
            'state': 'pending',
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Edit Request Submitted',
                'message': 'Your edit request has been submitted and is pending approval.',
                'type': 'success',
                'sticky': False,
            }
        }


