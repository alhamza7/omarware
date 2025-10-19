# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Conflict Resolution Wizard

Wizard to help resolve sync conflicts between SAP and Odoo.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
import json

from ..core.sap_logger import SapLogger, SapSyncError


class SapConflictResolutionWizard(models.TransientModel):
    """Wizard for resolving sync conflicts"""
    _name = 'sap.conflict.resolution.wizard'
    _description = 'SAP Conflict Resolution Wizard'
    
    
    # Basic Information
    synced_data_id = fields.Many2one(
        'sap.synced.data',
        string='Synced Data Record',
        required=True,
        readonly=True
    )
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        related='synced_data_id.backend_id',
        readonly=True
    )
    model_name = fields.Char(
        string='Model',
        related='synced_data_id.model_name',
        readonly=True
    )
    external_id = fields.Char(
        string='SAP External ID',
        related='synced_data_id.external_id',
        readonly=True
    )
    
    # Conflict Information
    conflict_reason = fields.Text(
        string='Conflict Reason',
        related='synced_data_id.conflict_reason',
        readonly=True
    )
    sap_data = fields.Text(
        string='SAP Data',
        compute='_compute_data_comparison',
        readonly=True
    )
    odoo_data = fields.Text(
        string='Odoo Data',
        compute='_compute_data_comparison',
        readonly=True
    )
    
    # Resolution Options
    resolution_type = fields.Selection([
        ('sap_wins', 'Use SAP Data'),
        ('odoo_wins', 'Use Odoo Data'),
        ('manual', 'Manual Resolution'),
        ('merged', 'Merge Data'),
        ('skip', 'Skip This Record')
    ], string='Resolution Type', required=True)
    
    resolution_notes = fields.Text(
        string='Resolution Notes',
        help="Notes about how the conflict was resolved"
    )
    
    # Field-level Resolution
    field_resolutions = fields.One2many(
        'sap.conflict.field.resolution',
        'wizard_id',
        string='Field Resolutions'
    )
    
    # Preview
    preview_data = fields.Text(
        string='Preview Data',
        compute='_compute_preview_data',
        readonly=True
    )
    
    @api.depends('synced_data_id')
    def _compute_data_comparison(self):
        """Compute data comparison for conflict resolution"""
        for wizard in self:
            if wizard.synced_data_id:
                wizard.sap_data = wizard.synced_data_id.last_sap_data or 'No SAP data available'
                wizard.odoo_data = wizard.synced_data_id.last_odoo_data or 'No Odoo data available'
            else:
                wizard.sap_data = ''
                wizard.odoo_data = ''
    
    @api.depends('resolution_type', 'field_resolutions')
    def _compute_preview_data(self):
        """Compute preview of resolved data"""
        for wizard in self:
            if wizard.resolution_type == 'sap_wins' and wizard.sap_data:
                wizard.preview_data = wizard.sap_data
            elif wizard.resolution_type == 'odoo_wins' and wizard.odoo_data:
                wizard.preview_data = wizard.odoo_data
            elif wizard.resolution_type == 'merged' and wizard.field_resolutions:
                # Merge data based on field resolutions
                merged_data = {}
                sap_data = json.loads(wizard.sap_data) if wizard.sap_data else {}
                odoo_data = json.loads(wizard.odoo_data) if wizard.odoo_data else {}
                
                for field_resolution in wizard.field_resolutions:
                    if field_resolution.resolution == 'sap':
                        merged_data[field_resolution.field_name] = field_resolution.sap_value
                    elif field_resolution.resolution == 'odoo':
                        merged_data[field_resolution.field_name] = field_resolution.odoo_value
                    elif field_resolution.resolution == 'custom':
                        merged_data[field_resolution.field_name] = field_resolution.custom_value
                
                wizard.preview_data = json.dumps(merged_data, indent=2)
            else:
                wizard.preview_data = ''
    
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        defaults = super().default_get(fields_list)
        
        if 'synced_data_id' in self.env.context:
            synced_data_id = self.env.context['synced_data_id']
            synced_data = self.env['sap.synced.data'].browse(synced_data_id)
            
            if synced_data.exists():
                defaults['synced_data_id'] = synced_data_id
                
                # Create field resolutions for conflicting fields
                if synced_data.last_sap_data and synced_data.last_odoo_data:
                    self._create_field_resolutions(synced_data)
        
        return defaults
    
    def _create_field_resolutions(self, synced_data):
        """Create field resolution records for conflicting fields"""
        try:
            sap_data = json.loads(synced_data.last_sap_data) if synced_data.last_sap_data else {}
            odoo_data = json.loads(synced_data.last_odoo_data) if synced_data.last_odoo_data else {}
            
            # Find conflicting fields
            conflicting_fields = []
            all_fields = set(sap_data.keys()) | set(odoo_data.keys())
            
            for field in all_fields:
                sap_value = sap_data.get(field, '')
                odoo_value = odoo_data.get(field, '')
                
                if str(sap_value).strip() != str(odoo_value).strip():
                    conflicting_fields.append({
                        'field_name': field,
                        'sap_value': sap_value,
                        'odoo_value': odoo_value,
                        'resolution': 'sap'  # Default to SAP
                    })
            
            # Store in context for later use
            self.env.context = dict(self.env.context)
            self.env.context['conflicting_fields'] = conflicting_fields
            
        except Exception as e:
            _logger.error(f"Error creating field resolutions: {str(e)}")
    
    @api.onchange('resolution_type')
    def _onchange_resolution_type(self):
        """Handle resolution type change"""
        if self.resolution_type == 'merged' and not self.field_resolutions:
            # Create field resolution records
            conflicting_fields = self.env.context.get('conflicting_fields', [])
            field_resolutions = []
            
            for field_data in conflicting_fields:
                field_resolutions.append((0, 0, {
                    'field_name': field_data['field_name'],
                    'sap_value': field_data['sap_value'],
                    'odoo_value': field_data['odoo_value'],
                    'resolution': 'sap'
                }))
            
            self.field_resolutions = field_resolutions
    
    def action_resolve_conflict(self):
        """Resolve the conflict"""
        try:
            if not self.synced_data_id:
                raise UserError("No synced data record selected")
            
            # Validate resolution
            if self.resolution_type == 'manual' and not self.resolution_notes:
                raise UserError("Resolution notes are required for manual resolution")
            
            # Apply resolution
            if self.resolution_type == 'sap_wins':
                self._apply_sap_data()
            elif self.resolution_type == 'odoo_wins':
                self._apply_odoo_data()
            elif self.resolution_type == 'merged':
                self._apply_merged_data()
            elif self.resolution_type == 'skip':
                self._skip_record()
            elif self.resolution_type == 'manual':
                self._apply_manual_resolution()
            
            # Update synced data record
            self.synced_data_id.resolve_conflict(
                self.resolution_type,
                self.resolution_notes
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conflict Resolved',
                    'message': f'Conflict for record {self.synced_data_id.display_name} has been resolved',
                    'type': 'success'
                }
            }
            
        except Exception as e:
            _logger.error(f"Error resolving conflict: {str(e)}")
            raise UserError(f"Failed to resolve conflict: {str(e)}")
    
    def _apply_sap_data(self):
        """Apply SAP data to Odoo record"""
        try:
            if not self.synced_data_id.odoo_record:
                raise UserError("No Odoo record found to update")
            
            # Get SAP data
            sap_data = json.loads(self.synced_data_id.last_sap_data) if self.synced_data_id.last_sap_data else {}
            
            # Map SAP data to Odoo format
            mapper = self.env['sap.data.mapper']
            if self.synced_data_id.model_name == 'res.partner':
                odoo_data = mapper.map_sap_partner_to_odoo(sap_data)
            elif self.synced_data_id.model_name == 'product.product':
                odoo_data = mapper.map_sap_product_to_odoo(sap_data)
            else:
                raise UserError(f"Unsupported model for conflict resolution: {self.synced_data_id.model_name}")
            
            # Update Odoo record
            odoo_record = self.synced_data_id.odoo_record
            odoo_record.write(odoo_data)
            
            _logger.info(f"Applied SAP data to Odoo record {odoo_record.id}")
            
        except Exception as e:
            _logger.error(f"Error applying SAP data: {str(e)}")
            raise
    
    def _apply_odoo_data(self):
        """Apply Odoo data to SAP"""
        try:
            if not self.synced_data_id.odoo_record:
                raise UserError("No Odoo record found")
            
            # Get Odoo data
            odoo_record = self.synced_data_id.odoo_record
            
            # Map Odoo data to SAP format
            mapper = self.env['sap.data.mapper']
            if self.synced_data_id.model_name == 'res.partner':
                sap_data = mapper.map_odoo_partner_to_sap(odoo_record)
            elif self.synced_data_id.model_name == 'product.product':
                sap_data = mapper.map_odoo_product_to_sap(odoo_record)
            else:
                raise UserError(f"Unsupported model for conflict resolution: {self.synced_data_id.model_name}")
            
            # Update SAP record
            connection = self.synced_data_id.backend_id.get_connection()
            if self.synced_data_id.model_name == 'res.partner':
                connection.update_business_partner(self.synced_data_id.external_id, sap_data)
            elif self.synced_data_id.model_name == 'product.product':
                connection.update_item(self.synced_data_id.external_id, sap_data)
            
            connection.close_session()
            
            _logger.info(f"Applied Odoo data to SAP record {self.synced_data_id.external_id}")
            
        except Exception as e:
            _logger.error(f"Error applying Odoo data: {str(e)}")
            raise
    
    def _apply_merged_data(self):
        """Apply merged data"""
        try:
            if not self.field_resolutions:
                raise UserError("No field resolutions defined for merged data")
            
            # Build merged data
            merged_data = {}
            for field_resolution in self.field_resolutions:
                if field_resolution.resolution == 'sap':
                    merged_data[field_resolution.field_name] = field_resolution.sap_value
                elif field_resolution.resolution == 'odoo':
                    merged_data[field_resolution.field_name] = field_resolution.odoo_value
                elif field_resolution.resolution == 'custom':
                    merged_data[field_resolution.field_name] = field_resolution.custom_value
            
            # Apply to both systems
            self._apply_sap_data()
            self._apply_odoo_data()
            
            _logger.info(f"Applied merged data for record {self.synced_data_id.display_name}")
            
        except Exception as e:
            _logger.error(f"Error applying merged data: {str(e)}")
            raise
    
    def _skip_record(self):
        """Skip this record"""
        self.synced_data_id.write({
            'sync_status': 'cancelled',
            'conflict_resolution': 'skip'
        })
        
        _logger.info(f"Skipped record {self.synced_data_id.display_name}")
    
    def _apply_manual_resolution(self):
        """Apply manual resolution"""
        # This would require custom implementation based on specific needs
        _logger.info(f"Manual resolution applied for record {self.synced_data_id.display_name}")
    
    def action_preview_resolution(self):
        """Preview the resolution"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resolution Preview',
            'res_model': 'sap.conflict.resolution.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'show_preview': True}
        }


class SapConflictFieldResolution(models.TransientModel):
    """Field-level conflict resolution"""
    _name = 'sap.conflict.field.resolution'
    _description = 'SAP Conflict Field Resolution'
    
    wizard_id = fields.Many2one(
        'sap.conflict.resolution.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    field_name = fields.Char(
        string='Field Name',
        required=True,
        readonly=True
    )
    sap_value = fields.Text(
        string='SAP Value',
        readonly=True
    )
    odoo_value = fields.Text(
        string='Odoo Value',
        readonly=True
    )
    resolution = fields.Selection([
        ('sap', 'Use SAP Value'),
        ('odoo', 'Use Odoo Value'),
        ('custom', 'Custom Value')
    ], string='Resolution', required=True, default='sap')
    
    custom_value = fields.Text(
        string='Custom Value',
        help="Custom value for this field"
    )
    
    @api.onchange('resolution')
    def _onchange_resolution(self):
        """Handle resolution change"""
        if self.resolution == 'custom' and not self.custom_value:
            # Set default custom value
            self.custom_value = self.sap_value
