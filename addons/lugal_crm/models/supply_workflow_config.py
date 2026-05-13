# -*- coding: utf-8 -*-
"""Settings + helpers for optional supply chain enhancements."""

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    supply_budget_control_enabled = fields.Boolean(
        string='Enable supply budget checks on PO confirm',
        config_parameter='lugal_supply.budget_control_enabled',
        default=False,
    )
    supply_stock_validate_po = fields.Boolean(
        string='Validate product stock before PO confirm',
        config_parameter='lugal_supply.stock_validate_po',
        default=True,
    )
    supply_workflow_activity_notify = fields.Boolean(
        string='Create activities on key workflow transitions',
        config_parameter='lugal_supply.workflow_activity_notify',
        default=True,
    )
    supply_workflow_level_count = fields.Integer(
        string='Extra approval levels (per document)',
        default=0,
        help='Number of approval rows auto-created on item request (Start), negotiation (create), '
             'and new supply PO. 0 keeps legacy e-sign / finalize behaviour only.',
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        icp = self.env['ir.config_parameter'].sudo()
        res['supply_workflow_level_count'] = int(
            icp.get_param('lugal_supply.workflow_level_count', '0') or 0
        )
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'lugal_supply.workflow_level_count',
            max(0, int(self.supply_workflow_level_count or 0)),
        )


def supply_workflow_level_count(env):
    return max(0, int(env['ir.config_parameter'].sudo().get_param('lugal_supply.workflow_level_count', '0') or 0))


def supply_budget_enabled(env):
    return env['ir.config_parameter'].sudo().get_param('lugal_supply.budget_control_enabled', 'False') == 'True'


def supply_stock_validate_enabled(env):
    return env['ir.config_parameter'].sudo().get_param('lugal_supply.stock_validate_po', 'True') == 'True'


def supply_activity_notify_enabled(env):
    return env['ir.config_parameter'].sudo().get_param('lugal_supply.workflow_activity_notify', 'True') == 'True'
