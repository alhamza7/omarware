# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SapImportWizard(models.TransientModel):
    """Wizard for importing data from SAP in bulk"""
    _name = 'sap.import.wizard'
    _description = 'SAP Bulk Import Wizard'
    
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        default=lambda self: self.env['sap.backend'].search([('active', '=', True)], limit=1),
        domain=[('active', '=', True)]
    )
    
    entity_type = fields.Selection([
        ('partner', 'Business Partners (Customers)'),
        ('product', 'Products (Items)'),
        ('order', 'Sale Orders'),
        ('invoice', 'Invoices'),
    ], string='Data Type', required=True, default='partner')
    
    import_mode = fields.Selection([
        ('all', 'Import All'),
        ('filter', 'Import with Filter'),
        ('specific', 'Import Specific Records'),
    ], string='Import Mode', default='all', required=True)
    
    filter_query = fields.Text(
        string='OData Filter',
        help="Example: CardType eq 'cCustomer' and Active eq 'Y'"
    )
    
    specific_ids = fields.Text(
        string='Specific IDs',
        help="Enter SAP IDs separated by commas. Example: C00001, C00002, C00003"
    )
    
    batch_size = fields.Integer(
        string='Batch Size',
        default=50,
        help="Number of records to import in each batch"
    )
    
    skip_existing = fields.Boolean(
        string='Skip Existing Records',
        default=True,
        help="Skip records that already exist in Odoo"
    )
    
    update_existing = fields.Boolean(
        string='Update Existing Records',
        default=False,
        help="Update records that already exist in Odoo"
    )
    
    # Results
    state = fields.Selection([
        ('draft', 'Draft'),
        ('importing', 'Importing'),
        ('done', 'Done'),
        ('error', 'Error'),
    ], default='draft', readonly=True)
    
    imported_count = fields.Integer('Imported', readonly=True)
    skipped_count = fields.Integer('Skipped', readonly=True)
    error_count = fields.Integer('Errors', readonly=True)
    error_log = fields.Text('Error Log', readonly=True)
    progress = fields.Float('Progress %', readonly=True)
    
    @api.onchange('backend_id')
    def _onchange_backend(self):
        """Update batch size from backend settings"""
        if self.backend_id:
            self.batch_size = self.backend_id.batch_size or 50
    
    def action_start_import(self):
        """Start the import process"""
        self.ensure_one()
        
        if not self.backend_id:
            raise UserError(_("Please select a SAP Backend"))
        
        if self.import_mode == 'filter' and not self.filter_query:
            raise UserError(_("Please enter a filter query"))
        
        if self.import_mode == 'specific' and not self.specific_ids:
            raise UserError(_("Please enter specific IDs"))
        
        try:
            self.write({
                'state': 'importing',
                'imported_count': 0,
                'skipped_count': 0,
                'error_count': 0,
                'error_log': '',
                'progress': 0,
            })
            
            # Call appropriate import method based on entity type
            if self.entity_type == 'partner':
                self._import_partners()
            elif self.entity_type == 'product':
                self._import_products()
            elif self.entity_type == 'order':
                self._import_orders()
            elif self.entity_type == 'invoice':
                self._import_invoices()
            
            self.state = 'done'
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'sap.import.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
            
        except Exception as e:
            error_msg = str(e)
            _logger.error(f"Import error: {error_msg}")
            self.write({
                'state': 'error',
                'error_log': error_msg,
            })
            raise UserError(_("Import failed: %s") % error_msg)
    
    def _import_partners(self):
        """Import business partners"""
        _logger.info(f"Starting partner import from backend {self.backend_id.name}")
        
        binding_model = self.env['sap.res.partner']
        
        if self.import_mode == 'all':
            # Import all partners
            result = self._import_batch(binding_model, filters=self.filter_query)
            
        elif self.import_mode == 'filter':
            # Import with custom filter
            result = self._import_batch(binding_model, filters=self.filter_query)
            
        elif self.import_mode == 'specific':
            # Import specific IDs
            ids = [id.strip() for id in self.specific_ids.split(',') if id.strip()]
            result = self._import_specific(binding_model, ids)
        
        self._update_results(result)
    
    def _import_products(self):
        """Import products"""
        _logger.info(f"Starting product import from backend {self.backend_id.name}")
        
        binding_model = self.env['sap.product.product']
        
        if self.import_mode == 'all':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'filter':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'specific':
            ids = [id.strip() for id in self.specific_ids.split(',') if id.strip()]
            result = self._import_specific(binding_model, ids)
        
        self._update_results(result)
    
    def _import_orders(self):
        """Import sale orders"""
        _logger.info(f"Starting order import from backend {self.backend_id.name}")
        
        binding_model = self.env['sap.sale.order']
        
        if self.import_mode == 'all':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'filter':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'specific':
            ids = [id.strip() for id in self.specific_ids.split(',') if id.strip()]
            result = self._import_specific(binding_model, ids)
        
        self._update_results(result)
    
    def _import_invoices(self):
        """Import invoices"""
        _logger.info(f"Starting invoice import from backend {self.backend_id.name}")
        
        binding_model = self.env['sap.account.move']
        
        if self.import_mode == 'all':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'filter':
            result = self._import_batch(binding_model, filters=self.filter_query)
        elif self.import_mode == 'specific':
            ids = [id.strip() for id in self.specific_ids.split(',') if id.strip()]
            result = self._import_specific(binding_model, ids)
        
        self._update_results(result)
    
    def _import_batch(self, binding_model, filters=None):
        """Import records in batch"""
        try:
            result = binding_model.import_batch(self.backend_id, filters=filters)
            return result
        except Exception as e:
            _logger.error(f"Batch import error: {str(e)}")
            return {
                'imported': 0,
                'skipped': 0,
                'errors': 1,
                'error_messages': [str(e)]
            }
    
    def _import_specific(self, binding_model, external_ids):
        """Import specific records by external IDs"""
        imported = 0
        skipped = 0
        errors = 0
        error_messages = []
        
        total = len(external_ids)
        
        for idx, external_id in enumerate(external_ids):
            try:
                # Check if already exists
                if self.skip_existing:
                    existing = binding_model.search([
                        ('backend_id', '=', self.backend_id.id),
                        ('external_id', '=', external_id)
                    ])
                    if existing:
                        skipped += 1
                        continue
                
                # Import record
                binding_model.import_record(self.backend_id, external_id)
                imported += 1
                
                # Update progress
                progress = ((idx + 1) / total) * 100
                self.progress = progress
                
            except Exception as e:
                errors += 1
                error_messages.append(f"{external_id}: {str(e)}")
                _logger.error(f"Error importing {external_id}: {str(e)}")
        
        return {
            'imported': imported,
            'skipped': skipped,
            'errors': errors,
            'error_messages': error_messages
        }
    
    def _update_results(self, result):
        """Update wizard with import results"""
        self.write({
            'imported_count': result.get('imported', 0),
            'skipped_count': result.get('skipped', 0),
            'error_count': result.get('errors', 0),
            'error_log': '\n'.join(result.get('error_messages', [])),
            'progress': 100,
        })
    
    def action_view_imported(self):
        """View imported records"""
        self.ensure_one()
        
        model_map = {
            'partner': 'sap.res.partner',
            'product': 'sap.product.product',
            'order': 'sap.sale.order',
            'invoice': 'sap.account.move',
        }
        
        model = model_map.get(self.entity_type)
        if not model:
            return
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Imported Records'),
            'res_model': model,
            'view_mode': 'tree,form',
            'domain': [('backend_id', '=', self.backend_id.id)],
            'context': dict(self.env.context),
        }
    
    def action_close(self):
        """Close wizard"""
        return {'type': 'ir.actions.act_window_close'}
