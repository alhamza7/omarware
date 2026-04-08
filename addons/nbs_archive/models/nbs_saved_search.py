# -*- coding: utf-8 -*-
from odoo import models, fields, api
import json


class NBSSavedSearch(models.Model):
    _name = 'nbs.saved.search'
    _description = 'Saved Search Filters'
    _order = 'sequence, name'
    
    name = fields.Char(string='Search Name', required=True)
    user_id = fields.Many2one('res.users', string='Owner', default=lambda self: self.env.user, required=True)
    is_public = fields.Boolean(string='Public', default=False)
    sequence = fields.Integer(default=10)
    
    # Search criteria (stored as JSON)
    search_criteria = fields.Text(string='Search Criteria (JSON)')
    
    # Quick access
    department_ids = fields.Many2many('nbs.department', string='Departments')
    document_type_ids = fields.Many2many('nbs.document.type', string='Document Types')
    folder_ids = fields.Many2many('nbs.document.folder', string='Folders')
    
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('strict', 'Strict')
    ], string='Confidentiality')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('trash', 'Trash')
    ], string='Status')
    
    tags = fields.Char(string='Tags (comma separated)')
    
    result_count = fields.Integer(string='Results', compute='_compute_result_count')
    
    def _compute_result_count(self):
        for search in self:
            domain = search._build_domain()
            search.result_count = self.env['nbs.document'].search_count(domain)
    
    def _build_domain(self):
        """Build search domain from criteria"""
        self.ensure_one()
        domain = []
        
        if self.department_ids:
            domain.append(('department_id', 'in', self.department_ids.ids))
        
        if self.document_type_ids:
            domain.append(('document_type_id', 'in', self.document_type_ids.ids))
        
        if self.folder_ids:
            domain.append(('folder_id', 'in', self.folder_ids.ids))
        
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        
        if self.confidentiality_level:
            domain.append(('confidentiality_level', '=', self.confidentiality_level))
        
        if self.state:
            domain.append(('state', '=', self.state))
        
        # Parse JSON criteria if exists
        if self.search_criteria:
            try:
                criteria = json.loads(self.search_criteria)
                # Add custom criteria here
            except:
                pass
        
        return domain
    
    def execute_search(self):
        """Execute the saved search"""
        self.ensure_one()
        domain = self._build_domain()
        documents = self.env['nbs.document'].search(domain)
        return documents
