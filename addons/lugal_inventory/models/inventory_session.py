from odoo import models, fields, api


class InventorySession(models.Model):
    """Represents a physical inventory counting session for a warehouse."""
    _name = 'lugal.inventory.session'
    _description = 'Inventory Session'
    _order = 'create_date desc'
    _rec_name = 'name'

    name = fields.Char(string='Session Name', required=True, default=lambda self: self._default_name())
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, index=True)
    state = fields.Selection([
        ('open', 'Open'),
        ('closed', 'Closed'),
    ], string='Status', default='open', index=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user)
    audit_line_ids = fields.One2many('lugal.inventory.audit', 'session_id', string='Audit Lines')
    audit_count = fields.Integer(string='Audit Count', compute='_compute_audit_count', store=True)
    note = fields.Text(string='Notes')

    @api.model
    def _default_name(self):
        """Generate a default session name based on current date."""
        return self.env['ir.sequence'].next_by_code('lugal.inventory.session') or 'New'

    @api.depends('audit_line_ids')
    def _compute_audit_count(self):
        for session in self:
            session.audit_count = len(session.audit_line_ids)

    def action_close(self):
        """Close the inventory session."""
        self.write({'state': 'closed'})

    def action_reopen(self):
        """Reopen a closed session."""
        self.write({'state': 'open'})
