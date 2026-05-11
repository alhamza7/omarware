# -*- coding: utf-8 -*-
"""Job-title-level permission templates.

Every employee with a given job title inherits the permissions stored here
as their baseline. An admin can edit a template and optionally propagate the
change to every user that carries that job title (apply_to_all_users flag).
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalCrmPermissionTemplate(models.Model):
    _name = 'lugal.crm.permission.template'
    _description = 'CRM Job Title Permission Template'
    _order = 'job_title asc'
    _rec_name = 'job_title'

    job_title = fields.Char(
        string='Job Title / المسمى الوظيفي',
        required=True,
        index=True,
    )
    label = fields.Char(string='Display Label', help='Human-friendly label shown in admin UI')
    crm_role = fields.Selection(
        selection=[
            ('none',            'No CRM Role'),
            ('agent',           'Agent'),
            ('supervisor',      'Supervisor'),
            ('manager',         'Manager'),
            ('general_manager', 'General Manager'),
            ('qa_auditor',      'QA Auditor'),
            ('qa_supervisor',   'QA Supervisor'),
        ],
        string='System CRM Role',
        default='none',
        help='Odoo security group assigned to users of this job title. '
             'The permission JSON below overrides what the group implies.',
    )
    permissions_json = fields.Text(
        string='Permissions JSON',
        default='{}',
        help='Full permission snapshot for this job title. '
             'Stored as a JSON object matching the canonical permission tree.',
    )
    route_visibility_json = fields.Text(
        string='Route Visibility Overrides JSON',
        default='{}',
        help='Explicit route show/hide map keyed by route path for this template.',
    )
    notes = fields.Text(string='Admin Notes')
    is_active = fields.Boolean(default=True)
    user_count = fields.Integer(
        string='Users',
        compute='_compute_user_count',
        store=False,
    )

    _sql_constraints = [
        ('job_title_unique', 'UNIQUE(job_title)',
         'A permission template already exists for this job title.'),
    ]

    def _auto_init(self):
        """Ensure route_visibility_json column exists on module install/update."""
        try:
            self.env.cr.execute("""
                ALTER TABLE lugal_crm_permission_template
                ADD COLUMN IF NOT EXISTS route_visibility_json TEXT DEFAULT '{}'
            """)
        except Exception as exc:
            _logger.debug('_auto_init route_visibility_json already exists: %s', exc)
        super()._auto_init()

    @api.depends()
    def _compute_user_count(self):
        for rec in self:
            partners = self.env['res.partner'].search([
                ('function', '=ilike', rec.job_title),
            ])
            rec.user_count = self.env['res.users'].search_count([
                ('partner_id', 'in', partners.ids),
                ('active', '=', True),
            ])

    def get_permissions(self) -> dict:
        """Return parsed permissions dict (safe fallback to {})."""
        try:
            permissions = json.loads(self.permissions_json or '{}') or {}
            permissions.pop('_route_visibility', None)
            return permissions
        except Exception:
            return {}

    def get_route_visibility(self) -> dict:
        """Return parsed route-visibility overrides dict (safe fallback to {})."""
        route_visibility = {}
        try:
            route_visibility = json.loads(self.route_visibility_json or '{}') or {}
        except Exception:
            route_visibility = {}
        try:
            legacy = (json.loads(self.permissions_json or '{}') or {}).get('_route_visibility') or {}
            if isinstance(legacy, dict):
                route_visibility = {**legacy, **route_visibility}
        except Exception:
            pass
        return route_visibility
