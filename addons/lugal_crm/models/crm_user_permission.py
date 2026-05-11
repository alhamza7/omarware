# -*- coding: utf-8 -*-
"""Per-user permission overrides.

When the admin needs to grant (or restrict) an individual employee
beyond what their job-title template defines, those deltas are stored here.

Effective permissions = deep_merge(job_title_template, this_override)
— values in this record WIN over the template.
"""
import json
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class LugalCrmUserPermission(models.Model):
    _name = 'lugal.crm.user.permission'
    _description = 'User-specific Permission Override'
    _order = 'user_id asc'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True,
        ondelete='cascade',
    )
    job_title_override = fields.Char(
        string='Job Title Override',
        help='If set, the system uses this job title (instead of user.job_title) '
             'to look up the base template for this user.',
    )
    permissions_json = fields.Text(
        string='Override Permissions JSON',
        default='{}',
        help='Contains ONLY the actions that differ from the job-title template. '
             'Merged on top of the template at query time.',
    )
    route_visibility_json = fields.Text(
        string='Route Visibility Overrides JSON',
        default='{}',
        help='Explicit route show/hide map keyed by route path. '
             '"false" always hides a nav section regardless of action permissions. '
             '"true" always shows it. Omitted paths fall back to computed visibility.',
    )
    admin_notes = fields.Text(
        string='Admin Notes',
        help='Why was this exception created?',
    )
    last_modified_by = fields.Many2one('res.users', string='Last Modified By', readonly=True)
    last_modified_at = fields.Datetime(string='Last Modified At', readonly=True)

    _sql_constraints = [
        ('user_unique', 'UNIQUE(user_id)',
         'A permission override record already exists for this user.'),
    ]

    def _auto_init(self):
        """Ensure route_visibility_json column exists on module install/update."""
        try:
            self.env.cr.execute("""
                ALTER TABLE lugal_crm_user_permission
                ADD COLUMN IF NOT EXISTS route_visibility_json TEXT DEFAULT '{}'
            """)
        except Exception as exc:
            _logger.debug('_auto_init route_visibility_json already exists: %s', exc)
        super()._auto_init()

    def get_overrides(self) -> dict:
        """Return parsed action-level overrides dict (safe fallback to {})."""
        try:
            overrides = json.loads(self.permissions_json or '{}') or {}
            overrides.pop('_route_visibility', None)
            return overrides
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
            # Backward compatibility for the short-lived implementation that
            # stored this under permissions_json["_route_visibility"].
            legacy = (json.loads(self.permissions_json or '{}') or {}).get('_route_visibility') or {}
            if isinstance(legacy, dict):
                route_visibility = {**legacy, **route_visibility}
        except Exception:
            pass
        return route_visibility

    @api.model
    def upsert_for_user(self, user_id: int, overrides: dict,
                        route_visibility: dict = None,
                        job_title_override: str = None,
                        admin_notes: str = None,
                        modifier_id: int = None) -> 'LugalCrmUserPermission':
        """Create or update the override record for a user."""
        existing = self.search([('user_id', '=', user_id)], limit=1)
        vals = {
            'permissions_json': json.dumps(overrides or {}, ensure_ascii=False),
            'last_modified_by': modifier_id,
            'last_modified_at': fields.Datetime.now(),
        }
        if route_visibility is not None:
            vals['route_visibility_json'] = json.dumps(route_visibility, ensure_ascii=False)
        if job_title_override is not None:
            vals['job_title_override'] = job_title_override or False
        if admin_notes is not None:
            vals['admin_notes'] = admin_notes or False
        if existing:
            existing.write(vals)
            return existing
        vals['user_id'] = user_id
        return self.create(vals)
