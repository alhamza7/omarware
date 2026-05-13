# -*- coding: utf-8 -*-
import logging
from datetime import timezone

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmMarquee(models.Model):
    """System-wide scrolling announcement shown to all employees with an expiry."""

    _name        = 'lugal.crm.marquee'
    _description = 'Marquee Announcement'
    _order       = 'created_at desc, id desc'
    _rec_name    = 'message'

    message    = fields.Text(string='Message (EN)',  required=True)
    message_ar = fields.Text(string='Message (AR)')

    # Visibility window
    starts_at  = fields.Datetime(string='Starts At',  required=True,
                                 default=fields.Datetime.now)
    expires_at = fields.Datetime(string='Expires At', required=True,
                                 help='Marquee stops showing after this datetime (server UTC).')

    # Optional styling hints for the FE
    bg_color   = fields.Char(string='Background Color', default='#1E3A5F',
                             help='CSS colour, e.g. #1E3A5F or rgba(30,58,95,1)')
    text_color = fields.Char(string='Text Color', default='#FFFFFF')
    speed      = fields.Integer(string='Scroll Speed (px/s)', default=60,
                                help='How fast the text scrolls. Suggested: 40–120.')

    is_active  = fields.Boolean(string='Active', compute='_compute_is_active', store=False)
    created_by = fields.Many2one('res.users', string='Created By',
                                 default=lambda self: self.env.user, ondelete='set null')
    created_at = fields.Datetime(string='Created At', default=fields.Datetime.now, readonly=True)

    # ------------------------------------------------------------------ #
    @api.depends('starts_at', 'expires_at')
    def _compute_is_active(self):
        now = fields.Datetime.now()
        for rec in self:
            rec.is_active = bool(
                rec.starts_at and rec.expires_at
                and rec.starts_at <= now <= rec.expires_at
            )

    # ------------------------------------------------------------------ #
    def _to_dict(self):
        """Serialise for the REST API / WS payload."""
        def _iso(dt):
            if not dt:
                return None
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.isoformat(timespec='seconds')

        return {
            'id':         self.id,
            'message':    self.message or '',
            'message_ar': self.message_ar or '',
            'starts_at':  _iso(self.starts_at),
            'expires_at': _iso(self.expires_at),
            'bg_color':   self.bg_color or '#1E3A5F',
            'text_color': self.text_color or '#FFFFFF',
            'speed':      self.speed or 60,
            'is_active':  self.is_active,
            'created_by': self.created_by.name if self.created_by else None,
            'created_at': _iso(self.created_at),
        }

    # ------------------------------------------------------------------ #
    def _push_to_all_users(self, event_type='crm.marquee.new'):
        """Broadcast this marquee to every logged-in user via bus.bus."""
        payload = self._to_dict()
        try:
            self.env['bus.bus'].sudo()._sendone(
                'crm_broadcast',
                event_type,
                payload,
            )
            _logger.info('[Marquee] pushed id=%s event=%s to crm_broadcast', self.id, event_type)
        except Exception:
            _logger.exception('[Marquee] bus push failed for id=%s', self.id)

    # ------------------------------------------------------------------ #
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._push_to_all_users('crm.marquee.new')
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._push_to_all_users('crm.marquee.updated')
        return res
