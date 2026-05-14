from odoo import models, fields, api


class InventoryAudit(models.Model):
    """Records a single inventory count entry (product + qty + warehouse + user)."""
    _name = 'lugal.inventory.audit'
    _description = 'Inventory Audit Line'
    _order = 'id desc'

    session_id = fields.Many2one('lugal.inventory.session', string='Session', index=True, ondelete='set null')
    product_id = fields.Many2one('product.product', string='Product', required=True, index=True)
    # Stored as plain Char (not related) to avoid jsonb flush error on product.name (translatable)
    product_code = fields.Char(string='Product Code', store=True, readonly=True)
    product_name = fields.Char(string='Product Name', store=True, readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, index=True)
    warehouse_name = fields.Char(string='Warehouse Name', store=True, readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    quantity = fields.Float(string='Quantity', required=True, digits=(16, 4))
    user_id = fields.Many2one('res.users', string='Counted By', default=lambda self: self.env.user, index=True)
    user_name = fields.Char(string='User Name', store=True, readonly=True)
    barcode_used = fields.Char(string='Barcode Used')
    note = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        """Populate denormalized name fields from related records on create."""
        for vals in vals_list:
            if vals.get('product_id') and not vals.get('product_code'):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['product_code'] = product.default_code or ''
                # Read name directly from DB to avoid ORM display_name [CODE] prefix
                # and jsonb field issues
                self.env.cr.execute(
                    "SELECT pt.name, pp.default_code FROM product_product pp "
                    "JOIN product_template pt ON pp.product_tmpl_id = pt.id "
                    "WHERE pp.id = %s", [product.id]
                )
                row = self.env.cr.fetchone()
                if row:
                    raw_name = row[0]
                    if isinstance(raw_name, dict):
                        vals['product_name'] = raw_name.get('en_US') or raw_name.get('ar_001') or next(iter(raw_name.values()), '')
                    else:
                        vals['product_name'] = str(raw_name) if raw_name else ''
                    if not vals.get('product_code') and row[1]:
                        vals['product_code'] = row[1]
            if vals.get('warehouse_id') and not vals.get('warehouse_name'):
                warehouse = self.env['stock.warehouse'].browse(vals['warehouse_id'])
                vals['warehouse_name'] = warehouse.name or ''
            if vals.get('user_id') and not vals.get('user_name'):
                user = self.env['res.users'].browse(vals['user_id'])
                vals['user_name'] = user.name or ''
        return super().create(vals_list)

    def name_get(self):
        """Display audit as 'Product Code - Warehouse'."""
        result = []
        for audit in self:
            name = f"{audit.product_code or ''} - {audit.warehouse_name or ''}"
            result.append((audit.id, name))
        return result
