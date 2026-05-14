from odoo import models, fields, api


class InventoryUser(models.Model):
    """Extends res.users to link users with specific warehouses for inventory operations."""
    _name = 'lugal.inventory.user'
    _description = 'Inventory User'
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='User', required=True, index=True, ondelete='cascade')
    full_name = fields.Char(string='Full Name')
    username = fields.Char(string='Username', related='user_id.login', store=True, readonly=True)
    role = fields.Selection([
        ('admin', 'مدير'),
        ('user', 'مستخدم'),
    ], string='Role', default='user', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, index=True)
    warehouse_name = fields.Char(string='Warehouse Name', related='warehouse_id.name', store=True, readonly=True)
    active = fields.Boolean(string='Active', default=True)

    _sql_constraints = [
        ('user_warehouse_unique', 'UNIQUE(user_id, warehouse_id)', 'User is already assigned to this warehouse!'),
    ]

    def name_get(self):
        """Display user as 'username - warehouse'."""
        result = []
        for rec in self:
            name = f"{rec.username or ''} - {rec.warehouse_name or ''}"
            result.append((rec.id, name))
        return result
