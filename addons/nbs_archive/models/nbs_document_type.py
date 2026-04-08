# -*- coding: utf-8 -*-

import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class NBSDocumentType(models.Model):
    _name = 'nbs.document.type'
    _description = 'Document Type'
    _inherit = ['mail.thread']
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Document Type',
        required=True,
        translate=True,
        tracking=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        size=20,
        index=True,
        tracking=True,
        help='Unique code for this document type (e.g., CONTRACT, INVOICE)'
    )
    department_id = fields.Many2one(
        'nbs.department',
        string='Department',
        required=True,
        ondelete='restrict',
        tracking=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    # Custom Fields Configuration (stored as JSON)
    custom_field_config = fields.Text(
        string='Custom Fields Configuration',
        help='JSON configuration for type-specific fields',
        default='[]'
    )
    
    # Example structure:
    # [
    #   {
    #     "name": "supplier_name",
    #     "type": "char",
    #     "label": "Supplier Name",
    #     "label_ar": "اسم المورد",
    #     "required": true,
    #     "help": "Name of the supplier"
    #   },
    #   {
    #     "name": "contract_value",
    #     "type": "float",
    #     "label": "Contract Value",
    #     "label_ar": "قيمة العقد",
    #     "required": false
    #   }
    # ]
    
    # Relations
    document_ids = fields.One2many(
        'nbs.document',
        'document_type_id',
        string='Documents'
    )
    
    # Computed
    document_count = fields.Integer(
        string='Documents',
        compute='_compute_document_count',
        store=False
    )
    
    _sql_constraints = [
        ('code_dept_unique', 'UNIQUE(code, department_id)', 
         'Document type code must be unique per department!'),
    ]
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        for doc_type in self:
            doc_type.document_count = len(doc_type.document_ids)
    
    @api.constrains('code')
    def _check_code(self):
        for doc_type in self:
            if doc_type.code:
                if not doc_type.code.replace('_', '').isalnum():
                    raise ValidationError(_('Code must contain only letters, numbers, and underscores'))
                if doc_type.code != doc_type.code.upper():
                    doc_type.code = doc_type.code.upper()
    
    @api.constrains('custom_field_config')
    def _check_custom_field_config(self):
        """Validate JSON structure"""
        for doc_type in self:
            if doc_type.custom_field_config:
                try:
                    config = json.loads(doc_type.custom_field_config)
                    if not isinstance(config, list):
                        raise ValidationError(_('Custom field configuration must be a JSON array'))
                    
                    # Validate each field
                    for field_def in config:
                        if not isinstance(field_def, dict):
                            raise ValidationError(_('Each field definition must be a JSON object'))
                        
                        required_keys = ['name', 'type', 'label']
                        for key in required_keys:
                            if key not in field_def:
                                raise ValidationError(_('Field definition missing required key: %s') % key)
                        
                        # Validate field type
                        valid_types = ['char', 'text', 'integer', 'float', 'boolean', 
                                     'date', 'datetime', 'selection']
                        if field_def['type'] not in valid_types:
                            raise ValidationError(_('Invalid field type: %s') % field_def['type'])
                        
                except json.JSONDecodeError:
                    raise ValidationError(_('Invalid JSON format in custom field configuration'))
    
    def name_get(self):
        result = []
        for doc_type in self:
            name = f'[{doc_type.code}] {doc_type.name}'
            if doc_type.department_id:
                name = f'{doc_type.department_id.code} - {name}'
            result.append((doc_type.id, name))
        return result
    
    def get_custom_fields(self):
        """Return parsed custom fields configuration"""
        self.ensure_one()
        if self.custom_field_config:
            try:
                return json.loads(self.custom_field_config)
            except json.JSONDecodeError:
                return []
        return []
    
    def action_view_documents(self):
        """Action to view documents of this type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents - %s') % self.name,
            'res_model': 'nbs.document',
            'view_mode': 'kanban,tree,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': {
                'default_document_type_id': self.id,
                'default_department_id': self.department_id.id,
            }
        }


