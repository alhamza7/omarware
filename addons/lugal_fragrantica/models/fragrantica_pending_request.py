# -*- coding: utf-8 -*-

from odoo import models, fields, api

class FragranticaPendingRequest(models.Model):
    _name = 'fragrantica.pending.request'
    _description = 'Fragrantica Pending Request'
    _order = 'create_date desc'
    
    name = fields.Char('Request Name', compute='_compute_name', store=True)
    fragrantica_url = fields.Char('Fragrantica URL', required=True)
    
    product_id = fields.Many2one('product.template', string='Related Product', ondelete='set null')
    
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ], string='Status', default='pending', required=True)
    
    notes = fields.Text('Notes')
    error_message = fields.Text('Error Message')
    
    # Metadata
    requested_by = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user)
    create_date = fields.Datetime('Request Date', readonly=True)
    completed_date = fields.Datetime('Completion Date', readonly=True)
    
    @api.depends('fragrantica_url', 'product_id')
    def _compute_name(self):
        """Compute display name"""
        for request in self:
            if request.product_id:
                request.name = f"Request for: {request.product_id.name}"
            elif request.fragrantica_url:
                request.name = f"Request: {request.fragrantica_url[:50]}..."
            else:
                request.name = "New Request"
    
    def action_mark_completed(self):
        """Mark request as completed"""
        self.write({
            'state': 'completed',
            'completed_date': fields.Datetime.now()
        })
    
    def action_mark_failed(self):
        """Mark request as failed"""
        self.write({
            'state': 'failed',
            'completed_date': fields.Datetime.now()
        })
    
    def action_retry(self):
        """Reset request to pending"""
        self.write({
            'state': 'pending',
            'error_message': False,
            'completed_date': False
        })

