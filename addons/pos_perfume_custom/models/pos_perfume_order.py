# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PosPerfumeOrder(models.Model):
    _name = 'pos.perfume.order'
    _description = 'POS Perfume Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Order Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
        tracking=True
    )
    
    date = fields.Datetime(
        string='Order Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='Salesperson',
        required=True,
        default=lambda self: self.env.user,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    
    order_line_ids = fields.One2many(
        'pos.perfume.order.line',
        'order_id',
        string='Order Lines',
        copy=True
    )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation'),
        ('sale', 'Sale Order'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, required=True)
    
    # Totals
    amount_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    amount_discount = fields.Monetary(
        string='Total Discount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    amount_tax = fields.Monetary(
        string='Taxes',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    amount_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.ref('base.USD', raise_if_not_found=False) or self.env.company.currency_id,
        required=True
    )
    
    # IQD Currency
    amount_total_iqd = fields.Monetary(
        string='Total (IQD)',
        compute='_compute_amount_iqd',
        store=True,
        currency_field='currency_iqd_id'
    )
    
    currency_iqd_id = fields.Many2one(
        'res.currency',
        string='IQD Currency',
        default=lambda self: self.env.ref('base.IQD', raise_if_not_found=False)
    )
    
    exchange_rate = fields.Float(
        string='Exchange Rate (USD to IQD)',
        default=1300.0,
        digits=(12, 2)
    )
    
    # Related Sale Order
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Sale Order',
        readonly=True,
        copy=False
    )
    
    # Notes
    note = fields.Text(string='Notes')
    
    @api.depends('order_line_ids.line_subtotal', 'order_line_ids.discount_amount')
    def _compute_amounts(self):
        """Calculate order totals from lines"""
        for order in self:
            amount_subtotal = 0.0
            amount_discount = 0.0
            amount_tax = 0.0
            
            for line in order.order_line_ids:
                amount_subtotal += line.line_subtotal
                amount_discount += line.discount_amount
            
            order.amount_subtotal = amount_subtotal
            order.amount_discount = amount_discount
            order.amount_tax = amount_tax
            order.amount_total = amount_subtotal - amount_discount + amount_tax
    
    @api.depends('amount_total', 'exchange_rate')
    def _compute_amount_iqd(self):
        """Convert total to IQD"""
        for order in self:
            order.amount_total_iqd = order.amount_total * order.exchange_rate
    
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number for new orders"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'pos.perfume.order'
                ) or _('New')
        return super().create(vals_list)
    
    def action_quotation(self):
        """Set order to quotation state"""
        self.ensure_one()
        self.state = 'quotation'
        return True
    
    def action_confirm(self):
        """Confirm order and create sale order"""
        self.ensure_one()
        
        if not self.order_line_ids:
            raise UserError(_('Cannot confirm an order without lines.'))
        
        # Create Sale Order
        sale_vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.user_id.id,
            'date_order': self.date,
            'origin': self.name,
            'note': self.note,
        }
        
        # Create sale order lines
        order_lines = []
        for line in self.order_line_ids:
            order_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.quantity,
                'price_unit': line.unit_price,
                'discount': line.discount_percent,
            }))
        
        sale_vals['order_line'] = order_lines
        sale_order = self.env['sale.order'].create(sale_vals)
        
        self.write({
            'state': 'sale',
            'sale_order_id': sale_order.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_cancel(self):
        """Cancel order"""
        for order in self:
            if order.state == 'done':
                raise UserError(_('Cannot cancel a done order.'))
            order.state = 'cancel'
        return True
    
    def action_draft(self):
        """Set back to draft"""
        for order in self:
            order.state = 'draft'
        return True
    
    def action_send_whatsapp(self):
        """Open WhatsApp wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Send via WhatsApp'),
            'res_model': 'pos.whatsapp.send',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }
    
    def action_view_sale_order(self):
        """View linked sale order"""
        self.ensure_one()
        if not self.sale_order_id:
            raise UserError(_('No sale order linked to this POS order.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sale Order'),
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }


class PosPerfumeOrderLine(models.Model):
    _name = 'pos.perfume.order.line'
    _description = 'POS Perfume Order Line'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Sequence', default=10)
    
    order_id = fields.Many2one(
        'pos.perfume.order',
        string='Order Reference',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        domain=[('sale_ok', '=', True)],
        index=True
    )
    
    product_code = fields.Char(
        related='product_id.default_code',
        string='Product Code',
        readonly=True,
        store=True
    )
    
    product_foreign_name = fields.Char(
        related='product_id.foreign_name',
        string='Foreign Name',
        readonly=True,
        store=True
    )
    
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True
    )
    
    quantity = fields.Float(
        string='Quantity',
        required=True,
        default=1.0,
        digits='Product Unit of Measure'
    )
    
    unit_price = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price'
    )
    
    discount_percent = fields.Float(
        string='Discount %',
        default=0.0,
        digits=(5, 2)
    )
    
    # Computed fields
    price_after_discount = fields.Monetary(
        string='Price After Discount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    line_subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    discount_amount = fields.Monetary(
        string='Discount Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    line_total = fields.Monetary(
        string='Total',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='order_id.currency_id',
        string='Currency',
        store=True
    )
    
    # Stock availability
    available_qty = fields.Float(
        string='Available Qty',
        compute='_compute_available_qty',
        digits='Product Unit of Measure'
    )
    
    @api.depends('quantity', 'unit_price', 'discount_percent')
    def _compute_amounts(self):
        """Calculate line amounts"""
        for line in self:
            # Price after applying discount percentage
            price_after_discount = line.unit_price * (1 - line.discount_percent / 100)
            
            # Subtotal before discount
            line_subtotal = line.quantity * line.unit_price
            
            # Discount amount
            discount_amount = line_subtotal * (line.discount_percent / 100)
            
            # Line total (quantity * price after discount)
            line_total = line.quantity * price_after_discount
            
            line.update({
                'price_after_discount': price_after_discount,
                'line_subtotal': line_subtotal,
                'discount_amount': discount_amount,
                'line_total': line_total,
            })
    
    @api.depends('product_id', 'warehouse_id')
    def _compute_available_qty(self):
        """Get available quantity in selected warehouse"""
        for line in self:
            if line.product_id and line.warehouse_id:
                # Get stock location of warehouse
                location = line.warehouse_id.lot_stock_id
                
                # Get available quantity
                quants = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', 'child_of', location.id),
                ])
                line.available_qty = sum(quants.mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            else:
                line.available_qty = 0.0
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set default price when product is selected"""
        if self.product_id:
            self.unit_price = self.product_id.list_price
    
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Quantity must be positive.'))
    
    @api.constrains('discount_percent')
    def _check_discount(self):
        """Validate discount is between 0 and 100"""
        for line in self:
            if line.discount_percent < 0 or line.discount_percent > 100:
                raise ValidationError(_('Discount must be between 0% and 100%.'))
    
    @api.constrains('unit_price')
    def _check_price(self):
        """Validate price is not negative"""
        for line in self:
            if line.unit_price < 0:
                raise ValidationError(_('Price cannot be negative.'))

