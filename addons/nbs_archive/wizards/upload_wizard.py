# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class UploadWizard(models.TransientModel):
    _name = 'nbs.upload.wizard'
    _description = 'Document Upload Wizard'

    department_id = fields.Many2one('nbs.department', string='Department', required=True)
    document_type_id = fields.Many2one('nbs.document.type', string='Document Type', required=True)
    title = fields.Char(string='Title', required=True)
    file_data = fields.Binary(string='File', required=True, attachment=True)
    file_name = fields.Char(string='File Name')
    tags = fields.Many2many('nbs.document.tag', string='Tags')
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict'),
    ], string='Confidentiality Level', default='internal', required=True)
    
    @api.onchange('department_id')
    def _onchange_department_id(self):
        """Filter document types by department"""
        if self.department_id:
            return {'domain': {'document_type_id': [('department_id', '=', self.department_id.id)]}}
        return {'domain': {'document_type_id': []}}
    
    def action_upload_document(self):
        """Upload document"""
        self.ensure_one()
        
        if not self.file_data:
            raise UserError('Please select a file to upload.')
        
        # Create document
        document = self.env['nbs.document'].create({
            'department_id': self.department_id.id,
            'document_type_id': self.document_type_id.id,
            'title': self.title,
            'file_data': self.file_data,
            'file_name': self.file_name,
            'tag_ids': [(6, 0, self.tags.ids)],
            'confidentiality_level': self.confidentiality_level,
            'uploader_id': self.env.user.id,
            'status': 'active',
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nbs.document',
            'res_id': document.id,
            'view_mode': 'form',
            'target': 'current',
        }


