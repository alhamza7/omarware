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
    
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Pricelist',
        required=True,
        default=lambda self: self._get_default_pricelist(),
        tracking=True
    )
    
    def _get_default_pricelist(self):
        """Get default pricelist - try to find 'Price list 1' first"""
        # Try to find "Price list 1" - case insensitive
        pricelist = self.env['product.pricelist'].search([
            ('name', 'ilike', 'Price list 1'),
            ('active', '=', True)
        ], limit=1)
        
        # If not found, try "list 1"
        if not pricelist:
            pricelist = self.env['product.pricelist'].search([
                ('name', 'ilike', 'list 1'),
                ('active', '=', True)
            ], limit=1)
        
        # If still not found, use Public Pricelist (list0)
        if not pricelist:
            pricelist = self.env.ref('product.list0', raise_if_not_found=False)
        
        return pricelist.id if pricelist else False
    
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
    
    @api.onchange('partner_id')
    def _onchange_partner_pricelist(self):
        """Set pricelist from customer - DISABLED: Always use Price list 1"""
        # DISABLED: Keep pricelist fixed to "Price list 1" regardless of customer
        # if self.partner_id and self.partner_id.property_product_pricelist:
        #     self.pricelist_id = self.partner_id.property_product_pricelist
        pass
    
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
        import logging
        _logger = logging.getLogger(__name__)
        
        # Get IDs and normalize them - flatten nested lists and ensure integers
        def normalize_ids(ids):
            """Flatten nested lists and extract integer IDs"""
            result = []
            if isinstance(ids, (list, tuple)):
                for item in ids:
                    if isinstance(item, (list, tuple)):
                        result.extend(normalize_ids(item))
                    elif isinstance(item, int):
                        result.append(item)
                    elif hasattr(item, 'id'):
                        result.append(item.id)
            elif isinstance(ids, int):
                result.append(ids)
            elif hasattr(ids, 'id'):
                result.append(ids.id)
            return result
        
        order_ids = normalize_ids(self.ids)
        if not order_ids:
            raise UserError(_('No orders selected.'))
        
        # Ensure all IDs are integers
        order_ids = [int(id) for id in order_ids if id]
        
        # Browse records fresh to avoid any cached state issues
        orders = self.env['pos.perfume.order'].browse(order_ids)
        _logger.info(f"[POS Confirm] Starting action_confirm for {len(orders)} orders")
        results = []
        
        for order in orders:
            order_id = order.id
            # Read all needed fields at once to avoid multiple field cache accesses
            try:
                order_data = order.read(['name', 'partner_id', 'user_id', 'date', 'pricelist_id', 'note'])[0]
                order_name = order_data.get('name', f"Order-{order_id}")
            except (TypeError, AttributeError, KeyError, IndexError) as e:
                _logger.warning(f"[POS Confirm] Error reading order data: {e}, using ID only")
                order_name = f"Order-{order_id}"
                order_data = {}
            
            _logger.info(f"[POS Confirm] Processing order {order_id}: {order_name}")
            
            # Validate - get order lines using search to avoid field cache issues
            try:
                order_lines = self.env['pos.perfume.order.line'].search([('order_id', '=', order_id)])
            except (TypeError, AttributeError):
                # Fallback to direct access if search fails
                order_lines = order.order_line_ids
            
            if not order_lines:
                _logger.error(f"[POS Confirm] No lines in order {order_id}")
                raise UserError(_('Cannot confirm an order without lines.'))
            
            _logger.info(f"[POS Confirm] Order has {len(order_lines)} lines")
            
            # Create Sale Order - use read data or direct access with fallback
            sale_vals = {
                'partner_id': order_data.get('partner_id', [False])[0] if order_data.get('partner_id') else order.partner_id.id,
                'user_id': order_data.get('user_id', [False])[0] if order_data.get('user_id') else order.user_id.id,
                'date_order': order_data.get('date') or order.date,
                'origin': order_name,
                'note': order_data.get('note', '') or (order.note or ''),
                'pricelist_id': order_data.get('pricelist_id', [False])[0] if order_data.get('pricelist_id') else (order.pricelist_id.id if order.pricelist_id else False),
            }
            
            # Create sale order lines
            sale_order_lines = []
            for line in order_lines:
                line_vals = {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom_id': line.product_uom_id.id if line.product_uom_id else line.product_id.uom_id.id,
                    'price_unit': line.unit_price,
                    'discount': line.discount_percent or 0.0,
                }
                # Add warehouse info if available (for sale_order_line_multi_warehouse)
                if line.warehouse_id:
                    line_vals['product_warehouse_id'] = line.warehouse_id.id
                sale_order_lines.append((0, 0, line_vals))
            
            sale_vals['order_line'] = sale_order_lines
            
            _logger.info(f"[POS Confirm] Creating sale.order with {len(sale_order_lines)} lines")
            _logger.info(f"[POS Confirm] Sale vals: partner={sale_vals['partner_id']}, pricelist={sale_vals['pricelist_id']}")
            
            try:
                sale_order = self.env['sale.order'].create(sale_vals)
                _logger.info(f"[POS Confirm] Sale order created: {sale_order.name} (ID: {sale_order.id})")
            except Exception as e:
                _logger.error(f"[POS Confirm] Error creating sale order: {e}", exc_info=True)
                raise
            
            # Update POS order
            order.write({
                'state': 'sale',
                'sale_order_id': sale_order.id,
            })
            
            _logger.info(f"[POS Confirm] POS order updated to state=sale")
            
            results.append({
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'res_id': sale_order.id,
                'view_mode': 'form',
                'views': [[False, 'form']],
                'target': 'current',
            })
        
        # Return single result if single record, otherwise first result
        return results[0] if len(results) == 1 else results
    
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
    
    # UoM Support
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        help='Unit of measure for this product'
    )
    
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True
    )
    
    location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        help='Specific storage location within warehouse'
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
        """Set default price and UoM when product is selected"""
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.list_price
    
    @api.onchange('product_id', 'product_uom_id')
    def _onchange_product_uom(self):
        """Get price based on UoM from pricelist"""
        if self.product_id and self.product_uom_id and self.order_id.pricelist_id:
            price = self._get_uom_price(
                self.order_id.pricelist_id,
                self.product_uom_id
            )
            if price:
                self.unit_price = price
    
    @api.onchange('warehouse_id')
    def _onchange_warehouse(self):
        """Set default location when warehouse changes"""
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id
    
    def _get_uom_price(self, pricelist, uom):
        """Get price for specific UoM from pricelist items"""
        self.ensure_one()
        
        # Search for exact UoM match in pricelist
        item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('product_packaging_id', '=', uom.id),
            ('compute_price', '=', 'fixed'),
        ], limit=1)
        
        if item:
            return item.fixed_price
        
        # Fallback to base price with conversion
        if uom != self.product_id.uom_id:
            return self.product_id.uom_id._compute_price(
                self.product_id.list_price,
                uom
            )
        
        return self.product_id.list_price
    
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

