# -*- coding: utf-8 -*-
# Copyright 2024 Your Company
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from odoo import models, fields, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class SapDashboard(models.Model):
    """SAP Integration Dashboard Statistics"""
    _name = 'sap.dashboard'
    _description = 'SAP Dashboard'
    
    name = fields.Char('Dashboard Name', default='SAP Integration Dashboard', readonly=True)
    
    # Backend Statistics
    total_backends = fields.Integer('Total Backends', compute='_compute_backend_stats')
    active_backends = fields.Integer('Active Backends', compute='_compute_backend_stats')
    connected_backends = fields.Integer('Connected Backends', compute='_compute_backend_stats')
    
    # Sync Statistics
    total_partners = fields.Integer('Total Partners', compute='_compute_sync_stats')
    total_products = fields.Integer('Total Products', compute='_compute_sync_stats')
    total_orders = fields.Integer('Total Orders', compute='_compute_sync_stats')
    total_invoices = fields.Integer('Total Invoices', compute='_compute_sync_stats')
    
    # Recent Sync Statistics (Last 7 days)
    partners_last_week = fields.Integer('Partners (Last 7 Days)', compute='_compute_recent_stats')
    products_last_week = fields.Integer('Products (Last 7 Days)', compute='_compute_recent_stats')
    orders_last_week = fields.Integer('Orders (Last 7 Days)', compute='_compute_recent_stats')
    
    # Error Statistics
    total_errors = fields.Integer('Total Errors', compute='_compute_error_stats')
    errors_last_week = fields.Integer('Errors (Last 7 Days)', compute='_compute_error_stats')
    
    # Performance Metrics
    avg_sync_time = fields.Float('Avg Sync Time (s)', compute='_compute_performance')
    last_sync_date = fields.Datetime('Last Sync', compute='_compute_performance')
    
    @api.depends()
    def _compute_backend_stats(self):
        """Compute backend statistics"""
        for record in self:
            record.total_backends = self.env['sap.backend'].search_count([])
            record.active_backends = self.env['sap.backend'].search_count([('active', '=', True)])
            record.connected_backends = self.env['sap.backend'].search_count([
                ('active', '=', True),
                ('connection_status', '=', 'connected')
            ])
    
    @api.depends()
    def _compute_sync_stats(self):
        """Compute synchronization statistics"""
        for record in self:
            record.total_partners = self.env['sap.res.partner'].search_count([])
            record.total_products = self.env['sap.product.product'].search_count([])
            record.total_orders = self.env['sap.sale.order'].search_count([])
            record.total_invoices = self.env['sap.account.move'].search_count([])
    
    @api.depends()
    def _compute_recent_stats(self):
        """Compute recent sync statistics (last 7 days)"""
        for record in self:
            last_week = datetime.now() - timedelta(days=7)
            
            record.partners_last_week = self.env['sap.res.partner'].search_count([
                ('create_date', '>=', last_week)
            ])
            record.products_last_week = self.env['sap.product.product'].search_count([
                ('create_date', '>=', last_week)
            ])
            record.orders_last_week = self.env['sap.sale.order'].search_count([
                ('create_date', '>=', last_week)
            ])
    
    @api.depends()
    def _compute_error_stats(self):
        """Compute error statistics"""
        for record in self:
            # Count records with sync errors
            partner_errors = self.env['sap.res.partner'].search_count([('sync_error', '!=', False)])
            product_errors = self.env['sap.product.product'].search_count([('sync_error', '!=', False)])
            order_errors = self.env['sap.sale.order'].search_count([('sync_error', '!=', False)])
            
            record.total_errors = partner_errors + product_errors + order_errors
            
            # Errors in last 7 days
            last_week = datetime.now() - timedelta(days=7)
            partner_errors_week = self.env['sap.res.partner'].search_count([
                ('sync_error', '!=', False),
                ('write_date', '>=', last_week)
            ])
            product_errors_week = self.env['sap.product.product'].search_count([
                ('sync_error', '!=', False),
                ('write_date', '>=', last_week)
            ])
            order_errors_week = self.env['sap.sale.order'].search_count([
                ('sync_error', '!=', False),
                ('write_date', '>=', last_week)
            ])
            
            record.errors_last_week = partner_errors_week + product_errors_week + order_errors_week
    
    @api.depends()
    def _compute_performance(self):
        """Compute performance metrics"""
        for record in self:
            # Get last sync date from most recent binding
            last_partner = self.env['sap.res.partner'].search([], order='sync_date desc', limit=1)
            last_product = self.env['sap.product.product'].search([], order='sync_date desc', limit=1)
            
            dates = [d.sync_date for d in [last_partner, last_product] if d.sync_date]
            record.last_sync_date = max(dates) if dates else False
            
            # Calculate average sync time (placeholder - would need actual timing data)
            record.avg_sync_time = 2.5
    
    def action_view_partners(self):
        """View all synced partners"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'SAP Partners',
            'res_model': 'sap.res.partner',
            'view_mode': 'tree,form',
            'context': dict(self.env.context),
        }
    
    def action_view_products(self):
        """View all synced products"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'SAP Products',
            'res_model': 'sap.product.product',
            'view_mode': 'tree,form',
            'context': dict(self.env.context),
        }
    
    def action_view_orders(self):
        """View all synced orders"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'SAP Orders',
            'res_model': 'sap.sale.order',
            'view_mode': 'tree,form',
            'context': dict(self.env.context),
        }
    
    def action_view_errors(self):
        """View all records with errors"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sync Errors',
            'res_model': 'sap.res.partner',
            'view_mode': 'tree,form',
            'domain': [('sync_error', '!=', False)],
            'context': dict(self.env.context),
        }
    
    def action_refresh_stats(self):
        """Refresh dashboard statistics"""
        self._compute_backend_stats()
        self._compute_sync_stats()
        self._compute_recent_stats()
        self._compute_error_stats()
        self._compute_performance()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Dashboard Refreshed',
                'message': 'Statistics have been updated',
                'type': 'success',
                'sticky': False,
            }
        }

