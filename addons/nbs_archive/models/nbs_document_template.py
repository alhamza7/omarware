# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NBSDocumentTemplate(models.Model):
    _name = 'nbs.document.template'
    _description = 'Document Templates'
    
    name = fields.Char(string='Template Name', required=True)
    description = fields.Text(string='Description')
    department_id = fields.Many2one('nbs.department', string='Department', required=True)
    document_type_id = fields.Many2one('nbs.document.type', string='Document Type', required=True)
    folder_id = fields.Many2one('nbs.document.folder', string='Default Folder')
    
    # Template fields
    default_name_pattern = fields.Char(string='Name Pattern', help='e.g., DOC-{date}-{seq}')
    default_description = fields.Text(string='Default Description')
    default_confidentiality = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], string='Confidentiality', default='internal')
    
    default_tags = fields.Char(string='Default Tags')
    active = fields.Boolean(default=True)
    
    def create_document_from_template(self):
        """Create a new document from this template"""
        self.ensure_one()
        return self.env['nbs.document'].create({
            'name': self.default_name_pattern or f"New Document from {self.name}",
            'description': self.default_description,
            'department_id': self.department_id.id,
            'document_type_id': self.document_type_id.id,
            'folder_id': self.folder_id.id if self.folder_id else False,
            'confidentiality_level': self.default_confidentiality,
            'state': 'draft'
        })


class NBSBatchOperation(models.Model):
    _name = 'nbs.batch.operation'
    _description = 'Batch Operations on Documents'
    
    name = fields.Char(string='Operation Name', required=True)
    operation_type = fields.Selection([
        ('archive', 'Archive Documents'),
        ('unarchive', 'Unarchive Documents'),
        ('trash', 'Move to Trash'),
        ('restore', 'Restore from Trash'),
        ('change_folder', 'Change Folder'),
        ('change_department', 'Change Department'),
        ('add_tags', 'Add Tags'),
        ('remove_tags', 'Remove Tags'),
    ], string='Operation Type', required=True)
    
    document_ids = fields.Many2many('nbs.document', string='Documents')
    document_count = fields.Integer(string='Documents Count', compute='_compute_document_count')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], default='draft')
    
    target_folder_id = fields.Many2one('nbs.document.folder', string='Target Folder')
    target_department_id = fields.Many2one('nbs.department', string='Target Department')
    tags_to_add = fields.Char(string='Tags to Add')
    tags_to_remove = fields.Char(string='Tags to Remove')
    
    processed_count = fields.Integer(string='Processed', default=0)
    success_count = fields.Integer(string='Successful', default=0)
    error_count = fields.Integer(string='Errors', default=0)
    error_log = fields.Text(string='Error Log')
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        for op in self:
            op.document_count = len(op.document_ids)
    
    def execute_batch_operation(self):
        """Execute the batch operation"""
        self.ensure_one()
        self.write({'status': 'processing'})
        
        errors = []
        success = 0
        
        for doc in self.document_ids:
            try:
                if self.operation_type == 'archive':
                    doc.write({'state': 'archived'})
                elif self.operation_type == 'unarchive':
                    doc.write({'state': 'active'})
                elif self.operation_type == 'trash':
                    doc.soft_delete(reason=f"Batch operation: {self.name}")
                elif self.operation_type == 'restore':
                    doc.restore_from_trash()
                elif self.operation_type == 'change_folder':
                    doc.write({'folder_id': self.target_folder_id.id})
                elif self.operation_type == 'change_department':
                    doc.write({'department_id': self.target_department_id.id})
                
                success += 1
            except Exception as e:
                errors.append(f"Doc {doc.id}: {str(e)}")
        
        self.write({
            'status': 'completed' if not errors else 'failed',
            'processed_count': len(self.document_ids),
            'success_count': success,
            'error_count': len(errors),
            'error_log': '\n'.join(errors) if errors else False
        })
