# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""
SAP Synced Data Model

Comprehensive model to track all synchronized records between SAP and Odoo.
"""

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import json

from ..core.sap_logger import SapLogger, SapSyncError, SapValidationError


class SapSyncedData(models.Model):
    """Comprehensive model to track all synchronized data"""
    _name = 'sap.synced.data'
    _description = 'SAP Synced Data'
    _order = 'last_sync_date desc, id desc'
    _rec_name = 'display_name'
    
    
    # Basic Information
    backend_id = fields.Many2one(
        'sap.backend',
        string='SAP Backend',
        required=True,
        ondelete='cascade',
        index=True
    )
    model_name = fields.Char(
        string='Odoo Model',
        required=True,
        index=True,
        help="Odoo model name (e.g., res.partner, product.product)"
    )
    odoo_id = fields.Integer(
        string='Odoo Record ID',
        required=True,
        index=True,
        help="ID of the Odoo record"
    )
    odoo_record = fields.Reference(
        selection='_get_odoo_models',
        string='Odoo Record',
        compute='_compute_odoo_record',
        store=False,
        help="Reference to the actual Odoo record"
    )
    
    # SAP Information
    external_id = fields.Char(
        string='SAP External ID',
        required=True,
        index=True,
        help="External ID from SAP (e.g., CardCode, ItemCode, DocEntry)"
    )
    sap_record_name = fields.Char(
        string='SAP Record Name',
        help="Name or description of the SAP record"
    )
    sap_model = fields.Char(
        string='SAP Model',
        help="SAP model/endpoint (e.g., BusinessPartners, Items, Orders)"
    )
    
    # Sync Information
    sync_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('conflict', 'Conflict'),
        ('needs_attention', 'Needs Attention')
    ], string='Sync Status', default='pending', required=True, index=True)
    
    sync_direction = fields.Selection([
        ('sap_to_odoo', 'SAP → Odoo'),
        ('odoo_to_sap', 'Odoo → SAP'),
        ('bidirectional', 'Bidirectional'),
        ('manual', 'Manual')
    ], string='Sync Direction', default='sap_to_odoo', required=True)
    
    # Timing Information
    first_sync_date = fields.Datetime(
        string='First Sync',
        readonly=True,
        help="When this record was first synchronized"
    )
    last_sync_date = fields.Datetime(
        string='Last Sync',
        readonly=True,
        index=True,
        help="When this record was last synchronized"
    )
    next_sync_date = fields.Datetime(
        string='Next Sync',
        help="When this record is scheduled for next sync"
    )
    sync_count = fields.Integer(
        string='Sync Count',
        default=0,
        readonly=True,
        help="Number of times this record has been synchronized"
    )
    
    # Data Information
    data_hash = fields.Char(
        string='Data Hash',
        help="Hash of the synchronized data for change detection"
    )
    last_sap_data = fields.Text(
        string='Last SAP Data',
        help="Last data received from SAP (JSON format)"
    )
    last_odoo_data = fields.Text(
        string='Last Odoo Data',
        help="Last data sent to Odoo (JSON format)"
    )
    
    # Error Information
    last_error = fields.Text(
        string='Last Error',
        readonly=True,
        help="Last error message if sync failed"
    )
    error_count = fields.Integer(
        string='Error Count',
        default=0,
        readonly=True,
        help="Number of consecutive sync errors"
    )
    last_error_date = fields.Datetime(
        string='Last Error Date',
        readonly=True,
        help="When the last error occurred"
    )
    retry_count = fields.Integer(
        string='Retry Count',
        default=0,
        readonly=True,
        help="Number of retry attempts"
    )
    max_retries = fields.Integer(
        string='Max Retries',
        default=3,
        help="Maximum number of retry attempts"
    )
    
    # Conflict Information
    conflict_reason = fields.Text(
        string='Conflict Reason',
        help="Reason for sync conflict"
    )
    conflict_resolution = fields.Selection([
        ('none', 'No Resolution'),
        ('sap_wins', 'SAP Data Wins'),
        ('odoo_wins', 'Odoo Data Wins'),
        ('manual', 'Manual Resolution'),
        ('merged', 'Data Merged')
    ], string='Conflict Resolution', default='none')
    
    # User Information
    created_by = fields.Many2one(
        'res.users',
        string='Created By',
        default=lambda self: self.env.user,
        readonly=True
    )
    last_modified_by = fields.Many2one(
        'res.users',
        string='Last Modified By',
        readonly=True
    )
    
    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    sync_age = fields.Integer(
        string='Sync Age (days)',
        compute='_compute_sync_age',
        store=True,
        help="Days since last successful sync"
    )
    is_stale = fields.Boolean(
        string='Is Stale',
        compute='_compute_is_stale',
        store=True,
        help="True if record hasn't been synced recently"
    )
    
    # Constraints
    _sql_constraints = [
        ('unique_backend_external_id', 
         'unique(backend_id, external_id)',
         'A record with the same external ID already exists for this backend.'),
        ('unique_backend_odoo_record',
         'unique(backend_id, model_name, odoo_id)',
         'A record with the same Odoo record already exists for this backend.')
    ]
    
    @api.model
    def _get_odoo_models(self):
        """Get available Odoo models for reference field"""
        models = [
            ('res.partner', 'Partner'),
            ('product.product', 'Product'),
            ('product.template', 'Product Template'),
            ('sale.order', 'Sale Order'),
            ('sale.order.line', 'Sale Order Line'),
            ('account.move', 'Invoice'),
            ('account.move.line', 'Invoice Line'),
            ('stock.picking', 'Stock Picking'),
            ('stock.move', 'Stock Move'),
            ('purchase.order', 'Purchase Order'),
            ('purchase.order.line', 'Purchase Order Line'),
        ]
        return models
    
    @api.depends('model_name', 'odoo_id', 'external_id', 'sap_record_name')
    def _compute_display_name(self):
        """Compute display name for the record"""
        for record in self:
            if record.sap_record_name:
                record.display_name = f"{record.sap_record_name} ({record.external_id})"
            else:
                record.display_name = f"{record.model_name}#{record.odoo_id} ({record.external_id})"
    
    @api.depends('last_sync_date')
    def _compute_sync_age(self):
        """Compute sync age in days"""
        for record in self:
            if record.last_sync_date:
                delta = fields.Datetime.now() - record.last_sync_date
                record.sync_age = delta.days
            else:
                record.sync_age = 0
    
    @api.depends('sync_age', 'sync_status')
    def _compute_is_stale(self):
        """Determine if record is stale"""
        for record in self:
            # Consider stale if more than 7 days old and not recently synced
            record.is_stale = (
                record.sync_age > 7 and 
                record.sync_status not in ['success', 'in_progress']
            )
    
    def _compute_odoo_record(self):
        """Compute reference to Odoo record"""
        for record in self:
            if record.model_name and record.odoo_id:
                try:
                    model = self.env[record.model_name]
                    odoo_record = model.browse(record.odoo_id)
                    if odoo_record.exists():
                        record.odoo_record = f"{record.model_name},{record.odoo_id}"
                    else:
                        record.odoo_record = False
                except:
                    record.odoo_record = False
            else:
                record.odoo_record = False
    
    @api.model
    def create_synced_record(self, backend_id, model_name, odoo_id, external_id, 
                            sync_direction='sap_to_odoo', sap_data=None, odoo_data=None):
        """Create a new synced data record"""
        try:
            # Check if record already exists
            existing = self.search([
                ('backend_id', '=', backend_id),
                ('external_id', '=', external_id)
            ])
            
            if existing:
                # Update existing record
                existing.write({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_count': existing.sync_count + 1,
                    'last_modified_by': self.env.user.id,
                    'last_sap_data': json.dumps(sap_data) if sap_data else existing.last_sap_data,
                    'last_odoo_data': json.dumps(odoo_data) if odoo_data else existing.last_odoo_data,
                    'sync_status': 'success',
                    'error_count': 0,
                    'last_error': False
                })
                return existing
            
            # Create new record
            vals = {
                'backend_id': backend_id,
                'model_name': model_name,
                'odoo_id': odoo_id,
                'external_id': external_id,
                'sync_direction': sync_direction,
                'first_sync_date': fields.Datetime.now(),
                'last_sync_date': fields.Datetime.now(),
                'sync_count': 1,
                'sync_status': 'success',
                'last_sap_data': json.dumps(sap_data) if sap_data else False,
                'last_odoo_data': json.dumps(odoo_data) if odoo_data else False,
                'created_by': self.env.user.id,
                'last_modified_by': self.env.user.id
            }
            
            # Add SAP record name if available
            if sap_data and isinstance(sap_data, dict):
                name_fields = ['CardName', 'ItemName', 'DocNum', 'name']
                for field in name_fields:
                    if field in sap_data:
                        vals['sap_record_name'] = sap_data[field]
                        break
            
            return self.create(vals)
            
        except Exception as e:
            _logger.error(f"Error creating synced record: {str(e)}")
            raise SapSyncError(f"Failed to create synced record: {str(e)}")
    
    def update_sync_status(self, status, error_message=None, sap_data=None, odoo_data=None):
        """Update sync status and related information"""
        try:
            update_vals = {
                'sync_status': status,
                'last_modified_by': self.env.user.id
            }
            
            if status == 'success':
                update_vals.update({
                    'last_sync_date': fields.Datetime.now(),
                    'sync_count': self.sync_count + 1,
                    'error_count': 0,
                    'last_error': False,
                    'last_error_date': False
                })
            elif status == 'failed':
                update_vals.update({
                    'error_count': self.error_count + 1,
                    'last_error': error_message,
                    'last_error_date': fields.Datetime.now(),
                    'retry_count': self.retry_count + 1
                })
            
            if sap_data:
                update_vals['last_sap_data'] = json.dumps(sap_data)
            if odoo_data:
                update_vals['last_odoo_data'] = json.dumps(odoo_data)
            
            self.write(update_vals)
            
        except Exception as e:
            _logger.error(f"Error updating sync status: {str(e)}")
            raise SapSyncError(f"Failed to update sync status: {str(e)}")
    
    def mark_for_resync(self):
        """Mark record for resynchronization"""
        self.write({
            'sync_status': 'pending',
            'next_sync_date': fields.Datetime.now(),
            'retry_count': 0
        })
    
    def resolve_conflict(self, resolution, resolution_notes=None):
        """Resolve sync conflict"""
        self.write({
            'sync_status': 'pending',
            'conflict_resolution': resolution,
            'conflict_reason': resolution_notes or self.conflict_reason,
            'next_sync_date': fields.Datetime.now()
        })
    
    def get_sync_history(self):
        """Get sync history for this record"""
        return self.env['sap.sync.log'].search([
            ('model_name', '=', self.model_name),
            ('external_id', '=', self.external_id),
            ('backend_id', '=', self.backend_id.id)
        ], order='create_date desc', limit=10)
    
    def get_related_records(self):
        """Get related synced records"""
        return self.search([
            ('backend_id', '=', self.backend_id.id),
            ('external_id', '=', self.external_id),
            ('id', '!=', self.id)
        ])
    
    @api.model
    def get_sync_statistics(self, backend_id=None, days=30):
        """Get sync statistics"""
        domain = [
            ('last_sync_date', '>=', fields.Datetime.now() - timedelta(days=days))
        ]
        if backend_id:
            domain.append(('backend_id', '=', backend_id))
        
        records = self.search(domain)
        
        stats = {
            'total_records': len(records),
            'by_status': {},
            'by_model': {},
            'by_direction': {},
            'success_rate': 0,
            'error_rate': 0,
            'stale_records': len(records.filtered('is_stale'))
        }
        
        # Count by status
        for status in ['pending', 'success', 'failed', 'cancelled', 'conflict', 'needs_attention']:
            count = len(records.filtered(lambda r: r.sync_status == status))
            stats['by_status'][status] = count
        
        # Count by model
        for model in records.mapped('model_name'):
            count = len(records.filtered(lambda r: r.model_name == model))
            stats['by_model'][model] = count
        
        # Count by direction
        for direction in ['sap_to_odoo', 'odoo_to_sap', 'bidirectional', 'manual']:
            count = len(records.filtered(lambda r: r.sync_direction == direction))
            stats['by_direction'][direction] = count
        
        # Calculate rates
        if stats['total_records'] > 0:
            stats['success_rate'] = round((stats['by_status']['success'] / stats['total_records']) * 100, 2)
            stats['error_rate'] = round((stats['by_status']['failed'] / stats['total_records']) * 100, 2)
        
        return stats
    
    def action_view_odoo_record(self):
        """Open the related Odoo record"""
        if not self.odoo_record:
            raise UserError("No Odoo record found")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.model_name,
            'res_id': self.odoo_id,
            'view_mode': 'form',
            'target': 'current'
        }
    
    def action_view_sync_history(self):
        """View sync history for this record"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Sync History - {self.display_name}',
            'res_model': 'sap.sync.log',
            'view_mode': 'tree,form',
            'domain': [
                ('model_name', '=', self.model_name),
                ('external_id', '=', self.external_id),
                ('backend_id', '=', self.backend_id.id)
            ],
            'context': {'default_model_name': self.model_name, 'default_external_id': self.external_id},
            'target': 'current'
        }
    
    def action_resync_record(self):
        """Resync this record"""
        self.mark_for_resync()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Resync Scheduled',
                'message': f'Record {self.display_name} has been marked for resynchronization',
                'type': 'success'
            }
        }
    
    def action_resolve_conflict(self):
        """Open conflict resolution wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resolve Sync Conflict',
            'res_model': 'sap.conflict.resolution.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_synced_data_id': self.id}
        }
